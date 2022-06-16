import difflib
import io
import random
import re
import secrets
import time
import urllib
from datetime import datetime

import discord
import lxml.html
import orjson
from discord.ext import commands

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
        "218": "This Is Fine",
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
        # Twitter End
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
        # nginx
        "494": "Request Header Too Large",
        "495": "SSL Certificate Error",
        "496": "SSL Certificate Required",
        "497": "HTTP Request Sent To HTTPS Port",
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
        "520": "Web Server Returned An Unknown Error",
        "521": "Web Server Is Down",
        "522": "Connection Timed Out",
        "523": "Origin Is Unreachable",
        "524": "A Timeout Occurred",
        "525": "SSL Handshake Failed",
        "526": "Invalid SSL Certificate",
        "527": "Railgun Error",
        # Qualys
        "529": "Site Is Overloaded",
        # Pantheon
        "530": "Site Is Frozen",
        # AWS
        "561": "Unauthorized",
        # AWS End
        "598": "(Informal Convention) Network Read Timeout Error",
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


class DeleteButton(discord.ui.View):
    def __init__(self, author: discord.Member):
        super().__init__()
        self.author = author

    @discord.ui.button(label="X", style=discord.ButtonStyle.red)
    async def delete(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user == self.author:
            if interaction.message:
                await interaction.message.delete()


class useful(commands.Cog):
    """Actually useful commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.DB = bot.DB
        self.loop = bot.loop
        self.cache = {}

    @commands.command()
    async def currency(self, ctx, *message):
        """Converts between currencies.

        Example usage:
            .currency usd
            .currency 3 usd
            .currency usd nzd
            .currency 3 usd nzd
            .currency usd to nzd
            .currency 3 usd to nzd

        message: tuple
        """
        embed = discord.Embed(color=discord.Color.blurple())

        if not message:
            embed.description = (
                "```ahk\nExample usage:\n  .currency usd nzd\n  .currency 3 "
                "usd nzd\n  .currency usd to nzd\n  .currency 3 usd to nzd```"
            )
            return await ctx.send(embed=embed)

        currencies = orjson.loads(self.DB.main.get(b"currencies"))
        length = len(message)

        if length == 1:
            new = "nzd"
            current = message[0]
            amount = 1
        elif length == 2:
            current, new = message
            if current.isdigit():
                new, current, amount = "nzd", new, float(current)
            else:
                amount = 1
        else:
            amount, current, *_, new = message

            if not amount.isdigit():
                current = amount
                amount = 1
            else:
                amount = float(amount)

        iso_current = current.upper()
        iso_new = new.upper()

        current = currencies.get(iso_current)
        new = currencies.get(iso_new)

        if not current:
            embed.title = f"Couldn't find currency with ISO code `{iso_current}`"
            return await ctx.send(embed=embed)

        if not new:
            embed.title = f"Couldn't find currency with ISO code `{iso_new}`"
            return await ctx.send(embed=embed)

        cprefix = current["symbol"]
        nprefix = new["symbol"]

        if new == "NZD":
            converted = amount / current["rate"]
        elif current == "NZD":
            converted = amount * new["rate"]
        else:
            converted = (new["rate"] * amount) / current["rate"]

        start = len(str(int(converted))) + 1
        count = 2

        # A shitty way to make sure we always have 2 significant *decimal* places
        for digit in str(converted)[start:]:
            if digit == "0":
                count += 1
            else:
                break

        embed.description = (
            f"```prolog\n{cprefix}{amount:,.0f} {iso_current}"
            f" is {nprefix}{converted:,.{count}f} {iso_new}```"
        )
        await ctx.send(embed=embed)

    @commands.command(aliases=["vaccines"])
    async def vaccine(self, ctx):
        """Gets current NZ vaccine data from the health.govt.nz website."""
        url = (
            "https://www.health.govt.nz/our-work/diseases-and-conditions/covid-19"
            "-novel-coronavirus/covid-19-data-and-statistics/covid-19-vaccine-data"
        )
        async with ctx.typing(), self.bot.client_session.get(url) as resp:
            soup = lxml.html.fromstring(await resp.text())

        data = soup.xpath(".//td")

        description = (
            "```prolog\n"
            "Eligible Population Vaccinated %:\n"
            f"  First Dose: {data[227].text_content()}\n"
            f"  Second Dose: {data[229].text_content()}\n"
            f"  Boosters: {data[233].text_content()}\n\n"
            "Cumulative Total:\n"
            f"  First Dose: {data[1].text}\n"
            f"  Second Dose: {data[4].text}\n"
            f"  Third Primary: {data[7].text}\n"
            f"  Boosters: {data[9].text}\n\n"
            "Vaccinations Yesterday:\n"
            f"  First Dose: {data[0].text}\n"
            f"  Second Dose: {data[3].text}\n"
            f"  Third Primary: {data[6].text}\n"
            f"  Boosters: {data[8].text}```"
        )

        await ctx.send(
            embed=discord.Embed(color=discord.Color.blurple(), description=description)
            .set_footer(text="Vaccine data from health.govt.nz")
            .set_image(
                url="https://www.health.govt.nz" + soup.xpath(".//img")[1].attrib["src"]
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

        embed = discord.Embed(color=discord.Color.blurple(), title="Upcoming Holidays")
        current_time = time.time()
        past_holidays = []

        for holiday in data:
            epoch = time.mktime(time.strptime(holiday["date"], "%Y-%m-%d"))
            # I want the the past holidays after everything else
            if epoch < current_time:
                past_holidays.append((holiday["name"], f"<t:{epoch:.0f}:R>"))
            else:
                embed.add_field(name=holiday["name"], value=f"<t:{epoch:.0f}:R>")

        embed.add_field(name="\u200B", value="\u200B", inline=False)

        for holiday, date in past_holidays[::-1]:
            embed.add_field(name=holiday, value=date)

        await ctx.send(embed=embed)

    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.cooldown(10, 60, commands.BucketType.default)
    @commands.command(aliases=["ss"])
    async def screenshot(self, ctx, website: str):
        """Takes a screenshot of a website and sends the image.

        website: str
        """
        if not website.startswith("http"):
            website = "https://" + website

        url = f"https://api.pikwy.com/?tkn=125&d=3000&u={website}&fs=0&w=1920&h=1080&f=png&rt=jweb"

        async with ctx.typing(), self.bot.client_session.post(url, timeout=40) as resp:
            data = await resp.json()

        await ctx.send(data["iurl"], view=DeleteButton(ctx.author))

    @commands.group(aliases=["temp"], invoke_without_command=True)
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

    @tempmail.command()
    async def messages(self, ctx):
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
            embed.title = "You haven't received any messages"
            embed.color = discord.Color.dark_red()
            return await ctx.send(embed=embed)

        for message in messages["hydra:member"]:
            intro = message.get("intro", "N/A")
            subject = message.get("subject", "N/A")

            embed.add_field(
                name=f"{message['from']['name']} [{message['from']['address']}]",
                value=f"```Id: {message['id']}\nSubject: {subject}\n\n{intro}```",
                inline=False,
            )

        embed.set_footer(text="Use .tempmessage [ID] to get the full message")
        await ctx.send(embed=embed)

    @tempmail.command()
    async def message(self, ctx, message_id):
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
    async def translate(self, ctx, *, text=None):
        """Translates text to english."""
        if not text:
            reference = ctx.message.reference
            if not reference or not reference.resolved:
                return await ctx.reply(
                    "Either reply to a message or use the text argument"
                )
            text = reference.resolved.content
        if not text:
            return await ctx.reply("You need to reply to a message with text")

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

                return await ctx.reply(translate_text)

    @commands.command()
    async def weather(self, ctx, *, location="auckland"):
        """Gets the weather from wttr.in defaults location to auckland.

        location: str
            The name of the location to get the weather of.
        """
        url = f"http://wttr.in/{location}?format=j1"
        embed = discord.Embed(color=discord.Color.blurple())

        async with ctx.typing(), self.bot.client_session.get(url) as resp:
            try:
                data = await resp.json()
            except ValueError:
                embed.title = "Failed to get weather for that location"
                embed.color = discord.Color.dark_red()
                return await ctx.send(embed=embed)

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
    @commands.guild_only()
    async def snipe(self, ctx):
        """Snipes the last deleted message."""
        data = self.DB.main.get(f"{ctx.guild.id}-snipe_message".encode())

        embed = discord.Embed(color=discord.Color.blurple())

        if not data:
            embed.title = "No message to snipe"
            embed.color = discord.Color.dark_red()
            return await ctx.send(embed=embed)

        message, author = orjson.loads(data)

        embed.title = f"{author} deleted:"
        embed.description = f"```{message}```"

        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    async def editsnipe(self, ctx):
        """Snipes the last edited message."""
        data = self.DB.main.get(f"{ctx.guild.id}-editsnipe_message".encode())

        embed = discord.Embed(color=discord.Color.blurple())

        if not data:
            embed.title = "No message to snipe"
            embed.color = discord.Color.dark_red()
            return await ctx.send(embed=embed)

        original, edited, author = orjson.loads(data)

        embed.title = f"{author} edited:"
        embed.add_field(name="From:", value=f"```{original}```")
        embed.add_field(name="To:", value=f"```{edited}```")

        await ctx.send(embed=embed)

    async def cache_check(self, search):
        """Checks the cache for an search if found randomly return a result.

        search: str
        """
        cache = self.bot.cache

        if search in cache:
            if not cache[search]:
                return {}

            url, title = random.choice(list(cache[search].items()))

            cache[search].pop(url)

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

            return await ctx.send(embed=embed, view=DeleteButton(ctx.author))

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
                embed.title = "No images found"
                embed.color = discord.Color.dark_red()
                return await ctx.send(embed=embed)

            url, title = random.choice(list(images.items()))
            images.pop(url)

            embed.set_image(url=url)
            embed.title = title

            await ctx.send(embed=embed, view=DeleteButton(ctx.author))

            cache[cache_search] = images
            self.loop.call_later(300, self.bot.remove_from_cache, cache_search)

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

            return await ctx.send(embed=embed, view=DeleteButton(ctx.author))

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
                embed.title = "No images found"
                embed.color = discord.Color.dark_red()
                embed.set_footer(text="Safe search is enabled.")
                return await ctx.send(embed=embed)

            url, title = random.choice(list(images.items()))
            images.pop(url)

            embed.set_image(url=url)
            embed.title = title

            await ctx.send(embed=embed, view=DeleteButton(ctx.author))

            cache[cache_search] = images
            self.loop.call_later(300, self.bot.remove_from_cache, cache_search)


def setup(bot: commands.Bot) -> None:
    """Starts the useful cog."""
    bot.add_cog(useful(bot))
