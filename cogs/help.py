import discord
from discord.ext import commands, menus
import asyncio
import difflib


# Taken From https://github.com/Rapptz/RoboDanny


class RoboPages(menus.MenuPages):
    def __init__(self, source):
        super().__init__(source=source, check_embeds=True)

    async def finalize(self, timed_out):
        try:
            if timed_out:
                await self.message.clear_reactions()
            else:
                await self.message.delete()
        except discord.HTTPException:
            pass


class BotHelpPageSource(menus.ListPageSource):
    def __init__(self, help_command, commands):
        super().__init__(
            entries=sorted(commands.keys(), key=lambda c: c.qualified_name), per_page=6
        )
        self.commands = commands
        self.help_command = help_command
        self.prefix = help_command.clean_prefix

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
            description=self.description,
            colour=discord.Colour.blurple(),
        )

        for command in commands:
            signature = f"{command.qualified_name} {command.signature}"
            embed.add_field(
                name=signature,
                value=command.short_doc or "No help given...",
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


class HelpMenu(RoboPages):
    def __init__(self, source):
        super().__init__(source)

    @menus.button("\N{WHITE QUESTION MARK ORNAMENT}", position=menus.Last(5))
    async def show_bot_help(self, payload):
        """Shows how to use the bot."""
        embed = discord.Embed(colour=discord.Colour.blurple())
        embed.title = "How Interpret The Help Pages"

        entries = (
            ("<argument>", "This means the argument is __**required**__."),
            ("[argument]", "This means the argument is __**optional**__."),
            ("[A|B]", "This means that it can be __**either A or B**__."),
            (
                "[argument...]",
                "This means you can have multiple arguments.\n"
                "Now that you know the basics, it should be noted that...\n"
                "__**You do not type in the brackets!**__",
            ),
        )

        for name, value in entries:
            embed.add_field(name=name, value=value, inline=False)

        embed.set_footer(
            text=f"We were on page {self.current_page + 1} before this message."
        )
        await self.message.edit(embed=embed)

        async def go_back_to_current_page():
            await asyncio.sleep(30.0)
            try:
                await self.show_page(self.current_page)
            except discord.errors.NotFound:
                return

        self.bot.loop.create_task(go_back_to_current_page())


class PaginatedHelpCommand(commands.HelpCommand):
    def __init__(self):
        super().__init__(
            command_attrs={
                "cooldown": commands.Cooldown(1, 3.0, commands.BucketType.member),
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
        menu = HelpMenu(GroupHelpPageSource(cog, entries, prefix=self.clean_prefix))
        await menu.start(self.context)

    def common_command_formatting(self, embed_like, command):
        embed_like.title = f"{self.context.prefix}{self.get_command_signature(command)}"
        if command.description:
            embed_like.description = f"```{command.description}\n\n{command.help}```"
        else:
            embed_like.description = f"```{command.help}```" or "```No help found...```"

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

        source = GroupHelpPageSource(group, entries, prefix=self.clean_prefix)
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
