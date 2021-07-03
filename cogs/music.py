import discord
from discord.ext import commands
import asyncio
import functools
import itertools
import random
import youtube_dl
import async_timeout

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
        "noplaylist": True,
        "nocheckcertificate": True,
        "ignoreerrors": False,
        "logtostderr": False,
        "quiet": True,
        "no_warnings": True,
        "default_search": "ytsearch",
        "source_address": "0.0.0.0",
    }

    FFMPEG_OPTIONS = {
        "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
        "options": "-vn",
    }

    ytdl = youtube_dl.YoutubeDL(YTDL_OPTIONS)
    ytdl.cache.remove()

    def __init__(
        self,
        ctx: commands.Context,
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
        self.uploader_url = data.get("uploader_url")
        date = data.get("upload_date")
        self.upload_date = date[6:8] + "." + date[4:6] + "." + date[0:4]
        self.title = data.get("title")
        self.thumbnail = data.get("thumbnail")
        self.description = data.get("description")
        self.duration = self.parse_duration(int(data.get("duration")))
        self.tags = data.get("tags")
        self.url = data.get("webpage_url")
        self.views = data.get("view_count")
        self.likes = data.get("like_count")
        self.dislikes = data.get("dislike_count")
        self.stream_url = data.get("url")

    def __str__(self):
        return f"**{self.title}** by **{self.uploader}**"

    @classmethod
    async def create_source(
        cls, ctx: commands.Context, search: str, *, loop: asyncio.BaseEventLoop = None
    ):
        loop = loop or asyncio.get_event_loop()

        partial = functools.partial(
            cls.ytdl.extract_info, search, download=False, process=False
        )
        data = await loop.run_in_executor(None, partial)

        if data is None:
            raise YTDLError(f"Couldn't find anything that matches {search}")

        if "entries" not in data:
            process_info = data
        else:
            process_info = None
            for entry in data["entries"]:
                if entry:
                    process_info = entry
                    break

            if process_info is None:
                raise YTDLError(f"Couldn't find anything that matches {search}")

        webpage_url = process_info["webpage_url"]
        partial = functools.partial(cls.ytdl.extract_info, webpage_url, download=False)
        processed_info = await loop.run_in_executor(None, partial)

        if processed_info is None:
            raise YTDLError(f"Couldn't fetch {webpage_url}")

        if "entries" not in processed_info:
            info = processed_info
        else:
            info = None
            while info is None:
                try:
                    info = processed_info["entries"].pop(0)
                except IndexError:
                    raise YTDLError(f"Couldn't retrieve any matches for {webpage_url}")

        if info["duration"] > 1800:
            raise YTDLError("Video is longer than 30 minutes")

        return cls(
            ctx, discord.FFmpegPCMAudio(info["url"], **cls.FFMPEG_OPTIONS), data=info
        )

    @staticmethod
    def parse_duration(duration: int):
        if duration > 0:
            minutes, seconds = (duration // 60, duration % 60)
            hours, minutes = (minutes // 60, minutes % 60)
            days, hours = (hours // 24, hours % 24)

            duration = []
            if days > 0:
                duration.append(str(days))
            if hours > 0:
                duration.append(str(hours))
            if minutes > 0:
                duration.append(str(minutes))
            if seconds >= 0:
                duration.append(f"{seconds:0>2}")

            value = ":".join(duration)

        elif duration == 0:
            value = "LIVE"

        return value


class Song:
    __slots__ = ("source", "requester")

    def __init__(self, source: YTDLSource):
        self.source = source
        self.requester = source.requester

    def create_embed(self):
        if self.source.duration == "":
            DURATION = "/"
        else:
            DURATION = self.source.duration
        embed = (
            discord.Embed(
                title="Now playing",
                description=f"```css\n{self.source.title}\n```",
                color=discord.Color.blurple(),
            )
            .add_field(name="Duration", value=DURATION)
            .add_field(name="Requested by", value=self.requester.mention)
            .add_field(
                name="Uploader",
                value=f"[{self.source.uploader}]({self.source.uploader_url})",
            )
            .add_field(name="URL", value=f"[Click]({self.source.url})")
            .set_thumbnail(url=self.source.thumbnail)
            .set_author(name=self.requester.name, icon_url=self.requester.avatar_url)
        )
        return embed


class SongQueue(asyncio.Queue):
    def __getitem__(self, item):
        if isinstance(item, slice):
            return list(itertools.islice(self._queue, item.start, item.stop, item.step))
        return self._queue[item]

    def __iter__(self):
        return self._queue.__iter__()

    def __len__(self):
        return self.qsize()

    def clear(self):
        self._queue.clear()

    def shuffle(self):
        random.shuffle(self._queue)

    def remove(self, index: int):
        del self._queue[index]


class VoiceState:
    def __init__(self, bot: commands.Bot, ctx: commands.Context):
        self.bot = bot
        self._ctx = ctx

        self.current = None
        self.voice = None
        self.next = asyncio.Event()
        self.songs = SongQueue()
        self.exists = True

        self._loop = False
        self._volume = 0.5
        self.skip_votes = set()

        self.audio_player = bot.loop.create_task(self.audio_player_task())

    def __del__(self):
        self.audio_player.cancel()

    @property
    def loop(self):
        return self._loop

    @loop.setter
    def loop(self, value: bool):
        self._loop = value

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value: float):
        self._volume = value

    @property
    def is_playing(self):
        return self.voice and self.current

    async def audio_player_task(self):
        while True:
            self.next.clear()
            self.now = None

            if self.loop is False:
                try:
                    async with async_timeout.timeout(120):
                        self.current = await self.songs.get()
                except asyncio.TimeoutError:
                    self.bot.loop.create_task(self.stop())
                    self.exists = False
                    return

                self.current.source.volume = self._volume
                self.voice.play(self.current.source, after=self.play_next_song)
                await self.current.source.channel.send(
                    embed=self.current.create_embed()
                )

            elif self.loop is True:
                self.now = discord.FFmpegPCMAudio(
                    self.current.source.stream_url, **YTDLSource.FFMPEG_OPTIONS
                )
                self.voice.play(self.now, after=self.play_next_song)

            await self.next.wait()

    def play_next_song(self, error=None):
        if error:
            raise VoiceError(str(error))

        if self.is_playing and len(self.voice.channel.members) <= 1:
            self.bot.loop.create_task(self.stop())

        self.next.set()

    def skip(self):
        self.skip_votes.clear()

        if self.is_playing:
            self.voice.stop()

    async def stop(self):
        self.songs.clear()

        if self.voice:
            await self.voice.disconnect()
            self.voice = None


class music(commands.Cog):
    """Commands related to music."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_states = {}

    def get_voice_state(self, ctx: commands.Context):
        state = self.voice_states.get(ctx.guild.id)
        if not state or not state.exists:
            state = VoiceState(self.bot, ctx)
            self.voice_states[ctx.guild.id] = state

        return state

    def cog_unload(self):
        for state in self.voice_states.values():
            self.bot.loop.create_task(state.stop())

    def cog_check(self, ctx: commands.Context):
        if not ctx.guild:
            raise commands.NoPrivateMessage(self.__cog_name__)

        return True

    async def cog_before_invoke(self, ctx: commands.Context):
        ctx.voice_state = self.get_voice_state(ctx)

    @commands.command(name="join")
    async def _join(self, ctx: commands.Context):
        """Joins your current voice channel."""
        destination = ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            return

        ctx.voice_state.voice = await destination.connect()

    @commands.command(name="summon")
    async def _summon(
        self, ctx: commands.Context, *, channel: discord.VoiceChannel = None
    ):
        """Summons the bot to a voice channel.

        channel: discord.VoiceChannel
            The channel to join defaulting to your voice channel.
        """
        if not channel and not ctx.author.voice:
            raise VoiceError(
                "You are neither connected to a voice channel nor specified a channel to join."
            )

        destination = channel or ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            return

        ctx.voice_state.voice = await destination.connect()

    @commands.command(name="leave", aliases=["disconnect"])
    async def _leave(self, ctx: commands.Context):
        """Clears the queue and leaves the voice channel."""
        if not ctx.voice_state.voice:
            return await ctx.send("Not connected to any voice channel.")

        await ctx.voice_state.stop()
        del self.voice_states[ctx.guild.id]

    @commands.command(name="volume")
    async def _volume(self, ctx: commands.Context, *, volume: int):
        """Sets the volume of the player.

        volume: int
            The volume to be set from 0% to 100%.
        """
        if not ctx.voice_state.is_playing:
            return await ctx.send("Nothing being played at the moment.")

        if 0 > volume > 100:
            return await ctx.send("Volume must be between 0 and 100")

        ctx.voice_state.current.source.volume = volume / 100
        await ctx.send(f"Volume of the player set to {volume}%")

    @commands.command(name="now", aliases=["current", "playing", "n"])
    async def _now(self, ctx: commands.Context):
        """Displays the currently playing song."""
        await ctx.send(embed=ctx.voice_state.current.create_embed())

    @commands.command(name="pause", aliases=["pa"])
    async def _pause(self, ctx: commands.Context):
        """Pauses the currently playing song."""
        if ctx.voice_state.voice.is_playing():
            ctx.voice_state.voice.pause()
            await ctx.message.add_reaction("⏯")

    @commands.command(name="resume", aliases=["re", "res"])
    async def _resume(self, ctx: commands.Context):
        """Resumes a currently paused song."""
        if ctx.voice_state.voice.is_paused():
            ctx.voice_state.voice.resume()
            await ctx.message.add_reaction("⏯")

    @commands.command(name="stop")
    async def _stop(self, ctx: commands.Context):
        """Stops playing song and clears the queue."""
        ctx.voice_state.songs.clear()

        if ctx.voice_state.is_playing:
            ctx.voice_state.voice.stop()
            await ctx.message.add_reaction("⏹")

    @commands.command(name="skip", aliases=["s", "sk"])
    async def _skip(self, ctx: commands.Context):
        """Vote to skip a song."""
        if not ctx.voice_state.is_playing:
            return await ctx.send("Not playing any music right now...")

        voter = ctx.author
        if (
            voter == ctx.voice_state.current.requester
            or voter.guild_permissions.administrator
        ):
            await ctx.message.add_reaction("⏭")
            ctx.voice_state.loop = False
            ctx.voice_state.skip()

        elif voter.id not in ctx.voice_state.skip_votes:
            ctx.voice_state.skip_votes.add(voter.id)
            total_votes = len(ctx.voice_state.skip_votes)

            if total_votes >= len(ctx.author.voice.channel.members) // 2:
                await ctx.message.add_reaction("⏭")
                ctx.voice_state.loop = False
                ctx.voice_state.skip()
            else:
                await ctx.send(f"Skip vote added, currently at **{total_votes}/1**")

        else:
            await ctx.send("You have already voted to skip this song.")

    @commands.command(name="queue", aliases=["q"])
    async def _queue(self, ctx: commands.Context, *, page: int = 1):
        """Shows the player's queue.

        page: int
            The page to display defaulting to the first page.
        """
        if len(ctx.voice_state.songs) == 0 and not ctx.voice_state.current:
            return await ctx.send("Empty queue.")

        items_per_page = 10
        # -(-3//2) == 2, just gets the ceil
        pages = -(-(len(ctx.voice_state.songs) + 1) // items_per_page)

        start = (page - 1) * items_per_page
        end = start + items_per_page

        queue = "`Playing` [**{0.title}**]({0.url})\n".format(
            ctx.voice_state.current.source
        )
        for i, song in enumerate(ctx.voice_state.songs[start:end], start=start + 1):
            queue += f"`{i}.` [**{song.source.title}**]({song.source.url})\n"

        embed = discord.Embed(
            description=f"**{len(ctx.voice_state.songs) + 1} tracks:**\n\n{queue}"
        ).set_footer(text=f"Viewing page {page}/{pages}")
        await ctx.send(embed=embed)

    @commands.command(name="shuffle")
    async def _shuffle(self, ctx: commands.Context):
        """Shuffles the queue."""
        if len(ctx.voice_state.songs) == 0:
            return await ctx.send("Empty queue.")

        ctx.voice_state.songs.shuffle()
        await ctx.message.add_reaction("✅")

    @commands.command(name="remove")
    async def _remove(self, ctx: commands.Context, index: int):
        """Removes a song from the queue at a given index.

        index: int
            The index of the song to remove.
        """
        if len(ctx.voice_state.songs) == 0:
            return await ctx.send("Empty queue.")

        ctx.voice_state.songs.remove(index - 1)
        await ctx.message.add_reaction("✅")

    @commands.command(name="loop")
    async def _loop(self, ctx: commands.Context):
        """Loops the currently playing song."""
        if not ctx.voice_state.is_playing:
            return await ctx.send("Nothing being played at the moment.")

        ctx.voice_state.loop = not ctx.voice_state.loop
        await ctx.message.add_reaction("✅")

    @commands.command(name="play", aliases=["p"])
    async def _play(self, ctx: commands.Context, *, search: str):
        """Plays a song.

        searcch: str
            The song to search for.
        """
        async with ctx.typing():
            try:
                source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop)
            except YTDLError as e:
                return await ctx.send(
                    embed=discord.Embed(
                        color=discord.Color.blurple(), description=f"```{e}```"
                    )
                )

            if not ctx.voice_state.voice:
                await ctx.invoke(self._join)

            song = Song(source)
            await ctx.voice_state.songs.put(song)
            await ctx.send(f"Enqueued {source}")

    @_join.before_invoke
    @_play.before_invoke
    async def ensure_voice_state(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandError("You are not connected to any voice channel.")

        if ctx.voice_client and ctx.voice_client.channel != ctx.author.voice.channel:
            raise commands.CommandError("Bot is already in a voice channel.")


def setup(bot: commands.Bot) -> None:
    """Starts music cog."""
    bot.add_cog(music(bot))
