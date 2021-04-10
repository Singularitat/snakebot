import discord
from discord.ext import commands
import ujson
import random


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

        embed = discord.Embed(color=discord.Color.blurple())
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
                    title="You don't have enough cash", color=discord.Color.red()
                )
            else:
                if lottery == number:
                    self.bal.put(member, str(bal + bet * 99).encode())
                    embed = discord.Embed(
                        title=f"You won ${bet * 99}", color=discord.Color.blurple()
                    )
                else:
                    self.bal.put(member, str(bal - bet).encode())
                    embed = discord.Embed(
                        title=f"You lost ${bet}", color=discord.Color.red()
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
            data["highestlose"] = max(data["highestlose"], data["currentlose"])
            data["totalwin"] += 1
            data["currentwin"] += 1
            data["currentlose"] = 0
        else:
            data["highestwin"] = max(data["highestwin"], data["currentwin"])
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
            ":kiwi:",
            ":pineapple:",
            ":coconut:",
            ":peach:",
            ":mango:",
        )

        a, b, c, d = (*random.choices(emojis, k=4),)

        result = "won"
        color = discord.Color.blurple()
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

        embed = discord.Embed(color=discord.Color.blurple())

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
                payee = str(member.id).encode()
                payee_bal = self.bal.get(payee)

                if not payee_bal:
                    payee_bal = 1000
                else:
                    payee_bal = float(payee_bal)

                bal -= amount
                payee_bal += amount

                embed = discord.Embed(
                    title=f"Sent ${amount} to {member.display_name}",
                    color=discord.Color.blurple(),
                )
                embed.set_footer(text=f"New Balance: ${bal}")

                self.bal.put(payee, str(payee_bal).encode())
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
            title=f"Paid {ctx.author.display_name} $1000", color=discord.Color.blurple()
        )
        embed.set_footer(text=f"Balance: ${bal:,}")

        self.bal.put(member, str(bal).encode())

        await ctx.send(embed=embed)

    @commands.command()
    async def streaktop(self, ctx):
        """Shows the top slot streaks."""
        streak_top = []

        for member, data in self.wins:
            user = self.bot.get_user(int(member))
            if user is not None:
                json = ujson.loads(data)
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
