import discord
from discord.ext import commands
import json
from os import listdir
from os.path import isfile, join
import re
import git


class admin(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command()
    async def stopthem(self, ctx, user: discord.Member):
        for role in user.roles:
            user.remove_roles(role)
        user.add_roles('stop')

    @commands.command()
    async def update(self, ctx):
        repo = git.Repo()
        repo.remotes.origin.pull('master')

    @commands.command()
    @commands.has_any_role('Highest Society')
    async def downvote(self, ctx, member: discord.Member):
        with open('json/real.json') as data_file:
            data = json.load(data_file)
        if str(member) in data["downvote"]:
            data["downvote"].remove(str(member))
        else:
            data["downvote"].append(str(member))
        if member in data["blacklist"]:
            data["blacklist"].remove(str(member))
        else:
            data["blacklist"].append(str(member))
        with open('json/real.json', 'w') as file:
            data = json.dump(data, file)

    @commands.command(aliases=['ban', 'unban'])
    @commands.has_any_role('Highest Society')
    async def ban_user(self, ctx, member: discord.Member):
        bans = await ctx.guild.bans()
        if member not in bans:
            await member.ban()
            await ctx.send(embed=discord.Embed(title=f'Banned {member}', color=discord.Color.dark_red()))
        else:
            member.unban()
            await ctx.send(embed=discord.Embed(title=f'Unbanned {member}', color=discord.Color.dark_blue()))

    @commands.command()
    @commands.has_any_role('Highest Society')
    async def role(self, ctx, member: discord.Member, *, role):
        role = discord.utils.get(member.guild.roles, name=role.capitalize())
        if role in member.roles:
            await member.remove_roles(role)
            embed = discord.Embed(title=f'Gave {member} the role {role}')
        else:
            await member.add_roles(role)
            embed = discord.Embed(title=f'Removed the role {role} from {member}')
        ctx.send(embed)

    @commands.command()
    async def appinfo(self, ctx):
        await ctx.send(await self.bot.application_info())

    @commands.command(aliases=['deletecmd', 'removecmd'])
    @commands.has_any_role('Sneak')
    async def deletecommand(self, ctx, command):
        """Removes inputted command from the bot"""
        self.bot.remove_command(command)
        await ctx.send(embed=discord.Embed(title=f'Removed command {command}'))

    @commands.command()
    @commands.has_any_role('Sneak')
    async def blacklist(self, ctx, user: discord.Member):
        with open('json/real.json') as data_file:
            data = json.load(data_file)
        if user is None:
            embed = discord.Embed(title='Blacklisted users', colour=discord.Color.blue())
            for num in range(len(data["blacklist"])):
                embed.add_field(name='User:', value=data["blacklist"][num], inline=True)
        else:
            if user.id in data["blacklist"]:
                data["blacklist"].remove(user.id)
                embed = discord.Embed(title="User Unblacklisted", description='***{0}*** has been unblacklisted'.format(user), color=discord.Color.blue())
            else:
                data["blacklist"].append(user.id)
                embed = discord.Embed(title="User Blacklisted", description='**{0}** has been added to the blacklist'.format(user), color=discord.Color.blue())
            with open('json/real.json', 'w') as file:
                data = json.dump(data, file)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_any_role('Sneak')
    async def kill(self, ctx):
        await self.bot.change_presence(status=discord.Status.online, activity=discord.Game(name="Dying..."))
        await ctx.send(embed=discord.Embed(title='Killing bot'))
        await self.bot.logout()

    @commands.command(aliases=['clear, clean'])
    @commands.has_any_role('Sneak', 'Higher Society')
    async def purge(self, ctx, num: int):
        """Purges inputed amount of messages"""
        await ctx.channel.purge(limit=num+1)

    @commands.command()
    @commands.has_any_role('Sneak')
    async def load(self, ctx, extension_name: str):
        """Loads an extension."""
        extension_name = "cogs." + extension_name
        try:
            self.bot.load_extension(extension_name)
        except (AttributeError, ImportError) as e:
            await ctx.send(embed=discord.Embed(title="```py\n{}: {}\n```".format(type(e).__name__, str(e)), color=discord.Color.blurple()))
            return
        await ctx.send(embed=discord.Embed(title=f"{extension_name} loaded.", color=discord.Color.blurple()))

    @commands.command()
    @commands.has_any_role('Sneak')
    async def unload(self, ctx, extension_name: str):
        """Unloads an extension."""
        extension_name = "cogs." + extension_name
        self.bot.unload_extension(extension_name)
        await ctx.send(embed=discord.Embed(title=f"{extension_name} unloaded.", color=discord.Color.blurple()))

    @commands.command()
    @commands.has_any_role('Sneak')
    async def restart(self, ctx):
        """Restarts all extensions."""
        for extension in [f.replace('.py', '') for f in listdir('cogs') if isfile(join('cogs', f))]:
            try:
                self.bot.reload_extension("cogs." + extension)
            except Exception as e:
                if e == f"ExtensionNotLoaded: Extension 'cogs.{extension}' has not been loaded.":
                    self.bot.load_extension("cogs." + extension)
                else:
                    await ctx.send(embed=discord.Embed(title="```{}: {}\n```".format(type(e).__name__, str(e)), color=discord.Color.blurple()))
        await ctx.send(embed=discord.Embed(title="Extensions restarted.", color=discord.Color.blurple()))

    @commands.command()
    @commands.has_any_role('Sneak')
    async def eval(self, ctx, *, code: str) -> None:
        """Run eval in a REPL-like format."""
        code = code.strip("`")
        if re.match('py(thon)?\n', code):
            code = "\n".join(code.split("\n")[1:])
        if not re.search(  # Check if it's an expression
                r"^(return|import|for|while|def|class|"
                r"from|exit|[a-zA-Z0-9]+\s*=)", code, re.M) and len(
                    code.split("\n")) == 1:
            code = "_ = " + code
        print(exec(code))


def setup(bot):
    bot.add_cog(admin(bot))
