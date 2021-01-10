import discord
from discord.ext import commands
import json
import random
import aiohttp
from bs4 import BeautifulSoup
import urllib.request
import time
import datetime
import string
from .utils.util import remove_html_tags, clean_non_letters


class Useful(commands.Cog):
    """For actually useful commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        global starttime
        starttime = time.time()

    @commands.command()
    @commands.is_owner()
    async def issue(self, ctx, *, issue):
        """Appends an issue to the snakebot-todo"""
        await ctx.channel.purge(limit=1)
        channel = self.bot.get_channel(776616587322327061)
        message = await channel.fetch_message(787153490996494336)
        issues = str(message.content).replace('`', '')
        issuelist = issues.split("\n")
        issue = string.capwords(issue)
        if issue[0:6] == "Delete":
            issuelist.remove(f'{issue[7:]}')
            issues = "\n".join(issuelist)
            await message.edit(content=f"""```{issues}```""")
        else:
            await message.edit(content=f"""```{issues}
{issue}```""")

    @commands.command()
    async def google(self, ctx, *, search):
        """Grabs a random image from a google image search"""
        search.replace(" ", "+")
        url = f'https://www.google.co.nz/search?q={search}&source=lnms&tbm=isch'
        headers = {"User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebkit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36'}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url) as page:
                soup = BeautifulSoup(await page.text(), 'html.parser')
        image = []
        for a in soup.find_all("img", {"class": "rg_i Q4LuWd"}):
            try:
                image.append(a['data-src'])
            except KeyError:
                pass
        await ctx.send(random.choice(image))

    @commands.command(aliases=['img'])
    async def image(self, ctx, *, search):
        """Searchs and finds a random image from bing"""
        search.replace(" ", "%20")
        url = f'https://www.bing.com/images/search?q={search}&first=1&scenario=ImageBasicHover'
        headers = {"User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36'}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url) as page:
                soup = BeautifulSoup(await page.text(),  'html.parser')
        image = []
        for a in soup.find_all("a", {"class": "iusc"}):
            m = json.loads(a["m"])
            image.append(m["murl"])
        if len(image) == 0:
            await ctx.send(embed=discord.Embed(title='No results found', color=discord.Color.red()))
            return
        link = (random.choice(image))
        x = 0
        while x < 11:
            try:
                x += 1
                code = urllib.request.urlopen(link).getcode()
                if code == 200:
                    await ctx.send(link)
                    break
            except Exception:
                link = (random.choice(image))

    @commands.command()
    async def discordping(self, ctx):
        """Gets the current lag between the bot and discord"""
        await ctx.send(f'{round(self.bot.latency * 1000)}ms')

    @commands.command()
    async def botping(self, ctx):
        """Gets the current lag between the bot sending a message and discord receiving it"""
        x = await ctx.send('Pinging...')
        ms = (x.created_at - ctx.message.created_at).total_seconds()*1000
        await x.edit(content=('{}ms'.format(int(ms))))

    @commands.command(aliases=['urbandictionary'])
    async def urban(self, ctx, search, ran=None):
        """Grabs the definition of something from the urbandictionary"""
        url = f'https://api.urbandictionary.com/v0/define?term={search}'
        async with aiohttp.ClientSession() as session:
            raw_response = await session.get(url)
            response = await raw_response.text()
            urban = json.loads(response)
        if urban['list']:
            if ran is None:
                num = 0
            else:
                num = random.randint(0, len(urban["list"]))
            remove = ['[', ']']
            list = [urban["list"][num]["definition"], urban["list"][num]["example"]]
            x = 0
            for word in list:
                for character in remove:
                    word = word.replace(character, "")
                    list[x] = word
                x += 1
            embed = discord.Embed(colour=discord.Color.red())
            embed.set_author(name=f'Defination of {search}')
            embed.add_field(name='Defination', value=list[0], inline=False)
            embed.add_field(name='Example', value=list[1], inline=False)
            embed.add_field(name='Upvotes', value=urban["list"][num]["thumbs_up"], inline=False)
            embed.set_footer(icon_url=self.bot.user.avatar_url, text='Go way hat you™')
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title='No results found', color=discord.Color.blue(), inline=True)
            await ctx.send(embed=embed)

    @commands.command()
    async def crypto(self, ctx, symbol):
        """Gets current price of a cyrpto currency"""
        url = 'https://coinmarketcap.com/'
        headers = {"User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36'}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url) as page:
                soup = BeautifulSoup(await page.text(),  'html.parser')
        symbol = symbol.upper()
        symbols = []
        prices = []
        images = []
        for a in soup.find_all("td", {"class": "cmc-table__cell cmc-table__cell--sortable cmc-table__cell--right cmc-table__cell--sort-by__circulating-supply"}):
            a = remove_html_tags(str(a))
            a = clean_non_letters(a)
            symbols.append(a)
        if symbol in symbols:
            index = symbols.index(symbol)
            for a in soup.find_all("td", {"class": "cmc-table__cell cmc-table__cell--sortable cmc-table__cell--right cmc-table__cell--sort-by__price"}):
                a = remove_html_tags(str(a))
                prices.append(a)
            for img in soup.findAll('img'):
                images.append(img.get('src'))
            url = 'https://api.exchangeratesapi.io/latest?base=NZD'
            async with aiohttp.ClientSession() as session:
                raw_response = await session.get(url)
                response = await raw_response.text()
                exchangerates = json.loads(response)
            embed = discord.Embed(colour=discord.Color.purple())
            embed.set_author(name=f'Current {symbol} price:', icon_url=(images[index*2]))
            embed.add_field(name=f'{symbol} Price:', value="$" + str("{:,.2f}".format(round((float(((prices[index]).replace(',', '')).replace('$', ''))/exchangerates["rates"]["USD"]), 2))), inline=True)
            index = (index*2)+1
            embed.set_image(url=(images[index]))
            embed.set_footer(text='Price graph (7d)')
            await ctx.send(embed=embed)
        else:
            await ctx.send("Not a valid symbol or website is down")

    @commands.command(aliases=['btc'])
    async def bitcoin(self, ctx, type='NZD'):
        """Graps the current bitcoin price in some supported currencys"""
        try:
            url = 'https://blockchain.info/ticker'
            async with aiohttp.ClientSession() as session:
                raw_response = await session.get(url)
                response = await raw_response.text()
                bitcoin = json.loads(response)
                symbol = bitcoin[type.upper()]['symbol']
            url = 'https://blockchain.info/tobtc?currency=' + type.upper() + '&value=1'
            async with aiohttp.ClientSession() as session:
                raw_response = await session.get(url)
                response = await raw_response.text()
                price = json.loads(response)
            embed = discord.Embed(colour=discord.Color.purple())
            embed.set_author(name='Current Bitcoin price in ' + type.upper())
            embed.add_field(name='Bitcoin Price:', value=symbol + (str("{:,.2f}".format(bitcoin[type.upper()]['last'])) + " " + type.upper()), inline=True)
            embed.add_field(name='1 ' + type.upper() + ' is worth:', value=(str(round(price, 5)) + " bitcoins"), inline=True)
            if type.upper() == 'NZD':
                with open('json/bitcoin.json') as data_file:
                    data = json.load(data_file)
                embed.add_field(name='Change from ' + data[1], value=(str("{:,.2f}".format(bitcoin[type.upper()]['last'] - data[0]))), inline=True)
                data[0] = bitcoin[type.upper()]['last']
                data[1] = (str(ctx.message.created_at))[5:-7]
                with open('json/bitcoin.json', 'w') as file:
                    data = json.dump(data, file)
            embed.set_footer(icon_url=self.bot.user.avatar_url, text='Go way hat you™')
            await ctx.send(embed=embed)
        except KeyError:
            await ctx.send("Only works for USD, AUD, BRL, CAD, CHF, CLP, CNY, DKK, EUR, GBP, HKD, INR, ISK, JPY, KRW, NZD, PLN, RUB, SEK, SGD, THB, TRY, TWD")

    @commands.command()
    async def covid(self, ctx, *, country='nz'):
        """Shows current coronavirus cases, defaults to New Zealand"""
        try:
            if len(country) > 2:
                url = 'https://corona.lmao.ninja/v3/covid-19/countries/'
                async with aiohttp.ClientSession() as session:
                    raw_response = await session.get(url)
                    response = await raw_response.text()
                    response = json.loads(response)
                    if len(country) == 3:
                        country = country.upper()
                    else:
                        country = country.title()
                    y = 0
                    for x in response:
                        if x['country'] == country:
                            response = response[y]
                        y += 1
            else:
                url = 'https://corona.lmao.ninja/v3/covid-19/countries/' + country
                if country.lower() == 'all':
                    url = 'https://corona.lmao.ninja/v3/covid-19/all'
                async with aiohttp.ClientSession() as session:
                    raw_response = await session.get(url)
                    response = await raw_response.text()
                    response = json.loads(response)
            embed = discord.Embed(colour=discord.Color.red())
            embed.set_author(name='Cornavirus ' + response['country'] + ':', icon_url=response['countryInfo']['flag'])
            embed.add_field(name='Total Cases', value=(str("{:,}".format(response['cases']))), inline=True)
            embed.add_field(name='Total Deaths', value=(str("{:,}".format(response['deaths']))), inline=True)
            embed.add_field(name='Active Cases', value=(str("{:,}".format(response['active']))), inline=True)
            embed.add_field(name='Cases Today', value=(str("{:,}".format(response['todayCases']))), inline=True)
            embed.add_field(name='Deaths Today', value=(str("{:,}".format(response['todayDeaths']))), inline=True)
            embed.add_field(name='Recovered Total', value=(str("{:,}".format(response['recovered']))), inline=True)
            updated = str(datetime.timedelta(seconds=(time.time() - (response['updated']/1000))))[:-4]
            embed.set_footer(icon_url=self.bot.user.avatar_url, text=f'Go way hat you™   Last updated {updated}')
            await ctx.send(embed=embed)
        except KeyError:
            await ctx.send('Not a valid country e.g NZ, New Zealand, US, USA, Canada, all')

    @commands.command(aliases=['data'])
    async def databreach(self, ctx, num):
        """Sends information on databreachs in 2020"""
        url = 'https://haveibeenpwned.com/api/v3/breaches'
        async with aiohttp.ClientSession() as session:
            raw_response = await session.get(url)
            response = await raw_response.text()
            response = json.loads(response)
            y = 0
            c = 0
            for x in response:
                if response[y]['BreachDate'][0:4] == '2020':
                    if c < int(num):
                        try:
                            embed = discord.Embed(colour=discord.Color.red())
                            embed.set_author(name=response[y]['Name'] + ' Databreach ')
                            embed.add_field(name='URL', value=(response[y]['Domain']), inline=True)
                            embed.add_field(name='Breach Date', value=(response[y]['BreachDate']), inline=True)
                            embed.add_field(name='PwnCount', value=(response[y]['PwnCount']), inline=True)
                            embed.add_field(name='Description', value=remove_html_tags((response[y]['Description'])), inline=True)
                            embed.set_footer(icon_url=self.bot.user.avatar_url, text='Go way hat you™')
                            await ctx.send("", embed=embed)
                        except Exception:
                            c -= 1
                            pass
                    else:
                        break
                    c += 1
                y += 1

    @commands.command()
    async def nz(self, ctx):
        """Shows current coronavirus cases in New Zealand from health.govt.nz"""
        url = 'https://www.health.govt.nz/our-work/diseases-and-conditions/covid-19-novel-coronavirus/covid-19-data-and-statistics/covid-19-current-cases'
        headers = {"User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebkit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36'}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url) as page:
                soup = BeautifulSoup(await page.text(), 'html.parser')
        list = []
        for a in soup.find_all("td", {"class": ""}):
            list.append(remove_html_tags(str(a)))
        embed = discord.Embed(colour=discord.Color.red())
        embed.set_author(name='Cornavirus NZ', icon_url=('https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/Flag_of_New_Zealand.svg/255px-Flag_of_New_Zealand.svg.png'))
        embed.add_field(name='Total', value=(list[21]), inline=True)
        embed.add_field(name='Total Deaths', value=(list[12]), inline=True)
        embed.add_field(name='Recovered', value=(list[10]), inline=True)
        embed.add_field(name='Active', value=(list[4]), inline=True)
        embed.add_field(name='Active Community', value=(list[2]), inline=True)
        embed.add_field(name='Active Border', value=(list[1]), inline=True)
        embed.add_field(name='Cases 24h', value=(list[0]), inline=True)
        embed.add_field(name='Deaths 24h', value=(list[11]), inline=True)
        embed.add_field(name='Recovered 24h', value=(list[9]), inline=True)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Useful(bot))
