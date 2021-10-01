import time
import math

from discord.ext import commands
import discord
import orjson

import config


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
)


IMAGE_BASE = "https://upload.wikimedia.org/wikipedia/commons/thumb/"
HANGMAN_IMAGES = {
    0: f"{IMAGE_BASE}8/8b/Hangman-0.png/60px-Hangman-0.png",
    1: f"{IMAGE_BASE}3/30/Hangman-1.png/60px-Hangman-1.png",
    2: f"{IMAGE_BASE}7/70/Hangman-2.png/60px-Hangman-2.png",
    3: f"{IMAGE_BASE}9/97/Hangman-3.png/60px-Hangman-3.png",
    4: f"{IMAGE_BASE}2/27/Hangman-4.png/60px-Hangman-4.png",
    5: f"{IMAGE_BASE}6/6b/Hangman-5.png/60px-Hangman-5.png",
    6: f"{IMAGE_BASE}d/d6/Hangman-6.png/60px-Hangman-6.png",
}


class CookieClickerButton(discord.ui.Button["CookieClicker"]):
    def __init__(self, name, cost, cps, label, row):
        super().__init__(style=discord.ButtonStyle.gray, label=label, row=row)
        self.cost = cost
        self.name = name
        self.cps = cps

    async def callback(self, interaction: discord.Interaction):
        view = self.view

        if interaction.user == view.user:
            user_id = str(view.user.id).encode()
            cookies = view.DB.cookies.get(user_id)

            if not cookies:
                cookies = view.default
            else:
                cookies = orjson.loads(cookies)

            cookies["cookies"] += (time.time() - cookies["start"]) * cookies["cps"]

            cookies["start"] = time.time()
            current = cookies[self.name]
            amount = cookies["buy_amount"]

            if amount > 1:
                cost = -(
                    self.cost
                    * ((1.15 ** current) - (1.15 ** (current + amount)))
                    / 0.15
                )
            else:
                cost = self.cost * 1.15 ** current

            if cookies["cookies"] < cost:
                return await interaction.response.edit_message(
                    content=(
                        f"You need {view.parse_num(cost - cookies['cookies'])}"
                        " more cookies to upgrade"
                    )
                )

            if amount == 0:
                while cookies["cookies"] > (
                    cost := self.cost * 1.15 ** cookies[self.name]
                ):
                    cookies["cookies"] -= cost
                    cookies[self.name] += 1
                    cookies["cps"] += self.cps
            else:
                cookies["cookies"] -= cost
                cookies[self.name] += amount
                cookies["cps"] += amount * self.cps

            view.DB.cookies.put(user_id, orjson.dumps(cookies))
            await interaction.response.edit_message(
                content=None, embed=view.get_embed(cookies)
            )


