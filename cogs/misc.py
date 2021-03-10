import discord
from discord.ext import commands
import random
import asyncio
import aiohttp
import lxml.html
import config
import ujson
import unicodedata
import re


class misc(commands.Cog):
    """Commands that don't fit into other cogs."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command()
    async def calc(self, ctx, num_base, *, args):
        """Does math.

        num_base: str
            The base you want to calculate in.
        args: str
            A str of arguments to calculate.
        """
        if num_base.lower() == "hex":
            base = 16
        elif num_base.lower() == "oct":
            base = 8
        elif num_base.lower() == "bin":
            base = 2
        else:
            base = int(num_base)

        numbers = re.sub(r'[^\w]', ' ', args)
        operators = re.sub(r'[?!^\w]', ' ', args)
        numbers = [str(int(num, base)) for num in [*filter(None, numbers.split(" "))]]
        operators = [*filter(None, operators.split(" "))]

        code = ""
        for i, num in enumerate(numbers):
            try:
                code += num + operators[i]
            except IndexError:
                code += num

        async with aiohttp.ClientSession() as session:
            data = {"language": "python", "source": f"print({code})", "args": "", "stdin": "", "log": 0}
            async with session.post(
                "https://emkc.org/api/v1/piston/execute", data=ujson.dumps(data)
            ) as response:
                r = await response.json()

        if r['stderr']:
            return await ctx.send("```Invalid```")
        await ctx.send(f"```{num_base.capitalize()}: {hex(int(float(r['output'])))} Decimal: {int(float(r['output']))}```")

    @commands.command(name="hex")
    async def _hex(self, ctx, number, convert: bool = False):
        """Shows a number in hexadecimal prefixed with “0x”.

        number: str
            The number you want to convert.
        convert: bool
            If you want to convert to decimal or not
        """
        if convert:
            return await ctx.send(f"```{int(number, 16)}```")
        await ctx.send(f"```{hex(int(number))}```")

    @commands.command(name="oct")
    async def _oct(self, ctx, number, convert: bool = False):
        """Shows a number in octal prefixed with “0o”.

        number: str
            The number you want to convert.
        convert: bool
            If you want to convert to decimal or not
        """
        if convert:
            return await ctx.send(f"```{int(number, 8)}```")
        await ctx.send(f"```{oct(int(number))}```")

    @commands.command(name="bin")
    async def _bin(self, ctx, number, convert: bool = False):
        """Shows a number in binary prefixed with “0b”.

        number: str
            The number you want to convert.
        convert: bool
            If you want to convert to decimal or not
        """
        if convert:
            return await ctx.send(f"```{int(number, 2)}```")
        await ctx.send(f"```{bin(int(number))}```")

    @commands.command()
    async def char(self, ctx, char: str, number: int = 26):
        """Sends the characters that come after a character in unicode.

        char: str
            The character to find the following unicode characters of.
        number: int
            The number of characters to find.
        """
        await ctx.send("".join(chr(ord(char) + i) for i in range(number)))

    @commands.command()
    async def charinfo(self, ctx, *, characters: str):
        """Shows you information about a number of characters.

        Only up to 25 characters at a time.

        characters: str
            The characters to find information about.
        """

        def to_string(c):
            digit = f"{ord(c):x}"
            name = unicodedata.name(c, "Name not found.")
            return f"`\\U{digit:>08}`: {name} - {c} \N{EM DASH} <http://www.fileformat.info/info/unicode/char/{digit}>"

        msg = "\n".join(map(to_string, characters))
        if len(msg) > 2000:
            return await ctx.send("Output too long to display.")
        await ctx.send(msg)

    @commands.command()
    async def karma(self, ctx, member: discord.Member = None):
        """Gets a members karma.

        member: discord.Member
            A member whos karma will be returned.
        """
        with open("json/real.json") as file:
            data = ujson.load(file)
        if not member:
            member = ctx.author
        if str(member.id) not in data["karma"]:
            data["karma"][str(member.id)] = 0
        embed = discord.Embed(
            color=discord.Color.blue(),
        )
        embed.add_field(
            name=f"{member}'s karma: ",
            value=f"{data['karma'][str(member.id)]}",
        )
        await ctx.send(embed=embed)
        with open("json/real.json", "w") as file:
            data = ujson.dump(data, file, indent=2)

    @commands.command(aliases=["element"])
    async def atom(self, ctx, element):
        """Displays information for a given atom.

        element: str
            The symbol of the element to search for.
        """
        url = f"http://www.chemicalelements.com/elements/{element.lower()}.html"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.67 Safari/537.36"
        }
        try:
            async with aiohttp.ClientSession(
                headers=headers, raise_for_status=True
            ) as session:
                async with session.get(url) as page:
                    text = lxml.html.fromstring(await page.text())
        except aiohttp.client_exceptions.ClientResponseError:
            await ctx.send(
                f"Could not find and element with the symbol {element.upper()}"
            )
            return
        image = f"http://www.chemicalelements.com{text.xpath('.//img')[1].attrib['src'][2:]}"
        text = text.xpath("//text()")[108:]

        embed = discord.Embed(title=text[1], colour=0x33CC82, type="rich")
        embed.set_thumbnail(url=image)
        embed.add_field(name="Name", value=text[text.index("Name:") + 1])
        embed.add_field(name="Symbol", value=text[text.index("Symbol:") + 1])
        embed.add_field(
            name="Atomic Number", value=text[text.index("Atomic Number:") + 1]
        )
        embed.add_field(name="Atomic Mass", value=text[text.index("Atomic Mass:") + 1])
        embed.add_field(
            name="Neutrons", value=text[text.index("Number of Neutrons:") + 1]
        )
        embed.add_field(name="Color", value=text[text.index("Color:") + 1])
        embed.add_field(name="Uses", value=text[text.index("Uses:") + 1])
        embed.add_field(
            name="Year of Discovery", value=text[text.index("Date of Discovery:") + 1]
        )
        embed.add_field(name="Discoverer", value=text[text.index("Discoverer:") + 1])

        await ctx.send(embed=embed)

    @commands.command()
    async def invite(self, ctx):
        """Sends the invite link of the bot."""
        perms = discord.Permissions.all()
        await ctx.send(f"<{discord.utils.oauth_url(self.bot.client_id, perms)}>")

    @commands.command()
    async def avatar(self, ctx, member: discord.Member):
        """Sends a members avatar url.

        member: discord.Member
            The member to show the avatar of.
        """
        await ctx.send(member.avatar_url)

    @commands.command()
    async def hug(self, ctx, *, search="hug"):
        """Gets a random gif from tenor defaulting to a hug gif.

        search: str
            The gif search term.
        """
        url = f"https://g.tenor.com/v1/search?q={search}&key={config.tenor}&limit=50"
        async with aiohttp.ClientSession() as session:
            raw_response = await session.get(url)
            response = await raw_response.text()
        tenor = ujson.loads(response)
        await ctx.send(random.choice(tenor["results"])["media"][0]["gif"]["url"])

    @commands.command()
    async def send(self, ctx, member: discord.Member, *, message):
        """Gets Snakebot to send a DM to member.

        member: discord.Member
            The member to DM.
        message: str
            The message to be sent.
        """
        try:
            await member.send(message)
            await ctx.send(f"Sent message to {member}")
        except discord.errors.Forbidden:
            await ctx.send(f"{member} has DMs disabled for non-friends")

    @commands.command()
    async def roll(self, ctx, dice: str):
        """Rolls dice in AdX format. A is number of dice, X is number of faces.

        dice: str
            The dice to roll in AdX format.
        """
        try:
            rolls, limit = map(int, dice.split("d"))
        except ValueError:
            await ctx.send("Format has to be AdX")
            return
        result = ", ".join(str(random.randint(1, limit)) for r in range(rolls))
        total = sum([int(item) for item in result.split(", ")])
        await ctx.send(f"Results: {result} Total: {total}")

    @commands.command()
    async def choose(self, ctx, *options: str):
        """Chooses between mulitple things.

        options: str
            The options to choose from.
        """
        await ctx.send(random.choice(options))

    @commands.command()
    async def yeah(self, ctx):
        """Oh yeah its all coming together."""
        await ctx.send("Oh yeah its all coming together")

    @commands.command()
    async def delay(self, ctx, time, *, message):
        """Sends a message after a delay.

        time: str
            The amount of time in seconds or minutes e.g 60 or 1m.
        message: str
            The message to be sent.
        """
        if time[-1] == "m":
            time = float(time[:-1])
            time *= 60
        time = float(time)
        await asyncio.sleep(time)
        await ctx.send(embed=discord.Embed(title=message))

    @commands.command()
    async def slap(self, ctx, member: discord.Member, *, reason):
        """Slaps a member.

        member: discord.Member
            The member to slap.
        reason: str
            The reason for the slap.
        """
        await ctx.send(
            f"{ctx.message.author.mention} slapped {member} because {reason}"
        )

    @commands.command()
    async def bar(self, ctx, graph_data: commands.Greedy[int] = None):
        """Sends a bar graph based of inputted numbers.

        e.g: bar 1 2 3

        graph_data: commands.Greedy[int]
            A list of graph_data
        """
        max_val = max(graph_data)
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
        await ctx.send(f"```{bar_graph}```")


def setup(bot: commands.Bot) -> None:
    """Starts misc cog."""
    bot.add_cog(misc(bot))
