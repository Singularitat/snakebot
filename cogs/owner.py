import asyncio
import cProfile
import difflib
import os
import pstats
import textwrap
import time
import traceback
from contextlib import redirect_stdout
from io import StringIO

import discord
import orjson
from discord.ext import commands, pages


class PerformanceMocker:
    """A mock object that can also be used in await expressions."""

    def __init__(self):
        self.loop = asyncio.get_running_loop()

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
    async def logs(self, ctx):
        """Paginates over the logs."""
        with open("bot.log") as file:
            lines = file.readlines()

        embeds = []

        for i in range(0, len(lines), 20):
            chunk = "".join(lines[i : i + 20])
            embeds.append(
                discord.Embed(
                    color=discord.Color.blurple(), description=f"```{chunk}```"
                )
            )

        paginator = pages.Paginator(pages=embeds)
        await paginator.send(ctx)

    @commands.command(aliases=["type"])
    async def findtype(self, ctx, snowflake: int):
        async def found_message(type_name: str) -> None:
            await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description=f"**ID**: `{snowflake}`\n"
                    f"**Type:** `{type_name.capitalize()}`\n"
                    f"**Created:** <t:{((snowflake >> 22) + 1420070400000)//1000}>",
                )
            )

        await ctx.trigger_typing()

        emoji = await self.bot.client_session.head(
            f"https://cdn.discordapp.com/emojis/{snowflake}"
        )
        if emoji.status == 200:
            return await found_message("emoji")

        try:
            if await ctx.fetch_message(snowflake):
                return await found_message("message")
        except discord.NotFound:
            pass

        types = (
            ("channel", True),
            ("user", True),
            ("guild", True),
            ("sticker", True),
            ("stage_instance", True),
            ("webhook", False),
            ("widget", False),
        )

        for obj_type, has_get_method in types:
            if has_get_method and getattr(self.bot, f"get_{obj_type}")(snowflake):
                return await found_message(obj_type)
            try:
                if await getattr(self.bot, f"fetch_{obj_type}")(snowflake):
                    return await found_message(obj_type)
            except discord.Forbidden:
                if (
                    obj_type != "guild"
                ):  # Even if the guild doesn't exist it says it is forbidden rather than not found
                    return await found_message(obj_type)
            except discord.NotFound:
                pass

        await ctx.reply("Cannot find type of object that this id is for")

    @commands.command(aliases=["d", "docs"])
    async def doc(self, ctx, search):
        """Gets the shows the dunder doc attribute of a discord object.

        search: str
            The discord object.
        """
        docs = self.DB.docs.get(search.encode())
        if not docs:
            names = [
                name.decode() for name in self.DB.docs.iterator(include_value=False)
            ]
            matches = "\n".join(
                difflib.get_close_matches(
                    search,
                    names,
                    n=9,
                    cutoff=0.0,
                )
            )
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(), description=f"```less\n{matches}```"
                )
            )

        docs = docs.decode()

        if len(docs) > 2000:
            return await ctx.send(file=discord.File(StringIO(docs), "doc.txt"))

        await ctx.send(f"```ahk\n{docs}```")

    @commands.command(pass_context=True, hidden=True, name="eval")
    async def _eval(self, ctx, *, code: str):
        """Evaluates code.

        code: str
        """
        env = {
            "bot": self.bot,
            "ctx": ctx,
            "channel": ctx.channel,
            "author": ctx.author,
            "guild": ctx.guild,
            "message": ctx.message,
        }

        env.update(globals())

        if code.startswith("```") and code.endswith("```"):
            code = "\n".join(code.split("\n")[1:-1])
        else:
            code = code.strip("` \n")

        stdout = StringIO()

        func = f'async def func():\n{textwrap.indent(code, "  ")}'

        try:
            exec(func, env)
        except Exception as e:
            return await ctx.send(f"```ml\n{e.__class__.__name__}: {e}\n```")

        func = env["func"]

        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception:
            value = stdout.getvalue()
            return await ctx.send(f"```py\n{value}{traceback.format_exc()}\n```")

        embed = discord.Embed(color=discord.Color.blurple())
        embed.add_field(name="stdout", value=stdout.getvalue() or "None", inline=False)
        embed.add_field(name="Return Value", value=ret, inline=False)

        return await ctx.send(embed=embed)

    @commands.command()
    async def profile(self, ctx, *, command):
        """Profiles a command.

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

    @commands.command(name="wipeblacklist")
    async def wipe_blacklist(self, ctx):
        """Wipes everyone from the blacklist list includes downvoted members."""
        for member, value in self.DB.blacklist:
            self.DB.blacklist.delete(member)

    @commands.group(invoke_without_command=True)
    async def db(self, ctx):
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

            value = (await ctx.message.attachments[0].read()).decode()

        self.DB.main.put(key.encode(), value.encode())

        length = len(value)
        if length < 1986:
            embed.description = f"```Put {value} at {key}```"
        else:
            embed.description = f"```Put {length} characters at {key}```"
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
    @commands.guild_only()
    async def clear_infractions(self, ctx, member: discord.Member):
        """Removes all infractions of a member.

        member: discord.Member
        """
        self.DB.infractions.delete(f"{ctx.guild.id}-{member.id}".encode())

    @commands.command(aliases=["showinf"])
    @commands.guild_only()
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
    @commands.guild_only()
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

    @commands.group(invoke_without_command=True)
    async def cache(self, ctx):
        """Command group for interacting with the cache."""
        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                description=f"```Usage: {ctx.prefix}cache [wipe/list]```",
            )
        )

    @cache.command()
    async def wipe(self, ctx):
        """Wipes cache from the db."""
        self.bot.cache.clear()

        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(), description="```prolog\nWiped Cache```"
            )
        )

    @cache.command(name="list")
    async def _list(self, ctx):
        """Lists the cached items in the db."""
        embed = discord.Embed(color=discord.Color.blurple())
        cache = self.bot.cache

        if not cache:
            embed.description = "```Nothing has been cached```"
            return await ctx.send(embed=embed)

        embed.description = "```\n{}```".format("\n".join(cache))
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
            f"```Successfully {ternary} the {command.qualified_name} command```"
        )
        await ctx.send(embed=embed)

    @commands.group(invoke_without_command=True)
    async def presence(self, ctx):
        """Command group for changing the bots presence"""
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
            error = traceback.format_exc().replace("`", "`\u200b")

            await ctx.send(f"```py\n{error}\n```")
        else:
            end = time.perf_counter()
            result = "Success"

        embed.description = f"```css\n{result}: {(end - start) * 1000:.2f}ms```"
        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
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
    async def sudo(self, ctx, member: discord.Member | discord.User, *, command: str):
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
        await self.bot.run_process("git fetch")
        status = await self.bot.run_process("git status", True)

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
                if isinstance(e, discord.errors.ExtensionNotLoaded):
                    self.bot.load_extension(f"cogs.{ext}")
                embed.description = f"```{type(e).__name__}: {e}```"
                return await ctx.send(embed=embed)

        embed.title = "Extensions restarted."
        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    """Starts owner cog."""
    bot.add_cog(owner(bot))
