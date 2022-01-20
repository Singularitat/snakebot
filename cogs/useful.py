import difflib
import io
import math
import random
import re
import secrets
import time
import urllib
from datetime import datetime
from zlib import compress

import discord
import lxml.html
import orjson
from discord.ext import commands, menus

from cogs.utils.calculation import bin_float, hex_float, oct_float, safe_eval

STATUS_CODES = {
    "1": {
        "title": "1xx informational response",
        "message": "An informational response indicates that the request was received and understood.",
        "100": "Continue",
        "101": "Switching Protocols",
        "102": "Processing",
        "103": "Early Hints",
    },
    "2": {
        "title": "2xx success",
        "message": "Action requested by the client was received, understood, and accepted.",
        "200": "OK",
        "201": "Created",
        "202": "Accepted",
        "203": "Non-Authoritative Information",
        "204": "No Content",
        "205": "Reset Content",
        "206": "Partial Content",
        "207": "Multi-Status",
        "208": "Already Reported",
        # Apache Web Server
        "218": "This is fine",
        "226": "IM Used",
    },
    "3": {
        "title": "3xx redirection",
        "message": "Client must take additional action to complete the request.",
        "300": "Multiple Choices",
        "301": "Moved Permanently",
        "302": "Found (Previously 'Moved temporarily')",
        "303": "See Other",
        "304": "Not Modified",
        "305": "Use Proxy",
        "306": "Switch Proxy",
        "307": "Temporary Redirect",
        "308": "Permanent Redirect",
    },
    "4": {
        "title": "4xx client errors",
        "message": "Errors that seem to have been caused by the client.",
        "400": "Bad Request",
        "401": "Unauthorized",
        "402": "Payment Required",
        "403": "Forbidden",
        "404": "Not Found",
        "405": "Method Not Allowed",
        "406": "Not Acceptable",
        "407": "Proxy Authentication Required",
        "408": "Request Timeout",
        "409": "Conflict",
        "410": "Gone",
        "411": "Length Required",
        "412": "Precondition Failed",
        "413": "Payload Too Large",
        "414": "URI Too Long",
        "415": "Unsupported Media Type",
        "416": "Range Not Satisfiable",
        "417": "Expectation Failed",
        "418": "Im A Teapot",
        # Laravel
        "419": "Page Expired",
        # Twitter
        "420": "Enhance Your Calm",
        # End
        "421": "Misdirected Request",
        "422": "Unprocessable Entity",
        "423": "Locked",
        "424": "Failed Dependency",
        "425": "Too Early",
        "426": "Upgrade Required",
        "428": "Precondition Required",
        "429": "Too Many Requests",
        # Shopify
        "430": "Request Header Fields Too Large",
        "431": "Request Header Fields Too Large",
        # nginx
        "444": "No Response",
        # Windows
        "450": "Blocked By Windows Parental Controls",
        "451": "Unavailable For Legal Reasons",
        # AWS
        "561": "Unauthorized",
        # nginx
        "494": "Request header too large",
        "495": "SSL Certificate Error",
        "496": "SSL Certificate Required",
        "497": "HTTP Request Sent to HTTPS Port",
        "499": "Client Closed Request",
    },
    "5": {
        "title": "5xx server errors",
        "message": "The server failed to fulfil a request.",
        "500": "Internal Server Error",
        "501": "Not Implemented",
        "502": "Bad Gateway",
        "503": "Service Unavailable",
        "504": "Gateway Timeout",
        "505": "HTTP Version Not Supported",
        "506": "Variant Also Negotiates",
        "507": "Insufficient Storage",
        "508": "Loop Detected",
        # Apache Web Server
        "509": "Bandwidth Limit Exceeded",
        "510": "Not Extended",
        "511": "Network Authentication Required",
        # Cloudflare
        "520": "Web Server Returned an Unknown Error",
        "521": "Web Server is Down",
        "522": "Connection Timed Out",
        "523": "Origin is Unreachable",
        "524": "A Timeout Occurred",
        "525": "SSL Handshake Failed",
        "526": "Invalid SSL Certificate",
        "527": "Railgun Error",
        # Qualys
        "529": "Site is overloaded",
        # Pantheon
        "530": "Site is frozen",
        # End
        "598": "(Informal convention) Network read timeout error",
        "599": "Network Connect Timeout Error",
    },
}