class CookieClicker(discord.ui.View):
    default = {
        "cookies": 0,
        "start": 0,
        "cps": 0,
        "cursor": 0,
        "grandma": 0,
        "farm": 0,
        "mine": 0,
        "factory": 0,
        "bank": 0,
        "temple": 0,
        "wizard tower": 0,
        "shipment": 0,
        "alchemy lab": 0,
        "portal": 0,
        "time machine": 0,
        "buy_amount": 1,
    }

    prices = {
        "cursor": (15, 0.1, "🖱️"),  # Cost, Cookies Per Second, Label
        "grandma": (100, 1, "👵"),
        "farm": (1_100, 8, "🚜"),
        "mine": (12_000, 47, "⛏️"),
        "factory": (130_000, 260, "🏭"),
        "bank": (1_400_000, 1_400, "🏦"),
        "temple": (20_000_000, 7_800, "🛕"),
        "wizard tower": (330_000_000, 44_000, "🧙‍♂️"),
        "shipment": (5_100_000_000, 260_000, "🚀"),
        "alchemy lab": (75_000_000_000, 1_600_000, "⚗️"),
        "portal": (1_000_000_000_000, 10_000_000, "🌀"),
        "time machine": (14_000_000_000_000, 65_000_000, "⌛"),
    }

    def __init__(self, db, user: discord.User):
        super().__init__(timeout=1200.0)
        self.user = user
        self.DB = db

        row = 7

        for name, (price, cps, label) in self.prices.items():
            row += 1
            self.add_item(CookieClickerButton(name, price, cps, label, row // 4))

    @staticmethod
    def parse_num(num):
        index = math.floor(math.log10(num) / 3) if num // 1 else 0
        return f"{num/10**(3*index):.1f} {BIG_NUMS[index]}"

    def get_embed(self, data):
        embed = discord.Embed(
            color=discord.Color.blurple(), title=self.user.display_name
        )

        embed.add_field(name="Cookies", value=f"{self.parse_num(data['cookies'])} 🍪")
        embed.add_field(name="CPS", value=f"{self.parse_num(data['cps'])}")
        embed.add_field(
            name="Buy Amount",
            value="Max" if not data["buy_amount"] else data["buy_amount"],
        )

        for building in self.prices:
            if data[building]:
                price = self.prices[building][0] * 1.15 ** data[building]
                embed.add_field(
                    name=building.title(),
                    value=f"{data[building]}/{self.parse_num(price)}",
                )

        return embed

    @discord.ui.select(
        placeholder="Change buy amount",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label="Buy 1", value=1),
            discord.SelectOption(label="Buy 10", value=10),
            discord.SelectOption(label="Buy 100", value=100),
            discord.SelectOption(label="Buy Max", value=0),
        ],
    )
    async def change_purchase_amount(self, select, interaction):
        if interaction.user == self.user:
            user_id = str(interaction.user.id).encode()
            cookies = self.DB.cookies.get(user_id)

            if not cookies:
                cookies = self.default
            else:
                cookies = orjson.loads(cookies)

            cookies["buy_amount"] = int(interaction.data["values"][0])
            self.DB.cookies.put(user_id, orjson.dumps(cookies))

            await interaction.response.edit_message(
                content=None, embed=self.get_embed(cookies)
            )

    @discord.ui.button(label="🍪", style=discord.ButtonStyle.blurple)
    async def click(self, button, interaction):
        if interaction.user == self.user:
            user_id = str(interaction.user.id).encode()
            cookies = self.DB.cookies.get(user_id)

            if not cookies:
                cookies = self.default
            else:
                cookies = orjson.loads(cookies)

            cookies["cookies"] += (
                10 * (cookies["cps"] + 1)
                + (time.time() - cookies["start"]) * cookies["cps"]
            )
            cookies["start"] = time.time()

            await interaction.response.edit_message(
                content=None, embed=self.get_embed(cookies)
            )
            self.DB.cookies.put(user_id, orjson.dumps(cookies))


class TicTacToeButton(discord.ui.Button["TicTacToe"]):
    def __init__(self, x: int, y: int):
        super().__init__(style=discord.ButtonStyle.secondary, label="\u200b", row=y)
        self.x = x
        self.y = y

    async def callback(self, interaction: discord.Interaction):
        view = self.view

        if not view.playing_against and interaction.user != view.author:
            view.playing_against = interaction.user

        if interaction.user not in (view.playing_against, view.author):
            return

        if view.current_player == -1:
            if interaction.user != view.author:
                return await interaction.response.edit_message(
                    content=f"It is {view.author}'s turn", view=view
                )
            self.style = discord.ButtonStyle.danger
            self.label = "X"
            content = f"It is now {view.playing_against}'s turn"
        else:
            if interaction.user != view.playing_against:
                return await interaction.response.edit_message(
                    content=f"It is {view.playing_against}'s turn", view=view
                )
            self.style = discord.ButtonStyle.success
            self.label = "O"
            content = f"It is now {view.author}'s turn"

        self.disabled = True
        view.board[self.y][self.x] = view.current_player
        view.current_player = -view.current_player

        if winner := view.check_for_win(
            str(view.author) if self.label == "X" else str(view.playing_against)
        ):
            content = winner

            for label in view.children:
                label.disabled = True

            view.stop()

        await interaction.response.edit_message(content=content, view=view)


class TicTacToe(discord.ui.View):
    def __init__(self, author: discord.Member):
        super().__init__()
        self.author = author
        self.playing_against = None
        self.current_player = -1
        self.board = [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]

        for x in range(3):
            for y in range(3):
                self.add_item(TicTacToeButton(x, y))

    def check_for_win(self, label):
        for across in self.board:
            value = sum(across)
            if value == -self.current_player * 3:
                return f"{label} won!"

        for line in range(3):
            value = self.board[0][line] + self.board[1][line] + self.board[2][line]
            if value == -self.current_player * 3:
                return f"{label} won!"

        diag = self.board[0][2] + self.board[1][1] + self.board[2][0]
        if diag == -self.current_player * 3:
            return f"{label} won!"

        diag = self.board[0][0] + self.board[1][1] + self.board[2][2]
        if diag == -self.current_player * 3:
            return f"{label} won!"

        if all(i != 0 for row in self.board for i in row):
            return "It's a tie!"

        return None


