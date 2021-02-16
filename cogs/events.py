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
                            f"{before.author} editted:\n{before.content} >>> {after.content}"
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
            self.bot.snipe_message = (message.content, message.author.name)
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
                    f"{message.author} deleted:\n{message.content.replace('`', '')}"
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

        if isinstance(error, discord.Forbidden):
            message = "I do not have the required permissions to run this command."

        elif isinstance(error, commands.BadArgument):
            ctx.command.reset_cooldown(ctx)
            message = f"{error}\n\nUsage:\n```{ctx.prefix}{ctx.command} {ctx.command.signature}```"

        elif isinstance(error, commands.errors.MissingRequiredArgument):
            ctx.command.reset_cooldown(ctx)
            message = f"Missing parameter: {error.param}"

        elif isinstance(error, commands.errors.MissingAnyRole):
            message = f"You are missing required roles: {error.missing_roles}"

        elif isinstance(error, commands.errors.MissingPermissions):
            message = f"You are missing required permissions: {error.missing_perms}"

        elif isinstance(error, commands.errors.ExtensionAlreadyLoaded):
            message = f"{error.name} is already loaded"

        elif isinstance(error, commands.errors.ExtensionNotFound):
            message = f"{error.name} was not found"

        elif isinstance(error, commands.errors.ExtensionNotLoaded):
            message = f"{error.name} failed to load"

        elif isinstance(error, commands.errors.BotMissingAnyRole):
            message = f"{self.bot.user.name} is missing required roles: {error.missing_roles}"

        elif isinstance(error, commands.errors.BotMissingPermissions):
            message = f"{self.bot.user.name} is missing required permissions: {error.missing_perms}"

        else:
            message = error

        await ctx.send(f"```{message}```")

    @commands.Cog.listener()
    async def on_ready(self):
        """Called when the bot is done preparing the data received from Discord."""
        if not hasattr(self.bot, "uptime"):
            self.bot.uptime = datetime.datetime.now()
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
    async def on_command(self, ctx):
        """Resets command cooldown for owners.

        ctx: commands.Context
        """
        if ctx.author.id in self.bot.owner_ids:
            ctx.command.reset_cooldown(ctx)


def setup(bot: commands.Bot) -> None:
    """Starts events cog."""
    bot.add_cog(events(bot))
