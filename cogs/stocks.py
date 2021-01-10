import discord
from discord.ext import commands
import json
from .utils.economy import stockgrab


class Stocks(commands.Cog):
    """For all stock related commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command()
    async def stocks(self, ctx):
        """Shows the price of stocks from nz.finance.yahoo.com"""
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
        """Shows the amount of stocks you have bought in a stock"""
        with open('json/economy.json') as data_file:
            data = json.load(data_file)
        symbol = symbol.upper()
        try:
            await ctx.send(embed=discord.Embed(title=f'You have {data["stocks"][symbol][str(ctx.author)]} stocks in {symbol}', color=discord.Color.blue()))
        except KeyError:
            await ctx.send(embed=discord.Embed(title=f'You have never invested in {symbol}', color=discord.Color.red()))

    @commands.command()
    async def stockprice(self, ctx, symbol):
        """Gets the price of a stock"""
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
        """Sells stock"""
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
        """Buys stock"""
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


def setup(bot):
    bot.add_cog(Stocks(bot))
