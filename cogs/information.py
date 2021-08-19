from datetime import datetime
from io import StringIO
import inspect
import os
import textwrap
import typing

from discord.ext import commands
import discord
import orjson
import psutil

from cogs.utils.useful import get_json


class information(commands.Cog):
    """Commands that give information about the bot or server."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.DB = bot.DB
        self.process = psutil.Process()

    @commands.command()
    async def roles(self, ctx):
        """Shows the roles of the server."""
        description = ""

        for i, role in enumerate(ctx.guild.roles[1:], start=1):
            if not i % 3:
                description += f"{role}\n"
            else:
                description += f"{str(role):<20}"

        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                title="Server Roles",
                description=f"```{description}```",
            )
        )

    @commands.command()
    async def changes(self, ctx):
        """Gets the last 12 commits."""
        url = "https://api.github.com/repos/Singularitat/snakebot/commits?per_page=12"

        async with ctx.typing():
            commits = await get_json(self.bot.client_session, url)

        embed = discord.Embed(color=discord.Color.blurple())

        for commit in commits:
            timestamp = int(
                datetime.fromisoformat(
                    commit["commit"]["author"]["date"][:-1]
                ).timestamp()
            )
            embed.add_field(
                name=f"<t:{timestamp}>",
                value=f"[**{commit['commit']['message']}**]({commit['html_url']})",
            )

        await ctx.send(embed=embed)

    @commands.command()
    async def about(self, ctx):
        """Shows information about the bot."""
        embed = discord.Embed(color=discord.Color.blurple())
        embed.add_field(name="Total Commands", value=len(self.bot.commands))
        embed.add_field(
            name="Source", value="[github](https://github.com/Singularitat/snakebot)"
        )
        embed.add_field(name="discord.py version", value=discord.__version__)
        await ctx.send(embed=embed)

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
                for m, b in self.DB.message_count
                if int(m.decode().split("-")[0]) == ctx.guild.id
            ],
            reverse=True,
        )[:amount]

        embed = discord.Embed(color=discord.Color.blurple())
        members = []
        counts = []

        for count, member in msgtop:
            user = self.bot.get_user(int(member.split("-")[1]))
            if user:
                members.append(user.display_name)
                counts.append(count)

        description = "\n".join(
            [
                f"**{member}:** {count} messages"
                for count, member in zip(members, counts)
            ]
        )

        if len(description) > 2048:
            embed.description = "```Message to large to send.```"
            return await ctx.send(embed=embed)

        embed.title = f"Top {len(msgtop)} chatters"
        embed.description = description
        data = str(
            {
                "type": "bar",
                "data": {
                    "labels": members,
                    "datasets": [{"label": "Users", "data": counts}],
                },
            }
        ).replace(" ", "%20")

        embed.set_image(url=f"https://quickchart.io/chart?bkg=%23202225&c={data}")

        await ctx.send(embed=embed)

    @commands.command()
    async def rule(self, ctx, number: int):
        """Shows the rules of the server.

        number: int
            Which rule to get.
        """
        rules = self.DB.main.get(f"{ctx.guild.id}-rules".encode())
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
        rules = self.DB.main.get(f"{ctx.guild.id}-rules".encode())
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
        embed.set_author(name=str(member), icon_url=member.avatar)

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
        await ctx.send(
            discord.utils.oauth_url(
                self.bot.user.id, permissions=discord.Permissions.all()
            )
        )

    @commands.command()
    async def ping(self, ctx):
        """Check how the bot is doing."""
        latency = (
            datetime.utcnow() - ctx.message.created_at.replace(tzinfo=None)
        ).total_seconds() * 1000

        if latency <= 0.05:
            latency = "Clock is out of sync"
        else:
            latency = f"`{latency:.2f} ms`"

        embed = discord.Embed(color=discord.Color.blurple())
        embed.add_field(name="Command Latency", value=latency, inline=False)
        embed.add_field(
            name="Discord API Latency", value=f"`{self.bot.latency*1000:.2f} ms`"
        )

        await ctx.send(embed=embed)

    @commands.command()
    async def usage(self, ctx):
        """Shows the bot's memory and cpu usage."""
        memory_usage = self.process.memory_full_info().rss / 1024 ** 2
        cpu_usage = self.process.cpu_percent()

        embed = discord.Embed(color=discord.Color.blurple())
        embed.add_field(name="Memory Usage: ", value=f"**{memory_usage:.2f} MB**")
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
        code = textwrap.dedent("".join(lines)).replace("`", "`\u200b")

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
        await ctx.send(f"Bot has been up since **<t:{self.bot.uptime:.0f}:R>**")

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
                Created: **<t:{ctx.guild.created_at.timestamp():.0f}:R>**
                Region: {ctx.guild.region.name.title()}
                Owner: {ctx.guild.owner}

                **Member Counts**
                Members: {ctx.guild.member_count:,} Roles: {len(ctx.guild.roles)}

                **Member Statuses**
                {online} {online_users:,} {dnd} {dnd_users:,} {idle} {idle_users:,} {offline} {offline_users:,}
            """
        )
        embed.set_thumbnail(url=ctx.guild.icon)
        await ctx.send(embed=embed)

    @commands.command(name="user", aliases=["member"])
    async def user_info(
        self, ctx, user: typing.Union[discord.Member, discord.User] = None
    ):
        """Sends info about a member.

        member: discord.Member
            The member to get info of defulting to the invoker.
        """
        user = user or ctx.author
        created = f"<t:{user.created_at.timestamp():.0f}:R>"

        embed = discord.Embed(
            title=(str(user) + (" `[BOT]`" if user.bot else "")),
            color=discord.Color.blurple(),
        )

        embed.add_field(
            name="User information",
            value=f"Created: **{created}**\nProfile: {user.mention}\nID: {user.id}",
            inline=False,
        )

        if hasattr(user, "guild"):
            roles = ", ".join(role.mention for role in user.roles[1:])
            joined = f"**<t:{user.joined_at.timestamp():.0f}:R>**"
            embed.color = user.top_role.colour if roles else embed.color
            embed.title = f"{user.nick} ({user})" if user.nick else embed.title

            embed.add_field(
                name="Member information",
                value=f"Joined: {joined}\nRoles: {roles or None}",
                inline=False,
            )

        embed.set_thumbnail(url=user.avatar)

        await ctx.send(embed=embed)

    @commands.command()
    async def icon(self, ctx, user: discord.User = None):
        """Sends a members avatar url.

        user: discord.User
            The member to show the avatar of.
        """
        user = user or ctx.author
        await ctx.send(user.avatar)


def setup(bot: commands.Bot) -> None:
    """Starts information cog."""
    bot.add_cog(information(bot))
