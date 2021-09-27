from io import StringIO
import difflib
import opcode
import random
import re

from discord.ext import commands
import aiohttp
import discord
import lxml.html

import config


opcodes = opcode.opmap


class misc(commands.Cog):
    """Commands that don't fit into other cogs."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.DB = bot.DB

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

        content = re.sub(r"\"\"\"[^\"\"\"]+\"\"\"", "", content)

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
            await ctx.send(embed=embed)

        message_embed = message.embeds[0]

        json = (
            str(message_embed.to_dict())
            .replace("'", '"')
            .replace("True", "true")
            .replace("False", "false")
        )

        if len(json) > 2000:
            return await ctx.send(file=discord.File(StringIO(json), "embed.json"))

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
        text = re.sub(r"(.)\1*", lambda m: str(len(m.group(0))) + m.group(1), text)
        await ctx.send(text)

    @rle.command()
    async def de(self, ctx, *, text):
        """Decodes a string with run length encoding."""
        text = re.sub(r"(\d+)(\D)", lambda m: m.group(2) * int(m.group(1)), text)
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
        table = str.maketrans({"1": "0", "0": "1"})
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

    @commands.command()
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
        await ctx.reply(random.randint(a, b))

    @staticmethod
    def format_op(op):
        return f"{hex(opcodes[op])[2:]:<5}{opcodes[op]:<5}{op}"

    @commands.command()
    async def opcode(self, ctx, search):
        """Gets closest matches for an opcode.

        search: str
        """
        matches = difflib.get_close_matches(
            search.upper(), list(opcodes), cutoff=0, n=5
        )
        msg = "\n".join([self.format_op(match) for match in matches])
        await ctx.send(f"```py\nHex: Num: Name:\n\n{msg}```")

    @commands.group()
    async def binary(self, ctx):
        """Encoded or decodes binary as ascii text."""
        if not ctx.invoked_subcommand:
            embed = discord.Embed(
                color=discord.Color.blurple(),
                description=f"```Usage: {ctx.prefix}binary [decode/encode]```",
            )
            await ctx.send(embed=embed)

    @binary.command(name="encode")
    async def binary_encode(self, ctx, *, text):
        """Encodes ascii text as binary.

        text: str
        """
        await ctx.send(" ".join([f"{bin(ord(letter))[2:]:0>8}" for letter in text]))

    @binary.command(name="decode")
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
        Introduction to programming using the python programming language.
        [Compsci 110](https://notes.joewuthrich.com/compsci110)
        This course explains how computers work and some of the things we can use them for.
        [Compsci 120](https://notes.joewuthrich.com/compsci120)
        Introduces basic mathematical tools and methods needed for computer science.
        [Compsci 130](https://notes.joewuthrich.com/compsci130)
        Entry course to Computer Science for students with prior programming knowledge.
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

    @commands.command()
    @commands.guild_only()
    async def youtube(self, ctx):
        """Starts a YouTube Together."""
        if (code := self.DB.main.get(b"youtube_together")) and discord.utils.get(
            await ctx.guild.invites(), code=code.decode()
        ):
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    title="There is another active Youtube Together",
                    description=f"https://discord.gg/{code.decode()}",
                )
            )

        if not ctx.author.voice:
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description="```You aren't connected to a voice channel.```",
                )
            )

        headers = {"Authorization": f"Bot {config.token}"}
        json = {
            "max_age": 300,
            "target_type": 2,
            "target_application_id": 755600276941176913,
        }

        async with self.bot.client_session.post(
            f"https://discord.com/api/v9/channels/{ctx.author.voice.channel.id}/invites",
            json=json,
            headers=headers,
        ) as response:
            data = await response.json()

        await ctx.send(f"https://discord.gg/{data['code']}")
        self.DB.main.put(b"youtube_together", data["code"].encode())

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
    async def _hex(self, ctx, number, convert: bool = False):
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
        embed.description = f"```{hex(int(number))}```"
        await ctx.send(embed=embed)

    @commands.command(name="oct")
    async def _oct(self, ctx, number, convert: bool = False):
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
        embed.description = f"```{oct(int(number))}```"
        await ctx.send(embed=embed)

    @commands.command(name="bin")
    async def _bin(self, ctx, number, convert: bool = False):
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
        embed.description = f"```{bin(int(number))}```"
        await ctx.send(embed=embed)

    @commands.command()
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

    @commands.command()
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
            return await ctx.send(file=discord.File(StringIO(bar_graph), "bar.txt"))

        await ctx.send(f"```\n{bar_graph}```")


def setup(bot: commands.Bot) -> None:
    """Starts misc cog."""
    bot.add_cog(misc(bot))
