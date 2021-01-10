import discord
from discord.ext import commands
import json
import platform
import os
from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer
import time
import datetime
import textwrap
from discord import Embed


chatbot = ChatBot(
    'Snakebot',
    storage_adapter='chatterbot.storage.SQLStorageAdapter',
    database_uri='sqlite:///cogs/db/database.sqlite3'
)
trainer = ChatterBotCorpusTrainer(chatbot)


class Events(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        with open('json/real.json') as data_file:
            data = json.load(data_file)
        if member.id in data["downvote"] and after.channel is not None:
            await member.edit(voice_channel=None)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if not after.content or before == after:
            pass
        else:
            if after.author != self.bot.user:
                if after.content.startswith('https'):
                    pass
                else:
                    try:
                        channel = discord.utils.get(after.guild.channels, name="logs")
                        await channel.send(f"```{before.author} editted:\n{before.content} >>> {after.content}```")
                    except Exception:
                        pass

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """Logs deleted messages into the logs channel"""
        if not message.content or message.content.startswith(f'{self.bot.command_prefix}issue'):
            pass
        else:
            if '@everyone' in message.content or '@here' in message.content:
                timesince = datetime.datetime.utcfromtimestamp(time.time())-message.created_at
                if timesince.total_seconds() < 360:
                    general = discord.utils.get(message.guild.channels, name="logs")
                    embed = Embed(colour=discord.Colour.blurple())
                    embed.description = (
                        textwrap.dedent(f"""
                            **{message.author} has ghosted pinged**
                            For their crimes they have been downvoted
                        """)
                    )
                    await general.send(embed=embed)
                    with open('json/real.json') as data_file:
                        data = json.load(data_file)
                    if message.author.id not in data["downvote"]:
                        data["downvote"].append(message.author.id)
                    with open('json/real.json', 'w') as file:
                        data = json.dump(data, file)
            try:
                channel = discord.utils.get(message.guild.channels, name="logs")
                await channel.send(f"```{message.author} deleted:\n{message.content.replace('`', '')}```")
            except Exception:
                pass

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        with open('json/real.json') as data_file:
            data = json.load(data_file)
        data["notevil"][str(after.id)] = []
        for role in after.roles:
            if str(role.name) != "@everyone" and role < after.guild.me.top_role:
                data["notevil"][str(after.id)].append(str(role.name))
        with open('json/real.json', 'w') as file:
            data = json.dump(data, file)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        with open('json/real.json') as data_file:
            data = json.load(data_file)
        if member in data["notevil"]:
            try:
                member.add_roles(data["notevil"][str(member.id)])
            except Exception:
                pass

    @commands.Cog.listener()
    async def on_message(self, message):
        """Sends and error message if someone blacklisted sends a command"""
        with open('json/real.json') as data_file:
            data = json.load(data_file)
        if message.author.id in data["downvote"]:
            await message.add_reaction(discord.utils.get(message.guild.emojis, name="downvote"))
        if str(message.channel) == 'snake-chat' and message.author != self.bot.user:
            await message.channel.send(chatbot.get_response(str(message.content)))

    @commands.Cog.listener()
    async def on_reaction_clear(self, message, reactions):
        with open('json/real.json') as data_file:
            data = json.load(data_file)
        if message.author.id in data["downvote"]:
            await message.add_reaction(discord.utils.get(message.guild.emojis, name="downvote"))

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Error message sender"""
        await ctx.send(embed=discord.Embed(title='No go away.', description='Error: ' + str(error), color=discord.Color.red()))

    @commands.Cog.listener()
    async def on_ready(self):
        if not hasattr(self, 'uptime'):
            self.bot.uptime = datetime.datetime.utcnow()
        self.bot.owner_id = 225708387558490112
        """Bot startup"""
        print('Logged in as', self.bot.user.name, self.bot.user.id,)
        print("Discord.py API version:", discord.__version__)
        print("Python version:", platform.python_version())
        print("Running on:", platform.system(), platform.release(), "(" + os.name + ")")
        print('-------------------')
        await self.bot.change_presence(status=discord.Status.online, activity=discord.Game(name="Tax Evasion Simulator 2020"))

    async def bot_check_once(self, ctx):
        if ctx.author.id == 225708387558490112:
            return True
        with open('json/real.json') as data_file:
            data = json.load(data_file)
        return ctx.author.id not in data['blacklist'] and ctx.author.id not in data["downvote"]

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        with open('json/real.json') as data_file:
            data = json.load(data_file)
        for member in data["notevil"]:
            if role in data["notevil"][member]:
                data["notevil"][member].remove(role)
        with open('json/real.json', 'w') as file:
            data = json.dump(data, file)


def setup(bot):
    bot.add_cog(Events(bot))
