import asyncio
import functools
from itertools import islice

import discord
import yt_dlp
from async_timeout import timeout
from discord.ext import commands

try:
    import uvloop
except ImportError:
    pass
else:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


class VoiceError(Exception):
    pass


class YTDLError(Exception):
    pass


class YTDLSource(discord.PCMVolumeTransformer):
    YTDL_OPTIONS = {
        "format": "bestaudio/best",
        "extractaudio": True,
        "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
        "restrictfilenames": True,
        "noplaylist": False,
        "nocheckcertificate": True,
        "ignoreerrors": False,
        "logtostderr": False,
        "quiet": True,
        "no_warnings": True,
        "default_search": "auto",
        "source_address": "0.0.0.0",
    }

    FFMPEG_OPTIONS = {
        "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
        "options": "-vn -loglevel -8",
    }

    ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

    def __init__(
        self,
        ctx,
        source: discord.FFmpegPCMAudio,
        *,
        data: dict,
        volume: float = 0.5,
    ):
        super().__init__(source, volume)

        self.requester = ctx.author
        self.channel = ctx.channel
        self.data = data

        self.uploader = data.get("uploader")
        self.title = data.get("title")
        self.title_limited = self.parse_limited_title(data["title"])
        self.title_limited_embed = self.parse_limited_title_embed(data["title"])
        self.thumbnail = data.get("thumbnail")
        self.description = data.get("description")
        self.duration = self.parse_duration(data["duration"])
        self.url = data.get("webpage_url")
        self.views = self.parse_number(data["view_count"])
        self.likes = self.parse_number(data["like_count"])
        self.stream_url = data.get("url")

    def __str__(self):
        return f"**{self.title}** by **{self.uploader}**"

    @classmethod
    async def check_type(cls, search: str, *, loop):
        try:
            partial = functools.partial(
                cls.ytdl.extract_info, search, download=False, process=False
            )
            data = await loop.run_in_executor(None, partial)

            if not data:
                raise YTDLError(f"Couldn't find anything that matches {search}")

            return data
        except Exception:
            pass

    @classmethod
    async def create_source_playlist(cls, typ, data, *, loop):
        search = data["url"]

        if typ == "playlist_alt":
            search = data["url"]

            partial = functools.partial(
                cls.ytdl.extract_info, search, download=False, process=False
            )
            data = await loop.run_in_executor(None, partial)

        if not data:
            raise YTDLError(f"Couldn't find anything that matches {data['url']}")

        songs = []

        for entry in data["entries"]:
            if entry:
                songs.append(entry)

        return songs

    @classmethod
    async def create_source_single(cls, ctx, data, *, loop):
        search = data.get("id")

        if search:
            search = f"https://www.youtube.com/watch?v={search}"
        else:
            search = data["webpage_url"]

        partial = functools.partial(cls.ytdl.extract_info, search, download=False)
        processed_info = await loop.run_in_executor(None, partial)

        if processed_info is None:
            raise YTDLError(f"Couldn't fetch: {search}")

        if "entries" in processed_info:
            info = None
            while info is None:
                try:
                    info = processed_info["entries"].pop(0)
                except IndexError:
                    raise YTDLError(f"Couldn't retrieve any matches for {search}")
        else:
            info = processed_info

        duration = info["duration"]

        if duration > 72000:
            raise YTDLError(f"Video is longer than 20 hours({duration//3600} hours)")

        return cls(
            ctx, discord.FFmpegPCMAudio(info["url"], **cls.FFMPEG_OPTIONS), data=info
        )

    @staticmethod
    def parse_duration(duration: int):
        minutes, seconds = divmod(duration, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)

        duration = []
        if days > 0:
            duration.append(f"{days} days")
        if hours > 0:
            duration.append(f"{hours} hours")
        if minutes > 0:
            duration.append(f"{minutes} minutes")
        if seconds > 0:
            duration.append(f"{seconds} seconds")

        return ", ".join(duration)

    @staticmethod
    def parse_number(number: int):
        if number < 10000:
            return f"{number}"

        if number < 1000000:
            return f"{round(number/1000, 2)}K"

        if number < 1000000000:
            return f"{round(number/1000000, 2)}M"

        return f"{round(number/1000000000, 2)}B"

    @staticmethod
    def parse_limited_title(title: str):
        title = title.replace("||", "")

        if len(title) > 72:
            return title[:72] + "..."
        return title

    @staticmethod
    def parse_limited_title_embed(title: str):
        title = title.replace("[", "").replace("]", "").replace("||", "")

        if len(title) > 45:
            return title[:43] + "..."
        return title


