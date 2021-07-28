from io import StringIO
import ast
import asyncio
import operator
import random
import re
import time
import urllib

from discord.ext import commands, menus
import aiohttp
import discord
import lxml.html
import orjson

import cogs.utils.database as DB


CODE_REGEX = re.compile(
    r"(?:(?P<lang>^[a-z0-9]+[\ \n])?)(?P<delim>(?P<block>```)|``?)(?(block)"
    r"(?:(?P<alang>[a-z0-9]+)\n)?)(?:[ \t]*\n)*(?P<code>.*?)\s*(?P=delim)",
    re.DOTALL | re.IGNORECASE,
)

RAW_CODE_REGEX = re.compile(
    r"(?:(?P<lang>^[a-z0-9]+[\ \n])?)(?P<code>(?s).*)", re.DOTALL | re.IGNORECASE
)


OPERATIONS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.LShift: operator.lshift,
    ast.RShift: operator.rshift,
    ast.BitOr: operator.or_,
    ast.BitAnd: operator.and_,
    ast.BitXor: operator.xor,
}


class InviteMenu(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=20)

    async def format_page(self, menu, entries):
        return discord.Embed(
            color=discord.Color.blurple(), description=f"```{''.join(entries)}```"
        )


class useful(commands.Cog):
    """Actually useful commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.loop = asyncio.get_event_loop()

    @commands.command(name="float")
    async def _float(self, ctx, number: float):
        """Converts a float a half-precision floating-point format.

        number: float
        """
        embed = discord.Embed(color=discord.Color.blurple())

        sign = str(int(number < 0))
        num = abs(number)

        if num < 0.001:
            embed.description = "```Number is too small```"
            return await ctx.send(embed=embed)

        exponent = 0
        shifted_num = number
        max_exponent = 9 - (len(bin(int(number))) - 2)

        while shifted_num != int(shifted_num) and exponent != max_exponent:
            shifted_num *= 2
            exponent += 1

        binary = f"{int(shifted_num):0{exponent + 1}b}"

        if index := binary.find("1"):
            binary_exponent = f"{index-1:0>5b}"
        elif not exponent:
            binary_exponent = f"{len(binary)-1:0>5b}"
        else:
            binary_exponent = f"{exponent-1:0>5b}"

        exponent_sign = str(int(bool(index)))
        mantissa = f"{binary.lstrip('0'):0<9}"[:9]

        binary_float = sign + mantissa + exponent_sign + binary_exponent

        # fmt: off
        hex_float = "".join(
            [
                hex(int(binary_float[i: i + 4], 2))[2:]
                for i in range(0, len(binary_float), 4)
            ]
        ).upper()
        # fmt: on

        embed.add_field(name="Decimal", value=number)
        embed.add_field(
            name="Binary",
            value=f"{binary[:-exponent]}.{binary[-exponent:].rstrip('0')}",
        )
        embed.add_field(
            name="Standard Form", value=f"{binary} x 2^{int(binary_exponent, 2)}"
        )
        embed.add_field(
            name="Sign of Mantissa  Mantissa  Sign of Exponent  Exponent",
            value=f"`{sign:^15s}{mantissa:^10s}{exponent_sign:^18s}{binary_exponent:^6s}`",
        )
        embed.add_field(name="Result", value=hex_float)
        return await ctx.send(embed=embed)

    @commands.command()
    async def translate(self, ctx, *, text):
        """Translates text to english."""
        headers = {
            "Referer": "http://translate.google.com/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/47.0.2526.106 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
        }
        url = "https://translate.google.com/_/TranslateWebserverUi/data/batchexecute"

        data = "f.req={}&".format(
            urllib.parse.quote(
                (
                    '[[["MkEWBc","[[\\"{}\\", \\"auto\\", \\"auto\\", True]'
                    ', [1]]",null,"generic"]]]'
                ).format(
                    text.strip()
                    .encode("unicode-escape")
                    .decode()
                    .encode("unicode-escape")
                    .decode()
                )
            )
        )

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=2)
        ) as session:
            response = await session.post(url, data=data, headers=headers)

        async for line in response.content:
            decoded_line = line.decode("utf-8")

            if "MkEWBc" in decoded_line:
                response = orjson.loads(orjson.loads(decoded_line)[0][2])[1][0][0][5]

                translate_text = ""
                for sentence in response:
                    translate_text += sentence[0].strip() + " "

                return await ctx.send(translate_text)

    @commands.command()
    async def weather(self, ctx, *, location="auckland"):
        """Gets the weather from google.

        location: str
            The name of the location to get the weather of.
        """
        url = f"https://www.google.co.nz/search?q=weather:{location}"

        async with ctx.typing():
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.67 Safari/537.36"
            }
            async with aiohttp.ClientSession(headers=headers) as session, session.get(
                url
            ) as page:
                soup = lxml.html.fromstring(await page.text())

            embed = discord.Embed(color=discord.Color.blurple())
            soup = soup.xpath('.//div[@class="nawv0d"]')

            if not soup:
                embed.description = f"```No weather for {location} found```"
                return await ctx.send(embed=embed)

            soup = soup[0]
            image = soup.xpath(".//img")[0].attrib["src"]
            location = soup.xpath('.//div[@id="wob_loc"]')[0].text_content()
            temp = soup.xpath('.//span[@id="wob_tm"]')[0].text_content()
            precipitation = soup.xpath('.//span[@id="wob_pp"]')[0].text_content()
            humidity = soup.xpath('.//span[@id="wob_hm"]')[0].text_content()
            wind = soup.xpath('.//span[@id="wob_ws"]')[0].text_content()
            state = soup.xpath('//span[@id="wob_dc"]')[0].text_content()
            current_time = soup.xpath('//div[@id="wob_dts"]')[0].text_content()

            embed.set_image(url=f"https:{image}")
            embed.title = location
            embed.description = state

            embed.add_field(name="Temp:", value=f"{temp}°C")
            embed.add_field(name="Precipitation:", value=precipitation)
            embed.add_field(name="Humidity:", value=humidity)
            embed.add_field(name="Wind:", value=wind)
            embed.add_field(name="Time:", value=current_time)

            await ctx.send(embed=embed)

    @commands.command(name="statuscodes")
    async def status_codes(self, ctx):
        """List of status codes for catstatus command."""
        embed = discord.Embed(color=discord.Color.blurple())
        embed.add_field(
            name="1xx informational response",
            value=(
                "```An informational response indicates that the request was received and understood.\n\n"
                "100 Continue\n"
                "101 Switching Protocols\n"
                "102 Processing\n"
                "103 Early Hints```"
            ),
            inline=False,
        )
        embed.add_field(
            name="2xx success",
            value=(
                "```Action requested by the client was received, understood, and accepted.\n\n"
                "200 OK\n"
                "201 Created\n"
                "202 Accepted\n"
                "203 Non-Authoritative Information\n"
                "204 No Content\n"
                "205 Reset Content\n"
                "206 Partial Content\n"
                "207 Multi-Status\n"
                "208 Already Reported```"
            ),
            inline=False,
        )
        embed.add_field(
            name="3xx redirection",
            value=(
                "```Client must take additional action to complete the request.\n\n"
                "300 Multiple Choices\n"
                "301 Moved Permanently\n"
                "302 Found (Previously 'Moved temporarily')\n"
                "303 See Other\n"
                "304 Not Modified\n"
                "305 Use Proxy\n"
                "306 Switch Proxy\n"
                "307 Temporary Redirect\n"
                "308 Permanent Redirect```"
            ),
            inline=False,
        )
        embed.add_field(
            name="4xx client errors",
            value=(
                "```Errors that seem to have been caused by the client.\n\n"
                "400 Bad Request\n"
                "401 Unauthorized\n"
                "402 Payment Required\n"
                "403 Forbidden\n"
                "404 Not Found\n"
                "405 Method Not Allowed\n"
                "406 Not Acceptable\n"
                "407 Proxy Authentication Required\n"
                "408 Request Timeout\n"
                "409 Conflict\n"
                "410 Gone\n"
                "411 Length Required\n"
                "412 Precondition Failed\n"
                "413 Payload Too Large\n"
                "414 URI Too Long\n"
                "415 Unsupported Media Type\n"
                "416 Range Not Satisfiable\n"
                "417 Expectation Failed\n"
                "418 I'm a teapot\n"
                "420 Enhance Your Calm\n"
                "421 Misdirected Request\n"
                "422 Unprocessable Entity\n"
                "423 Locked\n"
                "424 Failed Dependency\n"
                "425 Too Early\n"
                "426 Upgrade Required\n"
                "428 Precondition Required\n"
                "429 Too Many Requests\n"
                "431 Request Header Fields Too Large\n"
                "444 No Response\n"
                "450 Blocked by Windows Parental Controls\n"
                "451 Unavailable For Legal Reasons\n"
                "499 Client Closed Request```"
            ),
            inline=False,
        )
        embed.add_field(
            name="5xx server errors",
            value=(
                "```The server failed to fulfil a request.\n\n"
                "500 Internal Server Error\n"
                "501 Not Implemented\n"
                "502 Bad Gateway\n"
                "503 Service Unavailable\n"
                "504 Gateway Timeout\n"
                "505 HTTP Version Not Supported\n"
                "506 Variant Also Negotiates\n"
                "507 Insufficient Storage\n"
                "508 Loop Detected\n"
                "510 Not Extended\n"
                "511 Network Authentication Required```"
            ),
            inline=False,
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def languages(self, ctx):
        """Shows the languages that the run command can use."""
        languages = DB.db.get(b"languages")

        if not languages:
            return await ctx.send("No languages found")

        languages = orjson.loads(languages)
        msg = ""

        for count, language in enumerate(sorted(languages), start=1):
            if count % 4 == 0:
                msg += f"{language}\n"
            else:
                msg += f"{language:<13}"

        embed = discord.Embed(color=discord.Color.blurple(), description=f"```{msg}```")
        await ctx.send(embed=embed)

    @commands.command()
    async def emoji(self, ctx, *, name):
        """Does an emoji submission automatically.

        To use this command attach an image and put
        ".emoji [name]" as the comment

        name: str
            The emoji name. Must be at least 2 characters.
        """
        if len(name) < 2:
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description="```Name has to be at least 2 characters```",
                )
            )

        if discord.utils.get(ctx.guild.emojis, name=name):
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description="```An emoji already exists with that name```",
                )
            )

        if len(ctx.message.attachments) == 0:
            return await ctx.send(
                "```You need to attach the emoji image to the message```"
            )
        emojis = DB.db.get(b"emoji_submissions")

        if not emojis:
            emojis = {}
        else:
            emojis = orjson.loads(emojis)

        emojis[str(ctx.message.id)] = {"name": name, "users": []}

        DB.db.put(b"emoji_submissions", orjson.dumps(emojis))

    @commands.command()
    async def invites(self, ctx):
        """Shows the invites that users joined from."""
        invite_list = []
        for member, invite in DB.invites:
            if len(member) <= 18:
                member = self.bot.get_user(int(member))
                # I don't fetch the invite cause it takes 300ms per invite
                if member:
                    invite_list.append(f"{member.display_name}: {invite.decode()}\n")

        if not invite_list:
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description="```No stored invites```",
                )
            )

        pages = menus.MenuPages(
            source=InviteMenu(invite_list),
            clear_reactions_after=True,
            delete_message_after=True,
        )
        await pages.start(ctx)

    @commands.command()
    async def run(self, ctx, *, code=None):
        """Runs code.

        Examples:
        .run ```py
        print("Example")```

        .run py print("Example")

        .run py `print("Example")`

        .run py ```print("Example")```

        code: str
            The code to run.
        """
        if ctx.message.attachments:
            file = ctx.message.attachments[0]
            lang = file.filename.split(".")[-1]
            code = (await file.read()).decode()
        elif match := list(CODE_REGEX.finditer(code)):
            code, lang, alang = match[0].group("code", "lang", "alang")
            lang = lang or alang
        elif match := list(RAW_CODE_REGEX.finditer(code)):
            code, lang = match[0].group("code", "lang")

        if not lang:
            return await ctx.reply(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description="```You need to supply a language"
                    " either as an arg or inside a codeblock```",
                )
            )

        lang = lang.strip()

        if lang not in orjson.loads(DB.db.get(b"aliases")):
            return await ctx.reply(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description=f"```No support for language {lang}```",
                )
            )

        data = {
            "language": lang,
            "version": "*",
            "files": [{"content": code}],
            "args": "",
            "stdin": "",
            "log": 0,
        }

        async with ctx.typing(), aiohttp.ClientSession() as session, session.post(
            "https://emkc.org/api/v2/piston/execute", data=orjson.dumps(data)
        ) as response:
            data = await response.json()

        output = data["run"]["output"]

        if "compile" in data and data["compile"]["stderr"]:
            output = data["compile"]["stderr"] + "\n" + output

        if not output:
            return await ctx.reply(
                embed=discord.Embed(
                    color=discord.Color.blurple(), description="```No output```"
                )
            )

        if len(f"```\n{output}```") > 2000:
            return await ctx.reply(file=discord.File(StringIO(output), "output.txt"))

        await ctx.reply(f"```\n{output}```")

    @commands.command()
    async def time(self, ctx, *, command):
        """Runs a command whilst timing it.

        command: str
            The command to run including arguments.
        """
        ctx.content = f"{ctx.prefix}{command}"
        ctx = await self.bot.get_context(ctx, cls=type(ctx))
        embed = discord.Embed(color=discord.Color.blurple())

        if not ctx.command:
            embed.description = "```No command found```"
            return await ctx.send(embed=embed)

        start = time.time()
        await ctx.command.invoke(ctx)
        embed.description = f"`Time: {(time.time() - start) * 1000:.2f}ms`"
        await ctx.send(embed=embed)

    @commands.command()
    async def snipe(self, ctx):
        """Snipes the last deleted message."""
        data = DB.db.get(f"{ctx.guild.id}-snipe_message".encode())

        embed = discord.Embed(color=discord.Color.blurple())

        if not data:
            embed.description = "```No message to snipe```"
            return await ctx.send(embed=embed)

        message, author = orjson.loads(data)

        embed.title = f"{author} deleted:"
        embed.description = f"```{message}```"

        await ctx.send(embed=embed)

    @commands.command()
    async def editsnipe(self, ctx):
        """Snipes the last edited message."""
        data = DB.db.get(f"{ctx.guild.id}-editsnipe_message".encode())

        embed = discord.Embed(color=discord.Color.blurple())

        if not data:
            embed.description = "```No message to snipe```"
            return await ctx.send(embed=embed)

        original, edited, author = orjson.loads(data)

        embed.title = f"{author} edited:"
        embed.add_field(name="From:", value=f"```{original}```")
        embed.add_field(name="To:", value=f"```{edited}```")

        await ctx.send(embed=embed)

    @staticmethod
    async def wait_for_deletion(message: discord.Message, ctx):
        def check(reaction: discord.Reaction, user: discord.User) -> bool:
            return ctx.author.id == user.id and reaction.message.id == message.id

        await message.add_reaction("❎")
        reaction, user = await ctx.bot.wait_for(
            "reaction_add", timeout=60.0, check=check
        )
        await message.delete()

    async def cache_check(self, search):
        """Checks the cache for an search if found randomly return a result.

        search: str
        """
        cache = orjson.loads(DB.db.get(b"cache"))

        if search in cache:
            if len(cache[search]) == 0:
                return {}

            url, title = random.choice(list(cache[search].items()))

            cache[search].pop(url)

            DB.db.put(b"cache", orjson.dumps(cache))

            return url, title
        return cache

    @commands.command()
    async def google(self, ctx, *, search):
        """Searchs and finds a random image from google.

        search: str
            The term to search for.
        """
        embed = discord.Embed(color=discord.Color.blurple())

        cache_search = f"google-{search.lower()}"
        cache = await self.cache_check(cache_search)

        if isinstance(cache, tuple):
            url, title = cache
            embed.set_image(url=url)
            embed.title = title

            message = await ctx.send(embed=embed)
            return await self.wait_for_deletion(message, ctx)

        async with ctx.typing():
            url = f"https://www.google.co.nz/search?q={search}&source=lnms&tbm=isch&safe=active"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.67 Safari/537.36"
            }
            async with aiohttp.ClientSession(headers=headers) as session, session.get(
                url
            ) as page:
                soup = lxml.html.fromstring(await page.text())

            images = {}
            for a in soup.xpath('.//img[@class="rg_i Q4LuWd"]'):
                try:
                    images[a.attrib["data-src"]] = a.attrib["alt"]
                except KeyError:
                    pass

            if images == {}:
                embed.description = "```No images found```"
                return await ctx.send(embed=embed)

            url, title = random.choice(list(images.items()))
            images.pop(url)

            embed.set_image(url=url)
            embed.title = title

            message = await ctx.send(embed=embed)

            cache[cache_search] = images
            self.loop.call_later(300, DB.delete_cache, cache_search, cache)
            DB.db.put(b"cache", orjson.dumps(cache))

        await self.wait_for_deletion(message, ctx)

    @commands.command(aliases=["img"])
    async def image(self, ctx, *, search):
        """Searchs and finds a random image from bing.

        search: str
            The term to search for.
        """
        embed = discord.Embed(color=discord.Color.blurple())

        cache_search = f"image-{search}"
        cache = await self.cache_check(cache_search)

        if isinstance(cache, tuple):
            url, title = cache
            embed.set_image(url=url)
            embed.title = title

            message = await ctx.send(embed=embed)
            return await self.wait_for_deletion(message, ctx)

        async with ctx.typing():
            url = f"https://www.bing.com/images/search?q={search}&first=1"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.67 Safari/537.36"
            }
            async with aiohttp.ClientSession(headers=headers) as session, session.get(
                url
            ) as page:
                soup = lxml.html.fromstring(await page.text())

            images = {}
            for a in soup.xpath('.//a[@class="iusc"]'):
                data = orjson.loads(a.attrib["m"])
                images[data["turl"]] = data["desc"]

            if images == {}:
                embed.description = "```No images found```"
                return await ctx.send(embed=embed)

            url, title = random.choice(list(images.items()))
            images.pop(url)

            embed.set_image(url=url)
            embed.title = title

            message = await ctx.send(embed=embed)

            cache[cache_search] = images
            self.loop.call_later(300, DB.delete_cache, cache_search, cache)
            DB.db.put(b"cache", orjson.dumps(cache))

        await self.wait_for_deletion(message, ctx)

    @staticmethod
    def bin_float(number: float):
        exponent = 0
        shifted_num = number

        while shifted_num != int(shifted_num):
            shifted_num *= 2
            exponent += 1

        if not exponent:
            return bin(number).removeprefix("0b")

        binary = f"{int(shifted_num):0{exponent + 1}b}"
        return f"{binary[:-exponent]}.{binary[-exponent:].rstrip('0')}"

    @staticmethod
    def hex_float(number: float):
        exponent = 0
        shifted_num = number

        while shifted_num != int(shifted_num):
            shifted_num *= 16
            exponent += 1

        if not exponent:
            return hex(number).removeprefix("0x")

        hexadecimal = f"{int(shifted_num):0{exponent + 1}x}"
        return f"{hexadecimal[:-exponent]}.{hexadecimal[-exponent:]}"

    @staticmethod
    def oct_float(number: float):
        exponent = 0
        shifted_num = number

        while shifted_num != int(shifted_num):
            shifted_num *= 8
            exponent += 1

        if not exponent:
            return oct(number).removeprefix("0o")

        octal = f"{int(shifted_num):0{exponent + 1}o}"
        return f"{octal[:-exponent]}.{octal[-exponent:]}"

    def safe_eval(self, node):
        if isinstance(node, ast.Num):
            return node.n

        if isinstance(node, ast.BinOp):
            left = self.safe_eval(node.left)
            right = self.safe_eval(node.right)
            if isinstance(node.op, ast.Pow) and len(str(left)) * right > 1000:
                raise ValueError("Too large to calculate")
            return OPERATIONS[node.op.__class__](left, right)

        raise ValueError("Calculation failed")

    @commands.command()
    async def calc(self, ctx, num_base, *, args=""):
        """Does math.

        num_base: str
            The base you want to calculate in.
            Can be hex, oct, bin and for decimal ignore this argument
        args: str
            A str of arguments to calculate.
        """
        num_bases = {
            "h": (16, self.hex_float),
            "o": (8, self.oct_float),
            "b": (2, self.bin_float),
        }
        base, method = num_bases.get(num_base.lower()[:1], ("unknown", int))

        if base == "unknown":
            base = 10
            args = f"{num_base} {args}"

        if base == 8:
            args = args.replace("0o", "")
        elif base == 2:
            args = args.replace("0b", "")

        regex = r"(?:0[xX])?[0-9a-fA-F]+" if base == 16 else r"\d+"
        numbers = [int(num, base) for num in re.findall(regex, args)]

        expr = re.sub(regex, "%s", args) % tuple(numbers)
        result = self.safe_eval(ast.parse(expr, "<string>", "eval").body)

        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                description=f"```ml\n{expr}\n\n{method(result)}\n\nDecimal: {result}```",
            )
        )

    @commands.command(aliases=["ch", "cht"])
    async def cheatsheet(self, ctx, *search):
        """https://cheat.sh/python/ gets a cheatsheet.

        search: tuple
            The search terms.
        """
        search = "+".join(search)

        url = f"https://cheat.sh/python/{search}"
        headers = {"User-Agent": "curl/7.68.0"}

        escape = str.maketrans({"`": "\\`"})
        ansi = re.compile(r"\x1b\[.*?m")

        async with ctx.typing(), aiohttp.ClientSession(
            headers=headers
        ) as session, session.get(url) as page:
            result = ansi.sub("", await page.text()).translate(escape)

        embed = discord.Embed(
            title=f"https://cheat.sh/python/{search}", color=discord.Color.blurple()
        )
        embed.description = f"```py\n{result}```"

        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    """Starts useful cog."""
    bot.add_cog(useful(bot))