class games(commands.Cog):
    """For commands that are games."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.DB = bot.DB

    async def game_invite(
        self, game_id: int, ctx: commands.Context, key: bytes, msg: str
    ):
        """Creates an invite for a discord game interaction.

        game_id: int
            ID of the discord game interation.
        ctx: commands.Contex
            Context to send the invite link.
        key: bytes
            Key to put invite codes in the db.
        msg: str
            The message to send if there is another active game
        """
        if (code := self.DB.main.get(key)) and discord.utils.get(
            await ctx.guild.invites(), code=code.decode()
        ):
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    title=msg,
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
            "target_application_id": game_id,
        }

        async with self.bot.client_session.post(
            f"https://discord.com/api/v9/channels/{ctx.author.voice.channel.id}/invites",
            json=json,
            headers=headers,
        ) as response:
            data = await response.json()

        await ctx.send(f"https://discord.gg/{data['code']}")
        self.DB.main.put(key, data["code"].encode())

    @commands.command()
    async def word(self, ctx):
        """Starts a game of Word Snacks."""
        await self.bot.game_invite(
            879863976006127627,
            ctx,
            f"{ctx.guild.id}-snacks".encode(),
            "There is another active Word Snacks game",
        )

    @commands.command()
    async def scrabble(self, ctx):
        """Starts a game of Letter Tile."""
        await self.bot.game_invite(
            879863686565621790,
            ctx,
            f"{ctx.guild.id}-tile".encode(),
            "There is another active Letter Tile game",
        )

    @commands.command()
    async def doodle(self, ctx):
        """Starts a game of Doodle Crew."""
        await self.bot.game_invite(
            878067389634314250,
            ctx,
            f"{ctx.guild.id}-doodle".encode(),
            "There is another active Doodle Crew game",
        )

    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.command()
    async def cookie(self, ctx):
        """Starts a simple game of cookie clicker."""
        await ctx.send("Click for cookies", view=CookieClicker(self.DB, ctx.author))

    @commands.command()
    async def cookies(self, ctx, user: discord.User = None):
        """Gets a members cookies.

        user: discord.User
            The user whos cookies will be returned.
        """
        user = user or ctx.author

        user_id = str(user.id).encode()
        cookies = self.DB.cookies.get(user_id)

        if not cookies:
            cookies = {"cookies": 0, "upgrade": 1}
        else:
            cookies = orjson.loads(cookies)

        if "cps" in cookies:
            cookies["cookies"] += round(
                (time.time() - cookies["start"]) * cookies["cps"]
            )
            cookies["start"] = time.time()

        embed = discord.Embed(color=discord.Color.blurple())
        embed.add_field(
            name=f"{user.display_name}'s cookies",
            value=f"**{cookies['cookies']:,.0f}** 🍪",
        )

        await ctx.send(embed=embed)
        self.DB.cookies.put(user_id, orjson.dumps(cookies))

    @commands.command()
    async def cookietop(self, ctx):
        """Gets the users with the most cookies."""
        cookietop = []
        for member, data in self.DB.cookies:
            data = orjson.loads(data)
            cps = data.get("cps", 0)
            if cps:
                data["cookies"] += round((time.time() - data["start"]) * cps)

            cookietop.append((data["cookies"], int(member)))

        cookietop = sorted(cookietop, reverse=True)[:10]

        embed = discord.Embed(color=discord.Color.blurple())
        embed.title = f"Top {len(cookietop)} members"
        embed.description = "\n".join(
            [
                f"**{self.bot.get_user(member).display_name}:** `{bal:,.0f}` 🍪"
                for bal, member in cookietop
            ]
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def cookiegive(self, ctx, member: discord.Member, amount: int):
        """Gives cookies to someone.

        member: discord.Member
        amount: int
        """
        embed = discord.Embed(color=discord.Color.blurple())
        if amount < 0:
            embed.description = "```Can't send a negative amount of cookies```"
            return await ctx.send(embed=embed)

        if ctx.author == member:
            embed.description = "```Can't send cookies to yourself```"
            return await ctx.send(embed=embed)

        sender = str(ctx.author.id).encode()
        receiver = str(member.id).encode()

        sender_bal = self.DB.cookies.get(sender)

        if not sender_bal:
            embed.description = "```You don't have any cookies```"
            return await ctx.send(embed=embed)

        sender_bal = orjson.loads(sender_bal)

        if sender_bal["cookies"] < amount:
            embed.description = "```You don't have enough cookies```"
            return await ctx.send(embed=embed)

        receiver_bal = self.DB.cookies.get(receiver)

        if not receiver_bal:
            receiver_bal = {"cookies": amount, "upgrade": 1}
        else:
            receiver_bal = orjson.loads(receiver_bal)
            receiver_bal["cookies"] += amount

        sender_bal["cookies"] -= amount

        embed.description = f"{sender_bal['cookies']} 🍪 left"
        embed.title = f"You sent {amount} 🍪 to {member}"
        await ctx.send(embed=embed)

        self.DB.cookies.put(sender, orjson.dumps(sender_bal))
        self.DB.cookies.put(receiver, orjson.dumps(receiver_bal))

    @commands.command()
    async def tictactoe(self, ctx):
        """Starts a game of tic tac toe."""
        await ctx.send(
            f"Tic Tac Toe: {ctx.author} goes first", view=TicTacToe(ctx.author)
        )

    @commands.command()
    async def hangman(self, ctx):
        """Starts a game of hangman with a random word."""
        url = "https://random-word-api.herokuapp.com/word"

        async with self.bot.client_session.get(url) as response:
            data = await response.json()

        word = data[0]

        letter_indexs = {}
        guessed = []

        for index, letter in enumerate(word):
            if not letter.isalpha():
                guessed.append(letter + " ")
                continue

            guessed.append("\\_ ")

            if letter not in letter_indexs:
                letter_indexs[letter] = [index]
            else:
                letter_indexs[letter].append(index)

        missed_letters = set()
        misses = 0

        embed = discord.Embed(color=discord.Color.blurple(), title="".join(guessed))
        embed.set_image(url=HANGMAN_IMAGES[misses])
        embed.set_footer(text="Send a letter to make a guess")

        embed_message = await ctx.send(embed=embed)

        def check(message: discord.Message) -> bool:
            return message.author == ctx.author and message.channel == ctx.channel

        while True and misses < 7:
            message = await self.bot.wait_for("message", timeout=60.0, check=check)

            if message.content.lower() == word:
                return await embed_message.add_reaction("✅")

            guess = message.content[0].lower()
            if not guess.isalpha():
                continue

            if guess in letter_indexs:
                for index in letter_indexs[guess]:
                    guessed[index] = guess + " "

                if "\\_ " not in guessed:
                    return await embed_message.add_reaction("✅")
            else:
                missed_letters.add(guess)
                misses += 1

            if misses == 7:
                embed.title = word
            else:
                embed.title = "".join(guessed)
                embed.set_image(url=HANGMAN_IMAGES[misses])

            footer = "Send a letter to make a guess\n"
            if missed_letters:
                footer += f"Missed letters: {', '.join(missed_letters)}"
            embed.set_footer(text=footer)

            await embed_message.edit(embed=embed)

        await embed_message.add_reaction("❎")

    @commands.command()
    @commands.guild_only()
    async def chess(self, ctx):
        """Starts a Chess In The Park game."""
        await self.bot.game_invite(
            832012774040141894,
            ctx,
            f"{ctx.guild.id}-chess".encode(),
            "There is another active Chess In The Park game",
        )

    @commands.command()
    @commands.guild_only()
    async def poker(self, ctx):
        """Starts a Discord Poke Night."""
        await self.bot.game_invite(
            755827207812677713,
            ctx,
            f"{ctx.guild.id}-poker_night".encode(),
            "There is another active Poker Night game",
        )

    @commands.command()
    @commands.guild_only()
    async def betrayal(self, ctx):
        """Starts a Betrayal.io game."""
        await self.bot.game_invite(
            773336526917861400,
            ctx,
            f"{ctx.guild.id}-betrayal_io".encode(),
            "There is another active Betrayal.io game",
        )

    @commands.command()
    @commands.guild_only()
    async def fishing(self, ctx):
        """Starts a Fishington.io game."""
        await self.bot.game_invite(
            814288819477020702,
            ctx,
            f"{ctx.guild.id}-fishington".encode(),
            "There is another active Fishington.io game",
        )

    @commands.command()
    @commands.guild_only()
    async def youtube(self, ctx):
        """Starts a YouTube Together."""
        await self.bot.game_invite(
            755600276941176913,
            ctx,
            f"{ctx.guild.id}-youtube_together".encode(),
            "There is another active Youtube Together",
        )


def setup(bot: commands.Bot) -> None:
    """Starts the games cog."""
    bot.add_cog(games(bot))
