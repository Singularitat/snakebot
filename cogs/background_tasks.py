import lxml
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

    def __init__(self, bot):
        self.bot = bot
        self.stocks = self.bot.db.prefixed_db(b"stocks-")
        self.update_stocks.start()
        self.update_bot.start()
        self.backup_bot.start()
        self.update_languages.start()
        self.check_end_dates.start()

    def cog_unload(self):
        self.update_stocks.stop()
        self.update_bot.stop()
        self.backup_bot.stop()
        self.update_languages.stop()
        self.check_end_dates.stop()

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
        for task in dir(background_tasks):
            task_obj = getattr(self, task)
            if isinstance(task_obj, tasks.Loop):
                msg += "{:<20}{:<15}{}/{}/{}\n".format(
                    task,
                    f"{task_obj.hours}h {task_obj.minutes}m {task_obj.seconds}s",
                    task_obj.is_running(),
                    task_obj.failed(),
                    task_obj.current_loop,
                )

        embed.description = f"```\n{msg}```"
        await ctx.send(embed=embed)

    async def stockupdate(self, url):
        """Fetches stocks then updates the database.

        url: str
            The yahoo finance url to fetch stocks from.
        """
        async with aiohttp.ClientSession() as session, session.get(url) as page:
            soup = lxml.html.fromstring(await page.text())

        with self.stocks.write_batch() as wb:
            for table in soup.xpath('.//table[@class="W(100%)"]'):
                table_body = table.find("tbody")
                rows = table_body.findall("tr")
                for row in rows:
                    cols = [col.text_content() for col in row.findall("td")]

                    price = cols[2]
                    name = cols[0]

                    if price == "N/A" or len(name) > 6 or float(price) == 0:
                        continue

                    stock_data = {}
                    stock_data["name"] = cols[1]
                    stock_data["price"] = price
                    stock_data["change"] = cols[3]
                    stock_data["%change"] = cols[4]
                    stock_data["volume"] = cols[5]
                    stock_data["3Mvolume"] = cols[6]
                    stock_data["cap"] = cols[7]

                    wb.put(
                        name.replace(".NZ", "").encode(),
                        ujson.dumps(stock_data).encode(),
                    )

    @tasks.loop(minutes=30)
    async def update_stocks(self):
        """Updates stock prices every half hour."""
        await self.stockupdate(
            "https://nz.finance.yahoo.com/most-active?offset=0&count=200"
        )
        await self.stockupdate(
            "https://nz.finance.yahoo.com/most-active?offset=200&count=200"
        )
        await self.stockupdate(
            "https://finance.yahoo.com/most-active?offset=0&count=200"
        )

    async def run_process(self, command):
        process = await asyncio.create_subprocess_shell(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        result = await process.communicate()

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

        languages = []

        for language in data:
            for alias in language.values():
                if isinstance(alias, list):
                    languages += alias
                elif not alias[0].isnumeric():
                    languages.append(alias)

        self.bot.db.put(b"languages", ujson.dumps(languages).encode())

    async def date_check(self, db_key: bytes):
        """Checks end dates in a dictionary then yields the value.

        db_key: bytes
            A key to get a dictionary from the db.
        """
        dictionary = self.bot.db.get(db_key)

        if dictionary is None:
            return

        dictionary = ujson.loads(dictionary)

        for value in list(dictionary):
            if (
                datetime.strptime(dictionary[value]["date"], "%Y-%m-%d %H:%M:%S.%f")
                < datetime.now()
            ):
                if "guild" in dictionary[value]:
                    yield value, dictionary[value]["guild"]
                else:
                    yield value

                dictionary.pop(value)

        self.bot.db.put(db_key, ujson.dumps(dictionary).encode())

    @tasks.loop(seconds=10)
    async def check_end_dates(self):
        """Checks end dates on bans, downvotes and cache."""

        async for member, guild in self.date_check(b"banned_members"):
            user = self.bot.get_user(member)
            if user:
                await guild.unban(user)

        async for member in self.date_check(b"downvoted_users"):
            self.bot.db.delete(b"blacklist-" + member.encode())

        async for cache in self.date_check(b"cache"):
            pass


def setup(bot):
    bot.add_cog(background_tasks(bot))
