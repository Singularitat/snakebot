import discord
from discord.ext import commands
import textwrap
import psutil
import inspect
import os
from datetime import datetime
from .utils.relativedelta import relativedelta
import cogs.utils.database as DB
import orjson
from io import StringIO


class information(commands.Cog):
    """Commands that give information about the bot or server."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.process = psutil.Process()

    @commands.command(name="oldest", aliases=["accdate", "newest"])
    async def oldest_members(self, ctx, amount: int = 10):
        """Gets the oldest accounts in a server.
        Call with 'newest' to get the newest members

        amount: int
        """
        amount = max(0, min(50, amount))

        reverse = ctx.invoked_with.lower() == "newest"
        top = sorted(ctx.guild.members, key=lambda member: member.id, reverse=reverse)[
            :amount
        ]

        description = "\n".join([f"**{member}:** {member.id}" for member in top])
        embed = discord.Embed(color=discord.Color.blurple())

        if len(description) > 2048:
            embed.description = "```Message is too large to send.```"
            return await ctx.send(embed=embed)

        embed.title = f"{'Youngest' if reverse else 'Oldest'} Accounts"
        embed.description = description

        await ctx.send(embed=embed)

    @commands.command(aliases=["msgtop"])
    async def message_top(self, ctx, amount=10):
        """Gets the users with the most messages in a server.

        amount: int
        """
        amount = max(0, min(50, amount))

        msgtop = sorted(
            [
                (int(b), m.decode())
                for m, b in DB.message_count
                if int(m.decode().split("-")[0]) == ctx.guild.id
            ],
            reverse=True,
        )[:amount]

        embed = discord.Embed(color=discord.Color.blurple())
        result = []

        for count, member in msgtop:
            user = self.bot.get_user(int(member.split("-")[1]))
            result.append((count, user.display_name if user else member))

        description = "\n".join(
            [f"**{member}:** {count} messages" for count, member in result]
        )

        if len(description) > 2048:
            embed.description = "```Message to large to send.```"
            return await ctx.send(embed=embed)

        embed.title = f"Top {len(msgtop)} chatters"
        embed.description = description

        await ctx.send(embed=embed)

    @commands.command()
    async def rule(self, ctx, number: int):
        """Shows the rules of the server.

        number: int
            Which rule to get.
        """
        rules = DB.db.get(f"{ctx.guild.id}-rules".encode())
        embed = discord.Embed(color=discord.Color.blurple())

        if not rules:
            embed.description = "```No rules added yet.```"
            return await ctx.send(embed=embed)

        rules = orjson.loads(rules)

        if number not in range(1, len(rules) + 1):
            embed.description = "```No rule found.```"
            return await ctx.send(embed=embed)

        embed.description = f"```{rules[number-1]}```"
        await ctx.send(embed=embed)

    @commands.command()
    async def rules(self, ctx):
        """Shows all the rules of the server"""
        rules = DB.db.get(f"{ctx.guild.id}-rules".encode())
        embed = discord.Embed(color=discord.Color.blurple())

        if not rules:
            embed.description = "```No rules added yet.```"
            return await ctx.send(embed=embed)

        rules = orjson.loads(rules)
        embed.title = "Server Rules"
        for index, rule in enumerate(rules, start=1):
            embed.add_field(name=f"Rule {index}", value=rule, inline=False)

        await ctx.send(embed=embed)

    async def say_permissions(self, ctx, member, channel):
        """Sends an embed containing a members permissions in a channel.

        member: discord.Member
            The member to get permissions of.
        channel: discord.TextChannel
            The channel to get the permissions in.
        """
        permissions = channel.permissions_for(member)
        embed = discord.Embed(colour=member.colour)
        avatar = member.avatar_url_as(static_format="png")
        embed.set_author(name=str(member), icon_url=avatar)

        allowed, denied = [], []
        for name, value in permissions:
            name = name.replace("_", " ").replace("guild", "server").title()
            if value:
                allowed.append(f"+ {name}\n")
            else:
                denied.append(f"- {name}\n")

        embed.add_field(name="Allowed", value=f"```diff\n{''.join(allowed)}```")
        embed.add_field(name="Denied", value=f"```diff\n{''.join(denied)}```")
        await ctx.send(embed=embed)

    @commands.command(hidden=True, aliases=["botperms"])
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

    @commands.command(aliases=["perms"])
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
        member = member or ctx.author

        await self.say_permissions(ctx, member, channel)

    @commands.command()
    async def invite(self, ctx):
        """Sends the invite link of the bot."""
        perms = discord.Permissions.all()
        await ctx.send(f"<{discord.utils.oauth_url(self.bot.user.id, perms)}>")

    @commands.command()
    async def ping(self, ctx):
        """Check how the bot is doing."""
        pinger = await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(), description="```Pinging...```"
            )
        )

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
        if not command:
            return await ctx.send("https://github.com/Singularitat/snakebot")

        if command == "help":
            filename = inspect.getsourcefile(type(self.bot.help_command))
        else:
            obj = self.bot.get_command(command)
            if not obj:
                embed = discord.Embed(
                    color=discord.Color.blurple(),
                    description="```Couldn't find command.```",
                )
                return await ctx.send(embed=embed)

            src = obj.callback.__code__
            filename = src.co_filename

        lines, lineno = inspect.getsourcelines(src)
        cog = os.path.relpath(filename).replace("\\", "/")

        link = f"<https://github.com/Singularitat/snakebot/blob/main/{cog}#L{lineno}-L{lineno + len(lines) - 1}>"
        # The replace replaces the backticks with a backtick and a zero width space
        code = textwrap.dedent("".join(lines)).replace("`", "`​")

        if len(code) >= 1990 - len(link):
            return await ctx.send(
                link, file=discord.File(StringIO(code), f"{command}.py")
            )

        await ctx.send(f"{link}\n```py\n{code}```")

    @commands.command()
    async def cog(self, ctx, cog_name):
        """Sends the .py file of a cog.

        cog_name: str
            The name of the cog.
        """
        if f"{cog_name}.py" not in os.listdir("cogs"):
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description=f"```No cog named {cog_name} found```",
                )
            )
        with open(f"cogs/{cog_name}.py", "rb") as file:
            await ctx.send(file=discord.File(file, f"{cog_name}.py"))

    @commands.command()
    async def uptime(self, ctx):
        """Shows the bots uptime."""
        await ctx.send(f"**{self.time_since(self.bot.uptime)}**")

    @commands.command(name="server")
    async def server_info(self, ctx):
        """Shows information about the current server."""
        offline_users, online_users, dnd_users, idle_users = 0, 0, 0, 0
        for member in ctx.guild.members:
            if member.status is discord.Status.offline:
                offline_users += 1
            elif member.status is discord.Status.online:
                online_users += 1
            elif member.status is discord.Status.dnd:
                dnd_users += 1
            elif member.status is discord.Status.idle:
                idle_users += 1

        offline = "<:offline:766076363048222740>"
        online = "<:online:766076316512157768>"
        dnd = "<:dnd:766197955597959208>"
        idle = "<:idle:766197981955096608>"

        embed = discord.Embed(colour=discord.Colour.blurple())
        embed.description = textwrap.dedent(
            f"""
                **Server Information**
                Created: {self.time_since(ctx.guild.created_at)} ago
                Region: {ctx.guild.region.name.title()}
                Owner: {ctx.guild.owner}

                **Member Counts**
                Members: {ctx.guild.member_count:,} Roles: {len(ctx.guild.roles)}

                **Member Statuses**
                {online} {online_users:,} {dnd} {dnd_users:,} {idle} {idle_users:,} {offline} {offline_users:,}
            """
        )
        embed.set_thumbnail(url=ctx.guild.icon_url)
        await ctx.send(embed=embed)

    @commands.command(name="user", aliases=["member"])
    async def user_info(self, ctx, user: discord.User = None) -> None:
        """Sends info about a member.

        member: discord.Member
            The member to get info of defulting to the invoker.
        """
        user = user or ctx.author
        created = f"{self.time_since(user.created_at)} ago"

        embed = discord.Embed(
            title=(str(user) + (" `[BOT]`" if user.bot else "")),
            color=discord.Color.blurple(),
        )

        embed.add_field(
            name="User information",
            value=f"Created: {created}\nProfile: {user.mention}\nID: {user.id}",
            inline=False,
        )

        if hasattr(user, "guild"):
            roles = ", ".join(role.mention for role in user.roles[1:])
            joined = f"{self.time_since(user.joined_at)} ago"
            embed.color = user.top_role.colour if roles else embed.color
            embed.title = f"{user.nick} ({user})" if user.nick else embed.title

            embed.add_field(
                name="Member information",
                value=f"Joined: {joined}\nRoles: {roles or None}",
                inline=False,
            )

        embed.set_thumbnail(url=user.avatar_url_as(static_format="png"))

        await ctx.send(embed=embed)

    @staticmethod
    def time_since(past_time=False):
        """Get a datetime object or a int() Epoch timestamp and return a pretty time string."""
        now = datetime.utcnow()

        if isinstance(past_time, int):
            diff = relativedelta(now, datetime.fromtimestamp(past_time))
        elif isinstance(past_time, datetime):
            diff = relativedelta(now, past_time)
        elif not past_time:
            diff = relativedelta(now, now)

        years = diff.years
        months = diff.months
        days = diff.days
        hours = diff.hours
        minutes = diff.minutes
        seconds = diff.seconds

        def fmt_time(amount: int, unit: str):
            return f"{amount} {unit}{'s' if amount else ''}"

        if not days and not months and not years:
            h, m, s = "", "", ""
            if hours:
                h = f"{fmt_time(hours, 'hour')} {'and' if not seconds else ''}"

            if minutes:
                m = f"{fmt_time(minutes, 'minute')} {'and' if hours else ''} "

            if seconds:
                s = f"{seconds} second{'s' if seconds > 1 else ''}"
            return f"{h}{m}{s}"

        y, m, d = "", "", ""

        if years:
            y = f"{fmt_time(years, 'year')} {'and' if not days else ''} "

        if months:
            m = f"{fmt_time(months, 'month')} {'and' if days else ''} "

        if days:
            d = f"{days} day{'s' if days > 1 else ''}"

        return f"{y}{m}{d}"


def setup(bot: commands.Bot) -> None:
    """Starts information cog."""
    bot.add_cog(information(bot))
