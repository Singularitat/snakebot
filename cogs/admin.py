import discord
from discord.ext import commands
import json
from os import listdir
from os.path import isfile, join
import re
import git
import copy


class admin(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(hidden=True)
    @commands.has_any_role('Sneak')
    async def sudo(self, ctx, channel: discord.TextChannel, who: discord.Member, *, command: str):
        """Run a command as another user optionally in another channel."""
        msg = copy.copy(ctx.message)
        channel = channel or ctx.channel
        msg.channel = channel
        msg.author = who
        msg.content = ctx.prefix + command
        new_ctx = await self.bot.get_context(msg, cls=type(ctx))
        await self.bot.invoke(new_ctx)

    @commands.command(hidden=True)
    @commands.has_permissions(manage_roles=True)
    async def stopuser(self, ctx, member: discord.Member):
        """Stops them"""
        role = discord.utils.get(member.guild.roles, name='Stop')
        if role in member.roles:
            await member.remove_roles(role)
        else:
            await member.add_roles(role)

    @commands.command(hidden=True, aliases=["pull"])
    async def update2(self, ctx):
        """ Gets latest commits and applies them from git """
        def run_shell(command):
            with Popen(command, stdout=PIPE, stderr=PIPE, shell=True) as proc:
                return [std.decode("utf-8") for std in proc.communicate()]

        pull = await self.bot.loop.run_in_executor(
            None, run_shell, "git pull origin master"
        )
        for extension in [f.replace('.py', '') for f in listdir('cogs') if isfile(join('cogs', f))]:
            try:
                self.bot.reload_extension("cogs." + extension)
            except Exception as e:
                if e == f"ExtensionNotLoaded: Extension 'cogs.{extension}' has not been loaded.":
                    self.bot.load_extension("cogs." + extension)
                else:
                    await ctx.send(embed=discord.Embed(title="```{}: {}\n```".format(type(e).__name__, str(e)), color=discord.Color.blurple()))
        await ctx.send(embed=discord.Embed(title="Pulled latests commits and restarted.", color=discord.Color.blurple()))

    @commands.command(hidden=True)
    @commands.has_any_role('Sneak')
    async def update(self, ctx):
        """Updates the bot"""
        repo = git.Repo()
        repo.remotes.origin.pull('master')

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def downvote(self, ctx, member: discord.Member):
        """Automatically downvotes someone"""
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

    @commands.command(hidden=True, aliases=['ban', 'unban'])
    @commands.has_permissions(ban_members=True)
    async def ban_user(self, ctx, member: discord.Member):
        """Bans someone"""
        bans = await ctx.guild.bans()
        if member not in bans:
            await member.ban()
            await ctx.send(embed=discord.Embed(title=f'Banned {member}', color=discord.Color.dark_red()))
        else:
            member.unban()
            await ctx.send(embed=discord.Embed(title=f'Unbanned {member}', color=discord.Color.dark_blue()))

    @commands.command(hidden=True)
    @commands.has_any_role('Highest Society')
    async def role(self, ctx, member: discord.Member, *, role):
        """Gives someone a role"""
        role = discord.utils.get(member.guild.roles, name=role.capitalize())
        if role in member.roles:
            await member.remove_roles(role)
            embed = discord.Embed(title=f'Gave {member} the role {role}')
        else:
            await member.add_roles(role)
            embed = discord.Embed(title=f'Removed the role {role} from {member}')
        ctx.send(embed)

    @commands.command(hidden=True)
    async def appinfo(self, ctx):
        """Sends application info about the bot"""
        await ctx.send(await self.bot.application_info())

    @commands.command(hidden=True, aliases=['deletecmd', 'removecmd'])
    @commands.has_any_role('Sneak')
    async def deletecommand(self, ctx, command):
        """Removes inputted command from the bot"""
        self.bot.remove_command(command)
        await ctx.send(embed=discord.Embed(title=f'Removed command {command}'))

    @commands.command(hidden=True)
    @commands.has_any_role('Sneak')
    async def blacklist(self, ctx, user: discord.Member=None):
        """Blacklists someone from using the bot"""
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

    @commands.command(hidden=True)
    @commands.has_any_role('Sneak')
    async def kill(self, ctx):
        """Kills the bot"""
        await self.bot.change_presence(status=discord.Status.online, activity=discord.Game(name="Dying..."))
        await ctx.send(embed=discord.Embed(title='Killing bot'))
        await self.bot.logout()

    @commands.command(hidden=True, aliases=['clear, clean'])
    @commands.has_any_role('Sneak', 'Higher Society')
    async def purge(self, ctx, num: int):
        """Purges inputed amount of messages"""
        await ctx.channel.purge(limit=num+1)

    @commands.command(hidden=True)
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

    @commands.command(hidden=True)
    @commands.has_any_role('Sneak')
    async def unload(self, ctx, extension_name: str):
        """Unloads an extension."""
        extension_name = "cogs." + extension_name
        self.bot.unload_extension(extension_name)
        await ctx.send(embed=discord.Embed(title=f"{extension_name} unloaded.", color=discord.Color.blurple()))

    @commands.command(hidden=True)
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


def setup(bot):
    bot.add_cog(admin(bot))
