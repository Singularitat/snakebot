import re

import discord
import orjson
from discord.ext import commands

from cogs.utils.time import parse_time


class RoleButton(discord.ui.Button["ButtonRoles"]):
    def __init__(self, role: discord.Role, name: str, custom_id: str, row: int):
        self.role = role

        super().__init__(
            style=discord.ButtonStyle.secondary,
            label=name or role.name,
            custom_id=custom_id,
            row=row,
        )

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user

        if user.get_role(self.role.id):
            await user.remove_roles(self.role)
        else:
            await user.add_roles(self.role)


class ButtonRoles(discord.ui.View):
    def __init__(
        self, bot: commands.Bot, guild: int, roles: list[(int, str)], message_id: str
    ):
        super().__init__(timeout=None)
        guild = bot.get_guild(guild)
        count = 0
        row = 0

        if not guild:
            return

        self.guild = guild

        for role, name in roles:
            if role == "break":
                row += 1
                count = 0
                continue

            role = guild.get_role(role)

            if role:
                self.add_item(RoleButton(role, name, f"{message_id}-{role.id}", row))
                count += 1
                if count % 5 == 0:
                    row += 1


class admin(commands.Cog):
    """Administrative commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.DB = bot.DB
        self.loop = bot.loop

    async def cog_check(self, ctx):
        """Checks if the member is an administrator.

        ctx: commands.Context
        """
        if isinstance(ctx.author, discord.User):
            return ctx.author.id in self.bot.owner_ids
        return ctx.author.guild_permissions.administrator

    def on_ready(self):
        for message_id, data in self.DB.rrole:
            message_id = message_id.decode()
            data = orjson.loads(data)

            self.bot.add_view(
                ButtonRoles(self.bot, data["guild"], data["roles"], message_id)
            )

    @commands.command()
    async def role(self, ctx, *, information):
        """Creates a button role message.

        Example usage:
        .role `\u200B`\u200B`\u200Bless
        **Pronoun Role Menu**
        Click a button for a role
        he/him             | he/him
        she/her            |
        break
        they/them          |
        950348151674511360 |
        `\u200B`\u200B`\u200B

        Code blocks are optional.
        If a line doesn't have a | or is just a break then it is included in the title.
        To move to the next row of buttons early use break.
        Before the | is either an id or role name and after is the button label.
        If you don't give a button label the role name is used.
        """
        information = re.sub(r"```\w+\n|```", "", information)

        title = ""
        roles = []
        failed = []

        for line in information.split("\n"):
            role_name, *display = line.split("|")

            if role_name == "break":
                roles.append(("break", None))
                continue

            if not display:
                title += f"{role_name}\n"
                continue

            if not role_name:
                continue

            try:
                role_id = int(role_name)
            except ValueError:
                role = discord.utils.get(ctx.guild.roles, name=role_name.strip())

                if not role:
                    failed.append(role_name)
                    continue  # failed to get role

                role_id = role.id

            roles.append((role_id, display[0].strip()))

        message_id = str(ctx.message.id)

        await ctx.send(
            title, view=ButtonRoles(self.bot, ctx.guild.id, roles, message_id)
        )
        if failed:
            await ctx.send(f"Failed to find the following roles: {failed}")
        data = {
            "guild": ctx.guild.id,
            "roles": roles,
        }
        self.DB.rrole.put(message_id.encode(), orjson.dumps(data))

    @commands.command()
    async def prefix(self, ctx, prefix=None):
        """Changes the bot prefix in a guild.

        prefix: str
        """
        embed = discord.Embed(color=discord.Color.blurple())
        key = f"{ctx.guild.id}-prefix".encode()
        if not prefix:
            embed.description = (
                f"```xl\nCurrent prefix is: {self.DB.main.get(key, b'.').decode()}```"
            )
            return await ctx.send(embed=embed)
        self.DB.main.put(key, prefix.encode())
        embed.description = f"```prolog\nChanged prefix to {prefix}```"
        await ctx.send(embed=embed)

    @commands.command()
    async def unsnipe(self, ctx):
        """Unsnipes the last deleted message."""
        self.DB.main.delete(f"{ctx.guild.id}-snipe_message".encode())

    @commands.command()
    async def sudoin(self, ctx, channel: discord.TextChannel, *, command: str):
        """Runs a command in another channel.

        channel: discord.TextChannel
        command: str
        """
        ctx.message.channel = channel
        ctx.message.content = f"{ctx.prefix}{command}"
        new_ctx = await self.bot.get_context(ctx.message, cls=type(ctx))
        new_ctx.reply = new_ctx.send  # Can't reply to messages in other channels
        await self.bot.invoke(new_ctx)

    @commands.command(name="removereact")
    async def remove_reaction(self, ctx, message: discord.Message, reaction):
        """Removes a reaction from a message.

        message: discord.Message
            The id of the message you want to remove the reaction from.
        reaction: Union[discord.Emoji, str]
            The reaction to remove.
        """
        await message.clear_reaction(reaction)

    @commands.command(name="removereacts")
    async def remove_reactions(self, ctx, message: discord.Message):
        """Removes all reactions from a message.

        message: discord.Message
            The id of the message you want to remove the reaction from.
        """
        await message.clear_reactions()

    @commands.command()
    async def togglelog(self, ctx):
        """Toggles logging to the logs channel."""
        key = f"{ctx.guild.id}-logging".encode()
        if self.DB.main.get(key):
            self.DB.main.delete(key)
            state = "Enabled"
        else:
            self.DB.main.put(key, b"1")
            state = "Disabled"

        embed = discord.Embed(color=discord.Color.blurple())
        embed.description = f"```{state} logging```"
        await ctx.send(embed=embed)

    @commands.command(name="removerule")
    async def remove_rule(self, ctx, number: int):
        """Removes a rule from the server rules.

        number: int
            The number of the rule to delete starting from 1.
        """
        key = f"{ctx.guild.id}-rules".encode()
        rules = self.DB.main.get(key)
        embed = discord.Embed(color=discord.Color.blurple())

        if not rules:
            embed.description = "```No rules added yet.```"
            return await ctx.send(embed=embed)

        rules = orjson.loads(rules)

        if 0 < number - 1 < len(rules):
            embed.description = "```No rule found.```"
            return await ctx.send(embed=embed)

        rule = rules.pop(number - 1)
        self.DB.main.put(key, orjson.dumps(rules))
        embed.description = f"```Removed rule {rule}.```"
        await ctx.send(embed=embed)

    @commands.command(name="addrule")
    async def add_rule(self, ctx, *, rule):
        """Adds a rule to the server rules.

        rule: str
            The rule to add.
        """
        key = f"{ctx.guild.id}-rules".encode()
        rules = self.DB.main.get(key)

        if not rules:
            rules = []
        else:
            rules = orjson.loads(rules)

        rules.append(rule)
        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                description=f"```Added rule {len(rules)}\n{rule}```",
            )
        )
        self.DB.main.put(key, orjson.dumps(rules))

    @commands.command(aliases=["disablech"])
    async def disable_channel(self, ctx, channel: discord.TextChannel = None):
        """Disables commands from being used in a channel.

        channel: discord.TextChannel
        """
        channel = channel or ctx.channel
        guild = str(ctx.guild.id)
        key = f"{guild}-disabled_channels".encode()

        disabled = self.DB.main.get(key)

        if not disabled:
            disabled = {}
        else:
            disabled = orjson.loads(disabled)

        if guild not in disabled:
            disabled[guild] = []

        if channel.id in disabled[guild]:
            disabled[guild].remove(channel.id)
            state = "enabled"
        else:
            disabled[guild].append(channel.id)
            state = "disabled"

        embed = discord.Embed(color=discord.Color.blurple())
        embed.description = f"```Commands {state} in {channel}```"

        await ctx.send(embed=embed)
        self.DB.main.put(key, orjson.dumps(disabled))

    @commands.command()
    async def lockall(self, ctx, toggle: bool = True):
        """Removes the send messages permissions from @everyone in every category.

        toggle: bool
            Use False to let @everyone send messages again.
        """
        state = not toggle if toggle else None

        for channel in ctx.guild.text_channels:
            perms = channel.overwrites_for(ctx.guild.default_role)
            key = f"{ctx.guild.id}-{channel.id}-lock".encode()

            if perms.send_messages is False and state is False:
                self.DB.main.put(key, b"1")
            elif perms.send_messages is True and state is False:
                self.DB.main.put(key, b"0")
                perms.send_messages = False
                await channel.set_permissions(ctx.guild.default_role, overwrite=perms)
            elif (data := self.DB.main.get(key)) == b"0":
                perms.send_messages = True
                await channel.set_permissions(ctx.guild.default_role, overwrite=perms)
                self.DB.main.delete(key)
            elif not data:
                perms.send_messages = state
                await channel.set_permissions(ctx.guild.default_role, overwrite=perms)
            else:
                self.DB.main.delete(key)

        embed = discord.Embed(color=discord.Color.blurple())
        if toggle:
            embed.description = "```Set all channels to read only.```"
        else:
            embed.description = "```Reset channel read permissions to default.```"
        await ctx.send(embed=embed)

    @commands.command()
    async def lockall_catagories(self, ctx, toggle: bool = True):
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

        key = f"{ctx.guild.id}-t-{command}".encode()
        state = self.DB.main.get(key)

        if not state:
            self.DB.main.put(key, b"1")
            embed.description = f"```Disabled the {command} command```"
            return await ctx.send(embed=embed)

        self.DB.main.delete(key)
        embed.description = f"```Enabled the {command} command```"
        return await ctx.send(embed=embed)

    @commands.command()
    async def emojis(self, ctx):
        """Shows a list of the current emojis being voted on."""
        emojis = self.DB.main.get(b"emoji_submissions")

        embed = discord.Embed(color=discord.Color.blurple())

        if not emojis:
            embed.description = "```No emojis found```"
            return await ctx.send(embed=embed)

        emojis = orjson.loads(emojis)

        if not emojis:
            embed.description = "```No emojis found```"
            return await ctx.send(embed=embed)

        msg = ""

        for name, users in emojis.items():
            msg += f"{name}: {users}\n"

        embed.description = f"```{msg}```"
        await ctx.send(embed=embed)

    @commands.command(aliases=["demoji", "delemoji"])
    async def delete_emoji(self, ctx, message_id):
        """Deletes an emoji from the emojis being voted on.

        message_id: str
            Id of the message to remove from the db.
        """
        emojis = self.DB.main.get(b"emoji_submissions")

        if not emojis:
            emojis = {}
        else:
            emojis = orjson.loads(emojis)

        try:
            emojis.pop(message_id)
        except KeyError:
            await ctx.send(f"Message {message_id} not found in emojis")

        self.DB.main.put(b"emoji_submissions", orjson.dumps(emojis))

    @commands.command(aliases=["aemoji", "addemoji"])
    async def add_emoji(self, ctx, message_id, name):
        """Adds a emoji to be voted on.

        message_id: int
            Id of the message you are adding the emoji of.
        """
        emojis = self.DB.main.get(b"emoji_submissions")

        if not emojis:
            emojis = {}
        else:
            emojis = orjson.loads(emojis)

        emojis[message_id] = {"name": name, "users": []}

        self.DB.main.put(b"emoji_submissions", orjson.dumps(emojis))

    @commands.command()
    async def edit(self, ctx, message: discord.Message, *, content):
        """Edits the content of a bot message.

        message: discord.Message
            The message you want to edit.
        content: str
            What the content of the message will be changed to.
        """
        await message.edit(content=content)

    @commands.command(name="embededit")
    async def embed_edit(self, ctx, message: discord.Message, *, json):
        """Edits the embed of a bot message.

        example:
        .embed {
            "description": "description",
            "title": "title",
            "fields": [{"name": "name", "value": "value"}]
        }

        You only need either the title or description
        and fields are alaways optional

        json: str
        """
        await message.edit(embed=discord.Embed.from_dict(orjson.loads(json)))

    @commands.command()
    async def embed(self, ctx, *, json):
        """Sends an embed.

        example:
        .embed {
            "description": "description",
            "title": "title",
            "fields": [{"name": "name", "value": "value"}]
        }

        You only need either the title or description
        and fields are alaways optional

        json: str
        """
        await ctx.send(embed=discord.Embed.from_dict(orjson.loads(json)))

    @commands.command()
    async def downvote(self, ctx, member: discord.Member = None, *, duration=None):
        """Automatically downvotes someone.

        member: discord.Member
            The downvoted member.
        duration: str
            How long to downvote the user for e.g 5d 10h 25m 5s
        """
        embed = discord.Embed(color=discord.Color.blurple())

        if not member:
            for member_id in self.DB.blacklist.iterator(include_value=False):
                member_id = member_id.decode().split("-")

                if len(member_id) > 1:
                    guild, member_id = member_id
                    guild = self.bot.get_guild(int(guild))
                else:
                    guild, member_id = "Global", member_id[0]

                embed.add_field(
                    name="User:",
                    value=f"{guild}: {member_id}",
                )
            if not embed.fields:
                embed.title = "No downvoted users"
                return await ctx.send(embed=embed)

            embed.title = "Downvoted users"
            return await ctx.send(embed=embed)

        if member.bot:
            embed.description = "Bots cannot be added to the downvote list"
            return await ctx.send(embed=embed)

        member_id = f"{ctx.guild.id}-{str(member.id)}".encode()

        if self.DB.blacklist.get(member_id):
            self.DB.blacklist.delete(member_id)

            embed.title = "User Undownvoted"
            embed.description = (
                f"***{member}*** has been removed from the downvote list"
            )
            return await ctx.send(embed=embed)

        await member.edit(voice_channel=None)

        if not duration:
            self.DB.blacklist.put(member_id, b"1")
            embed.title = "User Downvoted"
            embed.description = f"**{member}** has been added to the downvote list"
            return await ctx.send(embed=embed)

        seconds = (parse_time(duration) - discord.utils.utcnow()).total_seconds()

        if not seconds:
            embed.description = "```Invalid duration. Example: '3d 5h 10m'```"
            return await ctx.send(embed=embed)

        self.DB.blacklist.put(member_id, b"1")
        self.loop.call_later(seconds, self.DB.blacklist.delete, member_id)

        embed.title = "User Undownvoted"
        embed.description = f"***{member}*** has been added from the downvote list"
        await ctx.send(embed=embed)

    @commands.command()
    async def blacklist(self, ctx, user: discord.User = None):
        """Blacklists someone from using the bot.

        user: discord.User
            The blacklisted user.
        """
        embed = discord.Embed(color=discord.Color.blurple())
        if not user:
            for member_id in self.DB.blacklist.iterator(include_value=False):
                member_id = member_id.decode().split("-")

                if len(member_id) > 1:
                    guild, member_id = member_id
                    guild = self.bot.get_guild(int(guild))
                else:
                    guild, member_id = "Global", member_id[0]

                embed.add_field(
                    name="User:",
                    value=f"{guild}: {member_id}",
                )
            if not embed.fields:
                embed.title = "No blacklisted users"
                return await ctx.send(embed=embed)

            embed.title = "Blacklisted users"
            return await ctx.send(embed=embed)

        user_id = f"{ctx.guild.id}-{str(user.id)}".encode()
        if self.DB.blacklist.get(user_id):
            self.DB.blacklist.delete(user_id)

            embed.title = "User Unblacklisted"
            embed.description = f"***{user}*** has been unblacklisted"
            return await ctx.send(embed=embed)

        self.DB.blacklist.put(user_id, b"2")
        embed.title = "User Blacklisted"
        embed.description = f"**{user}** has been added to the blacklist"

        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    """Starts admin cog."""
    bot.add_cog(admin(bot))
