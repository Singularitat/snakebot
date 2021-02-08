import discord
from discord.ext import commands
import ujson
import platform
import os
import time
import datetime
import textwrap
import psutil


class events(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

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
        with open("json/real.json") as file:
            data = ujson.load(file)
        if member.id in data["downvote"] and after.channel is not None:
            await member.edit(voice_channel=None)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """Logs edited messages to the logs channel.

        before: discord.Message
            The old message.
        after: discord.Message
            The new message.
        """
        if not after.content or before == after:
            pass
        else:
            if after.author != self.bot.user:
                if after.content.startswith("https"):
                    pass
                else:
                    try:
                        channel = discord.utils.get(after.guild.channels, name="logs")
                        await channel.send(
                            f"```{before.author} editted:\n{before.content} >>> {after.content}```"
                        )
                    except commands.errors.ChannelNotFound:
                        pass

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """Logs deleted messages to the logs channel.

        message: discord.Message
        """
        if not message.content or message.content.startswith(
            f"{self.bot.command_prefix}issue"
        ):
            pass
        else:
            if "@everyone" in message.content or "@here" in message.content:
                timesince = (
                    datetime.datetime.utcfromtimestamp(time.time()) - message.created_at
                )
                if timesince.total_seconds() < 360:
                    general = discord.utils.get(message.guild.channels, name="logs")
                    embed = discord.Embed(colour=discord.Colour.blurple())
                    embed.description = textwrap.dedent(
                        f"""
                            **{message.author} has ghosted pinged**
                            For their crimes they have been downvoted
                        """
                    )
                    await general.send(embed=embed)
                    with open("json/real.json") as file:
                        data = ujson.load(file)
                    if message.author.id not in data["downvote"]:
                        data["downvote"].append(message.author.id)
                    with open("json/real.json", "w") as file:
                        data = ujson.dump(data, file, indent=2)
            try:
                channel = discord.utils.get(message.guild.channels, name="logs")
                await channel.send(
                    f"```{message.author} deleted:\n{message.content.replace('`', '')}```"
                )
            except commands.errors.ChannelNotFound:
                pass

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Updates a members stored information.

        before: discord.Member
            The updated member's old info.
        after: discord.Member
            The updated member's new info.
        """
        with open("json/real.json") as file:
            data = ujson.load(file)
        data["notevil"][str(after.id)] = []
        for role in after.roles:
            if str(role.name) != "@everyone" and role < after.guild.me.top_role:
                data["notevil"][str(after.id)].append(str(role.name))
        with open("json/real.json", "w") as file:
            data = ujson.dump(data, file, indent=2)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Adds back someones roles if they have joined server before.

        member: discord.Member
        """
        with open("json/real.json") as file:
            data = ujson.load(file)
        if member in data["notevil"]:
            try:
                member.add_roles(data["notevil"][str(member.id)])
            except commands.errors.RoleNotFound:
                pass

    @commands.Cog.listener()
    async def on_message(self, message):
        """Sends and error message if someone blacklisted sends a command.

        message: discord.Message
        """
        with open("json/real.json") as file:
            data = ujson.load(file)
        if message.author.id in data["downvote"]:
            await message.add_reaction("<:downvote:766414744730206228>")

    @commands.Cog.listener()
    async def on_reaction_clear(self, message, reactions):
        """The event triggered when the reactions on a message are cleared.

        message: discord.Message
        reactions: List[discord.Reaction]
        """
        with open("json/real.json") as file:
            data = ujson.load(file)
        if message.author.id in data["downvote"]:
            await message.add_reaction("<:downvote:766414744730206228>")

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

        ignored = commands.errors.CommandNotFound
        if isinstance(error, ignored):
            return

        if hasattr(error, "param"):
            parameter = str(error.param).split(":")[0]
        else:
            parameter = ""

        if hasattr(error, "name"):
            name = error.name
        else:
            name = None

        if hasattr(error, "missing_roles"):
            roles = error.missing_roles
        else:
            roles = None

        if hasattr(error, "missing_perms"):
            permissions = error.missing_perms
        else:
            permissions = None

        handler = {
            discord.Forbidden: "```I do not have the required permissions to run this command.```",
            commands.errors.ChannelNotFound: "```Could not find channel```",
            commands.errors.MemberNotFound: "```Could not find member```",
            commands.errors.UserNotFound: "```Could not find user```",
            commands.errors.DisabledCommand: f"```The {ctx.command} command has been disabled.```",
            commands.errors.NoPrivateMessage: f"```{ctx.command} can not be used in Private Messages.```",
            commands.errors.CheckFailure: "```You aren't allowed to use this command!```",
            commands.errors.MissingAnyRole: f"```You are missing required roles: {roles}```",
            commands.errors.MissingPermissions: f"```You are missing required permissions: {permissions}```",
            commands.errors.MemberNotFound: f"```{error}```",
            commands.errors.CommandOnCooldown: f"```{error}```",
            commands.errors.BadArgument: f"```{error}```",
            commands.errors.MissingRequiredArgument: f"```Missing parameter: {parameter}```",
            commands.errors.ExtensionAlreadyLoaded: f"```{name} is already loaded```",
            commands.errors.ExtensionNotFound: f"```{name} was not found```",
            commands.errors.ExtensionNotLoaded: f"```{name} failed to load```",
            commands.errors.BotMissingAnyRole: f"```{self.bot.user.name} is missing required roles: {roles}```",
            commands.errors.BotMissingPermissions: f"```{self.bot.user.name} is missing required permissions: {permissions}```",
        }

        try:
            message = handler[type(error)]
        except KeyError:
            await ctx.send(f"{error} {type(error)}")
        else:
            await ctx.send(message)

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
        if ctx.author.id == self.bot.owner_id:
            return True
        with open("json/real.json") as file:
            data = ujson.load(file)
        return (
            ctx.author.id not in data["blacklist"]
            and ctx.author.id not in data["downvote"]
        )

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        """Updates member data as a role has been deleted.

        role: discord.Role
            The deleted role.
        """
        with open("json/real.json") as file:
            data = ujson.load(file)
        for member in data["notevil"]:
            if role in data["notevil"][member]:
                data["notevil"][member].remove(role)
        with open("json/real.json", "w") as file:
            data = ujson.dump(data, file, indent=2)

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        """Resets command cooldown for owners.

        ctx: commands.Context
        """
        if ctx.author.id == self.bot.owner_id:
            ctx.command.reset_cooldown(ctx)


def setup(bot):
    bot.add_cog(events(bot))
