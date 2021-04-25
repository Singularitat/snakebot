import aiohttp
from datetime import datetime
import os
import asyncio
import subprocess
import ujson
from discord.ext import commands, tasks
import discord


class background_tasks(commands.Cog):
    """Commands related to the background tasks of the bot."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.stocks = self.bot.db.prefixed_db(b"stocks-")
        self.crypto = self.bot.db.prefixed_db(b"crypto-")
        self.start_tasks()

    def cog_unload(self):
        """When the cog is unloaded stop all running tasks."""
        for task in self.tasks:
            self.tasks[task].cancel()

    def start_tasks(self):
        """Finds all the tasks in the cog and starts them."""
        task_dict = {}

        for task in dir(background_tasks):
            task_obj = getattr(self, task)

            if isinstance(task_obj, tasks.Loop):
                task_obj.start()
                task_dict[task] = task_obj

        self.tasks = task_dict

    @commands.group(hidden=True)
    @commands.is_owner()
    async def task(self, ctx):
        """The task command group."""
        if ctx.invoked_subcommand is None:
            await ctx.send("```No subcommand passed```")

    @task.command()
    async def restart(self, ctx, task):
        """Restarts a background task.

        task: str
            The name of the task to restart.
        """
        try:
            getattr(self, task).restart()
            await ctx.send(f"{task} restarted")
        except AttributeError:
            return await ctx.send("```Task not found```")

    @task.command()
    async def start(self, ctx, task):
        """Starts a background task.

        task: str
            The name of the task to start.
        """
        try:
            getattr(self, task).start()
            await ctx.send(f"{task} started")
        except AttributeError:
            return await ctx.send("```Task not found```")

    @task.command()
    async def stop(self, ctx, task):
        """Stops a background task.

        task: str
            The name of the task to stop.
        """
        try:
            getattr(self, task).stop()
            await ctx.send(f"{task} stopped")
        except AttributeError:
            return await ctx.send("```Task not found```")

    @task.command()
    async def list(self, ctx):
        """Lists background tasks.

        Example

        Name:               Interval:      Running/Failed/Count

        backup_bot          2h 0m 0s       True/False/10
        check_end_dates     0h 0m 10s      True/False/7200
        update_bot          0h 5m 0s       True/False/240
        update_languages    0h 0m 0s       False/False/1
        update_stocks       0h 30m 0s      True/False/40
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
        """Updates stock data every half hour."""
        url = "https://api.nasdaq.com/api/screener/stocks?limit=50000"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.67 Safari/537.36",
            "accept-language": "en-US,en;q=0.9",
        }
        async with aiohttp.ClientSession(headers=headers) as session, session.get(
            url
        ) as response:
            stocks = await response.json()

        with self.stocks.write_batch() as wb:
            for stock in stocks["data"]["table"]["rows"]:
                stock_data = {}
                stock_data["name"] = stock["name"]
                stock_data["price"] = stock["lastsale"][1:]
                stock_data["change"] = stock["netchange"]
                stock_data["%change"] = (
                    stock["pctchange"][:-1] if stock["pctchange"] != "--" else 0
                )
                stock_data["cap"] = stock["marketCap"]

                wb.put(
                    stock["symbol"].encode(),
                    ujson.dumps(stock_data).encode(),
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

        if "poetry.lock" in diff:
            await self.run_process("poetry install")

        for ext in [f[:-3] for f in os.listdir("cogs") if f.endswith(".py")]:
            try:
                self.bot.reload_extension(f"cogs.{ext}")
            except Exception as e:
                if isinstance(e, commands.errors.ExtensionNotLoaded):
                    self.bot.load_extension(f"cogs.{ext}")

    @tasks.loop(hours=2)
    async def backup_bot(self):
        """Makes a backup of the db every two hours."""
        os.makedirs("backup/", exist_ok=True)
        time = datetime.now()
        with open(f"backup/{time.hour // 2}backup.json", "w") as file:
            json = "".join(
                [
                    f'"{key.decode()}": "{value.decode()}", '
                    if '"' not in value.decode()
                    else f'"{key.decode()}": {value.decode()}, '
                    for key, value in self.bot.db
                ]
            )
            file.write(f"{{{json[:-2]}}}")

    @tasks.loop(count=1)
    async def update_languages(self):
        """Updates pistons supported languages for the run command."""
        url = "https://emkc.org/api/v1/piston/versions"
        async with aiohttp.ClientSession() as session, session.get(url) as page:
            data = await page.json()

        languages = set()

        for language in data:
            languages.update(set(language["aliases"]))
            languages.add(language["name"])

        self.bot.db.put(b"languages", ujson.dumps(list(languages)).encode())

    @tasks.loop(minutes=20)
    async def crypto_update(self):
        """Updates crypto currency data every 20 minutes."""
        # If we have just restarted we don't want to run this again
        # As free coinmarketcap API keys can only be used 333 per day
        if self.bot.db.get(b"restart") == b"1":
            self.bot.db.put(b"restart", b"0")
            return

        url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
        parameters = {"start": "1", "limit": "200", "convert": "NZD"}
        headers = {
            "Accepts": "application/json",
            "X-CMC_PRO_API_KEY": self.bot.coinmarketcap,
        }

        async with aiohttp.ClientSession() as session:
            response = await session.get(url, params=parameters, headers=headers)
            data = await response.json()

        with self.crypto.write_batch() as wb:
            for coin in data["data"]:
                wb.put(
                    coin["symbol"].encode(),
                    ujson.dumps(
                        {
                            "name": coin["name"],
                            "price": coin["quote"]["NZD"]["price"],
                            "circulating_supply": coin["circulating_supply"],
                            "max_supply": coin["max_supply"] or 0,
                            "market_cap": coin["quote"]["NZD"]["market_cap"],
                            "change_24h": coin["quote"]["NZD"]["percent_change_24h"],
                            "volume_24h": coin["quote"]["NZD"]["volume_24h"],
                        }
                    ).encode(),
                )


def setup(bot):
    bot.add_cog(background_tasks(bot))
