import discord
from discord.ext import commands
import ujson
import os
import copy
import asyncio
import traceback
import time


class PerformanceMocker:
    """A mock object that can also be used in await expressions."""

    def __init__(self):
        self.loop = asyncio.get_event_loop()

    def __getattr__(self, attr):
        return self

    def __call__(self, *args, **kwargs):
        return self

    def __repr__(self):
        return "<PerformanceMocker>"

    def __await__(self):
        future = self.loop.create_future()
        future.set_result(self)
        return future.__await__()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return self

    def __len__(self):
        return 0

    def __bool__(self):
        return False


class admin(commands.Cog):
    """Administrative commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(hidden=True)
    @commands.guild_only()
    @commands.is_owner()
    async def botpermissions(self, ctx, *, channel: discord.TextChannel = None):
        """Shows the bot's permissions in a specific channel.

        channel: discord.TextChannel
            The channel to get the bots perrmissions in.
        """
        channel = channel or ctx.channel
        member = ctx.guild.me
        await self.say_permissions(ctx, member, channel)

    @commands.command()
    @commands.guild_only()
    async def permissions(
        self, ctx, member: discord.Member = None, channel: discord.TextChannel = None
    ):
        """Shows a member's permissions in a specific channel.

        member: discord.Member
            The member to get permissions of.
        channel: discord.TextChannel
            The channel to get the permissions in.
        """
        channel = channel or ctx.channel
        if member is None:
            member = ctx.author

        await self.say_permissions(ctx, member, channel)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def chunked(self, ctx):
        """Checks if the current guild is chunked and chunks guild if not."""
        if ctx.author.guild.chunked:
            await ctx.send(f"```{ctx.author.guild} is chunked```")
        else:
            await ctx.author.guild.chunk()
            ctx.send(
                f"```{ctx.author.guild} was not chunked it has now been chunked```"
            )

    @commands.command(hidden=True)
    @commands.is_owner()
    async def toggle(self, ctx, command):
        """Toggles a command from being disabled or enabled.

        command: str
            The command to be toggled
        """
        command = self.bot.get_command(command)
        if command is None:
            await ctx.send("```No such command```")
        else:
            command.enabled = not command.enabled
            ternary = "enabled" if command.enabled else "disabled"
            await ctx.send(
                f"```Sucessfully {ternary} the {command.qualified_name} command```"
            )

    @commands.command(hidden=True)
    @commands.is_owner()
    async def presence(self, ctx, *, presence):
        """Changes the bots activity.

        presence: str
            The new activity.
        """
        await self.bot.change_presence(
            status=discord.Status.online,
            activity=discord.Game(name=presence),
        )
        await ctx.send(f"Changed presence to {presence}")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def perf(self, ctx, *, command):
        """Checks the timing of a command, while attempting to suppress HTTP calls.

        command: str
            The command to run including arguments.
        """
        msg = copy.copy(ctx.message)
        msg.content = f"{ctx.prefix}{command}"

        new_ctx = await self.bot.get_context(msg, cls=type(ctx))

        # Intercepts the Messageable interface a bit
        new_ctx._state = PerformanceMocker()
        new_ctx.channel = PerformanceMocker()

        if new_ctx.command is None:
            return await ctx.send("```No command found```")

        start = time.perf_counter()
        try:
            await new_ctx.command.invoke(new_ctx)
            new_ctx.command.reset_cooldown(new_ctx)
        except commands.CommandError:
            end = time.perf_counter()
            success = ":negative_squared_cross_mark:"
            try:
                await ctx.send(f"```py\n{traceback.format_exc()}\n```")
            except discord.HTTPException:
                pass
        else:
            end = time.perf_counter()
            success = ":white_check_mark:"

        await ctx.send(f"Status: {success} Time: {(end - start) * 1000:.2f}ms")

    @commands.command(hiiden=True)
    @commands.is_owner()
    async def prefix(self, ctx, prefix: str):
        """Changes the bots command prefix.

        prefix: str
            The new prefix.
        """
        self.bot.command_prefix = prefix
        await ctx.send(f"Prefix changed to {prefix}")

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def sudo(
        self, ctx, channel: discord.TextChannel, member: discord.Member, *, command: str
    ):
        """Run a command as another user optionally in another channel.

        channel: discord.TextChannel
            The channel to run the command.
        member: discord.Member
            The member to run the command as.
        command: str
            The command name.
        """
        msg = copy.copy(ctx.message)
        channel = channel or ctx.channel
        msg.channel = channel
        msg.author = member
        msg.content = f"{ctx.prefix}{command}"
        new_ctx = await self.bot.get_context(msg, cls=type(ctx))
        await self.bot.invoke(new_ctx)

    @commands.command(hidden=True)
    @commands.has_permissions(manage_roles=True)
    async def stopuser(self, ctx, member: discord.Member):
        """Gives a user the stop role.

        member: discord.Member
            The member to give the role.
        """
        role = discord.utils.get(member.guild.roles, name="Stop")
        if role in member.roles:
            await member.remove_roles(role)
        else:
            await member.add_roles(role)

    @commands.command(hidden=True, aliases=["pull"])
    @commands.is_owner()
    async def update(self, ctx):
        """Gets latest commits and applies them through git."""
        os.system("git stash")
        pull = os.popen("git pull").read()

        if pull == "Already up to date.\n":
            await ctx.send(
                embed=discord.Embed(
                    title="Bot Is Already Up To Date", color=discord.Color.blurple()
                )
            )
        else:
            os.system("poetry install")

            await ctx.send(
                embed=discord.Embed(
                    title="Pulled latests commits, restarting.",
                    color=discord.Color.blurple(),
                )
            )

            await self.bot.logout()

            if os.name == "nt":
                os.system("python ./bot.py")
            else:
                os.system("nohup python3 bot.py &")

    @commands.command(name="ban", aliases=["unban"])
    @commands.has_permissions(ban_members=True)
    async def ban_member(self, ctx, *, member: discord.Member):
        """Bans a member.

        member: discord.Member
            The user to ban.
        """
        bans = await ctx.guild.bans()
        if member not in bans:
            await member.ban()
            await ctx.send(
                embed=discord.Embed(
                    title=f"Banned {member}", color=discord.Color.dark_red()
                )
            )
        else:
            await member.unban()
            await ctx.send(
                embed=discord.Embed(
                    title=f"Unbanned {member}", color=discord.Color.dark_blue()
                )
            )

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick_member(self, ctx, *, member: discord.Member):
        """Kicks a member.

        member: discord.Member
            The user to kick.
        """
        await member.kick()
        await ctx.send(
            embed=discord.Embed(
                title=f"Kicked {member}", color=discord.Color.dark_red()
            )
        )

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def role(self, ctx, member: discord.Member, *, role):
        """Gives member a role.

        member: discord.Member
            The member to give the role.
        role: str
            The role name.
        """
        role = discord.utils.get(member.guild.roles, name=role.capitalize())
        if role in member.roles:
            await member.remove_roles(role)
            embed = discord.Embed(title=f"Gave {member} the role {role}")
        else:
            await member.add_roles(role)
            embed = discord.Embed(title=f"Removed the role {role} from {member}")
        ctx.send(embed)

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def appinfo(self, ctx):
        """Sends application info about the bot."""
        await ctx.send(await self.bot.application_info())

    @commands.command(hidden=True, aliases=["deletecmd", "removecmd"])
    @commands.is_owner()
    async def deletecommand(self, ctx, command):
        """Removes command from the bot.

        command: str
            The command to remove.
        """
        self.bot.remove_command(command)
        await ctx.send(embed=discord.Embed(title=f"Removed command {command}"))

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def downvote(self, ctx, member: discord.Member = None):
        """Automatically downvotes someone.

        member: discord.Member
            The downvoted member.
        """
        with open("json/real.json") as file:
            data = ujson.load(file)
        if member is None:
            embed = discord.Embed(title="Downvoted users", colour=discord.Color.blue())
            for num in range(len(data["downvote"])):
                embed.add_field(name="User:", value=data["downvote"][num], inline=True)
        else:
            if member.id in data["downvote"]:
                data["downvote"].remove(member.id)
                embed = discord.Embed(
                    title="User Undownvoted",
                    description=f"***{member}*** has been removed from the downvote list",
                    color=discord.Color.blue(),
                )
            else:
                data["downvote"].append(member.id)
                embed = discord.Embed(
                    title="User Downvoted",
                    description=f"**{member}** has been added to the downvote list",
                    color=discord.Color.blue(),
                )
            with open("json/real.json", "w") as file:
                data = ujson.dump(data, file, indent=2)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def blacklist(self, ctx, member: discord.Member = None):
        """Blacklists someone from using the bot.

        member: discord.Member
            The blacklisted member.
        """
        with open("json/real.json") as file:
            data = ujson.load(file)
        if member is None:
            embed = discord.Embed(
                title="Blacklisted users", colour=discord.Color.blue()
            )
            for num in range(len(data["blacklist"])):
                embed.add_field(name="User:", value=data["blacklist"][num], inline=True)
        else:
            if member.id in data["blacklist"]:
                data["blacklist"].remove(member.id)
                embed = discord.Embed(
                    title="User Unblacklisted",
                    description=f"***{member}*** has been unblacklisted",
                    color=discord.Color.blue(),
                )
            else:
                data["blacklist"].append(member.id)
                embed = discord.Embed(
                    title="User Blacklisted",
                    description=f"**{member}** has been added to the blacklist",
                    color=discord.Color.blue(),
                )
            with open("json/real.json", "w") as file:
                data = ujson.dump(data, file, indent=2)
        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def kill(self, ctx):
        """Kills the bot."""
        await self.bot.change_presence(
            status=discord.Status.online, activity=discord.Game(name="Dying...")
        )
        await ctx.send(embed=discord.Embed(title="Killing bot"))
        await self.bot.logout()

    @commands.command(aliases=["clear, clean"])
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def purge(self, ctx, num: int = 20):
        """Purges messages.

        num: int
            The number of messages to delete defaults to 20.
        """
        await ctx.channel.purge(limit=num + 1)

    @commands.command(name="purge_till", hidden=True, aliases=["purget", "purgetill"])
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def purge_till(self, ctx, message_id: int):
        """Clear messages in a channel until the given message_id. Given ID is not deleted."""
        try:
            message = await ctx.fetch_message(message_id)
        except discord.errors.NotFound:
            await ctx.send("```Message could not be found in this channel```")
            return

        await ctx.channel.purge(after=message)

    @commands.command(name="purge_user", hidden=True, aliases=["purgeu", "purgeuser"])
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def purge_user(self, ctx, user: discord.User, num_messages: int = 100):
        """Clear all messagges of <User> withing the last [n=100] messages."""

        def check(msg):
            return msg.author.id == user.id

        await ctx.channel.purge(limit=num_messages, check=check, before=None)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def load(self, ctx, extension: str):
        """Loads an extension.

        extension: str
            The extension to load.
        """
        extension = f"cogs.{extension}"
        try:
            self.bot.load_extension(extension)
        except (AttributeError, ImportError) as e:
            await ctx.send(
                embed=discord.Embed(
                    title="```py\n{}: {}\n```".format(type(e).__name__, str(e)),
                    color=discord.Color.blurple(),
                )
            )
            return
        await ctx.send(
            embed=discord.Embed(
                title=f"{extension} loaded.", color=discord.Color.blurple()
            )
        )

    @commands.command(hidden=True)
    @commands.is_owner()
    async def unload(self, ctx, extension: str):
        """Unloads an extension.

        extension: str
            The extension to unload.
        """
        extension = f"cogs.{extension}"
        self.bot.unload_extension(extension)
        await ctx.send(
            embed=discord.Embed(
                title=f"{extension} unloaded.", color=discord.Color.blurple()
            )
        )

    @commands.command(hidden=True)
    @commands.is_owner()
    async def reload(self, ctx, extension: str):
        """Reloads an extension.

        extension: str
            The extension to reload.
        """
        extension = f"cogs.{extension}"
        self.bot.reload_extension(extension)
        await ctx.send(
            embed=discord.Embed(
                title=f"{extension} reloaded.", color=discord.Color.blurple()
            )
        )

    @commands.command(hidden=True)
    @commands.is_owner()
    async def restart(self, ctx):
        """Restarts all extensions."""
        for extension in [
            f.replace(".py", "")
            for f in os.listdir("cogs")
            if os.path.isfile(os.path.join("cogs", f))
        ]:
            try:
                self.bot.reload_extension(f"cogs.{extension}")
            except Exception as e:
                if (
                    e
                    == f"ExtensionNotLoaded: Extension 'cogs.{extension}' has not been loaded."
                ):
                    self.bot.load_extension(f"cogs.{extension}")
                else:
                    await ctx.send(
                        embed=discord.Embed(
                            title="```{}: {}\n```".format(type(e).__name__, str(e)),
                            color=discord.Color.blurple(),
                        )
                    )
        await ctx.send(
            embed=discord.Embed(
                title="Extensions restarted.", color=discord.Color.blurple()
            )
        )

    @commands.command(hidden=True)
    @commands.is_owner()
    async def revive(self, ctx):
        """Kills the bot then revives it."""
        await ctx.send(
            embed=discord.Embed(
                title="Killing bot.",
                color=discord.Color.blurple(),
            )
        )
        await self.bot.logout()
        if os.name == "nt":
            os.system("python ./bot.py")
        else:
            os.system("nohup python3 bot.py &")


def setup(bot: commands.Bot) -> None:
    """Starts admin cog."""
    bot.add_cog(admin(bot))
