from discord import Embed
import textwrap
import discord
from discord.ext import commands
from .utils import time
from .utils.util import time_since, get_matching_emote


class Information(commands.Cog):
    """For generating embeds with server info and member info."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def get_bot_uptime(self, *, brief=False):
        return time.human_timedelta(self.bot.uptime, accuracy=None, brief=brief, suffix=False)

    @commands.command()
    async def uptime(self, ctx):
        """Shows the bots uptime"""
        await ctx.send(f'**{self.get_bot_uptime()}**')

    @commands.command()
    @commands.has_any_role('High Society', 'Higher Society')
    async def roles(self, ctx, member: discord.Member):
        """Sends a list of all roles in the server"""
        role_list = []
        for role in member.roles:
            if str(role.name) != '@everyone':
                role_list.append(f"*{role.name}*")
        await ctx.send(embed=discord.Embed(title=str(role_list)[1:-1], color=discord.Color.dark_gold()))

    @commands.command(name="server", aliases=["server_info", "guild", "guild_info", "info", "information"])
    async def server_info(self, ctx):
        """Sends an embed of server information."""
        created = time_since(ctx.guild.created_at, precision="days")
        region = ctx.guild.region
        roles = len(ctx.guild.roles)
        member_count = ctx.guild.member_count
        owner = ctx.guild.owner
        online_users = sum([member.status is discord.Status.online for member in ctx.guild.members])
        offline_users = sum([member.status is discord.Status.offline for member in ctx.guild.members])
        dnd_users = sum([member.status is discord.Status.dnd for member in ctx.guild.members])
        idle_users = sum([member.status is discord.Status.idle for member in ctx.guild.members])
        offline = get_matching_emote(ctx.guild, ':offline:')
        online = get_matching_emote(ctx.guild, ':online:')
        dnd = get_matching_emote(ctx.guild, ':dnd:')
        idle = get_matching_emote(ctx.guild, ':idle:')
        embed = Embed(colour=discord.Colour.blurple())
        embed.description = (
            textwrap.dedent(f"""
                **Server information**
                Created: {created}
                Region: {region}
                Owner: {owner}

                **Member counts**
                Members: {member_count:,} Roles: {roles}

                **Member statuses**
                {online} {online_users:,} {dnd} {dnd_users:,} {idle} {idle_users:,} {offline} {offline_users:,}
            """)
        )
        embed.set_thumbnail(url=ctx.guild.icon_url)
        await ctx.send(embed=embed)

    @commands.command(name="user", aliases=["user_info", "member", "member_info"])
    async def user_info(self, ctx, member: discord.Member = None) -> None:
        """Sends info about a member."""
        if member is None:
            member = ctx.author
        embed = await self.create_user_embed(ctx, member)
        await ctx.send(embed=embed)

    async def create_user_embed(self, ctx, member: discord.Member) -> Embed:
        """Creates an embed containing information on the `user`."""
        created = time_since(member.created_at, max_units=3)
        name = str(member)
        if member.nick:
            name = f"{member.nick} ({name})"
        joined = time_since(member.joined_at, max_units=3)
        roles = ", ".join(role.mention for role in member.roles[1:])
        fields = [
            (
                "User information",
                textwrap.dedent(f"""
                    Created: {created}
                    Profile: {member.mention}
                    ID: {member.id}
                """).strip()
            ),
            (
                "Member information",
                textwrap.dedent(f"""
                    Joined: {joined}
                    Roles: {roles or None}
                """).strip()
            ),
        ]
        embed = Embed(
            title=name,
        )
        for field_name, field_content in fields:
            embed.add_field(name=field_name, value=field_content, inline=False)
        embed.set_thumbnail(url=member.avatar_url_as(static_format="png"))
        embed.colour = member.top_role.colour if roles else discord.Colour.blurple()
        return embed


def setup(bot: commands.Bot) -> None:
    """Load the Information cog."""
    bot.add_cog(Information(bot))
