import io
import difflib
import opcode
import random
import re
import unicodedata
from datetime import datetime
import math

from discord.ext import commands
import aiohttp
import discord
import lxml.html
import orjson

from cogs.utils.time import parse_date
from cogs.utils.color import hsslv
from cogs.utils.calculation import hex_float, oct_float, bin_float


CHARACTERS = (
    "Miss Pauling",
    "Scout",
    "Soldier",
    "Demoman",
    "Heavy",
    "Engineer",
    "Medic",
    "Sniper",
    "Spy",
    "Stanley",
    "The Narrator",
    "Steven Universe",
    "Rise Kujikawa",
    "SpongeBob SquarePants",
    "Dan",
)

ALT_NAMES = {
    "Pauling": "Miss Pauling",
    "Narrator": "The Narrator",
    "Steven": "Steven Universe",
    "Rise": "Rise Kujikawa",
    "Spongebob": "SpongeBob SquarePants",
    "Spongebob Squarepants": "SpongeBob SquarePants",
}

BIG_NUMS = (
    "",
    "Thousand",
    "Million",
    "Billion",
    "Trillion",
    "Quadrillion",
    "Quintillion",
    "Sextillion",
    "Septillion",
    "Octillion",
    "Nonillion",
    "Decillion",
    "Undecillion",
    "Duodecillion",
    "Tredecillion",
    "Quattuordecillion",
    "Quindecillion",
    "Sexdecillion",
    "Septendecillion",
    "Octodecillion",
    "Novemdecillion",
    "Vigintillion",
    "Unvigintillion",
    "Duovigintillion",
    "Tresvigintillion",
    "Quattuorvigintillion",
    "Quinvigintillion",
    "Sesvigintillion",
    "Septemvigintillion",
    "Octovigintillion",
    "Novemvigintillion",
    "Trigintillion",
    "Untrigintillion",
    "Duotrigintillion",
    "Trestrigintillion",
    "Quattuortrigintillion",
    "Quintrigintillion",
    "Sestrigintillion",
    "Septentrigintillion",
    "Octotrigintillion",
    "Noventrigintillion",
    "Quadragintillion",
)

opcodes = opcode.opmap