class VoiceState:
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.current = None
        self.voice = None
        self.next = asyncio.Event()
        self.songs = SongQueue()

        self.processing = False
        self._loop = False
        self._volume = 0.5
        self.skip_votes = set()

        self.audio_player = bot.loop.create_task(self.audio_player_task())

    @property
    def loop(self):
        return self._loop

    @loop.setter
    def loop(self, value: bool):
        self._loop = value

    @property
    def volume(self):
        return self._volume

    @property
    def is_playing(self):
        return self.voice and self.current

    async def audio_player_task(self):
        while True:
            self.next.clear()

            if not self.loop:
                try:
                    async with timeout(180):
                        self.current = await self.songs.get()
                except asyncio.TimeoutError:
                    return await self.stop()
                self.current.source.volume = self._volume
                self.voice.play(self.current.source, after=self.play_next_song)
            else:
                self.now = discord.FFmpegPCMAudio(
                    self.current.source.stream_url, **YTDLSource.FFMPEG_OPTIONS
                )
                self.voice.play(self.now, after=self.play_next_song)

            if not self.voice:
                return

            await self.next.wait()
            self.current.source.cleanup()

    def play_next_song(self, error=None):
        if error:
            raise VoiceError(str(error))

        self.next.set()

    def skip(self):
        self.skip_votes.clear()

        if self.is_playing:
            self.voice.stop()

    async def stop(self):
        self.songs.clear()
        self.audio_player.cancel()

        if self.voice:
            await self.voice.disconnect()
            self.voice.cleanup()
            self.voice = None

    async def maybe_stop(self):
        if not self.voice:
            self.songs.clear()
            self.audio_player.cancel()


class Song:
    __slots__ = ("source", "requester")

    def __init__(self, source: YTDLSource):
        self.source = source
        self.requester = source.requester

    def create_embed(self, songs, looped):
        if len(songs) == 0:
            queue = "Empty queue."
        else:
            queue = ""
            for i, song in enumerate(songs[0:5], start=0):
                queue += (
                    f"`{i + 1}.` [**{song.source.title_limited_embed}**]"
                    f"({song.source.url} '{song.source.title}')\n"
                )

        if len(songs) > 6:
            queue += f"And {len(songs) - 5} more."

        embed = (
            discord.Embed(
                title="Now playing",
                description=f"```css\n{self.source.title}\n```",
                color=discord.Color.blurple(),
            )
            .set_thumbnail(url=self.source.thumbnail)
            .add_field(name="Duration", value=self.source.duration)
            .add_field(name="Requested by", value=self.requester.mention)
            .add_field(name="\u200b", value="\u200b")
            .add_field(
                name="Looped", value="Currently looped" if looped else "Not looped"
            )
            .add_field(name="URL", value=f"[Click]({self.source.url})")
            .add_field(name="\u200b", value="\u200b")
            .add_field(name="Queue:", value=queue)
            .add_field(name="Views", value=self.source.views)
            .add_field(name="\u200b", value="\u200b")
        )
        return embed


class SongQueue(asyncio.Queue):
    def __getitem__(self, item):
        if isinstance(item, slice):
            return list(islice(self._queue, item.start, item.stop, item.step))

        return self._queue[item]

    def __len__(self):
        return self.qsize()

    def clear(self):
        self._queue.clear()


