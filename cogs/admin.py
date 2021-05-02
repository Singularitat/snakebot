import discord
from discord.ext import commands
import ujson
import asyncio
import cogs.utils.database as DB


class admin(commands.Cog):
    """Administrative commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.loop = asyncio.get_event_loop()

    async def cog_check(self, ctx):
        """Checks if the member is an owner.

        ctx: commands.Context
        """
        if not ctx.author.guild_permissions.administrator:
            await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.red(),
                    description="```You need to be an Administrator to run this command.```",
                )
            )
            return False
        return True

    @commands.command()
    async def color_roles(self, ctx):
        """Creates basiic color roles if they don't exist."""
        roles = {
            "Gold": (discord.Color.gold(), "⭐"),
            "Red": (discord.Color.from_rgb(255, 0, 0), "🔴"),
            "Orange": (discord.Color.orange(), "🟠"),
            "Green": (discord.Color.green(), "🟢"),
            "Magenta": (discord.Color.magenta(), "🟣"),
            "Blue": (discord.Color.blue(), "🔵"),
            "Blurple": (discord.Color.blurple(), "💙"),
        }
        rrole = {}

        msg = (
            "**Color Role Menu:**\nReact for a color role.\n"
            "Also the emojis aren't accurate to what color the role is.\n\n"
        )

        for name in roles:
            role = discord.utils.get(ctx.guild.roles, name=name)
            if not role:
                role = await ctx.guild.create_role(
                    name=name,
                    permissions=discord.Permissions.none(),
                    color=roles[name][0],
                )
            rrole[roles[name][1]] = role.id
            msg += f"{roles[name][1]}: `{name}`\n\n"

        message = await ctx.send(msg)

        DB.rrole.put(str(message.id).encode(), ujson.dumps(rrole).encode())
        for name in roles:
            await message.add_reaction(roles[name][1])

    @commands.command()
    async def lockall(self, ctx, toggle: bool = True):
        """Removes the send messages permissions from @everyone in every category.

        toggle: bool
            Use False to let @everyone send messages again.
        """
        for category in ctx.guild.categories:
            await category.set_permissions(
                ctx.guild.default_role, send_messages=not toggle if toggle else None
            )
        embed = discord.Embed(color=discord.Color.blurple())
        if toggle:
            embed.description = "```Set all categories to read only.```"
        else:
            embed.description = "```Reset categories read permissions to default.```"
        await ctx.send(embed=embed)

    @commands.command()
    async def toggle(self, ctx, *, command):
        """Toggles a command in the current guild."""
        embed = discord.Embed(color=discord.Color.blurple())

        if not self.bot.get_command(command):
            embed.description = "```Command not found.```"
            return await ctx.send(embed=embed)

        key = f"{ctx.guild.id}-{command}".encode()
        state = DB.db.get(key)

        if state is None:
            DB.db.put(key, b"1")
            embed.description = f"```Disabled the {command} command```"
            return await ctx.send(embed=embed)

        DB.db.delete(key)
        embed.description = f"```Enabled the {command} command```"
        return await ctx.send(embed=embed)

    @commands.command(hidden=True)
    async def emojis(self, ctx):
        """Shows a list of the current emojis being voted on."""
        emojis = DB.db.get(b"emoji_submissions")

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

    @commands.command(hidden=True, aliases=["demoji"])
    async def delete_emoji(self, ctx, message_id):
        """Shows a list of the current emojis being voted on.

        message_id: str
            Id of the message to remove from the db.
        """
        emojis = DB.db.get(b"emoji_submissions")

        if not emojis:
            emojis = {}
        else:
            emojis = ujson.loads(emojis)

        try:
            emojis.pop(message_id)
        except KeyError:
            await ctx.send(f"Message {message_id} not found in emojis")

        DB.db.put(b"emoji_submissions", ujson.dumps(emojis).encode())

    @commands.command(hidden=True, aliases=["aemoji"])
    async def add_emoji(self, ctx, message_id, name):
        """Adds a emoji to be voted on.

        message_id: int
            Id of the message you are adding the emoji of.
        """
        emojis = DB.db.get(b"emoji_submissions")

        if not emojis:
            emojis = {}
        else:
            emojis = ujson.loads(emojis)

        emojis[message_id] = {"name": name, "users": []}

        DB.db.put(b"emoji_submissions", ujson.dumps(emojis).encode())

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
    async def downvote(self, ctx, member: discord.Member = None, *, duration=None):
        """Automatically downvotes someone.

        member: discord.Member
            The downvoted member.
        duration: str
            How long to downvote the user for e.g 5d 10h 25m 5s
        """
        embed = discord.Embed(color=discord.Color.blurple())
        if member is None:
            if list(DB.blacklist) == []:
                embed.title = "No downvoted users"
                return await ctx.send(embed=embed)

            embed.title = "Downvoted users"
            for member_id in DB.blacklist.iterator(include_value=False):
                guild, member_id = member_id.decode().split("-")
                embed.add_field(
                    name="User:",
                    value=f"{self.bot.get_guild(int(guild))}: {member_id}",
                )

            return await ctx.send(embed=embed)

        member_id = f"{ctx.guild.id}-{str(member.id)}".encode()

        if DB.blacklist.get(member_id):
            DB.blacklist.delete(member_id)

            embed.title = "User Undownvoted"
            embed.description = (
                f"***{member}*** has been removed from the downvote list"
            )
            return await ctx.send(embed=embed)

        await member.edit(voice_channel=None)

        if duration is None:
            DB.blacklist.put(member_id, b"1")
            embed.title = "User Downvoted"
            embed.description = f"**{member}** has been added to the downvote list"
            return await ctx.send(embed=embed)

        seconds = await self.end_date(duration)

        if not seconds:
            embed.description = "```Invalid duration. Example: '3d 5h 10m'```"
            return await ctx.send(embed=embed)

        DB.blacklist.put(member_id, b"1")
        self.loop.call_later(seconds, DB.blacklist.delete, member_id)

        embed.title = "User Undownvoted"
        embed.description = f"***{member}*** has been added from the downvote list"
        await ctx.send(embed=embed)

    @commands.command()
    async def wipe_downvote(self, ctx):
        """Wipes everyone from the downvote list."""
        for member, value in DB.blacklist:
            DB.blacklist.delete(member)

    @commands.command()
    async def blacklist(self, ctx, user: discord.User = None):
        """Blacklists someone from using the bot.

        user: discord.User
            The blacklisted user.
        """
        embed = discord.Embed(color=discord.Color.blurple())
        if user is None:
            if list(DB.blacklist) == []:
                embed.title = "No blacklisted users"
                return await ctx.send(embed=embed)

            embed.title = "Blacklisted users"
            for user_id in DB.blacklist.iterator(include_value=False):
                embed.add_field(name="Member:", value=user_id.decode())
            return await ctx.send(embed=embed)

        user_id = f"{ctx.guild.id}-{str(user.id)}".encode()
        if DB.blacklist.get(user_id):
            DB.blacklist.delete(user_id)

            embed.title = "User Unblacklisted"
            embed.description = f"***{user}*** has been unblacklisted"
            return await ctx.send(embed=embed)

        DB.blacklist.put(user_id, b"2")
        embed.title = "User Blacklisted"
        embed.description = f"**{user}** has been added to the blacklist"

        await ctx.send(embed=embed)

    async def unban(self, guild: discord.Guild, member: discord.Member):
        await guild.unban(member)


def setup(bot: commands.Bot) -> None:
    """Starts admin cog."""
    bot.add_cog(admin(bot))
