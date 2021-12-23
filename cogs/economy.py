import random

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

        self.card_deck = []
        for suit in suits:
            for card, value in cards.items():
                self.card_deck.append(Card(suits[suit], card, value))

        self.member_cards = [self.get_card(), self.get_card()]
        self.dealer_cards = [self.get_card(), self.get_card()]

    @staticmethod
    def get_score(cards):
        score = sum(card.value for card in cards)
        if score > 21:
            for card in cards:
                if card.name == "A":
                    score -= 10
                    if score < 21:
                        return score
        return score

    def get_card(self):
        return self.card_deck.pop(random.randrange(len(self.card_deck)))

    def get_embed(self, bet, hidden=True):
        embed = discord.Embed(color=discord.Color.blurple())
        embed.title = f"Blackjack game (${bet})"
        embed.description = """
        **Your Hand: {}**
        {}
        **Dealers Hand: {}**
        {}
        """.format(
            self.get_score(self.member_cards),
            " ".join([f"`{c.name}{c.suit}`" for c in self.member_cards]),
            self.get_score(self.dealer_cards) if not hidden else "",
            " ".join([f"`{c.name}{c.suit}`" for c in self.dealer_cards])
            if not hidden
            else f"`{self.dealer_cards[0].name}{self.dealer_cards[0].suit}` `##`",
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
                return bal * ((float(bet[:-1])) / 100)
            return float(bet.replace(",", ""))
        except ValueError:
            return None

    @commands.command()
    async def blackjack(self, ctx, bet=0):
        """Starts a game of blackjack.

        bet: float
        """
        embed = discord.Embed(color=discord.Color.blurple())

        member = str(ctx.author.id).encode()
        bal = await self.DB.get_bal(member)
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

        m_cards = deck.member_cards
        d_cards = deck.dealer_cards

        message = await ctx.send(embed=deck.get_embed(bet))

        if deck.get_score(m_cards) == 21:
            await message.edit(embed=deck.get_embed(bet, False))
            await self.DB.put_bal(member, bal + bet)
            return await message.add_reaction("✅")

        if deck.get_score(d_cards) == 21:
            await message.edit(embed=deck.get_embed(bet, False))
            await self.DB.put_bal(member, bal - bet)
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

        while deck.get_score(m_cards) < 21:
            reaction, user = await ctx.bot.wait_for(
                "reaction_add", timeout=60.0, check=check
            )
            if reaction.emoji == "🇭":
                m_cards.append(deck.get_card())
            else:
                break
            await reaction.remove(user)
            await message.edit(embed=deck.get_embed(bet))

        if (m_score := deck.get_score(m_cards)) > 21:
            bal -= bet
            await message.add_reaction("❎")
        else:
            while (score := deck.get_score(d_cards)) < 16 or score < m_score:
                d_cards.append(deck.get_card())

            if score > 21 or m_score > score:
                bal += bet
                await message.add_reaction("✅")
            elif score == m_score:
                await message.add_reaction("➖")
            else:
                bal -= bet
                await message.add_reaction("❎")

        await message.edit(embed=deck.get_embed(bet, False))
        await self.DB.put_bal(member, bal)

    @commands.command(aliases=["coinf"])
    async def coinflip(self, ctx, choice="h", bet=0):
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
        bal = await self.DB.get_bal(member)
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

        await self.DB.put_bal(member, bal)

        embed.set_footer(text=f"Balance: ${bal:,}")
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

    @commands.command()
    async def lottery(self, ctx, bet=0):
        """Lottery with a 1/99 chance of winning 99 times the bet.

        bet: float
            The amount of money you are betting.
        """
        embed = discord.Embed(color=discord.Color.blurple())

        member = str(ctx.author.id).encode()
        bal = await self.DB.get_bal(member)
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
            await self.DB.put_bal(member, bal)
            embed.title = f"You won ${bet * 99}"
            embed.set_footer(text=f"Balance: ${bal:,}")
            return await ctx.send(embed=embed)

        await self.DB.put_bal(member, bal - bet)
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
    async def slot(self, ctx, bet=0, silent: bool = False):
        """Rolls the slot machine.

        bet: str
            The amount of money you are betting.
        silent: bool
            If the final message should be sent
        """
        embed = discord.Embed(color=discord.Color.red())

        member = str(ctx.author.id).encode()
        bal = await self.DB.get_bal(member)
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
        await self.DB.put_bal(member, bal)

        if not silent:
            embed.title = f"[ {a} {b} {c} {d} ]"
            embed.description = f"You {result} ${bet*(abs(winnings)):,.2f}"
            embed.set_footer(text=f"Balance: ${bal:,}")

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
            name="**Wins/Loses**",
            value=f"""
            **Total Wins:** {wins["totalwin"]}
            **Total Losses:** {wins["totallose"]}
            **Current Wins:** {wins["currentwin"]}
            **Current Loses:** {wins["currentlose"]}
            **Highest Win Streak:** {wins["highestwin"]}
            **Highest Loss Streak:** {wins["highestlose"]}
            """,
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def chances(self, ctx):
        """Sends simulated chances of the slot machine from 1000000000 runs."""
        embed = discord.Embed(
            title="Chances from 1000000000 runs", color=discord.Color.blurple()
        )
        embed.add_field(name="Quad:", value="455431, 0.04554%")
        embed.add_field(name="Triple:", value="21855314, 2.18553%")
        embed.add_field(name="Double double:", value="16378846, 1.63788%")
        embed.add_field(name="Double:", value="360525049, 36.05250%")
        embed.add_field(name="None:", value="600785361, 60.07854%")
        embed.add_field(name="Percentage gain/loss:", value="18.7624388%")
        embed.add_field(name="Highest win streak:", value=22)
        embed.add_field(name="Highest lose streak:", value=38)
        embed.add_field(name="Time taken:", value="2104.39373s")

        await ctx.send(embed=embed)

    @commands.command(aliases=["bal"])
    async def balance(self, ctx, user: discord.User = None):
        """Gets a members balance.

        user: discord.User
            The user whos balance will be returned.
        """
        user = user or ctx.author

        user_id = str(user.id).encode()
        bal = await self.DB.get_bal(user_id)

        embed = discord.Embed(color=discord.Color.blurple())
        embed.add_field(name=f"{user.display_name}'s balance", value=f"${bal:,}")

        await ctx.send(embed=embed)

    @commands.command(aliases=["give", "donate"])
    async def pay(self, ctx, user: discord.User, amount: float):
        """Pays a user from your balance.

        user: discord.User
            The member you are paying.
        amount: float
            The amount you are paying.
        """
        embed = discord.Embed(color=discord.Color.blurple())

        if ctx.author == user:
            embed.description = "```You can't pay yourself.```"
            return await ctx.send(embed=embed)

        _from = str(ctx.author.id).encode()
        to = str(user.id).encode()

        bal = await self.DB.transfer(_from, to, amount)

        embed = discord.Embed(
            title=f"Sent ${amount} to {user.display_name}",
            color=discord.Color.blurple(),
        )
        embed.set_footer(text=f"New Balance: ${bal:,}")

        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 21600, commands.BucketType.user)
    async def salary(self, ctx):
        """Gives you a salary of 1000 on a 6 hour cooldown."""
        member = str(ctx.author.id).encode()
        bal = await self.DB.add_bal(member, 1000)

        embed = discord.Embed(
            title=f"Paid {ctx.author.display_name} $1000", color=discord.Color.blurple()
        )
        embed.set_footer(text=f"Balance: ${bal:,}")

        await ctx.send(embed=embed)

    @commands.command(name="streaktop")
    async def top_streaks(self, ctx):
        """Shows the top slot streaks."""
        streak_top = []

        for member, data in self.DB.wins:
            user = self.bot.get_user(int(member))
            if user is not None:
                json = orjson.loads(data)
                data = ((json["highestwin"], json["highestlose"]), user.display_name)
                streak_top.append(data)

        streak_top.sort(reverse=True)

        embed = discord.Embed(color=discord.Color.blurple())
        embed.description = "```Highest Streaks [win/lose]:\n\n{}```".format(
            "\n".join([f"{member}: {hw[0]}/{hw[1]}" for hw, member in streak_top[:10]])
        )

        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    """Starts economy cog."""
    bot.add_cog(economy(bot))
