import discord
from discord.ext import commands
import ujson
import random
import time


class economy(commands.Cog):
    """Commands related to the economy."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.bal = self.bot.db.prefixed_db(b"bal-")
        self.wins = self.bot.db.prefixed_db(b"wins-")

    @commands.command()
    async def baltop(self, ctx, amount: int = 10):
        """Gets the top balances.

        amount: int
            The amount of balances to get defaulting to 3.
        """
        topbal = sorted([(float(b), int(m)) for m, b in self.bal], reverse=True)[
            :amount
        ]

        embed = discord.Embed(color=discord.Color.blue())
        embed.add_field(
            name=f"Top {len(topbal)} Balances",
            value="\n".join(
                [
                    f"**{self.bot.get_user(member).display_name}:** ${bal:,.2f}"
                    for bal, member in topbal
                ]
            ),
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def lottery(self, ctx, bet: float):
        """Lottery with a 1/99 chance of winning 99 times the bet.

        bet: float
            The amount of money you are betting.
        """
        if bet > 0:
            lottery = random.randint(1, 100)
            number = random.randint(1, 100)

            member = str(ctx.author.id).encode()
            bal = self.bal.get(member)

            if bal is None:
                bal = 1000
            else:
                bal = float(bal)

            if bal < bet:
                embed = discord.Embed(
                    title="You don't have enough cash", color=discord.Color.blue()
                )
            else:
                if lottery == number:
                    self.bal.put(member, str(bal + bet * 99).encode())
                    embed = discord.Embed(
                        title=f"You won ${bet * 99}", color=discord.Color.blue()
                    )
                else:
                    self.bal.put(member, str(bal - bet).encode())
                    embed = discord.Embed(
                        title=f"You lost ${bet}", color=discord.Color.blue()
                    )
            await ctx.send(embed=embed)
        else:
            await ctx.send(
                embed=discord.Embed(
                    title="Bet must be positive", color=discord.Color.red()
                )
            )

    async def streak_update(self, member, result):
        data = self.wins.get(member)

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
            data = ujson.loads(data.decode())

        if result == "won":
            if data["highestlose"] < data["currentlose"]:
                data["highestlose"] = data["currentlose"]
            data["totalwin"] += 1
            data["currentwin"] += 1
            data["currentlose"] = 0
        else:
            if data["highestwin"] < data["currentwin"]:
                data["highestwin"] = data["currentwin"]
            data["totallose"] += 1
            data["currentlose"] += 1
            data["currentwin"] = 0
        self.wins.put(member, ujson.dumps(data).encode())

    @commands.command(aliases=["slots"])
    async def slot(self, ctx, bet):
        """Rolls the slot machine.

        bet: str
            The amount of money you are betting.
        """
        try:
            bet = float(bet.replace(",", ""))
        except ValueError:
            return await ctx.send(f"```Invalid bet. e.g {ctx.prefix}slot 1000```")

        if bet < 0:
            return await ctx.send(
                embed=discord.Embed(
                    title="Bet must be positive", color=discord.Color.red()
                )
            )

        member = str(ctx.author.id).encode()
        bal = self.bal.get(member)

        if bal is None:
            bal = 1000
        else:
            bal = float(bal)

        if bal <= 1:
            bal += 1

        if bal < bet:
            return await ctx.send(
                embed=discord.Embed(
                    title="You don't have enough cash", color=discord.Color.red()
                )
            )

        emojis = (
            ":apple:",
            ":tangerine:",
            ":pear:",
            ":lemon:",
            ":watermelon:",
            ":grapes:",
            ":strawberry:",
            ":cherries:",
            ":melon:",
            ":kiwi:",
            ":pineapple:",
            ":green_apple:",
            ":coconut:",
            ":peach:",
            ":mango:",
        )

        a, b, c, d = (
            random.choice(emojis),
            random.choice(emojis),
            random.choice(emojis),
            random.choice(emojis),
        )

        result = "won"
        color = discord.Color.blue()
        if a == b == c == d:
            winnings = 100
        elif (a == b == c) or (a == c == d) or (a == b == d) or (b == c == d):
            winnings = 10
        elif (a == b) and (d == c) or (b == c) and (d == a) or (d == b) and (a == c):
            winnings = 15
        elif (a == b) or (a == c) or (b == c) or (d == c) or (d == b) or (d == a):
            winnings = 1
        else:
            winnings = -1
            result = "lost"
            color = discord.Color.red()

        bal += bet * winnings
        self.bal.put(member, str(bal).encode())

        embed = discord.Embed(
            title=f"[ {a} {b} {c} {d} ]",
            description=f"You {result} ${bet*(abs(winnings)):,.2f}",
            color=color,
        )
        embed.set_footer(text=f"Balance: ${bal:,}")

        await ctx.send(embed=embed)
        await self.streak_update(member, result)

    @commands.command(aliases=["streaks"])
    async def streak(self, ctx, member: discord.Member = None):
        """Gets your streaks on the slot machine."""
        if member:
            member = str(member.id).encode()

        else:
            member = str(ctx.author.id).encode()

        wins = self.wins.get(member)

        if not wins:
            return

        wins = ujson.loads(wins.decode())

        embed = discord.Embed(color=discord.Color.blue())
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
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def chances(self, ctx, amount: int):
        """Sends simulated chances of the slot machine.

        amount: int
            The amount of times to simulate the slot machine maxing at 100000.
        """
        start = time.time()
        emojis = (
            ":apple:",
            ":tangerine:",
            ":pear:",
            ":lemon:",
            ":watermelon:",
            ":grapes:",
            ":strawberry:",
            ":cherries:",
            ":melon:",
            ":kiwi:",
            ":pineapple:",
            ":green_apple:",
            ":coconut:",
            ":peach:",
            ":mango:",
        )

        (quad, triple, dd, double, none, win, lose, hl, hw, run, iswin,) = (
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            True,
        )
        if amount > 100000:
            await ctx.send("```Choose a lower number```")
        else:
            while run < amount:
                run += 1
                a, b, c, d = (
                    random.choice(emojis),
                    random.choice(emojis),
                    random.choice(emojis),
                    random.choice(emojis),
                )
                iswin = True
                if a == b == c == d:
                    quad += 1
                elif (a == b == c) or (a == c == d) or (a == b == d) or (b == d == c):
                    triple += 1
                elif (
                    (a == b)
                    and (d == c)
                    or (b == c)
                    and (d == a)
                    or (d == b)
                    and (a == c)
                ):
                    dd += 1
                elif (
                    (a == b) or (a == c) or (b == c) or (d == c) or (d == b) or (d == a)
                ):
                    double += 1
                else:
                    none += 1
                    iswin = False
                    lose += 1
                    win = 0
                    hl = max(hl, lose)
                if iswin is True:
                    win += 1
                    lose = 0
                    hw = max(hw, win)
            total = (
                ((quad * 100) + (triple * 10) + (dd * 15) + (double * 1) - (none))
                * (1 / amount)
            ) * 100

            embed = discord.Embed(
                title=f"Chances from {run} attempts", color=discord.Color.blue()
            )
            embed.add_field(
                name="Quad: ",
                value=f"{quad}, {quad/amount*100:.2f}%",
                inline=True,
            )
            embed.add_field(
                name="Triple: ",
                value=f"{triple}, {triple/amount*100:.2f}%",
                inline=True,
            )
            embed.add_field(
                name="Double double: ",
                value=f"{dd}, {dd/amount*100:.2f}%",
                inline=True,
            )
            embed.add_field(
                name="Double: ",
                value=f"{double}, {double/amount*100:.2f}%",
                inline=True,
            )
            embed.add_field(
                name="None: ",
                value=f"{none}, {none/amount*100:.2f}%",
                inline=True,
            )
            embed.add_field(
                name="Percentage gain/loss: ", value=f"{total:.2f}%", inline=True
            )
            embed.add_field(name="Highest win streak: ", value=hw, inline=True)
            embed.add_field(name="Highest lose streak: ", value=hl, inline=True)
            embed.add_field(
                name="Time taken: ",
                value=f"{time.time() - start:.3f}s",
                inline=True,
            )

            await ctx.send(embed=embed)

    @commands.command(aliases=["bal"])
    async def balance(self, ctx, member: discord.Member = None):
        """Gets a members balance.

        members: discord.Member
            The member whos balance will be returned.
        """
        if not member:
            member = ctx.author

        member_id = str(member.id).encode()

        bal = self.bal.get(member_id)

        if not bal:
            bal = 1000
        else:
            bal = float(bal)

        embed = discord.Embed(color=discord.Color.blue())

        embed.add_field(
            name=f"{member.display_name}'s balance", value=f"${bal:,.2f}", inline=False
        )

        await ctx.send(embed=embed)

    @commands.command(aliases=["give", "donate"])
    async def pay(self, ctx, member: discord.Member, amount: float):
        """Pays a member from your balance.

        member: discord.Member
            The member you are paying.
        amount: float
            The amount you are paying.
        """
        if amount > 0:
            member_id = str(ctx.author.id).encode()
            bal = self.bal.get(member_id)

            if not bal:
                bal = 1000
            else:
                bal = float(bal)

            if bal < amount:
                await ctx.send(
                    embed=discord.Embed(
                        title="You don't have enough cash", color=discord.Color.red()
                    )
                )
            else:
                bal -= amount
                bal += amount

                embed = discord.Embed(
                    title=f"Sent ${amount} to {member.display_name}",
                    color=discord.Color.blue(),
                )
                embed.set_footer(text=f"New Balance: ${bal}")

                self.bal.put(member_id, str(bal).encode())

                await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 21600, commands.BucketType.user)
    async def salary(self, ctx):
        """Gives you a salary of 1000 on a 6 hour cooldown."""
        member = str(ctx.author.id).encode()
        bal = self.bal.get(member)

        if not bal:
            bal = 1000
        else:
            bal = float(bal)

        bal += 1000

        embed = discord.Embed(
            title=f"Paid {ctx.author.display_name} $1000", color=discord.Color.blue()
        )
        embed.set_footer(text=f"Balance: ${bal:,}")

        self.bal.put(member, str(bal).encode())

        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    """Starts economy cog."""
    bot.add_cog(economy(bot))
