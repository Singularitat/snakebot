import difflib

import discord
from discord.ext import commands, pages


class PaginatedHelpCommand(commands.HelpCommand):
    def __init__(self):
        super().__init__(
            command_attrs={
                "cooldown": commands.CooldownMapping(
                    commands.Cooldown(1, 5.0), commands.BucketType.member
                ),
                "help": "Shows help about the bot, a command, or a category",
                "hidden": True,
            }
        )

    @staticmethod
    def format_commands(cog, commands):
        if cog.description:
            short_doc = cog.description.split("\n", 1)[0] + "\n"
        else:
            short_doc = "No help found...\n"

        current_count = len(short_doc)
        ending_note = "+%d not shown"
        ending_length = len(ending_note)

        page = []
        for command in commands:
            parent = getattr(command, "parent", None)
            value = f"`{parent.name + ' ' if parent else ''}{command.name}`"
            count = len(value) + 1  # The space
            if count + current_count < 800:
                current_count += count
                page.append(value)
            else:
                if current_count + ending_length + 1 > 800:
                    page.pop()

                break

        if len(page) == len(commands):
            return short_doc + " ".join(page)

        hidden = len(commands) - len(page)
        return short_doc + " ".join(page) + "\n" + (ending_note % hidden)

    async def format_cogs(self, cogs):
        prefix = self.context.prefix
        description = (
            f'Use "{prefix}help command" for more info on a command.\n'
            f'Use "{prefix}help category" for more info on a category.\n'
        )

        embed = discord.Embed(
            title="Categories", description=description, colour=discord.Colour.blurple()
        )

        for i, (cog, items) in enumerate(cogs):
            value = self.format_commands(cog, items)
            embed.add_field(name=cog.qualified_name, value=value)

            if not i % 2:
                embed.add_field(name="\u200b", value="\u200b")
        return embed

    def format_group(self, title, description, commands):
        embed = discord.Embed(
            title=title,
            description=description,
            colour=discord.Colour.blurple(),
        )

        for command in commands:
            signature = f"{command.qualified_name} {command.signature}"
            embed.add_field(
                name=signature,
                value=f"```{command.short_doc}```"
                if command.short_doc
                else "```No help given...```",
                inline=False,
            )

        embed.set_footer(
            text=f'Use "{self.context.prefix}help command" for more info on a command.'
        )
        return embed

    def command_not_found(self, command):
        all_commands = [
            str(command)
            for command in self.context.bot.walk_commands()
            if not command.hidden
        ]
        matches = difflib.get_close_matches(command, all_commands, cutoff=0)

        return discord.Embed(
            color=discord.Color.dark_red(),
            title=f"Command {command} not found.",
            description="```Did you mean:\n\n{}```".format("\n".join(matches)),
        )

    async def send_error_message(self, error):
        if isinstance(error, discord.Embed):
            await self.context.channel.send(embed=error)
        else:
            await self.context.channel.send(error)

    @staticmethod
    def get_command_signature(command):
        parent = command.full_parent_name
        if len(command.aliases) > 0:
            aliases = "|".join(command.aliases)
            fmt = f"[{command.name}|{aliases}]"
            if parent:
                fmt = f"{parent} {fmt}"
            alias = fmt
        else:
            alias = command.name if not parent else f"{parent} {command.name}"
        return f"{alias} {command.signature}"

    async def send_bot_help(self, mapping):
        embeds = []
        cogs = []
        count = 1
        for cog in self.context.bot.cogs.values():
            commands = await self.filter_commands(cog.get_commands(), sort=True)
            if not commands:
                continue
            cogs.append((cog, commands))

            if count == 4:
                embeds.append(await self.format_cogs(cogs))
                cogs.clear()
                count = 1
            else:
                count += 1

        if cogs:
            embeds.append(await self.format_cogs(cogs))

        paginator = pages.Paginator(pages=embeds)
        await paginator.send(self.context)

    async def send_cog_help(self, cog):
        entries = await self.filter_commands(cog.get_commands(), sort=True)
        count = 1
        commands = []
        embeds = []

        title = f"{cog.qualified_name} Commands"
        for command in entries:
            commands.append(command)
            if count == 6:
                embeds.append(self.format_group(title, cog.description, commands))
                commands.clear()
                count = 1
            else:
                count += 1
        if commands:
            embeds.append(self.format_group(title, cog.description, commands))

        paginator = pages.Paginator(pages=embeds)
        await paginator.send(self.context)

    def common_command_formatting(self, embed_like, command):
        embed_like.title = f"{self.context.prefix}{self.get_command_signature(command)}"
        if command.description:
            embed_like.description = f"```{command.description}\n\n{command.help}```"
        else:
            embed_like.description = (
                f"```{command.help}```" if command.help else "```No help found...```"
            )

    async def send_command_help(self, command):
        embed = discord.Embed(colour=discord.Colour.blurple())
        self.common_command_formatting(embed, command)
        await self.context.send(embed=embed)

    async def send_group_help(self, group):
        subcommands = group.commands
        if len(subcommands) == 0:
            return await self.send_command_help(group)

        entries = await self.filter_commands(subcommands, sort=True)
        if len(entries) == 0:
            return await self.send_command_help(group)

        count = 1
        commands = []
        embeds = []
        title = f"{group.qualified_name} Commands"
        for command in entries:
            commands.append(command)
            if count == 6:
                embeds.append(self.format_group(title, group.description, commands))
                commands.clear()
                count = 1
            else:
                count += 1

        if commands:
            embeds.append(self.format_group(title, group.description, commands))

        paginator = pages.Paginator(pages=embeds)
        await paginator.send(self.context)


class _help(commands.Cog, name="help"):
    """For the help command."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.old_help_command = bot.help_command
        bot.help_command = PaginatedHelpCommand()
        bot.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = self.old_help_command


def setup(bot: commands.Bot) -> None:
    """Starts help cog."""
    bot.add_cog(_help(bot))
