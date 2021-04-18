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
        if not member:
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

        if not bal:
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
        if not symbol or not cash:
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

        if not bal:
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

    @commands.group(name="crypto", aliases=["coin"])
    async def _crypto(self, ctx):
        """Gets some information about crypto currencies."""
        if ctx.invoked_subcommand is not None:
            return

        embed = discord.Embed(colour=discord.Colour.blurple())

        if not ctx.subcommand_passed:
            embed.description = "```No subcommand passed```"
            await ctx.send(embed=embed)

        symbol = ctx.subcommand_passed.upper().encode()
        crypto = self.crypto.get(symbol)

        if not crypto:
            embed.description = f"```Couldn't find {symbol}```"
            return await ctx.send(embed=embed)

        crypto = ujson.loads(crypto)
        max_supply = f"{crypto['max_supply']:,}" if crypto["max_supply"] else "N/A"

        embed.description = textwrap.dedent(
            f"""
                ```diff
                {crypto['name']} [{symbol.decode()}]

                Price:
                ${crypto['price']:,.2f}

                Circulating/Max Supply:
                {crypto['circulating_supply']:,}/{max_supply}

                Market Cap:
                ${crypto['market_cap']:,.2f}

                24h Change:
                {crypto['change_24h']}%

                24h Volume:
                {crypto['volume_24h']}
                ```
            """
        )

        await ctx.send(embed=embed)

    @_crypto.command(aliases=["b"])
    async def buy(self, ctx, symbol: str, cash: int):
        """Buys an amount of crypto.

        coin: str
            The symbol of the crypto.
        cash: int
            How much money you want to invest in the coin.
        """
        embed = discord.Embed(color=discord.Color.blurple())
        symbol = symbol.upper()
        price = self.crypto.get(symbol.encode())

        if not price:
            embed.description = f"```Couldn't find crypto {symbol}```"
            return await ctx.send(embed=embed)

        price = ujson.loads(price)["price"]
        member_id = str(ctx.author.id).encode()
        bal = self.bal.get(member_id)

        if not bal:
            bal = 1000
        else:
            bal = float(bal)

        if bal < cash:
            embed.description = "```You don't have enough cash```"
            return await ctx.send(embed=embed)

        amount = cash / float(price)

        cryptobal = self.cryptobal.get(member_id)

        if not cryptobal:
            cryptobal = {}
        else:
            cryptobal = ujson.loads(cryptobal)

        if symbol not in cryptobal:
            cryptobal[symbol] = 0

        cryptobal[symbol] += amount
        bal -= cash

        embed = discord.Embed(
            title=f"You bought {amount:.2f} in {symbol}",
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
        symbol = symbol.upper()
        price = self.crypto.get(symbol.encode())
        embed = discord.Embed(color=discord.Color.blurple())

        if not price:
            embed.description = f"```Couldn't find {symbol}```"
            return await ctx.send(embed=embed)

        price = ujson.loads(price)["price"]
        member_id = str(ctx.author.id).encode()
        cryptobal = self.cryptobal.get(member_id)

        if not cryptobal:
            embed.description = f"```You have never invested in {symbol}```"
            return await ctx.send(embed=embed)

        cryptobal = ujson.loads(cryptobal)

        if cryptobal[symbol] < amount:
            embed.description = f"```Not enough {symbol} you have: {cryptobal[symbol]}```"
            return await ctx.send(embed=embed)

        bal = self.bal.get(member_id)

        if not bal:
            bal = 1000
        else:
            bal = float(bal)

        cash = amount * float(price)

        cryptobal[symbol] -= amount

        if cryptobal[symbol] == 0:
            cryptobal.pop(symbol, None)

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
        msg = f"{member.display_name}'s crypto profile:\n"

        for crypto in cryptobal:
            data = ujson.loads(self.crypto.get(crypto.encode()))

            msg += f"\n{str(data['change_24h'])[0]} {crypto:>4}: {cryptobal[crypto]:<14.2f}"
            msg += f" Price: ${data['price']:<7.2f} {data['change_24h']}%"

            net_value += cryptobal[crypto] * float(data["price"])

        embed.description = f"```diff\n{msg}\n\nNet Value: ${net_value:.2f}```"
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

        max_supply = f"{crypto['max_supply']:,}" if crypto["max_supply"] else "N/A"

        embed.description = textwrap.dedent(
            f"""
                ```diff
                {crypto['name']} [{symbol.decode()}]

                Bal: {cryptobal[symbol]}

                Price:
                ${crypto['price']:,.2f}

                Circulating/Max Supply:
                {crypto['circulating_supply']:,}/{max_supply}

                Market Cap:
                ${crypto['market_cap']:,.2f}

                24h Change:
                {crypto['change_24h']}%

                24h Volume:
                {crypto['volume_24h']}
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


def setup(bot: commands.Bot) -> None:
    """Starts stocks cog."""
    bot.add_cog(stocks(bot))
