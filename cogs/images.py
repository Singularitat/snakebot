from io import BytesIO
import base64

import discord

from discord.ext import commands


class images(commands.Cog):
    """Image manipulation commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def dagpi(self, ctx, method, image_url):
        if not image_url:
            if ctx.message.attachments:
                image_url = ctx.message.attachments[0].url
            elif ctx.message.reference:
                message = ctx.message.reference.cached_message
                if message and message.attachments:
                    image_url = message.attachments[0].url
            else:
                image_url = ctx.author.display_avatar.url
        url = "https://dagpi.xyz/api/routes/dagpi-manip"
        data = {
            "method": method,
            "token": "",
            "url": image_url,
        }
        headers = {
            "content-type": "text/plain;charset=UTF-8",
        }

        async with ctx.typing(), self.bot.client_session.post(
            url, json=data, headers=headers, timeout=30
        ) as resp:
            if resp.content_type == "text/plain":
                return await ctx.reply(
                    embed=discord.Embed(
                        color=discord.Color.blurple(),
                        description=f"```ml\n{(await resp.text())}```",
                    )
                )
            resp = await resp.json()

            if "response" in resp:
                return await ctx.reply(
                    embed=discord.Embed(
                        color=discord.Color.blurple(),
                        description=f"```\n{resp['response']}```",
                    )
                )

            with BytesIO(base64.b64decode(resp["image"][22:])) as image:
                filename = f"image.{resp['format']}"
                await ctx.reply(file=discord.File(fp=image, filename=filename))

    @commands.command()
    async def deepfry(self, ctx, url: str = None):
        """Deepfrys an image.

        url: str
        """
        await self.dagpi(ctx, "deepfry", url)

    @commands.command()
    async def pixelate(self, ctx, url: str = None):
        """Pixelates an image.

        url: str
        """
        await self.dagpi(ctx, "pixel", url)

    @commands.command()
    async def ascii(self, ctx, url: str = None):
        """Turns an image into ascii text.

        url: str
        """
        await self.dagpi(ctx, "ascii", url)

    @commands.command()
    async def sketch(self, ctx, url: str = None):
        """Make a gif of sketching the image.

        url: str
        """
        await self.dagpi(ctx, "sketch", url)

    @commands.command()
    async def sobel(self, ctx, url: str = None):
        """Gets an image with the sobel effect.

        url: str
        """
        await self.dagpi(ctx, "sobel", url)

    @commands.command()
    async def magik(self, ctx, url: str = None):
        """Does magik on an image.

        url: str
        """
        await self.dagpi(ctx, "magik", url)

    @commands.command()
    async def colors(self, ctx, url: str = None):
        """Shows the colors present in the image.

        url: str
        """
        await self.dagpi(ctx, "colors", url)

    @commands.command()
    async def petpet(self, ctx, url: str = None):
        """Pet Pet.

        url: str
        """
        await self.dagpi(ctx, "petpet", url)

    @commands.command()
    async def invert(self, ctx, url: str = None):
        """Inverts the colors of an image.

        url: str
        """
        await self.dagpi(ctx, "invert", url)

    @commands.command()
    async def hog(self, ctx, url: str = None):
        """Histogram of Oriented Gradients of an image.

        url: str
        """
        await self.dagpi(ctx, "hog", url)


def setup(bot: commands.Bot) -> None:
    """Starts the image cog."""
    bot.add_cog(images(bot))
