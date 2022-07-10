import random
from decimal import Decimal

import discord
import orjson
from discord.ext import commands


class Card:
    def __init__(self, suit, name, value):
        self.suit = suit
        self.name = name
        self.value = value


class Deck:
    def __init__(self):
        suits = {
            "Spades": "\u2664",
            "Hearts": "\u2661",
            "Clubs": "\u2667",
            "Diamonds": "\u2662",
        }

        cards = {
            "A": 11,
            "2": 2,
            "3": 3,
            "4": 4,
            "5": 5,
            "6": 6,
            "7": 7,
            "8": 8,
            "9": 9,
            "10": 10,
            "J": 10,
            "Q": 10,
            "K": 10,
        }

        self.items = []
        for suit in suits:
            for card, value in cards.items():
                self.items.append(Card(suits[suit], card, value))
        random.shuffle(self.items)

        self.member = [self.items.pop(), self.items.pop()]
        self.dealer = [self.items.pop(), self.items.pop()]

    @staticmethod
    def score(cards):
        score = sum(card.value for card in cards)
        if score > 21:
            for card in cards:
                if card.name == "A":
                    score -= 10
                    if score < 21:
                        return score
        return score

    def is_win(self):
        if (m_score := self.score(self.member)) > 21:
            return False

        while (score := self.score(self.dealer)) < 16 or score < m_score:
            self.dealer.append(self.items.pop())

        if score > 21 or m_score > score:
            return True
        if score == m_score:
            return None
        return False

    def get_embed(self, bet, hidden=True):
        embed = discord.Embed(color=discord.Color.blurple())
        embed.title = f"Blackjack game (${bet})"
        embed.description = """
        **Your Hand: {}**
        {}
        **Dealers Hand: {}**
        {}
        """.format(
            self.score(self.member),
            " ".join([f"`{c.name}{c.suit}`" for c in self.member]),
            self.score(self.dealer) if not hidden else "",
            " ".join([f"`{c.name}{c.suit}`" for c in self.dealer])
            if not hidden
            else f"`{self.dealer[0].name}{self.dealer[0].suit}` `##`",
        )
        return embed


