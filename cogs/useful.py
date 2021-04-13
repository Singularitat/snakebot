import discord
from discord.ext import commands, menus
import ujson
import random
import aiohttp
import time
import lxml.html
import re


class InviteMenu(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=20)

    async def format_page(self, menu, entries):
        msg = ""
        embed = discord.Embed(color=discord.Color.blurple())

        if entries == []:
            embed.description = "```No stored information found```"
            return embed

        for member, invite in entries:
            if len(member) <= 18:
                name = self.bot.get_user(int(member)).display_name
                msg += f"{name}: {invite.decode()}\n"
        embed.description = f"```{msg}```"
        return embed


class useful(commands.Cog):
    """Actually useful commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.invites = self.bot.db.prefixed_db(b"invites-")

    @commands.command()
    async def emoji(self, ctx, *, name):
        """Does an emoji submission automatically.

        To use this command attach an image and put
        ".emoji [name]" as the comment

        name: str
            The emoji name. Must be at least 2 characters."""
        if len(name) < 2:
            return await ctx.send("```Name has to be at least 2 characters```")

        if discord.utils.get(ctx.guild.emojis, name=name):
            return await ctx.send("```An emoji already exists with that name```")

        if len(ctx.message.attachments) == 0:
            return await ctx.send(
                "```You need to attach the emoji image to the message```"
            )
        emojis = self.bot.db.get(b"emoji_submissions")

        if not emojis:
            emojis = {}
        else:
            emojis = ujson.loads(emojis)

        emojis[ctx.message.id] = {}
        emojis[ctx.message.id]["name"] = name
        emojis[ctx.message.id]["users"] = []

        self.bot.db.delete(b"emoji_submissions")
        self.bot.db.put(b"emoji_submissions", ujson.dumps(emojis).encode())

    @commands.command()
    async def invites(self, ctx):
        """Shows the invites that users joined from."""
        pages = menus.MenuPages(
            source=InviteMenu(list(self.invites)), clear_reactions_after=True
        )
        await pages.start(ctx)

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

        if len("```\n{r['output']}```") > 2000:
            return await ctx.send(f"```\n{r['output'][:1975]}\nTruncated Output```")

        await ctx.send(f"```\n{r['output']}```")

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
        message = self.bot.db.get(b"snipe_message")

        if message is not None:
            message = ujson.loads(message)

            # Example, ["Yeah I deleted this", "Singulaity"]
            await ctx.send(f"```{message[1]} deleted:\n{message[0]}```")

    @commands.command()
    async def editsnipe(self, ctx):
        """Snipes the last edited message."""
        message = self.bot.db.get(b"editsnipe_message")

        if message is not None:
            message = ujson.loads(message)
            await ctx.send(f"```{message[2]} edited:\n{message[0]} >>> {message[1]}```")

    @commands.command(aliases=["dir"])
    async def _dir(self, ctx, obj, arg, *, attr=None):
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

        if obj not in objects:
            return await ctx.send("```Could not find object```")

        try:
            obj = await objects[obj].convert(ctx, arg)
        except commands.BadArgument:
            return await ctx.send("```Conversion failed```")

        if attr:
            attributes = attr.split(".")
            try:
                for attribute in attributes:
                    obj = getattr(obj, attribute)
            except AttributeError:
                return await ctx.send(f"{obj} has no attribute {attribute}")
            return await ctx.send(f"```{obj}\n\n{dir(obj)}```")

        await ctx.send(f"```{obj}\n\n{dir(obj)}```")

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

        if images == []:
            return await ctx.send("```No images found```")

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

        async with aiohttp.ClientSession(headers=headers) as session, session.get(
            url
        ) as page:
            result = ansi.sub("", await page.text()).translate(escape)

        embed = discord.Embed(
            title=f"https://cheat.sh/python/{search}", color=discord.Color.blurple()
        )
        embed.description = f"```py\n{result}```"

        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    """Starts useful cog."""
    bot.add_cog(useful(bot))
