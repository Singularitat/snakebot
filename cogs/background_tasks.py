import lxml
import aiohttp
import datetime
import os
import asyncio
import subprocess
import ujson
from discord.ext import commands, tasks


class background_tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.stocks = self.bot.db.prefixed_db(b"stocks-")
        self.update_stocks.start()
        self.update_bot.start()
        self.backup_bot.start()
        self.update_languages.start()

    def cog_unload(self):
        self.update_stocks.stop()
        self.update_bot.stop()
        self.backup_bot.stop()
        self.update_languages.stop()

    async def stockgrab(self, url):
        """Yields some information abouts stocks from yahoo finance.

        url: str
            The yahoo finance url to fetch stocks from.
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.67 Safari/537.36"
        }
        async with aiohttp.ClientSession(headers=headers) as session, session.get(
            url
        ) as page:
            soup = lxml.html.fromstring(await page.text())

        for table in soup.xpath('.//table[@class="W(100%)"]'):
            table_body = table.find("tbody")
            rows = table_body.findall("tr")
            for row in rows:
                cols = [col.text_content() for col in row.findall("td")]

                price = cols[2]
                name = cols[0]

                if price != "N/A" and len(name) <= 6 and float(price) != 0:
                    stock_data = {}
                    stock_data["name"] = cols[1]
                    stock_data["price"] = price
                    stock_data["change"] = cols[3]
                    stock_data["%change"] = cols[4]
                    stock_data["volume"] = cols[5]
                    stock_data["3Mvolume"] = cols[6]
                    stock_data["cap"] = cols[7]

                    yield name, stock_data

    async def stockupdate(self, url):
        """Fetches stocks then updates the database.

        url: str
            The yahoo finance url to fetch stocks from.
        """
        with self.stocks.write_batch() as wb:
            async for stock in self.stockgrab(url):
                wb.put(
                    stock[0].replace(".NZ", "").encode(), ujson.dumps(stock[1]).encode()
                )

    @tasks.loop(minutes=30)
    async def update_stocks(self):
        """Updates stock prices every half hour."""
        time = datetime.datetime.utcnow().hour
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
        """Checks for updates every 3 minutes and then updates if needed."""
        pull = await self.run_process("git pull")

        if pull == ["Already", "up", "to", "date."]:
            return

        diff = await self.run_process("git diff --name-only HEAD@{0} HEAD@{1}")

        if "poetry.lock" in diff:
            await self.run_process("poetry install")

        diff = [ext.replace("/cogs", "") for ext in diff if ext[:5] == "/cogs"]

        for extension in [
            f.replace(".py", "")
            for f in os.listdir("cogs")
            if os.path.isfile(os.path.join("cogs", f)) and f in diff
        ]:
            try:
                self.bot.reload_extension(f"cogs.{extension}")
            except Exception as e:
                if (
                    e
                    == f"ExtensionNotLoaded: Extension 'cogs.{extension}' has not been loaded."
                ):
                    self.bot.load_extension(f"cogs.{extension}")

    @tasks.loop(hours=2)
    async def backup_bot(self):
        """Makes a backup of the db every two hours."""
        os.makedirs("backup/", exist_ok=True)
        time = datetime.datetime.now()
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

    @tasks.loop(minutes=1)
    async def unban_members(self):
        members = ujson.loads(self.bot.db.get(b"banned_members"))
        if members == {}:
            return
        for member in members:
            if members[member]["date"] > datetime.datetime.now():
                guild = self.bot.get_guild(members[member]["guild"])
                user = self.bot.get_user(member)
                await guild.unban(user)


def setup(bot):
    bot.add_cog(background_tasks(bot))
