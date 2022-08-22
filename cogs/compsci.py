import io
import ipaddress
import math
import re
from zlib import compress

import discord
import orjson
from discord.ext import commands, pages

from cogs.utils.calculation import bin_float, hex_float, oct_float, safe_eval

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


class compsci(commands.Cog):
    """Commands related Computer Science."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.DB = bot.DB

    @commands.command(aliases=["course"])
    async def courses(self, ctx, course_number: int = None):
        """Gets information about compsci courses at the University of Auckland."""
        embed = discord.Embed(color=discord.Color.blurple())
        courses = self.DB.main.get(b"courses")

        if not courses:
            embed.title = "Failed to get course information"
            return await ctx.send(embed=embed)

        courses = orjson.loads(courses)

        if course_number:
            name = f"COMPSCI {course_number}"
            info = courses.get(name)
            if not info:
                embed.title = "Couldn't find that course"
                return await ctx.send(embed=embed)

            stages, description, restrictions = info

            stages = "\n".join(stages)
            if not description:
                description = "No description..."

            embed.description = f"{stages}\n\n{description}\n\n{restrictions}"
            embed.title = name
            return await ctx.send(embed=embed)

        count = 0
        embeds = []

        for course_name, info in courses.items():
            count += 1

            stages, description, restrictions = info

            stages = "\n".join(stages)
            if description:
                description = description.split(".", 1)[0]
            else:
                description = "No description..."

            embed.add_field(
                name=course_name, value=f"{stages}\n\n{description}\n\n{restrictions}"
            )

            if count == 6:
                embeds.append(embed)
                embed = discord.Embed(color=discord.Color.blurple())
                count = 0

        if count != 6:
            embeds.append(embed)

        paginator = pages.Paginator(pages=embeds)
        await paginator.send(ctx)

    @commands.command(aliases=["propagation", "transmission"])
    async def prop(self, ctx, data_rate, length, speed, frame_size):
        """Calculates transmission time, propagation time and effective data rate."""
        data_rate = int(data_rate.upper().rstrip("MB"))
        length = int(length.upper().rstrip("KM"))
        speed = int(speed.upper().rstrip("KM").rstrip("KM/S"))
        frame_size = int(frame_size)

        transmission = frame_size / data_rate
        propagation = (length / speed) * 1000
        effective_excluding = propagation * 2
        effective = (transmission / 1000) + effective_excluding

        await ctx.send(
            f"```ahk\nTransmission Time: {transmission}μs\n"
            f"Propagation Time: {propagation}ms\n"
            f"Effective Data Rate: {effective}Mb/s "
            f"({effective_excluding}Mb/s excluding transmission)```"
        )

    @prop.error
    async def prop_error_handler(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.dark_red(),
                    description=(
                        f"```properties\nUsage:\n{ctx.prefix}"
                        "prop <data_rate> <length> <speed> <frame_size>\n\n"
                        f"Example:\n{ctx.prefix}prop 1000Mb 800km 200000km/s 10000\n\n"
                        "data_rate: bits per second\n"
                        "length: cable length in km\n"
                        "speed: speed of light in cable\n"
                        "frame_size: frame size in bytes```"
                    ),
                )
            )

    @commands.command()
    async def network(self, ctx, ip):
        net = ipaddress.ip_network(ip, False)

        def dotted(ip):
            return ".".join([format(chunk, "08b") for chunk in ip.packed])

        network_address = net.network_address
        netmask = net.netmask
        hostmask = net.hostmask
        broadcast_address = net.broadcast_address
        max_address = net[-2]
        min_address = net[1]

        # Due to the IPv4Address not having an __format__ method for padding they need to be converted to strings first
        await ctx.send(
            f"```ahk\nNetwork Address: {str(network_address):<22}; {dotted(network_address)}\n"
            f"Network Mask: {str(netmask):<25}; {dotted(netmask)}\n"
            f"Host Mask: {str(hostmask):<28}; {dotted(hostmask)}\n"
            f"Broadcast Address: {str(broadcast_address):<20}; {dotted(broadcast_address)}\n"
            f"Max Address: {str(max_address):<26}; {dotted(max_address)}\n"
            f"Min Address: {str(min_address):<26}; {dotted(min_address)}\n"
            f"Total Addresses: {net.num_addresses} ({net.num_addresses - 2})```"
        )

    @commands.command()
    async def ip(self, ctx, ip):
        """Convert ip to binary and vice versa.

        ip: str
        """
        if "." in ip:
            binary = "```ahk\n{:08b}{:08b}{:08b}{:08b}```".format(
                *map(int, ip.split("."))
            )
            return await ctx.send(binary)

        network_a, network_b, host_a, host_b = (
            int(ip[:8], 2),
            int(ip[8:16], 2),
            int(ip[16:24], 2),
            int(ip[24:], 2),
        )
        return await ctx.send(f"```ahk\n{network_a}.{network_b}.{host_a}.{host_b}```")

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
                f"```py\n{expr}\n\n>>> {method(result)}\n\nDecimal: {result}```"
            )
            return await ctx.send(embed=embed)

        embed.description = f"```py\n{expr}\n\n>>> {result}```"
        await ctx.send(embed=embed)

    @commands.command(aliases=["r"])
    async def run(self, ctx, *, code=None):
        """Runs code.

        Examples:
        .run `\u200b`\u200b`\u200bpy
        print("Example")`\u200b`\u200b`\u200b

        .run py print("Example")

        .run py `\u200bprint("Example")`\u200b

        .run py `\u200b`\u200b`\u200bprint("Example")`\u200b`\u200b`\u200b
        """
        if ctx.message.attachments:
            file = ctx.message.attachments[0]
            lang = file.filename.split(".")[-1]
            code = (await file.read()).decode()
        elif not code:
            return await ctx.send_help(ctx.command)
        elif match := list(CODE_REGEX.finditer(code)):
            code, lang, alang = match[0].group("code", "lang", "alang")
            lang = lang or alang
        elif match := list(RAW_CODE_REGEX.finditer(code)):
            code, lang = match[0].group("code", "lang")

        if not lang:
            return await ctx.send_help(ctx.command)

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

        output = data["run"]["output"].strip()

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
            url, data=data, timeout=15
        ) as resp:
            output = (await resp.read()).decode("utf-8")
            output = output.replace(output[:16], "")

        await ctx.reply(f"```{lang}\n{output}```")

    @commands.command()
    async def tiolanguages(self, ctx):
        """Shows all the languages that tio.run can handle."""
        languages = orjson.loads(self.DB.main.get(b"tiolanguages"))

        messages = []
        message = ""
        count = 1

        for language in sorted(languages):
            if count % 2 == 0:
                message += f"{language}\n"
            else:
                message += f"{language:<26}"

            count += 1

            if count == 61:
                messages.append(discord.Embed(description=f"```{message}```"))
                message = ""
                count = 1

        if count != 61:
            messages.append(discord.Embed(description=f"```{message}```"))

        paginator = pages.Paginator(pages=messages)
        await paginator.send(ctx)

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

        [Compsci 210](https://notes.joewuthrich.com/compsci210)
        An introduction to computer organisation, programming in the LC3 assembly language and C.

        [Compsci 215](https://notes.joewuthrich.com/compsci215)
        An introduction to data communications and security.

        [Compsci 220](https://notes.joewuthrich.com/compsci220)
        An introduction to the analysis of algorithms and data structures.

        [Compsci 225](https://notes.joewuthrich.com/compsci225)
        Discrete Structures in Mathematics and Computer Science.

        [Compsci 230](https://notes.joewuthrich.com/compsci230)
        An introduction to object-oriented coding in Java.

        [Compsci 235](https://notes.joewuthrich.com/compsci235)
        Software design methodologies to structure the process of developing software.

        [Compsci 320](https://notes.joewuthrich.com/compsci320)
        Fundamental design techniques used for efficient algorithmic problem-solving.

        [Compsci 335](https://notes.joewuthrich.com/compsci335)
        Web application development.

        [Compsci 340](https://notes.joewuthrich.com/compsci340)
        Operating system principles.
        """
        await ctx.send(embed=embed)

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

        bin_exponent = 0
        shifted_num = number

        while shifted_num != int(shifted_num):
            shifted_num *= 2
            bin_exponent += 1

        if not bin_exponent:
            binary = standard = f"{int(number):b}"
        else:
            standard = f"{int(shifted_num):0{bin_exponent + 1}b}"
            binary = (
                f"{standard[:-bin_exponent]}.{standard[-bin_exponent:].rstrip('0')}"
            )

        binary = binary[: max(binary.find("1") + 1, 12)]

        embed = discord.Embed(color=discord.Color.blurple())
        embed.add_field(name="Decimal", value=number)
        embed.add_field(
            name="Binary",
            value=binary,
        )
        embed.add_field(name="\u200b", value="\u200b")
        embed.add_field(
            name="Standard Form", value=f"{standard.lstrip('0')[:9]:0>9} x 2^{exponent}"
        )
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

    @_float.command(name="decode", aliases=["d"])
    async def _decode(self, ctx, number):
        """Decodes a float from the half-precision floating-point format.

        number: str
        """
        number = int(number, 16)

        sign = (number & 32768) >> 15
        mantissa = (number & 32704) >> 6
        exponent_sign = (number & 32) >> 5
        exponent = number & 31
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

    @commands.command(name="hex")
    async def _hex(self, ctx, number):
        """Shows a number in hexadecimal prefixed with “0x”.

        number: str
            The number you want to convert.
        """
        try:
            hexadecimal = hex_float(float(number))
        except (ValueError, OverflowError):
            hexadecimal = "failed"
        try:
            decimal = int(number, 16)
        except ValueError:
            decimal = "failed"

        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                description=f"```py\nhex: {hexadecimal}\nint: {decimal}```",
            )
        )

    @commands.command(name="oct")
    async def _oct(self, ctx, number):
        """Shows a number in octal prefixed with “0o”.

        number: str
            The number you want to convert.
        """
        try:
            octal = oct_float(float(number))
        except (ValueError, OverflowError):
            octal = "failed"
        try:
            decimal = int(number, 8)
        except ValueError:
            decimal = "failed"

        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                description=f"```py\noct: {octal}\nint: {decimal}```",
            )
        )

    @commands.command(name="bin")
    async def _bin(self, ctx, number):
        """Shows a number in binary prefixed with “0b”.

        number: str
            The number you want to convert.
        """
        try:
            binary = bin_float(float(number))
        except (ValueError, OverflowError):
            binary = "failed"

        whole, *frac = number.split(".")
        try:
            decimal = int(whole, 2)

            if frac:
                for i, digit in enumerate(frac[0], start=1):
                    if digit == "1":
                        decimal += 0.5**i
                    elif digit != "0":
                        decimal = "failed"
                        break
        except ValueError:
            decimal = "failed"

        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                description=f"```py\nbin: {binary}\nint: {decimal}```",
            )
        )

    @commands.group()
    async def caesar(self, ctx):
        """Solves or encodes a caesar cipher."""
        if not ctx.invoked_subcommand:
            embed = discord.Embed(
                color=discord.Color.blurple(),
                description=f"```Usage: {ctx.prefix}caesar [decode/encode]```",
            )
            await ctx.reply(embed=embed)

    @caesar.command(name="encode")
    async def caesar_encode(self, ctx, shift: int, *, message):
        """Encodes a message using the caesar cipher.

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

        await ctx.reply(message.translate(table))

    @caesar.command(name="decode", aliases=["solve", "brute"])
    async def caesar_decode(self, ctx, *, message):
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
            "a": 8.167, "b": 1.492, "c": 2.782, "d": 4.253,
            "e": 12.702, "f": 2.228, "g": 2.015, "h": 6.094,
            "i": 6.966, "j": 0.153, "k": 0.772, "l": 4.025,
            "m": 2.406, "n": 6.749, "o": 7.507, "p": 1.929,
            "q": 0.095, "r": 5.987, "s": 6.327, "t": 9.056,
            "u": 2.758, "v": 0.978, "w": 2.360, "x": 0.150,
            "y": 1.974, "z": 0.074,
        }

        # fmt: on

        msg_len = len(message)

        rotate_one = str.maketrans(chars, chars[1:] + chars[0])
        embed = discord.Embed(color=discord.Color.blurple())

        results = []
        counts = {}

        # Gets the count of each letter
        for letter in message.lower():
            counts[letter] = counts.get(letter, 0) + 1

        for i in range(25, 0, -1):
            message = message.translate(rotate_one)
            chi = 0
            for char in set(message.lower()):
                frequency = freq.get(char)
                if frequency:
                    chi += (
                        ((counts.get(char, 0) / msg_len) - frequency) ** 2
                    ) / frequency
            results.append((chi, (i, message)))

        for chi, result in sorted(results, reverse=True):
            embed.add_field(name=result[0], value=result[1])

        embed.set_footer(text="Sorted by the chi-square of their letter frequencies")

        await ctx.reply(embed=embed)

    @commands.command()
    async def block(self, ctx, A, B):
        """Solves a block cipher in the format of a python matrix.

        e.g
        "1 2 3" "3 7 15, 6 2 61, 2 5 1"

        A: str
        B: str
        """

        def starmap(iterable):
            for num1, num2 in iterable:
                yield num1 * num2

        if A > "a":
            A = [[ord(letter) - 97 for letter in A]]
        else:
            A = A.split(",")
            A = [[int(num) for num in block.split()] for block in A]
        B = B.split(",")
        B = [[int(num) for num in block.split()] for block in B]

        results = ""

        for block in A:
            results += f"{[sum(starmap(zip(block, col))) for col in zip(*B)]}\n"

        embed = discord.Embed(
            color=discord.Color.blurple(), description=f"```{results}```"
        )
        await ctx.send(embed=embed)

    @commands.group()
    async def binary(self, ctx):
        """Encoded or decodes binary as ascii text."""
        if not ctx.invoked_subcommand:
            embed = discord.Embed(
                color=discord.Color.blurple(),
                description=f"```Usage: {ctx.prefix}binary [decode/encode]```",
            )
            await ctx.reply(embed=embed)

    @binary.command(name="encode", aliases=["en"])
    async def binary_encode(self, ctx, *, text):
        """Encodes ascii text as binary.

        text: str
        """
        await ctx.reply(
            "```less\n{}```".format(
                " ".join([f"{bin(ord(letter))[2:]:0>8}" for letter in text])
            )
        )

    @binary.command(name="decode", aliases=["de"])
    async def binary_decode(self, ctx, *, binary):
        """Decodes binary as ascii text.

        binary: str
        """
        binary = binary.replace(" ", "")
        await ctx.reply(
            "".join([chr(int(binary[i : i + 8], 2)) for i in range(0, len(binary), 8)])
        )

    @commands.command()
    async def ones(self, ctx, number: int, bits: int):
        """Converts a decimal number to binary ones complement.

        number: int
        """
        table = {49: "0", 48: "1"}
        sign = 1 - (number >= 0)
        return await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                description=f"```{sign}{f'{abs(number):0>{bits-1}b}'.translate(table)}```",
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
                description=f"```{number & (2 ** bits - 1):0>{bits}b}```",
            )
        )

    @commands.group()
    async def rle(self, ctx):
        """Encodes or decodes a string with run length encoding."""
        if not ctx.invoked_subcommand:
            embed = discord.Embed(
                color=discord.Color.blurple(),
                description=f"```Usage: {ctx.prefix}rle [de/en]```",
            )
            await ctx.reply(embed=embed)

    @rle.command()
    async def en(self, ctx, *, text):
        """Encodes a string with run length encoding."""
        text = re.sub(r"(.)\1*", lambda m: m.group(1) + str(len(m.group(0))), text)
        await ctx.reply(text)

    @rle.command()
    async def de(self, ctx, *, text):
        """Decodes a string with run length encoding."""
        text = re.sub(r"(\D)(\d+)", lambda m: int(m.group(2)) * m.group(1), text)
        await ctx.reply(text)

    @commands.command(aliases=["ch", "rust", "java"])
    async def cheatsheet(self, ctx, *search):
        """https://cheat.sh/python/ gets a cheatsheet.

        search: tuple
            The search terms.
        """
        search = "+".join(search)
        language = (
            "python" if ctx.invoked_with in ("ch", "cheatsheet") else ctx.invoked_with
        )

        url = f"https://cheat.sh/{language}/{search}"
        headers = {"User-Agent": "curl/7.68.0"}

        async with ctx.typing(), self.bot.client_session.get(
            url, headers=headers
        ) as page:
            result = ANSI.sub("", await page.text()).translate({96: "\\`"})

        embed = discord.Embed(
            title=url,
            color=discord.Color.blurple(),
            description=f"```{language}\n{result}```",
        )

        await ctx.send(embed=embed)

    @commands.command()
    async def truth(self, ctx, *, expr):
        """Converts a proposition to a truth table.

        example usage:
            .truth A => B

        expr: str
        """
        letters = []
        table = {}

        for letter in expr:
            if letter.isalpha() and letter not in letters:
                letters.append(letter)
                table[ord(letter)] = f"{{{letter}}}"

        count = len(letters)

        if count > 6:
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    title=f"More than 6 variables ({count})",
                ).set_footer(
                    text="Having more than 6 variables would make the table too large to send"
                )
            )

        letters.sort()

        total = 2**count
        checks = [list(f"{num:0>{count}b}") for num in range(total)]

        # ⇒ | (not A) or B
        # ↔ | A == B
        # ∧ | A and B
        # ∨ | A or B
        # ~ | not (A)
        table.update(
            {
                8658: " @ ",  # ⇒
                8594: " @ ",  # →
                8596: " == ",  # ↔
                8743: " and ",  # ∧
                8744: " or ",  # ∨
                172: "not ",  # ¬
                126: "not ",  # ~
            }
        )
        expr = expr.replace("<=>", " == ").replace("=>", " @ ").translate(table)

        message = ("| {} " * count).format(*letters) + f"|\n{'_' * ((count * 4) + 1)}\n"

        for check in checks:
            result = safe_eval(
                compile(
                    expr.format(**dict(zip(letters, check))),
                    "<calc>",
                    "eval",
                    flags=1024,
                ).body
            )
            message += (("| {} " * count) + "| {}").format(*check, int(result)) + "\n"

        await ctx.send(f"```hs\n{message}```")


def setup(bot: commands.Bot) -> None:
    """Starts the compsci cog."""
    bot.add_cog(compsci(bot))
