import discord
from discord.ext import commands
import json
import platform
import os


class events(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        with open('json/real.json') as data_file:
            data = json.load(data_file)
        if str(member) in data["downvote"] and after.channel is not None:
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
                    channel = self.bot.get_channel(765410315038621748)
                    await channel.send(f"```{before.author} editted:\n{before.content} >>> {after.content}```")

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """Logs deleted messages into the log channel"""
        if not message.content:
            pass
        else:
            channel = self.bot.get_channel(765410315038621748)
            await channel.send(f"```{message.author} deleted:\n{message.content.replace('`', '')}```")

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        with open('json/real.json') as data_file:
            data = json.load(data_file)
        data["notevil"][str(after)] = []
        for role in after.roles:
            data["notevil"][str(after)].append(str(role.name))
        with open('json/real.json', 'w') as file:
            data = json.dump(data, file)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        with open('json/real.json') as data_file:
            data = json.load(data_file)
        if member in data["notevil"]:
            try:
                member.add_roles(data["notevil"][str(member)])
            except Exception as e:
                print(e)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Sends and error message if someone blacklisted sends a command"""
        with open('json/real.json') as data_file:
            data = json.load(data_file)
        if message.content.startswith('.'):
            if str(message.author) in data["blacklist"]:
                await message.channel.send(embed=discord.Embed(title='You\'re blacklisted!', description='Haha dumb dumb.', color=0x00FF00))
        if str(message.author) in data["downvote"]:
            await message.add_reaction(self.bot.get_emoji(766414744730206228))
        if message.author.id != self.bot.user.id:
            print(f"{message.guild}/{message.channel}/{message.author.name}>{message.content}")
            if message.embeds:
                print(message.embeds[0].to_dict())

    @commands.Cog.listener()
    async def on_reaction_clear(self, message, reactions):
        with open('json/real.json') as data_file:
            data = json.load(data_file)
        if str(message.author) in data["downvote"]:
            await message.add_reaction(self.bot.get_emoji(766414744730206228))

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Error message sender"""
        await ctx.send(embed=discord.Embed(title='No go away.', description='Error: ' + str(error), color=discord.Color.red()))

    @commands.Cog.listener()
    async def on_ready(self):
        """Bot startup"""
        print('Logged in as', self.bot.user.name, self.bot.user.id,)
        print("Discord.py API version:", discord.__version__)
        print("Python version:", platform.python_version())
        print("Running on:", platform.system(), platform.release(), "(" + os.name + ")")
        print('-------------------')
        await self.bot.change_presence(status=discord.Status.online, activity=discord.Game(name="Tax Evasion Simulator 2020"))

    async def bot_check_once(self, ctx):
        with open('json/real.json') as data_file:
            data = json.load(data_file)
        return ctx.author.id not in data['blacklist']

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
    bot.add_cog(events(bot))
