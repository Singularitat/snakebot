import textwrap
from decimal import Decimal

import discord
import orjson
from discord.ext import commands, pages


class stocks(commands.Cog):
    """Stock related commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.DB = bot.DB

    @commands.group()
    async def stock(self, ctx):
        """Gets the current price of a stock.

        symbol: str
            The symbol of the stock to find.
        """
        if ctx.invoked_subcommand:
            return

        embed = discord.Embed(colour=discord.Colour.blurple())

        if not ctx.subcommand_passed:
            embed = discord.Embed(color=discord.Color.blurple())
            embed.description = (
                f"```Usage: {ctx.prefix}stock [buy/sell/bal/profile/list/history]"
                f" or {ctx.prefix}stock [ticker]```"
            )
            return await ctx.send(embed=embed)

        symbol = ctx.subcommand_passed.upper()
        stock = self.DB.get_stock(symbol)
        embed = discord.Embed(color=discord.Color.blurple())

        if not stock:
            embed.description = f"```No stock found for {symbol}```"
            return await ctx.send(embed=embed)

        change = stock["change"]
        sign = "" if change[0] == "-" else "+"

        embed.title = f"{symbol} [{stock['name']}]"
        embed.add_field(name="Price", value=f"```${stock['price']}```")
        embed.add_field(name="Market Cap", value=f"```${stock['cap']}```", inline=False)
        embed.add_field(name="24h Change", value=f"```diff\n{sign}{change}```")
        embed.add_field(
            name="Percent 24h Change", value=f"```diff\n{sign}{stock['%change']}%```"
        )
        embed.set_image(url=f"https://charts2.finviz.com/chart.ashx?s=l&p=w&t={symbol}")

        await ctx.send(embed=embed)

    @stock.command()
    async def sell(self, ctx, symbol, amount):
        """Sells stock.

        symbol: str
            The symbol of the stock to sell.
        amount: float
            The amount of stock to sell.
        """
        embed = discord.Embed(color=discord.Color.blurple())

        symbol = symbol.upper()
        price = self.DB.get_stock(symbol)

        if not price:
            embed.description = f"```Couldn't find stock {symbol}```"
            return await ctx.send(embed=embed)

        price = price["price"]
        member_id = str(ctx.author.id).encode()
        stockbal = self.DB.get_stockbal(member_id)

        if not stockbal:
            embed.description = f"```You have never invested in {symbol}```"
            return await ctx.send(embed=embed)

        if amount[-1] == "%":
            amount = stockbal[symbol]["total"] * ((float(amount[:-1])) / 100)
        else:
            amount = float(amount)

        if amount < 0:
            embed.description = "```You can't sell a negative amount of stocks```"
            return await ctx.send(embed=embed)

        if stockbal[symbol]["total"] < amount:
            embed.description = (
                f"```Not enough stock you have: {stockbal[symbol]['total']}```"
            )
            return await ctx.send(embed=embed)

        bal = self.DB.get_bal(member_id)

        cash = amount * float(price)

        stockbal[symbol]["total"] -= amount

        if stockbal[symbol]["total"] == 0:
            stockbal.pop(symbol, None)
        else:
            stockbal[symbol]["history"].append((-amount, cash))

        bal += Decimal(cash)

        embed = discord.Embed(
            title=f"Sold {amount:.2f} stocks for ${cash:.2f}",
            color=discord.Color.blurple(),
        )
        embed.set_footer(text=f"Balance: ${bal:,}")

        await ctx.send(embed=embed)

        self.DB.put_bal(member_id, bal)
        self.DB.put_stockbal(member_id, stockbal)

    @stock.command(aliases=["buy"])
    async def invest(self, ctx, symbol, cash: float):
        """Buys stock or if nothing is passed in it shows the price of some stocks.
        symbol: str
            The symbol of the stock to buy.
        cash: int
            The amount of money to invest.
        """
        embed = discord.Embed(color=discord.Color.blurple())

        if cash < 0:
            embed.description = "```You can't buy a negative amount of stocks```"
            return await ctx.send(embed=embed)

        symbol = symbol.upper()
        stock = self.DB.get_stock(symbol)

        if not stock:
            embed.description = f"```Couldn't find stock {symbol}```"
            return await ctx.send(embed=embed)

        stock = stock["price"]
        member_id = str(ctx.author.id).encode()
        bal = self.DB.get_bal(member_id)

        if bal < cash:
            embed.description = "```You don't have enough cash```"
            return await ctx.send(embed=embed)

        amount = cash / float(stock)

        stockbal = self.DB.get_stockbal(member_id)

        if symbol not in stockbal:
            stockbal[symbol] = {"total": 0, "history": [(amount, cash)]}
        else:
            stockbal[symbol]["history"].append((amount, cash))

        stockbal[symbol]["total"] += amount
        bal -= Decimal(cash)

        embed = discord.Embed(
            title=f"You bought {amount:.2f} stocks in {symbol}",
            color=discord.Color.blurple(),
        )
        embed.set_footer(text=f"Balance: ${bal:,}")

        await ctx.send(embed=embed)

        self.DB.put_bal(member_id, bal)
        self.DB.put_stockbal(member_id, stockbal)

    @stock.command(aliases=["balance"])
    async def bal(self, ctx, symbol):
        """Shows the amount of stocks you have bought in a stock.

        symbol: str
            The symbol of the stock to find.
        """
        symbol = symbol.upper()
        member_id = str(ctx.author.id).encode()
        stockbal = self.DB.get_stockbal(member_id)
        embed = discord.Embed(color=discord.Color.blurple())

        if not stockbal:
            embed.description = "```You have never invested```"
            return await ctx.send(embed=embed)

        if symbol not in stockbal:
            embed.description = f"```You have never invested in {symbol}```"
            return await ctx.send(embed=embed)

        stock = self.DB.get_stock(symbol)

        trades = [
            trade[1] / trade[0] for trade in stockbal[symbol]["history"] if trade[0] > 0
        ]
        change = ((float(stock["price"]) / (sum(trades) / len(trades))) - 1) * 100

        embed.description = textwrap.dedent(
            f"""
                ```diff
                You have {stockbal[symbol]['total']:.2f} stocks in {symbol}

                Price: {stock['price']}

                Percent Gain/Loss:
                {"" if change < 0 else "+"}{change:.2f}%

                Market Cap: {stock['cap']}
                ```
            """
        )

        await ctx.send(embed=embed)

    @stock.command(aliases=["p"])
    async def profile(self, ctx, member: discord.Member = None):
        """Gets someone's stock profile.

        member: discord.Member
            The member whose stockprofile will be shown
        """
        member = member or ctx.author

        member_id = str(member.id).encode()
        stockbal = self.DB.get_stockbal(member_id)
        embed = discord.Embed(color=discord.Color.blurple())

        if not stockbal:
            embed.description = "```You have never invested```"
            return await ctx.send(embed=embed)

        if len(stockbal) == 0:
            embed.description = "```You have sold all your stocks.```"
            return await ctx.send(embed=embed)

        net_value = 0
        msg = (
            f"{member.display_name}'s stock profile:\n\n"
            "Name:    Amount:      Price:             Percent Gain:\n"
        )

        for stock in stockbal:
            data = self.DB.get_stock(stock)
            price = float(data["price"])

            trades = [
                trade[1] / trade[0]
                for trade in stockbal[stock]["history"]
                if trade[0] > 0
            ]
            change = ((price / (sum(trades) / len(trades))) - 1) * 100
            color = "31" if change < 0 else "32"

            msg += (
                f"[2;{color}m{stock + ':':<8} {stockbal[stock]['total']:<13.2f}"
                f"${price:<17.2f} {change:.2f}%\n[0m"
            )

            net_value += stockbal[stock]["total"] * price

        embed.description = f"```ansi\n{msg}\nNet Value: ${net_value:.2f}```"
        await ctx.send(embed=embed)

    @stock.command()
    async def list(self, ctx):
        """Shows the prices of stocks from the nasdaq api."""
        messages = []
        stocks_ = ""
        for i, (stock, price) in enumerate(self.DB.stocks, start=1):
            price = orjson.loads(price)["price"]

            if not i % 3:
                stocks_ += f"{stock.decode():}: ${float(price):.2f}\n"
            else:
                stocks_ += f"{stock.decode():}: ${float(price):.2f}\t".expandtabs()

            if not i % 99:
                messages.append(discord.Embed(description=f"```prolog\n{stocks_}```"))
                stocks_ = ""

        if i % 99:
            messages.append(discord.Embed(description=f"```prolog\n{stocks_}```"))

        paginator = pages.Paginator(pages=messages)
        await paginator.send(ctx)

    @stock.command(aliases=["h"])
    async def history(self, ctx, member: discord.Member = None, amount=10):
        """Gets a members crypto transaction history.

        member: discord.Member
        amount: int
            How many transactions to get
        """
        member = member or ctx.author

        embed = discord.Embed(color=discord.Color.blurple())
        stockbal = self.DB.get_stockbal(str(member.id).encode())

        if not stockbal:
            embed.description = "```You haven't invested.```"
            return await ctx.send(embed=embed)

        msg = ""

        for stock_name, stock_data in stockbal.items():
            msg += f"{stock_name}:\n"
            for trade in stock_data["history"]:
                if trade[0] < 0:
                    kind = "Sold"
                else:
                    kind = "Bought"
                msg += f"{kind} {abs(trade[0]):.2f} for ${trade[1]:.2f}\n"
            msg += "\n"

        embed.description = f"```{msg}```"
        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    """Starts stocks cog."""
    bot.add_cog(stocks(bot))
