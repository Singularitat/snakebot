import discord
from discord.ext import commands
import random
import asyncio
import time
from baseconv import base2, base16, base64
import datetime


class garbage(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        global starttime
        starttime = time.time()

    @commands.command()
    @commands.has_any_role('Sneak', 'Higher Society', 'High Society')
    async def send(self, ctx, member: discord.Member, *, content):
        """Sends a DM to targeted member"""
        try:
            channel = await member.create_dm()
            await channel.send(content)
            await ctx.send('Sent')
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
        if time[-1] == 'm':
            time = float(time[:-1])
            time *= 60
        time = float(time)
        await asyncio.sleep(time)
        await ctx.send(embed=discord.Embed(title=message))

    @commands.command()
    async def uptime(self, ctx):
        """Gets the current uptime of the bot"""
        uptime = datetime.timedelta(seconds=(time.time() - starttime))
        await ctx.send(embed=discord.Embed(title=f'Uptime: {str(uptime)[:-4]}', color=discord.Color.blue()))

    @commands.command()
    async def binary(self, ctx, number: int, decode=None):
        """Encodes or decodes in binary"""
        if decode is None:
            await ctx.send(base2.encode(number))
        elif decode == "decode":
            await ctx.send(base2.decode(number))

    @commands.command()
    async def octal(self, ctx, number, decode=None):
        """Encodes or decodes in octal decimal"""
        if decode is None:
            await ctx.send(oct(int(number)))
        elif decode == "decode":
            await ctx.send(int(str(number), 8))

    @commands.command()
    async def hex(self, ctx, number: int, decode=None):
        """Encodes or decodes in hexadecimal"""
        if decode is None:
            await ctx.send(base16.encode(int(number)))
        elif decode == "decode":
            await ctx.send(base16.decode(number))

    @commands.command()
    async def base(self, ctx, number: int, decode=None):
        """Encodes or decodes in base64"""
        if decode is None:
            await ctx.send(base64.encode(int(number)))
        elif decode == "decode":
            await ctx.send(base64.decode(number))

    @commands.command()
    async def slap(self, ctx, target, *, reason):
        """Slaps targetted user"""
        await ctx.send(ctx.message.author.mention + " slapped " + target + " because " + reason)

    class Slapper(commands.Converter):
        async def convert(self, ctx, argument):
            return '{0.author} slapped {1} because *{2}*'.format(ctx, random.choice(ctx.guild.members), argument)

    @commands.command()
    async def randomslap(self, ctx, *, reason: Slapper):
        """Slaps a random discord user"""
        await ctx.send(reason)

    # Spams inputed amount of times

    @commands.command()
    @commands.has_any_role('Sneak', 'Higher Society')
    async def spam(self, ctx, amount: int, *, text):
        """Spams the inputted text an inputted amout of times"""
        async with ctx.typing():
            for _ in range(int(amount)):
                await ctx.send(text)


def setup(bot):
    bot.add_cog(garbage(bot))
