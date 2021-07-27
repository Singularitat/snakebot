from discord.ext import commands
import aiohttp
import discord
import orjson

import cogs.utils.database as DB
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
    def __init__(self, user: discord.User):
        super().__init__(timeout=600.0)
        self.user = user

    @discord.ui.button(label="🍪", style=discord.ButtonStyle.blurple)
    async def click(self, button, interaction):
        if interaction.user == self.user:
            user_id = str(interaction.user.id).encode()
            cookies = DB.cookies.get(user_id)

            if not cookies:
                cookies = {"cookies": 1, "upgrade": 1}
            else:
                cookies = orjson.loads(cookies)

            cookies["cookies"] += 1 * cookies["upgrade"]

            DB.cookies.put(user_id, orjson.dumps(cookies))
            await interaction.response.edit_message(
                content=f"You have {cookies['cookies']} 🍪's"
            )

    @discord.ui.button(label="🆙", style=discord.ButtonStyle.blurple)
    async def upgrade(self, button, interaction):
        if interaction.user == self.user:
            user_id = str(interaction.user.id).encode()
            cookies = DB.cookies.get(user_id)

            if not cookies:
                cookies = {"cookies": 1, "upgrade": 1}
            else:
                cookies = orjson.loads(cookies)

            if cookies["cookies"] < 100 * cookies["upgrade"]:
                return await interaction.response.edit_message(
                    content=f"You need {100 * cookies['upgrade']} cookies to upgrade"
                )

            cookies["cookies"] -= 100 * cookies["upgrade"]
            cookies["upgrade"] += 1

            DB.cookies.put(user_id, orjson.dumps(cookies))
            await interaction.response.edit_message(
                content=f"You have {cookies['upgrade']} upgrades"
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

        if view.current_player == -1:
            if interaction.user != view.author:
                return await interaction.response.edit_message(
                    content="It is X's turn", view=view
                )
            self.style = discord.ButtonStyle.danger
            self.label = "X"
            content = "It is now O's turn"
        else:
            if interaction.user != view.playing_against:
                return await interaction.response.edit_message(
                    content="It is O's turn", view=view
                )
            self.style = discord.ButtonStyle.success
            self.label = "O"
            content = "It is now X's turn"

        self.disabled = True
        view.board[self.y][self.x] = view.current_player
        view.current_player = -view.current_player

        if winner := view.check_for_win(self.label):
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

    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.command()
    async def cookie(self, ctx):
        """Starts a simple game of cookie clicker."""
        await ctx.send("Click for cookies", view=CookieClicker(ctx.author))

    @commands.command()
    async def cookies(self, ctx, user: discord.User = None):
        """Gets a members cookies.

        user: discord.User
            The user whos cookies will be returned.
        """
        user = user or ctx.author

        user_id = str(user.id).encode()
        cookies = DB.cookies.get(user_id)

        if not cookies:
            cookies = {"cookies": 0, "upgrade": 1}
        else:
            cookies = orjson.loads(cookies)

        embed = discord.Embed(color=discord.Color.blurple())
        embed.add_field(
            name=f"{user.display_name}'s cookies", value=f"**{cookies['cookies']:,}** 🍪"
        )

        await ctx.send(embed=embed)

    @commands.command()
    async def cookietop(self, ctx):
        """Gets the users with the most cookies."""
        cookietop = sorted(
            [(orjson.loads(c)["cookies"], int(m)) for m, c in DB.cookies], reverse=True
        )[:10]

        embed = discord.Embed(color=discord.Color.blurple())
        embed.title = f"Top {len(cookietop)} members"
        embed.description = "\n".join(
            [
                f"**{self.bot.get_user(member).display_name}:** {bal:,} 🍪"
                for bal, member in cookietop
            ]
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def tictactoe(self, ctx):
        """Starts a game of tic tac toe."""
        await ctx.send("Tic Tac Toe: X goes first", view=TicTacToe(ctx.author))

    @commands.command()
    async def hangman(self, ctx):
        """Starts a game of hangman with a random word."""
        url = "https://random-words-api.vercel.app/word"

        async with aiohttp.ClientSession() as session, session.get(url) as response:
            data = await response.json()

        word = data[0]["word"]
        definition = data[0]["definition"]

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
                embed.description = definition
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
    @commands.guild_only()
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
    @commands.guild_only()
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


def setup(bot: commands.Bot) -> None:
    """Starts the games cog."""
    bot.add_cog(games(bot))