WWO_CODES = {
    "113": "☀️",
    "116": "⛅️",
    "119": "☁️",
    "122": "☁️",
    "143": "🌫",
    "176": "🌦",
    "179": "🌧",
    "182": "🌧",
    "185": "🌧",
    "200": "⛈",
    "227": "🌨",
    "230": "❄️",
    "248": "🌫",
    "260": "🌫",
    "263": "🌦",
    "266": "🌦",
    "281": "🌧",
    "284": "🌧",
    "293": "🌦",
    "296": "🌦",
    "299": "🌧",
    "302": "🌧",
    "305": "🌧",
    "308": "🌧",
    "311": "🌧",
    "314": "🌧",
    "317": "🌧",
    "320": "🌨",
    "323": "🌨",
    "326": "🌨",
    "329": "❄️",
    "332": "❄️",
    "335": "❄️",
    "338": "❄️",
    "350": "🌧",
    "353": "🌦",
    "356": "🌧",
    "359": "🌧",
    "362": "🌧",
    "365": "🌧",
    "368": "🌨",
    "371": "❄️",
    "374": "🌧",
    "377": "🌧",
    "386": "⛈",
    "389": "🌩",
    "392": "⛈",
    "395": "❄️",
}


TIO_ALIASES = {
    "asm": "assembly-nasm",
    "c": "c-gcc",
    "cpp": "cpp-gcc",
    "c++": "cpp-gcc",
    "cs": "cs-core",
    "java": "java-openjdk",
    "js": "javascript-node",
    "javascript": "javascript-node",
    "ts": "typescript",
    "py": "python3",
    "python": "python3",
    "prolog": "prolog-ciao",
    "swift": "swift4",
}

CODE_REGEX = re.compile(
    r"(?:(?P<lang>^[a-z0-9]+[\ \n])?)(?P<delim>(?P<block>```)|``?)(?(block)"
    r"(?:(?P<alang>[a-z0-9]+)\n)?)(?:[ \t]*\n)*(?P<code>.*?)\s*(?P=delim)",
    re.DOTALL | re.IGNORECASE,
)

RAW_CODE_REGEX = re.compile(
    r"(?:(?P<lang>^[a-z0-9]+[\ \n])?)(?P<code>(?s).*)", re.DOTALL | re.IGNORECASE
)

ANSI = re.compile(r"\x1b\[.*?m")


class InviteMenu(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=20)

    async def format_page(self, menu, entries):
        return discord.Embed(
            color=discord.Color.blurple(), description=f"```{''.join(entries)}```"
        )


class LanguageMenu(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=60)

    async def format_page(self, menu, entries):
        msg = ""

        for count, language in enumerate(sorted(entries), start=1):
            if count % 2 == 0:
                msg += f"{language}\n"
            else:
                msg += f"{language:<26}"

        return discord.Embed(color=discord.Color.blurple(), description=f"```{msg}```")


