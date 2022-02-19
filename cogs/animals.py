from __future__ import annotations

import random
from io import BytesIO

import discord
from discord.ext import commands


class animals(commands.Cog):
    """For commands related to animals."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def get(self, ctx, url: str, key: str | int, subkey: str | int = None):
        """Returns json response from url or sends error embed."""
        with ctx.typing():
            resp = await self.bot.get_json(url)

        if not resp:
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.dark_red(), description="Failed to reach api"
                ).set_footer(
                    text="api may be temporarily down or experiencing high trafic"
                )
            )
        await ctx.send(resp[key] if not subkey else resp[key][subkey])

    @commands.command()
    async def horse(self, ctx):
        """This horse doesn't exist."""
        url = "https://thishorsedoesnotexist.com"

        async with ctx.typing(), self.bot.client_session.get(url) as resp:
            with BytesIO((await resp.read())) as image_binary:
                await ctx.send(file=discord.File(fp=image_binary, filename="image.png"))

    @commands.command()
    async def axolotl(self, ctx):
        """Gets a random axolotl image."""
        await self.get(ctx, "https://axoltlapi.herokuapp.com", "url")

    @commands.command()
    async def lizard(self, ctx):
        """Gets a random lizard image."""
        await self.get(ctx, "https://nekos.life/api/v2/img/lizard", "url")

    @commands.command()
    async def duck(self, ctx):
        """Gets a random duck image."""
        await self.get(ctx, "https://random-d.uk/api/v2/random", "url")

    @commands.command(name="duckstatus")
    async def duck_status(self, ctx, status=404):
        """Gets a duck image for status codes e.g 404.

        status: str
        """
        await ctx.send(f"https://random-d.uk/api/http/{status}.jpg")

    @commands.command()
    async def bunny(self, ctx):
        """Gets a random bunny image."""
        await self.get(
            ctx, "https://api.bunnies.io/v2/loop/random/?media=webm", "media", "webm"
        )

    @commands.command()
    async def whale(self, ctx):
        """Gets a random whale image."""
        await self.get(ctx, "https://some-random-api.ml/img/whale", "link")

    @commands.command()
    async def snake(self, ctx):
        """Gets a random snake image."""
        await ctx.send(
            "https://raw.githubusercontent.com/Singularitat/snake-api/master/images/{}.jpg".format(
                random.randint(1, 769)
            )
        )

    @commands.command()
    async def racoon(self, ctx):
        """Gets a random racoon image."""
        await self.get(ctx, "https://some-random-api.ml/img/racoon", "link")

    @commands.command()
    async def kangaroo(self, ctx):
        """Gets a random kangaroo image."""
        await self.get(ctx, "https://some-random-api.ml/img/kangaroo", "link")

    @commands.command()
    async def koala(self, ctx):
        """Gets a random koala image."""
        await self.get(ctx, "https://some-random-api.ml/img/koala", "link")

    @commands.command()
    async def bird(self, ctx):
        """Gets a random bird image."""
        await self.get(ctx, "https://some-random-api.ml/img/birb", "link")

    @commands.command()
    async def bird2(self, ctx):
        """Gets a random bird image."""
        await self.get(ctx, "http://shibe.online/api/birds", 0)

    @commands.command()
    async def bird4(self, ctx):
        """Gets a random bird image"""
        await self.get(ctx, "https://api.alexflipnote.dev/birb", "file")

    @commands.command()
    async def redpanda(self, ctx):
        """Gets a random red panda image."""
        await self.get(ctx, "https://some-random-api.ml/img/red_panda", "link")

    @commands.command()
    async def panda(self, ctx):
        """Gets a random panda image."""
        await self.get(ctx, "https://some-random-api.ml/img/panda", "link")

    @commands.command()
    async def fox(self, ctx):
        """Gets a random fox image."""
        await self.get(ctx, "https://randomfox.ca/floof", "image")

    @commands.command()
    async def fox2(self, ctx):
        """Gets a random fox image."""
        await self.get(ctx, "https://wohlsoft.ru/images/foxybot/randomfox.php", "file")

    @commands.command()
    async def fox3(self, ctx):
        """Gets a random fox image."""
        await self.get(ctx, "https://some-random-api.ml/img/fox", "link")

    @commands.command()
    async def cat(self, ctx):
        """This cat doesn't exist."""
        url = "https://thiscatdoesnotexist.com"

        async with ctx.typing(), self.bot.client_session.get(url) as resp:
            with BytesIO((await resp.read())) as image_binary:
                await ctx.send(file=discord.File(fp=image_binary, filename="image.png"))

    @commands.command()
    async def cat2(self, ctx):
        """Gets a random cat image."""
        await self.get(ctx, "https://api.thecatapi.com/v1/images/search", 0, "url")

    @commands.command()
    async def cat3(self, ctx):
        """Gets a random cat image."""
        url = "https://cataas.com/cat?json=true"

        with ctx.typing():
            resp = await self.bot.get_json(url)

        if not resp:
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.dark_red(), description="Failed to reach api"
                ).set_footer(
                    text="api may be temporarily down or experiencing high trafic"
                )
            )

        await ctx.send(f"https://cataas.com{resp['url']}")

    @commands.command()
    async def cat4(self, ctx):
        """Gets a random cat image."""
        await self.get(ctx, "https://thatcopy.pw/catapi/rest", "webpurl")

    @commands.command()
    async def cat5(self, ctx):
        """Gets a random cat image."""
        await self.get(ctx, "http://shibe.online/api/cats", 0)

    @commands.command()
    async def cat6(self, ctx):
        """Gets a random cat image."""
        await self.get(ctx, "https://aws.random.cat/meow", "file")

    @commands.command()
    async def catstatus(self, ctx, status=404):
        """Gets a cat image for a status e.g 404.

        status: str
        """
        await ctx.send(f"https://http.cat/{status}")

    @commands.command()
    async def dog(self, ctx, breed=None):
        """Gets a random dog image."""
        if breed:
            url = f"https://dog.ceo/api/breed/{breed}/images/random"
        else:
            url = "https://dog.ceo/api/breeds/image/random"

        await self.get(ctx, url, "message")

    @commands.command()
    async def dog2(self, ctx):
        """Gets a random dog image."""
        await self.get(ctx, "https://random.dog/woof.json", "url")

    @commands.command()
    async def dog3(self, ctx):
        """Gets a random dog image."""
        await self.get(
            ctx,
            "https://api.thedogapi.com/v1/images/search?sub_id=demo-3d4325",
            0,
            "url",
        )

    @commands.command()
    async def dogstatus(self, ctx, status=404):
        """Gets a dog image for a status e.g 404.

        status: str
        """
        await ctx.send(f"https://http.dog/{status}.jpg")

    @commands.command()
    async def shibe(self, ctx):
        """Gets a random dog image."""
        await self.get(ctx, "http://shibe.online/api/shibes", 0)


def setup(bot: commands.Bot) -> None:
    """Starts the animals cog."""
    bot.add_cog(animals(bot))
