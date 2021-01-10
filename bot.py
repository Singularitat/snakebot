import discord
from discord.ext import commands
import json
from os import listdir
from os.path import isfile, join


# Connects to discord, Sets command prefix, Removes default help command
# Sets discord intents to enable certain gateway features that are necessary

intents = discord.Intents(guilds=True, members=True, bans=True, emojis=True, voice_states=True, messages=True, reactions=True)
bot = discord.Client(intents=intents)
bot = commands.Bot(command_prefix="\\", help_command=None)

# Gets discord TOKEN

with open('json/data.txt') as json_file:
    data = json.load(json_file)
    TOKEN = (data['token'])

# Runs all the the cogs in /cogs as extensions

cogs_dir = "cogs"

if __name__ == "__main__":
    for extension in [f.replace('.py', '') for f in listdir(cogs_dir) if isfile(join(cogs_dir, f))]:
        try:
            bot.load_extension(cogs_dir + "." + extension)
        except Exception as e:
            print(f'Failed to load extension {extension}.')
            print(f'{e} \n')

bot.run(TOKEN)
