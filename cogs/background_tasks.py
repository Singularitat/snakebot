import asyncio
import os
from datetime import datetime

import discord
import orjson
from discord.ext import commands, tasks


class background_tasks(commands.Cog):
    """Commands related to the background tasks of the bot."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.DB = bot.DB
        self.start_tasks()

    def cog_unload(self):
        """When the cog is unloaded stop all running tasks."""
        for task in self.tasks.values():
            task.cancel()

    async def cog_check(self, ctx):
        """Checks if the member is an owner.

        ctx: commands.Context
        """
        return ctx.author.id in self.bot.owner_ids

    def start_tasks(self):
        """Finds all the tasks in the cog and starts them.
        This also builds a dictionary of the tasks so we can access them later.
        """
        self.tasks = {}

        for name, task_obj in vars(background_tasks).items():
            if isinstance(task_obj, tasks.Loop):
                task = getattr(self, name)
                task.start()
                self.tasks[name] = task

    @commands.group(hidden=True)
    async def task(self, ctx):
        """The task command group."""
        if not ctx.invoked_subcommand:
            embed = discord.Embed(color=discord.Color.blurple())
            task_name = ctx.subcommand_passed

            if task_name not in self.tasks:
                embed.description = (
                    f"```Usage: {ctx.prefix}task [restart/start/stop/list]```"
                )
                return await ctx.send(embed=embed)

            task = self.tasks[task_name]
            embed.title = f"{task_name.replace('_', ' ').title()} Task"
            embed.add_field(name="Running", value=task.is_running())
            embed.add_field(name="Failed", value=task.failed())
            embed.add_field(name="Count", value=task.current_loop)
            if task.next_iteration:
                embed.add_field(
                    name="Next Loop",
                    value=f"**<t:{task.next_iteration.timestamp():.0f}:R>**",
                )
            embed.add_field(
                name="Interval",
                value=f"{task.hours:.0f}h {task.minutes:.0f}m {task.seconds:.0f}s",
            )
            await ctx.send(embed=embed)

    @task.command()
    async def restart(self, ctx, task_name=None):
        """Restarts a background task.

        task_name: str
            The name of the task to restart.
            If not passed in then all tasks are restarted
        """
        embed = discord.Embed(color=discord.Color.blurple())

        if not task_name:
            for task in self.tasks.values():
                task.restart()
            embed.description = "```Restarted all tasks```"
            return await ctx.send(embed=embed)

        if task_name not in self.tasks:
            embed.description = "```Task not found```"
            return await ctx.send(embed=embed)

        self.tasks[task_name].restart()
        embed.description = f"{task_name} restarted"
        await ctx.send(embed=embed)

    @task.command()
    async def start(self, ctx, task_name=None):
        """Starts a background task.

        task_name: str
            The name of the task to start.
            If not passed in then all tasks are started
        """
        embed = discord.Embed(color=discord.Color.blurple())

        if not task_name:
            for name, task in self.tasks.items():
                task.cancel()
                embed.add_field(
                    name=name, value=f">>> ```ahk\nRunning: {task.is_running()}```"
                )
            embed.description = "```Tried to start all tasks```"
            return await ctx.send(embed=embed)

        if task_name not in self.tasks:
            embed.description = "```Task not found```"
            return await ctx.send(embed=embed)

        self.tasks[task_name].start()
        embed.description = f"{task_name} started"
        await ctx.send(embed=embed)

    @task.command()
    async def stop(self, ctx, task_name=None):
        """Stops a background task.

        Unlike cancel it waits for the task to finish its current loop

        task_name: str
            The name of the task to stop.
            If not passed in then all tasks are stopped
        """
        embed = discord.Embed(color=discord.Color.blurple())

        if not task_name:
            for name, task in self.tasks.items():
                task.cancel()
                embed.add_field(
                    name=name, value=f">>> ```ahk\nRunning: {task.is_running()}```"
                )
            embed.description = "```Tried to stop all tasks```"
            return await ctx.send(embed=embed)

        if task_name not in self.tasks:
            embed.description = "```Task not found```"
            return await ctx.send(embed=embed)

        self.tasks[task_name].stop()
        embed.description = f"{task_name} stopped"
        await ctx.send(embed=embed)

    @task.command()
    async def cancel(self, ctx, task_name=None):
        """Cancels a background task.

        Unlike stop it ends the task immediately

        task_name: str
            The name of the task to stop.
            If not passed in then all tasks are canceled
        """
        embed = discord.Embed(color=discord.Color.blurple())

        if not task_name:
            for name, task in self.tasks.items():
                task.cancel()
                embed.add_field(
                    name=name, value=f">>> ```ahk\nRunning: {task.is_running()}```"
                )
            embed.description = "```Tried to cancel all tasks```"
            return await ctx.send(embed=embed)

        if task_name not in self.tasks:
            embed.description = "```Task not found```"
            return await ctx.send(embed=embed)

        self.tasks[task_name].cancel()
        embed.description = f"{task_name} canceled"
        await ctx.send(embed=embed)

    @task.command()
    async def list(self, ctx):
        """Lists background tasks.

        Example

        Name:               Interval:    Running: Failed: Count:

        get_stocks          0h  30m 0s   True     False   161
        update_bot          0h  5m  0s   True     False   970
        backup              6h  0m  0s   True     False   13
        get_languages       0h  0m  0s   False    False   0
        get_crypto          0h  30m 0s   True     False   161
        get_domain          24h 0m  0s   True     False   3
        """
        embed = discord.Embed(color=discord.Color.blurple())

        msg = "Name:               Interval:    Running: Failed: Count:\n\n"
        for name, task in self.tasks.items():
            msg += "{:<20}{:<4}{:<4}{:<5}{:<9}{:<8}{}\n".format(
                name,
                f"{task.hours:.0f}h",
                f"{task.minutes:.0f}m",
                f"{task.seconds:.0f}s",
                str(task.is_running()),
                str(task.failed()),
                task.current_loop,
            )

        embed.description = f"```prolog\n{msg}```"
        await ctx.send(embed=embed)

    @tasks.loop(hours=1)
    async def get_stocks(self):
        """Updates stock data every hour."""
        url = "https://api.nasdaq.com/api/screener/stocks?limit=50000"
        headers = {
            "authority": "api.nasdaq.com",
            "cache-control": "max-age=0",
            "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="96"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "sec-fetch-site": "none",
            "sec-fetch-mode": "navigate",
            "sec-fetch-user": "?1",
            "sec-fetch-dest": "document",
            "accept-language": "en-US,en;q=0.9",
        }
        current_cookies = self.DB.main.get(b"stock-cookies")
        if not current_cookies:
            current_cookies = {}
        else:
            current_cookies = orjson.loads(current_cookies)

        async with self.bot.client_session.get(
            url, headers=headers, cookies=current_cookies
        ) as resp:
            next_cookies = {}
            for header, value in resp.raw_headers:
                if header != b"Set-Cookie":
                    continue
                name, cookie = value.decode().split("=", 1)
                next_cookies[name] = cookie.split(":", 1)[0]
            self.DB.main.put(b"stock-cookies", orjson.dumps(next_cookies))
            stocks = await resp.json()

        if not stocks:
            return

        with self.DB.stocks.write_batch() as wb:
            for stock in stocks["data"]["table"]["rows"]:
                stock_data = {
                    "name": stock["name"],
                    "price": stock["lastsale"][1:],
                    "change": stock["netchange"],
                    "%change": stock["pctchange"][:-1]
                    if stock["pctchange"] != "--"
                    else 0,
                    "cap": stock["marketCap"],
                }

                wb.put(
                    stock["symbol"].encode(),
                    orjson.dumps(stock_data),
                )

    @tasks.loop(minutes=5)
    async def update_bot(self):
        """Tries to update every 5 minutes and then reloads if needed."""
        pull = await self.bot.run_process("git pull")

        if pull[:4] == ["Already", "up", "to", "date."]:
            return

        diff = await self.bot.run_process("git diff --name-only HEAD@{0} HEAD@{1}")

        if "requirements.txt" in diff:
            await self.bot.run_process("pip install -r ./requirements.txt")

        for ext in (
            file.removesuffix(".py")
            for file in os.listdir("cogs")
            if file.endswith(".py") and f"cogs/{file}" in diff
        ):
            try:
                self.bot.reload_extension(f"cogs.{ext}")
            except Exception as e:
                if isinstance(e, commands.errors.ExtensionNotLoaded):
                    self.bot.load_extension(f"cogs.{ext}")

    @tasks.loop(hours=6)
    async def backup(self):
        """Makes a backup of the db every 6 hours."""
        if self.DB.main.get(b"restart") == b"1":
            return self.DB.main.delete(b"restart")

        number = self.DB.main.get(b"backup_number")

        if not number:
            number = -1
        else:
            number = int(number.decode())

        number = (number + 1) % 11

        self.DB.main.put(b"backup_number", str(number).encode())

        os.makedirs("backup/", exist_ok=True)
        with open(f"backup/{number}backup.json", "w", encoding="utf-8") as file:
            database = {}

            excluded = (
                b"crypto",
                b"stocks",
                b"boot_times",
                b"tiolanguages",
                b"helloworlds",
                b"docs",
            )

            for key, value in self.DB.main:
                if key.split(b"-")[0] not in excluded:
                    if value[:1] in [b"{", b"["]:
                        value = orjson.loads(value)
                    else:
                        value = value.decode()
                    database[key.decode()] = value

            file.write(str(database))

    @tasks.loop(count=1)
    async def get_languages(self):
        """Updates pistons supported languages for the run command."""
        url = "https://emkc.org/api/v2/piston/runtimes"
        data = await self.bot.get_json(url)

        if data:
            aliases = set()
            languages = set()

            for language in data:
                aliases.update(language["aliases"])
                aliases.add(language["language"])
                languages.add(language["language"])

            self.DB.main.put(b"languages", orjson.dumps(list(languages)))
            self.DB.main.put(b"aliases", orjson.dumps(list(aliases)))

        url = "https://tio.run/languages.json"
        data = await self.bot.get_json(url)

        if not data:
            return

        self.DB.main.put(b"tiolanguages", orjson.dumps([*data]))

        hello_worlds = {}

        for language in data:
            for request in data[language]["tests"]["helloWorld"]["request"]:
                if request["command"] == "F" and ".code.tio" in request["payload"]:
                    hello_worlds[language] = request["payload"][".code.tio"]

        self.DB.main.put(b"helloworlds", orjson.dumps(hello_worlds))

    @tasks.loop(minutes=30)
    async def get_crypto(self):
        """Updates crypto currency data every 30 minutes."""
        url = "https://api.coinmarketcap.com/data-api/v3/cryptocurrency/listing?limit=50000&convert=NZD&cryptoType=coins"
        crypto = await self.bot.get_json(url)

        if not crypto:
            return

        with self.DB.crypto.write_batch() as wb:
            for coin in crypto["data"]["cryptoCurrencyList"]:
                if "price" not in coin["quotes"][0]:
                    continue

                timestamp = datetime.fromisoformat(
                    coin["quotes"][0]["lastUpdated"][:-1]
                ).timestamp()

                wb.put(
                    coin["symbol"].encode(),
                    orjson.dumps(
                        {
                            "name": coin["name"],
                            "id": coin["id"],
                            "price": coin["quotes"][0]["price"],
                            "circulating_supply": int(coin["circulatingSupply"]),
                            "max_supply": int(coin.get("maxSupply", 0)),
                            "market_cap": coin["quotes"][0].get("marketCap", 0),
                            "change_24h": coin["quotes"][0]["percentChange24h"],
                            "volume_24h": coin["quotes"][0].get("volume24h", 0),
                            "timestamp": int(timestamp),
                        }
                    ),
                )

    @tasks.loop(hours=24)
    async def get_domain(self):
        """Updates the domain used for the tempmail command."""
        url = "https://api.mail.tm/domains?page=1"
        async with self.bot.client_session.get(url) as resp:
            data = await resp.json()

        domain = data["hydra:member"][0]["domain"]
        self.DB.main.put(b"tempdomain", domain.encode())

    def _get_documentation(self, obj, wb):
        if not getattr(obj, "__doc__", None):
            return
        if not hasattr(obj, "__name__"):
            return

        name = getattr(obj, "__qualname__", None) or obj.__name__
        wb.put(name.encode(), obj.__doc__.encode())

        for name in dir(obj):
            if name.startswith("_"):
                continue
            sub_obj = getattr(obj, name, None)
            if (
                sub_obj
                and getattr(sub_obj, "__module__", None)
                and sub_obj.__module__.startswith("discord")
            ):
                self._get_documentation(sub_obj, wb)

    @tasks.loop(count=1)
    async def get_documentation(self):
        """Gets the documentation of all discord objects from their __doc__ attribute."""
        with self.DB.docs.write_batch() as wb:
            self._get_documentation(discord, wb)
            self._get_documentation(commands, wb)
            self._get_documentation(tasks, wb)

    @tasks.loop(hours=2)
    async def get_currencies(self):
        url = "https://api.vatcomply.com/rates?base=NZD"
        rates = await self.bot.get_json(url)

        url = "https://api.vatcomply.com/currencies"
        symbols = await self.bot.get_json(url)

        if not symbols or not rates:
            return

        for key, rate in rates["rates"].items():
            symbols[key]["rate"] = rate

        symbols["NZD"]["symbol"] = "$"
        symbols["CAD"]["symbol"] = "$"
        symbols["AUD"]["symbol"] = "$"

        self.DB.main.put(b"currencies", orjson.dumps(symbols))

    @get_stocks.before_loop
    async def wait_for_proxy(self):
        """Make sure we have proxy before we request stocks."""
        if self.tasks["get_stocks"].current_loop == 0:
            await asyncio.sleep(3)


def setup(bot):
    """Starts the background tasks cog"""
    bot.add_cog(background_tasks(bot))
