import discord
from discord.ext import commands
import ujson
import random
import aiohttp
import time
import lxml.html
import re


class useful(commands.Cog):
    """Actually useful commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command()
    async def run(self, ctx, lang, *, code):
        """Runs code.

        lang: str
            The programming language.
        code: str
            The code to run.
        """
        if lang not in ujson.loads(self.bot.db.get(b"languages")):
            return await ctx.send(f"No support for language {lang}")

        code = re.sub(r"```\w+\n|```", "", code)

        data = {"language": lang, "source": code, "args": "", "stdin": "", "log": 0}

        async with aiohttp.ClientSession() as session, session.post(
            "https://emkc.org/api/v1/piston/execute", data=ujson.dumps(data)
        ) as response:
            r = await response.json()

        if not r["output"]:
            return await ctx.send("No output")

        await ctx.send(f"```{r['output']}```")

    @run.error
    async def run_handler(self, ctx, error):
        """Error handler for run command."""
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await ctx.send(
                f"```Usage:\n{ctx.prefix}{ctx.command} {ctx.command.signature}```"
            )

    @commands.command(name="removereact")
    async def _remove_reaction(self, ctx, message: discord.Message, reaction):
        """Removes a reaction from a message.

        message: discord.Message
            The id of the message you want to remove the reaction from.
        reaction: Union[discord.Emoji, str]
            The reaction to remove.
        """
        await message.clear_reaction(reaction)

    @commands.command()
    async def time(self, ctx, *, command):
        """Runs a command whilst timing it.

        command: str
            The command to run including arguments.
        """
        ctx.content = f"{ctx.prefix}{command}"

        ctx = await self.bot.get_context(ctx, cls=type(ctx))

        if ctx.command is None:
            return await ctx.send("```No command found```")

        start = time.time()
        await ctx.command.invoke(ctx)
        await ctx.send(f"`Time: {(time.time() - start) * 1000:.2f}ms`")

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

    @commands.command(aliases=["arg"])
    async def argument(self, ctx, arg, obj, subarg=None):
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
            "text": commands.TextChannelConverter(),
            "voice": commands.VoiceChannelConverter(),
            "category": commands.CategoryChannelConverter(),
            "invite": commands.InviteConverter(),
            "role": commands.RoleConverter(),
            "game": commands.GameConverter(),
            "colour": commands.ColourConverter(),
            "color": commands.ColorConverter(),
            "emoji": commands.EmojiConverter(),
            "partial": commands.PartialEmojiConverter(),
        }
        if obj in objects:
            try:
                obj = await objects[obj].convert(ctx, arg)
            except commands.BadArgument:
                await ctx.send("```Conversion failed```")
            else:
                if subarg:
                    attr = getattr(obj, subarg)
                    await ctx.send(f"```{attr}\n\n{dir(attr)}```")
                else:
                    await ctx.send(f"```{obj}\n\n{dir(obj)}```")
        else:
            await ctx.send("```Could not find object```")

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
        async with aiohttp.ClientSession(headers=headers) as session, session.get(
            url
        ) as page:
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
        async with aiohttp.ClientSession(headers=headers) as session, session.get(
            url
        ) as page:
            soup = lxml.html.fromstring(await page.text())
        images = []
        for a in soup.xpath('.//a[@class="iusc"]'):
            images.append(ujson.loads(a.attrib["m"])["turl"])
        await ctx.send(random.choice(images))

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

        operators = re.sub(r"\d+", "%s", args)
        numbers = re.findall(r"\d+", args)
        numbers = [str(int(num, base)) for num in numbers]

        code = operators % tuple(numbers)

        data = {
            "language": "python",
            "source": f"print(round({code}))",
            "args": "",
            "stdin": "",
            "log": 0,
        }

        async with aiohttp.ClientSession() as session, session.post(
            "https://emkc.org/api/v1/piston/execute", data=ujson.dumps(data)
        ) as response:
            r = await response.json()

        if r["stderr"]:
            return await ctx.send("```Invalid```")

        if num_base.lower() == "hex":
            result = hex(int(r["output"]))
        elif num_base.lower() == "oct":
            result = oct(int(r["output"]))
        elif num_base.lower() == "bin":
            result = bin(int(r["output"]))
        else:
            result = r["output"]

        await ctx.send(
            f"```{num_base.capitalize()}: {result} Decimal: {r['output']}```"
        )


def setup(bot: commands.Bot) -> None:
    """Starts useful cog."""
    bot.add_cog(useful(bot))
