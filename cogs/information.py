from __future__ import annotations

import inspect
import os
import platform
import textwrap
from datetime import datetime
from io import StringIO

import discord
import orjson
import psutil
from discord.ext import commands


class information(commands.Cog):
    """Commands that give information about the bot or server."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.DB = bot.DB
        self.process = psutil.Process()

    @commands.command()
    async def changes(self, ctx):
        """Gets the last 12 commits."""
        url = "https://api.github.com/repos/Singularitat/snakebot/commits?per_page=24"

        async with ctx.typing():
            commits = await self.bot.get_json(url)

        embed = discord.Embed(color=discord.Color.blurple())

        count = 0
        for commit in commits:
            if commit["commit"]["verification"]["payload"]:
                continue
            if count == 12:
                break
            count += 1

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
        embed.add_field(name="Uptime", value=f"Since **<t:{self.bot.uptime:.0f}:R>**")
        embed.add_field(name="Pycord version", value=discord.__version__)
        embed.add_field(name="Python version", value=platform.python_version())
        embed.add_field(
            name="OS", value=f"{platform.system()} {platform.release()}({os.name})"
        )
        await ctx.send(embed=embed)

    @commands.command(aliases=["newest"])
    @commands.guild_only()
    async def oldest(self, ctx, amount: int = 10):
        """Gets the oldest accounts in a server.
        Run with the `newest` alias to get the newest members

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
    @commands.guild_only()
    async def message_top(self, ctx, amount=None):
        """Gets the users with the most messages in a server.

        Maximum amount that can be shown in the graph is 250

        amount: str
        """
        msgtop = []
        guild = str(ctx.guild.id).encode()

        for member, count in self.DB.message_count:
            if member.startswith(guild):
                msgtop.append((int(count), member.decode()))

        msgtop.sort(reverse=True)

        amount = 10 if not amount else 250 if amount.lower() == "all" else int(amount)

        total_lines = 0
        members = []
        counts = []
        lines = ""

        for count, member in msgtop:
            user = self.bot.get_user(int(member.split("-")[1]))
            if user:
                total_lines += 1

                members.append(user.display_name)
                counts.append(count)

                if total_lines < 30:
                    lines += f"**{user.display_name}:** {count} messages\n"

                if total_lines == amount:
                    break

        data = {
            "c": {
                "type": "bar",
                "data": {
                    "labels": members,
                    "datasets": [{"label": "Users", "data": counts}],
                },
            },
            "backgroundColor": "#202225",
            "format": "png",
        }

        url = "https://quickchart.io/chart/create"
        async with self.bot.client_session.get(url, json=data) as resp:
            resp = await resp.json()

        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                description=lines,
                title=f"Top {total_lines} chatters",
            ).set_image(url=resp["url"])
        )

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

        permissions = channel.permissions_for(member)
        embed = discord.Embed(color=member.color)
        embed.set_author(name=str(member), icon_url=member.avatar)

        allowed, denied = [], []
        for name, value in permissions:
            name = name.replace("_", " ").replace("guild", "server").title()
            (allowed if value else denied).append(name)

        allowed = "\n".join(allowed)
        denied = "\n".join(denied)

        embed.add_field(name="Allowed", value=f"```ansi\n[2;32m{allowed}[0m```")
        embed.add_field(name="Denied", value=f"```ansi\n[2;31m{denied}[0m```")
        await ctx.send(embed=embed)

    @commands.command()
    async def invite(self, ctx):
        """Sends the invite link of the bot."""
        # View Channels, Send Messages, Send Messages in Threads, Embed Links
        # Attach Files, Use External Emoji, Read Message History, Connect, Speak
        general_perms = discord.utils.oauth_url(
            self.bot.user.id, permissions=discord.Permissions(274881432576)
        )
        # Manage Emojis and Stickers, Kick Members, Ban Members Manage Messages
        # Manage Threads + General Perms
        mod_perms = discord.utils.oauth_url(
            self.bot.user.id, permissions=discord.Permissions(293134789638)
        )
        # Administrator
        admin_perms = discord.utils.oauth_url(
            self.bot.user.id, permissions=discord.Permissions(8)
        )
        view = discord.ui.View(
            discord.ui.Button(label="Admin Perms", url=admin_perms),
            discord.ui.Button(label="Moderator Perms", url=mod_perms),
            discord.ui.Button(label="General Perms", url=general_perms),
        )
        embed = discord.Embed(color=discord.Color.blurple())
        embed.add_field(
            name="Admin Perms",
            value="Gives the bot Administrator\n"
            "[Full Perms](https://discordapi.com/permissions.html#8)",
        )
        embed.add_field(
            name="Mod Perms",
            value="Kick, Ban and Manage Messages\n"
            "[Full Perms](https://discordapi.com/permissions.html#293134789638)",
        )
        embed.add_field(
            name="General Perms",
            value="Send Messages, Read Messages, Connect to voice and Speak\n"
            "[Full Perms](https://discordapi.com/permissions.html#274881432576)",
        )
        await ctx.send(embed=embed, view=view)

    @commands.command()
    async def ping(self, ctx):
        """Check how the bot is doing."""
        latency = (
            discord.utils.utcnow() - ctx.message.created_at
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
        memory_usage = self.process.memory_full_info().rss / 1024**2
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
            src = type(self.bot.help_command)
            filename = inspect.getsourcefile(src)
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
    async def uptime(self, ctx):
        """Shows the bots uptime."""
        await ctx.send(f"Bot has been up since **<t:{self.bot.uptime:.0f}:R>**")

    @commands.command()
    @commands.guild_only()
    async def server(self, ctx):
        """Shows information about the current server."""
        guild = ctx.guild
        offline_u, online_u, dnd_u, idle_u, bots = 0, 0, 0, 0, 0
        for member in guild.members:
            if member.bot:
                bots += 1
            if member.status is discord.Status.offline:
                offline_u += 1
            elif member.status is discord.Status.online:
                online_u += 1
            elif member.status is discord.Status.dnd:
                dnd_u += 1
            elif member.status is discord.Status.idle:
                idle_u += 1

        offline = "<:offline:766076363048222740>"
        online = "<:online:766076316512157768>"
        dnd = "<:dnd:766197955597959208>"
        idle = "<:idle:766197981955096608>"

        embed = discord.Embed(colour=discord.Colour.blurple())
        embed.description = f"""
            **Server Information**
            Created: **<t:{guild.created_at.timestamp():.0f}:R>**
            Owner: {guild.owner.mention}

            **Member Counts**
            Members: {guild.member_count:,} ({bots} bots)
            Roles: {len(guild.roles)}

            **Member Statuses**
            {online} {online_u:,} {dnd} {dnd_u:,} {idle} {idle_u:,} {offline} {offline_u:,}
        """

        if guild.icon:
            embed.set_thumbnail(url=guild.icon)

        await ctx.send(embed=embed)

    @commands.command(aliases=["member"])
    async def user(self, ctx, user: discord.Member | discord.User = None):
        """Sends info about a member.

        member: typing.Union[discord.Member, discord.User]
            The member to get info of defulting to the invoker.
        """
        user = user or ctx.author
        created = f"<t:{user.created_at.timestamp():.0f}:R>"

        embed = discord.Embed(
            title=(str(user) + (" `[BOT]`" if user.bot else "")),
            color=discord.Color.random(),
        )

        embed.add_field(
            name="User information",
            value=f"Created: **{created}**\nProfile: {user.mention}\nID: `{user.id}`",
            inline=False,
        )

        if isinstance(user, discord.Member):
            length = len(user.roles) - 1
            if length > 10:
                roles = (
                    ", ".join(role.mention for role in user.roles[1:11])
                    + f" + {length - 10} more roles"
                )
            else:
                roles = ", ".join(role.mention for role in user.roles[1:])

            joined = f"**<t:{user.joined_at.timestamp():.0f}:R>**"
            if roles and user.top_role.colour.value != 0:
                embed.color = user.top_role.colour
            embed.title = f"{user.nick} ({user})" if user.nick else embed.title

            embed.add_field(
                name="Member information",
                value=f"Joined: {joined}\nRoles: {roles or None}\n",
                inline=False,
            )
            des = "ini" if user.desktop_status.value != "offline" else "css"
            mob = "ini" if user.mobile_status.value != "offline" else "css"
            web = "ini" if user.web_status.value != "offline" else "css"

            embed.add_field(
                name="Desktop", value=f"```{des}\n[{user.desktop_status}]```"
            )
            embed.add_field(name="Mobile", value=f"```{mob}\n[{user.mobile_status}]```")
            embed.add_field(name="Web", value=f"```{web}\n[{user.web_status}]```")

        embed.set_thumbnail(url=user.display_avatar)

        await ctx.send(embed=embed)

    @commands.command(aliases=["avatar"])
    async def icon(self, ctx, user: discord.User = None):
        """Sends a members avatar url.

        user: discord.User
            The member to show the avatar of.
        """
        user = user or ctx.author
        await ctx.send(user.display_avatar)

    @commands.command()
    async def banner(self, ctx, user: discord.User = None):
        """Sends a members banner url.

        user: discord.User
            The member to show the banner of.
        """
        user = user or ctx.author

        if not user.banner:
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description="```User doesn't have a banner```",
                )
            )

        await ctx.send(user.banner.url)


def setup(bot: commands.Bot) -> None:
    """Starts information cog."""
    bot.add_cog(information(bot))
