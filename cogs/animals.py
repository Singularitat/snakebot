import random
from io import BytesIO

import discord
from discord.ext import commands


class animals(commands.Cog):
    """For commands related to animals."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

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
        url = "https://axoltlapi.herokuapp.com/"

        with ctx.typing():
            image = await self.bot.get_json(url)

        await ctx.send(image["url"])

    @commands.command()
    async def lizard(self, ctx):
        """Gets a random lizard image."""
        url = "https://nekos.life/api/v2/img/lizard"

        with ctx.typing():
            lizard = await self.bot.get_json(url)

        await ctx.send(lizard["url"])

    @commands.command()
    async def duck(self, ctx):
        """Gets a random duck image."""
        url = "https://random-d.uk/api/v2/random"

        with ctx.typing():
            duck = await self.bot.get_json(url)

        await ctx.send(duck["url"])

    @commands.command(name="duckstatus")
    async def duck_status(self, ctx, status=404):
        """Gets a duck image for status codes e.g 404.

        status: str
        """
        await ctx.send(f"https://random-d.uk/api/http/{status}.jpg")

    @commands.command()
    async def bunny(self, ctx):
        """Gets a random bunny image."""
        url = "https://api.bunnies.io/v2/loop/random/?media=webm"

        with ctx.typing():
            bunny = await self.bot.get_json(url)

        await ctx.send(bunny["media"]["webm"])

    @commands.command()
    async def whale(self, ctx):
        """Gets a random whale image."""
        url = "https://some-random-api.ml/img/whale"

        with ctx.typing():
            whale = await self.bot.get_json(url)

        await ctx.send(whale["link"])

    @commands.command()
    async def snake(self, ctx):
        """Gets a random snake image."""
        await ctx.send(
            "https://raw.githubusercontent.com/Singularitat/snake-api/master/images/{}.jpg".format(
                random.randint(1, 769)
            )
        )

    @commands.command()
    async def monkey(self, ctx):
        """Gets a random monkey"""
        url = "https://api.monkedev.com/attachments/monkey"

        with ctx.typing():
            monkey = await self.bot.get_json(url)

        await ctx.send(monkey["url"])

    @commands.command()
    async def racoon(self, ctx):
        """Gets a random racoon image."""
        url = "https://some-random-api.ml/img/racoon"

        with ctx.typing():
            image = await self.bot.get_json(url)

        await ctx.send(image["link"])

    @commands.command()
    async def kangaroo(self, ctx):
        """Gets a random kangaroo image."""
        url = "https://some-random-api.ml/img/kangaroo"

        with ctx.typing():
            image = await self.bot.get_json(url)

        await ctx.send(image["link"])

    @commands.command()
    async def koala(self, ctx):
        """Gets a random koala image."""
        url = "https://some-random-api.ml/img/koala"

        with ctx.typing():
            image = await self.bot.get_json(url)

        await ctx.send(image["link"])

    @commands.command()
    async def bird(self, ctx):
        """Gets a random bird image."""
        url = "https://some-random-api.ml/img/birb"

        with ctx.typing():
            image = await self.bot.get_json(url)

        await ctx.send(image["link"])

    @commands.command()
    async def bird2(self, ctx):
        """Gets a random bird image."""
        url = "http://shibe.online/api/birds"

        with ctx.typing():
            image = await self.bot.get_json(url)

        await ctx.send(image[0])

    @commands.command()
    async def bird3(self, ctx):
        """Gets a random bird image."""
        url = "https://api.monkedev.com/attachments/bird"

        with ctx.typing():
            bird = await self.bot.get_json(url)

        await ctx.send(bird["url"])

    @commands.command()
    async def bird4(self, ctx):
        """Gets a random bird image"""
        url = "https://api.alexflipnote.dev/birb"

        with ctx.typing():
            image = await self.bot.get_json(url)

        await ctx.send(image["file"])

    @commands.command()
    async def redpanda(self, ctx):
        """Gets a random red panda image."""
        url = "https://some-random-api.ml/img/red_panda"

        with ctx.typing():
            image = await self.bot.get_json(url)

        await ctx.send(image["link"])

    @commands.command()
    async def panda(self, ctx):
        """Gets a random panda image."""
        url = "https://some-random-api.ml/img/panda"

        with ctx.typing():
            image = await self.bot.get_json(url)

        await ctx.send(image["link"])

    @commands.command()
    async def fox(self, ctx):
        """Gets a random fox image."""
        url = "https://randomfox.ca/floof"

        with ctx.typing():
            image = await self.bot.get_json(url)

        await ctx.send(image["image"])

    @commands.command()
    async def fox2(self, ctx):
        """Gets a random fox image."""
        url = "https://wohlsoft.ru/images/foxybot/randomfox.php"

        with ctx.typing():
            image = await self.bot.get_json(url)

        await ctx.send(image["file"])

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
        url = "https://api.thecatapi.com/v1/images/search"

        with ctx.typing():
            image = await self.bot.get_json(url)

        await ctx.send(image[0]["url"])

    @commands.command()
    async def cat3(self, ctx):
        """Gets a random cat image."""
        url = "https://cataas.com/cat?json=true"

        with ctx.typing():
            image = await self.bot.get_json(url)

        await ctx.send(f"https://cataas.com{image['url']}")

    @commands.command()
    async def cat4(self, ctx):
        """Gets a random cat image."""
        url = "https://thatcopy.pw/catapi/rest"

        with ctx.typing():
            image = await self.bot.get_json(url)

        if not image:
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.dark_red(), description="Failed to reach api"
                ).set_footer(text="api may be temporarily down or experiencing high trafic")
            )

        await ctx.send(image["webpurl"])

    @commands.command()
    async def cat5(self, ctx):
        """Gets a random cat image."""
        url = "http://shibe.online/api/cats"

        with ctx.typing():
            image = await self.bot.get_json(url)

        await ctx.send(image[0])

    @commands.command()
    async def cat6(self, ctx):
        """Gets a random cat image."""
        url = "https://aws.random.cat/meow"

        with ctx.typing():
            image = await self.bot.get_json(url)

        if not image:
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.dark_red(), description="Failed to reach api"
                ).set_footer(text="api may be temporarily down or experiencing high trafic")
            )

        await ctx.send(image["file"])

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

        with ctx.typing():
            image = await self.bot.get_json(url)

        await ctx.send(image["message"])

    @commands.command()
    async def dog2(self, ctx):
        """Gets a random dog image."""
        url = "https://random.dog/woof.json"

        with ctx.typing():
            image = await self.bot.get_json(url)

        await ctx.send(image["url"])

    @commands.command()
    async def dog3(self, ctx):
        """Gets a random dog image."""
        url = "https://api.thedogapi.com/v1/images/search?sub_id=demo-3d4325"

        with ctx.typing():
            image = await self.bot.get_json(url)

        await ctx.send(image[0]["url"])

    @commands.command()
    async def dogstatus(self, ctx, status=404):
        """Gets a dog image for a status e.g 404.

        status: str
        """
        await ctx.send(f"https://http.dog/{status}.jpg")

    @commands.command()
    async def shibe(self, ctx):
        """Gets a random dog image."""
        url = "http://shibe.online/api/shibes"

        with ctx.typing():
            image = await self.bot.get_json(url)

        await ctx.send(image[0])


def setup(bot: commands.Bot) -> None:
    """Starts the animals cog."""
    bot.add_cog(animals(bot))
