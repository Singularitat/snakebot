from discord import Embed
import textwrap
import discord
from discord.ext import commands
from .utils.util import (
    time_since,
    get_matching_emote
)


class Information(commands.Cog):
    """A cog with commands for generating embeds with server info, such as server stats and user info."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    @commands.has_any_role('High Society', 'Higher Society')
    async def roles(self, ctx, member: discord.Member):
        role_list = []
        for role in member.roles:
            if str(role.name) != '@everyone':
                role_list.append(f"*{role.name}*")
        await ctx.send(embed=discord.Embed(title=str(role_list)[1:-1], color=discord.Color.dark_gold()))

    @commands.command(name="server", aliases=["server_info", "guild", "guild_info", "info", "information"])
    async def server_info(self, ctx):
        """Returns an embed of server information."""
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
    async def user_info(self, ctx, user: discord.Member = None) -> None:
        """Returns info about a user."""
        if user is None:
            user = ctx.author
        embed = await self.create_user_embed(ctx, user)
        await ctx.send(embed=embed)

    async def create_user_embed(self, ctx, user: discord.Member) -> Embed:
        """Creates an embed containing information on the `user`."""
        created = time_since(user.created_at, max_units=3)
        name = str(user)
        if user.nick:
            name = f"{user.nick} ({name})"
        joined = time_since(user.joined_at, max_units=3)
        roles = ", ".join(role.mention for role in user.roles[1:])
        fields = [
            (
                "User information",
                textwrap.dedent(f"""
                    Created: {created}
                    Profile: {user.mention}
                    ID: {user.id}
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
        embed.set_thumbnail(url=user.avatar_url_as(static_format="png"))
        embed.colour = user.top_role.colour if roles else discord.Colour.blurple()
        return embed


def setup(bot: commands.Bot) -> None:
    """Load the Information cog."""
    bot.add_cog(Information(bot))
