import discord
from discord.ext import commands
import ujson
from .utils.economy import stockgrab


class stocks(commands.Cog):
    """Stock related commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command()
    async def stocks(self, ctx):
        """Shows the price of stocks from yahoo finance."""
        url = "https://nz.finance.yahoo.com/most-active?offset=0&count=200"
        with open("json/economy.json") as file:
            data = ujson.load(file)
        embed = discord.Embed(colour=discord.Color.blue())
        x = 0
        y = 25
        for stock in await stockgrab(url):
            if float(stock[2]) >= 1 or stock[0][:3] in data["stocks"]:
                embed.add_field(name=stock[0][:3], value=f"${stock[2]}", inline=True)
                if x == y:
                    await ctx.send(embed=embed)
                    embed = discord.Embed(colour=discord.Color.blue())
                    y += 25
                x += 1

    @commands.command()
    async def stockbal(self, ctx, symbol):
        """Shows the amount of stocks you have bought in a stock.

        symbol: str
            The symbol of the stock to find.
        """
        with open("json/economy.json") as file:
            data = ujson.load(file)
        symbol = symbol.upper()
        try:
            await ctx.send(
                embed=discord.Embed(
                    title=f'You have {data["stocks"][symbol][ctx.author.id]} stocks in {symbol}',
                    color=discord.Color.blue(),
                )
            )
        except KeyError:
            await ctx.send(
                embed=discord.Embed(
                    title=f"You have never invested in {symbol}",
                    color=discord.Color.red(),
                )
            )

    @commands.command()
    async def stockprice(self, ctx, symbol):
        """Gets the current price of a stock.

        symbol: str
            The symbol of the stock to find.
        """
        url = "https://nz.finance.yahoo.com/most-active?offset=0&count=200"
        symbol = symbol.upper()
        with open("json/economy.json") as file:
            data = ujson.load(file)
        for stock in await stockgrab(url):
            if float(stock[2]) >= 1 or stock[0][:3] in data["stocks"]:
                try:
                    data["stocks"][stock[0][:3]]["price"] = stock[2]
                except KeyError:
                    pass
        for stock in data["stocks"]:
            if stock == symbol:
                await ctx.send(
                    embed=discord.Embed(
                        title=f'1 {symbol} is worth ${data["stocks"][symbol]["price"]}',
                        color=discord.Color.blue(),
                    )
                )
                break
        if symbol != stock:
            await ctx.send(
                embed=discord.Embed(
                    title=f"No stock found for {symbol}", color=discord.Color.red()
                )
            )
        with open("json/economy.json", "w") as file:
            data = ujson.dump(data, file, indent=2)

    @commands.command()
    async def sellstock(self, ctx, symbol, amount: float):
        """Sells stock.

        symbol: str
            The symbol of the stock to sell.
        amount: float
            The amount of stock to sell.
        """
        url = "https://nz.finance.yahoo.com/most-active?offset=0&count=200"
        user = str(ctx.author.id)
        with open("json/economy.json") as file:
            data = ujson.load(file)
        symbol = symbol.upper()
        for stock in await stockgrab(url):
            if float(stock[2]) >= 1 or stock[0][:3] in data["stocks"]:
                try:
                    data["stocks"][stock[0][:3]]["price"] = stock[2]
                except KeyError:
                    pass
        if symbol in data["stocks"]:
            if amount <= data["stocks"][symbol][user]:
                cash = amount * float(data["stocks"][symbol]["price"])
                data["stocks"][symbol][user] -= amount
                data["money"][user] += cash
                await ctx.send(
                    embed=discord.Embed(
                        title=f"Sold {amount} stocks for ${cash}",
                        color=discord.Color.blue(),
                    )
                )
            else:
                await ctx.send(
                    embed=discord.Embed(
                        title=f"You dont have enough stocks you have {amount} stocks",
                        color=discord.Color.red(),
                    )
                )
        with open("json/economy.json", "w") as file:
            data = ujson.dump(data, file, indent=2)

    @commands.command()
    async def invest(self, ctx, symbol=None, cash=False):
        """Buys stock or if nothing is passed in it shows the price of some stocks.

        symbol: str
            The symbol of the stock to buy.
        cash: int
            The amount of money to invest.
        """
        url = "https://nz.finance.yahoo.com/most-active?offset=0&count=200"
        user = str(ctx.author.id)
        if not cash:
            cash = float(cash)
        if symbol is None:
            embed = discord.Embed(colour=discord.Color.blue())
            embed.set_author(name="Stocks")
            embed.set_footer(icon_url=self.bot.user.avatar_url, text="Go way hat you™")
            for stock in await stockgrab(url):
                if float(stock[2]) >= 1:
                    embed.add_field(
                        name=stock[0][:3], value=f"${stock[2]}", inline=True
                    )
            await ctx.send(embed=embed)
        else:
            with open("json/economy.json") as file:
                data = ujson.load(file)
            for stock in await stockgrab(url):
                if float(stock[2]) >= 1 or stock[0][:3] in data["stocks"]:
                    try:
                        data["stocks"][stock[0][:3]]["price"] = stock[2]
                    except KeyError:
                        data["stocks"][stock[0][:3]] = {}
            symbol = symbol.upper()
            if symbol in data["stocks"]:
                if data["money"][user] >= cash:
                    amount = cash / float(data["stocks"][symbol]["price"])
                    await ctx.send(
                        embed=discord.Embed(
                            title=f"You bought {amount} stocks in {symbol}",
                            color=discord.Color.red(),
                        )
                    )
                    try:
                        amount = amount + data["stocks"][symbol][user]
                    except TypeError:
                        pass
                    data["stocks"][symbol][user] = amount
                    data["money"][user] -= cash
            else:
                await ctx.send(
                    embed=discord.Embed(
                        title=f"No stock found for {symbol}", color=discord.Color.red()
                    )
                )
            with open("json/economy.json", "w") as file:
                data = ujson.dump(data, file, indent=2)


def setup(bot: commands.Bot) -> None:
    """Starts stocks cog."""
    bot.add_cog(stocks(bot))
