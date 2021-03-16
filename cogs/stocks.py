import discord
from discord.ext import commands
import ujson


class stocks(commands.Cog):
    """Stock related commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command()
    async def stocks(self, ctx):
        """Shows the price of stocks from yahoo finance."""
        with open("json/economy.json") as file:
            data = ujson.load(file)

        msg = "```Stocks\n"
        i = 0

        for stock in data["stocks"]:
            if len(msg + f"{stock}: ${data['stocks'][stock]:<9}") < 2000:
                if i % 6 == 0:
                    msg += "\n"
                i += 1
                msg += f"{stock}: ${data['stocks'][stock]:<9}"

        await ctx.send(f"{msg}```")

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
            await ctx.send(
                f"```You have {data['stockbal'][str(ctx.author.id)][symbol]:.2f} stocks in {symbol}```"
            )
        else:
            await ctx.send(f"```You have never invested in {symbol}```")

    @commands.command(aliases=["stockprof", "stockp"])
    async def stockprofile(self, ctx, member: discord.Member = None):
        """Gets someone's stock profile."""
        with open("json/economy.json") as file:
            data = ujson.load(file)

        if member is None:
            member = ctx.author

        if str(member.id) in data["stockbal"]:
            msg = f"```{ctx.message.author}'s stock profile"

            for stock in data["stockbal"][str(member.id)]:
                msg += f"\n{stock}: {data['stockbal'][str(member.id)][stock]:.2f}"

            await ctx.send(f"{msg}```")
        else:
            await ctx.send("```You have never invested```")

    @commands.command()
    async def stockprice(self, ctx, symbol):
        """Gets the current price of a stock.

        symbol: str
            The symbol of the stock to find.
        """
        symbol = symbol.upper()
        with open("json/economy.json") as file:
            data = ujson.load(file)

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
        user = str(ctx.author.id)
        with open("json/economy.json") as file:
            print(file)
            data = ujson.load(file)
        symbol = symbol.upper()

        if symbol in data["stocks"]:
            if user not in data["money"]:
                data["money"][user] = 1000

            if user not in data["stockbal"]:
                data["stockbal"][user] = {}
                return await ctx.send("```You have never invested```")

            if symbol not in data["stockbal"][user]:
                data["stockbal"][user][symbol] = 0
                return await ctx.send(f"```You have never invested in {symbol}```")

            cash = amount * float(data["stocks"][symbol])

            data["stockbal"][user][symbol] -= amount
            data["money"][user] += cash

            await ctx.send(f"```Sold {amount:.2f} stocks for ${cash:.2f}```")
        else:
            await ctx.send(f"```Couldn't find stock {symbol}```")
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
            return await ctx.send(
                f"```Usage:\n{ctx.prefix}{ctx.command} {ctx.command.signature}```"
            )

        user = str(ctx.author.id)

        with open("json/economy.json") as file:
            data = ujson.load(file)

        if symbol is None:
            embed = discord.Embed(colour=discord.Color.blue())
            embed.set_author(name="Stocks")

            for num, stock in enumerate(data["stocks"]):
                embed.add_field(name=stock[0][:3], value=f"${stock[2]}", inline=True)
                if num == 24:
                    return
            await ctx.send(embed=embed)
        else:
            if user not in data["money"]:
                data["money"][user] = 1000

            symbol = symbol.upper()

            if symbol in data["stocks"]:
                if data["money"][user] >= cash:
                    amount = cash / float(data["stocks"][symbol])
                    await ctx.send(f"```You bought {amount:.2f} stocks in {symbol}```")

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
