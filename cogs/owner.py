from io import StringIO
import asyncio
import cProfile
import logging
import os
import pstats
import re
import time
import traceback

from discord.ext import commands
import discord
import orjson

from cogs.utils.useful import run_process


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
        self.DB = bot.DB

    async def cog_check(self, ctx):
        """Checks if the member is an owner.

        ctx: commands.Context
        """
        return ctx.author.id in self.bot.owner_ids

    @commands.command()
    async def profile(self, ctx, *, command):
        """Profiles a comamnd.

        command: str
        """
        ctx.message.content = f"{ctx.prefix}{command}"
        new_ctx = await self.bot.get_context(ctx.message, cls=type(ctx))
        new_ctx.reply = new_ctx.send  # Reply ignores the PerformanceMocker

        new_ctx._state = PerformanceMocker()
        new_ctx.channel = PerformanceMocker()

        embed = discord.Embed(color=discord.Color.blurple())

        if not new_ctx.command:
            embed.description = "```No command found```"
            return await ctx.send(embed=embed)

        with cProfile.Profile() as pr:
            await new_ctx.command.invoke(new_ctx)

        file = StringIO()
        ps = pstats.Stats(pr, stream=file).strip_dirs().sort_stats("cumulative")
        ps.print_stats()

        await ctx.send(file=discord.File(StringIO(file.getvalue()), "profile.txt"))

    @commands.command()
    async def bytecode(self, ctx, *, command):
        """Gets the bytecode of a command.

        command: str
        """
        command = self.bot.get_command(command)
        if not command:
            embed = discord.Embed(
                color=discord.Color.blurple(),
                description="```Couldn't find command.```",
            )
            return await ctx.send(embed=embed)

        code_obj = command.callback.__code__

        argcount = code_obj.co_argcount
        posonlyargcount = code_obj.co_posonlyargcount
        kwonlyargcount = code_obj.co_kwonlyargcount
        nlocals = code_obj.co_nlocals
        stacksize = code_obj.co_stacksize
        flags = code_obj.co_flags

        args = (
            f"{argcount=}, {posonlyargcount=}, {kwonlyargcount=}, "
            f"{nlocals=}, {stacksize=}, {flags=}"
        ).replace("`", "`\u200b")

        await ctx.send(f"```py\n{args}\n\n``````fix\n{code_obj.co_code.hex()}```")

    @commands.command(name="wipeblacklist")
    async def wipe_blacklist(self, ctx):
        """Wipes everyone from the blacklist list includes downvoted members."""
        for member, value in self.DB.blacklist:
            self.DB.blacklist.delete(member)

    @commands.group()
    async def db(self, ctx):
        if not ctx.invoked_subcommand:
            await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description=f"```Usage: {ctx.prefix}db [del/show/get/put/pre]```",
                )
            )

    @db.command()
    async def put(self, ctx, key, *, value=None):
        """Puts a value in the database

        key: str
        value: str
        """
        embed = discord.Embed(color=discord.Color.blurple())

        if not value:
            if not ctx.message.attachments:
                embed.description = "```You need to attach a file or input a value.```"
                return await ctx.send(embed=embed)

            value = ctx.message.attachments[0].read().decode()

        self.DB.main.put(key.encode(), value.encode())

        embed.description = f"```Put {value} at {key}```"
        await ctx.send(embed=embed)

    @db.command(name="delete", aliases=["del"])
    async def db_delete(self, ctx, key):
        """Deletes an item from the database.

        key: str
        """
        self.DB.main.delete(key.encode())

        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                description=f"```Deleted {key} from database```",
            )
        )

    @db.command()
    async def get(self, ctx, key):
        """Shows an item from the database.

        key: str
        """
        item = self.DB.main.get(key.encode())

        if not item:
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description="```Key not found in database```",
                )
            )

        file = StringIO(item.decode())

        await ctx.send(file=discord.File(file, "data.txt"))

    @db.command()
    async def show(self, ctx, exclude=True):
        """Sends a json of the entire database."""
        database = {}

        if exclude:
            excluded = (
                b"crypto",
                b"stocks",
                b"message_count",
                b"invites",
                b"karma",
                b"boot_times",
                b"aliases",
            )

            for key, value in self.DB.main:
                if key.split(b"-")[0] not in excluded:
                    if value[:1] in [b"{", b"["]:
                        value = orjson.loads(value)
                    else:
                        value = value.decode()
                    database[key.decode()] = value
        else:
            for key, value in self.DB.main:
                if value[:1] in [b"{", b"["]:
                    value = orjson.loads(value)
                else:
                    value = value.decode()
                database[key.decode()] = value

        file = StringIO(str(database))
        await ctx.send(file=discord.File(file, "data.json"))

    @db.command(aliases=["pre"])
    async def show_prefixed(self, ctx, prefixed):
        """Sends a json of the entire database."""
        if not hasattr(self.DB, prefixed):
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description=f"```Prefixed DB {prefixed} not found```",
                )
            )

        database = {
            key.decode(): value.decode() for key, value in getattr(self.DB, prefixed)
        }

        file = StringIO(str(database))

        await ctx.send(file=discord.File(file, "data.json"))

    @commands.command(aliases=["clearinf"])
    async def clear_infractions(self, ctx, member: discord.Member):
        """Removes all infractions of a member.

        member: discord.Member
        """
        self.DB.infractions.delete(f"{ctx.guild.id}-{member.id}".encode())

    @commands.command(aliases=["showinf"])
    async def show_infractions(self, ctx, member: discord.Member):
        """Shows all infractions of a member.

        member: discord.Member
        """
        member_id = f"{ctx.guild.id}-{member.id}".encode()
        infractions = self.DB.infractions.get(member_id)

        embed = discord.Embed(color=discord.Color.blurple())

        if not infractions:
            embed.description = "No infractions found for member"
            return await ctx.send(embed=embed)

        inf = orjson.loads(infractions)

        embed.description = "Warnings: {}, Mutes: {}, Kicks: {}, Bans: {}".format(
            inf["warnings"], inf["mutes"], inf["kicks"], inf["bans"]
        )

        await ctx.send(embed=embed)

        self.DB.infractions.put(member_id, orjson.dumps(infractions))

    @commands.command(aliases=["removeinf"])
    async def remove_infraction(
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
        infractions = self.DB.infractions.get(member_id)

        embed = discord.Embed(color=discord.Color.blurple())

        if not infractions:
            embed.description = "No infractions found for member"
            return await ctx.send(embed=embed)

        inf = orjson.loads(infractions)
        infraction = inf[infraction].pop(index)

        embed.description = f"Deleted infraction [{infraction}] from {member}"
        await ctx.send(embed=embed)

        self.DB.infractions.put(member_id, orjson.dumps(infractions))

    @commands.command(name="loglevel")
    async def log_level(self, ctx, level):
        """Changes logging level.

        Options: DEBUG, INFO, WARNING, ERROR, CRITICAL

        level: str
            The new logging level.
        """
        level = level.upper()
        if level.upper() in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            logging.getLogger("discord").setLevel(getattr(logging, level))

    @commands.command(name="gblacklist")
    async def global_blacklist(self, ctx, user: discord.User):
        """Globally blacklists someone from the bot.

        user: discord.user
        """
        embed = discord.Embed(color=discord.Color.blurple())

        user_id = str(user.id).encode()
        if self.DB.blacklist.get(user_id):
            self.DB.blacklist.delete(user_id)

            embed.title = "User Unblacklisted"
            embed.description = f"***{user}*** has been unblacklisted"
            return await ctx.send(embed=embed)

        self.DB.blacklist.put(user_id, b"2")
        embed.title = "User Blacklisted"
        embed.description = f"**{user}** has been added to the blacklist"

        await ctx.send(embed=embed)

    @commands.command(name="gdownvote")
    async def global_downvote(self, ctx, user: discord.User):
        """Globally downvotes someones.

        user: discord.user
        """
        embed = discord.Embed(color=discord.Color.blurple())

        user_id = str(user.id).encode()
        if self.DB.blacklist.get(user_id):
            self.DB.blacklist.delete(user_id)

            embed.title = "User Undownvoted"
            embed.description = f"***{user}*** has been undownvoted"
            return await ctx.send(embed=embed)

        self.DB.blacklist.put(user_id, b"1")
        embed.title = "User Downvoted"
        embed.description = f"**{user}** has been added to the downvote list"

        await ctx.send(embed=embed)

    @commands.command()
    async def backup(self, ctx, number: int = None):
        """Sends the bot database backup as a json file.

        number: int
            Which backup to get.
        """
        if not number:
            number = int(self.DB.main.get(b"backup_number").decode())

            with open(f"backup/{number}backup.json", "rb") as file:
                return await ctx.send(file=discord.File(file, "backup.json"))

        number = min(10, max(number, 0))

        with open(f"backup/{number}backup.json", "rb") as file:
            await ctx.send(file=discord.File(file, "backup.json"))

    @commands.command(name="boot")
    async def boot_times(self, ctx):
        """Shows the average fastest and slowest boot times of the bot."""
        boot_times = self.DB.main.get(b"boot_times")

        embed = discord.Embed(color=discord.Color.blurple())

        if not boot_times:
            embed.description = "No boot times found"
            return await ctx.send(embed=embed)

        boot_times = orjson.loads(boot_times)

        msg = (
            f"\n\nAverage: {(sum(boot_times) / len(boot_times)):.5f}s"
            f"\nSlowest: {max(boot_times):.5f}s"
            f"\nFastest: {min(boot_times):.5f}s"
            f"\nLast Three: {boot_times[-3:]}"
        )

        embed.description = f"```{msg}```"
        await ctx.send(embed=embed)

    @commands.group()
    async def cache(self, ctx):
        """Command group for interacting with the cache."""
        if not ctx.invoked_subcommand:
            await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description=f"```Usage: {ctx.prefix}cache [wipe/list]```",
                )
            )

    @cache.command()
    async def wipe(self, ctx):
        """Wipes cache from the db."""
        self.DB.main.delete(b"cache")

        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(), description="```Wiped Cache```"
            )
        )

    @cache.command()
    async def list(self, ctx):
        """Lists the cached items in the db."""
        embed = discord.Embed(color=discord.Color.blurple())
        cache = self.DB.main.get(b"cache")

        if not cache or cache == b"{}":
            embed.description = "```Nothing has been cached```"
            return await ctx.send(embed=embed)

        cache = orjson.loads(cache)
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

    @commands.group()
    async def presence(self, ctx):
        """Command group for changing the bots precence"""
        if not ctx.invoked_subcommand:
            embed = discord.Embed(color=discord.Color.blurple())
            embed.description = (
                "```Usage: {}presence [game/streaming/listening/watching]```".format(
                    ctx.prefix
                )
            )
            await ctx.send(embed=embed)

    @presence.command()
    async def game(self, ctx, *, name):
        """Changes the bots status to playing a game.
        In the format of 'Playing [name]'

        name: str
        """
        await self.bot.change_presence(
            status=discord.Status.online,
            activity=discord.Game(name=name),
        )

    @presence.command()
    async def streaming(self, ctx, url, *, name):
        """Changes the bots status to streaming something.

        url: str
            The url of the stream
        name: str
            The name of the stream
        """
        await self.bot.change_presence(
            status=discord.Status.online,
            activity=discord.Streaming(url=url, name=name),
        )

    @presence.command()
    async def listening(self, ctx, *, name):
        """Changes the bots status to listening to something.
        In the format of 'Listening to [name]'

        name: str
        """
        await self.bot.change_presence(
            status=discord.Status.online,
            activity=discord.Activity(type=discord.ActivityType.listening, name=name),
        )

    @presence.command()
    async def watching(self, ctx, *, name):
        """Changes the bots status to listening to something.
        In the format of 'Watching [name]'

        name: str
        """
        await self.bot.change_presence(
            status=discord.Status.online,
            activity=discord.Activity(type=discord.ActivityType.watching, name=name),
        )

    @commands.command()
    async def perf(self, ctx, *, command):
        """Checks the timing of a command, while attempting to suppress HTTP calls.

        p.s just the command itself with nothing in it takes about 0.02ms

        command: str
            The command to run including arguments.
        """
        ctx.message.content = f"{ctx.prefix}{command}"
        new_ctx = await self.bot.get_context(ctx.message, cls=type(ctx))
        new_ctx.reply = new_ctx.send  # Reply ignores the PerformanceMocker

        # Intercepts the Messageable interface a bit
        new_ctx._state = PerformanceMocker()
        new_ctx.channel = PerformanceMocker()

        embed = discord.Embed(color=discord.Color.blurple())

        if not new_ctx.command:
            embed.description = "```No command found```"
            return await ctx.send(embed=embed)

        start = time.perf_counter()

        try:
            await new_ctx.command.invoke(new_ctx)
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

        embed.description = f"```css\n{result}: {(end - start) * 1000:.2f}ms```"
        await ctx.send(embed=embed)

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
    async def suin(
        self, ctx, channel: discord.TextChannel, member: discord.Member, *, command: str
    ):
        """Run a command as another user in another channel.

        channel: discord.TextChannel
            The channel to run the command in.
        member: discord.Member
            The member to run the command as.
        command: str
            The command name.
        """
        ctx.message.channel = channel
        ctx.message.author = member
        ctx.message.content = f"{ctx.prefix}{command}"
        new_ctx = await self.bot.get_context(ctx.message, cls=type(ctx))
        new_ctx.reply = new_ctx.send  # Can't reply to messages in other channels
        await self.bot.invoke(new_ctx)

    @commands.command()
    async def sudo(self, ctx, member: discord.Member, *, command: str):
        """Run a command as another user.

        member: discord.Member
            The member to run the command as.
        command: str
            The command name.
        """
        ctx.message.author = member
        ctx.message.content = f"{ctx.prefix}{command}"
        new_ctx = await self.bot.get_context(ctx.message, cls=type(ctx))
        await self.bot.invoke(new_ctx)

    @commands.command()
    async def status(self, ctx):
        await run_process("git fetch")
        status = await run_process("git status", True)

        embed = discord.Embed(color=discord.Color.blurple())
        embed.description = f"```ahk\n{' '.join(status)}```"

        await ctx.send(embed=embed)

    @commands.command(aliases=["deletecmd", "removecmd"])
    async def delete_command(self, ctx, command):
        """Removes command from the bot.

        command: str
            The command to remove.
        """
        self.bot.remove_command(command)
        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                description=f"```Removed command {command}```",
            )
        )

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
        self.DB.main.put(b"restart", b"1")

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

    @commands.group()
    async def rrole(self, ctx):
        if not ctx.invoked_subcommand:
            await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description=f"```Usage: {ctx.prefix}rrole [list/delete/start/edit]```",
                )
            )

    @rrole.command(name="list")
    async def rrole_list(self, ctx):
        """Sends a list of the message ids of current reaction roles."""
        msg = ""
        for message_id, roles in self.DB.rrole:
            msg += f"\n\n{message_id.decode()}: {orjson.loads(roles)}"
        await ctx.send(f"```{msg}```")

    @rrole.command(name="delete")
    async def rrole_delete(self, ctx, message_id: int):
        """Deletes a reaction role message and removes it from the db.

        message: int
            Id of the reaction role messgae to delete.
        """
        self.DB.rrole.delete(str(message_id).encode())
        message = ctx.channel.get_partial_message(message_id)
        await message.delete()

    @rrole.command()
    async def start(self, ctx, *emojis):
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
            if not channel:
                channel = ctx.channel
        except ValueError:
            channel = ctx.channel

        message = await channel.send(msg)

        try:
            for emoji in emojis:
                await message.add_reaction(emoji)
        except discord.errors.HTTPException:
            await message.delete()
            return await ctx.send("Invalid emoji")

        self.DB.rrole.put(
            str(message.id).encode(), orjson.dumps(dict(zip(emojis, roles)))
        )

    @rrole.command()
    async def edit(self, ctx, message: discord.Message, *emojis):
        """Edit a reaction role message.

        message: discord.Message
            The id of the reaction roles message.
        emojis: tuple
            A tuple of emojis.
        """
        reaction = self.DB.rrole.get(str(message.id).encode())

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

        self.DB.rrole.put(str(message.id).encode(), orjson.dumps(reaction))

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
