from discord.ext import commands
import aiohttp
import random
import discord
import re
import datetime
import config
import ujson


class apis(commands.Cog):
    """For commands related to apis."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def get_json(self, url):
        """Gets and loads json from a url.

        url: str
            The url to fetch the json from.
        """
        async with aiohttp.ClientSession() as session:
            response = await session.get(url)

        try:
            data = await response.json()
        except aiohttp.client_exceptions.ContentTypeError:
            return None

        return data

    @commands.command()
    async def avatar(self, ctx, *, seed):
        """Creates a avatar based off a seed.

        seed: str
            The seed it can be any alphanumeric characters.
        """
        await ctx.send(f"https://avatars.dicebear.com/api/avataaars/{seed}.svg")

    @commands.command()
    async def fox(self, ctx):
        """Gets a random fox image."""
        url = "https://randomfox.ca/floof"

        image = await self.get_json(url)

        await ctx.send(image["image"])

    @commands.command()
    async def cat(self, ctx):
        """Gets a random cat image."""
        url = "https://aws.random.cat/meow"

        image = await self.get_json(url)

        await ctx.send(image["file"])

    @commands.command()
    async def cat2(self, ctx):
        """Gets a random cat image."""
        url = "https://api.thecatapi.com/v1/images/search"

        image = await self.get_json(url)

        await ctx.send(image[0]["url"])

    @commands.command()
    async def catstatus(self, ctx, status):
        """Gets a cat image for a status e.g Error 404 not found."""
        await ctx.send(f"https://http.cat/{status}")

    @commands.command()
    async def dog2(self, ctx):
        """Gets a random dog image."""
        url = "https://random.dog/woof.json"

        image = await self.get_json(url)

        await ctx.send(image["url"])

    @commands.command()
    async def dog(self, ctx, breed=None):
        """Gets a random dog image."""
        if breed:
            url = f"https://dog.ceo/api/breed/{breed}/images/random"
        else:
            url = "https://dog.ceo/api/breeds/image/random"

        image = await self.get_json(url)

        await ctx.send(image["message"])

    @commands.command()
    async def shibe(self, ctx):
        """Gets a random dog image."""
        url = "http://shibe.online/api/shibes?count=1&urls=true&httpsUrls=true"

        image = await self.get_json(url)

        await ctx.send(image[0])

    @commands.command()
    async def qr(self, ctx, *, text):
        """Encodes a qr code with text.

        text: str
            The text you want to encode.
        """
        await ctx.send(
            f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={text}"
        )

    @commands.command()
    async def decode(self, ctx, qrcode):
        """Decodes a qr code from a url.

        qrcode: str
            The url to the qrcode.
        """
        url = f"http://api.qrserver.com/v1/read-qr-code/?fileurl={qrcode}"

        data = await self.get_json(url)

        if data is None:
            return await ctx.send("```Invalid url```")

        if data[0]["symbol"][0]["data"] is None:
            return await ctx.send("```Could not decode```")

        await ctx.send(data[0]["symbol"][0]["data"])

    @commands.command()
    async def xkcd(self, ctx):
        """Gets a random xkcd comic."""
        num = random.randint(0, 2438)

        url = f"https://xkcd.com/{num}/info.0.json"

        data = await self.get_json(url)

        await ctx.send(data["img"])

    @commands.command(aliases=["urbandictionary"])
    async def urban(self, ctx, *, search):
        """Grabs the definition of something from the urban dictionary.

        search: str
            The term to search for.
        """
        url = f"https://api.urbandictionary.com/v0/define?term={search}"

        urban = await self.get_json(url)

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
                data = await response.json()
                search_results = data["query"]["search"]
                for search_result in search_results:
                    if "may refer to" not in search_result["snippet"]:
                        pages.append(search_result["title"])
            except KeyError:
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

        except IndexError:
            await ctx.send(
                f"Sorry, please give an integer between `1` and `{titles_len}`"
            )

    @commands.command(aliases=["coin", "bitcoin", "btc"])
    async def crypto(self, ctx, crypto: str = "BTC", currency="NZD"):
        """Gets some information about crypto currencies.

        crypto: str
            The name or symbol to search for.
        currency: str
            The currency to return the price in.
        """
        url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
        parameters = {"start": "1", "limit": "150", "convert": currency}
        headers = {
            "Accepts": "application/json",
            "X-CMC_PRO_API_KEY": config.coinmarketcap,
        }
        async with aiohttp.ClientSession() as session:
            response = await session.get(url, params=parameters, headers=headers)
            cry = await response.json()

        cry = cry["data"]
        for index, coin in enumerate(cry):
            if (
                coin["name"].lower() == crypto.lower()
                or coin["symbol"] == crypto.upper()
            ):
                crypto = cry[index]
                break
        embed = discord.Embed(colour=discord.Colour.blurple())
        embed.set_author(
            name=f"{crypto['name']} [{crypto['symbol']}]",
        )
        embed.add_field(
            name="Price",
            value=f"${crypto['quote']['NZD']['price']:,.2f}",
            inline=False,
        )
        embed.add_field(
            name="Circulating/Max Supply",
            value=f"{crypto['circulating_supply']:,}/{crypto['max_supply']:,}",
            inline=False,
        )
        embed.add_field(
            name="Market Cap",
            value=f"${crypto['quote']['NZD']['market_cap']:,.2f}",
            inline=False,
        )
        embed.add_field(
            name="24h Change",
            value=f"{crypto['quote']['NZD']['percent_change_24h']}%",
            inline=False,
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def covid(self, ctx, *, country="nz"):
        """Shows current coronavirus cases, defaults to New Zealand.

        country: str - The country to search for
        """
        try:
            url = "https://corona.lmao.ninja/v3/covid-19/countries/" + country
            if country.lower() == "all":
                url = "https://corona.lmao.ninja/v3/covid-19/all"

            data = await self.get_json(url)

            embed = discord.Embed(colour=discord.Color.red())
            embed.set_author(
                name=f"Cornavirus {data['country']}:",
                icon_url=data["countryInfo"]["flag"],
            )
            embed.add_field(name="Total Cases", value=f"{data['cases']:,}", inline=True)
            embed.add_field(
                name="Total Deaths", value=f"{data['deaths']:,}", inline=True
            )
            embed.add_field(
                name="Active Cases", value=f"{data['active']:,}", inline=True
            )
            embed.add_field(
                name="Cases Today", value=f"{data['todayCases']:,}", inline=True
            )
            embed.add_field(
                name="Deaths Today", value=f"{data['todayDeaths']:,}", inline=True
            )
            embed.add_field(
                name="Recovered Total", value=f"{data['recovered']:,}", inline=True
            )
            await ctx.send(embed=embed)
        except KeyError:
            await ctx.send(
                "Not a valid country e.g NZ, New Zealand, US, USA, Canada, all"
            )

    @commands.command(name="github", aliases=["gh"])
    @commands.cooldown(1, 60, commands.BucketType.member)
    async def get_github_info(self, ctx: commands.Context, username: str) -> None:
        """Fetches a members's GitHub information."""
        async with ctx.typing():

            url = f"https://api.github.com/users/{username}"

            user_data = await self.get_json(url)

            if user_data.get("message") is not None:
                await ctx.send(
                    embed=discord.Embed(
                        title=f"The profile for `{username}` was not found.",
                        colour=discord.Colour.red(),
                    )
                )
                return

            org_data = await self.get_json(user_data["organizations_url"])

            orgs = [
                f"[{org['login']}](https://github.com/{org['login']})"
                for org in org_data
            ]
            orgs_to_add = " | ".join(orgs)

            gists = user_data["public_gists"]

            if user_data["blog"].startswith("http"):
                blog = user_data["blog"]
            elif user_data["blog"]:
                blog = f"https://{user_data['blog']}"
            else:
                blog = "No website link available"

            embed = discord.Embed(
                title=f"`{user_data['login']}`'s GitHub profile info",
                description=f"```{user_data['bio']}```\n"
                if user_data["bio"] is not None
                else "",
                colour=0x7289DA,
                url=user_data["html_url"],
                timestamp=datetime.datetime.strptime(
                    user_data["created_at"], "%Y-%m-%dT%H:%M:%SZ"
                ),
            )
            embed.set_thumbnail(url=user_data["avatar_url"])
            embed.set_footer(text="Account created at")

            if user_data["type"] == "User":

                embed.add_field(
                    name="Followers",
                    value=f"[{user_data['followers']}]({user_data['html_url']}?tab=followers)",
                )
                embed.add_field(name="\u200b", value="\u200b")
                embed.add_field(
                    name="Following",
                    value=f"[{user_data['following']}]({user_data['html_url']}?tab=following)",
                )

            embed.add_field(
                name="Public repos",
                value=f"[{user_data['public_repos']}]({user_data['html_url']}?tab=repositories)",
            )
            embed.add_field(name="\u200b", value="\u200b")

            if user_data["type"] == "User":
                embed.add_field(
                    name="Gists", value=f"[{gists}](https://gist.github.com/{username})"
                )

                embed.add_field(
                    name=f"Organization{'s' if len(orgs)!=1 else ''}",
                    value=orgs_to_add if orgs else "No organizations",
                )
                embed.add_field(name="\u200b", value="\u200b")
            embed.add_field(name="Website", value=blog)

        await ctx.send(embed=embed)

    @commands.command()
    async def tenor(self, ctx, *, search):
        """Gets a random gif from tenor based off a search.

        search: str
            The gif search term.
        """
        url = f"https://g.tenor.com/v1/search?q={search}&key={config.tenor}&limit=50"
        async with aiohttp.ClientSession() as session:
            raw_response = await session.get(url)
            response = await raw_response.text()
        tenor = ujson.loads(response)
        await ctx.send(random.choice(tenor["results"])["media"][0]["gif"]["url"])


def setup(bot: commands.Bot) -> None:
    """Starts logger cog."""
    bot.add_cog(apis(bot))