class useful(commands.Cog):
    """Actually useful commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.DB = bot.DB
        self.loop = bot.loop

    @commands.command(aliases=["vaccines"])
    async def vaccine(self, ctx):
        """Gets current NZ vaccine data from the health.govt.nz website."""
        url = (
            "https://www.health.govt.nz/our-work/diseases-and-conditions/covid-19"
            "-novel-coronavirus/covid-19-data-and-statistics/covid-19-vaccine-data"
        )
        async with ctx.typing(), self.bot.client_session.get(url) as resp:
            soup = lxml.html.fromstring(await resp.text())

        data = soup.xpath(".//td")[:16]

        description = (
            "```prolog\nEligible Population Vaccinated %:\n  First Dose: "
            f"{data[2].text}\n  Second Dose: {data[8].text}\n\nCumulative Total:\n  "
            f"First Dose: {data[4].text}\n  Second Dose: {data[7].text}\n  Third Primary:"
            f" {data[13].text}\n  Boosters: {data[15].text}\n\nVaccinations Yesterday:\n"
            f"  First Dose: {data[0].text}\n  Second Dose: {data[6].text}\n"
            f"  Third Primary: {data[12].text}\n  Boosters: {data[14].text}\n```"
        )

        await ctx.send(
            embed=discord.Embed(color=discord.Color.blurple(), description=description)
            .set_footer(text="Vaccine data from health.govt.nz")
            .set_image(
                url="https://www.health.govt.nz/sites/default/files/images/our-work/"
                "diseases-conditions/covid19/vaccine-data/uptake_summary_40_0.png"
            )
        )

    @commands.command()
    async def holidays(self, ctx, country_code="NZ"):
        """Gets the holidays in a country.

        country_code: str
        """
        url = (
            "https://date.nager.at/api/v3/PublicHolidays"
            f"/{discord.utils.utcnow().year}/NZ"
        )

        with ctx.typing():
            data = await self.bot.get_json(url)

        embed = discord.Embed(color=discord.Color.blurple())

        for holiday in data:
            epoch = time.mktime(time.strptime(holiday["date"], "%Y-%m-%d"))
            embed.add_field(name=holiday["name"], value=f"<t:{epoch:.0f}:R>")

        await ctx.send(embed=embed)

    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.cooldown(10, 60, commands.BucketType.default)
    @commands.command(aliases=["ss"])
    async def screenshot(self, ctx, website: str):
        """Takes a screenshot of a website and sends the image.

        url: str
        """
        if not website.startswith("http"):
            website = "https://" + website

        url = "https://onlinescreenshot.com/"

        headers = {
            "authority": "onlinescreenshot.com",
            "accept": "*/*",
            "x-requested-with": "XMLHttpRequest",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "origin": "https://onlinescreenshot.com",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": "https://onlinescreenshot.com/",
            "accept-language": "en-US,en;q=0.9",
        }

        data = {
            "url": website,
            "cookies": 0,
            "proxy": 0,
            "delay": 1,
            "captchaToken": False,
            "device": 1,
            "platform": 1,
            "browser": 1,
            "fFormat": 1,
            "width": 1920,
            "height": 1080,
            "uid": "NaN",
        }

        async with ctx.typing(), self.bot.client_session.post(
            url, headers=headers, data=data, timeout=40
        ) as resp:
            data = await resp.json()

        if data["imgUrl"]:
            message = await ctx.send(data["imgUrl"])
            await self.wait_for_deletion(ctx.author, message)
        elif data["error"]:
            await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description="```Another request is being processed```",
                )
            )

    @commands.command()
    async def tempmail(self, ctx):
        """Creates a random tempmail account for you."""
        url = "https://api.mail.tm/accounts"
        password = secrets.token_urlsafe()
        domain = self.DB.main.get(b"tempdomain").decode()
        account = {
            "address": f"{secrets.token_urlsafe(16)}@{domain}",
            "password": password,
        }

        async with self.bot.client_session.post(url, json=account) as resp:
            data = await resp.json()

        embed = discord.Embed(
            color=discord.Color.blurple(),
            title="Temp Mail Account Created",
        )
        embed.add_field(
            name="Email Address", value=f"```yaml\n{data['address']}```", inline=False
        )
        embed.add_field(name="Password", value=f"```yaml\n{password}```", inline=False)
        embed.set_footer(text="Account is deleted when you make a new one")

        await ctx.author.send(embed=embed)

        async with self.bot.client_session.post(
            "https://api.mail.tm/token",
            json={"address": data["address"], "password": password},
        ) as resp:
            token = (await resp.json())["token"]
            account["token"] = token

        key = f"tempmail-{ctx.author.id}".encode()
        old_account = self.DB.main.get(key)
        if old_account:
            old_account = orjson.loads(old_account)

            await self.bot.client_session.delete(
                f"https://api.mail.tm/accounts/{old_account['id']}",
                data={"id": old_account["id"]},
                headers={"Authorization": f"Bearer {old_account['token']}"},
            )

        account["id"] = data["id"]
        self.DB.main.put(key, orjson.dumps(account))

    @commands.command()
    async def tempmessages(self, ctx):
        """Gets the messages on your tempmail account if you have one."""
        url = "https://api.mail.tm/messages"
        key = f"tempmail-{ctx.author.id}".encode()
        embed = discord.Embed(color=discord.Color.blurple())

        account = self.DB.main.get(key)
        if not account:
            embed.description = (
                "You don't have a tempmail account do `.tempmail` to create one"
            )
            return await ctx.send(embed=embed)

        account = orjson.loads(account)

        async with self.bot.client_session.get(
            url, headers={"Authorization": f"Bearer {account['token']}"}
        ) as resp:
            messages = await resp.json()

        if not messages["hydra:totalItems"]:
            embed.description = "```You haven't received any messages```"
            return await ctx.send(embed=embed)

        for message in messages["hydra:member"]:
            embed.add_field(
                name=f"{message['from']['name']} [{message['from']['address']}]",
                value=f"```Id: {message['id']}\nSubject: {message['subject']}\n\n{message['intro']}```",
                inline=False,
            )

        embed.set_footer(text="Use .tempmessage [ID] to get the full message")
        await ctx.send(embed=embed)

    @commands.command()
    async def tempmessage(self, ctx, message_id):
        """Gets a tempmail message by its id.

        id: str
        """
        url = f"https://api.mail.tm/messages/{message_id}"
        key = f"tempmail-{ctx.author.id}".encode()
        embed = discord.Embed(color=discord.Color.blurple())

        account = self.DB.main.get(key)
        if not account:
            embed.description = (
                "You don't have a tempmail account do `.tempmail` to create one"
            )
            return await ctx.send(embed=embed)

        account = orjson.loads(account)

        async with self.bot.client_session.get(
            url, headers={"Authorization": f"Bearer {account['token']}"}
        ) as resp:
            message = await resp.json()

        await ctx.send(file=discord.File(io.StringIO(message["text"]), "email.txt"))

    @commands.command()
    async def text(self, ctx):
        """Extracts the text out of an image that you attach."""
        embed = discord.Embed(color=discord.Color.blurple())

        if not ctx.message.attachments:
            embed.description = "```You need to attach an image```"
            return await ctx.send(embed=embed)

        url = "https://api8.ocr.space/parse/image"

        data = {
            "url": ctx.message.attachments[0].url,
            "language": "eng",
            "isOverlayRequired": "true",
            "apikey": "5a64d478-9c89-43d8-88e3-c65de9999580",
            "OCREngine": 2,
        }

        async with self.bot.client_session.post(url, data=data) as response:
            results = (await response.json())["ParsedResults"][0]

        result = results["ParsedText"].replace("`", "`\u200b")

        if not result:
            embed.description = "```Failed to process image```"
            return await ctx.send(embed=embed)

        embed.description = f"```{result}```"
        await ctx.send(embed=embed)

    @commands.command()
    async def format(self, ctx, *, code=None):
        """Formats python code using the black formatter.

        code: str
        """
        if not code and ctx.message.attachments:
            file = ctx.message.attachments[0]
            if file.filename.split(".")[-1] != "py":
                return
            code = (await file.read()).decode()

        url = "https://1rctyledh3.execute-api.us-east-1.amazonaws.com/dev"
        data = {
            "options": {
                "fast": False,
                "line_length": 88,
                "py36": False,
                "pyi": False,
                "skip_string_normalization": False,
            },
            "source": re.sub(r"```\w+\n|```", "", code),
        }

        async with self.bot.client_session.post(url, json=data) as response:
            formatted = (await response.json())["formatted_code"]

        if len(formatted) > 1991:
            return await ctx.reply(
                file=discord.File(io.StringIO(formatted), "output.py")
            )

        formatted = formatted.replace("`", "`\u200b")
        await ctx.reply(f"```py\n{formatted}```")

    @commands.command()
    async def tiolanguages(self, ctx):
        """Shows all the languages that tio.run can handle."""
        languages = orjson.loads(self.DB.main.get(b"tiolanguages"))

        pages = menus.MenuPages(
            source=LanguageMenu(languages),
            clear_reactions_after=True,
            delete_message_after=True,
        )
        await pages.start(ctx)

    @commands.command()
    async def hello(self, ctx, language):
        """Gets the code for hello world in a language.

        language: str
        """
        language = TIO_ALIASES.get(language, language)
        data = orjson.loads(self.DB.main.get(b"helloworlds"))
        code = data.get(language)

        embed = discord.Embed(color=discord.Color.blurple())

        if not code:
            embed.description = "```Language not found.```"
            return await ctx.send(embed=embed)

        embed.description = f"```{language}\n{code}```"
        await ctx.send(embed=embed)

    @commands.command()
    async def tio(self, ctx, *, code):
        """Uses tio.run to run code.

        Examples:
        .tio `\u200b`\u200b`\u200bpy
        print("Example")`\u200b`\u200b`\u200b

        .tio py print("Example")

        .tio py `\u200bprint("Example")`\u200b

        .tio py `\u200b`\u200b`\u200bprint("Example")`\u200b`\u200b`\u200b

        code: str
            The code to run.
        """
        if ctx.message.attachments:
            file = ctx.message.attachments[0]
            lang = file.filename.split(".")[-1]
            code = (await file.read()).decode()
        elif match := [*CODE_REGEX.finditer(code)]:
            code, lang, alang = match[0].group("code", "lang", "alang")
            lang = lang or alang
        elif match := [*RAW_CODE_REGEX.finditer(code)]:
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
        lang = TIO_ALIASES.get(lang, lang)  # tio doesn't have default aliases

        if lang not in orjson.loads(self.DB.main.get(b"tiolanguages")):
            return await ctx.reply(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description=f"```No support for language {lang}```",
                )
            )

        url = "https://tio.run/cgi-bin/run/api/"

        data = compress(
            f"Vlang\x001\x00{lang}\x00F.code.tio\x00{len(code)}\x00{code}\x00R".encode(),
            9,
        )[2:-4]

        async with ctx.typing(), self.bot.client_session.post(
            url, data=data
        ) as response:
            response = (await response.read()).decode("utf-8")
            response = response.replace(response[:16], "")

        await ctx.reply(f"```{lang}\n{response}```")

    @commands.command()
    async def news(self, ctx):
        """Gets top New Zealand stories from google."""
        async with ctx.typing():
            url = "https://news.google.com/topstories?hl=en-NZ&gl=NZ&ceid=NZ:en"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.67 Safari/537.36"
            }

            async with self.bot.client_session.get(url, headers=headers) as page:
                soup = lxml.html.fromstring(await page.text())

        embed = discord.Embed(color=discord.Color.blurple())

        for article in soup.xpath(
            './/article[@class=" MQsxIb xTewfe R7GTQ keNKEd j7vNaf Cc0Z5d EjqUne"]'
        ):
            a_tag = article.xpath('.//a[@class="DY5T1d RZIKme"]')[0]
            embed.add_field(
                name=a_tag.text,
                value=f"[Link](https://news.google.com{a_tag.attrib['href'][1:]})",
            )

        await ctx.send(embed=embed)

    @commands.command()
    async def temp(self, ctx, *, location="auckland+cbd"):
        """Gets a temperature/rain graph of a location.

        location: str
        """
        await ctx.send(f"http://v2d.wttr.in/{location.replace(' ', '+')}.png")

    @commands.group(name="float", invoke_without_command=True)
    async def _float(self, ctx, number: float):
        """Converts a float to the half-precision floating-point format.

        number: float
        """
        decimal = abs(number)

        sign = 1 - (number >= 0)
        mantissa = math.floor(
            decimal * 2 ** math.floor(math.log2(0b111111111 / decimal))
        )
        exponent = math.floor(math.log2(decimal) + 1)
        exponent_sign, exponent = 1 - (exponent >= 0), abs(exponent)

        binary = bin_float(number)
        binary = binary[: max(binary.find("1") + 1, 12)]

        embed = discord.Embed(color=discord.Color.blurple())
        embed.add_field(name="Decimal", value=number)
        embed.add_field(
            name="Binary",
            value=binary,
        )
        embed.add_field(name="\u200b", value="\u200b")
        embed.add_field(name="Standard Form", value=f"{binary} x 2^{exponent}")
        embed.add_field(
            name="Result",
            value=f"{(sign << 15) | (mantissa << 6) | (exponent_sign << 5) | exponent:X}",
        )
        embed.add_field(name="\u200b", value="\u200b")

        sign, mantissa, exponent_sign, exponent = (
            f"{sign:b}",
            f"{mantissa:0>9b}",
            f"{exponent_sign:b}",
            f"{exponent:0>5b}",
        )

        embed.add_field(
            name="Mantissa Sign   Mantissa   Exponent Sign   Exponent",
            value=f"`{sign:^13s}{mantissa:^11s}{exponent_sign:^13s} {exponent:^9s}`",
        )

        return await ctx.send(embed=embed)

    @_float.command(aliases=["d"])
    async def decode(self, ctx, number):
        """Decodes a float from the half-precision floating-point format.

        number: str
        """
        number = int(number, 16)

        sign = (number & (2 ** 1 - 1) << 15) >> 15
        mantissa = (number & (2 ** 9 - 1) << 6) >> 6
        exponent_sign = (number & (2 ** 1 - 1) << 5) >> 5
        exponent = number & (2 ** 5 - 1)
        float_value = (
            (sign * -2 + 1) * mantissa * 2 ** (-9 + (exponent_sign * -2 + 1) * exponent)
        )
        sign, mantissa, exponent_sign, exponent = (
            f"{sign:b}",
            f"{mantissa:0>9b}",
            f"{exponent_sign:b}",
            f"{exponent:0>5b}",
        )
        embed = discord.Embed(color=discord.Color.blurple())
        embed.add_field(name="Decimal", value=float_value)
        embed.add_field(name="Binary", value=bin_float(float_value))
        embed.add_field(name="\u200b", value="\u200b")
        embed.add_field(
            name="Mantissa Sign   Mantissa   Exponent Sign   Exponent",
            value=f"`{sign:^13s}{mantissa:^11s}{exponent_sign:^13s} {exponent:^9s}`",
        )
        return await ctx.send(embed=embed)

    @commands.command()
    async def translate(self, ctx, *, text=None):
        """Translates text to english."""
        if not text:
            reference = ctx.message.reference
            if not reference or not reference.resolved:
                return await ctx.send(
                    "Either reply to a message or use the text argument"
                )
            text = reference.resolved.content
        if not text:
            return await ctx.send("You need to reply to a message with text")

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

        response = await self.bot.client_session.post(url, data=data, headers=headers)

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
        """Gets the weather from wttr.in defaults location to auckland.

        location: str
            The name of the location to get the weather of.
        """
        url = f"http://wttr.in/{location}?format=j1"
        embed = discord.Embed(color=discord.Color.blurple())

        async with ctx.typing():
            data = await self.bot.get_json(url)

            current = data["current_condition"][0]
            location = data["nearest_area"][0]
            emoji = WWO_CODES[current["weatherCode"]]

            embed.description = f"{current['weatherDesc'][0]['value']}"
            embed.title = (
                f"{emoji} {location['areaName'][0]['value']}"
                f", {location['country'][0]['value']}"
            )

            embed.add_field(
                name="Temperature",
                value=f"{current['temp_C']}°C / {current['temp_F']}°F",
            )
            embed.add_field(name="Humidity", value=f"{current['humidity']}%")
            embed.add_field(
                name="Wind Speed",
                value=f"{current['windspeedKmph']}kmph {current['winddir16Point']}",
            )
            for day in data["weather"]:
                hourly = day["hourly"]
                noon, night = hourly[4], hourly[7]

                embed.add_field(
                    name=day["date"],
                    value=f"**Max Temp:** {day['maxtempC']}°C / {day['maxtempF']}°F\n"
                    f"**Noon:** {WWO_CODES[noon['weatherCode']]} {noon['weatherDesc'][0]['value']}\n"
                    f"**Night:** {WWO_CODES[night['weatherCode']]} {night['weatherDesc'][0]['value']}",
                )

            embed.timestamp = datetime.strptime(
                current["localObsDateTime"], "%Y-%m-%d %I:%M %p"
            )
            embed.set_footer(text="Last Updated")

        await ctx.send(embed=embed)

    @commands.command(aliases=["statuscode"])
    async def statuscodes(self, ctx, *, code=None):
        """List of status codes for mainly for catstatus command."""
        embed = discord.Embed(color=discord.Color.blurple())

        if not code:
            for codes in STATUS_CODES.values():
                message = ""

                for code, tag in codes.items():
                    if not code.isdigit():
                        continue
                    message += f"\n{code} {tag}"

                embed.add_field(
                    name=codes["title"],
                    value=f"{codes['message']}\n```prolog\n{message}```",
                    inline=False,
                )
            return await ctx.send(embed=embed)

        group = code[0]
        info = STATUS_CODES.get(group)
        if not info:
            statuses = {}
            for data in STATUS_CODES.values():
                for scode, tag in data.items():
                    if scode.isdigit():
                        statuses[tag] = scode
            match = difflib.get_close_matches(
                code,
                [*statuses],
                n=1,
                cutoff=0.0,
            )
            code = statuses[match[0]]
            info = STATUS_CODES.get(code[0])

            if not info:
                embed.description = f"```No status code group for {group}xx```"
                return await ctx.send(embed=embed)

        if code not in info:
            embed.description = (
                f"```No {code} status code found in the {group}xx group```"
            )
            return await ctx.send(embed=embed)
        embed.title = info["title"]
        embed.description = f"{info['message']}\n```prolog\n{code} {info[code]}```"
        await ctx.send(embed=embed)

    @commands.command()
    async def languages(self, ctx):
        """Shows the languages that the run command can use."""
        languages = orjson.loads(self.DB.main.get(b"languages"))

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

        if not ctx.message.attachments:
            return await ctx.send(
                "```You need to attach the emoji image to the message```"
            )
        emojis = self.DB.main.get(b"emoji_submissions")

        if not emojis:
            emojis = {}
        else:
            emojis = orjson.loads(emojis)

        emojis[str(ctx.message.id)] = {"name": name, "users": []}

        self.DB.main.put(b"emoji_submissions", orjson.dumps(emojis))

    @commands.command()
    async def invites(self, ctx):
        """Shows the invites that users joined from."""
        invite_list = []
        for member, invite in self.DB.invites:
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
        .run `\u200b`\u200b`\u200bpy
        print("Example")`\u200b`\u200b`\u200b

        .run py print("Example")

        .run py `\u200bprint("Example")`\u200b

        .run py `\u200b`\u200b`\u200bprint("Example")`\u200b`\u200b`\u200b

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

        if lang not in orjson.loads(self.DB.main.get(b"aliases")):
            lang = lang.replace("`", "`\u200b")
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
        }

        async with ctx.typing(), self.bot.client_session.post(
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

        output = output.replace("`", "`\u200b")
        if len(output) + len(lang) > 1993:
            return await ctx.reply(file=discord.File(io.StringIO(output), "output.txt"))

        await ctx.reply(f"```{lang}\n{output}```")

    @commands.command()
    async def time(self, ctx, *, command):
        """Runs a command whilst timing it.

        command: str
            The command to run including arguments.
        """
        ctx.message.content = f"{ctx.prefix}{command}"
        new_ctx = await self.bot.get_context(ctx.message, cls=type(ctx))
        embed = discord.Embed(color=discord.Color.blurple())

        if not new_ctx.command:
            embed.description = "```Command not found```"
            return await ctx.send(embed=embed)

        start = time.perf_counter()
        await new_ctx.command.invoke(new_ctx)
        end = time.perf_counter()

        embed.description = f"`Time: {(end - start) * 1000:.2f}ms`"
        await ctx.send(embed=embed)

    @commands.command()
    async def snipe(self, ctx):
        """Snipes the last deleted message."""
        data = self.DB.main.get(f"{ctx.guild.id}-snipe_message".encode())

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
        data = self.DB.main.get(f"{ctx.guild.id}-editsnipe_message".encode())

        embed = discord.Embed(color=discord.Color.blurple())

        if not data:
            embed.description = "```No message to snipe```"
            return await ctx.send(embed=embed)

        original, edited, author = orjson.loads(data)

        embed.title = f"{author} edited:"
        embed.add_field(name="From:", value=f"```{original}```")
        embed.add_field(name="To:", value=f"```{edited}```")

        await ctx.send(embed=embed)

    async def wait_for_deletion(self, author: discord.Member, message: discord.Message):
        def check(reaction: discord.Reaction, user: discord.User) -> bool:
            return (
                author == user and reaction.message == message and reaction.emoji == "❎"
            )

        await message.add_reaction("❎")
        reaction, user = await self.bot.wait_for(
            "reaction_add", timeout=60.0, check=check
        )
        await message.delete()

    async def cache_check(self, search):
        """Checks the cache for an search if found randomly return a result.

        search: str
        """
        cache = orjson.loads(self.DB.main.get(b"cache"))

        if search in cache:
            if not cache[search]:
                return {}

            url, title = random.choice(list(cache[search].items()))

            cache[search].pop(url)

            self.DB.main.put(b"cache", orjson.dumps(cache))

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
            return await self.wait_for_deletion(ctx.author, message)

        async with ctx.typing():
            url = f"https://www.google.com/search?q={search}&source=lnms&tbm=isch&safe=active"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.67 Safari/537.36"
            }
            async with self.bot.client_session.get(url, headers=headers) as page:
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
            self.loop.call_later(300, self.DB.delete_cache, cache_search, cache)
            self.DB.main.put(b"cache", orjson.dumps(cache))

        await self.wait_for_deletion(ctx.author, message)

    @commands.command(aliases=["img"])
    async def image(self, ctx, *, search):
        """Searchs and finds a random image from yandex.

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
            return await self.wait_for_deletion(ctx.author, message)

        async with ctx.typing():
            url = f"https://yandex.com/images/search?family=yes&text={search}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.67 Safari/537.36"
            }
            async with self.bot.client_session.get(url, headers=headers) as page:
                soup = lxml.html.fromstring(await page.text())

            images = {}
            for a in soup.xpath('.//div[@role="listitem"]'):
                data = orjson.loads(a.attrib["data-bem"])["serp-item"]
                images[data["dups"][0]["url"]] = data["snippet"]["title"]

            if not images:
                embed.description = "```No images found```"
                embed.set_footer(text="Safe search is enabled.")
                return await ctx.send(embed=embed)

            url, title = random.choice(list(images.items()))
            images.pop(url)

            embed.set_image(url=url)
            embed.title = title

            message = await ctx.send(embed=embed)

            cache[cache_search] = images
            self.loop.call_later(300, self.DB.delete_cache, cache_search, cache)
            self.DB.main.put(b"cache", orjson.dumps(cache))

        await self.wait_for_deletion(ctx.author, message)

    @commands.command(aliases=["c"])
    async def calc(self, ctx, num_base, *, expr=""):
        """Does math.

        It access to the following basic math functions
        ceil, comb, [fact]orial, gcd, lcm, perm, log, log2,
        log10, sqrt, acos, asin, atan, cos, sin, tain
        and the constants pi, e, tau.

        num_base: str
            The base you want to calculate in.
            Can be hex, oct, bin and for decimal ignore this argument
        expr: str
            A expression to calculate.
        """
        num_bases = {
            "h": (16, hex_float, "0x"),
            "o": (8, oct_float, "0o"),
            "b": (2, bin_float, "0b"),
        }
        base, method, prefix = num_bases.get(num_base[0].lower(), (None, None, None))

        if not base:  # If we haven't been given a base it is decimal
            base = 10
            expr = f"{num_base} {expr}"  # We want the whole expression

        if prefix:
            expr = expr.replace(prefix, "")  # Remove the prefix for a simple regex

        regex = r"[0-9a-fA-F]+" if base == 16 else r"\d+"

        if method:  # No need to extract numbers if we aren't converting
            numbers = [int(num, base) for num in re.findall(regex, expr)]
            expr = re.sub(regex, "{}", expr).format(*numbers)

        result = safe_eval(compile(expr, "<calc>", "eval", flags=1024).body)

        embed = discord.Embed(color=discord.Color.blurple())

        if method:
            embed.description = (
                f"```py\n{expr}\n\n>>> {prefix}{method(result)}\n\nDecimal: {result}```"
            )
            return await ctx.send(embed=embed)

        embed.description = f"```py\n{expr}\n\n>>> {result}```"
        await ctx.send(embed=embed)

    @commands.command(aliases=["ch", "cht"])
    async def cheatsheet(self, ctx, *search):
        """https://cheat.sh/python/ gets a cheatsheet.

        search: tuple
            The search terms.
        """
        search = "+".join(search)

        url = f"https://cheat.sh/python/{search}"
        headers = {"User-Agent": "curl/7.68.0"}

        async with ctx.typing(), self.bot.client_session.get(
            url, headers=headers
        ) as page:
            result = ANSI.sub("", await page.text()).translate({96: "\\`"})

        embed = discord.Embed(
            title=f"https://cheat.sh/python/{search}",
            color=discord.Color.blurple(),
            description=f"```py\n{result}```",
        )

        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    """Starts useful cog."""
    bot.add_cog(useful(bot))
