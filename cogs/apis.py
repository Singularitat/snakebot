import html
import random
import re
import textwrap
from html import unescape

from datetime import datetime
from discord.ext import commands
import discord
import orjson


class apis(commands.Cog):
    """For commands related to apis."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.DB = bot.DB
        self.loop = bot.loop

    @commands.command()
    async def insult(self, ctx):
        """Insults you."""
        url = "https://evilinsult.com/generate_insult.php?lang=en&type=json"
        data = await self.bot.get_json(url)

        await ctx.send(data["insult"])

    @commands.command()
    async def inspiro(self, ctx):
        """Gets images from inspirobot.me an ai quote generator."""
        url = "https://inspirobot.me/api?generate=true"

        async with ctx.typing(), self.bot.client_session.get(url) as quote:
            await ctx.send(await quote.text())

    @commands.command()
    async def wikipath(self, ctx, source: str, *, target: str):
        """Gets the shortest wikipedia path between two articles.

        source: str
        target: str
        """
        url = "https://api.sixdegreesofwikipedia.com/paths"
        json = {"source": source, "target": target}

        embed = discord.Embed(color=discord.Color.blurple())
        description = ""

        async with ctx.typing(), self.bot.client_session.post(
            url, json=json
        ) as response:
            paths = await response.json()

            for num in paths["paths"][0]:
                page = paths["pages"][str(num)]
                description += (
                    f"[{page['title']}]({page['url']}) - {page['description']}\n"
                )

            embed.description = description
            embed.set_footer(text="In order of start to finish")
            first_page = paths["pages"][str(paths["paths"][0][0])]
            if "thumbnailUrl" in first_page:
                embed.set_author(
                    name=f"From {source} to {target}",
                    icon_url=first_page["thumbnailUrl"],
                )
            else:
                embed.title = f"From {source} to {target}"
            if "thumbnailUrl" in page:
                embed.set_thumbnail(url=page["thumbnailUrl"])
            await ctx.send(embed=embed)

    @commands.command()
    async def wolfram(self, ctx, *, query):
        """Gets the output of a query from wolfram alpha."""
        query = query.replace(" ", "+")
        url = (
            "https://lin2jing4-cors-1.herokuapp.com/api.wolframalpha.com/v2/query"
            "?&output=json&podstate=step-by-step+solution&podstate=step-by-step&podstate"
            "=show+all+steps&scantimeout=30&podtimeout=30&formattimeout=30&parsetimeout"
            "=30&totaltimeout=30&reinterpret=true&podstate=undefined&appid="
            f"KQRKKJ-8WHPY395HA&input={query}&lang=en"
        )

        headers = {"Origin": "https://wolfreealpha.gitlab.io"}
        embed = discord.Embed(color=discord.Color.blurple())

        async with ctx.typing(), self.bot.client_session.get(
            url, headers=headers
        ) as response:
            data = (await response.json())["queryresult"]

        if data["error"]:
            embed.description = "```Calculation errored out```"
            return await ctx.send(embed=embed)

        msg = ""

        for pod in data["pods"]:
            if pod["title"] and pod["subpods"][0]["plaintext"]:
                msg += f"{pod['title']}\n{pod['subpods'][0]['plaintext']}\n\n"

        embed.title = "Results"
        embed.description = f"```\n{msg}```"
        await ctx.send(embed=embed)

    @commands.command()
    async def currency(self, ctx, orginal, amount: float, new):
        """Converts between currencies.

        orginal: str
            The orginal currency.
        amount: int
        new: str
            The new currency.
        """
        new = new.upper()
        orginal = orginal.upper()

        url = f"https://api.frankfurter.app/latest?amount={amount}&from={orginal}&to={new}"
        embed = discord.Embed(color=discord.Color.blurple())

        async with ctx.typing():
            data = await self.bot.get_json(url)

            embed.description = (
                f"```{amount} {orginal} is {data['rates'][new]} {new}```"
            )

        await ctx.send(embed=embed)

    @commands.command()
    async def country(self, ctx, *, name):
        """Show information about a given country.

        name: str
        """
        url = f"https://restcountries.com/v3.1/name/{name}"
        embed = discord.Embed(color=discord.Color.blurple())

        async with ctx.typing():
            data = await self.bot.get_json(url)

            if not isinstance(data, list):
                embed.description = "```Country not found```"
                return await ctx.send(embed=embed)

            data = data[0]

            embed.set_author(name=data["name"]["common"], icon_url=data["flags"][-1])
            embed.add_field(
                name="Capital", value=data.get("capital", ["No Capital"])[0]
            )
            embed.add_field(name="Demonym", value=data["demonyms"]["eng"]["m"])
            embed.add_field(name="Continent", value=data["region"])
            embed.add_field(
                name="Total Area",
                value=f"{data['area']:,.0f}km²" if "area" in data else "NaN",
            )
            embed.add_field(name="TLD(s)", value=", ".join(data["tld"]))

        await ctx.send(embed=embed)

    @commands.command()
    async def fact(self, ctx):
        """Gets a random fact."""
        url = "https://asli-fun-fact-api.herokuapp.com"

        async with ctx.typing():
            data = await self.bot.get_json(url)

            text = data["data"]["fact"]

            await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(), description=f"```{text}```"
                )
            )

    @commands.command(aliases=["so"])
    async def stackoverflow(self, ctx, *, search):
        """Gets stackoverflow posts based off a search.

        search: str
        """
        url = (
            "https://api.stackexchange.com/2.3/search/advanced?pagesize=5&"
            f"order=asc&sort=relevance&q={search}&site=stackoverflow"
        )

        embed = discord.Embed(color=discord.Color.blurple())

        async with ctx.typing():
            posts = (await self.bot.get_json(url))["items"]

            if not posts:
                embed.description = "```No posts found```"
                return await ctx.send(embed=embed)

            for post in posts:
                embed.add_field(
                    name=f"`{unescape(post['title'])}`",
                    value=f"""
                    Score: {post['score']}
                    Views: {post['view_count']}
                    Tags: {', '.join(post['tags'][:3])}
                    [Link]({post['link']})""",
                    inline=False,
                )

        await ctx.send(embed=embed)

    @commands.command()
    async def kanye(self, ctx):
        """Gets a random Kanye West quote."""
        url = "https://api.kanye.rest"

        async with ctx.typing():
            quote = await self.bot.get_json(url)
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
            quote = await self.bot.get_json(url)
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
            quote = await self.bot.get_json(url)
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
            rhymes = await self.bot.get_json(url)

            embed = discord.Embed(color=discord.Color.blurple())

            if not rhymes:
                embed.description = "```No results found```"
                return await ctx.send(embed=embed)

            embed.set_footer(text="The numbers below are the scores")

            for rhyme in rhymes:
                embed.add_field(name=rhyme["word"], value=rhyme.get("score", "N/A"))

            await ctx.send(embed=embed)

    @commands.command()
    async def spelling(self, ctx, word):
        """Gets possible spellings of [word].

        words: str
            The words to get possible spellings of.
        """
        url = f"https://api.datamuse.com/words?sp={word}&max=9"

        async with ctx.typing():
            spellings = await self.bot.get_json(url)

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
            meanings = await self.bot.get_json(url)

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
            categories = await self.bot.get_json(url)

            await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    title="All categories of the public apis api",
                    description="```{}```".format("\n".join(categories)),
                )
            )

    @apis.command()
    async def random(self, ctx, category=""):
        """Gets a random api.

        category: str
        """
        url = f"https://api.publicapis.org/random?category={category}"

        async with ctx.typing():
            data = (await self.bot.get_json(url))["entries"][0]

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
            entries = (await self.bot.get_json(url))["entries"]

            embed = discord.Embed(color=discord.Color.blurple())

            if not entries:
                embed.description = f"No apis found for `{search}`"
                return await ctx.send(embed=embed)

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
            data = await self.bot.get_json(url)

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
                game = random.choice(await self.bot.get_json(url))

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
    async def category(self, ctx, category=None):
        """Gets a random game that is free by category.

        category: str
        """
        embed = discord.Embed(color=discord.Color.blurple())

        if not category:
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
            game = random.choice(await self.bot.get_json(url))

            embed.title = game["title"]
            embed.description = (
                f"{game['short_description']}\n[Link]({game['game_url']})"
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
            apod = await self.bot.get_json(url)

            embed = discord.Embed(
                color=discord.Color.blurple(),
                title=apod["title"],
                description="[Link](https://apod.nasa.gov/apod/astropix.html)",
            )
            if "hdurl" in apod:
                embed.set_image(url=apod["hdurl"])
            await ctx.send(embed=embed)

    @commands.command(name="githubtrending", aliases=["githubt", "tgithub"])
    async def github_trending(self, ctx):
        """Gets trending github repositories."""
        url = "https://api.trending-github.com/github/repositories"

        async with ctx.typing():
            repositories = await self.bot.get_json(url)
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
            data = await self.bot.get_json(url)
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
        if country != "new zealand":
            country = country.replace(" ", "_")

        async with ctx.typing():
            data = await self.bot.get_json(url)
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
            data = await self.bot.get_json(url)
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

        async with ctx.typing(), self.bot.client_session.get(
            url, headers=headers
        ) as reponse:
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
            data = await self.bot.get_json(url)
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
            data = await self.bot.get_json(url)

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
            data = await self.bot.get_json(url)

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
            definition = await self.bot.get_json(url)

            embed = discord.Embed(color=discord.Color.blurple())
            if isinstance(definition, dict):
                embed.description = "```No definition found```"
                return await ctx.send(embed=embed)

            definition = definition[0]

            if definition["phonetics"][0]:
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
            "\\usepackage{amsmath}\n"
            "\\usepackage{amsfonts}\n"
            "\\usepackage{amssymb}\n"
            "\\newcommand{\\N}{\\mathbb N}\n"
            "\\newcommand{\\Z}{\\mathbb Z}\n"
            "\\newcommand{\\Q}{\\mathbb Q}"
            "\\newcommand{\\R}{\\mathbb R}\n"
            "\\newcommand{\\C}{\\mathbb C}\n"
            "\\newcommand{\\V}[1]{\\begin{bmatrix}#1\\end{bmatrix}}\n"
            "\\newcommand{\\set}[1]{\\left\\{#1\\right\\}}"
        )

        table = {37: "%25", 38: "%26"}
        latex = re.sub(r"```\w+\n|```", "", latex).strip("\n").translate(table)

        if "%%preamble%%" in latex:
            _, pre, latex = re.split("%%preamble%%", latex)
            preamble += pre.translate(table)

        data = (
            f"formula={latex}&fsize=50px&fcolor=FFFFFF&mode=0&out=1"
            f"&remhost=quicklatex.com&preamble={preamble}"
        )

        async with ctx.typing(), self.bot.client_session.post(
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
    async def xkcd(self, ctx):
        """Gets a random xkcd comic."""
        await ctx.send(f"https://xkcd.com/{random.randint(0, 2509)}")

    @commands.command(aliases=["urbandictionary"])
    async def urban(self, ctx, *, search):
        """Grabs the definition of something from the urban dictionary.

        search: str
            The term to search for.
        """
        cache_search = f"urban-{search}"
        cache = orjson.loads(self.DB.main.get(b"cache"))

        embed = discord.Embed(colour=discord.Color.blurple())

        if cache_search in cache:
            defin = cache[cache_search].pop()

            if not cache[cache_search]:
                cache.pop(cache_search)
        else:
            url = f"https://api.urbandictionary.com/v0/define?term={search}"

            async with ctx.typing():
                urban = await self.bot.get_json(url)

            if not urban:
                embed.title = "Timed out try again later"
                return await ctx.send(embed=embed)

            if not urban["list"]:
                embed.title = "No results found"
                return await ctx.send(embed=embed)

            urban["list"].sort(key=lambda defin: defin["thumbs_up"])

            defin = urban["list"].pop()
            cache[cache_search] = urban["list"]
            self.DB.main.put(b"cache", orjson.dumps(cache))
            self.loop.call_later(300, self.DB.delete_cache, cache_search, cache)

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

    @commands.command()
    async def wikir(self, ctx):
        """Gets a random wikipedia article."""
        url = "https://en.wikipedia.org/api/rest_v1/page/random/summary"

        async with ctx.typing():
            data = await self.bot.get_json(url)

            embed = discord.Embed(
                color=discord.Color.blurple(),
                title=data["title"],
                description=data["extract"],
                url=data["content_urls"]["desktop"]["page"],
            )
            embed.set_image(url=data["thumbnail"]["source"])

            await ctx.send(embed=embed)

    @commands.command(aliases=["wiki"])
    async def wikipedia(self, ctx, *, search: str):
        """Return list of results containing your search query from wikipedia.

        search: str
            The term to search wikipedia for.
        """
        async with ctx.typing():
            titles = await self.bot.get_json(
                f"https://en.wikipedia.org/w/api.php?action=opensearch&search={search}",
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
        url = f"https://disease.sh/v3/covid-19/countries/{country}"

        embed = discord.Embed(colour=discord.Color.red())

        async with ctx.typing():
            data = await self.bot.get_json(url)

        if "message" in data:
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

    @commands.command(aliases=["gh"])
    async def github(self, ctx, username: str):
        """Fetches a members's GitHub information."""
        async with ctx.typing():
            user_data = await self.bot.get_json(
                f"https://api.github.com/users/{username}"
            )

            if user_data.get("message") is not None:
                return await ctx.send(
                    embed=discord.Embed(
                        title=f"The profile for `{username}` was not found.",
                        colour=discord.Colour.dark_red(),
                    )
                )

            org_data = await self.bot.get_json(user_data["organizations_url"])

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
                description=user_data["bio"] or "",
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
                    name="Organization(s)",
                    value=orgs_to_add or "No organizations",
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
        cache = orjson.loads(self.DB.main.get(b"cache"))

        if cache_search in cache:
            url = random.choice(cache[cache_search])
            cache[cache_search].remove(url)

            if not cache[cache_search]:
                cache.pop(cache_search)

            self.DB.main.put(b"cache", orjson.dumps(cache))

            return await ctx.send(url)

        url = f"https://api.tenor.com/v1/search?q={search}&limit=50"

        async with ctx.typing():
            tenor = await self.bot.get_json(url)

        tenor = [image["media"][0]["gif"]["url"] for image in tenor["results"]]
        image = random.choice(tenor)
        tenor.remove(image)
        cache[cache_search] = tenor

        self.DB.main.put(b"cache", orjson.dumps(cache))
        self.loop.call_later(300, self.DB.delete_cache, cache_search, cache)
        await ctx.send(image)


def setup(bot: commands.Bot) -> None:
    """Starts apis cog."""
    bot.add_cog(apis(bot))
