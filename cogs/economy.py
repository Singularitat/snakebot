import discord
from discord.ext import commands
import orjson
import random
import cogs.utils.database as DB


class economy(commands.Cog):
    """Commands related to the economy."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command()
    async def baltop(self, ctx, amount: int = 10):
        """Gets the top balances.

        amount: int
            The amount of balances to get defaulting to 3.
        """
        topbal = await DB.get_baltop(amount)

        embed = discord.Embed(color=discord.Color.blurple())
        embed.title = f"Top {len(topbal)} Balances"
        embed.description = "\n".join(
            [
                f"**{self.bot.get_user(member).display_name}:** ${bal:,.2f}"
                for bal, member in topbal
            ]
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def lottery(self, ctx, bet: float):
        """Lottery with a 1/99 chance of winning 99 times the bet.

        bet: float
            The amount of money you are betting.
        """
        embed = discord.Embed(color=discord.Color.blurple())

        if bet <= 0:
            embed.title = "Bet must be positive"
            return await ctx.send(embed=embed)

        member = str(ctx.author.id).encode()
        bal = await DB.get_bal(member)

        if bal < bet:
            embed.title = "You don't have enough cash"
            return await ctx.send(embed=embed)

        if random.randint(1, 100) == 50:
            bal += bet * 99
            await DB.put_bal(member, bal)
            embed.title = f"You won ${bet * 99}"
            embed.set_footer(text=f"Balance: ${bal:,}")
            return await ctx.send(embed=embed)

        await DB.put_bal(member, bal - bet)
        embed.title = f"You lost ${bet}"
        embed.set_footer(text=f"Balance: ${bal - bet:,}")
        embed.color = discord.Color.red()
        await ctx.send(embed=embed)

    async def streak_update(self, member, result):
        data = DB.wins.get(member)

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
        DB.wins.put(member, orjson.dumps(data))

    @commands.command(aliases=["slots"])
    async def slot(self, ctx, bet):
        """Rolls the slot machine.

        bet: str
            The amount of money you are betting.
        """
        embed = discord.Embed(color=discord.Color.red())
        try:
            bet = float(bet.replace(",", ""))
        except ValueError:
            embed.description = f"```Invalid bet. e.g {ctx.prefix}slot 1000```"
            return await ctx.send(embed=embed)

        if bet < 0:
            embed.title = "Bet must be positive"
            return await ctx.send(embed=embed)

        member = str(ctx.author.id).encode()
        bal = await DB.get_bal(member)

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
        await DB.put_bal(member, bal)

        embed.title = f"[ {a} {b} {c} {d} ]"
        embed.description = f"You {result} ${bet*(abs(winnings)):,.2f}"
        embed.set_footer(text=f"Balance: ${bal:,}")

        await ctx.send(embed=embed)
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

        wins = DB.wins.get(user)

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
        if not user:
            user = ctx.author

        user_id = str(user.id).encode()
        bal = await DB.get_bal(user_id)

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

        bal = await DB.transfer(_from, to, amount)

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
        bal = await DB.add_bal(member, 1000)

        embed = discord.Embed(
            title=f"Paid {ctx.author.display_name} $1000", color=discord.Color.blurple()
        )
        embed.set_footer(text=f"Balance: ${bal:,}")

        await ctx.send(embed=embed)

    @commands.command()
    async def streaktop(self, ctx):
        """Shows the top slot streaks."""
        streak_top = []

        for member, data in DB.wins:
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
