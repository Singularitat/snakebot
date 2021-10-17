import difflib

from discord import ui
from discord.ext import menus
from discord.ext import commands
import discord


class BotHelpPageSource(menus.ListPageSource):
    def __init__(self, help_command, commands):
        super().__init__(
            entries=sorted(commands.keys(), key=lambda c: c.qualified_name), per_page=6
        )
        self.commands = commands
        self.help_command = help_command

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
            value = f"`{command.name}`"
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

    async def format_page(self, menu, cogs):
        prefix = menu.ctx.prefix
        description = (
            f'Use "{prefix}help command" for more info on a command.\n'
            f'Use "{prefix}help category" for more info on a category.\n'
        )

        embed = discord.Embed(
            title="Categories", description=description, colour=discord.Colour.blurple()
        )

        for cog in cogs:
            commands = self.commands.get(cog)
            if commands:
                value = self.format_commands(cog, commands)
                embed.add_field(name=cog.qualified_name, value=value)

        maximum = self.get_max_pages()
        embed.set_footer(text=f"Page {menu.current_page + 1}/{maximum}")
        return embed


class GroupHelpPageSource(menus.ListPageSource):
    def __init__(self, group, commands, *, prefix):
        super().__init__(entries=commands, per_page=6)
        self.group = group
        self.prefix = prefix
        self.title = f"{self.group.qualified_name} Commands"
        self.description = self.group.description

    async def format_page(self, menu, commands):
        embed = discord.Embed(
            title=self.title,
            description=f"{self.description}",
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

        maximum = self.get_max_pages()
        if maximum > 1:
            embed.set_author(
                name=f"Page {menu.current_page + 1}/{maximum} ({len(self.entries)} commands)"
            )

        embed.set_footer(
            text=f'Use "{self.prefix}help command" for more info on a command.'
        )
        return embed


class HelpMenu(ui.View, menus.MenuPages):
    def __init__(self, source, *, delete_message_after=True):
        super().__init__(timeout=60)
        self._source = source
        self.current_page = 0
        self.ctx = None
        self.message = None
        self.delete_message_after = delete_message_after

    async def start(self, ctx, *, channel=None, wait=False):
        await self._source._prepare_once()
        self.ctx = ctx
        self.message = await self.send_initial_message(ctx, ctx.channel)

    async def _get_kwargs_from_page(self, page):
        """This method calls ListPageSource.format_page class"""
        value = await super()._get_kwargs_from_page(page)
        if "view" not in value:
            value.update({"view": self})
        return value

    async def interaction_check(self, interaction):
        """Only allow the author that invoke the command to be able to use the interaction"""
        return interaction.user == self.ctx.author

    @ui.button(
        emoji="<:before_fast_check:754948796139569224>",
        style=discord.ButtonStyle.blurple,
    )
    async def first_page(self, button, interaction):
        await self.show_page(0)

    @ui.button(
        emoji="<:before_check:754948796487565332>", style=discord.ButtonStyle.blurple
    )
    async def before_page(self, button, interaction):
        await self.show_checked_page(self.current_page - 1)

    @ui.button(
        emoji="<:stop_check:754948796365930517>", style=discord.ButtonStyle.blurple
    )
    async def stop_page(self, button, interaction):
        self.stop()
        if self.delete_message_after:
            await self.message.delete(delay=0)

    @ui.button(
        emoji="<:next_check:754948796361736213>", style=discord.ButtonStyle.blurple
    )
    async def next_page(self, button, interaction):
        await self.show_checked_page(self.current_page + 1)

    @ui.button(
        emoji="<:next_fast_check:754948796391227442>", style=discord.ButtonStyle.blurple
    )
    async def last_page(self, button, interaction):
        await self.show_page(self._source.get_max_pages() - 1)


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
        bot = self.context.bot
        entries = await self.filter_commands(bot.commands, sort=True)

        all_commands = {}
        for command in entries:
            if not command.cog:
                continue

            if command.cog in all_commands:
                all_commands[command.cog].append(command)
            else:
                all_commands[command.cog] = [command]

        menu = HelpMenu(BotHelpPageSource(self, all_commands))
        await menu.start(self.context)

    async def send_cog_help(self, cog):
        entries = await self.filter_commands(cog.get_commands(), sort=True)
        menu = HelpMenu(GroupHelpPageSource(cog, entries, prefix=self.context.prefix))
        await menu.start(self.context)

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

        source = GroupHelpPageSource(group, entries, prefix=self.context.prefix)
        self.common_command_formatting(source, group)
        menu = HelpMenu(source)
        await menu.start(self.context)


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
