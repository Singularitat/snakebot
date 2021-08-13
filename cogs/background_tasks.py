import os

from discord.ext import commands, tasks
import discord
import orjson

from cogs.utils.relativedelta import pretty_time
from cogs.utils.useful import run_process


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

            if task_name in self.tasks:
                task = self.tasks[task_name]
                embed.title = f"{task_name.replace('_', ' ').title()} Task"
                embed.description = (
                    "```Running: {}\nFailed: {}\nCount: {}"
                    "\n\nNext Loop:\n{}\n\nInterval:\n{}```"
                ).format(
                    task.is_running(),
                    task.failed(),
                    task.current_loop,
                    pretty_time(task.next_iteration.replace(tzinfo=None), False),
                    f"{task.hours:.0f}h {task.minutes:.0f}m {task.seconds:.0f}s",
                )
                return await ctx.send(embed=embed)

            embed.description = (
                f"```Usage: {ctx.prefix}task [restart/start/stop/list]```"
            )
            await ctx.send(embed=embed)

    @task.command()
    async def restart(self, ctx, task_name=None):
        """Restarts a background task.

        task: str
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

        task: str
            The name of the task to start.
            If not passed in then all tasks are started
        """
        embed = discord.Embed(color=discord.Color.blurple())

        if not task_name:
            for task in self.tasks.values():
                task.start()
            embed.description = "```Started all tasks```"
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

        task: str
            The name of the task to stop.
            If not passed in then all tasks are stopped
        """
        embed = discord.Embed(color=discord.Color.blurple())

        if not task_name:
            for task in self.tasks.values():
                task.stop()
            embed.description = "```Stopped all tasks```"
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

        task: str
            The name of the task to stop.
            If not passed in then all tasks are canceled
        """
        embed = discord.Embed(color=discord.Color.blurple())

        if not task_name:
            for task in self.tasks.values():
                task.cancel()
            embed.description = "```Canceled all tasks```"
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

        Name:               Interval:      Running/Failed/Count:

        update_stocks       0h 10m 0s      True/False/146
        update_bot          0h 5m 0s       True/False/291
        backup              6h 0m 0s       True/False/5
        update_languages    0h 0m 0s       False/False/0
        update_crypto       0h 10m 0s      True/False/146
        """
        embed = discord.Embed(color=discord.Color.blurple())

        msg = "Name:               Interval:      Running/Failed/Count:\n\n"
        for name, task in self.tasks.items():
            msg += "{:<20}{:<15}{}/{}/{}\n".format(
                name,
                f"{task.hours:.0f}h {task.minutes:.0f}m {task.seconds:.0f}s",
                task.is_running(),
                task.failed(),
                task.current_loop,
            )

        embed.description = f"```\n{msg}```"
        await ctx.send(embed=embed)

    @tasks.loop(minutes=10)
    async def update_stocks(self):
        """Updates stock data every 10 minutes."""
        url = "https://api.nasdaq.com/api/screener/stocks?limit=50000"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.67 Safari/537.36",
            "accept-language": "en-US,en;q=0.9",
        }
        async with self.bot.client_session.get(url, headers=headers) as response:
            stocks = await response.json()

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
        pull = await run_process("git pull")

        if pull[:4] == ["Already", "up", "to", "date."]:
            return

        diff = await run_process("git diff --name-only HEAD@{0} HEAD@{1}")

        if "requirements.txt" in diff:
            await run_process("pip install -r ./requirements.txt")

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
    async def update_languages(self):
        """Updates pistons supported languages for the run command."""
        url = "https://emkc.org/api/v2/piston/runtimes"
        async with self.bot.client_session.get(url) as page:
            data = await page.json()

        aliases = set()
        languages = []

        for language in data:
            aliases.update(language["aliases"])
            aliases.add(language["language"])
            languages.append(language["language"])

        self.DB.main.put(b"languages", orjson.dumps(languages))
        self.DB.main.put(b"aliases", orjson.dumps(list(aliases)))

    @tasks.loop(minutes=10)
    async def update_crypto(self):
        """Updates crypto currency data every 10 minutes."""
        url = "https://api.coinmarketcap.com/data-api/v3/cryptocurrency/listing?limit=50000&convert=NZD&cryptoType=coins"
        async with self.bot.client_session.get(url) as response:
            crypto = await response.json()

        with self.DB.crypto.write_batch() as wb:
            for coin in crypto["data"]["cryptoCurrencyList"]:
                if "price" not in coin["quotes"][0]:
                    continue

                wb.put(
                    coin["symbol"].encode(),
                    orjson.dumps(
                        {
                            "name": coin["name"],
                            "id": coin["id"],
                            "price": coin["quotes"][0]["price"],
                            "circulating_supply": coin["circulatingSupply"],
                            "max_supply": coin.get("maxSupply", 0),
                            "market_cap": coin["quotes"][0].get("marketCap", 0),
                            "change_24h": coin["quotes"][0]["percentChange24h"],
                            "volume_24h": coin["quotes"][0].get("volume24h", 0),
                        }
                    ),
                )


def setup(bot):
    """Starts the backgroud tasks cog"""
    bot.add_cog(background_tasks(bot))
