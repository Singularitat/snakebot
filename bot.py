import discord
from discord.ext import commands
import json
from os import listdir
from os.path import isfile, join


# Connects to discord, Sets command prefix, Removes default help command

bot = discord.Client()
bot = commands.Bot(command_prefix="\\")
bot.remove_command('help')

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
