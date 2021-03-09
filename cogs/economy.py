import discord
from discord.ext import commands
import ujson
import random
import time


class economy(commands.Cog):
    """Commands related to the economy."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command()
    async def baltop(self, ctx, amount: int = 3):
        """Gets the top balances.

        amount: int
            The amount of balances to get defaulting to 3.
        """
        with open("json/economy.json") as file:
            data = ujson.load(file)
        topbal = sorted(data["money"], key=data["money"].get, reverse=True)[:amount]
        embed = discord.Embed(color=discord.Color.blue())
        for num in range(amount):
            try:
                embed.add_field(
                    name=self.bot.get_user(int(topbal[num])),
                    value=f"${data['money'][topbal[num]]:,.2f}",
                    inline=False,
                )
            except IndexError:
                await ctx.send(f"```Could only find {num} members```")
                num -= 1
                break
        embed.title = f"Top {num+1} Balances"
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
            with open("json/economy.json") as file:
                data = ujson.load(file)
            user = str(ctx.author.id)
            if data["money"][user] < bet:
                embed = discord.Embed(
                    title="You don't have enough cash",
                    color=discord.Color.blue(),
                    inline=True,
                )
            else:
                if lottery == number:
                    data["money"][user] += bet * 99
                    embed = discord.Embed(
                        title=f"You won ${bet * 99}",
                        color=discord.Color.blue(),
                        inline=True,
                    )
                else:
                    data["money"][user] -= bet
                    embed = discord.Embed(
                        title=f"You lost ${bet}",
                        color=discord.Color.blue(),
                        inline=True,
                    )
            with open("json/economy.json", "w") as file:
                data = ujson.dump(data, file, indent=2)
            await ctx.send(embed=embed)
        else:
            await ctx.send(
                embed=discord.Embed(
                    title="Bet must be positive", color=discord.Color.red()
                )
            )

    @commands.command(aliases=["slots"])
    async def slot(self, ctx, bet: float):
        """Rolls the slot machine.

        bet: float
            The amount of money you are betting.
        """
        emojis = [
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
        ]
        if bet > 0:
            a, b, c, d = (
                random.choice(emojis),
                random.choice(emojis),
                random.choice(emojis),
                random.choice(emojis),
            )
            with open("json/economy.json") as file:
                data = ujson.load(file)
            user = str(ctx.author.id)
            if user not in data["money"]:
                data["money"][user] = 1000
            if data["money"][user] <= 1:
                data["money"][user] += 1
            if data["money"][user] >= bet:
                result = "won"
                color = discord.Color.blue()
                if a == b == c == d:
                    winnings = 100
                elif (a == b == c) or (a == c == d) or (a == b == d) or (b == c == d):
                    winnings = 10
                elif (
                    (a == b)
                    and (d == c)
                    or (b == c)
                    and (d == a)
                    or (d == b)
                    and (a == c)
                ):
                    winnings = 15
                elif (
                    (a == b) or (a == c) or (b == c) or (d == c) or (d == b) or (d == a)
                ):
                    winnings = 1
                else:
                    winnings = -1
                    result = "lost"
                    color = discord.Color.red()

                data["money"][user] = data["money"][user] + bet * winnings

                embed = discord.Embed(
                    title=f"[ {a} {b} {c} {d} ]",
                    description=f"You {result} ${bet*(abs(winnings)):,.2f}",
                    color=color,
                    inline=True,
                )
                embed.set_footer(text=f"Balance: {data['money'][user]}")
                if user not in data["wins"]:
                    data["wins"][user] = {
                        "currentwin": 0,
                        "currentlose": 0,
                        "highestwin": 0,
                        "highestlose": 0,
                        "totallose": 0,
                        "totalwin": 0,
                    }
                if result == "won":
                    data["wins"][user]["currentwin"] += 1
                    data["wins"][user]["totalwin"] += 1
                    if (
                        data["wins"][user]["highestlose"]
                        < data["wins"][user]["currentlose"]
                    ):
                        data["wins"][user]["highestlose"] = data["wins"][user][
                            "currentlose"
                        ]
                    data["wins"][user]["currentlose"] = 0
                else:
                    if (
                        data["wins"][user]["highestwin"]
                        < data["wins"][user]["currentwin"]
                    ):
                        data["wins"][user]["highestwin"] = data["wins"][user][
                            "currentwin"
                        ]
                    data["wins"][user]["totallose"] += 1
                    data["wins"][user]["currentwin"] = 0
                    data["wins"][user]["currentlose"] += 1
                with open("json/economy.json", "w") as file:
                    data = ujson.dump(data, file, indent=2)
            else:
                embed = discord.Embed(
                    title="You don't have enough cash",
                    color=discord.Color.red(),
                    inline=True,
                )
            await ctx.send(embed=embed)
        else:
            await ctx.send(
                embed=discord.Embed(
                    title="Bet must be positive", color=discord.Color.red()
                )
            )

    @commands.command()
    async def streak(self, ctx):
        """Gets your streaks on the slot machine."""
        with open("json/economy.json") as file:
            data = ujson.load(file)
        user = str(ctx.author.id)
        embed = discord.Embed(title="Wins/Loses", color=discord.Color.blue())
        embed.add_field(
            name="Current loses", value=data["wins"][user]["currentlose"], inline=True
        )
        embed.add_field(
            name="Current Wins", value=data["wins"][user]["currentwin"], inline=True
        )
        embed.add_field(
            name="Total losses", value=data["wins"][user]["totallose"], inline=True
        )
        embed.add_field(
            name="Total wins", value=data["wins"][user]["totalwin"], inline=True
        )
        embed.add_field(
            name="Highest loss streak",
            value=data["wins"][user]["highestlose"],
            inline=True,
        )
        embed.add_field(
            name="Highest win streak",
            value=data["wins"][user]["highestwin"],
            inline=True,
        )
        embed.set_footer(icon_url=self.bot.user.avatar_url, text="Go way hat you™")
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 5400, commands.BucketType.user)
    async def chances(self, ctx, amount: int, remove: int = 0):
        """Sends simulated chances of the slot machine.

        amount: int
            The amount of times to simulate the slot machine maxing at 100000.
        remove: int
            The amount of emojis to remove from the slot list deaulting to 0.
        """
        start = time.time()
        emojis = [
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
        ]
        if remove != 0:
            emojis = emojis[-remove]
        (
            quad,
            triple,
            dd,
            double,
            none,
            win,
            lose,
            highestlose,
            highestwin,
            run,
            iswin,
        ) = (
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
                    highestlose = max(highestlose, lose)
                if iswin is True:
                    win += 1
                    lose = 0
                    highestwin = max(highestwin, win)
            total = (
                ((quad * 100) + (triple * 10) + (dd * 15) + (double * 1) - (none))
                * (1 / amount)
            ) * 100
            embed = discord.Embed(
                title=f"Chances from {run} attempts", color=discord.Color.blue()
            )
            embed.add_field(
                name="Quad: ",
                value=f"{quad}, {round(((quad*(1/amount))*100), 2)}%",
                inline=True,
            )
            embed.add_field(
                name="Triple: ",
                value=f"{triple}, {round(((triple*(1/amount))*100), 2)}%",
                inline=True,
            )
            embed.add_field(
                name="Double double: ",
                value=f"{dd}, {round(((dd*(1/amount))*100), 2)}%",
                inline=True,
            )
            embed.add_field(
                name="Double: ",
                value=f"{double}, {round(((double*(1/amount))*100), 2)}%",
                inline=True,
            )
            embed.add_field(
                name="None: ",
                value=f"{none}, {round(((none*(1/amount))*100), 2)}%",
                inline=True,
            )
            embed.add_field(
                name="Percentage gain/loss: ", value=f"{round(total, 2)}%", inline=True
            )
            embed.add_field(name="Highest win streak: ", value=highestwin, inline=True)
            embed.add_field(
                name="Highest lose streak: ", value=highestlose, inline=True
            )
            embed.add_field(
                name="Time taken: ",
                value=f"{round(time.time() - start, 3)}s",
                inline=True,
            )
            embed.set_footer(icon_url=self.bot.user.avatar_url, text="Go way hat you™")
            await ctx.send(embed=embed)

    @commands.command(aliases=["bal"])
    async def balance(self, ctx, members: commands.Greedy[discord.Member] = None):
        """Gets a members balance.

        members: commands.Greedy[discord.Member]
            A list of members whos balances will be returned.
        """
        with open("json/economy.json") as file:
            data = ujson.load(file)
        if not members:
            members = [ctx.author]
        embed = discord.Embed(
            color=discord.Color.blue(),
        )
        for member in members:
            user = str(member.id)
            if user not in data["money"]:
                data["money"][user] = 1000
            embed.add_field(
                name=f"{member}'s balance: ",
                value=f"${data['money'][user]:,.2f}",
                inline=False,
            )
        await ctx.send(embed=embed)
        with open("json/economy.json", "w") as file:
            data = ujson.dump(data, file, indent=2)

    @commands.command(aliases=["give", "donate"])
    async def pay(self, ctx, member: discord.Member, amount: float):
        """Pays a member from your balance.

        member: discord.Member
            The member you are paying.
        amount: float
            The amount you are paying.
        """
        if amount > 0:
            with open("json/economy.json") as file:
                data = ujson.load(file)
            user = str(ctx.author.id)
            if data["money"][user] < amount:
                await ctx.send(
                    embed=discord.Embed(
                        title="You don't have enough cash", color=discord.Color.red()
                    )
                )
            else:
                if str(member.id) not in data["money"]:
                    data["money"][str(member.id)] = 1000
                data["money"][user] -= amount
                data["money"][str(member.id)] += amount
                with open("json/economy.json", "w") as file:
                    data = ujson.dump(data, file, indent=2)
                await ctx.send(
                    embed=discord.Embed(
                        title=f"Sent ${amount} to {member}", color=discord.Color.blue()
                    )
                )

    @commands.command()
    @commands.cooldown(1, 21600, commands.BucketType.user)
    async def salary(self, ctx):
        """Gives you a salary of 1000 on a 6 hour cooldown."""
        with open("json/economy.json") as file:
            data = ujson.load(file)
        user = str(ctx.author.id)
        if user not in data["money"]:
            data["money"][user] = 1000
        data["money"][user] += 1000
        with open("json/economy.json", "w") as file:
            data = ujson.dump(data, file, indent=2)
        await ctx.send(
            embed=discord.Embed(
                title=f"Gave {str(ctx.author)} $1000", color=discord.Color.blue()
            )
        )


def setup(bot: commands.Bot) -> None:
    """Starts economy cog."""
    bot.add_cog(economy(bot))