class economy(commands.Cog):
    """Commands related to the economy."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.DB = bot.DB

    @staticmethod
    def get_amount(bal, bet):
        try:
            if bet[-1] == "%":
                return bal * (Decimal(bet[:-1]) / 100)
            return Decimal(bet.replace(",", ""))
        except ValueError:
            return None

    @commands.command(aliases=["bj"])
    async def blackjack(self, ctx, bet="0"):
        """Starts a game of blackjack.

        bet: float
        """
        embed = discord.Embed(color=discord.Color.blurple())

        member = str(ctx.author.id).encode()
        bal = self.DB.get_bal(member)
        bet = self.get_amount(bal, bet)

        if bet is None:
            embed.description = f"```Invalid bet. e.g {ctx.prefix}blackjack 1000```"
            return await ctx.send(embed=embed)

        if bet < 0:
            embed.title = "Bet must be positive"
            return await ctx.send(embed=embed)

        if bal < bet:
            embed.title = "You don't have enough cash"
            return await ctx.send(embed=embed)

        deck = Deck()
        message = await ctx.send(embed=deck.get_embed(bet))

        if deck.score(deck.member) == 21:
            await message.edit(embed=deck.get_embed(bet, False))
            self.DB.put_bal(member, bal + bet)
            return await message.add_reaction("✅")

        if deck.score(deck.dealer) == 21:
            await message.edit(embed=deck.get_embed(bet, False))
            self.DB.put_bal(member, bal - bet)
            return await message.add_reaction("❎")

        reactions = ["🇭", "🇸"]

        def check(reaction: discord.Reaction, user: discord.User) -> bool:
            return (
                user.id == ctx.author.id
                and reaction.message.channel == ctx.channel
                and reaction.emoji in reactions
            )

        for reaction in reactions:
            await message.add_reaction(reaction)

        while deck.score(deck.member) < 21:
            reaction, user = await ctx.bot.wait_for(
                "reaction_add", timeout=60.0, check=check
            )
            if reaction.emoji == "🇭":
                deck.member.append(deck.items.pop())
            else:
                break
            await reaction.remove(user)
            await message.edit(embed=deck.get_embed(bet))

        is_win = deck.is_win()

        if is_win is None:
            await message.add_reaction("➖")
        elif is_win:
            bal += bet
            await message.add_reaction("✅")
        else:
            bal -= bet
            await message.add_reaction("❎")

        await message.edit(embed=deck.get_embed(bet, False))
        self.DB.put_bal(member, bal)

    @commands.command(aliases=["coinf", "cf"])
    async def coinflip(self, ctx, choice="h", bet="0"):
        """Flips a coin.

        choice: str
        bet: int
        """
        embed = discord.Embed(color=discord.Color.red())
        choice = choice[0].lower()
        if choice not in ("h", "t"):
            embed.title = "Must be [h]eads or [t]ails"
            return await ctx.send(embed=embed)

        member = str(ctx.author.id).encode()
        bal = self.DB.get_bal(member)
        bet = self.get_amount(bal, bet)

        if bet is None:
            embed.description = f"```Invalid bet. e.g {ctx.prefix}coinflip 1000```"
            return await ctx.send(embed=embed)

        if bet < 0:
            embed.title = "Bet must be positive"
            return await ctx.send(embed=embed)

        if bal <= 1:
            bal += 1

        if bal < bet:
            embed.title = "You don't have enough cash"
            return await ctx.send(embed=embed)

        images = {
            "heads": "https://i.imgur.com/168G0Cr.jpg",
            "tails": "https://i.imgur.com/EdBBcsz.jpg",
        }

        result = random.choice(["heads", "tails"])

        embed.set_author(name=result.capitalize(), icon_url=images[result])

        if choice == result[0]:
            embed.color = discord.Color.blurple()
            embed.description = f"You won ${bet}"
            bal += bet
        else:
            embed.description = f"You lost ${bet}"
            bal -= bet

        self.DB.put_bal(member, bal)

        embed.set_footer(text=f"Balance: ${bal:,f}")
        await ctx.send(embed=embed)

    @commands.command()
    async def lottery(self, ctx, bet="0"):
        """Lottery with a 1/99 chance of winning 99 times the bet.

        bet: float
            The amount of money you are betting.
        """
        embed = discord.Embed(color=discord.Color.blurple())

        member = str(ctx.author.id).encode()
        bal = self.DB.get_bal(member)
        bet = self.get_amount(bal, bet)

        if bet is None:
            embed.description = f"```Invalid bet. e.g {ctx.prefix}lottery 1000```"
            return await ctx.send(embed=embed)

        if bet <= 0:
            embed.title = "Bet must be positive"
            return await ctx.send(embed=embed)

        if bal < bet:
            embed.title = "You don't have enough cash"
            return await ctx.send(embed=embed)

        if random.randint(1, 100) == 50:
            bal += bet * 99
            self.DB.put_bal(member, bal)
            embed.title = f"You won ${bet * 99}"
            embed.set_footer(text=f"Balance: ${bal:,f}")
            return await ctx.send(embed=embed)

        self.DB.put_bal(member, bal - bet)
        embed.title = f"You lost ${bet}"
        embed.set_footer(text=f"Balance: ${bal - bet:,}")
        embed.color = discord.Color.red()
        await ctx.send(embed=embed)

    async def streak_update(self, member, result):
        data = self.DB.wins.get(member)

        if not data:
            data = {
                "currentwin": 0,
                "currentlose": 0,
                "highestwin": 0,
                "highestlose": 0,
                "totallose": 0,
                "totalwin": 0,
            }
        else:
            data = orjson.loads(data.decode())

        if result == "won":
            data["highestlose"] = max(data["highestlose"], data["currentlose"])
            data["totalwin"] += 1
            data["currentwin"] += 1
            data["currentlose"] = 0
        else:
            data["highestwin"] = max(data["highestwin"], data["currentwin"])
            data["totallose"] += 1
            data["currentlose"] += 1
            data["currentwin"] = 0
        self.DB.wins.put(member, orjson.dumps(data))

    @commands.command(aliases=["slots"])
    async def slot(self, ctx, bet="0", silent: bool = False):
        """Rolls the slot machine.

        bet: str
            The amount of money you are betting.
        silent: bool
            If the final message should be sent
        """
        embed = discord.Embed(color=discord.Color.red())

        member = str(ctx.author.id).encode()
        bal = self.DB.get_bal(member)
        bet = self.get_amount(bal, bet)

        if bet is None:
            embed.description = f"```Invalid bet. e.g {ctx.prefix}slot 1000```"
            return await ctx.send(embed=embed)

        if bet < 0:
            embed.title = "Bet must be positive"
            return await ctx.send(embed=embed)

        if bal <= 1:
            bal += 1

        if bal < bet:
            embed.title = "You don't have enough cash"
            return await ctx.send(embed=embed)

        emojis = (
            ":apple:",
            ":tangerine:",
            ":pear:",
            ":lemon:",
            ":watermelon:",
            ":grapes:",
            ":strawberry:",
            ":cherries:",
            ":kiwi:",
            ":pineapple:",
            ":coconut:",
            ":peach:",
            ":mango:",
        )

        a, b, c, d = random.choices(emojis, k=4)

        result = "won"
        embed.color = discord.Color.blurple()
        if a == b == c == d:
            winnings = 100
        elif (a == b == c) or (a == c == d) or (a == b == d) or (b == c == d):
            winnings = 10
        elif (a == b) and (d == c) or (b == c) and (d == a) or (d == b) and (a == c):
            winnings = 10
        elif (a == b) or (a == c) or (b == c) or (d == c) or (d == b) or (d == a):
            winnings = 1
        else:
            winnings = -1
            result = "lost"
            embed.color = discord.Color.red()

        bal += bet * winnings
        self.DB.put_bal(member, bal)

        if not silent:
            embed.title = f"[ {a} {b} {c} {d} ]"
            embed.description = f"You {result} ${bet*(abs(winnings)):,.2f}"
            embed.set_footer(text=f"Balance: ${bal:,f}")

            await ctx.reply(embed=embed, mention_author=False)

        await self.streak_update(member, result)

    @commands.command(aliases=["streaks"])
    async def streak(self, ctx, user: discord.User = None):
        """Gets a users streaks on the slot machine.

        user: discord.User
            The user to get streaks of defaults to the command author."""
        if user:
            user = str(user.id).encode()
        else:
            user = str(ctx.author.id).encode()

        wins = self.DB.wins.get(user)

        if not wins:
            return

        wins = orjson.loads(wins.decode())

        embed = discord.Embed(color=discord.Color.blurple())
        embed.add_field(
            name="**Wins/Losses**",
            value=f"""
            **Total Wins:** {wins["totalwin"]}
            **Total Losses:** {wins["totallose"]}
            **Current Wins:** {wins["currentwin"]}
            **Current Losses:** {wins["currentlose"]}
            **Highest Win Streak:** {wins["highestwin"]}
            **Highest Loss Streak:** {wins["highestlose"]}
            """,
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def chances(self, ctx):
        """Sends pre simulated chances based off one hundred billion runs of the slot command."""
        await ctx.send(
            embed=discord.Embed(color=discord.Color.blurple())
            .add_field(name="Quad:", value="0.0455%")
            .add_field(name="Triple:", value="2.1848%")
            .add_field(name="Double Double:", value="1.6386%")
            .add_field(name="Double:", value="36.0491%")
            .add_field(name="None:", value="60.082%")
            .add_field(name="Percentage gain/loss:", value="18.7531%")
            .set_footer(
                text="Based off one hundred billion simulated runs of the slot command"
            )
        )

    @commands.command(aliases=["bal"])
    async def balance(self, ctx, user: discord.User = None):
        """Gets a members balance.

        user: discord.User
            The user whose balance will be returned.
        """
        user = user or ctx.author

        user_id = str(user.id).encode()
        bal = self.DB.get_bal(user_id)

        embed = discord.Embed(color=discord.Color.blurple())
        embed.add_field(name=f"{user.display_name}'s balance", value=f"${bal:,f}")

        await ctx.send(embed=embed)

    @commands.command()
    async def baltop(self, ctx, amount: int = 10):
        """Gets members with the highest balances.

        amount: int
            The amount of balances to get defaulting to 10.
        """
        baltop = []
        for member, bal in self.DB.bal:
            member = self.bot.get_user(int(member))
            if member:
                baltop.append((float(bal), member.display_name))

        baltop = sorted(baltop, reverse=True)[:amount]

        embed = discord.Embed(
            color=discord.Color.blurple(),
            title=f"Top {len(baltop)} Balances",
            description="\n".join(
                [f"**{member}:** ${bal:,.2f}" for bal, member in baltop]
            ),
        )
        await ctx.send(embed=embed)

    @commands.command(aliases=["net"])
    async def networth(self, ctx, member: discord.Member = None):
        """Gets a members net worth.

        members: discord.Member
            The member whose net worth will be returned.
        """
        member = member or ctx.author

        member_id = str(member.id).encode()
        bal = self.DB.get_bal(member_id)

        embed = discord.Embed(color=discord.Color.blurple())

        def get_value(values, db):
            if values:
                return Decimal(
                    sum(
                        [
                            stock[1]["total"]
                            * float(orjson.loads(db.get(stock[0].encode()))["price"])
                            for stock in values.items()
                        ]
                    )
                )

            return 0

        stock_value = get_value(self.DB.get_stockbal(member_id), self.DB.stocks)
        crypto_value = get_value(self.DB.get_cryptobal(member_id), self.DB.crypto)

        embed.add_field(
            name=f"{member.display_name}'s net worth",
            value=f"${bal + stock_value + crypto_value:,.2f}",
        )

        embed.set_footer(
            text="Crypto: ${:,.2f}\nStocks: ${:,.2f}\nBalance: ${:,.2f}".format(
                crypto_value, stock_value, bal
            )
        )

        await ctx.send(embed=embed)

    @commands.command()
    async def nettop(self, ctx, amount: int = 10):
        """Gets members with the highest net worth

        amount: int
            The amount of members to get
        """

        def get_value(values, db):
            if values:
                return sum(
                    [
                        stock[1]["total"]
                        * float(orjson.loads(db.get(stock[0].encode()))["price"])
                        for stock in values.items()
                    ]
                )

            return 0

        net_top = []

        for member_id, value in self.DB.bal:
            stock_value = get_value(self.DB.get_stockbal(member_id), self.DB.stocks)
            crypto_value = get_value(self.DB.get_cryptobal(member_id), self.DB.crypto)
            # fmt: off
            if (member := self.bot.get_user(int(member_id))):
                net_top.append(
                    (float(value) + stock_value + crypto_value, member.display_name)
                )
            # fmt: on

        net_top = sorted(net_top, reverse=True)[:amount]
        embed = discord.Embed(color=discord.Color.blurple())

        embed.title = f"Top {len(net_top)} Richest Members"
        embed.description = "\n".join(
            [f"**{member}:** ${bal:,.2f}" for bal, member in net_top]
        )
        await ctx.send(embed=embed)

    @commands.command(aliases=["give", "donate"])
    async def pay(self, ctx, user: discord.User, amount):
        """Pays a user from your balance.

        user: discord.User
            The member you are paying.
        amount: str
            The amount you are paying.
        """
        embed = discord.Embed(color=discord.Color.blurple())

        if ctx.author == user:
            embed.description = "```You can't pay yourself.```"
            return await ctx.send(embed=embed)

        sender = str(ctx.author.id).encode()
        sender_bal = self.DB.get_bal(sender)

        amount = self.get_amount(sender_bal, amount)

        if amount < 0:
            embed.title = "You cannot pay a negative amount"
            return await ctx.send(embed=embed)

        if sender_bal < amount:
            embed.title = "You don't have enough cash"
            return await ctx.send(embed=embed)

        self.DB.add_bal(str(user.id).encode(), amount)
        sender_bal -= Decimal(amount)
        self.DB.put_bal(sender, sender_bal)

        embed.title = f"Sent ${amount:,f} to {user.display_name}"
        embed.set_footer(text=f"New Balance: ${sender_bal:,f}")

        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 21600, commands.BucketType.user)
    async def salary(self, ctx):
        """Gives you a salary of 1000 on a 6 hour cooldown."""
        member = str(ctx.author.id).encode()
        bal = self.DB.add_bal(member, 1000)

        embed = discord.Embed(
            title=f"Paid {ctx.author.display_name} $1000", color=discord.Color.blurple()
        )
        embed.set_footer(text=f"Balance: ${bal:,f}")

        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    """Starts economy cog."""
    bot.add_cog(economy(bot))
