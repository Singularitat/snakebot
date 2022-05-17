from __future__ import annotations

import asyncio
import time

import discord
import orjson
from discord.ext import commands, pages

from cogs.utils.time import parse_time


class moderation(commands.Cog):
    """For commands related to moderation."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.DB = bot.DB
        self.loop = bot.loop
        self.handles = {}

    @commands.command()
    async def invites(self, ctx, member: discord.User = None):
        """Shows the invites that users joined from.

        member: discord.Member
            Used to check the invite that a specific member used.
        """
        if member:
            invite_code = self.DB.invites.get(f"{member.id}-{ctx.guild.id}".encode())

            if not invite_code:
                return await ctx.send(
                    embed=discord.Embed(
                        color=discord.Color.dark_red(),
                        title="Failed to get the invite of that member",
                    )
                )

            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    title=f"{member} joined from the invite `{invite_code.decode()}`",
                )
            )

        invite_list = []
        invites = ""
        count = 0

        for member, invite in self.DB.invites:
            if invite.isdigit():
                continue

            member = self.bot.get_user(int(member.split(b"-")[0]))

            # I don't fetch the invite cause it takes 300ms per invite
            if member:
                invites += f"{member.display_name}: {invite.decode()}\n"
                count += 1

                if count == 20:
                    invite_list.append(f"```ahk\n{invites}```")
                    invites = ""

        if not invite_list:
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description="```No stored invites```",
                )
            )

        paginator = pages.Paginator(pages=invite_list)
        await paginator.send(ctx)

    @commands.command(hidden=True)
    @commands.guild_only()
    async def inactive(self, ctx, days: int = 7):
        """Gets how many people can be pruned.

        days: int
        """
        inactive = await ctx.guild.estimate_pruned_members(days=days)
        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                description=f"```{inactive} members inactive for {days} days```",
            )
        )

    async def _end_poll(self, guild, message):
        """Ends a poll and sends the results."""
        polls = self.DB.main.get(b"polls")

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
        self.DB.main.put(b"polls", orjson.dumps(polls))

    @commands.command()
    @commands.has_permissions(kick_members=True)
    @commands.guild_only()
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

        polls = self.DB.main.get(b"polls")

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
        message_id = str(message.id)

        polls[guild][message_id] = polls[guild].pop("temp")

        for i in range(len(options)):
            await message.add_reaction(chr(127462 + i))

        self.DB.main.put(b"polls", orjson.dumps(polls))
        handle = self.loop.call_later(
            21600, asyncio.create_task, self._end_poll(guild, message)
        )
        self.handles[message_id] = handle

    @commands.command()
    @commands.has_permissions(kick_members=True)
    @commands.guild_only()
    async def endpoll(self, ctx, message_id):
        """Ends a poll based off its message id."""
        polls = self.DB.main.get(b"polls")

        if not polls:
            return

        polls = orjson.loads(polls)

        if str(ctx.guild.id) not in polls:
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(), description="No polls found"
                )
            )

        if message_id not in polls[str(ctx.guild.id)]:
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(), description="Poll not found"
                )
            )

        winner = max(
            polls[str(ctx.guild.id)][message_id],
            key=lambda x: polls[str(ctx.guild.id)][message_id][x]["count"],
        )

        await ctx.reply(f"Winner of the poll was {winner}")

        polls[str(ctx.guild.id)].pop(message_id)
        self.DB.main.put(b"polls", orjson.dumps(polls))

        self.handles[message_id].cancel()
        self.handles.pop(message_id)

    @commands.command()
    @commands.has_permissions(manage_nicknames=True)
    @commands.guild_only()
    async def nick(self, ctx, member: discord.Member, *, nickname):
        """Changes a members nickname.

        member: discord.Member
        nickname: str
        """
        await member.edit(nick=nickname)
        await ctx.send(f"Changed {member.display_name}'s nickname to {nickname}'")

    @commands.command(name="warn")
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def warn_member(self, ctx, member: discord.Member, *, reason=None):
        """Warns a member and keeps track of how many warnings a member has.

        member: discord.member
        reason: str
        """
        member_id = f"{ctx.guild.id}-{member.id}".encode()
        infractions = self.DB.infractions.get(member_id)

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

        self.DB.infractions.put(member_id, orjson.dumps(infractions))

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def warnings(self, ctx, member: discord.Member):
        """Shows the warnings a member has.

        member: discord.members
        """
        member_id = f"{ctx.guild.id}-{member.id}".encode()
        infractions = self.DB.infractions.get(member_id)
        embed = discord.Embed(color=discord.Color.blurple())

        if not infractions:
            embed.description = "```Member has no infractions```"
            return await ctx.send(embed=embed)

        infractions = orjson.loads(infractions)
        embed.description = "```{} Has {} warnings\n\n{}```".format(
            member.display_name,
            len(infractions["warnings"]),
            "\n".join([warning or "N/A" for warning in infractions["warnings"]]),
        )
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def infractions(self, ctx, member: discord.Member):
        """Shows all infractions of a member.

        member: discord.Member
        """
        member_id = f"{ctx.guild.id}-{member.id}".encode()
        inf = self.DB.infractions.get(member_id)

        embed = discord.Embed(color=discord.Color.blurple())

        if not inf:
            embed.description = "No infractions found for member"
            return await ctx.send(embed=embed)

        inf = orjson.loads(inf)

        def _format(infractions):
            length = len(infractions)

            message = f"{length}\n"
            for i, infraction in enumerate(infractions, start=1):
                message += "{}: {}\n".format(i, infraction or "No Reason Given")

            return message

        embed.description = "Warnings: {}\nMutes: {}\nKicks: {}\nBans: {}".format(
            _format(inf["warnings"]),
            _format(inf["mutes"]),
            _format(inf["kicks"]),
            _format(inf["bans"]),
        )

        await ctx.send(embed=embed)

    @commands.command(aliases=["mute"])
    @commands.has_permissions(moderate_members=True)
    @commands.guild_only()
    async def timeout(self, ctx, member: discord.Member, *, duration="1d", reason=None):
        """Times out a member.

        Usage:
        .timeout @Singularity#8953 "1d 12h" He was rude

        member: discord.member
        reason: str
        """
        member_id = f"{ctx.guild.id}-{member.id}".encode()
        infractions = self.DB.infractions.get(member_id)

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

        await member.timeout(until=parse_time(duration), reason=reason)

        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.dark_red(),
                description="{} has been timed out. They have {} total infractions.".format(
                    member.mention, infractions["count"]
                ),
            )
        )

        self.DB.infractions.put(member_id, orjson.dumps(infractions))

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    @commands.guild_only()
    async def ban_member(
        self, ctx, member: discord.Member | discord.User, *, reason=None
    ):
        """Bans a member.

        Usage:
        .ban @Singularity#8953 He was rude

        member: discord.Member
            The member to ban.
        reason: str
            The reason for banning the member.
        """
        embed = discord.Embed(color=discord.Color.dark_red())
        if (
            isinstance(member, discord.Member)
            and ctx.author.top_role <= member.top_role
            and ctx.guild.owner != ctx.author
        ):
            embed.description = (
                "```You can't ban someone higher or equal in roles to you```"
            )
            return await ctx.send(embed=embed)

        await ctx.guild.ban(member, delete_message_days=0, reason=reason)

        member_id = f"{ctx.guild.id}-{member.id}".encode()
        infractions = self.DB.infractions.get(member_id)

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

        embed.title = f"Banned {member.display_name}"
        embed.description = f"```They had {infractions['count']} total infractions.```"
        self.DB.infractions.put(member_id, orjson.dumps(infractions))

        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    @commands.guild_only()
    async def unban(self, ctx, user: discord.User):
        """Unbans a member based off their id.

        user: discord.User
        """
        embed = discord.Embed(color=discord.Color.blurple())

        async for entry in ctx.guild.bans():
            if user == entry.user:
                await ctx.guild.unban(entry.user)

                embed.title = f"Unbanned {user}"
                return await ctx.send(embed=embed)

        embed.title = "Couldn't find user"
        await ctx.send(embed=embed)

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    @commands.guild_only()
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
        infractions = self.DB.infractions.get(member_id)

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
        self.DB.infractions.put(member_id, orjson.dumps(infractions))

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
                await ctx.channel.purge(limit=min(int(ctx.subcommand_passed) + 1, 101))
            except ValueError:
                embed = discord.Embed(
                    color=discord.Color.blurple(),
                    description=f"```Usage: {ctx.prefix}purge [amount]```",
                )
                await ctx.send(embed=embed)

    @purge.command()
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def till(self, ctx, message_id: int = None):
        """Clear messages in a channel until the given message_id. Given ID is not deleted."""
        if message_id:
            try:
                message = await ctx.fetch_message(message_id)
            except discord.errors.NotFound:
                return await ctx.send(
                    embed=discord.Embed(
                        color=discord.Color.blurple(),
                        description="```Message could not be found in this channel```",
                    )
                )
        elif ctx.message.reference and ctx.message.reference.resolved:
            message = ctx.message.reference.resolved
        else:
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description="```Either supply a message id or reply to message```",
                )
            )

        await ctx.channel.purge(after=message)

    @purge.command()
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def user(self, ctx, user: discord.User, num_messages: int = 100):
        """Clear all messages of <User> withing the last [n=100] messages.

        user: discord.User
            The user to purge the messages of.
        num_messages: int
            The number of messages to check.
        """

        def check(msg):
            return msg.author == user

        await ctx.channel.purge(limit=max(num_messages, 100), check=check, before=None)

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

    @staticmethod
    async def single_delete(messages):
        for m in messages:
            await m.delete()

    @purge.command(name="from")
    @commands.has_permissions(manage_channels=True)
    @commands.guild_only()
    async def _from(self, ctx, start: int, end: int):
        """Purges from [start] to [end] message without deleting said messages.

        start: int
        end: int
        """
        if start < end:
            start, end = end, start
        try:
            start = await ctx.fetch_message(start)
            end = await ctx.fetch_message(end)
        except discord.errors.NotFound:
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description="```One of the messages could not be found in this channel```",
                )
            )

        messages = []
        count = 0

        minimum_time = (
            int((time.time() - 14 * 24 * 60 * 60) * 1000.0 - 1420070400000) << 22
        )
        strategy = ctx.channel.delete_messages
        iterator = ctx.channel.history(limit=100, before=start, after=end)
        await iterator.messages.put(ctx.message)

        async for message in iterator:
            if count == 100:
                to_delete = messages[-100:]
                await strategy(to_delete)
                count = 0
                await asyncio.sleep(1)

            if message.id < minimum_time:
                if count == 1:
                    await messages[-1].delete()
                elif count >= 2:
                    to_delete = messages[-count:]
                    await strategy(to_delete)

                count = 0
                strategy = self.single_delete

            count += 1
            messages.append(message)

        await strategy(messages[-count:])

    @commands.group(invoke_without_command=True)
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def history(self, ctx):
        """Shows the edited message or deleted message history of a member."""
        embed = discord.Embed(
            color=discord.Color.blurple(),
            description=f"```Usage: {ctx.prefix}history [deleted/edited]```",
        )
        await ctx.send(embed=embed)

    @history.command(aliases=["d"])
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def deleted(self, ctx, member: discord.User = None):
        """Shows a members most recent deleted message history.

        member: discord.User
            The user to get the history of.
        amount: int
            The amount of messages to get.
        """
        member = member or ctx.author

        member_id = f"{ctx.guild.id}-{member.id}".encode()
        deleted = self.DB.deleted.get(member_id)
        embed = discord.Embed(color=discord.Color.blurple())

        if not deleted:
            embed.description = "```No deleted messages found```"
            return await ctx.send(embed=embed)

        deleted = orjson.loads(deleted)

        embeds = []
        count = 0

        for date, message in reversed(deleted.items()):
            message = message.replace("`", "`\u200B")
            if message:
                embed.add_field(name=f"<t:{date}:R>", value=message)
                count += 1

                if count == 10:
                    embeds.append(embed)
                    embed = discord.Embed(color=discord.Color.blurple())
                    count = 0

        if count != 10:
            embeds.append(embed)

        paginator = pages.Paginator(pages=embeds)
        await paginator.send(ctx)

    @history.command(aliases=["e"])
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def edited(self, ctx, member: discord.User = None):
        """Shows a users most recent edit message history.

        member: discord.User
            The user to get the edit history of.
        amount: int
            The amount of messages to get.
        """
        member = member or ctx.author

        member_id = f"{ctx.guild.id}-{member.id}".encode()
        edited = self.DB.edited.get(member_id)
        embed = discord.Embed(color=discord.Color.blurple())

        if not edited:
            embed.description = "```No edited messages found```"
            return await ctx.send(embed=embed)

        edited = orjson.loads(edited)
        embeds = []
        count = 0

        for index, (date, (before, after)) in enumerate(reversed(edited.items())):
            before = before.replace("`", "`\u200b")
            after = after.replace("`", "`\u200b")

            embed.add_field(name=f"<t:{date}:R>", value=f"{before} >>> {after}")
            count += 1

            if count == 10:
                embeds.append(embed)
                embed = discord.Embed(color=discord.Color.blurple())
                count = 0

        if count != 10:
            embeds.append(embed)

        paginator = pages.Paginator(pages=embeds)
        await paginator.send(ctx)


def setup(bot: commands.Bot) -> None:
    """Starts moderation cog."""
    bot.add_cog(moderation(bot))
