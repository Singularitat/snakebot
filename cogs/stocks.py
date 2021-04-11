import discord
from discord.ext import commands
import ujson
import textwrap


class stocks(commands.Cog):
    """Stock related commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.stocks = self.bot.db.prefixed_db(b"stocks-")
        self.bal = self.bot.db.prefixed_db(b"bal-")
        self.stockbal = self.bot.db.prefixed_db(b"stockbal-")

    @commands.command()
    async def stocks(self, ctx):
        """Shows the price of stocks from yahoo finance."""
        msg = ""
        i = 1

        for stock, price in self.stocks:
            price = ujson.loads(price)["price"]
            if len(msg) >= 2000:
                break

            if i % 3 == 0:
                msg += f"{stock.decode():<5}: ${price}\n"
            else:
                msg += f"{stock.decode():<5}: ${price:<9}"
            i += 1

        embed = discord.Embed(
            color=discord.Color.blurple(), description=f"```\n{msg}```"
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def stockbal(self, ctx, symbol):
        """Shows the amount of stocks you have bought in a stock.

        symbol: str
            The symbol of the stock to find.
        """
        symbol = symbol.upper()
        member_id = str(ctx.author.id).encode()

        stockbal = self.stockbal.get(member_id)

        if not stockbal:
            return await ctx.send("```You have never invested```")

        stockbal = ujson.loads(stockbal)

        if symbol not in stockbal:
            return await ctx.send(f"```You have never invested in {symbol}```")

        stock = ujson.loads(self.stocks.get(symbol.encode()))

        embed = discord.Embed(color=discord.Color.blurple())

        embed.description = textwrap.dedent(
            f"""
                ```diff
                You have {stockbal[symbol]:.2f} stocks in {symbol}

                Price: {stock['price']}

                Change from last trading day:
                {stock['change']}
                {stock['%change']}

                Volume: {stock['volume']}
                3 Month Average: {stock['3Mvolume']}

                Market Cap: {stock['cap']}
                ```
            """
        )

        await ctx.send(embed=embed)

    @commands.command(aliases=["stockprof", "stockp"])
    async def stockprofile(self, ctx, member: discord.Member = None):
        """Gets someone's stock profile.

        member: discord.Member
            The member whos stockprofile will be shown
        """
        if member is None:
            member = ctx.author

        member_id = str(member.id).encode()
        stockbal = self.stockbal.get(member_id)

        if not stockbal:
            return await ctx.send("```You have never invested```")

        stockbal = ujson.loads(stockbal)

        net_value = 0
        msg = f"{member.display_name}'s stock profile:\n"

        for stock in stockbal:
            data = ujson.loads(self.stocks.get(stock.encode()))

            msg += f"\n{data['%change'][0]} {stock:>4}: {stockbal[stock]:<14.2f}"
            msg += f" Price: ${data['price']:<7} {data['%change']}"

            net_value += stockbal[stock] * float(data["price"])

        embed = discord.Embed(color=discord.Color.blurple())

        embed.description = f"```diff\n{msg}\n\nNet Value: ${net_value:.2f}```"

        await ctx.send(embed=embed)

    @commands.command(aliases=["price"])
    async def stockprice(self, ctx, symbol):
        """Gets the current price of a stock.

        symbol: str
            The symbol of the stock to find.
        """
        symbol = symbol.upper()

        stock = self.stocks.get(symbol.encode())

        if not stock:
            return await ctx.send(f"```No stock found for {symbol}```")

        stock = ujson.loads(stock)

        embed = discord.Embed(
            color=discord.Color.blurple(), title=f"{symbol} [{stock['name']}]"
        )

        embed.description = textwrap.dedent(
            f"""
                ```diff
                Price: {stock['price']}

                Change from last trading day:
                {stock['change']}
                {stock['%change']}

                Volume: {stock['volume']}
                3 Month Average: {stock['3Mvolume']}

                Market Cap: {stock['cap']}
                ```
            """
        )

        await ctx.send(embed=embed)

    @commands.command(aliases=["sell"])
    async def sellstock(self, ctx, symbol, amount: float):
        """Sells stock.

        symbol: str
            The symbol of the stock to sell.
        amount: float
            The amount of stock to sell.
        """
        symbol = symbol.upper()

        price = self.stocks.get(symbol.encode())

        if not price:
            return await ctx.send(f"```Couldn't find stock {symbol}```")

        price = ujson.loads(price)["price"]
        member_id = str(ctx.author.id).encode()
        stockbal = self.stockbal.get(member_id)

        if not stockbal:
            return await ctx.send(f"```You have never invested in {symbol}```")

        stockbal = ujson.loads(stockbal)

        if stockbal[symbol] < amount:
            return await ctx.send(
                f"```Not enough stock you have: {stockbal[symbol]}```"
            )

        bal = self.bal.get(member_id)

        if bal is None:
            bal = 1000
        else:
            bal = float(bal)

        cash = amount * float(price)

        stockbal[symbol] -= amount

        if stockbal[symbol] == 0:
            stockbal.pop(symbol, None)

        bal += cash

        embed = discord.Embed(
            title=f"Sold {amount:.2f} stocks for ${cash:.2f}",
            color=discord.Color.blurple(),
        )
        embed.set_footer(text=f"Balance: ${bal}")

        await ctx.send(embed=embed)

        self.bal.put(member_id, str(bal).encode())
        self.stockbal.put(member_id, ujson.dumps(stockbal).encode())

    @commands.command(aliases=["buy"])
    async def invest(self, ctx, symbol=None, cash: float = None):
        """Buys stock or if nothing is passed in it shows the price of some stocks.
        symbol: str
            The symbol of the stock to buy.
        cash: int
            The amount of money to invest.
        """
        if symbol is None or cash is None:
            return await ctx.send(
                f"```Usage:\n{ctx.prefix}{ctx.command} {ctx.command.signature}```"
            )

        symbol = symbol.upper()

        stock = self.stocks.get(symbol.encode())

        if not stock:
            return await ctx.send(f"```Couldn't find stock {symbol}```")

        stock = ujson.loads(stock)["price"]
        member_id = str(ctx.author.id).encode()
        bal = self.bal.get(member_id)

        if bal is None:
            bal = 1000
        else:
            bal = float(bal)

        if bal < cash:
            return await ctx.send("```You don't have enough cash```")

        amount = cash / float(stock)

        stockbal = self.stockbal.get(member_id)

        if not stockbal:
            stockbal = {}
        else:
            stockbal = ujson.loads(stockbal)

        if symbol not in stockbal:
            stockbal[symbol] = 0

        stockbal[symbol] += amount
        bal -= cash

        embed = discord.Embed(
            title=f"You bought {amount:.2f} stocks in {symbol}",
            color=discord.Color.blurple(),
        )
        embed.set_footer(text=f"Balance: ${bal}")

        await ctx.send(embed=embed)

        self.bal.put(member_id, str(bal).encode())
        self.stockbal.put(member_id, ujson.dumps(stockbal).encode())

    @commands.command(aliases=["networth"])
    async def net(self, ctx, member: discord.Member = None):
        """Gets a members net worth.

        members: discord.Member
            The member whos net worth will be returned.
        """
        if not member:
            member = ctx.author

        member_id = str(member.id).encode()
        bal = self.bal.get(member_id)

        if not bal:
            self.bal.put(member_id, b"1000")
            bal = 1000
        else:
            bal = float(bal)

        stockbal = self.stockbal.get(member_id)

        embed = discord.Embed(color=discord.Color.blurple())

        if not stockbal:
            embed.add_field(
                name=f"{member.display_name}'s net worth",
                value=f"${bal}",
                inline=False,
            )
            embed.set_footer(text=f"Stocks: $0\nBalance: ${bal:,.2f}")
            return await ctx.send(embed=embed)

        stock_value = sum(
            [
                stock[1]
                * float(ujson.loads(self.stocks.get(stock[0].encode()))["price"])
                for stock in ujson.loads(stockbal).items()
            ]
        )

        embed.add_field(
            name=f"{member.display_name}'s net worth",
            value=f"${bal + stock_value:,.2f}",
            inline=False,
        )

        embed.set_footer(text=f"Stocks: ${stock_value:,.2f}\nBalance: ${bal:,.2f}")

        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    """Starts stocks cog."""
    bot.add_cog(stocks(bot))
