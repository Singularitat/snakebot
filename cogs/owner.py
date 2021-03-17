import discord
from discord.ext import commands
import ujson
import os
import copy
import asyncio
import traceback
import time
import string


class PerformanceMocker:
    """A mock object that can also be used in await expressions."""

    def __init__(self):
        self.loop = asyncio.get_event_loop()

    def __getattr__(self, attr):
        return self

    def __call__(self, *args, **kwargs):
        return self

    def __repr__(self):
        return "<PerformanceMocker>"

    def __await__(self):
        future = self.loop.create_future()
        future.set_result(self)
        return future.__await__()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return self

    def __len__(self):
        return 0

    def __bool__(self):
        return False


class owner(commands.Cog):
    """Administrative commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def issue(self, ctx, *, issue):
        """Appends an issue to the snakebot-todo.

        issue: str
            The issue to append.
        """
        await ctx.channel.purge(limit=1)
        channel = self.bot.get_channel(776616587322327061)
        message = await channel.fetch_message(787153490996494336)
        issues = str(message.content).replace("`", "")
        issuelist = issues.split("\n")
        issue = string.capwords(issue)
        if issue[0:6] == "Delete":
            issuelist.remove(f"{issue[7:]}")
            issues = "\n".join(issuelist)
            await message.edit(content=f"""```{issues}```""")
        else:
            await message.edit(
                content=f"""```{issues}
{issue}```"""
            )

    @commands.command(hidden=True)
    @commands.is_owner()
    async def toggle(self, ctx, command):
        """Toggles a command from being disabled or enabled.

        command: str
            The command to be toggled
        """
        command = self.bot.get_command(command)
        if command is None:
            await ctx.send("```No such command```")
        else:
            command.enabled = not command.enabled
            ternary = "enabled" if command.enabled else "disabled"
            await ctx.send(
                f"```Sucessfully {ternary} the {command.qualified_name} command```"
            )

    @commands.command(hidden=True)
    @commands.is_owner()
    async def presence(self, ctx, *, presence):
        """Changes the bots activity.

        presence: str
            The new activity.
        """
        await self.bot.change_presence(
            status=discord.Status.online,
            activity=discord.Game(name=presence),
        )

    @commands.command(hidden=True)
    @commands.is_owner()
    async def perf(self, ctx, *, command):
        """Checks the timing of a command, while attempting to suppress HTTP calls.

        command: str
            The command to run including arguments.
        """
        msg = copy.copy(ctx.message)
        msg.content = f"{ctx.prefix}{command}"

        new_ctx = await self.bot.get_context(msg, cls=type(ctx))

        # Intercepts the Messageable interface a bit
        new_ctx._state = PerformanceMocker()
        new_ctx.channel = PerformanceMocker()

        if new_ctx.command is None:
            return await ctx.send("```No command found```")

        start = time.perf_counter()
        try:
            await new_ctx.command.invoke(new_ctx)
            new_ctx.command.reset_cooldown(new_ctx)
        except commands.CommandError:
            end = time.perf_counter()
            success = "Failure"
            try:
                await ctx.send(f"```py\n{traceback.format_exc()}\n```")
            except discord.HTTPException:
                pass
        else:
            end = time.perf_counter()
            success = "Success"

        await ctx.send(f"```{success}; {(end - start) * 1000:.2f}ms```")

    @commands.command(hiiden=True)
    @commands.is_owner()
    async def prefix(self, ctx, prefix: str):
        """Changes the bots command prefix.

        prefix: str
            The new prefix.
        """
        self.bot.command_prefix = prefix
        await ctx.send(f"```Prefix changed to {prefix}```")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def sudo(
        self, ctx, channel: discord.TextChannel, member: discord.Member, *, command: str
    ):
        """Run a command as another user.

        channel: discord.TextChannel
            The channel to run the command.
        member: discord.Member
            The member to run the command as.
        command: str
            The command name.
        """
        msg = copy.copy(ctx.message)
        channel = channel or ctx.channel
        msg.channel = channel
        msg.author = member
        msg.content = f"{ctx.prefix}{command}"
        new_ctx = await self.bot.get_context(msg, cls=type(ctx))
        await self.bot.invoke(new_ctx)

    @commands.command(hidden=True, aliases=["pull"])
    @commands.is_owner()
    async def update(self, ctx):
        """Gets latest commits and applies them through git."""
        pull = os.popen("git pull").read()

        if pull == "Already up to date.\n":
            await ctx.send(
                embed=discord.Embed(
                    title="Bot Is Already Up To Date", color=discord.Color.blurple()
                )
            )
        else:
            os.system("poetry install")

            await ctx.send(
                embed=discord.Embed(
                    title="Pulled latests commits, restarting.",
                    color=discord.Color.blurple(),
                )
            )

            await self.bot.logout()

            if os.name == "nt":
                os.system("python ./bot.py")
            else:
                os.system("nohup python3 bot.py &")

    @commands.command(hidden=True, aliases=["deletecmd", "removecmd"])
    @commands.is_owner()
    async def deletecommand(self, ctx, command):
        """Removes command from the bot.

        command: str
            The command to remove.
        """
        self.bot.remove_command(command)
        await ctx.send(embed=discord.Embed(title=f"```Removed command {command}```"))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def kill(self, ctx):
        """Kills the bot."""
        await self.bot.change_presence(
            status=discord.Status.online, activity=discord.Game(name="Dying...")
        )
        await ctx.send(embed=discord.Embed(title="Killing bot"))
        await self.bot.logout()

    @commands.command(hidden=True)
    @commands.is_owner()
    async def load(self, ctx, extension: str):
        """Loads an extension.

        extension: str
            The extension to load.
        """
        extension = f"cogs.{extension}"
        try:
            self.bot.load_extension(extension)
        except (AttributeError, ImportError) as e:
            await ctx.send(
                embed=discord.Embed(
                    title="```py\n{}: {}\n```".format(type(e).__name__, str(e)),
                    color=discord.Color.blurple(),
                )
            )
            return
        await ctx.send(
            embed=discord.Embed(
                title=f"{extension} loaded.", color=discord.Color.blurple()
            )
        )

    @commands.command(hidden=True)
    @commands.is_owner()
    async def unload(self, ctx, extension: str):
        """Unloads an extension.

        extension: str
            The extension to unload.
        """
        extension = f"cogs.{extension}"
        self.bot.unload_extension(extension)
        await ctx.send(
            embed=discord.Embed(
                title=f"{extension} unloaded.", color=discord.Color.blurple()
            )
        )

    @commands.command(hidden=True)
    @commands.is_owner()
    async def reload(self, ctx, extension: str):
        """Reloads an extension.

        extension: str
            The extension to reload.
        """
        extension = f"cogs.{extension}"
        self.bot.reload_extension(extension)
        await ctx.send(
            embed=discord.Embed(
                title=f"{extension} reloaded.", color=discord.Color.blurple()
            )
        )

    @commands.command(hidden=True)
    @commands.is_owner()
    async def restart(self, ctx):
        """Restarts all extensions."""
        for extension in [
            f.replace(".py", "")
            for f in os.listdir("cogs")
            if os.path.isfile(os.path.join("cogs", f))
        ]:
            try:
                self.bot.reload_extension(f"cogs.{extension}")
            except Exception as e:
                if (
                    e
                    == f"ExtensionNotLoaded: Extension 'cogs.{extension}' has not been loaded."
                ):
                    self.bot.load_extension(f"cogs.{extension}")
                else:
                    await ctx.send(
                        embed=discord.Embed(
                            title="```{}: {}\n```".format(type(e).__name__, str(e)),
                            color=discord.Color.blurple(),
                        )
                    )
        await ctx.send(
            embed=discord.Embed(
                title="Extensions restarted.", color=discord.Color.blurple()
            )
        )

    @commands.command(hidden=True)
    @commands.is_owner()
    async def revive(self, ctx):
        """Kills the bot then revives it."""
        await ctx.send(
            embed=discord.Embed(
                title="Killing bot.",
                color=discord.Color.blurple(),
            )
        )
        await self.bot.logout()
        if os.name == "nt":
            os.system("python ./bot.py")
        else:
            os.system("nohup python3 bot.py &")

    async def open_json(self, file_path, msg):
        try:
            with open(file_path) as file:
                try:
                    data = ujson.load(file)
                except ValueError:
                    data = {}
                    msg += f"Error loading {file.name}\n"
        except FileNotFoundError:
            data = {}
            msg += f"{file} not found\n"
        return data, msg

    async def check_keys(self, data, msg, *keys):
        for key in keys:
            if key not in data:
                data[key] = {}
                msg += f"{key} not found\n"
        return msg

    @commands.command(hidden=True, name="fixjson")
    @commands.is_owner()
    async def fix_json(self, ctx):
        """Fixes the bots json files if they are broken."""
        msg = ""

        # Fixing economy.json

        data, msg = await self.open_json("json/economy.json", msg)

        msg = await self.check_keys(data, msg, "money", "stockbal", "wins", "stocks")

        with open("json/economy.json", "w") as file:
            data = ujson.dump(data, file, indent=2)

        # Fixing reaction_roles.json

        data, msg = await self.open_json("json/reaction_roles.json", msg)

        with open("json/reaction_roles.json", "w") as file:
            data = ujson.dump(data, file, indent=2)

        # Fixing real.json

        data, msg = await self.open_json("json/real.json", msg)

        msg = await self.check_keys(data, msg, "blacklist", "downvote", "karma")

        with open("json/real.json", "w") as file:
            data = ujson.dump(data, file, indent=2)

        if msg:
            await ctx.send(f"```{msg}```")
        else:
            await ctx.send("```No Errors```")

    @commands.command()
    @commands.is_owner()
    async def rrole(self, ctx, *emojis):
        """Starts a slightly interactive session to create a reaction role.

        emojis: tuple
            A tuple of emojis.
        """
        await ctx.message.delete()

        if emojis == ():
            return await ctx.send(
                "Put emojis as arguments in the command e.g rrole :fire:"
            )

        channel = await self.await_for_message(
            ctx, "Send the channel you want the message to be in"
        )
        breifs = await self.await_for_message(
            ctx, "Send an brief for every emote Seperated by ;"
        )
        roles = await self.await_for_message(
            ctx, "Send an role id/name for every role Seperated by ;"
        )

        roles = roles.content.split(";")

        for index, role in enumerate(roles):
            if not role.isnumeric():
                try:
                    role = discord.utils.get(ctx.guild.roles, name=role)
                    roles[index] = role.id
                except commands.errors.RoleNotFound:
                    return await ctx.send(f"Could not find role {index}")

        msg = "**Role Menu:**\nReact for a role.\n"

        for emoji, breif in zip(emojis, breifs.content.split(";")):
            msg += f"\n{emoji}: `{breif}`\n"
        message = await channel.channel.send(msg)

        for emoji in emojis:
            await message.add_reaction(emoji)

        with open("json/reaction_roles.json") as file:
            data = ujson.load(file)

        data[str(message.id)] = dict(zip(emojis, roles))

        with open("json/reaction_roles.json", "w") as file:
            data = ujson.dump(data, file, indent=2)

    @commands.command()
    @commands.is_owner()
    async def redit(self, ctx, message: discord.Message, *emojis):
        """Edit a reaction role message.

        message: discord.Message
            The id of the reaction roles message.
        emojis: tuple
            A tuple of emojis.
        """
        msg = message.content

        breifs = await self.await_for_message(
            ctx, "Send an brief for every emote Seperated by ;"
        )
        roles = await self.await_for_message(
            ctx, "Send an role id/name for every role Seperated by ;"
        )

        roles = roles.content.split(";")

        for index, role in enumerate(roles):
            if not role.isnumeric():
                try:
                    role = discord.utils.get(ctx.guild.roles, name=role)
                    roles[index] = role.id
                except commands.errors.RoleNotFound:
                    return await ctx.send(f"Could not find role {index}")

        msg += "\n"

        for emoji, breif in zip(emojis, breifs.content.split(";")):
            msg += f"\n{emoji}: `{breif}`\n"

        await message.edit(content=msg)

        for emoji in emojis:
            await message.add_reaction(emoji)

        with open("json/reaction_roles.json") as file:
            data = ujson.load(file)

        for emoji, role in zip(emojis, roles):
            data[str(message.id)][emoji] = role

        with open("json/reaction_roles.json", "w") as file:
            data = ujson.dump(data, file, indent=2)


def setup(bot: commands.Bot) -> None:
    """Starts owner cog."""
    bot.add_cog(owner(bot))
