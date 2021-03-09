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

    async def reaction_role_check(self, payload):
        with open("json/reaction_roles.json") as file:
            data = ujson.load(file)

        message_id = str(payload.message_id)

        if message_id in data:
            if str(payload.emoji) in data[message_id]:
                role_id = int(data[message_id][str(payload.emoji)])
            elif payload.emoji.name in data[message_id]:
                role_id = int(data[message_id][payload.emoji.name])
            else:
                return None

            guild = self.bot.get_guild(payload.guild_id)
            role = discord.utils.get(guild.roles, id=role_id)
            return role

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Gives roles based off reaction added if message in reaction_roles.json.

        payload: discord.RawReactionActionEvent
            A payload of raw data about the reaction and member.
        """
        if payload.member == self.bot.user:
            return

        role = self.reaction_role_check(payload)
        if role is not None:
            await payload.member.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """Removes roles based off reaction added if message in reaction_roles.json.

        payload: discord.RawReactionActionEvent
            A payload of raw data about the reaction and member.
        """
        if payload.member == self.bot.user:
            return

        role = self.reaction_role_check(payload)
        if role is not None:
            member = self.bot.get_member(payload.user_id)
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
        if not after.content or before.content == after.content:
            return

        if after.author != self.bot.user:
            self.bot.editsnipe_message = (
                before.content,
                after.content,
                after.author.name,
            )
            if after.content.startswith("https"):
                pass
            else:
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
        if (
            not message.content
            or message.content.startswith(f"{self.bot.command_prefix}issue")
            or message.author == self.bot.user
        ):
            return

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
        with open("json/real.json") as file:
            data = ujson.load(file)
        if message.author.id in data["downvote"]:
            await message.add_reaction("<:downvote:766414744730206228>")

    @commands.Cog.listener()
    async def on_reaction_clear(self, message, reactions):
        """The event called when the reactions on a message are cleared.

        message: discord.Message
        reactions: List[discord.Reaction]
        """
        with open("json/real.json") as file:
            data = ujson.load(file)
        if message.author.id in data["downvote"]:
            await message.add_reaction("<:downvote:766414744730206228>")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """The event called when a reaction is added to a message in the bots cache.

        reaction: discord.Reaction
        user: Union[discord.User, discord.Member]
        """
        if reaction.message.author == user:
            return
        time_since = (
            datetime.datetime.now() - reaction.message.created_at
        ).total_seconds() - 46800
        if time_since > 1800:
            return
        if reaction.custom_emoji:
            with open("json/real.json") as file:
                data = ujson.load(file)
            member = str(reaction.message.author.id)
            if reaction.emoji.name == "downvote":
                if member not in data["karma"]:
                    data["karma"][member] = 0
                data["karma"][member] -= 1
            elif reaction.emoji.name == "upvote":
                if member not in data["karma"]:
                    data["karma"][member] = 0
                data["karma"][member] += 1
            with open("json/real.json", "w") as file:
                data = ujson.dump(data, file, indent=2)

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
            message = (
                f"{error}\n\nUsage:\n{ctx.prefix}{ctx.command} {ctx.command.signature}"
            )

        elif isinstance(error, commands.errors.MissingRequiredArgument):
            ctx.command.reset_cooldown(ctx)
            message = error

        elif isinstance(error, commands.errors.ExtensionNotFound):
            message = f"Extension '{error.name}' was not found."

        elif isinstance(error, commands.errors.BotMissingAnyRole):
            message = (
                f"{self.bot.user.name} is missing required roles: {error.missing_roles}"
            )

        elif isinstance(error, commands.errors.BotMissingPermissions):
            message = f"{self.bot.user.name} is missing required permissions: {error.missing_perms}"

        else:
            message = error

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
        with open("json/real.json") as file:
            data = ujson.load(file)
        return (
            ctx.author.id not in data["blacklist"]
            and ctx.author.id not in data["downvote"]
        )

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
