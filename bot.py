from __future__ import annotations

import asyncio
import logging
import os
import subprocess
from contextlib import suppress

import aiohttp
import discord
from discord.ext import commands
from discord.gateway import DiscordWebSocket

import config
from cogs.utils.database import Database

log = logging.getLogger()
log.setLevel(50)

handler = logging.FileHandler(filename="bot.log", encoding="utf-8", mode="a")
handler.setFormatter(
    logging.Formatter("%(message)s; %(asctime)s", datefmt="%m-%d %H:%M:%S")
)

log.addHandler(handler)


class MonkeyWebSocket(DiscordWebSocket):
    async def send_as_json(self, data):
        if data.get("op") == self.IDENTIFY:
            if data.get("d", {}).get("properties", {}).get("$browser") is not None:
                data["d"]["properties"]["$browser"] = "Discord Android"
                data["d"]["properties"]["$device"] = "Discord Android"
        await super().send_as_json(data)


DiscordWebSocket.from_client = MonkeyWebSocket.from_client


class Bot(commands.Bot):
    """A subclass of discord.ext.commands.Bot."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.client_session = None
        self.cache = {}
        self.DB = Database()

    async def get_prefix(self, message: discord.Message) -> str:
        default = "."

        if not message.guild:
            return default

        prefix = self.DB.main.get(f"{message.guild.id}-prefix".encode())

        if not prefix:
            return default

        return prefix.decode()

    @classmethod
    def create(cls) -> commands.Bot:
        """Create and return an instance of a Bot."""
        loop = asyncio.new_event_loop()

        intents = discord.Intents.all()
        intents.dm_typing = False
        intents.webhooks = False
        intents.integrations = False

        return cls(
            loop=loop,
            command_prefix=commands.when_mentioned_or(cls.get_prefix),
            activity=discord.Game(name="Tax Evasion Simulator"),
            case_insensitive=True,
            allowed_mentions=discord.AllowedMentions(everyone=False),
            intents=intents,
            owner_ids=(225708387558490112,),
        )

    def load_extensions(self) -> None:
        """Load all extensions."""
        for extension in [f.name[:-3] for f in os.scandir("cogs") if f.is_file()]:
            try:
                self.load_extension(f"cogs.{extension}")
            except Exception as e:
                print(f"Failed to load extension {extension}.\n{e} \n")

    async def get_json(self, url: str) -> dict:
        """Gets and loads json from a url.

        url: str
            The url to fetch the json from.
        """
        try:
            async with self.client_session.get(url) as response:
                return await response.json()
        except (
            asyncio.exceptions.TimeoutError,
            aiohttp.client_exceptions.ContentTypeError,
        ):
            return None

    async def run_process(self, command, raw=False) -> list | str:
        """Runs a shell command and returns the output.

        command: str
            The command to run.
        raw: bool
            If True returns the result just decoded.
        """
        try:
            process = await asyncio.create_subprocess_shell(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            result = await process.communicate()
        except NotImplementedError:
            process = subprocess.Popen(
                command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            result = await self.loop.run_in_executor(None, process.communicate)

        if raw:
            return [output.decode() for output in result]

        return "".join([output.decode() for output in result]).split()

    def remove_from_cache(self, search):
        """Deletes a search from the cache.

        search: str
        """
        try:
            self.cache.pop(search)
        except KeyError:
            return

    async def close(self) -> None:
        """Close the Discord connection and the aiohttp session."""
        for ext in list(self.extensions):
            with suppress(Exception):
                self.unload_extension(ext)

        for cog in list(self.cogs):
            with suppress(Exception):
                self.remove_cog(cog)

        await super().close()

        if self.client_session:
            await self.client_session.close()

    async def login(self, *args, **kwargs) -> None:
        """Setup the client_session before logging in."""
        self.client_session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10)
        )

        await super().login(*args, **kwargs)


if __name__ == "__main__":
    bot = Bot.create()
    bot.load_extensions()
    bot.run(config.token)
