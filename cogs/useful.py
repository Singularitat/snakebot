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
import config


class useful(commands.Cog):
    """Actually useful commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.process = psutil.Process()

    @commands.command()
    async def snipe(self, ctx):
        """Snipes the last deleted message."""
        try:
            message, member = self.bot.snipe_message
            await ctx.send(f"```{member} deleted:\n{message}```")
        except AttributeError:
            await ctx.send("```No deleted messages found```")

    @commands.command()
    async def editsnipe(self, ctx):
        """Snipes the last edited message."""
        try:
            before, after, member = self.bot.editsnipe_message
            await ctx.send(f"```{member} edited:\n{before} >>> {after}```")
        except AttributeError:
            await ctx.send("```No edited messages found```")

    @commands.command()
    async def argument(self, ctx, arg, *, obj):
        """Converts arguments to a chosen discord object.

        arg: str
            The argument to be converted.
        object: str
            The object to attempt to convert to.
        """
        obj = obj.replace(" ", "").lower()
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
        if obj in objects:
            obj = await objects[obj].convert(ctx, arg)
            await ctx.send(dir(obj))
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
        """Gets the source code of a command from github.

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
        """Appends an issue to the snakebot-todo.

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
        """Grabs the definition of something from the urban dictionary.

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
            raw_response = await session.get(url, params=parameters, headers=headers)
            response = await raw_response.text()
        cry = ujson.loads(response)["data"]
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
            value=f"${round(crypto['quote']['NZD']['price'], 2)}",
            inline=False,
        )
        embed.add_field(
            name="Circulating/Max Supply",
            value=f"{crypto['circulating_supply']}/{crypto['max_supply']}",
            inline=False,
        )
        embed.add_field(
            name="Market Cap",
            value=f"${crypto['quote']['NZD']['market_cap']}",
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
                name=f"Cornavirus {response['country']}:",
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

    @commands.command(name="github", aliases=["gh"])
    @commands.cooldown(1, 60, commands.BucketType.member)
    async def get_github_info(self, ctx: commands.Context, username: str) -> None:
        """Fetches a members's GitHub information."""
        async with ctx.typing():
            async with aiohttp.ClientSession() as session:
                raw_response = await session.get(f"https://api.github.com/users/{username}")
                response = await raw_response.text()
                user_data = ujson.loads(response)

            if user_data.get("message") is not None:
                await ctx.send(
                    embed=discord.Embed(
                        title=f"The profile for `{username}` was not found.",
                        colour=discord.Colour.red(),
                    )
                )
                return

            async with aiohttp.ClientSession() as session:
                raw_response = await session.get(user_data["organizations_url"])
                response = await raw_response.text()
                org_data = ujson.loads(response)

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


def setup(bot: commands.Bot) -> None:
    """Starts useful cog."""
    bot.add_cog(useful(bot))
