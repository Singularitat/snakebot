import discord
from discord.ext import commands
import ujson


class stocks(commands.Cog):
    """Stock related commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command()
    async def stocks(self, ctx, order="low"):
        """Shows the price of stocks from yahoo finance.

        order: str
            The order you want the stocks to be in [high/low].
        """
        with open("json/economy.json") as file:
            data = ujson.load(file)

        if order.lower() == "low":
            stock_data = sorted(data["stocks"], key=data["stocks"].get)
        elif order.lower() == "high":
            stock_data = sorted(data["stocks"], key=data["stocks"].get, reverse=True)
        else:
            stock_data = sorted(data["stocks"])

        msg = "```\n"
        i = 1

        for stock in stock_data:
            if len(msg + f"{stock}: ${data['stocks'][stock]:<9}") < 2000:
                if i % 6 == 0:
                    msg += f"{stock}: ${data['stocks'][stock]}\n"
                else:
                    msg += f"{stock}: ${data['stocks'][stock]:<9}"
                i += 1

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
        member = str(ctx.author.id)

        if symbol in data["stockbal"][member]:
            await ctx.send(
                f"```You have {data['stockbal'][member][symbol]:.2f} stocks in {symbol}```"
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

            net_value = 0
            msg = f"{member.display_name}'s stock profile:\n"

            for stock in data["stockbal"][str(member.id)]:
                msg += f"\n{stock}: {data['stockbal'][str(member.id)][stock]:<15.2f} Price: ${data['stocks'][stock]}"
                net_value += (
                    data["stockbal"][str(member.id)][stock] * data["stocks"][stock]
                )

            await ctx.send(f"```{msg}\n\nNet Value: ${net_value:.2f}```")
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
        """Invests in stocks.

        symbol: str
            The symbol of the stock to buy.
        cash: int
            The amount of money to invest.
        """
        if symbol is None or cash is None:
            return await ctx.send(
                f"```Usage:\n{ctx.prefix}{ctx.command} {ctx.command.signature}```"
            )

        user = str(ctx.author.id)

        with open("json/economy.json") as file:
            data = ujson.load(file)

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
