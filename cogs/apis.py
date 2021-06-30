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
import cogs.utils.database as DB


class apis(commands.Cog):
    """For commands related to apis."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.loop = asyncio.get_event_loop()

    @staticmethod
    async def get_json(url):
        """Gets and loads json from a url.

        url: str
            The url to fetch the json from.
        """
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=6)
            ) as session, session.get(url) as response:
                return await response.json()
        except (
            asyncio.exceptions.TimeoutError,
            aiohttp.client_exceptions.ContentTypeError,
        ):
            return None

    @commands.command()
    async def kanye(self, ctx):
        """Gets a random Kanye West quote."""
        url = "https://api.kanye.rest"

        async with ctx.typing():
            quote = await self.get_json(url)
            embed = discord.Embed(
                color=discord.Color.blurple(), description=quote["quote"]
            )
            embed.set_footer(text="― Kayne West")
            await ctx.send(embed=embed)

    @commands.command()
    async def quote(self, ctx):
        """Gets a random quote."""
        url = "https://api.fisenko.net/quotes?l=en"

        async with ctx.typing():
            quote = await self.get_json(url)
            embed = discord.Embed(
                color=discord.Color.blurple(), description=quote["text"]
            )
            embed.set_footer(text=f"― {quote['author']}")
            await ctx.send(embed=embed)

    @commands.command()
    async def suntzu(self, ctx):
        """Gets fake Sun Tzu art of war quotes."""
        url = "http://api.fakeartofwar.gaborszathmari.me/v1/getquote"

        async with ctx.typing():
            quote = await self.get_json(url)
            embed = discord.Embed(
                color=discord.Color.blurple(), description=quote["quote"]
            )
            embed.set_footer(text="― Sun Tzu, Art Of War")
            await ctx.send(embed=embed)

    @commands.command()
    async def rhyme(self, ctx, word):
        """Gets words that rhyme with [word].

        words: str
        """
        url = f"https://api.datamuse.com/words?rel_rhy={word}&max=9"

        async with ctx.typing():
            rhymes = await self.get_json(url)

            embed = discord.Embed(color=discord.Color.blurple())

            if not rhymes:
                embed.description = "```No results found```"
                return await ctx.send(embed=embed)

            embed.set_footer(text="The numbers below are the scores")

            for rhyme in rhymes:
                embed.add_field(name=rhyme["word"], value=rhyme["score"])

            await ctx.send(embed=embed)

    @commands.command()
    async def spelling(self, ctx, word):
        """Gets possible spellings of [word].

        words: str
            The words to get possible spellings of.
        """
        url = f"https://api.datamuse.com/words?sp={word}&max=9"

        async with ctx.typing():
            spellings = await self.get_json(url)

            embed = discord.Embed(
                color=discord.Color.blurple(), title="Possible spellings"
            )

            if not spellings:
                embed.description = "```No results found```"
                return await ctx.send(embed=embed)

            embed.set_footer(text="The numbers below are the scores")

            for spelling in spellings:
                embed.add_field(name=spelling["word"], value=spelling["score"])

            await ctx.send(embed=embed)

    @commands.command()
    async def meaning(self, ctx, *, words):
        """Gets words with similar meaning to [words].
        Example .meaning ringing in the ears

        words: str
            The words to get possible meanings of.
        """
        url = f"https://api.datamuse.com/words?ml={words}&max=9"

        async with ctx.typing():
            meanings = await self.get_json(url)

            embed = discord.Embed(
                color=discord.Color.blurple(), title="Possible meanings"
            )

            if not meanings:
                embed.description = "```No results found```"
                return await ctx.send(embed=embed)

            embed.set_footer(text="The numbers below are the scores")

            for meaning in meanings:
                embed.add_field(name=meaning["word"], value=meaning["score"])

            await ctx.send(embed=embed)

    @commands.group()
    async def apis(self, ctx):
        """Command group for the public apis api."""
        if not ctx.invoked_subcommand:
            embed = discord.Embed(
                color=discord.Color.blurple(),
                description=f"```Usage: {ctx.prefix}apis [categories/random/search]```",
            )
            await ctx.send(embed=embed)

    @apis.command()
    async def categories(self, ctx):
        """Gets all the categories of the public apis api."""
        url = "https://api.publicapis.org/categories"

        async with ctx.typing():
            categories = await self.get_json(url)

            await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    title="All categories of the public apis api",
                    description="```{}```".format("\n".join(categories)),
                )
            )

    @apis.command()
    async def random(self, ctx, category=None):
        """Gets a random api.

        category: str
        """
        url = f"https://api.publicapis.org/random?category={category}"

        async with ctx.typing():
            data = (await self.get_json(url))["entries"][0]

            embed = discord.Embed(
                color=discord.Color.blurple(),
                title=data["API"],
                description=f"{data['Description']}\n[Link]({data['Link']})",
            )
            embed.add_field(
                name="Auth", value="None" if not data["Auth"] else data["Auth"]
            )
            embed.add_field(name="HTTPS", value=data["HTTPS"])
            embed.add_field(name="Cors", value=data["Cors"])
            embed.add_field(name="Category", value=data["Category"])

            await ctx.send(embed=embed)

    @apis.command()
    async def search(self, ctx, *, search):
        """Searchs for an match via substring matching.

        search: str
        """
        url = f"https://api.publicapis.org/entries?title={search}"

        async with ctx.typing():
            entries = (await self.get_json(url))["entries"]

            embed = discord.Embed(
                color=discord.Color.blurple(),
            )
            for index, entry in enumerate(entries):
                if index == 12:
                    break
                embed.add_field(
                    name=entry["API"],
                    value=f"{entry['Description']}\n[Link]({entry['Link']})",
                )

            await ctx.send(embed=embed)

    @commands.command()
    async def nationalize(self, ctx, first_name):
        """Estimate the nationality of a first name.

        first_name: str
        """
        url = f"https://api.nationalize.io/?name={first_name}"

        async with ctx.typing():
            data = await self.get_json(url)

            embed = discord.Embed(color=discord.Color.blurple())

            if not data["country"]:
                embed.description = "```No results found```"
                return await ctx.send(embed=embed)

            embed.title = f"Estimates of the nationality of {data['name']}"

            for country in data["country"]:
                embed.add_field(
                    name=country["country_id"],
                    value=f"{country['probability'] * 100:.2f}%",
                )
            await ctx.send(embed=embed)

    @commands.group()
    async def game(self, ctx):
        """Gets a random game that is free"""
        if not ctx.invoked_subcommand:
            url = "https://www.freetogame.com/api/games?platform=pc"

            async with ctx.typing():
                games = await self.get_json(url)
                game = random.choice(games)

                embed = discord.Embed(
                    color=discord.Color.blurple(),
                    title=game["title"],
                    description=f"{game['short_description']}\n[Link]({game['game_url']})",
                )
                embed.add_field(name="Genre", value=game["genre"])
                embed.add_field(name="Publisher", value=game["publisher"])
                embed.add_field(name="Developer", value=game["developer"])
                embed.set_image(url=game["thumbnail"])

                await ctx.send(embed=embed)

    @game.command()
    async def category(self, ctx, category):
        """Gets a random game that is free"""
        if category.lower() == "list":
            embed = discord.Embed(color=discord.Color.blurple())
            embed.description = textwrap.dedent(
                """
                ```mmorpg, shooter, strategy, moba, racing, sports
                social, sandbox, open-world, survival, pvp, pve, pixel
                voxel, zombie, turn-based, first-person, third-Person
                top-down, tank, space, sailing, side-scroller, superhero
                permadeath, card, battle-royale, mmo, mmofps, mmotps, 3d
                2d, anime, fantasy, sci-fi, fighting, action-rpg, action
                military, martial-arts, flight, low-spec, tower-defense
                horror, mmorts```
                """
            )
            return await ctx.send(embed=embed)

        url = f"https://www.freetogame.com/api/games?platform=pc&category={category}"

        async with ctx.typing():
            games = await self.get_json(url)
            game = random.choice(games)

            embed = discord.Embed(
                color=discord.Color.blurple(),
                title=game["title"],
                description=f"{game['short_description']}\n[Link]({game['game_url']})",
            )
            embed.add_field(name="Genre", value=game["genre"])
            embed.add_field(name="Publisher", value=game["publisher"])
            embed.add_field(name="Developer", value=game["developer"])
            embed.set_image(url=game["thumbnail"])

            await ctx.send(embed=embed)

    @commands.command()
    async def apod(self, ctx):
        """Gets the NASA Astronomy Picture of the Day."""
        url = "https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY"

        async with ctx.typing():
            apod = await self.get_json(url)

            embed = discord.Embed(
                color=discord.Color.blurple(),
                title=f"{apod['title']}",
                description="[Link](https://apod.nasa.gov/apod/astropix.html)",
            )
            embed.set_image(url=apod["hdurl"])
            await ctx.send(embed=embed)

    @commands.command(name="githubtrending", aliases=["githubt", "tgithub"])
    async def github_trending(self, ctx):
        """Gets trending github repositories."""
        url = "https://api.trending-github.com/github/repositories"

        async with ctx.typing():
            repositories = await self.get_json(url)
            embed = discord.Embed(
                color=discord.Color.blurple(), title="5 Trending Github Repositories"
            )

            for index, repo in enumerate(repositories, start=1):
                if index == 6:
                    break
                embed.add_field(
                    name=repo["name"].title(),
                    value=textwrap.dedent(
                        f"""
                    `Description:` {repo['description']}
                    `Language:` {repo['language']}
                    `Url:` {repo['url']}
                    `Stars:` {repo['stars']:,}
                    `Forks:` {repo['forks']:,}
                    """
                    ),
                    inline=False,
                )
            await ctx.send(embed=embed)

    @commands.command()
    async def gender(self, ctx, first_name):
        """Estimates a gender from a first name.

        first_name: str
        """
        url = f"https://api.genderize.io/?name={first_name}"

        async with ctx.typing():
            data = await self.get_json(url)
            embed = discord.Embed(color=discord.Color.blurple())
            embed.description = textwrap.dedent(
                f"""
                ```First Name: {data['name']}
                Gender: {data['gender']}
                Probability: {data['probability'] * 100}%
                Count: {data['count']}```
                """
            )
            await ctx.send(embed=embed)

    @commands.command()
    async def trends(self, ctx, *, country="new zealand"):
        """Gets the current google search trends in a country.

        country: str
        """
        url = "https://trends.google.com/trends/hottrends/visualize/internal/data"
        country = country.lower()

        async with ctx.typing():
            data = await self.get_json(url)
            embed = discord.Embed(color=discord.Color.blurple())

            if country not in data:
                embed.description = f"```Country {country.title()} not found.```"
                return await ctx.send(embed=embed)

            embed.title = f"{country.title()} Search Trends"
            embed.description = "```{}```".format("\n".join(data[country]))
            await ctx.send(embed=embed)

    @commands.command(name="fakeuser")
    async def fake_user(self, ctx):
        """Gets a fake user with some random data."""
        url = "https://randomuser.me/api/?results=1"

        async with ctx.typing():
            data = await self.get_json(url)
            data = data["results"][0]
            embed = (
                discord.Embed(color=discord.Color.blurple())
                .set_author(
                    name="{} {} {}".format(
                        data["name"]["title"],
                        data["name"]["first"],
                        data["name"]["last"],
                    ),
                    icon_url=data["picture"]["large"],
                )
                .add_field(name="Gender", value=data["gender"])
                .add_field(name="Username", value=data["login"]["username"])
                .add_field(name="Password", value=data["login"]["password"])
                .add_field(
                    name="Location",
                    value="{}, {}, {}, {}".format(
                        data["location"]["street"]["name"],
                        data["location"]["city"],
                        data["location"]["state"],
                        data["location"]["country"],
                    ),
                )
                .add_field(name="Email", value=data["email"])
                .add_field(name="Date of birth", value=data["dob"]["date"])
                .add_field(name="Phone", value=data["phone"])
            )

            await ctx.send(embed=embed)

    @commands.command(name="dadjoke")
    async def dad_joke(self, ctx):
        """Gets a random dad joke."""
        url = "https://icanhazdadjoke.com/"
        headers = {"Accept": "application/json"}

        async with ctx.typing(), aiohttp.ClientSession(
            headers=headers
        ) as session, session.get(url) as reponse:
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
            "Ip: {}\n"
            "Port: {}\n\n"
            "Online: {}\n\n"
            "Players:\n{}/{}\n{}\n"
            "Version(s):\n{}\n\n"
            "Mods:\n{}\n\n"
            "Motd:\n{}```"
        ).format(
            data["hostname"],
            data["ip"],
            data["port"],
            data["online"],
            data["players"]["online"],
            data["players"]["max"],
            ", ".join(data["players"]["list"]) if "list" in data["players"] else "",
            data["version"],
            len(data["mods"]["names"]) if "mods" in data else None,
            "\n".join([s.strip() for s in data["motd"]["clean"]]),
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
            if isinstance(definition, dict):
                embed.description = "```No definition found```"
                return await ctx.send(embed=embed)

            definition = definition[0]

            if "phonetics" in definition:
                embed.title = definition["phonetics"][0]["text"]
                embed.description = (
                    f"[pronunciation]({definition['phonetics'][0]['audio']})"
                )

            for meaning in definition["meanings"]:
                embed.add_field(
                    name=meaning["partOfSpeech"],
                    value=f"```{meaning['definitions'][0]['definition']}```",
                )

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

        latex = re.sub(r"```\w+\n|```", "", latex)

        if "%%preamble%%" in latex:
            _, pre, latex = re.split("%%preamble%%", latex)
            preamble += pre

        data = (
            f"formula={latex}&fsize=50px&fcolor=FFFFFF&mode=0&out=1"
            f"&remhost=quicklatex.com&preamble={preamble}"
        )

        async with ctx.typing(), aiohttp.ClientSession() as session, session.post(
            url, data=data
        ) as response:
            res = await response.text()

        if "Internal Server Error" in res:
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description="Internal Server Error.",
                )
            )

        image = res.split()[1]

        if image == "https://quicklatex.com/cache3/error.png":
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description=f"```latex\n{res[49:]}```",
                )
            )

        await ctx.send(image)

    @commands.command()
    async def snake(self, ctx):
        """Gets a random snake image."""
        await ctx.send(
            "https://raw.githubusercontent.com/Singularitat/snake-api/master/images/{}.jpg".format(
                random.randint(1, 769)
            )
        )

    @commands.command()
    async def monkey(self, ctx):
        """Gets a random monkey."""
        url = "https://ntgc.ddns.net/mAPI/api"

        async with ctx.typing():
            monkey = await self.get_json(url)

        await ctx.send(monkey["image"])

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
    async def bird2(self, ctx):
        """Gets a random bird image."""
        url = "http://shibe.online/api/birds"

        async with ctx.typing():
            image = await self.get_json(url)

        await ctx.send(image[0])

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
    async def cat3(self, ctx):
        """Gets a random cat image."""
        url = "https://cataas.com/cat?json=true"

        async with ctx.typing():
            image = await self.get_json(url)

        await ctx.send(f"https://cataas.com{image['url']}")

    @commands.command()
    async def cat4(self, ctx):
        """Gets a random cat image."""
        url = "https://thatcopy.pw/catapi/rest"

        async with ctx.typing():
            image = await self.get_json(url)

        await ctx.send(image["webpurl"])

    @commands.command()
    async def cat5(self, ctx):
        """Gets a random cat image."""
        url = "http://shibe.online/api/cats"

        async with ctx.typing():
            image = await self.get_json(url)

        await ctx.send(image[0])

    @commands.command(name="catstatus")
    async def cat_status(self, ctx, status):
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

    @commands.command(name="dogstatus")
    async def dog_status(self, ctx, status):
        """Gets a dog image for a status e.g Error 404 not found."""
        await ctx.send(f"https://httpstatusdogs.com/img/{status}.jpg")

    @commands.command()
    async def shibe(self, ctx):
        """Gets a random dog image."""
        url = "http://shibe.online/api/shibes"

        async with ctx.typing():
            image = await self.get_json(url)

        await ctx.send(image[0])

    @commands.command()
    async def xkcd(self, ctx, num: int = None):
        """Gets a random xkcd comic.

        num: int
            The xkcd to get has to be between 0 and 2438"""
        if not num or num > 2478 or num < 0:
            num = random.randint(0, 2478)

        url = f"https://xkcd.com/{num}/info.0.json"

        async with ctx.typing():
            data = await self.get_json(url)

        if not data:
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(), description="```xkcd timed out.```"
                )
            )

        await ctx.send(data["img"])

    @commands.command(aliases=["urbandictionary"])
    async def urban(self, ctx, *, search):
        """Grabs the definition of something from the urban dictionary.

        search: str
            The term to search for.
        """
        cache_search = f"urban-{search}"
        cache = orjson.loads(DB.db.get(b"cache"))

        embed = discord.Embed(colour=discord.Color.blurple())

        if cache_search in cache:
            defin = cache[cache_search].pop()

            if len(cache[cache_search]) == 0:
                cache.pop(cache_search)
        else:
            url = f"https://api.urbandictionary.com/v0/define?term={search}"

            async with ctx.typing():
                urban = await self.get_json(url)

            if not urban:
                embed.title = "Timed out try again later"
                return await ctx.send(embed=embed)

            if not urban["list"]:
                embed.title = "No results found"
                return await ctx.send(embed=embed)

            urban["list"].sort(key=lambda defin: defin["thumbs_up"])

            defin = urban["list"].pop()
            cache[cache_search] = urban["list"]

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

        DB.db.put(b"cache", orjson.dumps(cache))
        self.loop.call_later(300, DB.delete_cache, cache_search, cache)
        await ctx.send(embed=embed)

    @commands.command(aliases=["wiki"])
    async def wikipedia(self, ctx: commands.Context, *, search: str):
        """Return list of results containing your search query from wikipedia.

        search: str
            The term to search wikipedia for.
        """
        async with ctx.typing():
            titles = await self.get_json(
                f"https://en.wikipedia.org/w/api.php?action=opensearch&search={search}"
            )
            embed = discord.Embed(color=discord.Color.blurple())

            def check(message: discord.Message) -> bool:
                return (
                    message.author.id == ctx.author.id
                    and message.channel == ctx.channel
                )

            if not titles:
                embed.description = "```Couldn't find any results```"
                return await ctx.send(embed=embed)

            embed.title = f"Wikipedia results for `{search}`"
            embed.description = "\n".join(
                f"`{index}` [{title}]({url})"
                for index, (title, url) in enumerate(zip(titles[1], titles[3]), start=1)
            )
            embed.timestamp = datetime.utcnow()

            await ctx.send(embed=embed)

    @commands.command()
    async def covid(self, ctx, *, country="nz"):
        """Shows current coronavirus cases, defaults to New Zealand.

        country: str - The country to search for
        """
        url = "https://corona.lmao.ninja/v3/covid-19/countries/" + country
        if country.lower() == "all":
            url = "https://corona.lmao.ninja/v3/covid-19/all"

        embed = discord.Embed(colour=discord.Color.red())

        async with ctx.typing():
            data = await self.get_json(url)

        if "country" not in data:
            embed.description = (
                "```Not a valid country\nExamples: NZ, New Zealand, all```"
            )
            return await ctx.send(embed=embed)

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
        embed.timestamp = datetime.utcnow()

        await ctx.send(embed=embed)

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

    @commands.command()
    async def tenor(self, ctx, *, search):
        """Gets a random gif from tenor based off a search.

        search: str
            The gif search term.
        """
        cache_search = f"tenor-{search}"
        cache = orjson.loads(DB.db.get(b"cache"))

        if cache_search in cache:
            url = random.choice(cache[cache_search])
            cache[cache_search].remove(url)

            if len(cache[cache_search]) == 0:
                cache.pop(cache_search)

            DB.db.put(b"cache", orjson.dumps(cache))

            return await ctx.send(url)

        url = f"https://api.tenor.com/v1/search?q={search}&limit=50"

        async with ctx.typing():
            tenor = await self.get_json(url)

        tenor = [image["media"][0]["gif"]["url"] for image in tenor["results"]]
        image = random.choice(tenor)
        tenor.remove(image)
        cache[cache_search] = tenor

        DB.db.put(b"cache", orjson.dumps(cache))
        self.loop.call_later(300, DB.delete_cache, cache_search, cache)
        await ctx.send(image)


def setup(bot: commands.Bot) -> None:
    """Starts apis cog."""
    bot.add_cog(apis(bot))
