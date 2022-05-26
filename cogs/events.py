import difflib
import logging
import os
import platform
import re
from datetime import datetime, timedelta
from io import StringIO

import discord
import orjson
import psutil
from discord.ext import commands

GIST_REGEX = re.compile(
    r"(?P<host>(http(s)?://gist\.github\.com))/"
    r"(?P<owner>[\w,\-,\_]+)/(?P<id>[\w,\-,\_]+)((/){0,1})"
)


class DeleteButton(discord.ui.View):
    def __init__(self, author: discord.Member):
        super().__init__()
        self.author = author

    @discord.ui.button(label="X", style=discord.ButtonStyle.red)
    async def delete(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user == self.author:
            if interaction.message:
                await interaction.message.delete()


class CooldownByContent(commands.CooldownMapping):
    def _bucket_key(self, message: discord.Message) -> tuple[int, str]:
        return (message.channel.id, message.content)


class SpamChecker:
    """Checks if someone is spamming via the below criteria
    1) If a user has spammed more than 10 times in 12 seconds
    2) If the content has been spammed 15 times in 17 seconds.
    3) If a user has mentioned 40 people in 17 seconds.
    """

    def __init__(self):
        self.by_content = CooldownByContent.from_cooldown(
            15, 17.0, commands.BucketType.member
        )
        self.by_user = commands.CooldownMapping.from_cooldown(
            10, 12.0, commands.BucketType.user
        )

        self.by_mentions = commands.CooldownMapping.from_cooldown(
            40, 12, commands.BucketType.member
        )

    def is_spamming(self, message: discord.Message) -> bool:
        if message.guild is None:
            return False

        current = message.created_at.timestamp()

        user_bucket = self.by_user.get_bucket(message)
        if user_bucket.update_rate_limit(current):
            return True

        content_bucket = self.by_content.get_bucket(message)
        if content_bucket.update_rate_limit(current):
            return True

        if self.is_mention_spam(message, current):
            return True

        return False

    def is_mention_spam(self, message: discord.Message, current: float) -> bool:
        mention_bucket = self.by_mentions.get_bucket(message, current)
        mention_count = sum(
            not m.bot and m.id != message.author.id for m in message.mentions
        )
        mention_bucket._tokens -= mention_count - 1

        return mention_bucket.update_rate_limit(current) is not None


class events(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.DB = bot.DB
        self.spam_checker = SpamChecker()

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

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Gives roles based off reaction added if message in reaction_roles.json.

        payload: discord.RawReactionActionEvent
            A payload of raw data about the reaction and member.
        """
        if payload.member == self.bot.user:
            return

        await self.poll_check(payload)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """The event called when a reaction is added to a message in the cache.

        reaction: discord.Reaction
        user: Union[discord.User, discord.Member]
        """
        if not reaction.is_custom_emoji() or reaction.message.author == user:
            return

        time_since = (
            discord.utils.utcnow() - reaction.message.created_at
        ).total_seconds()

        if time_since > 1800:
            return

        reaction_name = reaction.emoji.name.lower()

        if reaction_name == "downvote":
            self.DB.add_karma(reaction.message.author.id, -1)
        elif reaction_name == "upvote":
            self.DB.add_karma(reaction.message.author.id, 1)

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        """The event called when a reaction is removed from a message in the cache.

        reaction: discord.Reaction
        user: Union[discord.User, discord.Member]
        """
        if not reaction.is_custom_emoji() or reaction.message.author == user:
            return

        time_since = (
            discord.utils.utcnow() - reaction.message.created_at
        ).total_seconds()

        if time_since > 1800:
            return

        reaction_name = reaction.emoji.name.lower()

        if reaction_name == "downvote":
            self.DB.add_karma(reaction.message.author.id, 1)
        elif reaction_name == "upvote":
            self.DB.add_karma(reaction.message.author.id, -1)

    @commands.Cog.listener()
    async def on_reaction_clear(self, message, reactions):
        """The event called when the reactions on a message are cleared.

        message: discord.Message
        reactions: List[discord.Reaction]
        """
        if self.DB.get_blacklist(message.author.id, message.guild.id) == b"1":
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

        if self.DB.get_blacklist(member.id, member.guild.id) == b"1":
            await member.edit(voice_channel=None)
            self.DB.add_karma(member.id, -1)

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

        time_sent = str(((message.id >> 22) + 1420070400000) // 1000)
        deleted[time_sent] = message.content

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
        guild_id = message.guild.id if message.guild else None

        if self.DB.get_blacklist(message.author.id, guild_id) == b"1":
            try:
                await message.add_reaction("<:downvote:766414744730206228>")
            except discord.errors.HTTPException:
                pass

        if not guild_id:
            return

        anti_spam = self.DB.main.get(f"anti_spam-{guild_id}".encode())
        channel = message.channel.name.lower()

        if anti_spam and channel != "bot" and self.spam_checker.is_spamming(message):
            try:
                await message.author.timeout(
                    until=datetime.now() + timedelta(hours=1), reason="Spamming"
                )
            except (discord.errors.Forbidden, discord.errors.HTTPException):
                pass

        key = f"{guild_id}-{message.author.id}".encode()
        count = self.DB.message_count.get(key)
        # Add 1 to count and put it back into the database
        self.DB.message_count.put(key, str(int(count) + 1).encode() if count else b"1")

        if key == b"815732601302155275-190747796452671488":
            if message.content and not message.content.startswith("."):
                messages = orjson.loads(self.DB.main.get(b"justins-messages"))
                messages.append(message.content)
                self.DB.main.put(b"justins-messages", orjson.dumps(messages))

        match = GIST_REGEX.search(message.content)

        if not message.author.bot and match:
            gist_id = match.group(5)
            url = f"https://api.github.com/gists/{gist_id}"
            data = await self.bot.get_json(url)

            if not data:
                return

            # We just want the first value in the dictionary
            file = data["files"].values().__iter__().__next__()
            content = file["content"]
            filename = file["filename"]
            extension = filename.split(".")[-1]

            if file["size"] + len(extension) > 1992:
                return await message.channel.send(
                    file=discord.File(StringIO(content), filename)
                )
            await message.channel.send(f"```{extension}\n{content}```")

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
            invite_key = f"{invite.code}-{invite.guild.id}"
            member_key = f"{member.id}-{invite.guild.id}"

            uses = self.DB.invites.get(invite_key.encode())

            if not uses:
                self.DB.invites.put(invite_key.encode(), str(invite.uses).encode())
                continue

            if invite.uses > int(uses):
                self.DB.invites.put(member_key.encode(), invite.code.encode())

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

        error = getattr(error, "original", error)

        message = str(error)
        if message.startswith("The check functions") or message.startswith(
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
            logging.log(
                50,
                f"Unhandled Error: {ctx.command.qualified_name}, Error: {error}, Type: {type(error)}",
            )

        if not str(message):
            logging.log(50, f"{ctx.command.qualified_name}, Error: {error}")
            return

        embed.description = f"```{message}```"
        await ctx.send(embed=embed, view=DeleteButton(ctx.author))

    @commands.Cog.listener()
    async def on_ready(self):
        """Called when the bot is done preparing the data received from Discord."""
        if not hasattr(self.bot, "uptime"):
            start_time = datetime.now().timestamp()
            boot_time = start_time - psutil.Process(os.getpid()).create_time()

            self.bot.uptime = start_time

            boot_times = self.DB.main.get(b"boot_times")
            boot_times = orjson.loads(boot_times) if boot_times else []
            boot_times.append(round(boot_time, 5))

            self.DB.main.put(b"boot_times", orjson.dumps(boot_times))

            # Wipe the polls as we have no way of knowing if they have expired
            self.DB.main.delete(b"polls")

            self.bot.get_cog("admin").on_ready()

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
            guild_id = ctx.guild.id
            disabled = self.DB.main.get(f"{guild_id}-disabled_channels".encode())

            if disabled and ctx.command.name != "disable_channel":
                if ctx.channel.id in orjson.loads(disabled):
                    return False

            if self.DB.main.get(f"{guild_id}-t-{ctx.command}".encode()):
                await ctx.send(
                    embed=discord.Embed(
                        color=discord.Color.red(), description="```Command disabled```"
                    )
                )
                return False
        else:
            guild_id = None

        if self.DB.get_blacklist(ctx.author.id, guild_id):
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
        logging.log(50, f"{ctx.author.id}: .{ctx.command.qualified_name}")
        if ctx.author.id in self.bot.owner_ids:
            ctx.command.reset_cooldown(ctx)


def setup(bot: commands.Bot) -> None:
    """Starts events cog."""
    bot.add_cog(events(bot))
