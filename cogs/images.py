import base64
from io import BytesIO

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
            elif ctx.message.reference and (message := ctx.message.reference.resolved):
                if message.attachments:
                    image_url = message.attachments[0].url
                elif message.embeds:
                    image_url = message.embeds[0].url
            else:
                image_url = ctx.author.display_avatar.url
        elif image_url.isdigit():
            user = self.bot.get_user(int(image_url))
            if not user:
                return await ctx.reply(
                    embed=discord.Embed(
                        color=discord.Color.blurple(),
                        description="```Couldn't process id```",
                    )
                )
            image_url = user.display_avatar.url

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

    async def jeyy(self, ctx, endpoint, url):
        if not url:
            if ctx.message.attachments:
                url = ctx.message.attachments[0].url
            elif ctx.message.reference and (message := ctx.message.reference.resolved):
                if message.attachments:
                    url = message.attachments[0].url
                elif message.embeds:
                    url = message.embeds[0].url
            else:
                url = ctx.author.display_avatar.url
        elif url.isdigit():
            user = self.bot.get_user(int(url))
            if not user:
                return await ctx.reply(
                    embed=discord.Embed(
                        color=discord.Color.blurple(),
                        description="```Couldn't process id```",
                    )
                )
            url = user.display_avatar.url

        url = f"https://api.jeyy.xyz/image/{endpoint}?image_url={url}"

        async with ctx.typing(), self.bot.client_session.get(url, timeout=30) as resp:
            if resp.status != 200:
                return await ctx.reply(
                    embed=discord.Embed(
                        color=discord.Color.blurple(),
                        description="```Couldn't process image```",
                    ).set_footer(text=f"Status code was {resp.status}")
                )
            image = BytesIO()

            async for chunk in resp.content.iter_chunked(8 * 1024):
                image.write(chunk)

            image.seek(0)
            await ctx.reply(file=discord.File(fp=image, filename=f"{endpoint}.gif"))

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

    @commands.command(name="ascii")
    async def _ascii(self, ctx, url: str = None):
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
        """Uses the Sobel operator on an image.

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

    @commands.command()
    async def mirror(self, ctx, url: str = None):
        """Mirror an image on the y axis.

        url: str
        """
        await self.dagpi(ctx, "mirror", url)

    @commands.command()
    async def lego(self, ctx, url: str = None):
        """Makes an image look like it is made out of lego.

        url: str
        """
        await self.dagpi(ctx, "lego", url)

    @commands.command()
    async def flip(self, ctx, url: str = None):
        """Flips an image upsidedown.

        url: str
        """
        await self.dagpi(ctx, "flip", url)

    @commands.command()
    async def mosaic(self, ctx, url: str = None):
        """Makes an image look like an roman mosaic.

        url: str
        """
        await self.dagpi(ctx, "mosiac", url)

    @commands.command()
    async def charcoal(self, ctx, url: str = None):
        """Makes an image look like a charcoal drawing.

        url: str
        """
        await self.dagpi(ctx, "charcoal", url)

    @commands.command()
    async def rgb(self, ctx, url: str = None):
        """Get an RGB graph of an image's colors.

        url: str
        """
        await self.dagpi(ctx, "rgb", url)

    @commands.command()
    async def shatter(self, ctx, url: str = None):
        """Puts a broken glass overlay on an image.

        url: str
        """
        await self.dagpi(ctx, "shatter", url)

    @commands.command()
    async def paint(self, ctx, url: str = None):
        """Makes an image look like a painting.

        url: str
        """
        await self.dagpi(ctx, "paint", url)

    @commands.command()
    async def rainbow(self, ctx, url: str = None):
        """Gives a weird rainbow effect to an image.

        url: str
        """
        await self.dagpi(ctx, "rainbow", url)

    @commands.command()
    async def burn(self, ctx, url: str = None):
        """Burns an image.

        url: str
        """
        await self.dagpi(ctx, "burn", url)

    @commands.command()
    async def triggered(self, ctx, url: str = None):
        """Makes a triggered gif with an image.

        url: str
        """
        await self.dagpi(ctx, "triggered", url)

    @commands.command()
    async def matrix(self, ctx, url: str = None):
        """Adds a matrix overlay onto image.

        url: str
        """
        await self.jeyy(ctx, "matrix", url)

    @commands.command()
    async def sensitive(self, ctx, url: str = None):
        """Puts the instagram sensitive content filter over an image.

        url: str
        """
        await self.jeyy(ctx, "sensitive", url)

    @commands.command()
    async def balls(self, ctx, url: str = None):
        """Turns an image into balls that are dropped.

        url: str
        """
        await self.jeyy(ctx, "balls", url)

    @commands.command()
    async def hearts(self, ctx, url: str = None):
        """Puts a hearts gif overlay onto an image.

        url: str
        """
        await self.jeyy(ctx, "hearts", url)

    @commands.command()
    async def glitch(self, ctx, url: str = None):
        """Adds glitches to an image as a gif.

        url: str
        """
        await self.jeyy(ctx, "glitch", url)

    @commands.command()
    async def lamp(self, ctx, url: str = None):
        """Flickers an image like a lamp turning on and off.

        url: str
        """
        await self.jeyy(ctx, "lamp", url)

    @commands.command()
    async def sob(self, ctx, url: str = None):
        """Puts a picture of Melvin Lawson sobbing on the background of an image.

        url: str
        """
        await self.jeyy(ctx, "sob", url)

    @commands.command()
    async def cartoon(self, ctx, url: str = None):
        """Makes an image look like a cartoon image.

        url: str
        """
        await self.jeyy(ctx, "cartoon", url)

    @commands.command()
    async def canny(self, ctx, url: str = None):
        """Canny edge detection on an image.

        url: str
        """
        await self.jeyy(ctx, "canny", url)

    @commands.command()
    async def bonk(self, ctx, url: str = None):
        """A gif of an image getting whacked by news paper.

        url: str
        """
        await self.jeyy(ctx, "bonks", url)

    @commands.command(name="print")
    async def _print(self, ctx, url: str = None):
        """Shows a gif of an image getting printed.

        url: str
        """
        await self.jeyy(ctx, "print", url)

    @commands.command()
    async def warp(self, ctx, url: str = None):
        """Warps an image.

        url: str
        """
        await self.jeyy(ctx, "warp", url)

    @commands.command()
    async def boil(self, ctx, url: str = None):
        """Boils an image.

        url: str
        """
        await self.jeyy(ctx, "boil", url)

    @commands.command()
    async def earthquake(self, ctx, url: str = None):
        """Shakes an image like an earthquake.

        url: str
        """
        await self.jeyy(ctx, "earthquake", url)

    @commands.command(aliases=["bomb"])
    async def nuke(self, ctx, url: str = None):
        """Nukes an image.

        url: str
        """
        await self.jeyy(ctx, "bomb", url)

    @commands.command()
    async def shock(self, ctx, url: str = None):
        """Pulses an image like a heartbeat.

        url: str
        """
        await self.jeyy(ctx, "shock", url)

    @commands.command()
    async def pattern(self, ctx, url: str = None):
        """Puts a pattern overlay gif on an image.

        url: str
        """
        await self.jeyy(ctx, "pattern", url)

    @commands.command(aliases=["kill"])
    async def shoot(self, ctx, url: str = None):
        """Shoots someone.

        url: str
        """
        await self.jeyy(ctx, "shoot", url)

    @commands.command()
    async def bubbles(self, ctx, url: str = None):
        """Turns an image into a gif of bubbles.

        url: str
        """
        await self.jeyy(ctx, "bubble", url)

    @commands.command()
    async def cloth(self, ctx, url: str = None):
        """Turns an image into a gif of a hanging cloth.

        url: str
        """
        await self.jeyy(ctx, "cloth", url)

    @commands.command()
    async def images(self, ctx):
        """Shows all the image manipulation commands."""
        image_commands = []
        for item in dir(self):
            item = getattr(self, item)
            if isinstance(item, commands.core.Command):
                image_commands.append(
                    "`{}{}` ({})".format(
                        ctx.prefix, item, item.help.rstrip("\nurl: str\n")
                    )
                )

        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                title="Image Manipulation Commands",
                description="\n".join(image_commands),
            )
        )


def setup(bot: commands.Bot) -> None:
    """Starts the image cog."""
    bot.add_cog(images(bot))
