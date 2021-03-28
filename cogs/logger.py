from discord.ext import commands
import logging


if str(logging.getLogger("discord").handlers) == "[<NullHandler (NOTSET)>]":
    log = logging.getLogger("discord")
    log.setLevel(logging.INFO)

    handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="a")

    handler.setFormatter(
        logging.Formatter(
            '{"message": "%(message)s", "level": "%(levelname)s", "time": "%(asctime)s"}'
        )
    )

    log.addHandler(handler)


class logger(commands.Cog):
    """For commands related to logging."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(hidden=True)
    @commands.is_owner()
    async def loglevel(self, ctx, level):
        """Changes logging level.

        level: str
            The new logging level.
        """
        if level.upper() in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            logging.getLogger("discord").setLevel(getattr(logging, level.upper()))


def setup(bot: commands.Bot) -> None:
    """Starts logger cog."""
    bot.add_cog(logger(bot))
