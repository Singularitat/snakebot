from discord.ext import commands
import aiohttp
import asyncio
import random
import discord
import re
from datetime import datetime
import textwrap
import orjson
import html


class apis(commands.Cog):
    """For commands related to apis."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.loop = asyncio.get_event_loop()

    async def get_json(self, url):
        """Gets and loads json from a url.

        url: str
            The url to fetch the json from.
        """
        timeout = aiohttp.ClientTimeout(total=6)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                response = await session.get(url)

                try:
                    data = await response.json()
                except aiohttp.client_exceptions.ContentTypeError:
                    return None

            return data
        except asyncio.exceptions.TimeoutError:
            return None

    @commands.command()
    async def fakeuser(self, ctx):
        """Gets a fake user with some random data."""
        url = "https://randomuser.me/api/?results=1"

        async with ctx.typing():
            data = await self.get_json(url)
            data = data["results"][0]
            embed = discord.Embed(color=discord.Color.blurple())

            embed.set_author(
                name="{} {} {}".format(
                    data["name"]["title"], data["name"]["first"], data["name"]["last"]
                ),
                icon_url=data["picture"]["large"],
            )
            embed.add_field(name="Gender", value=data["gender"])
            embed.add_field(
                name="Location",
                value="{}, {}, {}, {}".format(
                    data["location"]["street"]["name"],
                    data["location"]["city"],
                    data["location"]["state"],
                    data["location"]["country"],
                ),
            )
            embed.add_field(name="Email", value=data["email"])
            embed.add_field(name="Username", value=data["login"]["username"])
            embed.add_field(name="Password", value=data["login"]["sha256"])
            embed.add_field(name="Date of birth", value=data["dob"]["date"])
            embed.add_field(name="Phone", value=data["phone"])

        await ctx.send(embed=embed)

    @commands.command()
    async def dadjoke(self, ctx):
        """Gets a random dad joke."""
        url = "https://icanhazdadjoke.com/"
        headers = {"Accept": "application/json"}
        async with ctx.typing(), aiohttp.ClientSession(headers=headers) as session:
            reponse = await session.get(url)
            data = await reponse.json()
        await ctx.reply(data["joke"])

    @commands.command()
    async def cocktail(self, ctx, *, name=None):
        """Searchs for a cocktail and gets a random result by default.

        name: str
        """
        if not name:
            url = "https://www.thecocktaildb.com/api/json/v1/1/random.php"
        else:
            url = f"https://www.thecocktaildb.com/api/json/v1/1/search.php?s={name}"

        embed = discord.Embed(color=discord.Color.blurple())

        async with ctx.typing():
            data = await self.get_json(url)
            if not data["drinks"]:
                embed.description = "```No cocktails found.```"
                embed.color = discord.Color.red()
                return await ctx.send(embed=embed)
            drink = random.choice(data["drinks"])

        embed.set_image(url=drink["strDrinkThumb"])
        embed.set_author(name=drink["strDrink"], icon_url=drink["strDrinkThumb"])

        ingredients = []

        for i in range(1, 16):
            if not drink[f"strIngredient{i}"]:
                break
            ingredients.append(
                f"{drink[f'strIngredient{i}']}: {drink[f'strMeasure{i}']}"
            )

        embed.description = textwrap.dedent(
            f"""
        ```Category: {drink["strCategory"]}
        \nGlass: {drink["strGlass"]}
        \nAlcohol: {drink["strAlcoholic"]}
        \nInstructions: {drink["strInstructions"]}
        \n\nIngredients:
        \n{f"{chr(10)}".join(ingredients)}
        ```"""
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def lyrics(self, ctx, artist, *, song):
        """Shows the lyrics of a song.

        e.g .lyrics "sum 41" in too deep
        .lyrics incubus drive

        artist: str
        song: str
        """
        url = f"https://api.lyrics.ovh/v1/{artist}/{song}"

        async with ctx.typing():
            lyrics = await self.get_json(url)

        embed = discord.Embed(color=discord.Color.blurple())

        if not lyrics or "error" in lyrics:
            embed.description = "```No lyrics found```"
            return await ctx.send(embed=embed)

        embed.description = f"```{lyrics['lyrics'][:2000]}```"
        await ctx.send(embed=embed)

    @commands.command()
    async def trivia(self, ctx, difficulty="easy"):
        """Does a simple trivia game.

        difficulty: str
            Choices are easy, medium or hard.
        """
        url = f"https://opentdb.com/api.php?amount=1&difficulty={difficulty}&type=multiple"

        async with ctx.typing():
            data = await self.get_json(url)

        result = data["results"][0]

        embed = discord.Embed(
            color=discord.Color.blurple(), title=html.unescape(result["question"])
        )
        options = result["incorrect_answers"] + [result["correct_answer"]]
        random.shuffle(options)

        for i, option in enumerate(options, start=0):
            embed.add_field(name=i + 1, value=option)

        message = await ctx.send(embed=embed)
        reactions = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]

        for emoji in reactions:
            await message.add_reaction(emoji)

        def check(reaction: discord.Reaction, user: discord.User) -> bool:
            return (
                user.id == ctx.author.id
                and reaction.message.channel == ctx.channel
                and reaction.emoji in reactions
            )

        reaction, user = await ctx.bot.wait_for(
            "reaction_add", timeout=60.0, check=check
        )

        if reactions.index(reaction.emoji) == options.index(result["correct_answer"]):
            return await message.add_reaction("✅")

        await message.add_reaction("❎")
        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                description=f"Correct answer was {result['correct_answer']}",
            )
        )

    @commands.command()
    async def minecraft(self, ctx, ip):
        """Gets some information about a minecraft server.

        ip: str
        """
        url = f"https://api.mcsrvstat.us/2/{ip}"

        async with ctx.typing():
            data = await self.get_json(url)

            embed = discord.Embed(color=discord.Color.blurple())

            if not data:
                embed.description = "```Pinging timed out.```"
                return await ctx.send(embed=embed)

            if data["debug"]["ping"] is False:
                embed.description = "```Pinging failed.```"
                return await ctx.send(embed=embed)

            embed.description = (
                "```Hostname: {}\n"
                "Online: {}\n\n"
                "Players:\n{}/{}\n{}\n"
                "Version(s):\n{}\n\n"
                "Mods:\n{}\n\n"
                "Motd:\n{}```"
            ).format(
                data["hostname"],
                data["online"],
                data["players"]["online"],
                data["players"]["max"],
                ", ".join(data["players"]["list"]) if "list" in data["players"] else "",
                data["version"],
                len(data["mods"]["names"]) if "mods" in data else None,
                f"{chr(10)}".join([s.strip() for s in data["motd"]["clean"]]),
            )

            await ctx.send(embed=embed)

    @commands.command()
    async def define(self, ctx, *, word):
        """Defines a word via the dictionary.com api.

        word: str
        """
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en_US/{word}"

        async with ctx.typing():
            definition = await self.get_json(url)

            embed = discord.Embed(color=discord.Color.blurple())
            msg = ""

            for meaning in definition[0]["meanings"]:
                msg += f'{meaning["partOfSpeech"]}:\n{meaning["definitions"][0]["definition"]}\n\n'

            embed.description = f"```{msg}```"

            await ctx.send(embed=embed)

    @commands.command()
    async def latex(self, ctx, *, latex):
        r"""Converts latex into an image.

        To have custom preamble wrap it with %%preamble%%

        Example:

        %%preamble%%
        \usepackage{tikz}
        \usepackage{pgfplots}
        \pgfplotsset{compat=newest}
        %%preamble%%

        latex: str
        """
        url = "https://quicklatex.com/latex3.f"

        preamble = (
            r"\usepackage{amsmath}\n"
            r"\usepackage{amsfonts}\n"
            r"\usepackage{amssymb}\n"
            r"\newcommand{\N}{\mathbb N}\n"
            r"\newcommand{\Z}{\mathbb Z}\n"
            r"\newcommand{\Q}{\mathbb Q}"
            r"\newcommand{\R}{\mathbb R}\n"
            r"\newcommand{\C}{\mathbb C}\n"
            r"\newcommand{\V}[1]{\begin{bmatrix}#1\end{bmatrix}}\n"
            r"\newcommand{\set}[1]{\left\{#1\right\}}\n"
        )

        async with ctx.typing():
            latex = re.sub(r"```\w+\n|```", "", latex)

            if "%%preamble%%" in latex:
                _, pre, latex = re.split("%%preamble%%", latex)
                preamble += pre

            data = (
                f"formula={latex}&fsize=50px&fcolor=FFFFFF&mode=0&out=1"
                f"&remhost=quicklatex.com&preamble={preamble}"
            )

            async with aiohttp.ClientSession() as session, session.post(
                url, data=data
            ) as response:
                r = await response.text()

            if "Internal Server Error" in r:
                return await ctx.send(
                    embed=discord.Embed(
                        color=discord.Color.blurple(),
                        description="Internal Server Error.",
                    )
                )

            image = r.split()[1]

            if image == "https://quicklatex.com/cache3/error.png":
                return await ctx.send(
                    embed=discord.Embed(
                        color=discord.Color.blurple(),
                        description=f"```latex\n{r[49:]}```",
                    )
                )

            await ctx.send(image)

    @commands.command()
    async def racoon(self, ctx):
        """Gets a random racoon image."""
        url = "https://some-random-api.ml/img/racoon"

        async with ctx.typing():
            image = await self.get_json(url)

        await ctx.send(image["link"])

    @commands.command()
    async def kangaroo(self, ctx):
        """Gets a random kangaroo image."""
        url = "https://some-random-api.ml/img/kangaroo"

        async with ctx.typing():
            image = await self.get_json(url)

        await ctx.send(image["link"])

    @commands.command()
    async def koala(self, ctx):
        """Gets a random koala image."""
        url = "https://some-random-api.ml/img/koala"

        async with ctx.typing():
            image = await self.get_json(url)

        await ctx.send(image["link"])

    @commands.command()
    async def bird(self, ctx):
        """Gets a random bird image."""
        url = "https://some-random-api.ml/img/birb"

        async with ctx.typing():
            image = await self.get_json(url)

        await ctx.send(image["link"])

    @commands.command()
    async def redpanda(self, ctx):
        """Gets a random red panda image."""
        url = "https://some-random-api.ml/img/red_panda"

        async with ctx.typing():
            image = await self.get_json(url)

        await ctx.send(image["link"])

    @commands.command()
    async def panda(self, ctx):
        """Gets a random panda image."""
        url = "https://some-random-api.ml/img/panda"

        async with ctx.typing():
            image = await self.get_json(url)

        await ctx.send(image["link"])

    @commands.command()
    async def avatar(self, ctx, *, seed=""):
        """Creates a avatar based off a seed.

        seed: str
            The seed it can be any alphanumeric characters.
        """
        await ctx.send(f"https://avatars.dicebear.com/api/avataaars/{seed}.png")

    @commands.command()
    async def fox(self, ctx):
        """Gets a random fox image."""
        url = "https://randomfox.ca/floof"

        async with ctx.typing():
            image = await self.get_json(url)

        await ctx.send(image["image"])

    @commands.command()
    async def fox2(self, ctx):
        """Gets a random fox image."""
        url = "https://wohlsoft.ru/images/foxybot/randomfox.php"

        async with ctx.typing():
            image = await self.get_json(url)

        await ctx.send(image["file"])

    @commands.command()
    async def cat(self, ctx):
        """Gets a random cat image."""
        url = "https://aws.random.cat/meow"

        async with ctx.typing():
            image = await self.get_json(url)

        await ctx.send(image["file"])

    @commands.command()
    async def cat2(self, ctx):
        """Gets a random cat image."""
        url = "https://api.thecatapi.com/v1/images/search"

        async with ctx.typing():
            image = await self.get_json(url)

        await ctx.send(image[0]["url"])

    @commands.command()
    async def catstatus(self, ctx, status):
        """Gets a cat image for a status e.g Error 404 not found."""
        await ctx.send(f"https://http.cat/{status}")

    @commands.command()
    async def dog(self, ctx, breed=None):
        """Gets a random dog image."""
        if breed:
            url = f"https://dog.ceo/api/breed/{breed}/images/random"
        else:
            url = "https://dog.ceo/api/breeds/image/random"

        async with ctx.typing():
            image = await self.get_json(url)

        await ctx.send(image["message"])

    @commands.command()
    async def dog2(self, ctx):
        """Gets a random dog image."""
        url = "https://random.dog/woof.json"

        async with ctx.typing():
            image = await self.get_json(url)

        await ctx.send(image["url"])

    @commands.command()
    async def shibe(self, ctx):
        """Gets a random dog image."""
        url = "http://shibe.online/api/shibes?count=1&urls=true&httpsUrls=true"

        async with ctx.typing():
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
            The url to the qrcode has to be image format e.g jpg/jpeg/png.
        """
        url = f"http://api.qrserver.com/v1/read-qr-code/?fileurl={qrcode}"

        async with ctx.typing():
            data = await self.get_json(url)

        if data is None:
            return await ctx.send("```Invalid url```")

        if data[0]["symbol"][0]["data"] is None:
            return await ctx.send("```Could not decode```")

        await ctx.send(data[0]["symbol"][0]["data"])

    @commands.command()
    async def xkcd(self, ctx, num: int = None):
        """Gets a random xkcd comic.

        num: int
            The xkcd to get has to be between 0 and 2438"""
        if not num or num > 2438 or num < 0:
            num = random.randint(0, 2438)

        url = f"https://xkcd.com/{num}/info.0.json"

        async with ctx.typing():
            data = await self.get_json(url)

        if data is None:
            return await ctx.send("```xkcd timed out.```")

        await ctx.send(data["img"])

    @commands.command(aliases=["urbandictionary"])
    async def urban(self, ctx, *, search):
        """Grabs the definition of something from the urban dictionary.

        search: str
            The term to search for.
        """
        url = f"https://api.urbandictionary.com/v0/define?term={search}"

        async with ctx.typing():
            urban = await self.get_json(url)

        if not urban["list"]:
            return await ctx.send(
                embed=discord.Embed(title="No results found", color=discord.Color.red())
            )

        defin = random.choice(urban["list"])

        embed = discord.Embed(colour=discord.Color.blurple())

        embed.description = (
            "```diff\nDefinition of {}:\n"
            "{}\n\n"
            "Example:\n{}\n\n"
            "Votes:\n{}\n\n```"
        ).format(
            search,
            re.sub(r"\[(.*?)\]", r"\1", defin["definition"]),
            re.sub(r"\[(.*?)\]", r"\1", defin["example"]),
            defin["thumbs_up"],
        )

        await ctx.send(embed=embed)

    @staticmethod
    def formatted_wiki_url(index: int, title: str) -> str:
        """Formating wikipedia link with index and title.

        index: int
        title: str
        """
        return f'`{index}` [{title}](https://en.wikipedia.org/wiki/{title.replace(" ", "_")}))'

    async def search_wikipedia(self, search_term: str):
        """Search wikipedia and return the first 10 pages found.

        search_term: str
        """
        pages = []
        try:
            data = await self.get_json(
                f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={search_term}&format=json"
            )
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
                colour=discord.Color.blurple(),
                title=f"Wikipedia results for `{search}`",
                description=s_desc,
            )

            embed.timestamp = datetime.utcnow()
            embed.set_footer(text="Enter a number to choose")

            await ctx.send(embed=embed)

        titles_len = len(titles)
        try:
            message = await ctx.bot.wait_for("message", timeout=60.0, check=check)
            response_from_user = await self.bot.get_context(message)

            if response_from_user.command:
                return

            try:
                response = int(message.content)
            except ValueError:
                return await ctx.send(
                    f"Please give an integer between `1` and `{titles_len}`"
                )

            if response <= 0:
                return await ctx.send(
                    f"Please give an integer between `1` and `{titles_len}`"
                )

            await ctx.send(
                "https://en.wikipedia.org/wiki/{title}".format(
                    title=titles[response - 1].replace(" ", "_")
                )
            )

        except IndexError:
            await ctx.send(f"Please give an integer between `1` and `{titles_len}`")

    @commands.command()
    async def covid(self, ctx, *, country="nz"):
        """Shows current coronavirus cases, defaults to New Zealand.

        country: str - The country to search for
        """
        try:
            url = "https://corona.lmao.ninja/v3/covid-19/countries/" + country
            if country.lower() == "all":
                url = "https://corona.lmao.ninja/v3/covid-19/all"

            async with ctx.typing():
                data = await self.get_json(url)

            embed = discord.Embed(colour=discord.Color.red())
            embed.set_author(
                name=f"Cornavirus {data['country']}:",
                icon_url=data["countryInfo"]["flag"],
            )

            embed.description = textwrap.dedent(
                f"""
                    ```
                    Total Cases:   Total Deaths:
                    {data['cases']:<15,}{data['deaths']:,}

                    Active Cases:  Cases Today:
                    {data['active']:<15,}{data['todayCases']:,}

                    Deaths Today:  Recovered Total:
                    {data['todayDeaths']:<15,}{data['recovered']:,}
                    ```
                """
            )

            await ctx.send(embed=embed)

        except KeyError:
            await ctx.send(
                "Not a valid country e.g NZ, New Zealand, US, USA, Canada, all"
            )

    @commands.command(name="github", aliases=["gh"])
    async def get_github_info(self, ctx: commands.Context, username: str) -> None:
        """Fetches a members's GitHub information."""
        async with ctx.typing():
            user_data = await self.get_json(f"https://api.github.com/users/{username}")

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
                timestamp=datetime.strptime(
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

    def delete_cache(self, search, cache):
        """Deletes a search from the cache.

        search: str
        """
        cache.pop(search)
        self.bot.db.put(b"cache", orjson.dumps(cache))

    @commands.command()
    async def tenor(self, ctx, *, search):
        """Gets a random gif from tenor based off a search.

        search: str
            The gif search term.
        """
        cache_search = f"tenor-{search}"
        cache = orjson.loads(self.bot.db.get(b"cache"))

        if cache_search in cache:
            url = random.choice(cache[cache_search])
            cache[cache_search].remove(url)

            if len(cache[cache_search]) == 0:
                cache.pop(cache_search)

            self.bot.db.put(b"cache", orjson.dumps(cache))

            return await ctx.send(url)

        url = f"https://api.tenor.com/v1/search?q={search}&limit=50"

        async with ctx.typing():
            tenor = await self.get_json(url)

        tenor = [image["media"][0]["gif"]["url"] for image in tenor["results"]]
        image = random.choice(tenor)
        tenor.remove(image)
        cache[cache_search] = tenor

        self.bot.db.put(b"cache", orjson.dumps(cache))
        self.loop.call_later(300, self.delete_cache, cache_search, cache)
        await ctx.send(image)


def setup(bot: commands.Bot) -> None:
    """Starts logger cog."""
    bot.add_cog(apis(bot))
