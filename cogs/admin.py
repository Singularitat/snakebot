from discord.ext import commands
import discord
import orjson


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
            tenary = "Enabled"
        else:
            self.DB.main.put(key, b"1")
            tenary = "Disabled"

        embed = discord.Embed(color=discord.Color.blurple())
        embed.description = f"```{tenary} logging```"
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
            tenary = "enabled"
        else:
            disabled[guild].append(channel.id)
            tenary = "disabled"

        embed = discord.Embed(color=discord.Color.blurple())
        embed.description = f"```Commands {tenary} in {channel}```"

        await ctx.send(embed=embed)
        self.DB.main.put(key, orjson.dumps(disabled))

    @commands.command()
    @commands.cooldown(1, 86400, commands.BucketType.user)
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
        rrole = {"guild": ctx.guild.id}

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

        self.DB.rrole.put(str(message.id).encode(), orjson.dumps(rrole))
        for name in roles:
            await message.add_reaction(roles[name][1])

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

        key = f"{ctx.guild.id}-{command}".encode()
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

    @commands.command(aliases=["demoji"])
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

    @commands.command(aliases=["aemoji"])
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

    async def end_date(self, duration):
        """Converts a duration to an end date.

        duration: str
            How much to add onto the current date e.g 5d 10h 25m 5s
        """
        seconds = 0
        times = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        try:
            for time in duration.split():
                seconds += int(time[:-1]) * times[time[-1]]
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

        if not member:
            if list(self.DB.blacklist) == []:
                embed.title = "No downvoted users"
                return await ctx.send(embed=embed)

            embed.title = "Downvoted users"
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

        seconds = await self.end_date(duration)

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
            if list(self.DB.blacklist) == []:
                embed.title = "No blacklisted users"
                return await ctx.send(embed=embed)

            embed.title = "Blacklisted users"
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
