import discord
from discord.ext import commands, menus
import orjson
import textwrap
import cogs.utils.database as DB


class StockMenu(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=99)

    async def format_page(self, menu, entries):
        return discord.Embed(
            color=discord.Color.blurple(), description=f"```{''.join(entries)}```"
        )


class stocks(commands.Cog):
    """Stock related commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name="stocks")
    async def _stocks(self, ctx):
        """Shows the price of stocks from yahoo finance."""
        data = []
        for i, (stock, price) in enumerate(DB.stocks, start=1):
            price = orjson.loads(price)["price"]

            if not i % 3:
                data.append(f"{stock.decode():}: ${float(price):.2f}\n")
            else:
                data.append(f"{stock.decode():}: ${float(price):.2f}\t".expandtabs())

        pages = menus.MenuPages(
            source=StockMenu(data),
            clear_reactions_after=True,
            delete_message_after=True,
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
        stockbal = await DB.get_stockbal(member_id)
        embed = discord.Embed(color=discord.Color.blurple())

        if not stockbal:
            embed.description = "```You have never invested```"
            return await ctx.send(embed=embed)

        if symbol not in stockbal:
            embed.description = f"```You have never invested in {symbol}```"
            return await ctx.send(embed=embed)

        stock = await DB.get_stock(symbol)

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
        member = member or ctx.author

        member_id = str(member.id).encode()
        stockbal = await DB.get_stockbal(member_id)
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
            " Name:  Amount:        Price:             Percent Gain:\n"
        )

        for stock in stockbal:
            data = await DB.get_stock(stock)
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

    @commands.command(aliases=["price", "stock"])
    async def stockprice(self, ctx, symbol):
        """Gets the current price of a stock.

        symbol: str
            The symbol of the stock to find.
        """
        symbol = symbol.upper()
        stock = await DB.get_stock(symbol)
        embed = discord.Embed(color=discord.Color.blurple())

        if not stock:
            embed.description = f"```No stock found for {symbol}```"
            return await ctx.send(embed=embed)

        sign = "" if stock["change"][0] == "-" else "+"

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
        price = await DB.get_stock(symbol)

        if not price:
            embed.description = f"```Couldn't find stock {symbol}```"
            return await ctx.send(embed=embed)

        price = price["price"]
        member_id = str(ctx.author.id).encode()
        stockbal = await DB.get_stockbal(member_id)

        if not stockbal:
            embed.description = f"```You have never invested in {symbol}```"
            return await ctx.send(embed=embed)

        if stockbal[symbol]["total"] < amount:
            embed.description = (
                f"```Not enough stock you have: {stockbal[symbol]['total']}```"
            )
            return await ctx.send(embed=embed)

        bal = await DB.get_bal(member_id)

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

        await DB.put_bal(member_id, bal)
        await DB.put_stockbal(member_id, stockbal)

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
        stock = await DB.get_stock(symbol)

        if not stock:
            embed.description = f"```Couldn't find stock {symbol}```"
            return await ctx.send(embed=embed)

        stock = stock["price"]
        member_id = str(ctx.author.id).encode()
        bal = await DB.get_bal(member_id)

        if bal < cash:
            embed.description = "```You don't have enough cash```"
            return await ctx.send(embed=embed)

        amount = cash / float(stock)

        stockbal = await DB.get_stockbal(member_id)

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

        await DB.put_bal(member_id, bal)
        await DB.put_stockbal(member_id, stockbal)

    @commands.command()
    async def nettop(self, ctx, amount: int = 10):
        """Gets members with the highest net worth"""

        def get_value(values, db):
            if values:
                return sum(
                    [
                        stock[1]["total"]
                        * float(orjson.loads(db.get(stock[0].encode()))["price"])
                        for stock in values.items()
                    ]
                )

            return 0

        net_top = []

        for member_id, value in DB.bal:
            stock_value = get_value(await DB.get_stockbal(member_id), DB.stocks)
            crypto_value = get_value(await DB.get_cryptobal(member_id), DB.crypto)
            # fmt: off
            if (member := self.bot.get_user(int(member_id))):
                net_top.append(
                    (float(value) + stock_value + crypto_value, member.display_name)
                )
            # fmt: on

        net_top = sorted(net_top, reverse=True)[:amount]
        embed = discord.Embed(color=discord.Color.blurple())

        embed.title = f"Top {len(net_top)} Richest Members"
        embed.description = "\n".join(
            [f"**{member}:** ${bal:,.2f}" for bal, member in net_top]
        )
        await ctx.send(embed=embed)

    @commands.command(aliases=["networth"])
    async def net(self, ctx, member: discord.Member = None):
        """Gets a members net worth.

        members: discord.Member
            The member whos net worth will be returned.
        """
        member = member or ctx.author

        member_id = str(member.id).encode()
        bal = await DB.get_bal(member_id)

        embed = discord.Embed(color=discord.Color.blurple())

        def get_value(values, db):
            if values:
                return sum(
                    [
                        stock[1]["total"]
                        * float(orjson.loads(db.get(stock[0].encode()))["price"])
                        for stock in values.items()
                    ]
                )

            return 0

        stock_value = get_value(await DB.get_stockbal(member_id), DB.stocks)
        crypto_value = get_value(await DB.get_cryptobal(member_id), DB.crypto)

        embed.add_field(
            name=f"{member.display_name}'s net worth",
            value=f"${bal + stock_value + crypto_value:,.2f}",
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
            embed = discord.Embed(
                color=discord.Color.blurple(),
                description=f"```Usage: {ctx.prefix}coin [symbol]```",
            )
            return await ctx.send(embed=embed)

        symbol = ctx.subcommand_passed.upper()
        crypto = await DB.get_crypto(symbol)

        if not crypto:
            embed.description = f"```Couldn't find {symbol}```"
            return await ctx.send(embed=embed)

        sign = "+" if crypto["change_24h"] >= 0 else ""

        embed.set_author(
            name=f"{crypto['name']} [{symbol}]",
            icon_url=f"https://s2.coinmarketcap.com/static/img/coins/64x64/{crypto['id']}.png",
        )
        embed.description = textwrap.dedent(
            f"""
                ```diff
                Price:
                ${crypto['price']:,.2f}

                Circulating/Max Supply:
                {crypto['circulating_supply']:,}/{crypto['max_supply']:,}

                Market Cap:
                ${crypto['market_cap']:,.2f}

                24h Change:
                {sign}{crypto['change_24h']}%

                24h Volume:
                {crypto['volume_24h']:,.2f}
                ```
            """
        )
        embed.set_image(
            url=f"https://s3.coinmarketcap.com/generated/sparklines/web/1d/usd/{crypto['id']}.png"
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
        data = await DB.get_crypto(symbol)

        if not data:
            embed.description = f"```Couldn't find crypto {symbol}```"
            return await ctx.send(embed=embed)

        price = float(data["price"])
        member_id = str(ctx.author.id).encode()
        bal = await DB.get_bal(member_id)

        if bal < cash:
            embed.description = "```You don't have enough cash```"
            return await ctx.send(embed=embed)

        amount = cash / price

        cryptobal = await DB.get_cryptobal(member_id)

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

        await DB.put_bal(member_id, bal)
        await DB.put_cryptobal(member_id, cryptobal)

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
        price = await DB.get_crypto(symbol)

        if not price:
            embed.description = f"```Couldn't find {symbol}```"
            return await ctx.send(embed=embed)

        price = price["price"]
        member_id = str(ctx.author.id).encode()
        cryptobal = await DB.get_cryptobal(member_id)

        if not cryptobal:
            embed.description = "```You haven't invested.```"
            return await ctx.send(embed=embed)

        if symbol not in cryptobal:
            embed.description = f"```You haven't invested in {symbol}.```"
            return await ctx.send(embed=embed)

        if cryptobal[symbol]["total"] < amount:
            embed.description = (
                f"```Not enough {symbol} you have: {cryptobal[symbol]['total']}```"
            )
            return await ctx.send(embed=embed)

        bal = await DB.get_bal(member_id)
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

        await DB.put_bal(member_id, bal)
        await DB.put_cryptobal(member_id, cryptobal)

    @_crypto.command(aliases=["p"])
    async def profile(self, ctx, member: discord.Member = None):
        """Gets someone's crypto profile.

        member: discord.Member
            The member whos crypto profile will be shown.
        """
        member = member or ctx.author

        member_id = str(member.id).encode()
        cryptobal = await DB.get_cryptobal(member_id)
        embed = discord.Embed(color=discord.Color.blurple())

        if not cryptobal:
            embed.description = "```You haven't invested.```"
            return await ctx.send(embed=embed)

        net_value = 0
        msg = (
            f"{member.display_name}'s crypto profile:\n\n"
            " Name:                 Price:             Percent Gain:\n"
        )

        for crypto in cryptobal:
            data = await DB.get_crypto(crypto)

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

        cryptobal = await DB.get_cryptobal(member_id)
        embed = discord.Embed(color=discord.Color.blurple())

        if not cryptobal:
            embed.description = "```You haven't invested.```"
            return await ctx.send(embed=embed)

        if symbol not in cryptobal:
            embed.description = f"```You haven't invested in {symbol}```"
            return await ctx.send(embed=embed)

        crypto = await DB.get_crypto(symbol)

        trades = [
            trade[1] / trade[0]
            for trade in cryptobal[symbol]["history"]
            if trade[0] > 0
        ]
        change = ((crypto["price"] / (sum(trades) / len(trades))) - 1) * 100
        sign = "" if str(crypto["change_24h"])[0] == "-" else "+"

        embed.set_author(
            name=f"{crypto['name']} [{symbol}]",
            icon_url=f"https://s2.coinmarketcap.com/static/img/coins/64x64/{crypto['id']}.png",
        )
        embed.description = textwrap.dedent(
            f"""
                ```diff
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
        embed.set_image(
            url=f"https://s3.coinmarketcap.com/generated/sparklines/web/1d/usd/{crypto['id']}.png"
        )

        await ctx.send(embed=embed)

    @_crypto.command()
    async def list(self, ctx):
        """Shows the prices of crypto with pagination."""
        data = []
        for i, (stock, price) in enumerate(DB.crypto, start=1):
            price = orjson.loads(price)["price"]

            if not i % 3:
                data.append(f"{stock.decode()}: ${float(price):.2f}\n")
            else:
                data.append(f"{stock.decode()}: ${float(price):.2f}\t".expandtabs())

        pages = menus.MenuPages(
            source=StockMenu(data),
            clear_reactions_after=True,
            delete_message_after=True,
        )
        await pages.start(ctx)

    @_crypto.command()
    async def history(self, ctx, member: discord.Member = None, amount=10):
        member = member or ctx.author

        embed = discord.Embed(color=discord.Color.blurple())
        cryptobal = await DB.get_cryptobal(str(member.id).encode())

        if not cryptobal:
            embed.description = "```You haven't invested.```"
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
