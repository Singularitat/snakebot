import discord
from discord.ext import commands
import textwrap
import psutil
import inspect
import os
from datetime import datetime


class information(commands.Cog):
    """Commands that give information about the bot or server."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.process = psutil.Process()

    async def say_permissions(self, ctx, member, channel):
        """Sends an embed containing a members permissions in a channel.

        member: discord.Member
            The member to get permissions of.
        channel: discord.TextChannel
            The channel to get the permissions in.
        """
        permissions = channel.permissions_for(member)
        e = discord.Embed(colour=member.colour)
        avatar = member.avatar_url_as(static_format="png")
        e.set_author(name=str(member), url=avatar)

        allowed, denied = [], []
        for name, value in permissions:
            name = name.replace("_", " ").replace("guild", "server").title()
            if value:
                allowed.append(name)
            else:
                denied.append(name)

        e.add_field(name="Allowed", value="\n".join(allowed))
        e.add_field(name="Denied", value="\n".join(denied))
        await ctx.send(embed=e)

    @commands.command(hidden=True)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
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

    @commands.command()
    async def ping(self, ctx):
        """Check how the bot is doing."""
        pinger = await ctx.send("Pinging...")

        embed = discord.Embed(color=discord.Color.blurple())
        embed.add_field(
            name="Ping",
            value="`{} ms`".format(
                (pinger.created_at - ctx.message.created_at).total_seconds() * 1000
            ),
        )
        embed.add_field(name="Latency", value=f"`{self.bot.latency*1000:.2f} ms`")

        await pinger.edit(content=None, embed=embed)

    @commands.command()
    async def usage(self, ctx):
        """Shows the bot's memory and cpu usage."""
        memory_usage = self.process.memory_full_info().uss / 1024 ** 2
        cpu_usage = self.process.cpu_percent()

        embed = discord.Embed(color=discord.Color.blurple())
        embed.add_field(name="Memory Usage: ", value=f"**{memory_usage:.2f} MiB**")
        embed.add_field(name="CPU Usage:", value=f"**{cpu_usage}%**")
        await ctx.send(embed=embed)

    @commands.command()
    async def source(self, ctx, *, command: str = None):
        """Gets the source code of a command from github.

        command: str
            The command to find the source code of.
        """
        if command is None:
            return await ctx.send("https://github.com/Singularitat/snakebot")

        if command == "help":
            src = type(self.bot.help_command)
            filename = inspect.getsourcefile(src)
        else:
            obj = self.bot.get_command(command)
            if obj is None:
                return await ctx.send("```Could not find command.```")

            src = obj.callback.__code__
            filename = src.co_filename

        lines, lineno = inspect.getsourcelines(src)
        cog = os.path.relpath(filename).replace("\\", "/")

        msg = f"<https://github.com/Singularitat/snakebot/blob/main/{cog}#L{lineno}-L{lineno + len(lines) - 1}>"
        # The replace replaces the backticks with a backtick and a zero width space
        code = f'\n```py\n{textwrap.dedent("".join(lines)).replace("`", "`​")}```'

        if len(code) <= 2000:
            msg += code

        await ctx.send(msg)

    @commands.command()
    async def cog(self, ctx, cog_name):
        """Sends the .py file of a cog.

        cog_name: str
            The name of the cog.
        """
        with open(f"cogs/{cog_name}.py", "rb") as file:
            await ctx.send(file=discord.File(file, f"{cog_name}.py"))

    @commands.command()
    async def uptime(self, ctx):
        """Shows the bots uptime."""
        await ctx.send(f"**{self.time_since(self.bot.uptime)}**")

    @commands.command(
        name="server",
        aliases=["guild", "info"],
    )
    async def server_info(self, ctx):
        """Sends an embed of server information."""
        created = f"{self.time_since(ctx.guild.created_at)} ago"
        region = ctx.guild.region.name.capitalize()
        roles = len(ctx.guild.roles)
        member_count = ctx.guild.member_count
        owner = ctx.guild.owner
        online_users = sum(
            [member.status is discord.Status.online for member in ctx.guild.members]
        )
        offline_users = sum(
            [member.status is discord.Status.offline for member in ctx.guild.members]
        )
        dnd_users = sum(
            [member.status is discord.Status.dnd for member in ctx.guild.members]
        )
        idle_users = sum(
            [member.status is discord.Status.idle for member in ctx.guild.members]
        )
        offline = "<:offline:766076363048222740>"
        online = "<:online:766076316512157768>"
        dnd = "<:dnd:766197955597959208>"
        idle = "<:idle:766197981955096608>"
        embed = discord.Embed(colour=discord.Colour.blurple())
        embed.description = textwrap.dedent(
            f"""
                **Server Information**
                Created: {created}
                Region: {region}
                Owner: {owner}

                **Member Counts**
                Members: {member_count:,} Roles: {roles}

                **Member Statuses**
                {online} {online_users:,} {dnd} {dnd_users:,} {idle} {idle_users:,} {offline} {offline_users:,}
            """
        )
        embed.set_thumbnail(url=ctx.guild.icon_url)
        await ctx.send(embed=embed)

    @commands.command(name="user", aliases=["member"])
    async def user_info(self, ctx, member: discord.Member = None) -> None:
        """Sends info about a member.

        member: discord.Member
            The member to get info of defulting to the invoker.
        """
        if member is None:
            member = ctx.author
        embed = await self.create_user_embed(ctx, member)
        await ctx.send(embed=embed)

    async def create_user_embed(self, ctx, member: discord.Member) -> discord.Embed:
        """Creates an embed containing information on the `user`."""
        created = f"{self.time_since(member.created_at)} ago"
        name = str(member)
        if member.nick:
            name = f"{member.nick} ({name})"
        joined = f"{self.time_since(member.joined_at)} ago"
        roles = ", ".join(role.mention for role in member.roles[1:])
        fields = [
            (
                "User information",
                textwrap.dedent(
                    f"""
                    Created: {created}
                    Profile: {member.mention}
                    ID: {member.id}
                """
                ).strip(),
            ),
            (
                "Member information",
                textwrap.dedent(
                    f"""
                    Joined: {joined}
                    Roles: {roles or None}
                """
                ).strip(),
            ),
        ]
        embed = discord.Embed(
            title=name,
        )
        for field_name, field_content in fields:
            embed.add_field(name=field_name, value=field_content, inline=False)
        embed.set_thumbnail(url=member.avatar_url_as(static_format="png"))
        embed.colour = member.top_role.colour if roles else discord.Colour.blurple()
        return embed

    @staticmethod
    def time_since(past_time=False):
        """Get a datetime object or a int() Epoch timestamp and return a pretty time string."""
        now = datetime.utcnow()

        if isinstance(past_time, int):
            diff = now - datetime.fromtimestamp(past_time)
        elif isinstance(past_time, datetime):
            diff = now - past_time
        elif not past_time:
            diff = now - now

        sec = diff.seconds
        day = diff.days

        if day < 0:
            return ""

        if day == 0:
            if sec < 60:
                return f"{sec} seconds"
            if sec < 3600:
                return f"{sec // 60} minutes and {sec % 60} seconds"
            if sec < 86400:
                return f"{sec // 3600} hours {(sec % 3600) // 60} minutes and {(sec % 3600) % 60} seconds"

        if day < 7:
            return f"{day} days {sec // 3600} hours and {(sec % 3600) // 60} minutes"
        if day < 31:
            return f"{day // 7} weeks {day % 7} days and {sec // 3600} hours"
        if day < 365:
            return (
                f"{day // 30} months {(day % 30) // 7} weeks and {(day % 30) % 7} days"
            )

        return (
            f"{day // 365} years {(day % 365) // 30} months and {(day % 365) % 30} days"
        )


def setup(bot: commands.Bot) -> None:
    """Starts information cog."""
    bot.add_cog(information(bot))
