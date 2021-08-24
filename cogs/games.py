import time

from discord.ext import commands
import discord
import orjson

import config


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


class CookieClicker(discord.ui.View):
    def __init__(self, db, user: discord.User):
        super().__init__(timeout=1200.0)
        self.user = user
        self.DB = db

    @staticmethod
    def get_embed(name, data):
        cps = data.get("cps", 0) + 1
        upgrades = data["upgrade"]

        return (
            discord.Embed(color=discord.Color.blurple(), title=name)
            .add_field(name="Cookies", value=f"{data['cookies']} 🍪")
            .add_field(name="Upgrades", value=upgrades)
            .add_field(name="Cookies per second", value=cps)
            .add_field(name="\u200b", value="\u200b")
            .add_field(name="Cost", value=int((100 * upgrades) ** 0.8))
            .add_field(name="Cost", value=int((1000 * cps) ** 0.9))
        )

    @discord.ui.button(label="🍪", style=discord.ButtonStyle.blurple)
    async def click(self, button, interaction):
        if interaction.user == self.user:
            user_id = str(interaction.user.id).encode()
            cookies = self.DB.cookies.get(user_id)

            if not cookies:
                cookies = {"cookies": 1, "upgrade": 1}
            else:
                cookies = orjson.loads(cookies)

            cookies["cookies"] += cookies["upgrade"]

            if "start" in cookies:
                cookies["cookies"] += round(
                    (time.time() - cookies["start"]) * cookies["cps"]
                )
                cookies["start"] = time.time()

            await interaction.response.edit_message(
                content=None, embed=self.get_embed(self.user.display_name, cookies)
            )
            self.DB.cookies.put(user_id, orjson.dumps(cookies))

    @discord.ui.button(label="🆙", style=discord.ButtonStyle.blurple)
    async def upgrade(self, button, interaction):
        if interaction.user == self.user:
            user_id = str(interaction.user.id).encode()
            cookies = self.DB.cookies.get(user_id)

            if not cookies:
                cookies = {"cookies": 1, "upgrade": 1}
            else:
                cookies = orjson.loads(cookies)

            if "start" in cookies:
                cookies["cookies"] += round(
                    (time.time() - cookies["start"]) * cookies["cps"]
                )
                cookies["start"] = time.time()

            cost = int((100 * cookies["upgrade"]) ** 0.8)

            if cookies["cookies"] < cost:
                return await interaction.response.edit_message(
                    content=f"You need {cost} cookies to upgrade"
                )

            cookies["cookies"] -= cost
            cookies["upgrade"] += 1

            if cookies.get("buy_all"):
                while cookies["cookies"] > (
                    cost := int((100 * cookies["upgrade"]) ** 0.8)
                ):
                    cookies["cookies"] -= cost
                    cookies["upgrade"] += 1

            self.DB.cookies.put(user_id, orjson.dumps(cookies))
            await interaction.response.edit_message(
                content=None, embed=self.get_embed(self.user.display_name, cookies)
            )

    @discord.ui.button(label="🤖", style=discord.ButtonStyle.blurple)
    async def autocookie(self, button, interaction):
        if interaction.user == self.user:
            user_id = str(interaction.user.id).encode()
            cookies = self.DB.cookies.get(user_id)

            if not cookies:
                return

            cookies = orjson.loads(cookies)
            cost = int((1000 * (cookies.get("cps", 0) + 1)) ** 0.9)

            if "cps" in cookies:
                cookies["cookies"] += round(
                    (time.time() - cookies["start"]) * cookies["cps"]
                )
                cookies["start"] = time.time()

            if cookies["cookies"] < cost:
                return await interaction.response.edit_message(
                    content=f"You need {cost} cookies to upgrade"
                )

            if "cps" not in cookies:
                cookies["cps"] = 0
                cookies["start"] = time.time()

            cookies["cookies"] -= cost
            cookies["cps"] += 1

            if cookies.get("buy_all"):
                while cookies["cookies"] > (
                    cost := int((1000 * (cookies.get("cps", 0) + 1)) ** 0.9)
                ):
                    cookies["cookies"] -= cost
                    cookies["cps"] += 1

            self.DB.cookies.put(user_id, orjson.dumps(cookies))
            await interaction.response.edit_message(
                content=None, embed=self.get_embed(self.user.display_name, cookies)
            )

    @discord.ui.button(label="🕹️", style=discord.ButtonStyle.blurple)
    async def toggle(self, button, interaction):
        if interaction.user == self.user:
            user_id = str(interaction.user.id).encode()
            cookies = self.DB.cookies.get(user_id)

            if not cookies:
                return

            cookies = orjson.loads(cookies)
            cookies["buy_all"] = not cookies.get("buy_all")

            self.DB.cookies.put(user_id, orjson.dumps(cookies))
            response = "on" if cookies["buy_all"] else "off"
            await interaction.response.edit_message(
                content=f"Togged buy all {response}"
            )


