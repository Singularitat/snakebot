import discord
from discord import Embed
import textwrap
from discord.ext import commands
import json
import random
import time
from .utils.util import (
    stockgrab
)


class economy(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command()
    async def baltop(self, ctx):
        """Gets the top 3 balances"""
        with open('json/economy.json') as data_file:
            data = json.load(data_file)
        first = ['', 0]
        second = ['', 0]
        third = ['', 0]
        for user in data["money"]:
            if data["money"][user] > first[1]:
                first[0] = user
                first[1] = data["money"][user]
            elif data["money"][user] > second[1]:
                second[0] = user
                second[1] = data["money"][user]
            elif data["money"][user] > third[1]:
                third[0] = user
                third[1] = data["money"][user]
        embed = Embed(colour=discord.Colour.blurple())
        embed.description = (
            textwrap.dedent(f"""
                **Top 3 users**
                First: **{first[0]}**, {first[1]:.3e}
                Second: **{second[0]}**, {second[1]:.3e}
                Third: **{third[0]}**, {third[1]:.3e}
            """)
        )
        embed.set_thumbnail(url=ctx.guild.icon_url)
        await ctx.send(embed=embed)

    @commands.command()
    async def stocks(self, ctx):
        """Sends the price of every stock with a price above 1"""
        url = 'https://nz.finance.yahoo.com/most-active?offset=0&count=200'
        with open('json/economy.json') as data_file:
            data = json.load(data_file)
        embed = discord.Embed(colour=discord.Color.blue())
        x = 0
        y = 25
        for stock in await stockgrab(url):
            if float(stock[2]) >= 1 or stock[0][:3] in data["stocks"]:
                embed.add_field(name=stock[0][:3], value=f'${stock[2]}', inline=True)
                if x == y:
                    await ctx.send(embed=embed)
                    embed = discord.Embed(colour=discord.Color.blue())
                    y += 25
                x += 1

    @commands.command()
    async def stockbal(self, ctx, symbol):
        """Gets the amount of stocks you have in inputted stock"""
        with open('json/economy.json') as data_file:
            data = json.load(data_file)
        symbol = symbol.upper()
        try:
            await ctx.send(embed=discord.Embed(title=f'You have {data["stocks"][symbol][str(ctx.author)]} stocks in {symbol}', color=discord.Color.blue()))
        except KeyError:
            await ctx.send(embed=discord.Embed(title=f'You have never invested in {symbol}', color=discord.Color.red()))

    @commands.command()
    async def stockprice(self, ctx, symbol):
        """Gets the price of inputted stock"""
        url = 'https://nz.finance.yahoo.com/most-active?offset=0&count=200'
        symbol = symbol.upper()
        with open('json/economy.json') as data_file:
            data = json.load(data_file)
        for stock in await stockgrab(url):
            if float(stock[2]) >= 1 or stock[0][:3] in data["stocks"]:
                try:
                    data["stocks"][stock[0][:3]]["price"] = stock[2]
                except KeyError:
                    pass
        for stock in data["stocks"]:
            if stock == symbol:
                await ctx.send(embed=discord.Embed(title=f'1 {symbol} is worth ${data["stocks"][symbol]["price"]}', color=discord.Color.blue()))
                break
        if symbol != stock:
            await ctx.send(embed=discord.Embed(title=f'No stock found for {symbol}', color=discord.Color.red()))
        with open('json/economy.json', 'w') as file:
            data = json.dump(data, file)

    @commands.command()
    async def sellstock(self, ctx, symbol, amount: float):
        url = 'https://nz.finance.yahoo.com/most-active?offset=0&count=200'
        author = str(ctx.author)
        with open('json/economy.json') as data_file:
            data = json.load(data_file)
        symbol = symbol.upper()
        for stock in await stockgrab(url):
            if float(stock[2]) >= 1 or stock[0][:3] in data["stocks"]:
                try:
                    data["stocks"][stock[0][:3]]["price"] = stock[2]
                except KeyError:
                    pass
        if symbol in data["stocks"]:
            if amount <= data["stocks"][symbol][author]:
                cash = amount * float(data["stocks"][symbol]["price"])
                data["stocks"][symbol][author] -= amount
                data["money"][author] += cash
                await ctx.send(embed=discord.Embed(title=f"Sold {amount} stocks for ${cash}", color=discord.Color.blue()))
            else:
                await ctx.send(embed=discord.Embed(title=f'You dont have enough stocks you have {amount} stocks', color=discord.Color.red()))
        with open('json/economy.json', 'w') as file:
            data = json.dump(data, file)

    @commands.command()
    async def invest(self, ctx, symbol=None, cash=None):
        """Buys inputted stock with inputted amount of cash"""
        url = 'https://nz.finance.yahoo.com/most-active?offset=0&count=200'
        author = str(ctx.author)
        if symbol is None:
            embed = discord.Embed(colour=discord.Color.blue())
            embed.set_author(name='Stocks')
            embed.set_footer(icon_url=self.bot.user.avatar_url, text='Go way hat you™')
            for stock in await stockgrab(url):
                if float(stock[2]) >= 1:
                    embed.add_field(name=stock[0][:3], value=f'${stock[2]}', inline=True)
            await ctx.send(embed=embed)
        else:
            with open('json/economy.json') as data_file:
                data = json.load(data_file)
            for stock in await stockgrab(url):
                if float(stock[2]) >= 1 or stock[0][:3] in data["stocks"]:
                    try:
                        data["stocks"][stock[0][:3]]["price"] = stock[2]
                    except KeyError:
                        data["stocks"][stock[0][:3]] = {}
                        pass
            symbol = symbol.upper()
            if symbol in data["stocks"]:
                if data["money"][author] >= float(cash):
                    stocks = float(cash) / float(data["stocks"][symbol]["price"])
                    await ctx.send(embed=discord.Embed(title=f"You bought {stocks} stocks in {symbol}", color=discord.Color.red()))
                    try:
                        stocks = stocks + data["stocks"][symbol][author]
                    except Exception:
                        pass
                    data["stocks"][symbol][author] = stocks
                    data["money"][author] -= float(cash)
            else:
                await ctx.send(embed=discord.Embed(title=f"No stock found for {symbol}", color=discord.Color.red()))
            with open('json/economy.json', 'w') as file:
                data = json.dump(data, file)

    @commands.command()
    async def lottery(self, ctx, bet: float):
        """Does a lottery with a 1/99 chance of winning 99 times the bet"""
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

    @commands.command()
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
    async def chances(self, ctx, amount: int, remove: int = 0):
        """Gives the chances of getting quads triples doubles and singles in a given amount"""
        start = time.time()
        emojis = [
            ":apple:", ":tangerine:", ":pear:", ":lemon:", ":watermelon:", ":grapes:", ":strawberry:", ":cherries:", ":melon:",
            ":kiwi:", ":pineapple:", ":green_apple:", ":coconut:", ":peach:", ":mango:"
        ]
        if remove != 0:
            emojis = emojis[-remove]
        x = 0
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
        if amount > 1000000:
            await ctx.send('Choose a lower number')
        else:
            while amount > x:
                a = random.choice(emojis)
                b = random.choice(emojis)
                c = random.choice(emojis)
                d = random.choice(emojis)
                if (a == b == c == d):
                    quad += 1
                    iswin = True
                elif (a == b == c) or (a == c == d) or (a == b == d) or (b == d == c):
                    triple += 1
                    iswin = True
                elif (a == b) and (d == c) or (b == c) and (d == a) or (d == b) and (a == c):
                    scam += 1
                    iswin = True
                elif (a == b) or (a == c) or (b == c) or (d == c) or (d == b) or (d == a):
                    double += 1
                    iswin = True
                else:
                    none += 1
                    iswin = False
                if iswin is True:
                    win += 1
                    if highestlose < lose:
                        highestlose = lose
                    lose = 0
                else:
                    lose += 1
                    if highestwin < win:
                        highestwin = win
                    win = 0
                x += 1
            total = (((quad * 100) + (triple * 15) + (scam * 20) + (double * 1.5) - (none))/amount)*100
            embed = discord.Embed(title=f"Chances from {amount} attempts", color=discord.Color.blue())
            embed.add_field(name="Quad: ", value=f'{quad}, {round(((quad/amount)*100), 2)}%', inline=True)
            embed.add_field(name="Triple: ", value=f'{triple}, {round(((triple/amount)*100), 2)}%', inline=True)
            embed.add_field(name="Double double: ", value=f'{scam}, {round(((scam/amount)*100), 2)}%', inline=True)
            embed.add_field(name="Double: ", value=f'{double}, {round(((double/amount)*100), 2)}%', inline=True)
            embed.add_field(name="None: ", value=f'{none}, {round(((none/amount)*100), 2)}%', inline=True)
            embed.add_field(name="Percentage gain/loss: ", value=f'{round(total, 2)}%', inline=True)
            embed.add_field(name="Highest win streak: ", value=highestwin, inline=True)
            embed.add_field(name="Highest lose streak: ", value=highestlose, inline=True)
            embed.add_field(name="Time taken: ", value=str(time.time()-start)[:-4], inline=True)
            embed.set_footer(icon_url=self.bot.user.avatar_url, text="Go way hat you™")
            await ctx.send(embed=embed)

    @commands.command()
    async def balance(self, ctx):
        """Gets the users current balance"""
        with open('json/economy.json') as data_file:
            data = json.load(data_file)
        cash = str(ctx.author)
        if cash not in data["money"].keys():
            data["money"][cash] = 1000
        await ctx.send(embed=discord.Embed(title="Current balance ${:,.2f}".format(data["money"][cash]), color=discord.Color.blue()))
        with open('json/economy.json', 'w') as file:
            data = json.dump(data, file)

    @commands.command()
    async def pay(self, ctx, user: discord.Member, amount: float):
        """Pays inputted user inputted amount"""
        if (amount > 0):
            with open('json/economy.json') as data_file:
                data = json.load(data_file)
            cash = str(ctx.author)
            if data["money"][cash] < amount:
                await ctx.send(embed=discord.Embed(title="You don't have enough cash", color=discord.Color.red()))
            else:
                data["money"][cash] -= amount
                data["money"][str(user)] += amount
                with open('json/economy.json', 'w') as file:
                    data = json.dump(data, file)
                await ctx.send(embed=discord.Embed(title=f'Sent ${str(amount)} to {str(user)}', color=discord.Color.blue()))

    @commands.command()
    @commands.cooldown(1, 21600, commands.BucketType.user)
    async def salary(self, ctx):
        """Gives user a salary of 100"""
        with open('json/economy.json') as data_file:
            data = json.load(data_file)
        cash = str(ctx.author)
        if cash not in data["money"].keys():
            data["money"][cash] = 1000
        data["money"][cash] += 100
        with open('json/economy.json', 'w') as file:
            data = json.dump(data, file)
        await ctx.send(embed=discord.Embed(title=f'Gave {str(ctx.author)} $100', color=discord.Color.blue()))


def setup(bot):
    bot.add_cog(economy(bot))
