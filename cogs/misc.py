import io
import random
import re
import unicodedata
from datetime import datetime

import discord
import lxml.html
import opcode
import orjson
from discord.ext import commands, pages

from cogs.utils.color import hsslv
from cogs.utils.time import parse_date

try:
    from cogs.utils.oneliner import onelinerize
except ImportError:
    onelinerize = None

CHARACTERS = (
    # Portal
    "GLaDOS",
    "Wheatley",
    "Sentry Turret",
    "Chell",
    # SpongeBob
    "SpongeBob SquarePants",
    # Daria
    "Daria Morgendorffer",
    "Jane Lane",
    # Aqua Teen Hunger Force
    "Carl Brutananadilewski",
    # Team Fortress 2
    "Miss Pauling",
    "Scout",
    "Soldier",
    "Demoman",
    "Heavy",
    "Engineer",
    "Medic",
    "Sniper",
    "Spy",
    # Persona 4
    "Rise Kujikawa",
    # Steven Universe
    "Steven Universe",
    # Dan Vs.
    "Dan",
    # The Stanley Parable
    "Stanley",
    "The Narrator",
    # 2001: A Space Odyssey
    "HAL 9000",
    # Doctor Who
    "Tenth Doctor",
    # Sans
    "Sans",
    "Papyrus",
    "Flowey",
    "Toriel",
    "Asgore",
    "Asriel",
    "Alphys",
    "Undyne",
    "Mettaton",
    "Temmie",
    "Susie",
    "Noelle",
    "Berdly",
    "Rudolph",
    "Ralsei",
    "Lancer",
    "King",
    "Queen",
    "Jevil",
    "Spamton",
    "Gaster",
)

ALT_NAMES = {
    "Glados": "GLaDOS",
    "Sentry": "Sentry Turret",
    "Spongebob": "SpongeBob SquarePants",
    "Spongebob Squarepants": "SpongeBob SquarePants",
    "Daria": "Daria Morgendorffer",
    "Jane": "Jane Lane",
    "Carl": "Carl Brutananadilewski",
    "Pauling": "Miss Pauling",
    "Rise": "Rise Kujikawa",
    "Steven": "Steven Universe",
    "Narrator": "The Narrator",
    "Hal": "HAL 9000",
    "Hal 9000": "HAL 9000",
    "Tenth": "Tenth Doctor",
    "Doctor": "Tenth Doctor",
}

opcodes = opcode.opmap


