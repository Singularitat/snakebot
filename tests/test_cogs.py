import unittest
import asyncio
import re

from aiohttp import ClientSession

from bot import Bot
from tests.helpers import MockBot, MockContext, MockMessage
from cogs.animals import animals
from cogs.misc import misc
from cogs.useful import useful
from cogs.stocks import stocks
from cogs.crypto import crypto
from cogs.apis import apis


bot = Bot(MockBot())
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


url_regex = re.compile(
    r"^(?:http)s?://(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}"
    r"[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?))",
    re.IGNORECASE,
)


class AdminCogTests(unittest.IsolatedAsyncioTestCase):
    pass


class AnimalsCogTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.cog = animals(bot=bot)

    @unittest.skip("Really slow as it has to make api calls one by one.")
    async def test_animal_commands(self):
        if not bot.client_session:
            bot.client_session = ClientSession()

        context = MockContext()

        for command in self.cog.walk_commands():
            with self.subTest(command=command.name):
                await command._callback(self.cog, context)

                self.assertRegex(context.send.call_args.args[0], url_regex)


class ApisCogTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.cog = apis(bot=bot)

    @unittest.skip("Really slow as it has to make api calls one by one.")
    async def test_api_commands(self):
        if not bot.client_session:
            bot.client_session = ClientSession()

        context = MockContext()

        with self.subTest(command="fact"):
            await self.cog.fact(self.cog, context)

            self.assertNotEqual(
                context.send.call_args.kwargs["embed"].color.value, 10038562
            )

        with self.subTest(command="country"):
            await self.cog.country(self.cog, context, name="New Zealand")

            embed = context.send.call_args.kwargs["embed"]

            self.assertNotEqual(embed.color.value, 10038562)
            self.assertNotEqual(embed.description, "```Country not found```")

        with self.subTest(command="currency"):
            await self.cog.currency(
                self.cog, context, orginal="USD", amount=10, new="NZD"
            )

            self.assertNotEqual(
                context.send.call_args.kwargs["embed"].color.value, 10038562
            )

        with self.subTest(command="stackoverflow"):
            await self.cog.stackoverflow(
                self.cog, context, search="reverse a linked list"
            )

            embed = context.send.call_args.kwargs["embed"]

            self.assertNotEqual(embed.color.value, 10038562)
            self.assertNotEqual(embed.description, "```No posts found```")

        with self.subTest(command="wikir"):
            await self.cog.wikir(self.cog, context)

            self.assertNotEqual(
                context.send.call_args.kwargs["embed"].color.value, 10038562
            )

        with self.subTest(command="wikipedia"):
            await self.cog.wikipedia(self.cog, context, search="cat")

            embed = context.send.call_args.kwargs["embed"]

            self.assertNotEqual(embed.color.value, 10038562)
            self.assertNotEqual(embed.description, "```Couldn't find any results```")

        with self.subTest(command="covid"):
            await self.cog.covid(self.cog, context)

            embed = context.send.call_args.kwargs["embed"]

            self.assertNotEqual(embed.color.value, 10038562)
            self.assertNotEqual(
                embed.description,
                "```Not a valid country\nExamples: NZ, New Zealand, all```",
            )

        with self.subTest(command="github"):
            await self.cog.github(self.cog, context, username="Singularitat")

            self.assertNotEqual(
                context.send.call_args.kwargs["embed"].color.value, 10038562
            )

        with self.subTest(command="justin"):
            await self.cog.justin(self.cog, context)

            self.assertNotEqual(
                context.send.call_args.kwargs["embed"].color.value, 10038562
            )

        with self.subTest(command="quote"):
            await self.cog.quote(self.cog, context)

            self.assertNotEqual(
                context.send.call_args.kwargs["embed"].color.value, 10038562
            )

        with self.subTest(command="suntzu"):
            await self.cog.suntzu(self.cog, context)

            self.assertNotEqual(
                context.send.call_args.kwargs["embed"].color.value, 10038562
            )

        with self.subTest(command="rhyme"):
            await self.cog.rhyme(self.cog, context, word="forgetful")

            embed = context.send.call_args.kwargs["embed"]

            self.assertNotEqual(embed.color.value, 10038562)
            self.assertNotEqual(
                embed.description,
                "```No results found```",
            )

        with self.subTest(command="spelling"):
            await self.cog.spelling(self.cog, context, word="hipopatamus")

            embed = context.send.call_args.kwargs["embed"]

            self.assertNotEqual(embed.color.value, 10038562)
            self.assertNotEqual(
                embed.description,
                "```No results found```",
            )

        with self.subTest(command="meaning"):
            await self.cog.meaning(self.cog, context, words="ringing in the ears")

            embed = context.send.call_args.kwargs["embed"]

            self.assertNotEqual(embed.color.value, 10038562)
            self.assertNotEqual(
                embed.description,
                "```No results found```",
            )

        with self.subTest(command="apis"):
            await self.cog.apis(self.cog, context)

            self.assertNotEqual(
                context.send.call_args.kwargs["embed"].color.value, 10038562
            )

        with self.subTest(command="apis categories"):
            await self.cog.categories(self.cog, context)

            self.assertNotEqual(
                context.send.call_args.kwargs["embed"].color.value, 10038562
            )

        with self.subTest(command="apis random"):
            await self.cog.random(self.cog, context)

            self.assertNotEqual(
                context.send.call_args.kwargs["embed"].color.value, 10038562
            )

        with self.subTest(command="apis search"):
            await self.cog.search(self.cog, context, search="cat")

            self.assertNotEqual(
                context.send.call_args.kwargs["embed"].color.value, 10038562
            )

        with self.subTest(command="nationalize"):
            await self.cog.nationalize(self.cog, context, search="Joe")

            self.assertNotEqual(
                context.send.call_args.kwargs["embed"].color.value, 10038562
            )

        with self.subTest(command="game"):
            await self.cog.game(self.cog, context)

            self.assertNotEqual(
                context.send.call_args.kwargs["embed"].color.value, 10038562
            )

        with self.subTest(command="game category"):
            await self.cog.game(self.cog, context, category="open-world")

            self.assertNotEqual(
                context.send.call_args.kwargs["embed"].color.value, 10038562
            )