class TicTacToeButton(discord.ui.Button["TicTacToe"]):
    def __init__(self, x: int, y: int):
        super().__init__(style=discord.ButtonStyle.secondary, label="\u200b", row=y)
        self.x = x
        self.y = y

    async def callback(self, interaction: discord.Interaction):
        view = self.view

        if not view.playing_against and interaction.user != view.author:
            view.playing_against = interaction.user

        if view.playing_against != interaction.user and view.author != interaction.user:
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
            name=f"{user.display_name}'s cookies", value=f"**{cookies['cookies']:,}** 🍪"
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

            cookietop.append(((data["cookies"], data["upgrade"], cps), int(member)))

        cookietop = sorted(cookietop, reverse=True)[:10]

        embed = discord.Embed(color=discord.Color.blurple())
        embed.title = f"Top {len(cookietop)} members"
        embed.description = "\n".join(
            [
                f"**{self.bot.get_user(member).display_name}:**"
                f" `{bal[0]:,}` 🍪 `{bal[1]:,}` 🆙 `{bal[2]:,}` 🤖"
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
        url = "https://random-word-form.herokuapp.com/random/adjective"

        async with self.bot.client_session.get(url) as response:
            data = await response.json()

        word = data[0]

        letter_indexs = {}

        for index, letter in enumerate(word):
            if letter not in letter_indexs:
                letter_indexs[letter] = [index]
            else:
                letter_indexs[letter].append(index)

        guessed = ["\\_ "] * len(word)
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
        if (code := self.DB.main.get(b"chess")) and discord.utils.get(
            await ctx.guild.invites(), code=code.decode()
        ):
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    title="There is another active Chess In The Park",
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
            "target_application_id": 832012774040141894,
        }

        async with self.bot.client_session.post(
            f"https://discord.com/api/v9/channels/{ctx.author.voice.channel.id}/invites",
            json=json,
            headers=headers,
        ) as response:
            data = await response.json()

        await ctx.send(f"https://discord.gg/{data['code']}")
        self.DB.main.put(b"chess", data["code"].encode())

    @commands.command()
    @commands.guild_only()
    async def poker(self, ctx):
        """Starts a Discord Poke Night."""
        if (code := self.DB.main.get(b"poker_night")) and discord.utils.get(
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

        async with self.bot.client_session.post(
            f"https://discord.com/api/v9/channels/{ctx.author.voice.channel.id}/invites",
            json=json,
            headers=headers,
        ) as response:
            data = await response.json()

        await ctx.send(f"https://discord.gg/{data['code']}")
        self.DB.main.put(b"poker_night", data["code"].encode())

    @commands.command()
    @commands.guild_only()
    async def betrayal(self, ctx):
        """Starts a Betrayal.io game."""
        if (code := self.DB.main.get(b"betrayal_io")) and discord.utils.get(
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

        async with self.bot.client_session.post(
            f"https://discord.com/api/v9/channels/{ctx.author.voice.channel.id}/invites",
            json=json,
            headers=headers,
        ) as response:
            data = await response.json()

        await ctx.send(f"https://discord.gg/{data['code']}")
        self.DB.main.put(b"betrayal_io", data["code"].encode())

    @commands.command()
    @commands.guild_only()
    async def fishing(self, ctx):
        """Starts a Fishington.io game."""
        if (code := self.DB.main.get(b"fishington")) and discord.utils.get(
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

        async with self.bot.client_session.post(
            f"https://discord.com/api/v9/channels/{ctx.author.voice.channel.id}/invites",
            json=json,
            headers=headers,
        ) as response:
            data = await response.json()

        await ctx.send(f"https://discord.gg/{data['code']}")
        self.DB.main.put(b"fishington", data["code"].encode())


def setup(bot: commands.Bot) -> None:
    """Starts the games cog."""
    bot.add_cog(games(bot))
