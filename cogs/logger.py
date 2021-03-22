from discord.ext import commands
import logging
import requests
import config
import json

session = requests.Session()


class RequestsHandler(logging.Handler):
    def emit(self, record):
        if not hasattr(config, 'loggingtoken') or not config.loggingtoken:
            return
        try:
            log_entry = json.loads(self.format(record))
        except json.decoder.JSONDecodeError:
            log_entry = {
                "message": record.msg,
                "level": record.levelname,
                "name": record.name,
                "line": record.lineno,
                "time": record.asctime,
            }
        session.post(
            f"https://snakebotdashboard.qw.ms/api/log/new?token={config.loggingtoken}",
            json=log_entry,
        )


class RemoveNoise(logging.Filter):
    def __init__(self):
        super().__init__(name="discord.state")

    @staticmethod
    def filter(record):
        if record.levelname == "WARNING" and "referencing an unknown" in record.msg:
            return False
        return True


logging.getLogger("discord")
logging.getLogger("discord.http")
logging.getLogger("discord.state").addFilter(RemoveNoise())

log = logging.getLogger()
log.setLevel(logging.INFO)
custom_handler = RequestsHandler()
custom_handler.setFormatter(
    logging.Formatter(
        '{"message": "%(message)s", "level": "%(levelname)s", "name": "%(name)s", "line": "%(lineno)d", "time": "%(asctime)s"}'
    )
)
log.addHandler(custom_handler)


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
        if level.upper == "DEBUG":
            logging.getLogger().setLevel(logging.DEBUG)
        if level.upper == "INFO":
            logging.getLogger().setLevel(logging.INFO)
        if level.upper == "WARNING":
            logging.getLogger().setLevel(logging.WARNING)
        if level.upper == "ERROR":
            logging.getLogger().setLevel(logging.ERROR)
        if level.upper == "CRITICAL":
            logging.getLogger().setLevel(logging.CRITICAL)


def setup(bot: commands.Bot) -> None:
    """Starts logger cog."""
    bot.add_cog(logger(bot))
