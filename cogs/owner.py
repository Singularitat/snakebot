import discord
from discord.ext import commands
import orjson
import os
import copy
import asyncio
import traceback
import time
import subprocess
import re
import logging
import cogs.utils.database as DB


class PerformanceMocker:
    """A mock object that can also be used in await expressions."""

    def __init__(self):
        self.loop = asyncio.get_event_loop()

    def permissions_for(self, obj):
        perms = discord.Permissions.all()
        perms.embed_links = False
        return perms

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

    async def cog_check(self, ctx):
        """Checks if the member is an owner.

        ctx: commands.Context
        """
        return ctx.author.id in self.bot.owner_ids

    @commands.command(aliases=["clearinf"])
    async def clearinfractions(self, ctx, member: discord.Member):
        """Removes all infractions of a member.

        member: discord.Member
        """
        DB.infractions.delete(f"{ctx.guild.id}-{member.id}".encode())

    @commands.command(aliases=["showinf"])
    async def showinfractions(self, ctx, member: discord.Member):
        """Shows all infractions of a member.

        member: discord.Member
        """
        member_id = f"{ctx.guild.id}-{member.id}".encode()
        infractions = DB.infractions.get(member_id)

        embed = discord.Embed(color=discord.Color.blurple())

        if not infractions:
            embed.description = "No infractions found for member"
            return await ctx.send(embed=embed)

        inf = orjson.loads(infractions)

        embed.description = "Warnings: {}, Mutes: {}, Kicks: {}, Bans: {}".format(
            inf["warnings"], inf["mutes"], inf["kicks"], inf["bans"]
        )

        await ctx.send(embed=embed)

        DB.infractions.put(member_id, orjson.dumps(infractions))

    @commands.command(aliases=["removeinf"])
    async def removeinfraction(
        self, ctx, member: discord.Member, infraction: str, index: int
    ):
        """Removes an infraction at an index from a member.

        member: discord.Member
        type: str
            The type of infraction to remove e.g warnings, mutes, kicks, bans
        index: int
            The index of the infraction to remove e.g 0, 1, 2
        """
        member_id = f"{ctx.guild.id}-{member.id}".encode()
        infractions = DB.infractions.get(member_id)

        embed = discord.Embed(color=discord.Color.blurple())

        if not infractions:
            embed.description = "No infractions found for member"
            return await ctx.send(embed=embed)

        inf = orjson.loads(infractions)
        infraction = inf[infraction].pop(index)

        embed.description = f"Deleted infraction [{infraction}] from {member}"
        await ctx.send(embed=embed)

        DB.infractions.put(member_id, orjson.dumps(infractions))

    @commands.command()
    async def loglevel(self, ctx, level):
        """Changes logging level.

        level: str
            The new logging level.
        """
        if level.upper() in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            logging.getLogger("discord").setLevel(getattr(logging, level.upper()))

    @commands.command()
    async def gblacklist(self, ctx, user: discord.User):
        """Globally blacklists someone from the bot.

        user: discord.user
        """
        embed = discord.Embed(color=discord.Color.blurple())

        user_id = str(user.id).encode()
        if DB.blacklist.get(user_id):
            DB.blacklist.delete(user_id)

            embed.title = "User Unblacklisted"
            embed.description = f"***{user}*** has been unblacklisted"
            return await ctx.send(embed=embed)

        DB.blacklist.put(user_id, b"2")
        embed.title = "User Blacklisted"
        embed.description = f"**{user}** has been added to the blacklist"

        await ctx.send(embed=embed)

    @commands.command()
    async def gdownvote(self, ctx, user: discord.User):
        """Globally downvotes someones.

        user: discord.user
        """
        embed = discord.Embed(color=discord.Color.blurple())

        user_id = str(user.id).encode()
        if DB.blacklist.get(user_id):
            DB.blacklist.delete(user_id)

            embed.title = "User Undownvoted"
            embed.description = f"***{user}*** has been undownvoted"
            return await ctx.send(embed=embed)

        DB.blacklist.put(user_id, b"1")
        embed.title = "User Downvoted"
        embed.description = f"**{user}** has been added to the downvote list"

        await ctx.send(embed=embed)

    @commands.command()
    async def backup(self, ctx, number: int):
        """Sends the bot database backup as a json file.

        number: int
            Which backup to get.
        """
        number = min(10, max(number, 0))

        with open(f"backup/{number}backup.json", "rb") as file:
            await ctx.send(file=discord.File(file, "backup.json"))

    @commands.command(aliases=["boot"])
    async def boot_times(self, ctx):
        """Shows the average fastest and slowest boot times of the bot."""
        boot_times = DB.db.get(b"boot_times")

        embed = discord.Embed(color=discord.Color.blurple())

        if not boot_times:
            embed.description = "No boot times found"
            return await ctx.send(embed=embed)

        boot_times = orjson.loads(boot_times)

        msg = (
            f"\n\nAverage: {(sum(boot_times) / len(boot_times)):.5f}s"
            f"\nSlowest: {max(boot_times):.5f}s"
            f"\nFastest: {min(boot_times):.5f}s"
        )

        embed.description = f"```{msg}```"
        await ctx.send(embed=embed)

    @commands.command(aliases=["wipec"])
    async def wipe_cache(self, ctx):
        """Wipes cache from the db."""
        DB.db.put(b"cache", b"{}")

        embed = discord.Embed(color=discord.Color.blurple())
        embed.description = "```Wiped Cache```"
        await ctx.send(embed=embed)

    @commands.command(aliases=["cache"])
    async def list_cache(self, ctx):
        """Lists the cached items in the db."""
        embed = discord.Embed(color=discord.Color.blurple())
        cache = DB.db.get(b"cache")

        if cache:
            cache = orjson.loads(cache)
        else:
            embed.description = "```Nothing has been cached```"
            return await ctx.send(embed=embed)

        if cache == {}:
            embed.description = "```Nothing has been cached```"
            return await ctx.send(embed=embed)

        msg = []

        for item in cache:
            msg.append(item)

        embed.description = "```{}```".format("\n".join(msg))
        await ctx.send(embed=embed)

    @commands.command()
    async def disable(self, ctx, *, command):
        """Disables the use of a command for every guild.

        command: str
            The name of the command to disable.
        """
        command = self.bot.get_command(command)
        embed = discord.Embed(color=discord.Color.blurple())

        if not command:
            embed.description = "```Command not found```"
            return await ctx.send(embed=embed)

        command.enabled = not command.enabled
        ternary = "enabled" if command.enabled else "disabled"

        embed.description = (
            f"```Sucessfully {ternary} the {command.qualified_name} command```"
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def presence(self, ctx, *, presence):
        """Changes the bots activity.

        presence: str
            The new activity.
        """
        await self.bot.change_presence(
            status=discord.Status.online,
            activity=discord.Game(name=presence),
        )

    @commands.command()
    async def perf(self, ctx, *, command):
        """Checks the timing of a command, while attempting to suppress HTTP calls.

        p.s just the command itself with nothing in it takes about 0.02ms

        command: str
            The command to run including arguments.
        """
        msg = copy.copy(ctx.message)
        msg.content = f"{ctx.prefix}{command}"

        new_ctx = await self.bot.get_context(msg, cls=type(ctx))

        # Intercepts the Messageable interface a bit
        new_ctx._state = PerformanceMocker()
        new_ctx.channel = PerformanceMocker()

        if not new_ctx.command:
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(), description="```No command found```"
                )
            )

        start = time.perf_counter()

        try:
            await new_ctx.command.invoke(new_ctx)
            new_ctx.command.reset_cooldown(new_ctx)
        except commands.CommandError:
            end = time.perf_counter()
            result = "Failed"

            try:
                await ctx.send(f"```py\n{traceback.format_exc()}\n```")
            except discord.HTTPException:
                pass
        else:
            end = time.perf_counter()
            result = "Success"

        await ctx.send(f"```css\n{result}: {(end - start) * 1000:.2f}ms```")

    @commands.command()
    async def prefix(self, ctx, prefix: str):
        """Changes the bots command prefix.

        prefix: str
            The new prefix.
        """
        self.bot.command_prefix = prefix

        embed = discord.Embed(color=discord.Color.blurple())
        embed.description = f"```Prefix changed to {prefix}```"
        await ctx.send(embed=embed)

    @commands.command()
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

    async def run_process(self, command, raw=False):
        """Runs a shell command and returns the output.

        command: str
            The command to run.
        raw: bool
            If True returns the result just decoded.
        """
        try:
            process = await asyncio.create_subprocess_shell(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            result = await process.communicate()
        except NotImplementedError:
            process = subprocess.Popen(
                command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            result = await self.bot.loop.run_in_executor(None, process.communicate)

        if raw:
            return [output.decode() for output in result]

        return "".join([output.decode() for output in result]).split()

    @commands.command(aliases=["pull"])
    async def update(self, ctx):
        """Gets latest commits and applies them through git."""
        pull = await self.run_process("git pull")

        embed = discord.Embed(color=discord.Color.blurple())

        if pull == ["Already", "up", "to", "date."]:
            embed.title = "Bot Is Already Up To Date"
            return await ctx.send(embed=embed)

        diff = await self.run_process("git diff --name-only HEAD@{0} HEAD@{1}")

        if "poetry.lock" in diff:
            await self.run_process("poetry install")

        embed.title = "Pulled latests commits, restarting."
        await ctx.send(embed=embed)

        if "bot.py" in diff:
            await self.bot.logout()

            if os.name == "nt":
                await self.run_process("python ./bot.py")
            else:
                await self.run_process("nohup python3 bot.py &")
            return

        diff = [ext[5:] for ext in diff if ext.startswith("/cogs")]

        for ext in [
            f[:-3] for f in os.listdir("cogs") if f.endswith(".py") and f in diff
        ]:
            try:
                self.bot.reload_extension(f"cogs.{ext}")
            except Exception as e:
                if isinstance(e, commands.errors.ExtensionNotLoaded):
                    self.bot.load_extension(f"cogs.{ext}")

    @commands.command()
    async def status(self, ctx):
        await self.run_process("git fetch")
        status = await self.run_process("git status", True)

        embed = discord.Embed(color=discord.Color.blurple())
        embed.description = f"```ahk\n{' '.join(status)}```"

        await ctx.send(embed=embed)

    @commands.command(aliases=["deletecmd", "removecmd"])
    async def deletecommand(self, ctx, command):
        """Removes command from the bot.

        command: str
            The command to remove.
        """
        self.bot.remove_command(command)
        await ctx.send(embed=discord.Embed(title=f"```Removed command {command}```"))

    @commands.command()
    async def kill(self, ctx):
        """Kills the bot."""
        await self.bot.logout()

    @commands.command()
    async def load(self, ctx, extension: str):
        """Loads an extension.

        extension: str
            The extension to load.
        """
        embed = discord.Embed(color=discord.Color.blurple())

        try:
            self.bot.load_extension(f"cogs.{extension}")
        except (AttributeError, ImportError) as e:
            embed.description = f"```{type(e).__name__}: {e}```"
            return await ctx.send(embed=embed)

        embed.title = f"{extension} loaded."
        await ctx.send(embed=embed)

    @commands.command()
    async def unload(self, ctx, ext: str):
        """Unloads an extension.

        extension: str
            The extension to unload.
        """
        self.bot.unload_extension(f"cogs.{ext}")
        await ctx.send(
            embed=discord.Embed(title=f"{ext} unloaded.", color=discord.Color.blurple())
        )

    @commands.command()
    async def reload(self, ctx, ext: str):
        """Reloads an extension.

        extension: str
            The extension to reload.
        """
        self.bot.reload_extension(f"cogs.{ext}")
        await ctx.send(
            embed=discord.Embed(title=f"{ext} reloaded.", color=discord.Color.blurple())
        )

    @commands.command()
    async def restart(self, ctx):
        """Restarts all extensions."""
        embed = discord.Embed(color=discord.Color.blurple())
        DB.db.put(b"restart", b"1")

        for ext in [f[:-3] for f in os.listdir("cogs") if f.endswith(".py")]:
            try:
                self.bot.reload_extension(f"cogs.{ext}")
            except Exception as e:
                if isinstance(e, commands.errors.ExtensionNotLoaded):
                    self.bot.load_extension(f"cogs.{ext}")
                embed.description = f"```{type(e).__name__}: {e}```"
                return await ctx.send(embed=embed)

        embed.title = "Extensions restarted."
        await ctx.send(embed=embed)

    @commands.command()
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

    @commands.command()
    async def lrrole(self, ctx):
        """Sends a list of the message ids of current reaction roles."""
        msg = ""
        for message_id, roles in DB.rrole:
            msg += f"\n\n{message_id.decode()}: {orjson.loads(roles)}"
        await ctx.send(f"```{msg}```")

    @commands.command()
    async def drrole(self, ctx, message_id: int):
        """Deletes a reaction role message and removes it from the db.

        message: int
            Id of the reaction role messgae to delete.
        """
        DB.rrole.delete(str(message_id).encode())
        message = ctx.channel.get_partial_message(message_id)
        await message.delete()

    @commands.command()
    async def rrole(self, ctx, *emojis):
        """Starts a slightly interactive session to create a reaction role.

        emojis: tuple
            A tuple of emojis.
        """
        if emojis == ():
            return await ctx.send(
                "Put emojis as arguments in the command e.g rrole :fire:"
            )

        await ctx.message.delete()

        channel = await self.await_for_message(
            ctx, "Send the channel you want the message to be in"
        )
        breifs = await self.await_for_message(
            ctx, "Send an brief for every emote Seperated by |"
        )
        roles = await self.await_for_message(
            ctx, "Send an role id/name for every role Seperated by |"
        )

        roles = roles.content.split("|")

        for index, role in enumerate(roles):
            role = role.strip()
            if not role.isnumeric():
                tmp_role = discord.utils.get(ctx.guild.roles, name=role)
                if not tmp_role:
                    return await ctx.send(f"```Couldn't find role {role}```")
                roles[index] = tmp_role.id

        msg = "**Role Menu:**\nReact for a role.\n"

        for emoji, breif in zip(emojis, breifs.content.split("|")):
            msg += f"\n{emoji}: `{breif}`\n"

        channel_id = re.sub(r"[^\d.]+", "", channel.content)

        try:
            channel = ctx.guild.get_channel(int(channel_id))
        except ValueError:
            channel = ctx.channel
        else:
            if not channel:
                channel = ctx.channel

        message = await channel.send(msg)

        try:
            for emoji in emojis:
                await message.add_reaction(emoji)
        except discord.errors.HTTPException:
            await message.delete()
            return await ctx.send("Invalid emoji")

        DB.rrole.put(str(message.id).encode(), orjson.dumps(dict(zip(emojis, roles))))

    @commands.command()
    async def redit(self, ctx, message: discord.Message, *emojis):
        """Edit a reaction role message.

        message: discord.Message
            The id of the reaction roles message.
        emojis: tuple
            A tuple of emojis.
        """
        reaction = DB.rrole.get(str(message.id).encode())

        if not reaction:
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(), description="```Message not found```"
                )
            )

        msg = message.content

        breifs = await self.await_for_message(
            ctx, "Send an brief for every emote Seperated by |"
        )
        roles = await self.await_for_message(
            ctx, "Send an role id/name for every role Seperated by |"
        )

        roles = roles.content.split("|")

        for index, role in enumerate(roles):
            if not role.isnumeric():
                role = discord.utils.get(ctx.guild.roles, name=role)
                if not role:
                    return await ctx.send(f"```Could not find role {role}```")
                roles[index] = role.id

        msg += "\n"

        for emoji, breif in zip(emojis, breifs.content.split("|")):
            msg += f"\n{emoji}: `{breif}`\n"

        await message.edit(content=msg)

        for emoji in emojis:
            await message.add_reaction(emoji)

        reaction = orjson.loads(reaction)

        for emoji, role in zip(emojis, roles):
            reaction[emoji] = role

        DB.rrole.put(str(message.id).encode(), orjson.dumps(reaction))

    @staticmethod
    async def await_for_message(ctx, message):
        def check(message: discord.Message) -> bool:
            return message.author.id == ctx.author.id and message.channel == ctx.channel

        tmp_msg = await ctx.send(message)

        try:
            message = await ctx.bot.wait_for("message", timeout=300.0, check=check)
        except asyncio.TimeoutError:
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(), description="```Timed out```"
                )
            )

        await tmp_msg.delete()
        await message.delete()

        return message


def setup(bot: commands.Bot) -> None:
    """Starts owner cog."""
    bot.add_cog(owner(bot))
