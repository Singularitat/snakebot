import discord
from discord.ext import commands
import random
import aiohttp
import lxml.html
import orjson
import hashlib
from urllib.parse import quote
import re
import cogs.utils.database as DB
import config
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO


class misc(commands.Cog):
    """Commands that don't fit into other cogs."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @staticmethod
    async def visualize_predictions(image, predictions):
        img = Image.open(BytesIO(await image.read()))
        img = img.convert("RGBA")

        labels = {prediction["label"] for prediction in predictions}
        colors = {
            label: (
                random.randint(0, 200),
                random.randint(0, 200),
                random.randint(0, 200),
            )
            for label in labels
        }

        for prediction in predictions:
            bounding_boxes = (
                prediction["bbox"]["x1"],
                prediction["bbox"]["y1"],
                prediction["bbox"]["x2"],
                prediction["bbox"]["y2"],
            )
            label = prediction["label"]
            color = colors[label]

            x1, y1, x2, y2 = bounding_boxes
            mask = Image.new("RGBA", img.size, color + (0,))
            draw = ImageDraw.Draw(mask)

            font = ImageFont.truetype(r"fonts\DejaVuSans.ttf", round(img.width / 25))
            text_x, text_y = font.getsize(label)

            draw.rectangle(((x1, y1), (x2, y2)), fill=color + (96,))
            if (y1 - text_y) > 0 and x1 > 0 and x2 > 0:
                draw.rectangle(
                    ((x1, y1), (x1 + text_x, y1 - text_y)), fill=color + (96,)
                )
            else:
                text_y = 0

            draw.text((x1, y1 - text_y), text=label, fill="white", font=font)
            img = Image.alpha_composite(img, mask)

        img = img.convert("RGB")

        return img

    @commands.command()
    async def vision(self, ctx):
        """Machine vision via openvisionapi.com"""
        embed = discord.Embed(color=discord.Color.blurple())
        if not ctx.message.attachments:
            embed.description = "```You need to attach an image.```"
            return await ctx.send(embed=embed)

        image = ctx.message.attachments[0]

        if image.content_type not in ["image/png", "image/jpg", "image/jpeg"]:
            embed.description = "```Invalid file type.```"
            return await ctx.send(embed=embed)

        form = aiohttp.FormData({"model": "yolov4"})
        form.add_field(
            name="image", value=await image.read(), content_type=image.content_type
        )

        async with ctx.typing():
            async with aiohttp.ClientSession() as session, session.post(
                "https://api.openvisionapi.com/api/v1/detection",
                data=form,
            ) as response:
                if 200 < response.status < 300:
                    embed.description = (
                        "```Couldn't process image might be too large```"
                    )
                    return await ctx.send(embed=embed)
                data = await response.json()

            if "predictions" not in data:
                embed.description = "```Couldn't process image.```"
                return await ctx.send(embed=embed)

            if not data["predictions"]:
                embed.description = "```No predictions.```"
                return await ctx.send(embed=embed)

            img = await self.visualize_predictions(image, data["predictions"])

            with BytesIO() as image_binary:
                img.save(image_binary, "PNG")
                image_binary.seek(0)
                await ctx.send(file=discord.File(fp=image_binary, filename="image.png"))

    @commands.command()
    async def cipher(self, ctx, *, message):
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
            # Chi-square
            chi = sum(
                [
                    (((message.count(char) / msg_len) - freq[char]) ** 2) / freq[char]
                    for char in set(message.lower().replace(" ", ""))
                ]
            )
            results.append((chi, (i, message)))

        for chi, result in sorted(results, reverse=True):
            embed.add_field(name=f"{result[0]}, {chi:.2f}%", value=result[1])

        await ctx.send(embed=embed)

    @staticmethod
    def starmap(iterable):
        for num1, num2 in iterable:
            yield num1 * num2

    @commands.command()
    async def block(self, ctx, A, B):
        """Solves a block cipher in the format of a python matrix.

        e.g
        "1 2 3" "3 7 15, 6 2 61, 2 5 1"

        block1: str
        block2: str
        """
        A = A.split(",")
        A = [[int(num) for num in block.split()] for block in A]
        B = B.split(",")
        B = [[int(num) for num in block.split()] for block in B]

        results = ""

        for block in A:
            results += f"{[chr((sum(self.starmap(zip(block, col))) % 26) + 97) for col in zip(*B)]}\n"

        embed = discord.Embed(
            color=discord.Color.blurple(), description=f"```{results}```"
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def youtube(self, ctx):
        """Starts a YouTube Together."""
        if (code := DB.db.get(b"youtube_together")) and discord.utils.get(
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

        async with aiohttp.ClientSession(headers=headers) as session, session.post(
            f"https://discord.com/api/v9/channels/{ctx.author.voice.channel.id}/invites",
            json=json,
        ) as response:
            data = await response.json()

        await ctx.send(f"https://discord.gg/{data['code']}")
        DB.db.put(b"youtube_together", data["code"].encode())

    @commands.command()
    async def poker(self, ctx):
        """Starts a Discord Poke Night."""
        if (code := DB.db.get(b"poker_night")) and discord.utils.get(
            await ctx.guild.invites(), code=code.decode()
        ):
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    title="There is another active Poker Night",
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
            "target_application_id": 755827207812677713,
        }

        async with aiohttp.ClientSession(headers=headers) as session, session.post(
            f"https://discord.com/api/v9/channels/{ctx.author.voice.channel.id}/invites",
            json=json,
        ) as response:
            data = await response.json()

        await ctx.send(f"https://discord.gg/{data['code']}")
        DB.db.put(b"poker_night", data["code"].encode())

    @commands.command()
    async def betrayal(self, ctx):
        """Starts a Betrayal.io game."""
        if (code := DB.db.get(b"betrayal_io")) and discord.utils.get(
            await ctx.guild.invites(), code=code.decode()
        ):
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    title="There is another active Betrayal.io game",
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
            "target_application_id": 773336526917861400,
        }

        async with aiohttp.ClientSession(headers=headers) as session, session.post(
            f"https://discord.com/api/v9/channels/{ctx.author.voice.channel.id}/invites",
            json=json,
        ) as response:
            data = await response.json()

        await ctx.send(f"https://discord.gg/{data['code']}")
        DB.db.put(b"betrayal_io", data["code"].encode())

    @commands.command()
    async def fishing(self, ctx):
        """Starts a Fishington.io game."""
        if (code := DB.db.get(b"fishington")) and discord.utils.get(
            await ctx.guild.invites(), code=code.decode()
        ):
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    title="There is another active Fishington.io game",
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
            "target_application_id": 814288819477020702,
        }

        async with aiohttp.ClientSession(headers=headers) as session, session.post(
            f"https://discord.com/api/v9/channels/{ctx.author.voice.channel.id}/invites",
            json=json,
        ) as response:
            data = await response.json()

        await ctx.send(f"https://discord.gg/{data['code']}")
        DB.db.put(b"fishington", data["code"].encode())

    @commands.command(aliases=["accdate", "newest"])
    async def oldest(self, ctx, amount: int = 10):
        """Gets the oldest accounts in a server.

        amount: int
        """
        amount = max(0, min(50, amount))

        reverse = ctx.invoked_with.lower() == "newest"
        top = sorted(ctx.guild.members, key=lambda member: member.id, reverse=reverse)[
            :amount
        ]

        description = "\n".join([f"**{member}:** {member.id}" for member in top])
        embed = discord.Embed(color=discord.Color.blurple())

        if len(description) > 2048:
            embed.description = "```Message is too large to send.```"
            return await ctx.send(embed=embed)

        embed.title = f"{'Youngest' if reverse else 'Oldest'} Accounts"
        embed.description = description

        await ctx.send(embed=embed)

    @commands.command(aliases=["msgtop"])
    async def message_top(self, ctx, amount=10):
        """Gets the users with the most messages in a server.

        amount: int
        """
        amount = max(0, min(50, amount))

        msgtop = sorted(
            [
                (int(b), m.decode())
                for m, b in DB.message_count
                if int(m.decode().split("-")[0]) == ctx.guild.id
            ],
            reverse=True,
        )[:amount]

        embed = discord.Embed(color=discord.Color.blurple())
        result = []

        for count, member in msgtop:
            user = self.bot.get_user(int(member.split("-")[1]))
            result.append((count, user.display_name if user else member))

        description = "\n".join(
            [f"**{member}:** {count} messages" for count, member in result]
        )

        if len(description) > 2048:
            embed.description = "```Message to large to send.```"
            return await ctx.send(embed=embed)

        embed.title = f"Top {len(msgtop)} chatters"
        embed.description = description

        await ctx.send(embed=embed)

    @staticmethod
    def unquote_unreserved(uri):
        UNRESERVED_SET = frozenset(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz" + "0123456789-._~"
        )
        parts = uri.split("%")
        for i in range(1, len(parts)):
            h = parts[i][0:2]
            if len(h) == 2 and h.isalnum():
                try:
                    c = chr(int(h, 16))
                except ValueError:
                    raise ValueError("Invalid percent-escape sequence: '%s'" % h)

                if c in UNRESERVED_SET:
                    parts[i] = c + parts[i][2:]
                else:
                    parts[i] = "%" + parts[i]
            else:
                parts[i] = "%" + parts[i]
        return "".join(parts)

    def requote_uri(self, uri):
        safe_with_percent = "!#$%&'()*+,/:;=?@[]~"
        safe_without_percent = "!#$&'()*+,/:;=?@[]~"
        try:
            return quote(self.unquote_unreserved(uri), safe=safe_with_percent)
        except ValueError:
            return quote(uri, safe=safe_without_percent)

    @commands.command()
    async def chat(self, ctx, *, message):
        """Chats with an 'ai'.

        message: str
            The message you want to send.
        """
        async with ctx.typing():
            cookies = DB.db.get(b"chatcookies")
            if cookies is None:
                async with aiohttp.ClientSession() as session, session.get(
                    "https://www.cleverbot.com/"
                ) as response:
                    cookies = {
                        "XVIS": re.search(
                            r"\w+(?=;)", response.headers["Set-cookie"]
                        ).group()
                    }
                    DB.db.put(b"chatcookies", orjson.dumps(cookies))
            else:
                cookies = orjson.loads(cookies)

            history = DB.db.get(b"chatbot-history")

            if history:
                history = orjson.loads(history)
            else:
                history = {}

            payload = f"stimulus={self.requote_uri(message)}&"

            if str(ctx.author.id) not in history:
                history[str(ctx.author.id)] = []

            for i, context in enumerate(history[str(ctx.author.id)][::-1]):
                payload += f"vText{i + 2}={self.requote_uri(context)}&"

            payload += "cb_settings_scripting=no&islearning=1&icognoid=wsf&icognocheck="
            payload += hashlib.md5(payload[7:33].encode()).hexdigest()

            url = "https://www.cleverbot.com/webservicemin?uc=UseOfficialCleverbotAPI"

            async with aiohttp.ClientSession(cookies=cookies) as session, session.post(
                url, data=payload
            ) as response:
                res = await response.read()
                if b"503 Service Temporarily Unavailable" in res:
                    return await ctx.reply("```503 Service Temporarily Unavailable```")
                response = re.split(r"\\r", str(res))[0][2:-1]

            history[str(ctx.author.id)].extend([message, response])

            if len(history[str(ctx.author.id)]) >= 40:
                del history[str(ctx.author.id)][:2]

            DB.db.put(b"chatbot-history", orjson.dumps(history))

            await ctx.reply(response)

    @commands.command()
    async def rps(self, ctx, choice: str):
        """Plays a game of rock paper scissors against an ai.

        choice: str
            Can be Rock, Paper, or Scissors.
        """
        embed = discord.Embed(color=discord.Color.blurple())
        choice = choice[0].upper()

        rps = {"R": 0, "P": 1, "S": 2}

        if choice not in rps:
            embed.description = "```Invalid choice.```"
            await ctx.send(embed=embed)

        history = DB.db.get(b"rps")
        DB.db.put(b"rps", history if history else b"" + choice.encode())

        url = f"https://smartplay.afiniti.com/v1/play/{str(history)}"
        async with aiohttp.ClientSession() as session, session.get(url) as page:
            result = await page.json()

        result = ("tied", "won", "lost")[
            (3 + rps[choice] - rps[result["nextBestMove"]]) % 3
        ]
        embed.description = f"```You {result}```"
        await ctx.reply(embed=embed)

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
    async def karma(self, ctx, user: discord.User = None):
        """Gets a users karma.

        user: discord.User
            The user to get the karma of.
        """
        if not user:
            user = ctx.author

        user_id = str(user.id).encode()
        karma = DB.karma.get(user_id)

        if not karma:
            karma = 0
        else:
            karma = karma.decode()

        tenary = "+" if int(karma) > 0 else ""

        embed = discord.Embed(color=discord.Color.blurple())
        embed.description = f"```diff\n{user.display_name}'s karma:\n{tenary}{karma}```"
        await ctx.send(embed=embed)

    @commands.command(aliases=["kboard", "karmab", "karmatop"])
    async def karmaboard(self, ctx):
        """Displays the top 5 and bottom 5 members karma."""
        sorted_karma = sorted([(int(k), int(m)) for m, k in DB.karma], reverse=True)
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
                async with aiohttp.ClientSession(
                    raise_for_status=True
                ) as session, session.get(url) as page:
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
    async def invite(self, ctx):
        """Sends the invite link of the bot."""
        perms = discord.Permissions.all()
        await ctx.send(f"<{discord.utils.oauth_url(self.bot.user.id, perms)}>")

    @commands.command()
    async def icon(self, ctx, user: discord.User = None):
        """Sends a members avatar url.

        user: discord.User
            The member to show the avatar of.
        """
        if not user:
            user = ctx.author
        await ctx.send(user.avatar_url)

    @commands.command()
    async def send(self, ctx, user: discord.User, *, message):
        """Gets Snakebot to send a DM to member.

        user: discord.User
            The user to DM.
        message: str
            The message to be sent.
        """
        embed = discord.Embed(color=discord.Color.blurple)
        try:
            await user.send(message)
            embed.description = f"```Sent message to {user.display_name}```"
            await ctx.send(embed=embed)
        except discord.errors.Forbidden:
            embed.description = (
                f"```{user.display_name} has DMs disabled for non-friends```"
            )
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

        nums = [str(random.randint(1, limit)) for r in range(rolls)]
        result = ", ".join(nums)
        total = sum([int(num) for num in nums])
        embed.description = f"```Results: {result} Total: {total}```"
        await ctx.reply(embed=embed)

    @commands.command()
    async def choose(self, ctx, *options: str):
        """Chooses between mulitple things.

        options: str
            The options to choose from.
        """
        await ctx.reply(random.choice(options))

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
            f"{ctx.author.mention} slapped {member.mention} because {reason}"
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

        char_length = len(graph_data) * 6 * (max_val + 2) + max_val + 7
        if char_length > 2000:
            return await ctx.send(
                f"```Bar graph is greater than 2000 characters [{char_length}]```"
            )

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

    @commands.group(hidden=True)
    @commands.has_permissions(administrator=True)
    async def ledger(self, ctx):
        """The ledger command group, call without args to show ledger."""
        if ctx.invoked_subcommand is None:
            ledger = DB.db.get(b"ledger")
            embed = discord.Embed(color=discord.Color.blurple())

            if not ledger:
                embed.description = "```Ledger is empty.```"
                return await ctx.send(embed=embed)

            ledger = orjson.loads(ledger)
            msg = ""
            for item in ledger["items"]:
                msg += "{} {} {} ${} {}\n".format(
                    self.bot.get_user(int(item["payer"])).display_name,
                    item["type"],
                    self.bot.get_user(int(item["payee"])).display_name,
                    item["amount"],
                    item.get("reason", "paying off their debts"),
                )

            if len(msg) == 0:
                embed.description = "```Ledger is empty.```"
                return await ctx.send(embed=embed)

            embed.description = f"```{msg}```"
            await ctx.send(embed=embed)

    @ledger.command(hidden=True)
    async def payme(self, ctx, member: discord.Member, amount: float, *, reason="idk"):
        """Adds an amount to be paid by member to the ledger.

        member: discord.Member
            The person to pay you.
        amount: float
            How much they are to pay you.
        reason: str
            The reason for the payment.
        """
        ledger = DB.db.get(b"ledger")
        embed = discord.Embed(color=discord.Color.blurple())

        if not ledger:
            ledger = {"items": [], "members": {}}
        else:
            ledger = orjson.loads(ledger)

        ledger["items"].append(
            {
                "type": "owes",
                "amount": amount,
                "reason": f"for {reason}",
                "payee": ctx.author.id,
                "payer": member.id,
            }
        )
        if str(member.id) not in ledger["members"]:
            ledger["members"][str(member.id)] = {}

        if str(ctx.author.id) not in ledger["members"][str(member.id)]:
            ledger["members"][str(member.id)][str(ctx.author.id)] = 0

        if str(member.id) in ledger["members"][str(ctx.author.id)]:
            if ledger["members"][str(ctx.author.id)][str(member.id)] >= amount:
                embed.description = (
                    "```Since {} owes {} {} their debt was canceled out```".format(
                        ctx.author.display_name,
                        member.display_name,
                        ledger["members"][str(ctx.author.id)][str(member.id)],
                    )
                )
                ledger["members"][str(ctx.author.id)][str(member.id)] -= amount
                return await ctx.send(embed=embed)

            amount -= ledger["members"][str(ctx.author.id)][str(member.id)]

        ledger["members"][str(member.id)][str(ctx.author.id)] += amount

        embed.description = "```{} is to pay {} ${:,} because {}```".format(
            member.display_name, ctx.author.display_name, amount, reason
        )
        await ctx.send(embed=embed)
        DB.db.put(b"ledger", orjson.dumps(ledger))

    @ledger.command(hidden=True)
    async def delete(self, ctx, index: int):
        """Deletes an item made by you off the ledger.

        id: str
            The id of the ledger item.
        """
        ledger = DB.db.get(b"ledger")
        embed = discord.Embed(color=discord.Color.blurple())

        if not ledger:
            embed.description = "```Ledger is empty.```"
            return await ctx.send(embed=embed)

        ledger = orjson.loads(ledger)

        try:
            item = ledger["items"][index]
        except IndexError:
            embed.description = "```Index not in ledger.```"
            return await ctx.send(embed=embed)

        if (
            item["payee"] != ctx.author.id
            and item["type"] == "owes"
            or item["payer"] != ctx.author.id
            and item["type"] == "paid"
        ):
            embed.description = "```You are not the creator of this ledger item.```"
            return await ctx.send(embed=embed)

        ledger["items"].pop(index)
        DB.db.put(b"ledger", orjson.dumps(ledger))

    @ledger.command(hidden=True)
    async def pay(self, ctx, member: discord.Member, amount: float):
        """Pay for an ledger item.

        member: discord.Member
            The person to pay.
        amount: float
            The amount to pay.
        """
        ledger = DB.db.get(b"ledger")
        embed = discord.Embed(color=discord.Color.blurple())

        if not ledger:
            ledger = {"items": [], "members": {}}
        else:
            ledger = orjson.loads(ledger)

        ledger["items"].append(
            {
                "type": "paid",
                "amount": amount,
                "payee": member.id,
                "payer": ctx.author.id,
            }
        )

        ledger["members"][str(member.id)][str(ctx.author.id)] = (
            ledger["members"][str(member.id)][str(ctx.author.id)] or 0
        ) - amount

        embed.description = "```{} paid {} ${:,}```".format(
            ctx.author.display_name, member.display_name, amount
        )
        await ctx.send(embed=embed)
        DB.db.put(b"ledger", orjson.dumps(ledger))

    @ledger.command(hidden=True)
    async def member(self, ctx, member: discord.Member):
        """Returns the ledger of the member.

        member: discord.Member
        """
        ledger = DB.db.get(b"ledger")
        embed = discord.Embed(color=discord.Color.blurple())

        if not ledger:
            embed.description = "```Ledger is empty.```"
            return await ctx.send(embed=embed)

        ledger = orjson.loads(ledger)
        msg = ""
        for item in ledger["items"]:
            if item["payer"] == str(member.id) or item["payee"] == str(member.id):
                msg += "{} {} {} ${} {}\n".format(
                    self.bot.get_user(int(item["payer"])).display_name,
                    item["type"],
                    self.bot.get_user(int(item["payee"])).display_name,
                    item["amount"],
                    item.get("reason", "paying off their debts"),
                )

        if len(msg) == 0:
            embed.description = "```Ledger is empty.```"
            return await ctx.send(embed=embed)

        embed.description = f"```{msg}```"
        await ctx.send(embed=embed)

    @ledger.command(hidden=True)
    async def split(
        self, ctx, amount: float, members: commands.Greedy[discord.Member], reason="idk"
    ):
        """Splits an amount between mutiple ledger members.

        amount: float
        members: list[discord.Member]
        reason: str
        """
        ledger = DB.db.get(b"ledger")
        embed = discord.Embed(color=discord.Color.blurple())

        if not ledger:
            ledger = {"items": [], "members": {}}
        else:
            ledger = orjson.loads(ledger)

        for member in members:
            ledger["items"].append(
                {
                    "type": "owes",
                    "amount": amount,
                    "reason": f"for {reason}",
                    "payee": ctx.author.id,
                    "payer": member.id,
                }
            )
            if str(member.id) not in ledger["members"]:
                ledger["members"][str(member.id)] = {}

            if str(ctx.author.id) not in ledger["members"][str(member.id)]:
                ledger["members"][str(member.id)][str(ctx.author.id)] = 0

            if str(member.id) in ledger["members"][str(ctx.author.id)]:
                if ledger["members"][str(ctx.author.id)][str(member.id)] >= amount:
                    ledger["members"][str(ctx.author.id)][str(member.id)] -= amount
                    continue

                amount -= ledger["members"][str(ctx.author.id)][str(member.id)]

            ledger["members"][str(member.id)][str(ctx.author.id)] += amount

            embed.description = "```{} is to pay {} ${:,} because {}```".format(
                member.display_name, ctx.author.display_name, amount, reason
            )
            await ctx.send(embed=embed)
        DB.db.put(b"ledger", orjson.dumps(ledger))


def setup(bot: commands.Bot) -> None:
    """Starts misc cog."""
    bot.add_cog(misc(bot))
