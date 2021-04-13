import discord
from discord.ext import commands
import ujson
import platform
import os
from datetime import datetime
import psutil
import logging


class events(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.karma = self.bot.db.prefixed_db(b"karma-")
        self.blacklist = self.bot.db.prefixed_db(b"blacklist-")
        self.rrole = self.bot.db.prefixed_db(b"rrole-")
        self.deleted = self.bot.db.prefixed_db(b"deleted-")
        self.edited = self.bot.db.prefixed_db(b"edited-")
        self.invites = self.bot.db.prefixed_db(b"invites-")
        self.nicks = self.bot.db.prefixed_db(b"nicks-")

    async def reaction_role_check(self, payload):
        message_id = str(payload.message_id).encode()
        reaction = self.rrole.get(message_id)

        if not reaction:
            return None

        reaction = ujson.loads(reaction)

        if str(payload.emoji) in reaction:
            role_id = int(reaction[str(payload.emoji)])
        elif payload.emoji.name in reaction:
            role_id = int(reaction[payload.emoji.name])
        else:
            return None

        guild = self.bot.get_guild(payload.guild_id)
        role = guild.get_role(role_id)
        if payload.event_type == "REACTION_REMOVE":
            return (role, guild)
        return role

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Gives roles based off reaction added if message in reaction_roles.json.

        payload: discord.RawReactionActionEvent
            A payload of raw data about the reaction and member.
        """
        if payload.member == self.bot.user:
            return

        role = await self.reaction_role_check(payload)
        if role is not None:
            await payload.member.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """Removes roles based off reaction added if message in reaction_roles.json.

        payload: discord.RawReactionActionEvent
            A payload of raw data about the reaction and member.
        """
        try:
            role, guild = await self.reaction_role_check(payload)
        except TypeError:
            return
        if role is not None:
            member = guild.get_member(payload.user_id)
            await member.remove_roles(role)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """The event called when a reaction is added to a message in the cache.

        reaction: discord.Reaction
        user: Union[discord.User, discord.Member]
        """
        if reaction.message.author == user or not reaction.custom_emoji:
            return

        time_since = (datetime.utcnow() - reaction.message.created_at).total_seconds()

        if time_since > 1800:
            return

        member = str(reaction.message.author.id).encode()

        if reaction.emoji.name.lower() == "downvote":
            karma = self.karma.get(member)
            if not karma:
                karma = -1
            else:
                karma = int(karma.decode()) - 1
            self.karma.put(member, str(karma).encode())

        elif reaction.emoji.name.lower() == "upvote":
            karma = self.karma.get(member)
            if not karma:
                karma = 1
            else:
                karma = int(karma.decode()) + 1
            self.karma.put(member, str(karma).encode())

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        """The event called when a reaction is removed from a message in the cache.

        reaction: discord.Reaction
        user: Union[discord.User, discord.Member]
        """
        if reaction.message.author == user or not reaction.custom_emoji:
            return

        time_since = (datetime.utcnow() - reaction.message.created_at).total_seconds()

        if time_since > 1800:
            return

        member = str(reaction.message.author.id).encode()

        if reaction.emoji.name.lower() == "downvote":
            karma = self.karma.get(member)
            if not karma:
                karma = 1
            else:
                karma = int(karma.decode()) + 1
            self.karma.put(member, str(karma).encode())

        elif reaction.emoji.name.lower() == "upvote":
            karma = self.karma.get(member)
            if not karma:
                karma = -1
            else:
                karma = int(karma.decode()) - 1
            self.karma.put(member, str(karma).encode())

    @commands.Cog.listener()
    async def on_reaction_clear(self, message, reactions):
        """The event called when the reactions on a message are cleared.

        message: discord.Message
        reactions: List[discord.Reaction]
        """
        if self.blacklist.get(str(message.author.id).encode()) == b"1":
            await message.add_reaction("<:downvote:766414744730206228>")

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
        if after.channel is None:
            return

        if self.blacklist.get(str(member.id).encode()) == b"1":
            await member.edit(voice_channel=None)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """Logs edited messages to the logs channel.

        before: discord.Message
            The old message.
        after: discord.Message
            The new message.
        """
        if (
            not after.content
            or before.content == after.content
            or after.author == self.bot.user
        ):
            return

        member_id = str(after.author.id).encode()
        edited = self.edited.get(member_id)

        if edited is None:
            edited = {}
        else:
            edited = ujson.loads(edited)

        date = str(datetime.now())[:-7]
        edited[date] = [before.content, after.content]
        self.edited.put(member_id, ujson.dumps(edited).encode())
        self.bot.db.put(
            b"editsnipe_message",
            ujson.dumps(
                [before.content, after.content, after.author.display_name]
            ).encode(),
        )

        if after.content.startswith("https"):
            return

        channel = discord.utils.get(after.guild.channels, name="logs")

        if channel is None:
            return

        if "`" in before.content or "`" in after.content:
            before.content = before.content.replace("`", "")
            after.content = after.content.replace("`", "")

        await channel.send(
            f"```{before.author} edited:\n{before.content} >>> {after.content}```"
        )

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """Logs deleted messages to the logs channel.

        message: discord.Message
        """
        if (
            self.bot.db.get(b"logging") == b"0"
            or not message.content
            or message.author == self.bot.user
        ):
            return

        member_id = str(message.author.id).encode()
        deleted = self.deleted.get(member_id)

        if deleted is None:
            deleted = {}
        else:
            deleted = ujson.loads(deleted)

        date = str(datetime.now())[:-7]
        deleted[date] = message.content

        self.deleted.put(member_id, ujson.dumps(deleted).encode())
        self.bot.db.put(
            b"snipe_message",
            ujson.dumps([message.content, message.author.display_name]).encode(),
        )

        if discord.utils.escape_mentions(message.content) != message.content:
            timesince = datetime.utcnow() - message.created_at

            if timesince.total_seconds() < 30:
                self.blacklist.put(str(message.author.id).encode(), b"1")

        channel = discord.utils.get(message.guild.channels, name="logs")

        if channel is not None:
            await channel.send(
                f"```{message.author} deleted:\n{message.content.replace('`', '')}```"
            )

    @commands.Cog.listener()
    async def on_message(self, message):
        """Downvotes blacklisted members.

        message: discord.Message
        """
        if self.blacklist.get(str(message.author.id).encode()) == b"1":
            await message.add_reaction("<:downvote:766414744730206228>")

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

        nicks = self.nicks.get(member_id)

        if nicks is None:
            nicks = {"nicks": {}, "names": {}}
        else:
            nicks = ujson.loads(nicks)

        now = str(datetime.now())[:-7]

        if "current" in nicks["nicks"]:
            date = nicks["nicks"]["current"][1]
        else:
            date = now

        nicks["nicks"][date] = before.nick
        nicks["nicks"]["current"] = [after.nick, now]

        self.nicks.put(member_id, ujson.dumps(nicks).encode())

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

        names = self.nicks.get(member_id)

        if names is None:
            names = {"nicks": {}, "names": {}}
        else:
            names = ujson.loads(names)

        now = str(datetime.now())[:-7]

        if "current" in names["names"]:
            date = names["names"]["current"][1]
        else:
            date = now

        names["names"][date] = before.nick
        names["names"]["current"] = [after.nick, now]

        self.nicks.put(member_id, ujson.dumps(names).encode())

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Checks which invite someone has joined from.

        member: discord.Member
        """
        for invite in await member.guild.invites():
            key = f"{invite.code}-{invite.guild.id}"
            uses = self.invites.get(key.encode())

            if uses is None:
                self.invites.put(key.encode(), str(invite.uses).encode())
                continue

            if invite.uses > int(uses):
                self.invites.put(str(member.id).encode(), invite.code.encode())

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        """Puts invites into the db to get who used the invite.

        invite: discord.Invite
        """
        key = f"{invite.code}-{invite.guild.id}"
        self.invites.put(key.encode(), str(invite.uses).encode())

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        """Removes invites from the db when they have been deleted.

        invite: discord.Invite
        """
        self.invites.delete(f"{invite.code}-{invite.guild.id}".encode())

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """The event triggered when an error is raised while invoking a command.

        ctx: commands.Context
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

        if isinstance(error, commands.errors.CommandNotFound):
            return

        if isinstance(error, discord.Forbidden):
            message = "I do not have the required permissions to run this command."

        elif isinstance(
            error, (commands.BadArgument, commands.errors.MissingRequiredArgument)
        ):
            ctx.command.reset_cooldown(ctx)
            message = (
                f"{error}\n\nUsage:\n{ctx.prefix}{ctx.command} {ctx.command.signature}"
            )

        elif isinstance(error, commands.errors.ExtensionNotFound):
            message = f"Extension '{error.name}' was not found."

        elif isinstance(error, commands.errors.BotMissingAnyRole):
            message = (
                f"{self.bot.user.name} is missing required roles: {error.missing_roles}"
            )

        elif isinstance(error, commands.errors.BotMissingPermissions):
            message = f"{self.bot.user.name} is missing required permissions: {error.missing_perms}"

        else:
            logging.getLogger("discord").warning(
                f"Unhandled Error: {ctx.command.qualified_name}, Error: {error}, Type: {type(error)}"
            )
            message = error

        if len(str(message)) == 0:
            logging.getLogger("discord").warning(
                f"{ctx.command.qualified_name}, Error: {error}"
            )
            return

        await ctx.send(f"```{message}```")

    @commands.Cog.listener()
    async def on_ready(self):
        """Called when the bot is done preparing the data received from Discord."""
        if not hasattr(self.bot, "uptime"):
            self.bot.uptime = datetime.utcnow()
        print(
            f"""Logged in as {self.bot.user.name}
Discord.py version: {discord.__version__}
Python version: {platform.python_version()}
Running on: {platform.system()} {platform.release()}({os.name})
Boot time: {datetime.now().timestamp()-psutil.Process(os.getpid()).create_time():.3f}s
-------------------"""
        )

    async def bot_check_once(self, ctx):
        """Checks that a user is not blacklisted or downvoted.

        ctx: commands.Context
        """
        if ctx.author.id in self.bot.owner_ids:
            return True

        return not self.blacklist.get(str(ctx.author.id).encode())

    @commands.Cog.listener()
    async def on_command(self, ctx):
        """Resets command cooldown for owners.

        ctx: commands.Context
        """
        logging.getLogger("discord").info(
            f"{ctx.author.id} ran the command {ctx.command.qualified_name}"
        )
        if ctx.author.id in self.bot.owner_ids:
            ctx.command.reset_cooldown(ctx)


def setup(bot: commands.Bot) -> None:
    """Starts events cog."""
    bot.add_cog(events(bot))
