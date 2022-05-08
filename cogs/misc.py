import io
import math
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

    @commands.command(aliases=["tboard"])
    async def triviaboard(self, ctx):
        """Shows the top 10 trivia players."""
        users = []
        for user, stats in self.DB.trivia_wins:
            wins, losses = map(int, stats.decode().split(":"))
            user = self.bot.get_user(int(user.decode()))
            if not user:
                continue
            win_rate = (wins / (wins + losses)) * 100
            users.append((wins, losses, win_rate, user.display_name))

        users.sort(reverse=True)
        top_users = []

        for wins, losses, win_rate, user in users[:10]:
            top_users.append(f"{user:<20} {wins:>5} | {losses:<7}| {win_rate:.2f}%")

        embed = discord.Embed(
            color=discord.Color.blurple(), title=f"Top {len(top_users)} Trivia Players"
        )
        embed.description = (
            "```\n                      wins | losses | win rate\n{}```"
        ).format("\n".join(top_users))

        await ctx.send(embed=embed)

    @commands.command(aliases=["tstats"])
    async def triviastats(self, ctx, user: discord.User = None):
        """Shows the trivia stats of a user.

        user: discord.User
            The user to show the stats of.
        """
        user = user or ctx.author
        key = str(user.id).encode()
        embed = discord.Embed(color=discord.Color.blurple())

        stats = self.DB.trivia_wins.get(key)

        if not stats:
            embed.title = "You haven't played trivia yet"
            return await ctx.send(embed=embed)

        wins, losses = map(int, stats.decode().split(":"))

        embed.title = f"{user.display_name}'s Trivia Stats"
        embed.description = (
            f"**Win Rate:** {(wins / (wins + losses)) * 100:.2f}%\n"
            f"**Wins:** {wins}\n"
            f"**Losses:** {losses}"
        )

        await ctx.send(embed=embed)

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

        await ctx.reply(
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

        await ctx.reply(
            f"{user1.mention} is a {perc}% match with {user2.mention}",
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @commands.command()
    async def embedjson(self, ctx, message: discord.Message = None):
        """Converts the embed of a message to json.

        message: discord.Message
        """
        if not message and ctx.message.reference:
            message = ctx.message.reference.resolved

        embed = discord.Embed(color=discord.Color.blurple())

        if not message or not message.embeds:
            embed.description = "```Message has no embed```"
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
    async def rand(self, ctx, a: int, b: int):
        """Gets a random number such that a <= N <= b"""
        if a > b:
            a, b = b, a
        await ctx.reply(random.randint(a, b))

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

        prefix = "+" if int(karma) > 0 else ""

        embed = discord.Embed(color=discord.Color.blurple())
        embed.description = f"```diff\n{user.display_name}'s karma:\n{prefix}{karma}```"
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


def setup(bot: commands.Bot) -> None:
    """Starts misc cog."""
    bot.add_cog(misc(bot))
