import random

from discord.ext import commands

from cogs.utils.useful import get_json


class animals(commands.Cog):
    """For commands related to animals."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command()
    async def lizard(self, ctx):
        """Gets a random lizard image."""
        url = "https://nekos.life/api/v2/img/lizard"

        async with ctx.typing():
            lizard = await get_json(url)

        await ctx.send(lizard["url"])

    @commands.command()
    async def duck(self, ctx):
        """Gets a random duck image."""
        url = "https://random-d.uk/api/v1/random?type=png"

        async with ctx.typing():
            duck = await get_json(url)

        await ctx.send(duck["url"])

    @commands.command()
    async def bunny(self, ctx):
        """Gets a random bunny image."""
        url = "https://api.bunnies.io/v2/loop/random/?media=webm"

        async with ctx.typing():
            bunny = await get_json(url)

        await ctx.send(bunny["media"]["webm"])

    @commands.command()
    async def whale(self, ctx):
        """Gets a random whale image."""
        url = "https://some-random-api.ml/img/whale"

        async with ctx.typing():
            whale = await get_json(url)

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
        """Gets a random monkey."""
        url = "https://ntgc.ddns.net/mAPI/api"

        async with ctx.typing():
            monkey = await get_json(url)

        await ctx.send(monkey["image"])

    @commands.command()
    async def monkey2(self, ctx):
        """Gets a random monkey"""
        url = "https://api.monkedev.com/attachments/monkey"

        async with ctx.typing():
            monkey = await get_json(url)

        await ctx.send(monkey["url"])

    @commands.command()
    async def racoon(self, ctx):
        """Gets a random racoon image."""
        url = "https://some-random-api.ml/img/racoon"

        async with ctx.typing():
            image = await get_json(url)

        await ctx.send(image["link"])

    @commands.command()
    async def kangaroo(self, ctx):
        """Gets a random kangaroo image."""
        url = "https://some-random-api.ml/img/kangaroo"

        async with ctx.typing():
            image = await get_json(url)

        await ctx.send(image["link"])

    @commands.command()
    async def koala(self, ctx):
        """Gets a random koala image."""
        url = "https://some-random-api.ml/img/koala"

        async with ctx.typing():
            image = await get_json(url)

        await ctx.send(image["link"])

    @commands.command()
    async def bird(self, ctx):
        """Gets a random bird image."""
        url = "https://some-random-api.ml/img/birb"

        async with ctx.typing():
            image = await get_json(url)

        await ctx.send(image["link"])

    @commands.command()
    async def bird2(self, ctx):
        """Gets a random bird image."""
        url = "http://shibe.online/api/birds"

        async with ctx.typing():
            image = await get_json(url)

        await ctx.send(image[0])

    @commands.command()
    async def bird3(self, ctx):
        """Gets a rnadom bird image."""
        url = "https://api.monkedev.com/attachments/bird"

        async with ctx.typing():
            bird = await get_json(url)

        await ctx.send(bird["url"])

    @commands.command()
    async def redpanda(self, ctx):
        """Gets a random red panda image."""
        url = "https://some-random-api.ml/img/red_panda"

        async with ctx.typing():
            image = await get_json(url)

        await ctx.send(image["link"])

    @commands.command()
    async def panda(self, ctx):
        """Gets a random panda image."""
        url = "https://some-random-api.ml/img/panda"

        async with ctx.typing():
            image = await get_json(url)

        await ctx.send(image["link"])

    @commands.command()
    async def fox(self, ctx):
        """Gets a random fox image."""
        url = "https://randomfox.ca/floof"

        async with ctx.typing():
            image = await get_json(url)

        await ctx.send(image["image"])

    @commands.command()
    async def fox2(self, ctx):
        """Gets a random fox image."""
        url = "https://wohlsoft.ru/images/foxybot/randomfox.php"

        async with ctx.typing():
            image = await get_json(url)

        await ctx.send(image["file"])

    @commands.command()
    async def cat(self, ctx):
        """Gets a random cat image."""
        url = "https://api.thecatapi.com/v1/images/search"

        async with ctx.typing():
            image = await get_json(url)

        await ctx.send(image[0]["url"])

    @commands.command()
    async def cat2(self, ctx):
        """Gets a random cat image."""
        url = "https://cataas.com/cat?json=true"

        async with ctx.typing():
            image = await get_json(url)

        await ctx.send(f"https://cataas.com{image['url']}")

    @commands.command()
    async def cat3(self, ctx):
        """Gets a random cat image."""
        url = "https://thatcopy.pw/catapi/rest"

        async with ctx.typing():
            image = await get_json(url)

        await ctx.send(image["webpurl"])

    @commands.command()
    async def cat4(self, ctx):
        """Gets a random cat image."""
        url = "http://shibe.online/api/cats"

        async with ctx.typing():
            image = await get_json(url)

        await ctx.send(image[0])

    @commands.command()
    async def cat5(self, ctx):
        """Gets a random cat image."""
        url = "https://aws.random.cat/meow"

        async with ctx.typing():
            image = await get_json(url)

        await ctx.send(image["file"])

    @commands.command(name="catstatus")
    async def cat_status(self, ctx, status):
        """Gets a cat image for a status e.g Error 404 not found."""
        await ctx.send(f"https://http.cat/{status}")

    @commands.command()
    async def dog(self, ctx, breed=None):
        """Gets a random dog image."""
        if breed:
            url = f"https://dog.ceo/api/breed/{breed}/images/random"
        else:
            url = "https://dog.ceo/api/breeds/image/random"

        async with ctx.typing():
            image = await get_json(url)

        await ctx.send(image["message"])

    @commands.command()
    async def dog2(self, ctx):
        """Gets a random dog image."""
        url = "https://random.dog/woof.json"

        async with ctx.typing():
            image = await get_json(url)

        await ctx.send(image["url"])

    @commands.command(name="dogstatus")
    async def dog_status(self, ctx, status):
        """Gets a dog image for a status e.g Error 404 not found."""
        await ctx.send(f"https://httpstatusdogs.com/img/{status}.jpg")

    @commands.command()
    async def shibe(self, ctx):
        """Gets a random dog image."""
        url = "http://shibe.online/api/shibes"

        async with ctx.typing():
            image = await get_json(url)

        await ctx.send(image[0])


def setup(bot: commands.Bot) -> None:
    """Starts the animals cog."""
    bot.add_cog(animals(bot))