class misc(commands.Cog):
    """Commands that don't fit into other cogs."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.DB = bot.DB

    @commands.command()
    async def solved(self, ctx: commands.Context):
        """Marks a thread in the help forum as solved."""
        if not isinstance(ctx.channel, discord.Thread):
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(), title="This is not in a thread"
                )
            )

        if ctx.channel.id != 1019979153589670010:
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(), title="This is not in the help forum"
                )
            )

        if ctx.channel.owner_id != ctx.author.id:
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    title="You are not the Orginal Poster of this thread",
                )
            )

        try:
            await ctx.message.add_reaction("✅")
        except (discord.HTTPException, discord.Forbidden):
            pass
        await ctx.channel.edit(
            locked=True,
            archived=True,
            reason=f"Marked as solved ({ctx.author} {ctx.author.id})",
        )

    @commands.command()
    async def emoji(self, ctx, emoji: discord.Emoji):
        """Gets the url to the image of an emoji."""
        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(), title="Image link", url=emoji.url
            ).set_image(url=emoji.url)
        )

    @commands.command()
    async def oneline(self, ctx, *, code=None):
        """Convert python 3 code into one line.

        code: str
        """
        if not onelinerize:
            return

        if not code and ctx.message.attachments:
            file = ctx.message.attachments[0]
            if file.filename.split(".")[-1] != "py":
                return
            code = (await file.read()).decode()

        code = re.sub(r"```\w+\n|```", "", code)
        code = await self.bot.loop.run_in_executor(None, onelinerize, code)

        if len(code) > 1991:
            return await ctx.reply(file=discord.File(io.StringIO(code), "output.py"))

        code = code.replace("`", "`\u200b")
        await ctx.reply(f"```py\n{code}```")

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
        if len(text) > 271:
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
            "autoit",
            "basic",
            "fs",
            "gs",
            "haml",
            "hs",
            "hsp",
            "isbl",
            "julia",
            "ldif",
            "less",
            "llvm",
            "mk",
            "wl",
            "nginx",
            "properties",
            "rb",
            "rs",
        )

        embeds = [embed]

        for lang in languages[:21]:
            embed.add_field(name=lang, value=f"```{lang}\n{text}```")

        embed = discord.Embed(color=discord.Color.blurple())

        for lang in languages[21:]:
            embed.add_field(name=lang, value=f"```{lang}\n{text}```")

        embeds.append(embed)

        paginator = pages.Paginator(pages=embeds, use_default_buttons=False)
        paginator.add_button(
            pages.PaginatorButton("prev", label="<", style=discord.ButtonStyle.green)
        )
        paginator.add_button(
            pages.PaginatorButton(
                "page_indicator", style=discord.ButtonStyle.gray, disabled=True
            )
        )
        paginator.add_button(
            pages.PaginatorButton("next", label=">", style=discord.ButtonStyle.green)
        )
        await paginator.send(ctx)

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
                    f"and shorter than 200 characters[{length}]```",
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
    async def rate(self, ctx, user: discord.User = None):
        """Rates users out of 100.

        Results are not endorsed by Snake Bot

        user: discord.User
            Defaults to author.
        """
        user = user or ctx.author
        num = random.Random(user.id ^ 1970636).randint(0, 100)

        await ctx.reply(
            f"{user.mention} is a {num} out of 100",
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

        await ctx.reply(
            f"{user1.mention} is a {perc}% match with {user2.mention}",
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @commands.command(aliases=["ejson", "json"])
    async def embedjson(self, ctx, message: discord.Message = None):
        """Converts the embed of a message to json.

        message: discord.Message
        """
        if not message and ctx.message.reference:
            message = ctx.message.reference.resolved

        embed = discord.Embed(color=discord.Color.blurple())

        if not message:
            embed.title = "You need to reply to message or supply an id as an argument"
            embed.color = discord.Color.dark_red()
            return await ctx.send(embed=embed)

        if not message.embeds:
            embed.title = "Message has no embeds"
            embed.color = discord.Color.dark_red()
            return await ctx.send(embed=embed)

        message_embed = message.embeds[0]

        json = (
            str(message_embed.to_dict())
            .replace("'", '"')
            .replace('"inline": True', '"inline": true')
            .replace('"inline": False', '"inline": false')
            .replace("`", "`\u200b")
        )

        if len(json) > 2000:
            return await ctx.send(file=discord.File(io.StringIO(json), "embed.json"))

        embed.description = f"```json\n{json}```"
        await ctx.send(embed=embed)

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

        color = "32" if int(karma) > 0 else "31"

        embed = discord.Embed(color=0x0)

        embed.description = f"```ansi\n[2;34m{user.display_name}[0m's karma: [2;{color}m{karma}[0m```"
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
                color = "32" if int(karma) > 0 else "31"
                lst.append(f"[2;34m{member}[0m: [2;{color}m{karma}[0m")
            return lst

        embed.add_field(
            name="Top Five",
            value="```ansi\n{}```".format("\n".join(parse_karma(sorted_karma[:5]))),
        )
        embed.add_field(
            name="Bottom Five",
            value="```ansi\n{}```".format("\n".join(parse_karma(sorted_karma[-5:]))),
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
            async with self.bot.client_session.get(url) as resp:
                text = lxml.html.fromstring(await resp.text())

                if resp.status != 200:
                    embed.description = f"```Could not find and an element with the symbol {element.upper()}```"
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
        """Chooses between multiple things.

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


def setup(bot: commands.Bot) -> None:
    """Starts misc cog."""
    bot.add_cog(misc(bot))
