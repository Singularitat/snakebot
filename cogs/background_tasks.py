import asyncio
import os
import subprocess

from discord.ext import commands, tasks
import aiohttp
import discord
import orjson

from cogs.utils.relativedelta import pretty_time
import cogs.utils.database as DB


class background_tasks(commands.Cog):
    """Commands related to the background tasks of the bot."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.start_tasks()

    def cog_unload(self):
        """When the cog is unloaded stop all running tasks."""
        for task in self.tasks:
            self.tasks[task].cancel()

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
                    f"{task.hours}h {task.minutes}m {task.seconds}s",
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
        for task in self.tasks:
            task_obj = self.tasks[task]
            msg += "{:<20}{:<15}{}/{}/{}\n".format(
                task,
                f"{task_obj.hours}h {task_obj.minutes}m {task_obj.seconds}s",
                task_obj.is_running(),
                task_obj.failed(),
                task_obj.current_loop,
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
        async with aiohttp.ClientSession(headers=headers) as session, session.get(
            url
        ) as response:
            stocks = await response.json()

        with DB.stocks.write_batch() as wb:
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

    async def run_process(self, command):
        """Runs a shell command and returns the output.

        command: str
            The command to run.
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

        return "".join([output.decode() for output in result]).split()

    @tasks.loop(minutes=5)
    async def update_bot(self):
        """Tries to update every 5 minutes and then reloads if needed."""
        pull = await self.run_process("git pull")

        if pull[:4] == ["Already", "up", "to", "date."]:
            return

        diff = await self.run_process("git diff --name-only HEAD@{0} HEAD@{1}")

        if "requirements.txt" in diff:
            await self.run_process("pip install -r ./requirements.txt")

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
        if DB.db.get(b"restart") == b"1":
            return DB.db.delete(b"restart")

        number = DB.db.get(b"backup_number")

        if not number:
            number = -1
        else:
            number = int(number.decode())

        number = (number + 1) % 11

        DB.db.put(b"backup_number", str(number).encode())

        os.makedirs("backup/", exist_ok=True)
        with open(f"backup/{number}backup.json", "w", encoding="utf-8") as file:
            # I don't know why I did this as a jumbled mess but I did
            # Basically it just formats the db to json
            json = "".join(
                [
                    f'"{key.decode()}": "{value.decode()}", '
                    if '"' not in value.decode()
                    else f'"{key.decode()}": {value.decode()}, '
                    for key, value in DB.db
                    if not key.startswith(b"crypto-") and not key.startswith(b"stocks-")
                ]
            )
            file.write(f"{{{json[:-3]}}}")

    @tasks.loop(count=1)
    async def update_languages(self):
        """Updates pistons supported languages for the run command."""
        url = "https://emkc.org/api/v2/piston/runtimes"
        async with aiohttp.ClientSession() as session, session.get(url) as page:
            data = await page.json()

        aliases = set()
        languages = []

        for language in data:
            aliases.update(language["aliases"])
            aliases.add(language["language"])
            languages.append(language["language"])

        DB.db.put(b"languages", orjson.dumps(languages))
        DB.db.put(b"aliases", orjson.dumps(list(aliases)))

    @tasks.loop(minutes=10)
    async def update_crypto(self):
        """Updates crypto currency data every 10 minutes."""
        url = "https://api.coinmarketcap.com/data-api/v3/cryptocurrency/listing?limit=50000&convert=NZD&cryptoType=coins"
        async with aiohttp.ClientSession() as session, session.get(url) as response:
            crypto = await response.json()

        with DB.crypto.write_batch() as wb:
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
