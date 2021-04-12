import lxml
import aiohttp
from datetime import datetime
import os
import asyncio
import subprocess
import ujson
from discord.ext import commands, tasks


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
        if ctx.invoked_subcommand is None:
            await ctx.send("```No subcommand passed```")

    @task.command()
    async def restart(self, ctx, task):
        getattr(self, task).restart()

    @task.command()
    async def start(self, ctx, task):
        getattr(self, task).start()

    @task.command()
    async def stop(self, ctx, task):
        getattr(self, task).stop()

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
        time = datetime.utcnow().hour
        # Check if the stock market is open
        # 2:00 PM to 4 AM
        if time <= 14 and time >= 4 or self.stocks.get(b"GME") is None:
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

        if pull == ["Already", "up", "to", "date."]:
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

    async def members_check(self, members):
        """Checks if any end dates have been past then yields the member."""
        members = ujson.loads(members)

        for member in members:
            if (
                datetime.strptime(members[member]["date"], "%Y-%m-%d %H:%M:%S.%f")
                < datetime.now()
            ):
                yield member

    @tasks.loop(minutes=1)
    async def check_end_dates(self):
        """Checks end dates on bans and downvotes."""
        banned = self.bot.db.get(b"banned_members")
        downvoted = self.bot.db.get(b"downvoted_members")

        if banned is not None:
            async for member in self.members_check(banned):
                guild = self.bot.get_guild(banned[member]["guild"])
                user = self.bot.get_user(member)
                if user:
                    await guild.unban(user)

        if downvoted is not None:
            async for member in self.members_check(downvoted):
                self.bot.db.delete(b"blacklist-" + member.encode())


def setup(bot):
    bot.add_cog(background_tasks(bot))
