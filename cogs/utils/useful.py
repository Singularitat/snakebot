import asyncio
import subprocess

import aiohttp

loop = asyncio.get_event_loop()


async def run_process(command, raw=False):
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
        result = await loop.run_in_executor(None, process.communicate)

    if raw:
        return [output.decode() for output in result]

    return "".join([output.decode() for output in result]).split()


async def get_json(session, url):
    """Gets and loads json from a url.

    session: aiohttp.ClientSession
        A aiohttp client session so that a new one isn't made every request
    url: str
        The url to fetch the json from.
    """
    try:
        async with session.get(url) as response:
            return await response.json()
    except (
        asyncio.exceptions.TimeoutError,
        aiohttp.client_exceptions.ContentTypeError,
    ):
        return None