class Background_TasksCogTests(unittest.IsolatedAsyncioTestCase):
    pass


class CryptoCogTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.cog = crypto(bot=bot)

    async def test_crypto_command(self):
        context = MockContext()
        context.invoked_subcommand = None
        context.subcommand_passed = "BTC"

        await self.cog.crypto(self.cog, context)

        self.assertNotEqual(
            context.send.call_args.kwargs["embed"].description,
            "```No stock found for BTC```",
        )


class EconomyCogTests(unittest.IsolatedAsyncioTestCase):
    pass


class EventsCogTests(unittest.IsolatedAsyncioTestCase):
    pass


class HelpCogTests(unittest.IsolatedAsyncioTestCase):
    pass


class InformationCogTests(unittest.IsolatedAsyncioTestCase):
    pass


class MiscCogTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.cog = misc(bot=bot)

    async def test_yeah_command(self):
        context = MockContext()

        await self.cog.yeah(self.cog, context)

        context.send.assert_called_with("Oh yeah its all coming together")

    async def test_convert_command(self):
        context = MockContext()

        await self.cog.convert(self.cog, context, number=32)

        self.assertEqual(
            context.send.call_args.kwargs["embed"].description,
            "```32°F is 0.00°C```",
        )

    async def test_ones_command(self):
        context = MockContext()

        await self.cog.ones(self.cog, context, number=32)

        self.assertEqual(
            context.send.call_args.kwargs["embed"].description,
            "```011111```",
        )

    async def test_twos_command(self):
        context = MockContext()

        await self.cog.twos(self.cog, context, number=32, bits=8)

        self.assertEqual(
            context.send.call_args.kwargs["embed"].description,
            "```00100000```",
        )

    async def test_nato_command(self):
        context = MockContext()

        await self.cog.nato(
            self.cog, context, text="the quick brown fox jumps over 13 lazy dogs"
        )

        context.send.assert_called_with(
            "Tango Hotel Echo (space) Quebec Uniform India Charlie Kilo (space) Bravo "
            "Romeo Oscar Whiskey November (space) Foxtrot Oscar X-ray (space) Juliett "
            "Uniform Mike Papa Sierra (space) Oscar Victor Echo Romeo (space) One Three"
            " (space) Lima Alfa Zulu Yankee (space) Delta Oscar Golf Sierra ",
        )

    async def test_embedjson_command(self):
        context = MockContext()

        await self.cog.embed_json(self.cog, context, message=MockMessage())

        self.assertEqual(
            context.send.call_args.kwargs["embed"].description[:61],
            '```json\n<MagicMock name="mock.embeds.__getitem__().to_dict()"',
        )


class ModerationCogTests(unittest.IsolatedAsyncioTestCase):
    pass


class MusicCogTests(unittest.IsolatedAsyncioTestCase):
    pass


class OwnerCogTests(unittest.IsolatedAsyncioTestCase):
    pass


class StocksCogTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.cog = stocks(bot=bot)

    async def test_stock_command(self):
        context = MockContext()
        context.invoked_subcommand = None
        context.subcommand_passed = "TSLA"

        await self.cog.stock(self.cog, context)

        self.assertNotEqual(
            context.send.call_args.kwargs["embed"].description,
            "```No stock found for TSLA```",
        )


class UsefulCogTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.cog = useful(bot=bot)

    async def test_calc_command(self):
        context = MockContext()

        await self.cog.calc(self.cog, context, num_base="hex", args="0x7d * 0x7d")

        self.assertEqual(
            context.send.call_args.kwargs["embed"].description,
            "```ml\n125 * 125\n\n3d09\n\nDecimal: 15625```",
        )
