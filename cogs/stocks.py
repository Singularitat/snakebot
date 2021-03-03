import discord
from discord.ext import commands
import ujson
from .utils.economy import stockgrab, stockupdate


class stocks(commands.Cog):
    """Stock related commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command()
    async def stocks(self, ctx):
        """Shows the price of stocks from yahoo finance."""
        url = "https://nz.finance.yahoo.com/most-active?offset=0&count=200"
        msg = "```Stocks\n"
        for index, stock in enumerate(sorted(await stockgrab(url))):
            if index % 6 == 0:
                msg += "\n"
            if len(msg + f"{stock[0][:3]}: ${stock[2]}") > 1996:
                return await ctx.send(f"{msg}```")
            msg += f"{stock[0][:3]}: ${stock[2]}"
            msg += " "*(9 - len(stock[2]))

    @commands.command()
    async def stockbal(self, ctx, symbol):
        """Shows the amount of stocks you have bought in a stock.

        symbol: str
            The symbol of the stock to find.
        """
        with open("json/economy.json") as file:
            data = ujson.load(file)
        symbol = symbol.upper()
        if ctx.author.id in data["stocks"][symbol]:
            await ctx.send(f"```You have {data['stockbal'][str(ctx.author.id)][symbol]} stocks in {symbol}```")
        else:
            await ctx.send(f"```You have never invested in {symbol}```")

    @commands.command(aliases=["stockprof", "stockp"])
    async def stockprofile(self, ctx):
        with open("json/economy.json") as file:
            data = ujson.load(file)
        if data['stockbal'][str(ctx.author.id)]:
            msg = f"```{ctx.message.author}'s stock profile"
            for stock in data['stockbal'][str(ctx.author.id)]:
                msg += f"\n{stock}: {data['stockbal'][str(ctx.author.id)][stock]}"
            await ctx.send(f"{msg}```")
        else:
            await ctx.send("```You have never invested```")

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

        await stockupdate(data, url)

        with open("json/economy.json", "w") as file:
            data = ujson.dump(data, file, indent=2)

        if symbol in data["stocks"]:
            await ctx.send(f"```1 {symbol} is worth ${data['stocks'][symbol]}```")
        else:
            await ctx.send(f"```No stock found for {symbol}```")

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
        await stockupdate(data, url)
        if symbol in data["stocks"]:
            if amount <= data["stocks"][symbol][user]:
                cash = amount * float(data["stocks"][symbol])

                if user not in data["money"]:
                    data["money"][user] = 1000

                if user not in data["stockbal"]:
                    data["stockbal"][user] = {}

                if symbol not in data["stockbal"][user]:
                    data["stockbal"][user][symbol] = 0

                data["stockbal"][user][symbol] -= amount
                data["money"][user] += cash

                await ctx.send(f"```Sold {amount} stocks for ${cash}```")
            else:
                await ctx.send(f"```You dont have enough stocks you have {amount} stocks```")
        else:
            await ctx.send(f"```You have never invested in {symbol}```")
        with open("json/economy.json", "w") as file:
            data = ujson.dump(data, file, indent=2)

    @commands.command()
    async def invest(self, ctx, symbol=None, cash: float = None):
        """Buys stock or if nothing is passed in it shows the price of some stocks.

        symbol: str
            The symbol of the stock to buy.
        cash: int
            The amount of money to invest.
        """
        if symbol is not None and cash is None:
            return await ctx.send(f"```Usage:\n{ctx.prefix}{ctx.command} {ctx.command.signature}```")

        url = "https://nz.finance.yahoo.com/most-active?offset=0&count=200"
        user = str(ctx.author.id)

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

            if user not in data["money"]:
                data["money"][user] = 1000

            await stockupdate(data, url)
            symbol = symbol.upper()

            if symbol in data["stocks"]:
                if data["money"][user] >= cash:
                    amount = cash / float(data["stocks"][symbol])
                    await ctx.send(f"```You bought {amount} stocks in {symbol}```")

                    if user not in data["stockbal"]:
                        data["stockbal"][user] = {}

                    if symbol not in data["stockbal"][user]:
                        data["stockbal"][user][symbol] = 0

                    data["stockbal"][user][symbol] += amount
                    data["money"][user] -= cash
                else:
                    await ctx.send("```You don't have enough cash```")
            else:
                await ctx.send(f"```No stock found for {symbol}```")
            with open("json/economy.json", "w") as file:
                data = ujson.dump(data, file, indent=2)


def setup(bot: commands.Bot) -> None:
    """Starts stocks cog."""
    bot.add_cog(stocks(bot))
