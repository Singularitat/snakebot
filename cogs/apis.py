import asyncio
import html
import io
import random
import re
import textwrap
from datetime import datetime
from html import unescape

import discord
import orjson
from discord.ext import commands

URBAN_REGEX = re.compile(r"\[(.*?)\]")


class apis(commands.Cog):
    """For commands related to apis."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.DB = bot.DB
        self.loop = bot.loop

    @commands.command()
    async def curl(self, ctx, *, code):
        """Converts from a curl command to python requests.

        code: str
        """
        if not code and ctx.message.attachments:
            file = ctx.message.attachments[0]
            if file.filename.split(".")[-1] != "py":
                return
            code = (await file.read()).decode()

        url = "https://formatter.xyz:8000/api/v1/converter"
        data = {
            "from_language": "CURL",
            "input_code": re.sub(r"```\w+\n|```", "", code),
            "to_language": "PYTHON_REQUESTS",
        }

        async with ctx.typing(), self.bot.client_session.post(
            url, json=data
        ) as response:
            formatted = (await response.json())["output_code"]

        if len(formatted) > 1991:
            return await ctx.reply(
                file=discord.File(io.StringIO(formatted), "output.py")
            )

        formatted = formatted.replace("`", "`\u200b")
        await ctx.reply(f"```py\n{formatted}```")

    @commands.command()
    async def excuse(self, ctx, category=None):
        """Gets a random excuse.

        category: str
            One of the following, family, office, children, college, party
        """
        if not category:
            url = "https://excuser.herokuapp.com/v1/excuse"
        else:
            if category not in ("family", "office", "children", "college", "party"):
                return await ctx.send(
                    embed=discord.Embed(
                        description="```Category must be one of the following,"
                        " family, office, children, college, party```"
                    )
                )

            url = f"https://excuser.herokuapp.com/v1/excuse/{category}"

        data = await self.bot.get_json(url)
        await ctx.send(f"> {data[0]['excuse']}")

    @commands.command()
    async def idea(self, ctx):
        """Gets a random idea from the itsthisforthat.com website."""
        url = "http://itsthisforthat.com/api.php?json"

        async with self.bot.client_session.get(url) as resp:
            data = await resp.json(content_type=None)

        await ctx.send(data["this"] + " for " + data["that"])

    @commands.command()
    async def validate(self, ctx, domain: str):
        """Checks if domains are disposable used to check if tempmail is fine.

        domain: str
        """
        # This makes it so even if an email is passed in it is fine
        domain = domain.split("@")[-1]

        url = f"https://api.mailcheck.ai/domain/{domain}"
        data = await self.bot.get_json(url)
        embed = discord.Embed(color=discord.Color.blurple(), title=domain)

        if "error" in data:
            embed.description = f"```{data['error']}```"
            await ctx.send(embed=embed)

        if data["did_you_mean"]:
            embed.add_field(name="Did you mean?", value=data["did_you_mean"])
        embed.add_field(name="Disposable", value=data["disposable"])
        embed.add_field(name="MX records", value=data["mx"])
        embed.add_field(name="Status", value=data["status"])
        await ctx.send(embed=embed)

    @commands.command()
    async def advice(self, ctx):
        """Uses adviceslip.com to send you advice."""
        url = "https://api.adviceslip.com/advice"

        async with self.bot.client_session.get(url) as resp:
            data = await resp.json(content_type=None)

        await ctx.send("> " + data["slip"]["advice"])

    @commands.command()
    async def t0(self, ctx, *, prompt: str):
        """Uses the T0 model to do natural language processing on a prompt.

        prompt: str
        """
        url = "https://api-inference.huggingface.co/models/bigscience/T0pp"

        data = {
            "inputs": prompt,
        }

        async with ctx.typing(), self.bot.client_session.post(
            url, json=data, timeout=30
        ) as resp:
            resp = await resp.json(content_type=None)

        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                description=f"```\n{resp[0]['generated_text']}```",
            )
        )

    @commands.command()
    async def reddit(self, ctx, subreddit: str = "all"):
        """Gets a random post from a subreddit.

        subreddit: str
        """
        subreddit_cache = f"reddit-{subreddit}"
        cache = orjson.loads(self.DB.main.get(b"cache"))

        if subreddit_cache in cache:
            post = random.choice(cache[subreddit_cache])
            cache[subreddit_cache].remove(post)

            if not cache[subreddit_cache]:
                cache.pop(subreddit_cache)

            self.DB.main.put(b"cache", orjson.dumps(cache))
        else:
            url = f"https://old.reddit.com/r/{subreddit}/hot/.json"

            with ctx.typing():
                resp = await self.bot.get_json(url)

                error = resp.get("error")
                if error:
                    return await ctx.send(
                        embed=discord.Embed(
                            color=discord.Color.dark_red(),
                            description=f"Error: {error}\nMessage: {resp['message']}",
                        )
                    )

            posts = resp["data"]["children"]
            post = random.choice(posts)

            clean_posts = []

            for post in posts:
                post = post["data"]

                if post["over_18"]:
                    continue

                text = post["selftext"].replace("&amp;", "&")

                if text and len(text) > 4003:
                    text = f"{text[:4000]}..."

                if not text and (video := post["secure_media"]):
                    oembed = video.get("oembed")
                    if oembed:
                        video = oembed.get("thumbnail_url")
                        if not video:
                            video = oembed["url"]
                    else:
                        video = video["reddit_video"]["fallback_url"]
                else:
                    video = None

                title = post["title"]

                if len(title) > 256:
                    title = f"{title[:253]}..."

                clean_posts.append(
                    {
                        "title": title,
                        "text": text,
                        "video": video,
                        "url": post["url"],
                        "link": post["permalink"],
                        "sub": post["subreddit_name_prefixed"],
                    }
                )

            if not clean_posts:
                return await ctx.send(
                    embed=discord.Embed(
                        color=discord.Color.blurple(),
                        description="Couldn't find any SFW posts",
                    )
                )

            cache[subreddit_cache] = clean_posts
            self.DB.main.put(b"cache", orjson.dumps(cache))
            self.loop.call_later(300, self.DB.delete_cache, subreddit_cache, cache)

            post = random.choice(clean_posts)

        text = post.get("text")
        if text:
            embed = discord.Embed(
                color=discord.Color.blurple(),
                title=post["title"],
                description=f"{post['sub']} "
                f"[Post](https://reddit.com{post['link']})\n\n{text}",
            )
            return await ctx.send(embed=embed)

        video = post.get("video")
        if video:
            return await ctx.send(f"**{post['title']}**\n{post['sub']}\n{video}")

        if post["url"][-4:] in (".jpg", ".png"):
            embed = discord.Embed(
                color=discord.Color.blurple(),
                title=post["title"],
                description=f"{post['sub']} "
                f"[Post](https://reddit.com{post['link']})",
            )
            embed.set_image(url=post["url"])
            return await ctx.send(embed=embed)

        await ctx.send(f"**{post['title']}**\n{post['sub']}\n{post['url']}")

    @commands.command()
    async def bots(self, ctx, amount=12):
        """Shows a little information about the top bots.

        amount: int
            Amount of bots to get.
        """
        url = "https://topbots.advaith.workers.dev/"

        bots = await self.bot.get_json(url)
        embed = discord.Embed(color=discord.Color.blurple())

        for i, bot in enumerate(bots):
            if i == amount:
                break
            embed.add_field(
                name=bot["name"],
                value=(
                    f"```ahk\nID:\n{bot['id']}\n\n"
                    f"Servers:\n{bot['servers']:,}\n\n"
                    f"Discord library:\n{bot['lib']}```"
                ),
            )

        await ctx.send(embed=embed)

    @commands.command()
    async def sky(self, ctx):
        """Gets an ai generated night sky."""
        num = random.randint(1, 5000)
        url = (
            "https://firebasestorage.googleapis.com/v0/b/thisnightskydoes"
            f"notexist.appspot.com/o/images%2Fseed{num:0>4}.jpg?alt=media"
        )
        await ctx.send(url)

    @commands.command()
    async def beach(self, ctx):
        """Uses thisbeachdoesnotexist.com to gets an ai generated beach."""
        num = random.randint(1, 9999)
        await ctx.send(f"https://thisbeachdoesnotexist.com/data/seeds-075/{num}.jpg")

    @commands.command()
    async def wojak(self, ctx):
        """This wojak does not exist."""
        num = random.randint(1, 1576)  # This how how they do it on their website
        await ctx.send(f"https://thiswojakdoesnotexist.com/img/{num}.png")

    @commands.command()
    async def city(self, ctx):
        """This city doesn't exist."""
        url = "https://thiscitydoesnotexist.com/"

        async with self.bot.client_session.get(url) as resp:
            text = await resp.text()
            link = re.search(r"<img src=\"\.(.*)\" alt=", text).group(1)

        await ctx.send(f"http://thiscitydoesnotexist.com{link}")

    @commands.command()
    async def story(self, ctx):
        """Gets an ai generated story."""
        url = "https://boredhumans.com/api_story.php"

        async with ctx.typing(), self.bot.client_session.post(url) as resp:
            text = await resp.text()

        await ctx.send(text.replace("\n\n\n", "\n"))

    @commands.command()
    async def poetry(self, ctx):
        """Gets ai generated poetry."""
        url = "https://boredhumans.com/api_poetry.php"

        async with ctx.typing(), self.bot.client_session.post(
            url, data={"lyrics1": True}
        ) as resp:
            data = await resp.json(content_type=None)

        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                title=data["title"],
                description=">>> " + data["lyrics"],
            )
        )

    @commands.command()
    async def surreal(self, ctx):
        """Gets a surreal ai generated image."""
        num = random.randint(1, 125)
        await ctx.send(f"https://boredhumans.b-cdn.net/dreams/{num}.jpg")

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(aliases=["complete"])
    async def synth(self, ctx, *, prompt: str):
        """Completes a text prompt using GPT-J 6B."""
        url = "https://api.eleuther.ai/completion"

        data = {
            "context": prompt,
            "remove_input": False,
            "temp": 0.8,
            "topP": 0.9,
        }

        try:
            async with ctx.typing(), self.bot.client_session.post(
                url, json=data, timeout=30
            ) as resp:
                resp = await resp.json()
        except asyncio.TimeoutError:
            return await ctx.reply(
                embed=discord.Embed(
                    color=discord.Color.dark_red(),
                    description="Request timed out",
                ).set_footer(text="api may be experiencing high trafic")
            )

        await ctx.reply(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                description=f"```\n{resp[0]['generated_text']}```",
            )
        )

    @commands.command()
    async def art(self, ctx):
        """Gets an ai generated painting."""
        url = "https://thisartworkdoesnotexist.com"

        async with ctx.typing(), self.bot.client_session.get(url) as resp:
            with io.BytesIO((await resp.read())) as image_binary:
                await ctx.send(file=discord.File(fp=image_binary, filename="image.png"))

    @commands.command()
    async def coffee(self, ctx):
        """Gets a random image of coffee."""
        url = "https://coffee.alexflipnote.dev/random.json"
        data = await self.bot.get_json(url)

        await ctx.send(data["file"])

    @commands.command()
    async def insult(self, ctx):
        """Insults you."""
        url = "https://evilinsult.com/generate_insult.php?lang=en&type=json"

        with ctx.typing():
            data = await self.bot.get_json(url)

        await ctx.send(data["insult"])

    @commands.command()
    async def inspiration(self, ctx):
        """Uses zenquotes.io to get an inspirational quote."""
        url = "https://zenquotes.io/api/random"

        async with self.bot.client_session.get(url) as resp:
            data = (await resp.json(content_type=None))[0]

        embed = discord.Embed(color=discord.Color.blurple(), description=data["q"])
        embed.set_footer(text=f"― {data['a']}")

        await ctx.send(embed=embed)

    @commands.command()
    async def inspiro(self, ctx):
        """Gets images from inspirobot.me an ai quote generator."""
        url = "https://inspirobot.me/api?generate=true"

        async with self.bot.client_session.get(url) as quote:
            await ctx.send(
                embed=discord.Embed(color=discord.Color.random())
                .set_image(url=(await quote.text()))
                .set_footer(
                    icon_url="https://inspirobot.me/website/images/inspirobot-dark-green.png",
                    text="inspirobot.me",
                )
            )

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
            url, json=json, timeout=60
        ) as response:
            paths = await response.json()

        error = paths.get("error")
        if error:
            embed.description = error
            return await ctx.send(embed=embed)

        paths, pages = paths["paths"], paths["pages"]

        if not paths or not pages:
            embed.description = (
                f"No path of Wikipedia links exists from {source} to {target}"
            )
            return await ctx.send(embed=embed)

        for num in paths[0]:
            page = pages[str(num)]
            description += (
                f"[{page['title']}]({page['url']}) - {page.get('description', 'N/A')}\n"
            )

        embed.description = description
        embed.set_footer(text="In order of start to finish")
        first_page = pages[str(paths[0][0])]
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
        table = {33: "%21", 40: "%28", 41: "%29", 42: "%2B", 47: "%2F"}
        query = query.translate(table).replace(" ", "+")
        url = (
            "https://lin2jing4-cors-4.herokuapp.com/api.wolframalpha.com/v2/query"
            "?&output=json&podstate=step-by-step+solution&podstate=step-by-step&"
            "podstate=show+all+steps&scantimeout=30&podtimeout=30&formattimeout=30"
            "&parsetimeout=30&totaltimeout=30&reinterpret=true&podstate=undefined&"
            f"appid=P7JH3K-27RHWR53JQ&input={query}&lang=en"
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
    async def country(self, ctx, *, name="New Zealand"):
        """Show information about a given country.

        name: str
        """
        url = f"https://restcountries.com/v3.1/name/{name}"
        embed = discord.Embed(color=discord.Color.blurple())

        data = await self.bot.get_json(url)

        if not isinstance(data, list):
            embed.description = "```Country not found```"
            return await ctx.send(embed=embed)

        data = data[0]

        embed.set_author(name=data["name"]["common"], icon_url=data["flags"]["png"])
        embed.add_field(name="Capital", value=data.get("capital", ["No Capital"])[0])
        embed.add_field(name="Demonym", value=data["demonyms"]["eng"]["m"])
        embed.add_field(name="Continent", value=data["region"])
        embed.add_field(
            name="Total Area",
            value=f"{data['area']:,.0f}km²" if "area" in data else "NaN",
        )
        embed.add_field(name="Population", value=f"{data['population']:,}")
        embed.add_field(name="TLD(s)", value=", ".join(data["tld"]))

        await ctx.send(embed=embed)

    @commands.command()
    async def fact(self, ctx):
        """Gets a random fact."""
        url = "https://uselessfacts.jsph.pl/random.json?language=en"

        with ctx.typing():
            data = await self.bot.get_json(url)

            await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(), description=f"> {data['text']}"
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

        with ctx.typing():
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

        quote = await self.bot.get_json(url)
        embed = discord.Embed(
            color=discord.Color.blurple(), description="> " + quote["quote"]
        )
        embed.set_footer(text="― Kayne West")
        await ctx.send(embed=embed)

    @commands.command()
    async def quote(self, ctx):
        """Gets a random quote."""
        url = "https://quote-garden.herokuapp.com/api/v3/quotes/random"

        quote = await self.bot.get_json(url)
        quote = quote["data"][0]

        embed = discord.Embed(
            color=discord.Color.blurple(), description="> " + quote["quoteText"]
        )
        embed.set_footer(text=f"― {quote['quoteAuthor']}")
        await ctx.send(embed=embed)

    @commands.command()
    async def suntzu(self, ctx):
        """Gets fake Sun Tzu art of war quotes."""
        url = "http://api.fakeartofwar.gaborszathmari.me/v1/getquote"

        quote = await self.bot.get_json(url)
        embed = discord.Embed(
            color=discord.Color.blurple(), description="> " + quote["quote"]
        )
        embed.set_footer(text="― Sun Tzu, Art Of War")
        await ctx.send(embed=embed)

    @commands.command()
    async def rhyme(self, ctx, word):
        """Gets words that rhyme with [word].

        words: str
        """
        url = f"https://api.datamuse.com/words?rel_rhy={word}&max=9"

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

        spellings = await self.bot.get_json(url)

        embed = discord.Embed(color=discord.Color.blurple(), title="Possible spellings")

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

        meanings = await self.bot.get_json(url)

        embed = discord.Embed(color=discord.Color.blurple(), title="Possible meanings")

        if not meanings:
            embed.description = "```No results found```"
            return await ctx.send(embed=embed)

        embed.set_footer(text="The numbers below are the scores")

        for meaning in meanings:
            embed.add_field(name=meaning["word"], value=meaning["score"])

        await ctx.send(embed=embed)

    @commands.group(invoke_without_command=True)
    async def apis(self, ctx):
        """Command group for the public apis api."""
        embed = discord.Embed(
            color=discord.Color.blurple(),
            description=f"```Usage: {ctx.prefix}apis [categories/random/search]```",
        )
        await ctx.send(embed=embed)

    @apis.command()
    async def categories(self, ctx):
        """Gets all the categories of the public apis api."""
        url = "https://api.publicapis.org/categories"

        data = await self.bot.get_json(url)

        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                title="All categories of the public apis api",
                description="```prolog\n{}```".format("\n".join(data["categories"])),
            )
        )

    @apis.command()
    async def random(self, ctx, category=""):
        """Gets a random api.

        category: str
        """
        url = f"https://api.publicapis.org/random?category={category}"

        data = (await self.bot.get_json(url))["entries"][0]

        embed = discord.Embed(
            color=discord.Color.blurple(),
            title=data["API"],
            description=f"{data['Description']}\n[Link]({data['Link']})",
        )
        embed.add_field(name="Auth", value="None" if not data["Auth"] else data["Auth"])
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

    @commands.command()
    async def apod(self, ctx):
        """Gets the NASA Astronomy Picture of the Day."""
        url = "https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY"
        embed = discord.Embed(color=discord.Color.blurple())

        async with self.bot.client_session.get(url, timeout=30) as resp:
            apod = await resp.json()

        if not apod:
            embed.title = "Failed to get Astronomy Picture of the Day"
            embed.set_footer(
                text="NASA api might just be experiencing high amounts of trafic"
            )
            return await ctx.send(embed=embed)

        embed.title = apod["title"]
        embed.description = "[Link](https://apod.nasa.gov/apod/astropix.html)"

        if "hdurl" in apod:
            embed.set_image(url=apod["hdurl"])
        await ctx.send(embed=embed)

    @commands.command()
    async def gender(self, ctx, first_name):
        """Estimates a gender from a first name.

        first_name: str
        """
        url = f"https://api.genderize.io/?name={first_name}"

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

        data = await self.bot.get_json(url)
        embed = discord.Embed(color=discord.Color.blurple())

        if country not in data:
            embed.description = f"```Country {country.title()} not found.```"
            return await ctx.send(embed=embed)

        embed.title = f"{country.title()} Search Trends"
        embed.description = "```{}```".format("\n".join(data[country]))
        await ctx.send(embed=embed)

    @commands.command(name="dadjoke")
    async def dad_joke(self, ctx):
        """Gets a random dad joke."""
        url = "https://icanhazdadjoke.com/"
        headers = {"Accept": "application/json"}

        async with self.bot.client_session.get(url, headers=headers) as resp:
            data = await resp.json()

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
            amount = drink[f"strMeasure{i}"] or "N/A"
            ingredients.append(f"{drink[f'strIngredient{i}']}: {amount}")

        embed.add_field(name="Category", value=drink["strCategory"])
        embed.add_field(name="Glass", value=drink["strGlass"])
        embed.add_field(name="Alcohol", value=drink["strAlcoholic"])
        embed.add_field(name="Instructions", value=drink["strInstructions"])
        embed.add_field(name="Ingredients", value="\n".join(ingredients))

        await ctx.send(embed=embed)

    @commands.command()
    async def trivia(self, ctx, difficulty="easy"):
        """Does a simple trivia game.

        difficulty: str
            Choices are easy, medium or hard.
        """
        url = f"https://opentdb.com/api.php?amount=1&difficulty={difficulty}&type=multiple"

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
                user == ctx.author
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

        with ctx.typing():
            data = await self.bot.get_json(url)

        embed = discord.Embed(color=discord.Color.blurple())

        if not data:
            embed.description = "```Pinging timed out.```"
            return await ctx.send(embed=embed)

        if data["debug"]["ping"] is False:
            embed.description = "```Pinging failed.```"
            return await ctx.send(embed=embed)

        embed.add_field(name="Hostname", value=data.get("hostname", "N/A"))
        embed.add_field(name="IP/Port", value=f"{data['ip']}\n{data['port']}")
        embed.add_field(name="Online", value=data["online"])
        players = ", ".join(data["players"].get("list", ""))
        embed.add_field(
            name="Players",
            value=f"{data['players']['online']}/{data['players']['max']}\n{players}",
        )
        embed.add_field(name="Version", value=data["version"])
        embed.add_field(
            name="Mods", value=len(data["mods"]["names"]) if "mods" in data else "N/A"
        )
        embed.add_field(name="Motd", value="\n".join(data["motd"]["clean"]))
        cachetime = data["debug"]["cachetime"]
        if cachetime:
            embed.add_field(name="Cached", value=f"<t:{cachetime}:R>")
        embed.set_thumbnail(url=f"https://api.mcsrvstat.us/icon/{ip}")
        await ctx.send(embed=embed)

    @commands.command()
    async def define(self, ctx, *, word):
        """Defines a word via the dictionary.com api.

        word: str
        """
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"

        definition = await self.bot.get_json(url)

        embed = discord.Embed(color=discord.Color.blurple())
        if isinstance(definition, dict):
            embed.description = "```No definition found```"
            return await ctx.send(embed=embed)

        definition = definition[0]

        phonetics = definition["phonetics"]

        if phonetics and (phonetics := phonetics[0]):
            embed.title = phonetics["text"]
            embed.description = f"[pronunciation]({phonetics['audio']})"

        for meaning in definition["meanings"]:
            embed.add_field(
                name=meaning["partOfSpeech"],
                value=f"```{meaning['definitions'][0]['definition']}```",
            )

        await ctx.send(embed=embed)

    @commands.command(aliases=["syn", "synonym"])
    async def synonyms(self, ctx, *, word):
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"

        data = await self.bot.get_json(url)

        embed = discord.Embed(color=discord.Color.blurple())
        if isinstance(data, dict):
            embed.description = "```Word not found```"
            return await ctx.send(embed=embed)

        data = data[0]
        description = ""

        for meaning in data["meanings"]:
            temp = meaning["partOfSpeech"] + "\n  "
            seen = False
            for definition in meaning["definitions"]:
                synonyms = definition["synonyms"]
                if synonyms:
                    temp += (
                        definition["definition"]
                        + "\n    "
                        + "\n    ".join(synonyms)
                        + "\n\n  "
                    )
                    seen = True
            if seen:
                description += temp[:-2]

        if not description:
            embed.description = "```No synonyms found```"
            return await ctx.send(embed=embed)

        embed.url = f"https://www.dictionary.com/browse/{word}"
        embed.title = f"{word.title()} Synonyms"
        embed.description = f"```prolog\n{description.title().strip()}```"
        await ctx.send(embed=embed)

    @commands.command(aliases=["antonym"])
    async def antonyms(self, ctx, *, word):
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"

        data = await self.bot.get_json(url)

        embed = discord.Embed(color=discord.Color.blurple())
        if isinstance(data, dict):
            embed.description = "```Word not found```"
            return await ctx.send(embed=embed)

        data = data[0]
        description = ""

        for meaning in data["meanings"]:
            temp = meaning["partOfSpeech"] + "\n  "
            seen = False
            for definition in meaning["definitions"]:
                antonyms = definition["antonyms"]
                if antonyms:
                    temp += (
                        definition["definition"]
                        + "\n    "
                        + "\n    ".join(antonyms)
                        + "\n\n  "
                    )
                    seen = True
            if seen:
                description += temp[:-2]

        if not description:
            embed.description = "```No antonyms found```"
            return await ctx.send(embed=embed)

        embed.url = f"https://www.dictionary.com/browse/{word}"
        embed.title = f"{word.title()} Antonyms"
        embed.description = f"```prolog\n{description.title().strip()}```"
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
        await ctx.send(f"https://xkcd.com/{random.randint(0, 2586)}")

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
            item = cache[cache_search].pop()

            if not cache[cache_search]:
                cache.pop(cache_search)
        else:
            url = f"https://api.urbandictionary.com/v0/define?term={search}"

            urban = await self.bot.get_json(url)

            if not urban:
                embed.title = "Timed out try again later"
                return await ctx.send(embed=embed)

            if not urban["list"]:
                embed.title = "No results found"
                return await ctx.send(embed=embed)

            urban["list"].sort(key=lambda item: item["thumbs_up"] - item["thumbs_down"])

            item = urban["list"].pop()
            cache[cache_search] = urban["list"]
            self.DB.main.put(b"cache", orjson.dumps(cache))
            self.loop.call_later(300, self.DB.delete_cache, cache_search, cache)

        embed.title = search.title()
        embed.add_field(
            name="Definition",
            value=URBAN_REGEX.sub(r"\1", item["definition"]),
            inline=False,
        )
        embed.add_field(
            name="Example", value=URBAN_REGEX.sub(r"\1", item["example"]), inline=False
        )
        embed.add_field(
            name="Votes", value=item["thumbs_up"] - item["thumbs_down"], inline=False
        )

        await ctx.send(embed=embed)

    @commands.command()
    async def wikir(self, ctx):
        """Gets a random wikipedia article."""
        url = "https://en.wikipedia.org/api/rest_v1/page/random/summary"

        data = await self.bot.get_json(url)

        embed = discord.Embed(
            color=discord.Color.blurple(),
            title=data["title"],
            description=data["extract"],
            url=data["content_urls"]["desktop"]["page"],
        )

        thumbnail = data.get("thumbnail")
        if thumbnail:
            embed.set_image(url=thumbnail["source"])

        await ctx.send(embed=embed)

    @commands.command(aliases=["wiki"])
    async def wikipedia(self, ctx, *, search: str):
        """Return list of results containing your search query from wikipedia.

        search: str
            The term to search wikipedia for.
        """
        titles = await self.bot.get_json(
            f"https://en.wikipedia.org/w/api.php?action=opensearch&search={search}",
        )
        embed = discord.Embed(color=discord.Color.blurple())

        if not titles:
            embed.description = "```Couldn't find any results```"
            return await ctx.send(embed=embed)

        embed.title = f"Wikipedia results for `{search}`"
        embed.description = "\n".join(
            f"`{index}` [{title}]({url})"
            for index, (title, url) in enumerate(zip(titles[1], titles[3]), start=1)
        )
        embed.timestamp = discord.utils.utcnow()

        await ctx.send(embed=embed)

    @commands.command()
    async def covid(self, ctx, *, country="nz"):
        """Shows current coronavirus cases, defaults to New Zealand.

        country: str - The country to search for
        """
        url = f"https://disease.sh/v3/covid-19/countries/{country}"

        embed = discord.Embed(colour=discord.Color.red())

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
                ```prolog
                Total Cases:   Total Deaths:
                {data['cases']:<15,}{data['deaths']:,}

                Active Cases:  Cases Today:
                {data['active']:<15,}{data['todayCases']:,}

                Deaths Today:  Recovered Total:
                {data['todayDeaths']:<15,}{data['recovered']:,}
                ```
            """
        )
        embed.timestamp = discord.utils.utcnow()

        await ctx.send(embed=embed)

    @commands.command(aliases=["gh"])
    async def github(self, ctx, username: str):
        """Fetches a members's GitHub information."""
        user_data = await self.bot.get_json(f"https://api.github.com/users/{username}")

        if user_data.get("message") is not None:
            return await ctx.send(
                embed=discord.Embed(
                    title=f"The profile for `{username}` was not found.",
                    colour=discord.Colour.dark_red(),
                )
            )

        org_data = await self.bot.get_json(user_data["organizations_url"])

        orgs = [
            f"[{org['login']}](https://github.com/{org['login']})" for org in org_data
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
            timestamp=datetime.strptime(user_data["created_at"], "%Y-%m-%dT%H:%M:%SZ"),
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


def setup(bot: commands.Bot) -> None:
    """Starts apis cog."""
    bot.add_cog(apis(bot))
