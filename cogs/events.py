import discord
from discord.ext import commands
import ujson
import platform
import os
import time
import datetime
import psutil
import logging


class events(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.karma = self.bot.db.prefixed_db(b"karma-")
        self.blacklist = self.bot.db.prefixed_db(b"blacklist-")
        self.rrole = self.bot.db.prefixed_db(b"rrole-")
        self.deleted = self.bot.db.prefixed_db(b"deleted-")

    async def reaction_role_check(self, payload):
        message_id = str(payload.message_id).encode()
        reaction = self.rrole.get(message_id)

        if not reaction:
            return None

        reaction = ujson.loads(reaction.decode())

        if str(payload.emoji) in reaction:
            role_id = int(reaction[str(payload.emoji)])
        elif payload.emoji.name in reaction:
            role_id = int(reaction[payload.emoji.name])
        else:
            return None

        guild = self.bot.get_guild(payload.guild_id)
        role = discord.utils.get(guild.roles, id=role_id)
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
            member = discord.utils.get(guild.members, id=payload.user_id)
            await member.remove_roles(role)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Disconnects a member from voice if they are downvoted.

        member: discord.Member
            The downvoted member.
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
            or after.author != self.bot.user
        ):
            return

        self.bot.editsnipe_message = (
            before.content,
            after.content,
            after.author.display_name,
        )

        if after.content.startswith("https"):
            return

        try:
            channel = discord.utils.get(after.guild.channels, name="logs")
            if "`" in before.content or "`" in after.content:
                before.content = before.content.replace("`", "")
                after.content = after.content.replace("`", "")
            await channel.send(
                f"```{before.author} edited:\n{before.content} >>> {after.content}```"
            )
        except AttributeError:
            pass

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """Logs deleted messages to the logs channel.

        message: discord.Message
        """
        if not message.content or message.author == self.bot.user:
            return

        member_id = str(message.author.id).encode()
        deleted = self.deleted.get(member_id)

        if deleted is None:
            deleted = {}
        else:
            deleted = ujson.loads(deleted)

        date = datetime.datetime.now()
        deleted[date] = message.content

        self.deleted.put(member_id, ujson.dumps(deleted).encode())

        self.bot.snipe_message = (message.content, message.author.display_name)
        if "@everyone" in message.content or "@here" in message.content:
            timesince = (
                datetime.datetime.utcfromtimestamp(time.time()) - message.created_at
            )

            if timesince.total_seconds() < 360:
                self.blacklist.put(str(message.author.id).encode())

        channel = discord.utils.get(message.guild.channels, name="logs")

        if channel is not None:
            await channel.send(
                f"```{message.author} deleted:\n{message.content.replace('`', '')}```"
            )

    @commands.Cog.listener()
    async def on_message(self, message):
        """Sends and error message if someone blacklisted sends a command.

        message: discord.Message
        """
        if self.blacklist.get(str(message.author.id).encode()) == b"1":
            await message.add_reaction("<:downvote:766414744730206228>")

    @commands.Cog.listener()
    async def on_reaction_clear(self, message, reactions):
        """The event called when the reactions on a message are cleared.

        message: discord.Message
        reactions: List[discord.Reaction]
        """
        if self.blacklist.get(str(message.author.id).encode()) == b"1":
            await message.add_reaction("<:downvote:766414744730206228>")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """The event called when a reaction is added to a message in the bots cache.

        reaction: discord.Reaction
        user: Union[discord.User, discord.Member]
        """
        if reaction.message.author == user or not reaction.custom_emoji:
            return

        time_since = (
            datetime.datetime.now() - reaction.message.created_at
        ).total_seconds() - 46800

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
        """The event called when a reaction is removed from a message in the bots cache.

        reaction: discord.Reaction
        user: Union[discord.User, discord.Member]
        """
        if reaction.message.author == user or not reaction.custom_emoji:
            return

        time_since = (
            datetime.datetime.now() - reaction.message.created_at
        ).total_seconds() - 46800

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
            logging.getLogger("discord").info(
                f"Unhandled Error: {ctx.command.qualified_name}, Error: {error}"
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
            self.bot.uptime = datetime.datetime.utcnow()
        print(
            f"""Logged in as {self.bot.user.name}
Discord.py version: {discord.__version__}
Python version: {platform.python_version()}
Running on: {platform.system()} {platform.release()}({os.name})
Boot time: {round(time.time()-psutil.Process(os.getpid()).create_time(), 3)}s
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
