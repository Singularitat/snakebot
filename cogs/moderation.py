from discord.ext import commands, menus
import discord
import asyncio
import cogs.utils.database as DB
import orjson


class HistoryMenu(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=10)

    async def format_page(self, menu, entries):
        embed = discord.Embed(color=discord.Color.blurple())
        for date, message in entries:
            if not message:
                continue
            embed.add_field(name=f"<t:{date}:R>", value=message)
        return embed


class moderation(commands.Cog):
    """For commands related to moderation."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.loop = asyncio.get_event_loop()

    @staticmethod
    async def _end_poll(guild, message):
        """Ends a poll and sends the results."""
        polls = DB.db.get(b"polls")

        if not polls:
            return

        message_id = str(message.id)
        polls = orjson.loads(polls)

        if guild not in polls:
            return

        if message_id not in polls[guild]:
            return

        winner = max(
            polls[guild][message_id], key=lambda x: polls[guild][message_id][x]["count"]
        )

        await message.reply(f"Winner of the poll was {winner}")

        polls[guild].pop(message_id)
        DB.db.put(b"polls", orjson.dumps(polls))

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def poll(self, ctx, title, *options):
        """Starts a poll.

        title: str
        options: tuple
        """
        embed = discord.Embed(color=discord.Color.blurple())

        if len(options) > 20:
            embed.description = "```You can have a maximum of 20 options```"
            return await ctx.send(embed=embed)

        if len(options) < 2:
            embed.description = "```You need at least 2 options```"
            return await ctx.send(embed=embed)

        polls = DB.db.get(b"polls")

        if not polls:
            polls = {}
        else:
            polls = orjson.loads(polls)

        guild = str(ctx.guild.id)

        if guild not in polls:
            polls[guild] = {}

        polls[guild]["temp"] = {}
        embed.description = ""

        for number, option in enumerate(options):
            emoji = chr(127462 + number)
            polls[guild]["temp"][emoji] = {
                "name": option,
                "count": 0,
            }
            embed.description += f"{emoji}: {option}\n"

        embed.title = title
        message = await ctx.send(embed=embed)

        polls[guild][str(message.id)] = polls[guild].pop("temp")

        for i in range(len(options)):
            await message.add_reaction(chr(127462 + i))

        DB.db.put(b"polls", orjson.dumps(polls))
        self.loop.call_later(21600, asyncio.create_task, self.end_poll(guild, message))

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def end_poll(self, ctx, message_id):
        """Ends a poll based off its message id."""
        polls = DB.db.get(b"polls")

        if not polls:
            return

        polls = orjson.loads(polls)

        if str(ctx.guild.id) not in polls:
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Colo.blurple(), description="No polls found"
                )
            )

        if message_id not in polls[str(ctx.guild.id)]:
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Colo.blurple(), description="Poll not found"
                )
            )

        winner = max(
            polls[str(ctx.guild.id)][message_id],
            key=lambda x: polls[str(ctx.guild.id)][message_id][x]["count"],
        )

        await ctx.reply(f"Winner of the poll was {winner}")

        polls[str(ctx.guild.id)].pop(message_id)
        DB.db.put(b"polls", orjson.dumps(polls))

    @commands.command(name="mute")
    @commands.has_permissions(kick_members=True)
    async def mute_member(self, ctx, member: discord.Member, *, reason=None):
        """Mutes a member.

        member: discord.member
        reason: str
        """
        role = discord.utils.get(ctx.guild.roles, name="Muted")
        embed = discord.Embed(color=discord.Color.blurple())

        if role in member.roles:
            await member.remove_roles(role)
            embed.description = f"```Unmuted {member.display_name}```"
            return await ctx.send(embed=embed)

        member_id = f"{ctx.guild.id}-{member.id}".encode()
        infractions = DB.infractions.get(member_id)

        if not infractions:
            infractions = {
                "count": 0,
                "bans": [],
                "kicks": [],
                "mutes": [],
                "warnings": [],
            }
        else:
            infractions = orjson.loads(infractions)

        infractions["count"] += 1
        infractions["mutes"].append(reason)

        if not role:
            reactions = ["✅", "❎"]

            def check(reaction: discord.Reaction, user: discord.User) -> bool:
                return (
                    user.id == ctx.author.id
                    and reaction.message.channel == ctx.channel
                    and reaction.emoji in reactions
                )

            embed.description = "```No muted role found react to add Muted role.```"

            message = await ctx.send(embed=embed)

            for reaction in reactions:
                await message.add_reaction(reaction)

            reaction, user = await ctx.bot.wait_for(
                "reaction_add", timeout=60.0, check=check
            )

            if reaction.emoji == "✅":
                role = await ctx.guild.create_role(
                    name="Muted", color=discord.Color.dark_red()
                )
                for categories in ctx.guild.categories:
                    await categories.set_permissions(
                        role, send_messages=False, connect=False
                    )
            else:
                return

        await member.add_roles(role)

        embed = discord.Embed(
            color=discord.Color.dark_red(),
            description="{} has been muted. They have {} total infractions.".format(
                member.mention, infractions["count"]
            ),
        )
        await ctx.send(embed=embed)

        DB.infractions.put(member_id, orjson.dumps(infractions))

    @commands.command()
    @commands.has_permissions(manage_nicknames=True)
    async def nick(self, ctx, member: discord.Member, *, nickname):
        """Changes a members nickname.

        member: discord.Member
        nickname: str
        """
        await member.edit(nick=nickname)
        await ctx.send(f"Changed {member.display_name}'s nickname to {nickname}'")

    @commands.command(name="warn")
    @commands.has_permissions(manage_messages=True)
    async def warn_member(self, ctx, member: discord.Member, *, reason=None):
        """Warns a member and keeps track of how many warnings a member has.

        member: discord.member
        reason: str
        """
        member_id = f"{ctx.guild.id}-{member.id}".encode()
        infractions = DB.infractions.get(member_id)

        if not infractions:
            infractions = {
                "count": 0,
                "bans": [],
                "kicks": [],
                "mutes": [],
                "warnings": [],
            }
        else:
            infractions = orjson.loads(infractions)

        infractions["count"] += 1
        infractions["warnings"].append(reason)

        embed = discord.Embed(
            color=discord.Color.dark_red(),
            description="{} has been warned. They have {} total infractions.".format(
                member.mention, infractions["count"]
            ),
        )
        await ctx.send(embed=embed)

        DB.infractions.put(member_id, orjson.dumps(infractions))

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def warnings(self, ctx, member: discord.Member):
        """Shows the warnings a member has.

        member: discord.members
        """
        member_id = f"{ctx.guild.id}-{member.id}".encode()
        infractions = DB.infractions.get(member_id)
        embed = discord.Embed(color=discord.Color.blurple())

        if not infractions:
            embed.description = "```Member has no infractions```"
            return await ctx.send(embed=embed)

        infractions = orjson.loads(infractions)
        embed.description = "```{} Has {} warnings\n\n{}```".format(
            member.display_name,
            len(infractions["warnings"]),
            "\n".join(infractions["warnings"]),
        )
        await ctx.send(embed=embed)

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

    async def ban(self, ctx, member: discord.Member, duration=None, *, reason=None):
        """Bans a member.

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

        if duration:
            seconds = await self.end_date(duration)

            if not seconds:
                embed.description = "```Invalid duration. Example: '3d 5h 10m'```"
                return await ctx.send(embed=embed)

            self.loop.call_later(seconds, asyncio.create_task, ctx.guild.unban(member))
            embed.title = f"Banned {member.display_name} for {seconds}s"
        else:
            embed.title = f"Banned {member.display_name}"

        await member.ban(reason=reason)

        member_id = f"{ctx.guild.id}-{member.id}".encode()
        infractions = DB.infractions.get(member_id)

        if not infractions:
            infractions = {
                "count": 0,
                "bans": [],
                "kicks": [],
                "mutes": [],
                "warnings": [],
            }
        else:
            infractions = orjson.loads(infractions)

        infractions["count"] += 1
        infractions["bans"].append(reason)

        embed.description = f"```They had {infractions['count']} total infractions.```"
        DB.infractions.put(member_id, orjson.dumps(infractions))

        await ctx.send(embed=embed)

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban_member(self, ctx, member: discord.Member, *, reason=None):
        """Bans a member.

        Usage:
        .ban @Singularity#8953 He was rude

        member: discord.Member
            The member to ban.
        reason: str
            The reason for banning the member.
        """
        await self.ban(ctx=ctx, member=member, reason=reason)

    @commands.command(name="tempban")
    @commands.has_permissions(ban_members=True)
    async def temp_ban_member(
        self, ctx, member: discord.Member, duration=None, *, reason=None
    ):
        """Temporarily bans a member.

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
        await self.ban(ctx=ctx, member=member, duration=duration, reason=reason)

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick_member(self, ctx, member: discord.Member, *, reason=None):
        """Kicks a member.

        member: discord.Member
            The member to kick can be an id, @ or name.
        reason: str
        """
        if ctx.author.top_role <= member.top_role and ctx.guild.owner != ctx.author:
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description="```You can't kick someone higher or equal to you```",
                )
            )

        await member.kick()

        member_id = f"{ctx.guild.id}-{member.id}".encode()
        infractions = DB.infractions.get(member_id)

        if not infractions:
            infractions = {
                "count": 0,
                "bans": [],
                "kicks": [],
                "mutes": [],
                "warnings": [],
            }
        else:
            infractions = orjson.loads(infractions)

        infractions["count"] += 1
        infractions["kicks"].append(reason)

        embed = discord.Embed(
            color=discord.Color.dark_red(),
            title=f"{member.display_name} has been kicked",
            description=f"```They had {infractions['count']} total infractions.```",
        )
        await ctx.send(embed=embed)
        DB.infractions.put(member_id, orjson.dumps(infractions))

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def role(self, ctx, role: discord.Role, member: discord.Member = None):
        """Gives member a role.

        member: discord.Member
            The member to give the role.
        role: str
            The name of the role.
        """
        embed = discord.Embed(color=discord.Color.blurple())
        member = member or ctx.author

        if (
            ctx.author != member
            and ctx.author.top_role <= member.top_role
            and ctx.guild.owner != ctx.author
        ):
            embed.title = "```You can't change the roles of someone higher than you.```"
            return await ctx.send(embed=embed)

        if (
            ctx.author == member
            and ctx.author.top_role <= role
            and ctx.guild.owner != ctx.author
        ):
            embed.title = (
                "```You can't give yourself a role higher than your highest role.```"
            )
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
        if not ctx.invoked_subcommand:
            try:
                await ctx.channel.purge(limit=int(ctx.subcommand_passed) + 1)
            except ValueError:
                embed = discord.Embed(
                    color=discord.Color.blurple(),
                    description=f"```Usage: {ctx.prefix}purge [amount]```",
                )
                await ctx.send(embed=embed)

    @purge.command()
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def till(self, ctx, message_id: int):
        """Clear messages in a channel until the given message_id. Given ID is not deleted."""
        try:
            message = await ctx.fetch_message(message_id)
        except discord.errors.NotFound:
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description="```Message could not be found in this channel```",
                )
            )

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
        """Purges a channel by cloning and then deleting it.

        channel: discord.TextChannel
        """
        channel = channel or ctx.channel
        await channel.clone()
        await channel.delete()

    @commands.group()
    @commands.has_permissions(manage_messages=True)
    async def history(self, ctx):
        """Shows the edited message or deleted message history of a member."""
        if not ctx.invoked_subcommand:
            embed = discord.Embed(
                color=discord.Color.blurple(),
                description=f"```Usage: {ctx.prefix}history [deleted/edited]```",
            )
            await ctx.send(embed=embed)

    @history.command(aliases=["d"])
    @commands.has_permissions(manage_messages=True)
    async def deleted(self, ctx, member: discord.Member = None):
        """Shows a members most recent deleted message history.

        member: discord.Member
            The user to get the history of.
        amount: int
            The amount of messages to get.
        """
        member = member or ctx.author

        member_id = f"{ctx.guild.id}-{member.id}".encode()
        deleted = DB.deleted.get(member_id)
        embed = discord.Embed(color=discord.Color.blurple())

        if not deleted:
            embed.description = "```No deleted messages found```"
            return await ctx.send(embed=embed)

        deleted = orjson.loads(deleted)
        messages = []

        for index, date in enumerate(reversed(deleted)):
            messages.append((date, deleted[date].replace("`", "`​")))

        pages = menus.MenuPages(
            source=HistoryMenu(messages),
            clear_reactions_after=True,
            delete_message_after=True,
        )
        await pages.start(ctx)

    @history.command(aliases=["e"])
    @commands.has_permissions(manage_messages=True)
    async def edited(self, ctx, member: discord.Member = None, amount: int = 10):
        """Shows a users most recent edit message history.

        member: discord.Member
            The user to get the edit history of.
        amount: int
            The amount of messages to get.
        """
        member = member or ctx.author

        member_id = f"{ctx.guild.id}-{member.id}".encode()
        edited = DB.edited.get(member_id)
        embed = discord.Embed(color=discord.Color.blurple())

        if not edited:
            embed.description = "```No edited messages found```"
            return await ctx.send(embed=embed)

        edited = orjson.loads(edited)
        messages = []

        for index, date in enumerate(reversed(edited)):
            if index == amount:
                break

            before = edited[date][0].replace("`", "`\u200b")
            after = edited[date][1].replace("`", "`\u200b")

            messages.append((date, f"{before} >>> {after}"))

        pages = menus.MenuPages(
            source=HistoryMenu(messages),
            clear_reactions_after=True,
            delete_message_after=True,
        )
        await pages.start(ctx)


def setup(bot: commands.Bot) -> None:
    """Starts moderation cog."""
    bot.add_cog(moderation(bot))
