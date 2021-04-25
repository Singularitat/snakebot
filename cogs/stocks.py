import discord
from discord.ext import commands, menus
import ujson
import textwrap


class StockMenu(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=100)

    async def format_page(self, menu, entries):
        msg = "\n"
        i = 1
        for stock, price in entries:
            price = ujson.loads(price)["price"]
            if len(msg) >= 2000:
                break

            if i % 3 == 0:
                msg += f"{stock.decode():<5}: ${float(price):.2f}\n"
            else:
                msg += f"{stock.decode():<5}: ${float(price):<9.2f}"
            i += 1

        embed = discord.Embed(color=discord.Color.blurple(), description=f"```{msg}```")
        return embed


class stocks(commands.Cog):
    """Stock related commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.cryptobal = self.bot.db.prefixed_db(b"cryptobal-")
        self.crypto = self.bot.db.prefixed_db(b"crypto-")
        self.stocks = self.bot.db.prefixed_db(b"stocks-")
        self.bal = self.bot.db.prefixed_db(b"bal-")
        self.stockbal = self.bot.db.prefixed_db(b"stockbal-")

    def bal_check(self, member_id):
        bal = self.bal.get(member_id)

        if not bal:
            bal = 1000
        else:
            bal = float(bal)

        return bal

    @commands.command(name="wipestocks")
    async def wipe_stock_data(self, ctx):
        """Wipes the stocks db."""
        with self.stocks.write_batch() as wb:
            for symbol in self.stocks.iterator(include_value=False):
                wb.delete(symbol)

    @commands.command(name="stocks")
    async def _stocks(self, ctx):
        """Shows the price of stocks from yahoo finance."""
        pages = menus.MenuPages(
            source=StockMenu(list(self.stocks)), clear_reactions_after=True
        )
        await pages.start(ctx)

    @commands.command()
    async def stockbal(self, ctx, symbol):
        """Shows the amount of stocks you have bought in a stock.

        symbol: str
            The symbol of the stock to find.
        """
        symbol = symbol.upper()
        member_id = str(ctx.author.id).encode()
        stockbal = self.stockbal.get(member_id)
        embed = discord.Embed(color=discord.Color.blurple())

        if not stockbal:
            embed.description = "```You have never invested```"
            return await ctx.send(embed=embed)

        stockbal = ujson.loads(stockbal)

        if symbol not in stockbal:
            embed.description = f"```You have never invested in {symbol}```"
            return await ctx.send(embed=embed)

        stock = ujson.loads(self.stocks.get(symbol.encode()))

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
                {"" if str(change)[0] == "-" else "+"}{change:.2f}%

                Market Cap: {stock['cap']}
                ```
            """
        )

        await ctx.send(embed=embed)

    @commands.command(aliases=["stockp"])
    async def stockprofile(self, ctx, member: discord.Member = None):
        """Gets someone's stock profile.

        member: discord.Member
            The member whos stockprofile will be shown
        """
        if not member:
            member = ctx.author

        member_id = str(member.id).encode()
        stockbal = self.stockbal.get(member_id)
        embed = discord.Embed(color=discord.Color.blurple())

        if not stockbal:
            embed.description = "```You have never invested```"
            return await ctx.send(embed=embed)

        stockbal = ujson.loads(stockbal)

        net_value = 0
        msg = f"{member.display_name}'s stock profile:\n\n"
        msg += " Name:                 Price:             Percent Gain:\n"

        for stock in stockbal:
            data = ujson.loads(self.stocks.get(stock.encode()))
            price = float(data["price"])

            trades = [
                trade[1] / trade[0]
                for trade in stockbal[stock]["history"]
                if trade[0] > 0
            ]
            change = ((price / (sum(trades) / len(trades))) - 1) * 100
            sign = "-" if str(change)[0] == "-" else "+"

            msg += f"{sign} {stock:>4}: {stockbal[stock]['total']:<14.2f}"
            msg += f" Price: ${price:<10.2f} {change:.2f}%\n"

            net_value += stockbal[stock]["total"] * price

        embed.description = f"```diff\n{msg}\nNet Value: ${net_value:.2f}```"
        await ctx.send(embed=embed)

    @commands.command(aliases=["price"])
    async def stockprice(self, ctx, symbol):
        """Gets the current price of a stock.

        symbol: str
            The symbol of the stock to find.
        """
        symbol = symbol.upper()
        stock = self.stocks.get(symbol.encode())
        embed = discord.Embed(color=discord.Color.blurple())

        if not stock:
            embed.description = f"```No stock found for {symbol}```"
            return await ctx.send(embed=embed)

        stock = ujson.loads(stock)
        sign = "" if stock['change'][0] == "-" else "+"

        embed.title = f"{symbol} [{stock['name']}]"
        embed.description = textwrap.dedent(
            f"""
                ```diff
                Price: {stock['price']}

                24h Change:
                {sign}{stock['change']}

                Percent 24h Change:
                {sign}{stock['%change']}

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
        embed = discord.Embed(color=discord.Color.blurple())

        if amount < 0:
            embed.description = "```You can't sell a negative amount of stocks```"
            return await ctx.send(embed=embed)

        symbol = symbol.upper()
        price = self.stocks.get(symbol.encode())

        if not price:
            embed.description = f"```Couldn't find stock {symbol}```"
            return await ctx.send(embed=embed)

        price = ujson.loads(price)["price"]
        member_id = str(ctx.author.id).encode()
        stockbal = self.stockbal.get(member_id)

        if not stockbal:
            embed.description = f"```You have never invested in {symbol}```"
            return await ctx.send(embed=embed)

        stockbal = ujson.loads(stockbal)

        if stockbal[symbol]["total"] < amount:
            embed.description = (
                f"```Not enough stock you have: {stockbal[symbol]['total']}```"
            )
            return await ctx.send(embed=embed)

        bal = self.bal_check(member_id)

        cash = amount * float(price)

        stockbal[symbol]["total"] -= amount

        if stockbal[symbol]["total"] == 0:
            stockbal.pop(symbol, None)
        else:
            stockbal[symbol]["history"].append((-amount, cash))

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
        stock = self.stocks.get(symbol.encode())

        if not stock:
            embed.description = f"```Couldn't find stock {symbol}```"
            return await ctx.send(embed=embed)

        stock = ujson.loads(stock)["price"]
        member_id = str(ctx.author.id).encode()
        bal = self.bal_check(member_id)

        if bal < cash:
            embed.description = "```You don't have enough cash```"
            return await ctx.send(embed=embed)

        amount = cash / float(stock)

        stockbal = self.stockbal.get(member_id)

        if not stockbal:
            stockbal = {}
        else:
            stockbal = ujson.loads(stockbal)

        if symbol not in stockbal:
            stockbal[symbol] = {"total": 0, "history": [(amount, cash)]}
        else:
            stockbal[symbol]["history"].append((amount, cash))

        stockbal[symbol]["total"] += amount
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
        bal = self.bal_check(member_id)

        embed = discord.Embed(color=discord.Color.blurple())

        def get_value(values, db):
            if values:
                return sum(
                    [
                        stock[1]["total"]
                        * float(ujson.loads(db.get(stock[0].encode()))["price"])
                        for stock in ujson.loads(values).items()
                    ]
                )

            return 0

        stock_value = get_value(self.stockbal.get(member_id), self.stocks)
        crypto_value = get_value(self.cryptobal.get(member_id), self.crypto)

        embed.add_field(
            name=f"{member.display_name}'s net worth",
            value=f"${bal + stock_value + crypto_value:,.2f}",
            inline=False,
        )

        embed.set_footer(
            text="Crypto: ${:,.2f}\nStocks: ${:,.2f}\nBalance: ${:,.2f}".format(
                crypto_value, stock_value, bal
            )
        )

        await ctx.send(embed=embed)

    @commands.group(name="crypto", aliases=["coin"])
    async def _crypto(self, ctx):
        """Gets some information about crypto currencies."""
        if ctx.invoked_subcommand is not None:
            return

        embed = discord.Embed(colour=discord.Colour.blurple())

        if not ctx.subcommand_passed:
            embed.description = "```No subcommand passed```"
            return await ctx.send(embed=embed)

        symbol = ctx.subcommand_passed.upper()
        crypto = self.crypto.get(symbol.encode())

        if not crypto:
            embed.description = f"```Couldn't find {symbol}```"
            return await ctx.send(embed=embed)

        crypto = ujson.loads(crypto)

        embed.description = textwrap.dedent(
            f"""
                ```diff
                {crypto['name']} [{symbol}]

                Price:
                ${crypto['price']:,.2f}

                Circulating/Max Supply:
                {crypto['circulating_supply']:,}/{crypto['max_supply']:,}

                Market Cap:
                ${crypto['market_cap']:,.2f}

                24h Change:
                {crypto['change_24h']}%

                24h Volume:
                {crypto['volume_24h']:,.2f}
                ```
            """
        )

        await ctx.send(embed=embed)

    @_crypto.command(aliases=["b"])
    async def buy(self, ctx, symbol: str, cash: float):
        """Buys an amount of crypto.

        coin: str
            The symbol of the crypto.
        cash: int
            How much money you want to invest in the coin.
        """
        embed = discord.Embed(color=discord.Color.blurple())

        if cash < 0:
            embed.description = "```You can't buy a negative amount of crypto```"
            return await ctx.send(embed=embed)

        symbol = symbol.upper()
        data = self.crypto.get(symbol.encode())

        if not data:
            embed.description = f"```Couldn't find crypto {symbol}```"
            return await ctx.send(embed=embed)

        data = ujson.loads(data)

        price = float(data["price"])
        member_id = str(ctx.author.id).encode()
        bal = self.bal_check(member_id)

        if bal < cash:
            embed.description = "```You don't have enough cash```"
            return await ctx.send(embed=embed)

        amount = cash / price

        cryptobal = self.cryptobal.get(member_id)

        if not cryptobal:
            cryptobal = {}
        else:
            cryptobal = ujson.loads(cryptobal)

        if symbol not in cryptobal:
            cryptobal[symbol] = {"total": 0, "history": [(amount, cash)]}
        else:
            cryptobal[symbol]["history"].append((amount, cash))

        cryptobal[symbol]["total"] += amount
        bal -= cash

        embed = discord.Embed(
            title=f"You bought {amount:.2f} {data['name']}",
            color=discord.Color.blurple(),
        )
        embed.set_footer(text=f"Balance: ${bal}")

        await ctx.send(embed=embed)

        self.bal.put(member_id, str(bal).encode())
        self.cryptobal.put(member_id, ujson.dumps(cryptobal).encode())

    @_crypto.command(aliases=["s"])
    async def sell(self, ctx, symbol, amount: float):
        """Sells crypto.

        symbol: str
            The symbol of the crypto to sell.
        amount: float
            The amount to sell.
        """
        embed = discord.Embed(color=discord.Color.blurple())

        if amount < 0:
            embed.description = "```You can't sell a negative amount of crypto```"
            return await ctx.send(embed=embed)

        symbol = symbol.upper()
        price = self.crypto.get(symbol.encode())

        if not price:
            embed.description = f"```Couldn't find {symbol}```"
            return await ctx.send(embed=embed)

        price = ujson.loads(price)["price"]
        member_id = str(ctx.author.id).encode()
        cryptobal = self.cryptobal.get(member_id)

        if not cryptobal:
            embed.description = "```You have never invested.```"
            return await ctx.send(embed=embed)

        cryptobal = ujson.loads(cryptobal)

        if symbol not in cryptobal:
            embed.description = f"```You have never invested in {symbol}.```"
            return await ctx.send(embed=embed)

        if cryptobal[symbol]["total"] < amount:
            embed.description = (
                f"```Not enough {symbol} you have: {cryptobal[symbol]['total']}```"
            )
            return await ctx.send(embed=embed)

        bal = self.bal_check(member_id)
        cash = amount * float(price)

        cryptobal[symbol]["total"] -= amount

        if cryptobal[symbol]["total"] == 0:
            cryptobal.pop(symbol, None)
        else:
            cryptobal[symbol]["history"].append((-amount, cash))

        bal += cash

        embed.title = f"Sold {amount:.2f} {symbol} for ${cash:.2f}"
        embed.set_footer(text=f"Balance: ${bal}")

        await ctx.send(embed=embed)

        self.bal.put(member_id, str(bal).encode())
        self.cryptobal.put(member_id, ujson.dumps(cryptobal).encode())

    @_crypto.command(aliases=["p"])
    async def profile(self, ctx, member: discord.Member = None):
        """Gets someone's crypto profile.

        member: discord.Member
            The member whos crypto profile will be shown.
        """
        if not member:
            member = ctx.author

        member_id = str(member.id).encode()
        cryptobal = self.cryptobal.get(member_id)
        embed = discord.Embed(color=discord.Color.blurple())

        if not cryptobal:
            embed.description = "```You have never invested.```"
            return await ctx.send(embed=embed)

        cryptobal = ujson.loads(cryptobal)

        net_value = 0
        msg = f"{member.display_name}'s crypto profile:\n\n"
        msg += " Name:                 Price:             Percent Gain:\n"

        for crypto in cryptobal:
            data = ujson.loads(self.crypto.get(crypto.encode()))

            trades = [
                trade[1] / trade[0]
                for trade in cryptobal[crypto]["history"]
                if trade[0] > 0
            ]
            change = ((data["price"] / (sum(trades) / len(trades))) - 1) * 100
            sign = "-" if str(change)[0] == "-" else "+"

            msg += f"{sign} {crypto:>4}: {cryptobal[crypto]['total']:<14.2f}"
            msg += f" Price: ${data['price']:<10.2f} {change:.2f}%\n"

            net_value += cryptobal[crypto]["total"] * float(data["price"])

        embed.description = f"```diff\n{msg}\nNet Value: ${net_value:.2f}```"
        await ctx.send(embed=embed)

    @_crypto.command()
    async def bal(self, ctx, symbol: str):
        """Shows how much of a crypto you have.

        symbol: str
            The symbol of the crypto to find.
        """
        symbol = symbol.upper()
        member_id = str(ctx.author.id).encode()

        cryptobal = self.cryptobal.get(member_id)
        embed = discord.Embed(color=discord.Color.blurple())

        if not cryptobal:
            embed.description = "```You have never invested.```"
            return await ctx.send(embed=embed)

        cryptobal = ujson.loads(cryptobal)

        if symbol not in cryptobal:
            embed.description = f"```You have never invested in {symbol}```"
            return await ctx.send(embed=embed)

        crypto = ujson.loads(self.crypto.get(symbol.encode()))

        trades = [
            trade[1] / trade[0]
            for trade in cryptobal[symbol]["history"]
            if trade[0] > 0
        ]
        change = ((crypto["price"] / (sum(trades) / len(trades))) - 1) * 100
        sign = "" if str(crypto["change_24h"])[0] == "-" else "+"

        embed.description = textwrap.dedent(
            f"""
                ```diff
                {crypto['name']} [{symbol}]

                Bal: {cryptobal[symbol]['total']}

                Percent Gain/Loss:
                {"" if str(change)[0] == "-" else "+"}{change:.2f}%

                Price:
                ${crypto['price']:,.2f}

                24h Change:
                {sign}{crypto['change_24h']}%
                ```
            """
        )

        await ctx.send(embed=embed)

    @_crypto.command()
    async def list(self, ctx):
        """Shows the prices of crypto with pagination."""
        pages = menus.MenuPages(
            source=StockMenu(list(self.crypto)), clear_reactions_after=True
        )
        await pages.start(ctx)

    @_crypto.command()
    async def history(self, ctx, member: discord.Member = None, amount=10):
        if not member:
            member = ctx.author

        embed = discord.Embed(color=discord.Color.blurple())
        cryptobal = self.cryptobal.get(str(member.id).encode())

        if not cryptobal:
            embed.description = "```You have never invested.```"
            return await ctx.send(embed=embed)

        cryptobal = ujson.loads(cryptobal)

        if len(cryptobal) == 0:
            embed.description = "```You have sold all your crypto.```"
            return await ctx.send(embed=embed)

        msg = ""

        for crypto in cryptobal:
            msg += f"{crypto}:\n"
            for trade in cryptobal[crypto]["history"]:
                if trade[0] < 0:
                    kind = "Sold"
                else:
                    kind = "Bought"
                msg += f"{kind} {trade[0]:.2f} for ${trade[1]:.2f}\n"
            msg += "\n"

        embed.description = f"```{msg}```"
        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    """Starts stocks cog."""
    bot.add_cog(stocks(bot))
