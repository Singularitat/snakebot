import lxml
import aiohttp
import datetime
import os
import asyncio
import subprocess
from discord.ext import commands, tasks


class background_tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.stocks = self.bot.db.prefixed_db(b"stocks-")
        self.update_stocks.start()
        self.update_bot.start()

    async def stockgrab(self, url):
        """Grabs some information abouts stocks from yahoo finance.

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
        stockdata = []
        for table in soup.xpath('.//table[@class="W(100%)"]'):
            table_body = table.find("tbody")
            rows = table_body.findall("tr")
            for row in rows:
                cols = row.findall("td")
                cols = [ele.text_content().strip() for ele in cols]
                stockdata.append([ele for ele in cols if ele])
        return stockdata

    async def stockupdate(self, url):
        """Fetches stocks then updates the json files.

        url: str
            The yahoo finance url to fetch stocks from.
        """
        with self.stocks.write_batch() as wb:
            for stock in await self.stockgrab(url):
                if len(stock[0]) <= 6 and stock[2] != "N/A" and float(stock[2]) != 0:
                    wb.put(stock[0].replace(".NZ", "").encode(), stock[2].encode())

    @tasks.loop(minutes=30)
    async def update_stocks(self):
        """Updates stock prices every half hour."""
        time = datetime.datetime.now()
        # Check if the stock market is open
        # 2:00 PM to 4 AM
        if time.hour >= 4 and time.hour <= 14 or (self.stocks.get(b"GME") is None):
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

        return " ".join([output.decode() for output in result]).split()

    @tasks.loop(minutes=10)
    async def update_bot(self):
        """Checks for updates every 10 minutes and then updates if needed."""
        pull = await self.run_process("git pull")

        if pull == ["Already", "up", "to", "date."]:
            return

        diff = await self.run_process("git diff --name-only HEAD@{0} HEAD@{1}")
        diff = [ext.replace("/cogs", "") for ext in diff if ext[:5] == "/cogs"]

        await self.run_process("poetry install")

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


def setup(bot):
    bot.add_cog(background_tasks(bot))
