import discord
from discord import Embed
import textwrap
from discord.ext import commands
import json
import random
import time


class Economy(commands.Cog):
    """For commands related to the economy."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command()
    async def baltop(self, ctx):
        """Gets the top 3 balances"""
        with open('json/economy.json') as data_file:
            data = json.load(data_file)
        topthree = sorted(data["money"], key=data["money"].get, reverse=True)[:3]
        embed = Embed(colour=discord.Colour.blurple())
        embed.description = (
            textwrap.dedent(f"""
                **Top 3 users**
                First: **{topthree[0]}**, {data["money"][topthree[0]]:.3e}
                Second: **{topthree[1]}**, {data["money"][topthree[1]]:.3e}
                Third: **{topthree[2]}**, {data["money"][topthree[2]]:.3e}
            """)
        )
        embed.set_thumbnail(url=ctx.guild.icon_url)
        await ctx.send(embed=embed)

    @commands.command()
    async def lottery(self, ctx, bet: float):
        """A lottery with a 1/99 chance of winning 99 times the bet"""
        if (bet > 0):
            lottery = random.randint(1, 100)
            number = random.randint(1, 100)
            with open('json/economy.json') as data_file:
                data = json.load(data_file)
            cash = str(ctx.author)
            if data["money"][cash] < bet:
                embed = discord.Embed(title="You don't have enough cash", color=discord.Color.blue(), inline=True)
            else:
                if lottery == number:
                    data["money"][cash] += (bet * 99)
                    embed = discord.Embed(title=f"You won ${bet * 99}", color=discord.Color.blue(), inline=True)
                else:
                    data["money"][cash] -= bet
                    embed = discord.Embed(title=f"You lost ${bet}", color=discord.Color.blue(), inline=True)
            with open('json/economy.json', 'w') as file:
                data = json.dump(data, file)
            await ctx.send(embed=embed)
        else:
            await ctx.send(embed=discord.Embed(title='Bet must be positive', color=discord.Color.red()))

    @commands.command(aliases=["slots"])
    async def slot(self, ctx, bet: float):
        """Rolls the slot machine"""
        emojis = [
            ":apple:", ":tangerine:", ":pear:", ":lemon:", ":watermelon:", ":grapes:", ":strawberry:", ":cherries:", ":melon:",
            ":kiwi:", ":pineapple:", ":green_apple:", ":coconut:", ":peach:", ":mango:"
        ]
        if (bet > 0):
            a = random.choice(emojis)
            b = random.choice(emojis)
            c = random.choice(emojis)
            d = random.choice(emojis)
            with open('json/economy.json') as data_file:
                data = json.load(data_file)
            cash = str(ctx.author)
            if cash not in data["money"].keys():
                data["money"][cash] = 1000
            if data["money"][cash] < 1:
                data["money"][cash] += 1
            if data["money"][cash] >= bet:
                win = "won"
                color = discord.Color.blue()
                if (a == b == c == d):
                    winnings = 100
                elif (a == b == c) or (a == c == d) or (a == b == d) or (b == c == d):
                    winnings = 15
                elif (a == b) and (d == c) or (b == c) and (d == a) or (d == b) and (a == c):
                    winnings = 20
                elif (a == b) or (a == c) or (b == c) or (d == c) or (d == b) or (d == a):
                    winnings = 1.5
                else:
                    winnings = -1
                    win = "lost"
                    color = discord.Color.red()
                embed = discord.Embed(title=f"[ {a} {b} {c} {d} ]", description=f"You {win} " + "${:,.2f}".format(bet*abs(winnings)), color=color, inline=True)
                data["money"][cash] = data["money"][cash] + bet*winnings
                if cash not in data["wins"].keys():
                    data["wins"][cash] = dict()
                    data["wins"][cash]["currentwin"] = 0
                    data["wins"][cash]["currentlose"] = 0
                    data["wins"][cash]["totalwin"] = 0
                    data["wins"][cash]["totallose"] = 0
                    data["wins"][cash]["highestlose"] = 0
                    data["wins"][cash]["highestwin"] = 0
                if win == "won":
                    data["wins"][cash]["currentwin"] += 1
                    data["wins"][cash]["totalwin"] += 1
                    if data["wins"][cash]["highestlose"] < data["wins"][cash]["currentlose"]:
                        data["wins"][cash]["highestlose"] = data["wins"][cash]["currentlose"]
                    data["wins"][cash]["currentlose"] = 0
                else:
                    if data["wins"][cash]["highestwin"] < data["wins"][cash]["currentwin"]:
                        data["wins"][cash]["highestwin"] = data["wins"][cash]["currentwin"]
                    data["wins"][cash]["totallose"] += 1
                    data["wins"][cash]["currentwin"] = 0
                    data["wins"][cash]["currentlose"] += 1
                with open('json/economy.json', 'w') as file:
                    data = json.dump(data, file)
            else:
                embed = discord.Embed(title="You don't have enough cash", color=discord.Color.red(), inline=True)
            await ctx.send(embed=embed)
        else:
            await ctx.send(embed=discord.Embed(title='Bet must be positive', color=discord.Color.red()))

    @commands.command()
    async def streak(self, ctx):
        """Gets your streaks on the slot machine"""
        with open('json/economy.json') as data_file:
            data = json.load(data_file)
        cash = str(ctx.author)
        embed = discord.Embed(title="Wins/Loses", color=discord.Color.blue())
        embed.add_field(name='Current loses', value=data["wins"][cash]["currentlose"], inline=True)
        embed.add_field(name='Current Wins', value=data["wins"][cash]["currentwin"], inline=True)
        embed.add_field(name='Total losses', value=data["wins"][cash]["totallose"], inline=True)
        embed.add_field(name='Total wins', value=data["wins"][cash]["totalwin"], inline=True)
        embed.add_field(name='Highest loss streak', value=data["wins"][cash]["highestlose"], inline=True)
        embed.add_field(name='Highest win streak', value=data["wins"][cash]["highestwin"], inline=True)
        embed.set_footer(icon_url=self.bot.user.avatar_url, text="Go way hat you™")
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 5400, commands.BucketType.user)
    async def chances(self, ctx, amount: int, remove: int = 0):
        """Sends simulated chances of the slot machine"""
        start = time.time()
        emojis = [
            ":apple:", ":tangerine:", ":pear:", ":lemon:", ":watermelon:", ":grapes:", ":strawberry:", ":cherries:", ":melon:",
            ":kiwi:", ":pineapple:", ":green_apple:", ":coconut:", ":peach:", ":mango:"
        ]
        if remove != 0:
            emojis = emojis[-remove]
        quad = 0
        triple = 0
        double = 0
        none = 0
        scam = 0
        iswin = True
        win = 0
        lose = 0
        highestlose = 0
        highestwin = 0
        if amount > 100000:
            await ctx.send('Choose a lower number')
        else:
            for i in range(amount):
                a = random.choice(emojis)
                b = random.choice(emojis)
                c = random.choice(emojis)
                d = random.choice(emojis)
                iswin = True
                if (a == b == c == d):
                    quad += 1
                elif (a == b == c) or (a == c == d) or (a == b == d) or (b == d == c):
                    triple += 1
                elif (a == b) and (d == c) or (b == c) and (d == a) or (d == b) and (a == c):
                    scam += 1
                elif (a == b) or (a == c) or (b == c) or (d == c) or (d == b) or (d == a):
                    double += 1
                else:
                    none += 1
                    iswin = False
                    lose += 1
                    if highestwin < win:
                        highestwin = win
                    win = 0
                if iswin is True:
                    win += 1
                    if highestlose < lose:
                        highestlose = lose
                    lose = 0
            total = (((quad * 100) + (triple * 15) + (scam * 20) + (double * 1.5) - (none))*(1/amount))*100
            embed = discord.Embed(title=f"Chances from {amount} attempts", color=discord.Color.blue())
            embed.add_field(name="Quad: ", value=f'{quad}, {round(((quad*(1/amount))*100), 2)}%', inline=True)
            embed.add_field(name="Triple: ", value=f'{triple}, {round(((triple*(1/amount))*100), 2)}%', inline=True)
            embed.add_field(name="Double double: ", value=f'{scam}, {round(((scam*(1/amount))*100), 2)}%', inline=True)
            embed.add_field(name="Double: ", value=f'{double}, {round(((double*(1/amount))*100), 2)}%', inline=True)
            embed.add_field(name="None: ", value=f'{none}, {round(((none*(1/amount))*100), 2)}%', inline=True)
            embed.add_field(name="Percentage gain/loss: ", value=f'{round(total, 2)}%', inline=True)
            embed.add_field(name="Highest win streak: ", value=highestwin, inline=True)
            embed.add_field(name="Highest lose streak: ", value=highestlose, inline=True)
            embed.add_field(name="Time taken: ", value=str(time.time()-start)[:-4], inline=True)
            embed.set_footer(icon_url=self.bot.user.avatar_url, text="Go way hat you™")
            await ctx.send(embed=embed)

    @commands.command(aliases=["bal"])
    async def balance(self, ctx):
        """Gets your current balance"""
        with open('json/economy.json') as data_file:
            data = json.load(data_file)
        cash = str(ctx.author)
        if cash not in data["money"].keys():
            data["money"][cash] = 1000
        await ctx.send(embed=discord.Embed(title="Current balance ${:,.2f}".format(data["money"][cash]), color=discord.Color.blue()))
        with open('json/economy.json', 'w') as file:
            data = json.dump(data, file)

    @commands.command(aliases=["give", "donate"])
    async def pay(self, ctx, member: discord.Member, amount: float):
        """Pays a member from your balance"""
        if (amount > 0):
            with open('json/economy.json') as data_file:
                data = json.load(data_file)
            cash = str(ctx.author)
            if data["money"][cash] < amount:
                await ctx.send(embed=discord.Embed(title="You don't have enough cash", color=discord.Color.red()))
            else:
                if str(member) not in data["money"].keys():
                    data["money"][str(member)] = 1000
                data["money"][cash] -= amount
                data["money"][str(member)] += amount
                with open('json/economy.json', 'w') as file:
                    data = json.dump(data, file)
                await ctx.send(embed=discord.Embed(title=f'Sent ${str(amount)} to {str(member)}', color=discord.Color.blue()))

    @commands.command()
    @commands.cooldown(1, 21600, commands.BucketType.user)
    async def salary(self, ctx):
        """Gives you a salary of 1000 on a 6 hour cooldown"""
        with open('json/economy.json') as data_file:
            data = json.load(data_file)
        cash = str(ctx.author)
        if cash not in data["money"].keys():
            data["money"][cash] = 1000
        data["money"][cash] += 1000
        with open('json/economy.json', 'w') as file:
            data = json.dump(data, file)
        await ctx.send(embed=discord.Embed(title=f'Gave {str(ctx.author)} $1000', color=discord.Color.blue()))


def setup(bot):
    bot.add_cog(Economy(bot))
