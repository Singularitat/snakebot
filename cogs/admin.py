import discord
from discord.ext import commands
import ujson
import asyncio


class admin(commands.Cog):
    """Administrative commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.loop = asyncio.get_event_loop()
        self.blacklist = self.bot.db.prefixed_db(b"blacklist-")
        self.deleted = self.bot.db.prefixed_db(b"deleted-")
        self.edited = self.bot.db.prefixed_db(b"edited-")

    @commands.has_permissions(administrator=True)
    @commands.command()
    async def toggle(self, ctx, *, command):
        """Toggles a command in the current guild."""
        embed = discord.Embed(color=discord.Color.blurple())

        if not self.bot.get_command(command):
            embed.description = "```Command not found.```"
            return await ctx.send(embed=embed)

        key = f"{ctx.guild.id}-{command}".encode()
        state = self.bot.db.get(key)

        if state is None:
            self.bot.db.put(key, b"1")
            embed.description = f"```Disabled the {command} command```"
            return await ctx.send(embed=embed)

        self.bot.db.delete(key)
        embed.description = f"```Enabled the {command} command```"
        return await ctx.send(embed=embed)

    @commands.has_permissions(administrator=True)
    @commands.command(hidden=True)
    async def emojis(self, ctx):
        """Shows a list of the current emojis being voted on."""
        emojis = self.bot.db.get(b"emoji_submissions")

        if not emojis:
            emojis = {}
        else:
            emojis = ujson.loads(emojis)

        if len(emojis) == 0:
            return await ctx.send("```No emojis found```")

        msg = ""

        for name, users in emojis.items():
            msg += f"{name}: {users}\n"

        embed = discord.Embed(color=discord.Color.blurple())
        embed.description = f"```{msg}```"
        await ctx.send(embed=embed)

    @commands.has_permissions(administrator=True)
    @commands.command(hidden=True, aliases=["demoji"])
    async def delete_emoji(self, ctx, message_id):
        """Shows a list of the current emojis being voted on.

        message_id: str
            Id of the message to remove from the db.
        """
        emojis = self.bot.db.get(b"emoji_submissions")

        if not emojis:
            emojis = {}
        else:
            emojis = ujson.loads(emojis)

        try:
            emojis.pop(message_id)
        except KeyError:
            await ctx.send(f"Message {message_id} not found in emojis")

        self.bot.db.put(b"emoji_submissions", ujson.dumps(emojis).encode())

    @commands.has_permissions(administrator=True)
    @commands.command(hidden=True, aliases=["aemoji"])
    async def add_emoji(self, ctx, message_id, name):
        """Adds a emoji to be voted on.

        message_id: int
            Id of the message you are adding the emoji of.
        """
        emojis = self.bot.db.get(b"emoji_submissions")

        if not emojis:
            emojis = {}
        else:
            emojis = ujson.loads(emojis)

        emojis[message_id] = {"name": name, "users": []}

        self.bot.db.put(b"emoji_submissions", ujson.dumps(emojis).encode())

    @commands.has_permissions(administrator=True)
    @commands.command(hidden=True)
    async def edit(self, ctx, message: discord.Message, *, content):
        """Edits the content of a bot message.

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

    @commands.has_permissions(administrator=True)
    @commands.command(hidden=True)
    async def embededit(self, ctx, message: discord.Message, description, title=None):
        """Edits the embed of a bot message.

        message: discord.Message
            The message you want to edit.
        description: str
            Description of the embed.
        title: str
            Title of the embed.
        """
        embed = discord.Embed(color=discord.Color.blurple())
        embed.description = description
        if title:
            embed.title = title
        await message.edit(embed=embed)

    @commands.has_permissions(administrator=True)
    @commands.command(hidden=True)
    async def embed(self, ctx, description, title=None):
        """Sends an embed.

        message: discord.Message
            The message you want to edit.
        description: str
            Description of the embed.
        title: str
            Title of the embed.
        """
        embed = discord.Embed(color=discord.Color.blurple())
        embed.description = description
        if title:
            embed.title = title
        await ctx.send(embed=embed)

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
        """Converts a duration to an end date.

        duration: str
            How much to add onto the current date e.g 5d 10h 25m 5s
        """
        seconds = 0
        try:
            for time in duration.split():
                if time[-1] == "s":
                    seconds += int(time[:-1])
                elif time[-1] == "m":
                    seconds += int(time[:-1]) * 60
                elif time[-1] == "h":
                    seconds += int(time[:-1]) * 3600
                elif time[-1] == "d":
                    seconds += int(time[:-1]) * 86400
        except ValueError:
            return None

        return seconds

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def downvote(self, ctx, member: discord.Member = None, *, duration=None):
        """Automatically downvotes someone.

        member: discord.Member
            The downvoted member.
        duration: str
            How long to downvote the user for e.g 5d 10h 25m 5s
        """
        embed = discord.Embed(color=discord.Color.blurple())
        if member is None:
            if list(self.blacklist) == []:
                embed.title = "No downvoted users"
                return await ctx.send(embed=embed)

            embed.title = "Downvoted users"
            for member_id in self.blacklist.iterator(include_value=False):
                guild, member_id = member_id.decode().split("-")
                embed.add_field(
                    name="User:",
                    value=f"{self.bot.get_guild(int(guild))}: {member_id}",
                )

            return await ctx.send(embed=embed)

        member_id = f"{ctx.guild.id}-{str(member.id)}".encode()

        if self.blacklist.get(member_id):
            self.blacklist.delete(member_id)

            embed.title = "User Undownvoted"
            embed.description = (
                f"***{member}*** has been removed from the downvote list"
            )
            return await ctx.send(embed=embed)

        await member.edit(voice_channel=None)

        if duration is None:
            self.blacklist.put(member_id, b"1")
            embed.title = "User Downvoted"
            embed.description = f"**{member}** has been added to the downvote list"
            return await ctx.send(embed=embed)

        seconds = await self.end_date(duration)

        if not seconds:
            embed.description = "```Invalid duration. Example: '3d 5h 10m'```"
            return await ctx.send(embed=embed)

        self.blacklist.put(member_id, b"1")
        self.loop.call_later(seconds, self.blacklist.delete, member_id)

        embed.title = "User Undownvoted"
        embed.description = f"***{member}*** has been added from the downvote list"
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def wipe_downvote(self, ctx):
        """Wipes everyone from the downvote list."""
        for member, value in self.blacklist:
            self.blacklist.delete(member)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def blacklist(self, ctx, user: discord.User = None):
        """Blacklists someone from using the bot.

        user: discord.User
            The blacklisted user.
        """
        embed = discord.Embed(color=discord.Color.blurple())
        if user is None:
            if list(self.blacklist) == []:
                embed.title = "No blacklisted users"
                return await ctx.send(embed=embed)

            embed.title = "Blacklisted users"
            for user_id in self.blacklist.iterator(include_value=False):
                embed.add_field(name="Member:", value=user_id.decode())
            return await ctx.send(embed=embed)

        user_id = str(user.id).encode()
        if self.blacklist.get(user_id):
            self.blacklist.delete(user_id)

            embed.title = "User Unblacklisted"
            embed.description = f"***{user}*** has been unblacklisted"
            return await ctx.send(embed=embed)

        self.blacklist.put(user_id, b"2")
        embed.title = "User Blacklisted"
        embed.description = f"**{user}** has been added to the blacklist"

        await ctx.send(embed=embed)

    async def unban(self, guild: discord.Guild, member: discord.Member):
        await guild.unban(member)

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
        embed = discord.Embed(color=discord.Color.dark_red())
        if ctx.author.top_role <= member.top_role and ctx.guild.owner != ctx.author:
            embed.description = "```You can't ban someone higher or equal to you```"
            return await ctx.send(embed=embed)

        if not duration:
            await member.ban(reason=reason)
            embed.title = f"Banned {member}"
            return await ctx.send(embed=embed)

        seconds = await self.end_date(duration)

        if not seconds:
            embed.description = "```Invalid duration. Example: '3d 5h 10m'```"
            return await ctx.send(embed=embed)

        await member.ban(reason=reason)
        self.loop.call_later(seconds, asyncio.create_task, ctx.guild.unban(member))

        embed.title = f"Banned {member} for {seconds}s"
        await ctx.send(embed=embed)

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
    async def role(self, ctx, role_name: str, member: discord.Member = None):
        """Gives member a role.

        member: discord.Member
            The member to give the role.
        role: str
            The name of the role.
        """
        embed = discord.Embed(color=discord.Color.blurple())

        if member is None:
            member = ctx.author

        if (
            ctx.author != member
            and ctx.author.top_role <= member.top_role
            and ctx.guild.owner != ctx.author
        ):
            embed.title = "```You can't change the roles of someone higher than you```"
            return await ctx.send(embed=embed)

        role = None

        for r in ctx.guild.roles:
            if r.name.lower() == role_name.lower():
                role = r
                break

        if role is None:
            embed.title = "```Couldn't find role``"
            return await ctx.send(embed=embed)

        if role in member.roles:
            await member.remove_roles(role)
            embed.title = f"Removed the role {role} from {member}"
            return await ctx.send(embed=embed)

        await member.add_roles(role)
        embed.title = f"Gave {member} the role {role}"
        return await ctx.send(embed=embed)

    @commands.group()
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def purge(self, ctx):
        """Purges messages.

        num: int
            The number of messages to delete.
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
    async def user(self, ctx, user: discord.User, num_messages: int = 100):
        """Clear all messagges of <User> withing the last [n=100] messages.

        user: discord.User
            The user to purge the messages of.
        num_messages: int
            The number of messages to check.
        """

        def check(msg):
            return msg.author.id == user.id

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

    @commands.group(hidden=True)
    async def history(self, ctx):
        """Shows the edited message or deleted message history of a member."""
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(color=discord.Color.blurple())
            embed.description = f"```Usage: {ctx.prefix}history [deleted/edited]```"
            await ctx.send(embed=embed)

    @history.command(aliases=["d"])
    @commands.has_permissions(manage_messages=True)
    async def deleted(self, ctx, user: discord.User = None, amount: int = 10):
        """Shows a members most recent deleted message history.

        user: discord.User
            The user to get the history of.
        amount: int
            The amount of messages to get.
        """
        if user is None:
            user = ctx.author

        user_id = str(user.id).encode()
        deleted = self.deleted.get(user_id)

        if deleted is None:
            return await ctx.send("```No deleted messages found```")

        deleted = ujson.loads(deleted)

        embed = discord.Embed(
            color=discord.Color.blurple(),
            title=f"{user.display_name}'s Deleted Messages",
        )

        msg = ""

        for index, date in enumerate(reversed(deleted)):
            if index == amount:
                break

            # The replace replaces the backticks with a backtick and a zero width space
            msg += f"{date}: {deleted[date].replace('`', '`​')}\n"

        embed.description = f"```{msg}```"
        return await ctx.send(embed=embed)

    @history.command(aliases=["e"])
    @commands.has_permissions(manage_messages=True)
    async def edited(self, ctx, user: discord.User = None, amount: int = 10):
        """Shows a users most recent edit message history.

        member: discord.User
            The user to get the edit history of.
        amount: int
            The amount of messages to get.
        """
        if user is None:
            user = ctx.author

        user_id = str(user.id).encode()
        edited = self.edited.get(user_id)

        if edited is None:
            return await ctx.send("```No edited messages found```")

        edited = ujson.loads(edited)

        embed = discord.Embed(
            color=discord.Color.blurple(),
            title=f"{user.display_name}'s Edited Messages",
        )

        msg = ""

        for index, date in enumerate(reversed(edited)):
            if index == amount:
                break

            # The replace replaces the backticks with a backtick and a zero width space
            before = edited[date][0].replace("`", "`​")
            after = edited[date][1].replace("`", "`​")

            msg += f"{date}: {before} >>> {after}\n"

        embed.description = f"```{msg}```"
        return await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    """Starts admin cog."""
    bot.add_cog(admin(bot))