class music(commands.Cog):
    """Commands related to playing music."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_states = {}

    def cog_unload(self):
        for state in self.voice_states.values():
            self.bot.loop.create_task(state.stop())

    def cog_check(self, ctx):
        return bool(ctx.guild)

    async def cog_before_invoke(self, ctx):
        state = self.voice_states.get(ctx.guild.id)

        if not state:
            state = VoiceState(self.bot)
            self.voice_states[ctx.guild.id] = state

        ctx.voice_state = state

    async def cog_command_error(self, ctx, error: commands.CommandError):
        if getattr(ctx, "voice_state", None):
            ctx.voice_state.processing = False

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before, after):
        """Gets when the bot has been disconnected from voice to do cleanup."""
        if self.bot.user == member:
            if not after.channel:
                guild = member.guild.id
                if guild in self.voice_states:
                    voice_state = self.voice_states.pop(guild)
                    await voice_state.maybe_stop()
            elif before.channel != after.channel:
                voice_state = self.voice_states.get(member.guild.id)
                if voice_state and voice_state.voice:
                    await voice_state.voice.move_to(after.channel)

    async def command_success(self, message):
        try:
            await message.add_reaction("✅")
        except discord.errors.HTTPException:
            pass

    async def command_error(self, message):
        try:
            await message.add_reaction("❌")
        except discord.errors.HTTPException:
            pass

    async def refresh_embed(self, ctx):
        await ctx.send(
            embed=ctx.voice_state.current.create_embed(
                ctx.voice_state.songs, ctx.voice_state.loop
            )
        )

    @commands.command()
    async def pause(self, ctx):
        """Pauses the currently playing song."""
        if not ctx.voice_state.voice:
            await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.dark_red(),
                    title="Not playing anything at the moment.",
                )
            )
            return await self.command_error(ctx.message)

        if ctx.voice_state.is_playing and ctx.voice_state.voice.is_playing():
            ctx.voice_state.voice.pause()
            return await self.command_success(ctx.message)
        await self.command_error(ctx.message)

    @commands.command()
    async def resume(self, ctx):
        """Resumes a currently paused song."""
        if not ctx.voice_state.voice:
            await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.dark_red(),
                    title="Not playing anything at the moment.",
                )
            )
            return await self.command_error(ctx.message)

        if ctx.voice_state.is_playing and ctx.voice_state.voice.is_paused():
            ctx.voice_state.voice.resume()
            return await self.command_success(ctx.message)
        await self.command_error(ctx.message)

    @commands.command()
    async def volume(self, ctx, *, volume: int):
        """Sets the volume of the player.

        volume: int
            The percentage volume
        """
        if not ctx.voice_state.voice:
            await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.dark_red(),
                    title="Not playing anything at the moment.",
                )
            )
            return await self.command_error(ctx.message)

        volume = max(min(volume, 100), 0)

        ctx.voice_state._volume = volume / 100
        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                title=f"Volume of the player set to {volume}%",
            ).set_footer(text="Volume will take effect at the next song")
        )
        await self.command_success(ctx.message)

    @commands.command()
    async def seek(self, ctx, seconds: int):
        """Seeks to a point in a song.

        Seeks from the begining of the song to the amount of seconds inputted.
        """
        if not ctx.voice_state.voice:
            await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.dark_red(),
                    title="Not playing anything at the moment.",
                )
            )
            return await self.command_error(ctx.message)

        data = ctx.voice_state.current.source.data

        if seconds < 0 or seconds > data["duration"]:
            await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.dark_red(),
                    title="Can't seek to a point before or after the song.",
                )
            )
            return await self.command_error(ctx.message)

        song = Song(
            YTDLSource(
                ctx,
                discord.FFmpegPCMAudio(
                    ctx.voice_state.current.source.stream_url,
                    before_options="-reconnect 1 -reconnect_streamed 1 "
                    "-reconnect_delay_max 5",
                    options=f"-vn -loglevel -8 -ss {seconds}",
                ),
                data=data,
            )
        )
        ctx.voice_state.songs._queue.appendleft(song)
        ctx.voice_state.skip()
        await self.command_success(ctx.message)

    @commands.command()
    async def leave(self, ctx):
        """Clears the queue and leaves the voice channel."""
        if not ctx.voice_state.voice:
            await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.dark_red(),
                    title="Not playing anything at the moment.",
                )
            )
            return await self.command_error(ctx.message)

        voice_state = self.voice_states.pop(ctx.guild.id)
        await voice_state.stop()
        await self.command_success(ctx.message)

    @commands.command()
    async def now(self, ctx):
        """Displays the currently playing song."""
        if not ctx.voice_state.current:
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.dark_red(),
                    title="Not playing anything at the moment.",
                )
            )

        await self.refresh_embed(ctx)

    @commands.command()
    async def skip(self, ctx):
        """Vote to skip a song."""
        if not ctx.voice_state.is_playing:
            await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.dark_red(),
                    title="Not playing anything at the moment.",
                )
            )
            return await self.command_error(ctx.message)

        voter = ctx.author

        if (
            voter.guild_permissions.administrator
            or voter == ctx.voice_state.current.requester
        ):
            ctx.voice_state.skip()
            return await self.command_success(ctx.message)

        if voter.id not in ctx.voice_state.skip_votes:
            ctx.voice_state.skip_votes.add(voter.id)
            total_votes = len(ctx.voice_state.skip_votes)

            if total_votes >= len(ctx.author.voice.channel.members) // 2:
                ctx.voice_state.skip()
                return await ctx.message.add_reaction("⏭")
            return await ctx.message.add_reaction("✅")

        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.dark_red(),
                title="You have already voted to skip this song.",
            )
        )
        await self.command_error(ctx.message)

    @commands.command(aliases=["q"])
    async def queue(self, ctx, *, page: int = 1):
        """Shows the player's queue.

        page: int
            The page to display defaulting to the first page.
        """
        if len(ctx.voice_state.songs) == 0:
            await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.dark_red(),
                    title="The queue is empty",
                )
            )
            return await self.command_error(ctx.message)

        queue = ""
        # fmt: off
        songs = ctx.voice_state.songs[(page - 1) * 10: (((page - 1) * 10) + 10)]
        # fmt: on
        for i, song in enumerate(songs, start=(page - 1) * 10):
            queue += (
                f"`{i + 1}.` [**{song.source.title_limited}**]"
                f"({song.source.url} '{song.source.title}')\n"
            )

        embed = discord.Embed(
            description=f"**{len(ctx.voice_state.songs)} tracks:**\n\n{queue}"
        ).set_footer(text=f"Viewing page {page}/{-(-len(ctx.voice_state.songs) // 10)}")
        await ctx.send(embed=embed)
        await self.command_success(ctx.message)

    @commands.command()
    async def clear(self, ctx):
        """Clears the queue."""
        if ctx.voice_state.processing:
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.dark_red(),
                    title="I'm currently processing the previous request.",
                )
            )

        if len(ctx.voice_state.songs) == 0:
            await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.dark_red(),
                    title="The queue is alreay empty.",
                )
            )
            return await self.command_error(ctx.message)

        ctx.voice_state.songs.clear()
        await self.command_success(ctx.message)

    @commands.command()
    async def loop(self, ctx):
        """Loops the currently playing song."""
        await self.command_success(ctx.message)
        if not ctx.voice_state.is_playing:
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.dark_red(),
                    title="Nothing being played at the moment",
                )
            )

        ctx.voice_state.loop = not ctx.voice_state.loop

    @commands.command(aliases=["p"])
    async def play(self, ctx, *, search: str):
        """Plays a song from youtube from a search."""
        if ctx.voice_state.processing:
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.dark_red(),
                    title="I'm currently processing the previous request.",
                )
            )

        if not ctx.voice_state.voice:
            ctx.voice_state.voice = await ctx.author.voice.channel.connect()

        async with ctx.typing():
            data = await YTDLSource.check_type(search, loop=self.bot.loop)
            typ = data.get("_type")
            if "https://www.youtube.com/" in search and "list" in search:
                typ = "playlist_alt"

            if typ in ("playlist", "playlist_alt"):
                ctx.voice_state.processing = True
                skipped = 0

                playlist = await YTDLSource.create_source_playlist(
                    typ, data, loop=self.bot.loop
                )

                for song in playlist:
                    # If the bot has been disconnected in the middle stop adding songs.
                    if not ctx.voice_state.voice:
                        return
                    try:
                        source = await YTDLSource.create_source_single(
                            ctx,
                            song,
                            loop=self.bot.loop,
                        )

                        await ctx.voice_state.songs.put(Song(source))
                    except discord.errors.HTTPException:
                        skipped += 1

                await ctx.send(f"Playlist added. Removed {skipped} songs.")
                ctx.voice_state.processing = False

                return await self.refresh_embed(ctx)

            ctx.voice_state.processing = True
            source = await YTDLSource.create_source_single(
                ctx,
                data,
                loop=self.bot.loop,
            )

            if not ctx.voice_state.voice:
                return

            await ctx.voice_state.songs.put(Song(source))
            await self.command_success(ctx.message)
            ctx.voice_state.processing = False

            await ctx.send(f"Enqueued {source}", delete_after=20)
            await self.refresh_embed(ctx)

    @play.before_invoke
    async def ensure_voice_state(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandError("You are not connected to any voice channel.")

        if ctx.voice_client and ctx.voice_client.channel != ctx.author.voice.channel:
            raise commands.CommandError("Bot is already in a voice channel.")


def setup(bot: commands.Bot) -> None:
    """Starts music cog."""
    bot.add_cog(music(bot))
