import difflib
import logging
import os
import platform
import re
from datetime import datetime
from io import BytesIO, StringIO

import discord
import orjson
import psutil
from discord.ext import commands
from PIL import Image

GIST_REGEX = re.compile(
    r"(?P<host>(http(s)?://gist\.github\.com))/"
    r"(?P<owner>[\w,\-,\_]+)/(?P<id>[\w,\-,\_]+)((/){0,1})"
)


class events(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.DB = bot.DB

    async def poll_check(self, payload):
        """Keeps track of poll results.

        payload: discord.RawReactionActionEvent
            A payload of raw data about the reaction and member.
        """
        if not payload.guild_id or payload.emoji.is_custom_emoji():
            return

        polls = self.DB.main.get(b"polls")

        if not polls:
            return

        polls = orjson.loads(polls)
        guild = str(payload.guild_id)

        if guild not in polls:
            return

        message = str(payload.message_id)

        if message not in polls[guild]:
            return

        if payload.emoji.name not in polls[guild][message]:
            return

        polls[guild][message][payload.emoji.name]["count"] += 1

        self.DB.main.put(b"polls", orjson.dumps(polls))

    async def emoji_submission_check(self, payload):
        """Checks if an emoji submission has passed 8 votes.

        payload: discord.RawReactionActionEvent
            A payload of raw data about the reaction and member.
        """
        emojis = self.DB.main.get(b"emoji_submissions")

        if not payload.emoji.is_custom_emoji():
            return

        if not emojis or payload.emoji.name.lower() != "upvote":
            return

        emojis = orjson.loads(emojis)
        message_id = str(payload.message_id)

        if message_id not in emojis:
            return

        if payload.user_id not in emojis[message_id]["users"]:
            emojis[message_id]["users"].append(payload.user_id)

        if len(emojis[message_id]["users"]) >= 8:
            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            file = message.attachments[0]
            file = BytesIO(await file.read())
            file = Image.open(file)
            file.thumbnail((256, 256), Image.LANCZOS)

            imgByteArr = BytesIO()
            file.save(imgByteArr, format="PNG")
            file = imgByteArr.getvalue()

            name = emojis[message_id]["name"]

            if not discord.utils.get(message.guild.emojis, name=name):
                emoji = await message.guild.create_custom_emoji(name=name, image=file)
                await message.add_reaction(emoji)

            emojis.pop(message_id)

        self.DB.main.put(b"emoji_submissions", orjson.dumps(emojis))

    async def reaction_role_check(self, payload):
        """Checks if a reaction was on a reaction role message.

        payload: discord.RawReactionActionEvent
            A payload of raw data about the reaction and member.
        """
        reaction_roles = self.DB.rrole.get(str(payload.message_id).encode())

        if not reaction_roles:
            return

        reaction_roles = orjson.loads(reaction_roles)

        if str(payload.emoji) in reaction_roles:
            role_id = int(reaction_roles[str(payload.emoji)])
        elif payload.emoji.name in reaction_roles:
            role_id = int(reaction_roles[payload.emoji.name])
        else:
            return

        guild = self.bot.get_guild(payload.guild_id)

        if not guild:
            return

        role = guild.get_role(role_id)

        if not role:
            return

        if payload.event_type == "REACTION_REMOVE":
            member = guild.get_member(payload.user_id)
            return await member.remove_roles(role)

        if not payload.member:
            return

        await payload.member.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Gives roles based off reaction added if message in reaction_roles.json.

        payload: discord.RawReactionActionEvent
            A payload of raw data about the reaction and member.
        """
        if payload.member == self.bot.user:
            return

        await self.emoji_submission_check(payload)
        await self.poll_check(payload)
        await self.reaction_role_check(payload)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """Removes roles based off reaction added if message in reaction_roles.json.

        payload: discord.RawReactionActionEvent
            A payload of raw data about the reaction and member.
        """
        await self.reaction_role_check(payload)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """The event called when a reaction is added to a message in the cache.

        reaction: discord.Reaction
        user: Union[discord.User, discord.Member]
        """
        if not reaction.is_custom_emoji():
            return

        if reaction.message.author == user:
            return

        time_since = (
            discord.utils.utcnow() - reaction.message.created_at
        ).total_seconds()

        if time_since > 1800:
            return

        if reaction.emoji.name.lower() == "downvote":
            await self.DB.add_karma(reaction.message.author.id, -1)
        elif reaction.emoji.name.lower() == "upvote":
            await self.DB.add_karma(reaction.message.author.id, 1)

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        """The event called when a reaction is removed from a message in the cache.

        reaction: discord.Reaction
        user: Union[discord.User, discord.Member]
        """
        if not reaction.is_custom_emoji():
            return

        if reaction.message.author == user:
            return

        time_since = (
            discord.utils.utcnow() - reaction.message.created_at
        ).total_seconds()

        if time_since > 1800:
            return

        if reaction.emoji.name.lower() == "downvote":
            await self.DB.add_karma(reaction.message.author.id, 1)
        elif reaction.emoji.name.lower() == "upvote":
            await self.DB.add_karma(reaction.message.author.id, -1)

    @commands.Cog.listener()
    async def on_reaction_clear(self, message, reactions):
        """The event called when the reactions on a message are cleared.

        message: discord.Message
        reactions: List[discord.Reaction]
        """
        if await self.DB.get_blacklist(message.author.id, message.guild.id) == b"1":
            try:
                await message.add_reaction("<:downvote:766414744730206228>")
            except discord.errors.HTTPException:
                pass

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Disconnects a member from voice if they are downvoted.

        member: discord.Member
            The member.
        before: discord.VoiceState
            The old voice state.
        after: discord.VoiceState
            The new voice state.
        """
        if not after.channel:
            return

        if await self.DB.get_blacklist(member.id, member.guild.id) == b"1":
            await member.edit(voice_channel=None)
            await self.DB.add_karma(member.id, -1)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """Logs edited messages to the logs channel.

        before: discord.Message
            The old message.
        after: discord.Message
            The new message.
        """
        if (
            not before.guild
            or self.DB.main.get(f"{after.guild.id}-logging".encode())
            or not after.content
            or before.content == after.content
            or after.author == self.bot.user
        ):
            return

        member_id = f"{before.guild.id}-{before.author.id}".encode()
        edited = self.DB.edited.get(member_id)

        if not edited:
            edited = {}
        else:
            edited = orjson.loads(edited)

        date = str(int(datetime.now().timestamp()))
        edited[date] = [before.content, after.content]
        self.DB.edited.put(member_id, orjson.dumps(edited))
        self.DB.main.put(
            f"{before.guild.id}-editsnipe_message".encode(),
            orjson.dumps([before.content, after.content, before.author.display_name]),
        )

        if after.content.startswith("https"):
            return

        channel = discord.utils.get(after.guild.channels, name="logs")

        if not channel:
            return

        # Replaces backticks with a backtick and a zero width space
        before.content = before.content.replace("`", "`\u200b")
        after.content = after.content.replace("`", "`\u200b")

        embed = discord.Embed(
            title=f"{before.author.display_name} edited:",
            color=discord.Color.blurple(),
        )
        embed.add_field(name="From:", value=f"```{before.content}```")
        embed.add_field(name="To:", value=f"```{after.content}```")
        embed.set_footer(text=f"Member ID: {before.author.id}")

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """Logs deleted messages to the logs channel.

        message: discord.Message
        """
        if (
            not message.guild
            or self.DB.main.get(f"{message.guild.id}-logging".encode())
            or message.author == self.bot.user
        ):
            return

        attachments = [
            attach.url
            for attach in message.attachments
            if attach.content_type.startswith("image/")
        ]

        if not message.content and not attachments:
            return

        content = "{}\n{}".format(
            (message.content.replace("`", "`\u200b") if message.content else ""),
            "\n".join(attachments),
        )

        member_id = f"{message.guild.id}-{message.author.id}".encode()
        deleted = self.DB.deleted.get(member_id)

        if not deleted:
            deleted = {}
        else:
            deleted = orjson.loads(deleted)

        date = str(int(datetime.now().timestamp()))
        deleted[date] = message.content

        self.DB.deleted.put(member_id, orjson.dumps(deleted))
        self.DB.main.put(
            f"{message.guild.id}-snipe_message".encode(),
            orjson.dumps([content, message.author.display_name]),
        )

        channel = discord.utils.get(message.guild.channels, name="logs")

        if not channel:
            return

        embed = discord.Embed(
            title=f"{message.author.display_name} deleted:",
            description=f"```\n{content}```",
            color=discord.Color.blurple(),
        )
        embed.set_footer(text=f"Member ID: {message.author.id}")
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Downvotes blacklisted members.

        message: discord.Message
        """
        if message.guild:
            guild = message.guild.id

            key = f"{guild}-{message.author.id}".encode()
            count = self.DB.message_count.get(key)

            if count:
                count = int(count) + 1
            else:
                count = 1

            self.DB.message_count.put(key, str(count).encode())

            if key == b"815732601302155275-190747796452671488":
                if message.content and not message.content.startswith("."):
                    messages = orjson.loads(self.DB.main.get(b"justins-messages"))
                    messages.append(message.content)
                    self.DB.main.put(b"justins-messages", orjson.dumps(messages))
        else:
            guild = None

        if await self.DB.get_blacklist(message.author.id, guild) == b"1":
            try:
                await message.add_reaction("<:downvote:766414744730206228>")
            except discord.errors.HTTPException:
                pass

        match = GIST_REGEX.search(message.content)

        if not message.author.bot and match:
            gist_id = match.group(5)
            url = f"https://api.github.com/gists/{gist_id}"
            data = await self.bot.get_json(url)

            if not data:
                return

            files = []

            for file in data["files"].values():
                files.append(discord.File(StringIO(file["content"]), file["filename"]))

            await message.channel.send(files=files)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Puts members nickname history into the db.

        before: discord.Member
            The member object before the update.
        after: discord.Member
            The member object after the update.
        """
        if before.nick == after.nick:
            return

        member_id = str(after.id).encode()

        nicks = self.DB.nicks.get(member_id)

        if not nicks:
            nicks = {"nicks": {}, "names": {}}
        else:
            nicks = orjson.loads(nicks)

        now = str(datetime.now())[:-7]

        if "current" in nicks["nicks"]:
            date = nicks["nicks"]["current"][1]
        else:
            date = now

        nicks["nicks"][date] = before.nick
        nicks["nicks"]["current"] = [after.nick, now]

        self.DB.nicks.put(member_id, orjson.dumps(nicks))

    @commands.Cog.listener()
    async def on_user_update(self, before, after):
        """Puts users name history into the db.

        before: discord.User
            The user object before the update.
        after: discord.User
            The user object after the update.
        """
        if before.name == after.name:
            return

        member_id = str(after.id).encode()

        names = self.DB.nicks.get(member_id)

        if not names:
            names = {"nicks": {}, "names": {}}
        else:
            names = orjson.loads(names)

        now = str(datetime.now())[:-7]

        if "current" in names["names"]:
            date = names["names"]["current"][1]
        else:
            date = now

        names["names"][date] = before.name
        names["names"]["current"] = [after.name, now]

        self.DB.nicks.put(member_id, orjson.dumps(names))

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Checks which invite someone has joined from.

        member: discord.Member
        """
        for invite in await member.guild.invites():
            key = f"{invite.code}-{invite.guild.id}"
            uses = self.DB.invites.get(key.encode())

            if not uses:
                self.DB.invites.put(key.encode(), str(invite.uses).encode())
                continue

            if invite.uses > int(uses):
                self.DB.invites.put(str(member.id).encode(), invite.code.encode())

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Logs when a member leaves a guild.

        member: discord.Member
        """
        if self.DB.main.get(f"{member.guild.id}-logging".encode()):
            return

        channel = discord.utils.get(member.guild.channels, name="logs")

        if not channel:
            return

        embed = discord.Embed(color=discord.Color.blurple())
        embed.description = (
            f"```{member.display_name} left the server\n\nMember ID: {member.id}```"
        )

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        """Puts invites into the db to get who used the invite.

        invite: discord.Invite
        """
        key = f"{invite.code}-{invite.guild.id}"
        self.DB.invites.put(key.encode(), str(invite.uses).encode())

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        """Removes invites from the db when they have been deleted.

        invite: discord.Invite
        """
        self.DB.invites.delete(f"{invite.code}-{invite.guild.id}".encode())

    @staticmethod
    async def can_run(ctx, command):
        try:
            return await command.can_run(ctx)
        except commands.errors.CommandError:
            return False

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """The event triggered when an error is raised while invoking a command.

        error: Exception
        """
        if hasattr(ctx.command, "on_error"):
            return

        cog = ctx.cog
        if cog:
            attr = f"_{cog.__class__.__name__}__error"
            if hasattr(cog, attr):
                return

        error = getattr(error, "original", error)

        if str(error).startswith("The check functions") or str(error).startswith(
            "The global check"
        ):
            return

        embed = discord.Embed(color=discord.Color.dark_red())

        if isinstance(error, commands.errors.CommandNotFound):
            if ctx.message.content.startswith(ctx.prefix * 2):
                return

            invoked = ctx.message.content.split()[0].removeprefix(ctx.prefix)

            all_commands = [
                str(command)
                for command in self.bot.walk_commands()
                if not command.hidden and await self.can_run(ctx, command)
            ]

            matches = difflib.get_close_matches(invoked, all_commands, cutoff=0.5)

            if not matches:
                return

            message = "Did you mean:\n\n" + "\n".join(matches)
            embed.title = f"Command {invoked} not found."

        elif isinstance(error, commands.errors.CommandOnCooldown):
            cooldown = int(error.cooldown.get_retry_after())
            message = "You are on cooldown. Try again in {} hours {} minutes and {} seconds".format(
                cooldown // 3600, (cooldown % 3600) // 60, (cooldown % 3600) % 60
            )

        elif isinstance(error, discord.Forbidden):
            message = "I do not have the required permissions to run this command."

        elif isinstance(
            error, (commands.BadArgument, commands.errors.MissingRequiredArgument)
        ):
            ctx.command.reset_cooldown(ctx)
            message = (
                f"{error}\n\nUsage:\n{ctx.prefix}{ctx.command} {ctx.command.signature}"
            )

        elif isinstance(error, commands.errors.BotMissingPermissions):
            message = f"{self.bot.user.name} is missing required permissions: {error.missing_perms}"

        else:
            logging.getLogger("discord").warning(
                f"Unhandled Error: {ctx.command.qualified_name}, Error: {error}, Type: {type(error)}"
            )
            message = error

        if not str(message):
            logging.getLogger("discord").warning(
                f"{ctx.command.qualified_name}, Error: {error}"
            )
            return

        embed.description = f"```{message}```"
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_ready(self):
        """Called when the bot is done preparing the data received from Discord."""
        if not hasattr(self.bot, "uptime"):
            start_time = datetime.now().timestamp()
            boot_time = start_time - psutil.Process(os.getpid()).create_time()

            self.bot.uptime = start_time
            boot_times = self.DB.main.get(b"boot_times")

            if boot_times:
                boot_times = orjson.loads(boot_times)
            else:
                boot_times = []

            boot_times.append(round(boot_time, 5))
            self.DB.main.put(b"boot_times", orjson.dumps(boot_times))

            # Wipe the cache and polls as we have no way of knowing if they have expired
            self.DB.main.put(b"cache", b"{}")
            self.DB.main.delete(b"polls")

            print(
                f"Logged in as {self.bot.user.name}\n"
                f"Pycord version: {discord.__version__}\n"
                f"Python version: {platform.python_version()}\n"
                f"Running on: {platform.system()} {platform.release()}({os.name})\n"
                f"Boot time: {boot_time:.3f}s\n"
                "-------------------"
            )

    async def bot_check_once(self, ctx):
        """Checks if a user blacklisted and the if the command is disabled."""
        if ctx.author.id in self.bot.owner_ids:
            return True

        if ctx.guild:
            disabled = self.DB.main.get(f"{ctx.guild.id}-disabled_channels".encode())

            if (
                disabled
                and ctx.command.name != "disable_channel"
                and str(ctx.guild.id) in (disabled := orjson.loads(disabled))
            ):
                if ctx.channel.id in disabled[str(ctx.guild.id)]:
                    return False

            if ctx.guild and self.DB.main.get(
                f"{ctx.guild.id}-t-{ctx.command}".encode()
            ):
                await ctx.send(
                    embed=discord.Embed(
                        color=discord.Color.red(), description="```Command disabled```"
                    )
                )
                return False

        if await self.DB.get_blacklist(
            ctx.author.id, ctx.guild.id if ctx.guild else None
        ):
            await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.red(),
                    description="```You are blacklisted from using commands```",
                )
            )
            return False

        return True

    @commands.Cog.listener()
    async def on_command(self, ctx):
        """Resets command cooldown for owners."""
        logging.getLogger("discord").info(
            f"{ctx.author.id} ran the command {ctx.command.qualified_name}"
        )
        if ctx.author.id in self.bot.owner_ids:
            ctx.command.reset_cooldown(ctx)


def setup(bot: commands.Bot) -> None:
    """Starts events cog."""
    bot.add_cog(events(bot))
