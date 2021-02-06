from discord.ext import commands
import logging
import requests
import config


class RequestsHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        return None
        return requests.get(
            f"https://snakebotdashboard.qw.ms/api/log/new?token={config.loggingtoken}&error={log_entry}"
        ).content


class RemoveNoise(logging.Filter):
    def __init__(self):
        super().__init__(name="discord.state")

    # @staticmethod
    # def filter(self, record):
    #     if record.levelname == "WARNING" and "referencing an unknown" in record.msg:
    #         return False
    #     return True


logging.getLogger("discord")
logging.getLogger("discord.http")
logging.getLogger("discord.state").addFilter(RemoveNoise())

log = logging.getLogger()
log.setLevel(logging.INFO)
custom_handler = RequestsHandler()
custom_handler.setFormatter(
    logging.Formatter(
        "{'@message': %(message)s, '@level': %(levelname)s, '@name': %(name)s, '@line': %(lineno)s"
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
            log.setLevel(logging.DEBUG)
        if level.upper == "info":
            log.setLevel(logging.INFO)
        if level.upper == "WARNING":
            log.setLevel(logging.WARNING)
        if level.upper == "ERROR":
            log.setLevel(logging.ERROR)
        if level.upper == "CRITICAL":
            log.setLevel(logging.CRITICAL)


def setup(bot):
    bot.add_cog(logger(bot))
