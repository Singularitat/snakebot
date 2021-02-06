import discord
from discord.ext import commands
import ujson
import random
import aiohttp
import time
import datetime
import string
import inspect
import os
import lxml.html
import re
import psutil


class useful(commands.Cog):
    """Actually useful commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.process = psutil.Process()

    @commands.command(name="dir")
    async def _dir(self, ctx, arg, *, object):
        """Converts arguments to a chosen discord object

        arg: str
            The argument to be converted.
        object: str
            The object to attempt to convert to.
        """
        object = object.replace(" ", "").lower()
        objects = {
            "member": commands.MemberConverter(),
            "user": commands.UserConverter(),
            "message": commands.MessageConverter(),
            "textchannel": commands.TextChannelConverter(),
            "voicechannel": commands.VoiceChannelConverter(),
            "categorychannel": commands.CategoryChannelConverter(),
            "invite": commands.InviteConverter(),
            "role": commands.RoleConverter(),
            "game": commands.GameConverter(),
            "color": commands.ColourConverter(),
            "emoji": commands.EmojiConverter(),
            "partialemoji": commands.PartialEmojiConverter(),
        }
        if object in objects:
            object = await objects[object].convert(ctx, arg)
            await ctx.send(dir(object))
        else:
            await ctx.send("```Could not find object```")

    @commands.command()
    async def usage(self, ctx):
        """Shows the bot's memory and cpu usage."""
        memory_usage = self.process.memory_full_info().uss / 1024 ** 2
        cpu_usage = self.process.cpu_percent() / psutil.cpu_count()

        embed = discord.Embed(color=discord.Color.teal())
        embed.add_field(name="Memory Usage: ", value=f"**{memory_usage:.2f} MiB**")
        embed.add_field(name="CPU Usage:", value=f"**{cpu_usage}%**")
        await ctx.send(embed=embed)

    @commands.command()
    async def source(self, ctx, *, command: str = None):
        """Gets the source code of a command from github

        command: str
            The command to find the source code of.
        """
        if command is None:
            return await ctx.send("https://github.com/Singularitat/snakebot")

        if command == "help":
            src = type(self.bot.help_command)
            filename = inspect.getsourcefile(src)
        else:
            obj = self.bot.get_command(command.replace(".", " "))
            if obj is None:
                return await ctx.send("Could not find command.")

            src = obj.callback.__code__
            filename = src.co_filename

        lines, lineno = inspect.getsourcelines(src)
        cog = os.path.relpath(filename).replace("\\", "/")

        final_url = f"<https://github.com/Singularitat/snakebot/blob/main/{cog}#L{lineno}-L{lineno + len(lines) - 1}>"
        if len(f'```py\n{"".join(lines)}```') <= 2000:
            await ctx.send(f'```py\n{("".join(lines)).replace("`", "")}```')
        await ctx.send(final_url)

    @commands.command()
    @commands.is_owner()
    async def issue(self, ctx, *, issue):
        """Appends an issue to the snakebot-todo

        issue: str
            The issue to append.
        """
        await ctx.channel.purge(limit=1)
        channel = self.bot.get_channel(776616587322327061)
        message = await channel.fetch_message(787153490996494336)
        issues = str(message.content).replace("`", "")
        issuelist = issues.split("\n")
        issue = string.capwords(issue)
        if issue[0:6] == "Delete":
            issuelist.remove(f"{issue[7:]}")
            issues = "\n".join(issuelist)
            await message.edit(content=f"""```{issues}```""")
        else:
            await message.edit(
                content=f"""```{issues}
{issue}```"""
            )

    @commands.command()
    async def google(self, ctx, *, search):
        """Searchs and finds a random image from google.

        search: str
            The term to search for.
        """
        search.replace(" ", "+")
        url = f"https://www.google.co.nz/search?q={search}&source=lnms&tbm=isch"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.67 Safari/537.36"
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url) as page:
                soup = lxml.html.fromstring(await page.text())
        images = []
        for a in soup.xpath('.//img[@class="rg_i Q4LuWd"]'):
            try:
                images.append(a.attrib["data-src"])
            except KeyError:
                pass
        await ctx.send(random.choice(images))

    @commands.command(aliases=["img"])
    async def image(self, ctx, *, search):
        """Searchs and finds a random image from bing.

        search: str
            The term to search for.
        """
        search.replace(" ", "%20")
        url = f"https://www.bing.com/images/search?q={search}&first=1&scenario=ImageBasicHover"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.67 Safari/537.36"
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url) as page:
                soup = lxml.html.fromstring(await page.text())
        images = []
        for a in soup.xpath('.//a[@class="iusc"]'):
            images.append(ujson.loads(a.attrib["m"])["turl"])
        await ctx.send(random.choice(images))

    @commands.command()
    async def ping(self, ctx):
        """Check how the bot is doing."""

        start = time.monotonic()
        pinger = await ctx.send("Pinging...")
        diff = "%.2f" % (1000 * (time.monotonic() - start))

        embed = discord.Embed()
        embed.add_field(name="Ping", value=f"`{diff} ms`")
        embed.add_field(name="Latency", value=f"`{round(self.bot.latency*1000, 2)} ms`")

        await pinger.edit(content=None, embed=embed)

    @commands.command(aliases=["urbandictionary"])
    async def urban(self, ctx, *, search):
        """Grabs the definition of something from the urbandictionary

        search: str
            The term to search for.
        """
        url = f"https://api.urbandictionary.com/v0/define?term={search}"
        async with aiohttp.ClientSession() as session:
            raw_response = await session.get(url)
            response = await raw_response.text()
            urban = ujson.loads(response)
        if urban["list"]:
            defin = random.choice(urban["list"])
            embed = discord.Embed(colour=discord.Color.red())
            embed.add_field(
                name=f"Definition of {search}",
                value=re.sub(r"\[(.*?)\]", r"\1", defin["definition"]),
                inline=False,
            )
            embed.add_field(
                name="Example",
                value=re.sub(r"\[(.*?)\]", r"\1", defin["example"]),
                inline=False,
            )
            embed.add_field(name="Upvotes", value=defin["thumbs_up"], inline=False)
            embed.set_footer(icon_url=self.bot.user.avatar_url, text="Go way hat you™")
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="No results found", color=discord.Color.blue(), inline=False
            )
            await ctx.send(embed=embed)

    @staticmethod
    def formatted_wiki_url(index: int, title: str) -> str:
        """Formating wikipedia link with index and title.

        index: int
        title: str
        """
        return f'`{index}` [{title}]({f"https://en.wikipedia.org/wiki/{title}".format(title=title.replace(" ", "_"))})'

    async def search_wikipedia(self, search_term: str):
        """Search wikipedia and return the first 10 pages found.

        search_term: str
        """
        pages = []
        async with aiohttp.ClientSession() as session:
            response = await session.get(
                f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={search_term}&format=json"
            )
            try:
                data = await response.ujson()
                search_results = data["query"]["search"]
                for search_result in search_results:
                    if "may refer to" not in search_result["snippet"]:
                        pages.append(search_result["title"])
            except Exception:
                pages = None
        return pages

    @commands.command(name="wikipedia", aliases=["wiki"])
    async def wikipedia_search_command(
        self, ctx: commands.Context, *, search: str
    ) -> None:
        """Return list of results containing your search query from wikipedia.

        search: str
            The term to search wikipedia for.
        """
        titles = await self.search_wikipedia(search)

        def check(message: discord.Message) -> bool:
            return message.author.id == ctx.author.id and message.channel == ctx.channel

        if not titles:
            await ctx.send("Could not find a wikipedia article using that search term")
            return

        async with ctx.typing():
            s_desc = "\n".join(
                self.formatted_wiki_url(index, title)
                for index, title in enumerate(titles, start=1)
            )
            embed = discord.Embed(
                colour=discord.Color.blue(),
                title=f"Wikipedia results for `{search}`",
                description=s_desc,
            )
            embed.timestamp = datetime.datetime.utcnow()
            await ctx.send(embed=embed)
        embed = discord.Embed(
            colour=discord.Color.green(), description="Enter number to choose"
        )
        titles_len = len(titles)
        try:
            message = await ctx.bot.wait_for("message", timeout=60.0, check=check)
            response_from_user = await self.bot.get_context(message)

            if response_from_user.command:
                return

            response = int(message.content)
            if response <= 0:
                await ctx.send(f"Give an integer between `1` and `{titles_len}`")
            else:
                await ctx.send(
                    "https://en.wikipedia.org/wiki/{title}".format(
                        title=titles[response - 1].replace(" ", "_")
                    )
                )

        except IndexError or ValueError:
            await ctx.send(
                f"Sorry, please give an integer between `1` and `{titles_len}`"
            )

    @commands.command(aliases=["btc"])
    async def bitcoin(self, ctx, currency="NZD"):
        """Grabs the current bitcoin price in some supported currencys.

        currency: str
            The currency to show the price in defaults to NZD.
        """
        currency = currency.upper()
        try:
            url = "https://blockchain.info/ticker"
            async with aiohttp.ClientSession() as session:
                raw_response = await session.get(url)
                response = await raw_response.text()
                bitcoin = ujson.loads(response)
                symbol = bitcoin[currency]["symbol"]
            url = f"https://blockchain.info/tobtc?currency={currency}&value=1"
            async with aiohttp.ClientSession() as session:
                raw_response = await session.get(url)
                response = await raw_response.text()
                price = ujson.loads(response)
            embed = discord.Embed(colour=discord.Color.purple())
            embed.set_author(name=f"Current Bitcoin price in {currency}")
            embed.add_field(
                name="Bitcoin Price:",
                value=f'{symbol}{bitcoin[currency]["last"]:,.2f} {currency}',
                inline=True,
            )
            embed.add_field(
                name=f"1 {currency} is worth:",
                value=f"{str(round(price, 5))} bitcoins",
                inline=True,
            )
            if currency == "NZD":
                with open("json/bitcoin.json") as file:
                    data = ujson.load(file)
                embed.add_field(
                    name=f"Change from {data[1]}",
                    value=f'{bitcoin[currency]["last"] - data[0]:,.2f}',
                    inline=True,
                )
                data = [
                    bitcoin[currency]["last"],
                    (str(ctx.message.created_at))[5:-7],
                ]
                with open("json/bitcoin.json", "w") as file:
                    data = ujson.dump(data, file, indent=2)
            embed.set_footer(icon_url=self.bot.user.avatar_url, text="Go way hat you™")
            await ctx.send(embed=embed)
        except KeyError:
            await ctx.send(
                "Only works for USD, AUD, BRL, CAD, CHF, CLP, CNY, DKK, EUR, GBP, HKD, INR, ISK, JPY, KRW, NZD, PLN, RUB, SEK, SGD, THB, TRY, TWD"
            )

    @commands.command()
    async def covid(self, ctx, *, country="nz"):
        """Shows current coronavirus cases, defaults to New Zealand.

        country: str - The country to search for
        """
        try:
            if len(country) > 2:
                url = "https://corona.lmao.ninja/v3/covid-19/countries/"
                async with aiohttp.ClientSession() as session:
                    raw_response = await session.get(url)
                    response = await raw_response.text()
                    response = ujson.loads(response)
                    if len(country) == 3:
                        country = country.upper()
                    else:
                        country = country.title()
                    y = 0
                    for x in response:
                        if x["country"] == country:
                            response = response[y]
                            break
                        y += 1
            else:
                url = "https://corona.lmao.ninja/v3/covid-19/countries/" + country
                if country.lower() == "all":
                    url = "https://corona.lmao.ninja/v3/covid-19/all"
                async with aiohttp.ClientSession() as session:
                    raw_response = await session.get(url)
                    response = await raw_response.text()
                    response = ujson.loads(response)
            embed = discord.Embed(colour=discord.Color.red())
            embed.set_author(
                name="Cornavirus " + response["country"] + ":",
                icon_url=response["countryInfo"]["flag"],
            )
            embed.add_field(
                name="Total Cases", value=f"{response['cases']:,}", inline=True
            )
            embed.add_field(
                name="Total Deaths", value=f"{response['deaths']:,}", inline=True
            )
            embed.add_field(
                name="Active Cases", value=f"{response['active']:,}", inline=True
            )
            embed.add_field(
                name="Cases Today", value=f"{response['todayCases']:,}", inline=True
            )
            embed.add_field(
                name="Deaths Today", value=f"{response['todayDeaths']:,}", inline=True
            )
            embed.add_field(
                name="Recovered Total", value=f"{response['recovered']:,}", inline=True
            )
            embed.set_footer(
                icon_url=self.bot.user.avatar_url,
                text=f'Go way hat you™   Updated {round(time.time() - (response["updated"]/1000))}s ago',
            )
            await ctx.send(embed=embed)
        except KeyError:
            await ctx.send(
                "Not a valid country e.g NZ, New Zealand, US, USA, Canada, all"
            )


def setup(bot):
    bot.add_cog(useful(bot))
