import discord
from discord.ext import commands
import ujson
import datetime


class admin(commands.Cog):
    """Administrative commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.blacklist = self.bot.db.prefixed_db(b"blacklist-")
        self.deleted = self.bot.db.prefixed_db(b"deleted-")
        self.edited = self.bot.db.prefixed_db(b"edited-")

    @commands.has_permissions(administrator=True)
    @commands.command(hidden=True)
    async def edit(self, ctx, message: discord.Message, *, content):
        """Edits one of the bots messages.

        message: discord.Message
            The message you want to edit.
        content: str
            What the content of the message will be changed to.
        """
        await message.edit(content=content)

    @edit.error
    async def edit_handler(self, ctx, error):
        """Error handler for edit command."""
        await ctx.send("```I cannot edit this message```")

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

    async def end_date(self, duration):
        end_date = datetime.datetime.now()

        for time in duration.split():
            if time[-1] == "s":
                end_date += datetime.timedelta(seconds=int(time[:-1]))
            elif time[-1] == "m":
                end_date += datetime.timedelta(minutes=int(time[:-1]))
            elif time[-1] == "h":
                end_date += datetime.timedelta(hours=int(time[:-1]))
            elif time[-1] == "d":
                end_date += datetime.timedelta(days=int(time[:-1]))

        return str(end_date)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def downvote(self, ctx, member: discord.Member = None, *, duration=None):
        """Automatically downvotes someone.

        member: discord.Member
            The downvoted member.
        duration: str
            How long to downvote the member for e.g 5d 10h 25m 5s
        """
        embed = discord.Embed(color=discord.Color.blurple())
        if member is None:
            if list(self.blacklist) == []:
                embed.title = "No downvoted members"
                return await ctx.send(embed=embed)

            embed.title = "Downvoted members"
            for member_id in self.blacklist.iterator(include_value=False):
                embed.add_field(name="Member:", value=member_id.decode())

            return await ctx.send(embed=embed)

        member_id = str(member.id).encode()

        if self.blacklist.get(member_id):
            self.blacklist.delete(member_id)

            embed.title = "Member Undownvoted"
            embed.description = (
                f"***{member}*** has been removed from the downvote list"
            )
            return await ctx.send(embed=embed)

        await member.edit(voice_channel=None)

        self.blacklist.put(member_id, b"1")
        members = self.bot.db.get(b"downvoted_members")

        if duration is not None:
            if not members:
                data = {}
            else:
                data = ujson.loads(members)

            end_date = await self.end_date(duration)
            data[member.id] = {"date": end_date, "guild": ctx.guild.id}
            self.bot.db.put(b"downvoted_members", ujson.dumps(data).encode())

        embed.title = "Member Downvoted"
        embed.description = f"**{member}** has been added to the downvote list"
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def blacklist(self, ctx, member: discord.Member = None):
        """Blacklists someone from using the bot.

        member: discord.Member
            The blacklisted member.
        """
        embed = discord.Embed(color=discord.Color.blurple())
        if member is None:
            if list(self.blacklist) == []:
                embed.title = "No blacklisted members"
                return await ctx.send(embed=embed)

            embed.title = "Blacklisted members"
            for member_id in self.blacklist.iterator(include_value=False):
                embed.add_field(name="Member:", value=member_id.decode())
            return await ctx.send(embed=embed)

        member_id = str(member.id).encode()
        if self.blacklist.get(member_id):
            self.blacklist.delete(member_id)

            embed.title = "Member Unblacklisted"
            embed.description = f"***{member}*** has been unblacklisted"
            return await ctx.send(embed=embed)

        self.blacklist.put(member_id, b"2")
        embed.title = "Member Blacklisted"
        embed.description = f"**{member}** has been added to the blacklist"

        await ctx.send(embed=embed)

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban_member(
        self, ctx, member: discord.Member, duration=None, *, reason=None
    ):
        """Bans a member.

        Usage:
        .ban @Singularity#8953 "3d 5h 10m" He was rude

        You need the quotes for the duration or it will only get the first argument

        member: discord.Member
            The member to ban.
        duration: str
            How long to ban the member for.
        reason: str
            The reason for banning the member.
        """
        if ctx.author.top_role <= member.top_role and ctx.guild.owner != ctx.author:
            return await ctx.send("```You can't ban someone higher or equal to you```")

        await member.ban(reason=reason)
        members = self.bot.db.get(b"banned_members")
        if not members:
            data = {}
        else:
            data = ujson.loads(members)

        end_date = await self.end_date(duration)

        data[member.id] = {"date": end_date, "guild": ctx.guild.id}

        self.bot.db.put(b"banned_members", ujson.dumps(data).encode())

        await ctx.send(
            embed=discord.Embed(
                title=f"Banned {member} untill {end_date}",
                color=discord.Color.dark_red(),
            )
        )

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick_member(self, ctx, member: discord.Member):
        """Kicks a member.

        member: discord.Member
            The member to kick.
        """
        if ctx.author.top_role <= member.top_role and ctx.guild.owner != ctx.author:
            return await ctx.send("```You can't kick someone higher or equal to you```")

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
            The name of the role.
        """
        role = discord.utils.get(member.guild.roles, name=role)
        if role is None:
            return await ctx.send("```Could not find role```")

        if role in member.roles:
            await member.remove_roles(role)
            return await ctx.send(f"Removed the role {role} from {member}")

        await member.add_roles(role)
        return await ctx.send(f"Gave {member} the role {role}")

    @commands.group()
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def purge(self, ctx):
        """Purges messages.

        num: int
            The number of messages to delete defaults to 20.
        """
        if ctx.invoked_subcommand is None:
            try:
                await ctx.channel.purge(limit=int(ctx.subcommand_passed) + 1)
            except ValueError:
                await ctx.send("No subcommand passed")

    @purge.command()
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def till(self, ctx, message_id: int):
        """Clear messages in a channel until the given message_id. Given ID is not deleted."""
        try:
            message = await ctx.fetch_message(message_id)
        except discord.errors.NotFound:
            return await ctx.send("```Message could not be found in this channel```")

        await ctx.channel.purge(after=message)

    @purge.command()
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def user(self, ctx, member: discord.Member, num_messages: int = 100):
        """Clear all messagges of <User> withing the last [n=100] messages."""

        def check(msg):
            return msg.author.id == member.id

        await ctx.channel.purge(limit=num_messages, check=check, before=None)

    @purge.command()
    @commands.has_permissions(manage_channels=True)
    @commands.guild_only()
    async def channel(self, ctx, channel: discord.TextChannel = None):
        """Purges a channel by cloning and deleting it.

        channel: discord.TextChannel
            The channel to clone and delete.
        """
        if channel is None:
            channel = ctx.channel

        await channel.clone()
        await channel.delete()

    @commands.group()
    async def history(self, ctx):
        """Shows the edited message or deleted message history of a member."""
        if ctx.invoked_subcommand is None:
            await ctx.send(f"Usage: `{ctx.prefix}history deleted`")

    @history.command(hidden=True)
    @commands.has_permissions(manage_messages=True)
    async def deleted(self, ctx, member: discord.Member = None, amount: int = 5):
        """Shows a members most recent deleted message history.

        member: discord.Member
            The member to get the history of.
        amount: int
            The amount of messages to get.
        """
        if member is None:
            member = ctx.author

        member_id = str(member.id).encode()
        deleted = self.deleted.get(member_id)

        if deleted is None:
            return await ctx.send("```No deleted messages found```")

        deleted = ujson.loads(deleted)

        embed = discord.Embed(
            color=discord.Color.blurple(),
            title=f"{member.display_name}'s Deleted Messages",
        )

        msg = ""

        for index, date in enumerate(reversed(deleted)):
            if index == amount:
                break

            msg += f"{date}: {deleted[date]}\n"

        embed.description = f"```{msg}```"
        return await ctx.send(embed=embed)

    @history.command(hidden=True)
    @commands.has_permissions(manage_messages=True)
    async def edited(self, ctx, member: discord.Member = None, amount: int = 5):
        """Shows a members most recent edit message history.

        member: discord.Member
            The member to get the edit history of.
        amount: int
            The amount of messages to get.
        """
        if member is None:
            member = ctx.author

        member_id = str(member.id).encode()
        edited = self.edited.get(member_id)

        if edited is None:
            return await ctx.send("```No edited messages found```")

        edited = ujson.loads(edited)

        embed = discord.Embed(
            color=discord.Color.blurple(),
            title=f"{member.display_name}'s Edited Messages",
        )

        msg = ""

        for index, date in enumerate(reversed(edited)):
            if index == amount:
                break

            msg += f"{date}: {edited[date][0]} >>> {edited[date][1]}\n"

        embed.description = f"```{msg}```"
        return await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    """Starts admin cog."""
    bot.add_cog(admin(bot))