class misc(commands.Cog):
    """Commands that don't fit into other cogs."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.DB = bot.DB

    @commands.command()
    async def num(self, ctx, num: int):
        """Parses a number into short scale form.

        num: int
        """
        prefix = ""
        if num < 0:
            num = abs(num)
            prefix = "-"
        index = math.floor(math.log10(num) / 3) if num // 1 else 0
        if index > 41:
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.red(),
                    description="Largest number that can be shown is Quadragintillion (126 digits)",
                )
            )
        return await ctx.send(f"{prefix}{num/10**(3*index):.1f} {BIG_NUMS[index]}")

    @commands.command(aliases=["commits"])
    async def dcommits(self, ctx):
        """Gets all the urls of discord commits with comments."""
        url = "https://api.github.com/repos/Discord-Datamining/Discord-Datamining/commits?per_page=100"
        data = await self.bot.get_json(url)
        embed = discord.Embed(color=discord.Color.og_blurple())
        count = 0

        for commit in data:
            comment_count = commit["commit"]["comment_count"]
            if comment_count:
                timestamp = int(
                    datetime.strptime(
                        commit["commit"]["author"]["date"], "%Y-%m-%dT%H:%M:%SZ"
                    ).timestamp()
                )
                embed.add_field(
                    name=f"<t:{timestamp}:R>",
                    value=f"[Link](<{commit['html_url']}#comments>) - {comment_count} comments",
                )
                count += 1
                if count == 24:
                    return await ctx.send(embed=embed)

        await ctx.send(embed=embed)

    @commands.command()
    async def char(self, ctx, *, characters: str):
        """Shows you information about some unicode characters."""

        def to_string(c):
            digit = f"{ord(c):x}"
            return (
                f"`\\U{digit:>08}`: {unicodedata.name(c, 'Name not found.')} - {c}\n"
                f"<http://www.fileformat.info/info/unicode/char/{digit}/index.htm>"
            )

        msg = "\n".join(map(to_string, characters))
        if len(msg) > 2000:
            return await ctx.send("Output too long to display.")
        await ctx.send(msg)

    @commands.command()
    async def tiles(self, ctx, sat: float = 0.25):
        """Generates tiles of a random color with a deafult 25% saturation.

        sat: float
            Saturation of the random color.
        """
        color = discord.Color.from_hsv(random.random(), sat, 1)
        url = (
            f"https://php-noise.com/noise.php?hex={color.value:X}"
            "&tileSize=20&borderWidth=2&json"
        )

        tile = await self.bot.get_json(url)

        embed = discord.Embed(color=color)
        embed.set_image(url=tile["uri"])
        await ctx.send(embed=embed)

    @commands.command()
    async def code(self, ctx):
        embed = discord.Embed(
            color=discord.Color.random(), title="Discord Code Block formatting"
        )
        embed.description = """
        You can format code like this
        \\`\\`\\`py
        print("test")
        \\`\\`\\`

        Which renders in discord as
        ```py\nprint("test")```
        """
        await ctx.send(embed=embed)

    @commands.command()
    async def md(self, ctx, *, text):
        """Shows text inside a variety of different code block markdown.

        text: str
        """
        embed = discord.Embed(color=discord.Color.blurple())
        if len(text) > 236:
            embed.description = "```Text must be shorter than 236 characters```"
            return await ctx.send(embed=embed)

        languages = (
            "asciidoc",
            "ahk",
            "bash",
            "coffee",
            "cpp",
            "cs",
            "css",
            "diff",
            "fix",
            "glsl",
            "ini",
            "json",
            "md",
            "ml",
            "prolog",
            "py",
            "tex",
            "xl",
            "xml",
            "clj",
            "dst",
            "fs",
            "f95",
            "go",
        )

        for lang in languages:
            embed.add_field(name=lang, value=f"```{lang}\n{text}```")

        await ctx.send(embed=embed)

    @commands.command()
    async def fen(self, ctx, *, fen: str):
        """Converts a chess fen to an image.

        fen examples:
        r1b1k1nr/p2p1pNp/n2B4/1p1NP2P/6P1/3P1Q2/P1P1K3/q5b1
        rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
        4k2r/6r1/8/8/8/8/3R4/R3K3 w Qk - 0 1

        fen: str
        """
        await ctx.send(
            f"https://www.chess.com/dynboard?fen={fen.replace(' ', '%20')}&size=2"
        )

    @commands.command()
    async def epoch(self, ctx, epoch: int):
        """Converts epoch time to relative time.

        epoch: int
            The epoch time to convert can be seconds, milliseconds, microseconds.
        """
        await ctx.send(f"<t:{str(epoch)[:10]}:R>")

    @commands.command()
    async def color(self, ctx, color):
        """Gets information about a hex color.

        color: str
            Hex color value.
        """
        color = color.removeprefix("#").removeprefix("0x")
        url = f"https://api.alexflipnote.dev/color/{color:0>6}"
        data = await self.bot.get_json(url)

        if "description" in data:
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description=f"```prolog\n{data['description']}```",
                )
            )
        embed = discord.Embed(title=data["name"], color=data["int"])

        r, g, b = data["rgb_values"].values()

        embed.add_field(name="RGB", value=f"{r}, {g}, {b}")

        r, g, b = r / 255, g / 255, b / 255

        hue, satv, satl, lum, val = hsslv(r, g, b)
        embed.add_field(
            name="HSL", value=f"{hue*360:.0f}°, {satl*100:.0f}%, {lum*100:.0f}%"
        )
        embed.add_field(
            name="HSV", value=f"{hue*360:.0f}°, {satv*100:.0f}%, {val*100:.0f}%"
        )
        embed.set_thumbnail(
            url=(
                "https://app.pixelencounter.com/api/basic/svgmonsters"
                f"/image/png?primaryColor=%23{color:0>6}&size=256&format=png"
            )
        )
        embed.set_image(url=data["image_gradient"])
        embed.set_footer(
            text="Above is shades/tints, top-right is"
            f" a svg monster of the color #{color:0>6}"
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def diff(self, ctx, start, end=None):
        """Gets the difference between two times.

        Although the arguments have been named start-end
        it doesn't matter if the start is greater than the end

        Supported Date Formats:
            13/10/2021    2021/10/13
            13.10.2021    2021.10.13
            13-10-2021    2021-10-13

        start: str
            The start time
        end: str
            The ending time
        """
        date = parse_date(start)
        if end:
            date = parse_date(end) - date + discord.utils.utcnow()

        await ctx.send(f"<t:{date.timestamp():.0f}:R>")

    @commands.command()
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def tts(self, ctx, character=None, *, text=None):
        """Uses 15.ai to convert text to an audio file."""
        if not character or not text:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description="```.tts [character] [text]"
                    f"\n\nOptions: {', '.join(CHARACTERS)}\n\n"
                    "Use quotes around characters with a space```",
                )
            )

        if re.search(r"\d", text):
            ctx.command.reset_cooldown(ctx)
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description="```Text cannot include numbers "
                    "spell out the numbers instead```",
                )
            )

        character = character.title()
        character = ALT_NAMES.get(character, character)

        if character not in CHARACTERS:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description=f"```No character found for {character}"
                    f"\n\nOptions: {', '.join(CHARACTERS)}```",
                )
            )

        if (length := len(text)) > 200:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description=f"```Text must be longer than 4 characters "
                    f"and shorter than 200 charcters[{length}]```",
                )
            )

        url = "https://api.15.ai/app/getAudioFile5"
        data = {
            "character": character,
            "emotion": "Contextual",
            "text": text + "." if text[-1] not in [".", "!"] else "",
        }
        files = []

        async with ctx.typing():
            resp = await self.bot.client_session.post(url, json=data, timeout=60)
            if resp.status != 200:
                ctx.command.reset_cooldown(ctx)
                return await ctx.send(
                    embed=discord.Embed(
                        color=discord.Color.blurple(),
                        description=f"```Api cannot be reached [{resp.status}]```",
                    )
                )
            data = await resp.json(content_type=None)

            if "wavNames" not in data:
                ctx.command.reset_cooldown(ctx)
                return await ctx.send(
                    embed=discord.Embed(
                        color=discord.Color.blurple(),
                        description=f"```Failed to process request"
                        f" [{data['message']}]```",
                    )
                )

            for audiofile in data["wavNames"]:
                audio = await self.bot.client_session.get(
                    f"https://cdn.15.ai/audio/{audiofile}"
                )
                files.append(discord.File(io.BytesIO(await audio.read()), audiofile))

        await ctx.send(files=files)

    @commands.command()
    async def justin(self, ctx):
        """Gets a random message from justin."""
        messages = orjson.loads(self.DB.main.get(b"justins-messages"))

        embed = discord.Embed(
            color=discord.Color.blurple(), description=random.choice(messages)
        )
        embed.set_footer(text="― Justin")
        await ctx.send(embed=embed)

    @commands.command()
    async def euler(self, ctx, problem: int):
        """Gets a solution to a project euler problem in python.

        problem: int
        """
        url = (
            "https://raw.githubusercontent.com/TheAlgorithms/Python"
            f"/master/project_euler/problem_{problem:0>3}/sol1.py"
        )

        async with self.bot.client_session.get(url) as page:
            content = await page.text()

        content = re.sub(r'"""[\w\W]*?"""', "", content)
        content = re.sub(r"\n\ \ \ \ \n", "", content)

        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                title=f"Project Euler Problem {problem} Solution",
                description=f"```py\n{content}```",
            )
        )

    @commands.command()
    async def rate(self, ctx, user: discord.User = None):
        """Rates users out of 100.

        Results are not endorsed by Snake Bot

        user: discord.User
            Defaults to author.
        """
        user = user or ctx.author
        num = random.Random(user.id ^ 1970636).randint(0, 100)

        await ctx.send(
            f"{user.mention} is a {num} out of 100",
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @commands.guild_only()
    @commands.command()
    async def ship(self, ctx, user: discord.User = None):
        """Ships a user with a random other user.

        Results are not endorsed by Snake Bot

        user: discord.User
            Defaults to author.
        """
        user = user or ctx.author
        temp_random = random.Random(user.id >> 4)

        ship = temp_random.choice(ctx.guild.members)

        while user == ship:
            ship = temp_random.choice(ctx.guild.members)

        await ctx.send(
            f"{user.mention} has been shipped with {ship.mention} :eyes:",
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @commands.command()
    async def match(self, ctx, user1: discord.User, user2: discord.User = None):
        """Sees how much of a match two users are.

        Results are not endorsed by Snake Bot

        user1: discord.User
        user2: discord.User
            Defaults to author.
        """
        user2 = user2 or ctx.author
        perc = random.Random(user1.id & user2.id).randint(0, 100)

        await ctx.send(
            f"{user1.mention} is a {perc}% match with {user2.mention}",
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @commands.command(name="embedjson")
    async def embed_json(self, ctx, message: discord.Message):
        """Converts the embed of a message to json.

        message: discord.Message
        """
        embed = discord.Embed(color=discord.Color.blurple())

        if not message.embeds:
            embed.description = "```Message has no embed```"
            return await ctx.send(embed=embed)

        message_embed = message.embeds[0]

        json = (
            str(message_embed.to_dict())
            .replace("'", '"')
            .replace("True", "true")
            .replace("False", "false")
            .replace("`", "`\u200b")
        )

        if len(json) > 2000:
            return await ctx.send(file=discord.File(io.StringIO(json), "embed.json"))

        embed.description = f"```json\n{json}```"
        await ctx.send(embed=embed)

    @commands.command()
    async def nato(self, ctx, *, text):
        """Converts text to the NATO phonetic alphabet.

        text: str
        """
        table = {
            32: "(space) ",
            49: "One ",
            50: "Two ",
            51: "Three ",
            52: "Four ",
            53: "Five ",
            54: "Six ",
            55: "Seven ",
            56: "Eight ",
            57: "Nine ",
            97: "Alfa ",
            98: "Bravo ",
            99: "Charlie ",
            100: "Delta ",
            101: "Echo ",
            102: "Foxtrot ",
            103: "Golf ",
            104: "Hotel ",
            105: "India ",
            106: "Juliett ",
            107: "Kilo ",
            108: "Lima ",
            109: "Mike ",
            110: "November ",
            111: "Oscar ",
            112: "Papa ",
            113: "Quebec ",
            114: "Romeo ",
            115: "Sierra ",
            116: "Tango ",
            117: "Uniform ",
            118: "Victor ",
            119: "Whiskey ",
            120: "X-ray ",
            121: "Yankee ",
            122: "Zulu ",
        }

        await ctx.send(text.lower().translate(table))

    @commands.group()
    async def rle(self, ctx):
        """Encodes or decodes a string with run length encoding."""
        if not ctx.invoked_subcommand:
            embed = discord.Embed(
                color=discord.Color.blurple(),
                description=f"```Usage: {ctx.prefix}rle [de/en]```",
            )
            await ctx.send(embed=embed)

    @rle.command()
    async def en(self, ctx, *, text):
        """Encodes a string with run length encoding."""
        text = re.sub(r"(.)\1*", lambda m: m.group(1) + str(len(m.group(0))), text)
        await ctx.send(text)

    @rle.command()
    async def de(self, ctx, *, text):
        """Decodes a string with run length encoding."""
        text = re.sub(r"(\D)(\d+)", lambda m: int(m.group(2)) * m.group(1), text)
        await ctx.send(text)

    @commands.command()
    async def convert(self, ctx, number: int):
        """Converts fahrenheit to celsius

        number: int
        """
        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                description=f"```{number}°F is {(number - 32) * (5/9):.2f}°C```",
            )
        )

    @commands.command()
    async def ones(self, ctx, number: int):
        """Converts a decimal number to binary ones complement.

        number: int
        """
        table = {49: "0", 48: "1"}
        return await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                description=f"```{bin(number)[2:].translate(table)}```",
            )
        )

    @commands.command()
    async def twos(self, ctx, number: int, bits: int):
        """Converts a decimal number to binary twos complement.

        number: int
        bits: int
        """
        return await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                description=f"```{bin(number & int('1'*bits, 2))[2:]:0>{bits}}```",
            )
        )

    @commands.command(aliases=["id"])
    async def snowflake(self, ctx, snowflake: int):
        """Shows some information about a discord snowflake.

        snowflake: int
            A discord snowflake e.g 744747000293228684
        """
        embed = discord.Embed(color=discord.Color.blurple())
        embed.add_field(
            name="Internal Worker ID", value=(snowflake & 0x3E0000) >> 17, inline=False
        )
        embed.add_field(
            name="Internal process ID", value=(snowflake & 0x1F000) >> 12, inline=False
        )
        embed.add_field(
            name="Time",
            value=f"<t:{((snowflake >> 22) + 1420070400000)//1000}>",
            inline=False,
        )
        embed.add_field(name="Increment", value=snowflake & 0xFFF, inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def unsplash(self, ctx, *, search):
        """Gets an image from unsplash based off a search.

        search: str
        """
        url = f"https://source.unsplash.com/random?{search}"
        async with ctx.typing(), self.bot.client_session.get(
            url, allow_redirects=False
        ) as page:
            soup = lxml.html.fromstring(await page.text())

        await ctx.send(soup.xpath(".//a")[0].attrib["href"])

    @commands.command()
    async def rand(self, ctx, a: int, b: int):
        """Gets a random number such that a <= N <= b"""
        if a > b:
            a, b = b, a
        await ctx.reply(random.randint(a, b))

    @commands.command()
    async def opcode(self, ctx, search):
        """Gets closest matches for an opcode.
        Example usage .opcode UNARY_INVERT

        search: str
        """

        def format_op(op):
            code = opcodes[op]
            return f"{code:<5x}{code:<5}{repr(chr(code)):<8}{op}"

        matches = difflib.get_close_matches(search.upper(), [*opcodes], cutoff=0, n=5)
        msg = "\n".join([format_op(match) for match in matches])
        await ctx.send(f"```prolog\nHex: Num: BC:     Name:\n\n{msg}```")

    @commands.group()
    async def binary(self, ctx):
        """Encoded or decodes binary as ascii text."""
        if not ctx.invoked_subcommand:
            embed = discord.Embed(
                color=discord.Color.blurple(),
                description=f"```Usage: {ctx.prefix}binary [decode/encode]```",
            )
            await ctx.send(embed=embed)

    @binary.command(name="en")
    async def binary_encode(self, ctx, *, text):
        """Encodes ascii text as binary.

        text: str
        """
        await ctx.send(" ".join([f"{bin(ord(letter))[2:]:0>8}" for letter in text]))

    @binary.command(name="de")
    async def binary_decode(self, ctx, *, binary):
        """Decodes binary as ascii text.

        binary: str
        """
        binary = binary.replace(" ", "")
        # fmt: off
        await ctx.send(
            "".join([chr(int(binary[i: i + 8], 2)) for i in range(0, len(binary), 8)])
        )
        # fmt: on

    @commands.command()
    async def dashboard(self, ctx):
        """Sends a link to Bryns dashboard."""
        await ctx.send("https://web.tukib.org/uoa")

    @commands.command()
    async def notes(self, ctx):
        """Sends a link to Joes notes."""
        embed = discord.Embed(color=discord.Color.blurple(), title="Joes Notes")

        embed.description = """
        [Home Page](https://notes.joewuthrich.com)

        [Compsci 101](https://notes.joewuthrich.com/compsci101)
        Introduction to programming using the Python programming language.

        [Compsci 110](https://notes.joewuthrich.com/compsci110)
        This course explains how computers work and some of the things we can use them for.

        [Compsci 120](https://notes.joewuthrich.com/compsci120)
        Introduces basic mathematical tools and methods needed for computer science.

        [Compsci 130](https://notes.joewuthrich.com/compsci130)
        Entry course to Computer Science for students with prior programming knowledge in Python.

        [Compsci 225](https://notes.joewuthrich.com/compsci225)
        Discrete Structures in Mathematics and Computer Science.
        """
        await ctx.send(embed=embed)

    @commands.command()
    async def markdown(self, ctx):
        """Sends a link to a guide on markdown"""
        await ctx.send(
            "https://gist.github.com/matthewzring/9f7bbfd102003963f9be7dbcf7d40e51"
        )

    @staticmethod
    def starmap(iterable):
        for num1, num2 in iterable:
            yield num1 * num2

    @commands.group()
    async def cipher(self, ctx):
        """Solves or encodes a caesar cipher."""
        if not ctx.invoked_subcommand:
            embed = discord.Embed(
                color=discord.Color.blurple(),
                description=f"```Usage: {ctx.prefix}cipher [decode/encode]```",
            )
            await ctx.send(embed=embed)

    @cipher.command()
    async def encode(self, ctx, shift: int, *, message):
        """Encodes a message using the ceasar cipher.

        shift: int
            How much you want to shift the message.
        message: str
        """
        if message.isupper():
            chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        else:
            message = message.lower()
            chars = "abcdefghijklmnopqrstuvwxyz"

        table = str.maketrans(chars, chars[shift:] + chars[:shift])

        await ctx.send(message.translate(table))

    @cipher.command(aliases=["solve", "brute"])
    async def decode(self, ctx, *, message):
        """Solves a caesar cipher via brute force.
        Shows results sorted by the chi-square of letter frequencies

        message: str
        """
        if message.isupper():
            chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        else:
            message = message.lower()
            chars = "abcdefghijklmnopqrstuvwxyz"

        # fmt: off

        freq = {
            "a": 8.04, "b": 1.48, "c": 3.34,
            "d": 3.82, "e": 12.49, "f": 2.4,
            "g": 1.87, "h": 5.05, "i": 7.57,
            "j": 0.16, "k": 0.54, "l": 4.07,
            "m": 2.51, "n": 7.23, "o": 7.64,
            "p": 2.14, "q": 0.12, "r": 6.28,
            "s": 6.51, "t": 9.28, "u": 2.73,
            "v": 1.05, "w": 1.68, "x": 0.23,
            "y": 1.66, "z": 0.09,
        }

        # fmt: on

        msg_len = len(message)

        rotate1 = str.maketrans(chars, chars[1:] + chars[0])
        embed = discord.Embed(color=discord.Color.blurple())

        results = []

        for i in range(25, 0, -1):
            message = message.translate(rotate1)
            chi = sum(
                [
                    (((message.count(char) / msg_len) - freq[char]) ** 2) / freq[char]
                    for char in set(message.lower().replace(" ", ""))
                ]
            )
            results.append((chi, (i, message)))

        for chi, result in sorted(results, reverse=True):
            embed.add_field(name=result[0], value=result[1])

        embed.set_footer(text="Sorted by the chi-square of their letter frequencies")

        await ctx.send(embed=embed)

    @commands.command()
    async def block(self, ctx, A, B):
        """Solves a block cipher in the format of a python matrix.

        e.g
        "1 2 3" "3 7 15, 6 2 61, 2 5 1"

        A: str
        B: str
        """
        if "a" < A:
            A = [[ord(letter) - 97 for letter in A]]
        else:
            A = A.split(",")
            A = [[int(num) for num in block.split()] for block in A]
        B = B.split(",")
        B = [[int(num) for num in block.split()] for block in B]

        results = ""

        for block in A:
            results += f"{[sum(self.starmap(zip(block, col))) for col in zip(*B)]}\n"

        embed = discord.Embed(
            color=discord.Color.blurple(), description=f"```{results}```"
        )
        await ctx.send(embed=embed)

    @commands.command(name="8ball")
    async def eightball(self, ctx):
        """Seek advice or fortune-telling."""
        responses = [
            "It is certain.",
            "Without a doubt.",
            "Most likely.",
            "Outlook good.",
            "Yes.",
            "Reply hazy, try again.",
            "Ask again later.",
            "Better not tell you now.",
            "Cannot predict now.",
            "Concentrate and ask again.",
            "Don't count on it.",
            "My reply is no.",
            "My sources say no.",
            "Outlook not so good.",
            "Very doubtful.",
        ]
        await ctx.reply(random.choice(responses))

    @commands.command(name="hex")
    async def _hex(self, ctx, number: float, convert: bool = False):
        """Shows a number in hexadecimal prefixed with “0x”.

        number: str
            The number you want to convert.
        convert: bool
            If you want to convert to decimal or not
        """
        embed = discord.Embed(color=discord.Color.blurple())
        if convert:
            embed.description = f"```{int(number, 16)}```"
            return await ctx.send(embed=embed)
        embed.description = f"```{hex_float(number)}```"
        await ctx.send(embed=embed)

    @commands.command(name="oct")
    async def _oct(self, ctx, number: float, convert: bool = False):
        """Shows a number in octal prefixed with “0o”.

        number: str
            The number you want to convert.
        convert: bool
            If you want to convert to decimal or not
        """
        embed = discord.Embed(color=discord.Color.blurple())
        if convert:
            embed.description = f"```{int(number, 8)}```"
            return await ctx.send(embed=embed)
        embed.description = f"```{oct_float(number)}```"
        await ctx.send(embed=embed)

    @commands.command(name="bin")
    async def _bin(self, ctx, number: float, convert: bool = False):
        """Shows a number in binary prefixed with “0b”.

        number: str
            The number you want to convert.
        convert: bool
            If you want to convert to decimal or not
        """
        embed = discord.Embed(color=discord.Color.blurple())
        if convert:
            embed.description = f"```{int(number, 2)}```"
            return await ctx.send(embed=embed)
        embed.description = f"```{bin_float(number)}```"
        await ctx.send(embed=embed)

    @commands.command(aliases=["socialcredit"])
    async def karma(self, ctx, user: discord.User = None):
        """Gets a users karma.

        user: discord.User
            The user to get the karma of.
        """
        user = user or ctx.author
        user_id = str(user.id).encode()
        karma = self.DB.karma.get(user_id)

        if not karma:
            karma = 0
        else:
            karma = karma.decode()

        tenary = "+" if int(karma) > 0 else ""

        embed = discord.Embed(color=discord.Color.blurple())
        embed.description = f"```diff\n{user.display_name}'s karma:\n{tenary}{karma}```"
        await ctx.send(embed=embed)

    @commands.command(aliases=["kboard", "ktop", "karmatop"])
    async def karmaboard(self, ctx):
        """Displays the top 5 and bottom 5 members karma."""
        sorted_karma = sorted(
            [(int(k), int(m)) for m, k in self.DB.karma], reverse=True
        )
        embed = discord.Embed(title="Karma Board", color=discord.Color.blurple())

        def parse_karma(data):
            lst = []
            for karma, member in data:
                temp = self.bot.get_user(member)
                member = temp.display_name if temp else member
                lst.append(f"{'-' if karma < 0 else '+'} {member}: {karma}")
            return lst

        embed.add_field(
            name="Top Five",
            value="```diff\n{}```".format("\n".join(parse_karma(sorted_karma[:5]))),
        )
        embed.add_field(
            name="Bottom Five",
            value="```diff\n{}```".format("\n".join(parse_karma(sorted_karma[-5:]))),
        )
        await ctx.send(embed=embed)

    @commands.command(aliases=["element", "ele"])
    async def atom(self, ctx, element):
        """Displays information for a given atom.

        element: str
            The symbol of the element to search for.
        """
        url = f"http://www.chemicalelements.com/elements/{element.lower()}.html"
        embed = discord.Embed(colour=discord.Color.blurple())

        async with ctx.typing():
            try:
                async with self.bot.client_session.get(url) as page:
                    text = lxml.html.fromstring(await page.text())
            except aiohttp.client_exceptions.ClientResponseError:
                embed.description = f"```Could not find and element with the symbol {element.upper()}```"
                return await ctx.send(embed=embed)

        image = f"http://www.chemicalelements.com{text.xpath('.//img')[1].attrib['src'][2:]}"
        text = text.xpath("//text()")[108:]

        embed.title = text[1]
        embed.set_thumbnail(url=image)
        embed.add_field(name="Name", value=text[1])
        embed.add_field(name="Symbol", value=text[3])
        embed.add_field(name="Atomic Number", value=text[5])
        embed.add_field(name="Atomic Mass", value=text[7])
        embed.add_field(name="Melting Point", value=text[9])
        embed.add_field(name="Boiling Point", value=text[11])
        embed.add_field(name="Protons/Electrons", value=text[13])
        embed.add_field(name="Neutrons", value=text[15])
        embed.add_field(name="Color", value=text[text.index("Color:") + 1])
        embed.add_field(name="Uses", value=text[text.index("Uses:") + 1])
        embed.add_field(
            name="Year of Discovery", value=text[text.index("Date of Discovery:") + 1]
        )
        embed.add_field(name="Discoverer", value=text[text.index("Discoverer:") + 1])

        await ctx.send(embed=embed)

    @commands.command()
    async def roll(self, ctx, dice: str):
        """Rolls dice in AdX format. A is number of dice, X is number of faces.

        dice: str
            The dice to roll in AdX format.
        """
        embed = discord.Embed(color=discord.Color.blurple())

        try:
            rolls, limit = map(int, dice.split("d"))
        except ValueError:
            embed.description = "```Format has to be AdX```"
            return await ctx.send(embed=embed)

        if rolls > 1000:
            embed.description = "```You can't do more than 1000 rolls at once.```"
            return await ctx.send(embed=embed)

        nums = random.choices(range(1, limit + 1), k=rolls)
        embed.description = "```Results: {} Total: {}```".format(
            ", ".join(map(str, nums)), sum(nums)
        )
        await ctx.reply(embed=embed)

    @commands.command()
    async def choose(self, ctx, *options: str):
        """Chooses between mulitple things.

        options: str
            The options to choose from.
        """
        await ctx.reply(
            random.choice(options), allowed_mentions=discord.AllowedMentions.none()
        )

    @commands.command()
    async def yeah(self, ctx):
        """Oh yeah its all coming together."""
        await ctx.send("Oh yeah its all coming together")

    @commands.command()
    async def slap(self, ctx, member: discord.Member, *, reason="they are evil"):
        """Slaps a member.

        member: discord.Member
            The member to slap.
        reason: str
            The reason for the slap.
        """
        await ctx.send(
            f"{ctx.author.mention} slapped {member.mention} because {reason}",
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @commands.command()
    async def bar(self, ctx, graph_data: commands.Greedy[int] = None):
        """Sends a bar graph based of inputted numbers.

        e.g: bar 1 2 3

                     ____
               ____ |    |
         ____ |    ||    |
        |    ||    ||    |
        ------------------

        graph_data: commands.Greedy[int]
            A list of graph data.
        """
        max_val = max(graph_data)

        if len(graph_data) * 6 * (max_val + 2) + max_val + 7 > 10000:
            return

        bar_graph = ""

        for val in range(max_val + 1, 0, -1):
            for index in range(len(graph_data)):
                if graph_data[index] - val > -1:
                    bar_graph += "|    |"
                elif graph_data[index] - val == -1:
                    bar_graph += " ____ "
                else:
                    bar_graph += "      "
            bar_graph += "\n"
        bar_graph += "------" * len(graph_data)

        if len(graph_data) * 6 * (max_val + 2) + max_val + 7 > 2000:
            return await ctx.send(file=discord.File(io.StringIO(bar_graph), "bar.txt"))

        await ctx.send(f"```\n{bar_graph}```")


def setup(bot: commands.Bot) -> None:
    """Starts misc cog."""
    bot.add_cog(misc(bot))
