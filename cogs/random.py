import discord
from discord.ext import commands
import random
import asyncio
from bs4 import BeautifulSoup
import aiohttp


class Random(commands.Cog):
    """For commands that don't deserve a unique cog."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command()
    async def hug(self, ctx):
        """Gets a random hug gif from tenor"""
        url = 'https://tenor.com/search/hug-gifs'
        headers = {"User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebkit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36'}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url) as page:
                soup = BeautifulSoup(await page.text(), 'html.parser')
        images = []
        for a in soup.find_all("img"):
            image = a.get('src')
            if image.startswith('https://media.tenor.com/'):
                images.append(image)
        await ctx.send(random.choice(images))

    @commands.command()
    @commands.has_any_role('Sneak', 'Higher Society', 'High Society')
    async def send(self, ctx, member: discord.Member, *, content):
        """Gets Snakebot to send a DM to member"""
        try:
            await member.send(content)
            await ctx.send(f'Sent message to {member}')
        except Exception:
            await ctx.send(f'{member} has DMs disabled for non-friends')

    @commands.command()
    async def roll(self, ctx, dice: str):
        """Rolls dice in NdN format"""
        try:
            rolls, limit = map(int, dice.split('d'))
        except Exception:
            await ctx.send('Format has to be NdN')
            return
        result = ', '.join(str(random.randint(1, limit)) for r in range(rolls))
        total = result.split(", ")
        for i in range(0, len(total)):
            total[i] = int(total[i])
        total = sum(total)
        await ctx.send(f'Results: {result} Total: {total}')

    @commands.command()
    @commands.has_any_role('Sneak', 'Higher Society', 'High Society')
    async def choose(self, ctx, *choices: str):
        """"Chooses between mulitple inputs"""
        await ctx.send(random.choice(choices))

    @commands.command()
    async def yeah(self, ctx):
        """Oh yeah its all coming together"""
        await ctx.send('Oh yeah its all coming together')

    @commands.command()
    async def delay(self, ctx, time, *, message):
        """Sends a message after a delay"""
        if time[-1] == 'm':
            time = float(time[:-1])
            time *= 60
        time = float(time)
        await asyncio.sleep(time)
        await ctx.send(embed=discord.Embed(title=message))

    @commands.command()
    async def slap(self, ctx, target, *, reason):
        """Slaps a member"""
        await ctx.send(ctx.message.author.mention + " slapped " + target + " because " + reason)


def setup(bot):
    bot.add_cog(Random(bot))
