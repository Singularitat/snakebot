import unittest
import asyncio
import re

from aiohttp import ClientSession

from bot import Bot
import tests.helpers as helpers
from cogs.animals import animals
from cogs.misc import misc
from cogs.useful import useful
from cogs.stocks import stocks
from cogs.crypto import crypto
from cogs.apis import apis


bot = Bot(helpers.MockBot())
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

    async def run_command(self, command):
        context = helpers.MockContext()

        with self.subTest(command=command.name):
            await command._callback(self.cog, context)

            self.assertRegex(context.send.call_args.args[0], url_regex)

    async def test_animal_commands(self):
        bot.client_session = ClientSession()

        await asyncio.gather(
            *[self.run_command(command) for command in self.cog.walk_commands()]
        )


class ApisCogTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.cog = apis(bot=bot)

    async def test_api_commands(self):
        bot.client_session = ClientSession()

        await asyncio.gather(
            *[getattr(self, name)() for name in dir(self) if name.endswith("command")]
        )

    async def fact_command(self):
        context = helpers.MockContext()

        with self.subTest(command="fact"):
            await self.cog.fact(self.cog, context)

            self.assertNotEqual(
                context.send.call_args.kwargs["embed"].color.value, 10038562
            )

    async def country_command(self):
        context = helpers.MockContext()

        with self.subTest(command="country"):
            await self.cog.country(self.cog, context, name="New Zealand")

            embed = context.send.call_args.kwargs["embed"]

            self.assertNotEqual(embed.color.value, 10038562)
            self.assertNotEqual(embed.description, "```Country not found```")

    async def currency_command(self):
        context = helpers.MockContext()

        with self.subTest(command="currency"):
            await self.cog.currency(
                self.cog, context, orginal="USD", amount=10, new="NZD"
            )

            self.assertNotEqual(
                context.send.call_args.kwargs["embed"].color.value, 10038562
            )

    async def stackoverflow_command(self):
        context = helpers.MockContext()

        with self.subTest(command="stackoverflow"):
            await self.cog.stackoverflow(
                self.cog, context, search="reverse a linked list"
            )

            embed = context.send.call_args.kwargs["embed"]

            self.assertNotEqual(embed.color.value, 10038562)
            self.assertNotEqual(embed.description, "```No posts found```")

    async def justin_command(self):
        context = helpers.MockContext()

        with self.subTest(command="justin"):
            await self.cog.justin(self.cog, context)

            self.assertNotEqual(
                context.send.call_args.kwargs["embed"].color.value, 10038562
            )

    async def quote_command(self):
        context = helpers.MockContext()

        with self.subTest(command="quote"):
            await self.cog.quote(self.cog, context)

            self.assertNotEqual(
                context.send.call_args.kwargs["embed"].color.value, 10038562
            )

    async def suntzu_command(self):
        context = helpers.MockContext()

        with self.subTest(command="suntzu"):
            await self.cog.suntzu(self.cog, context)

            self.assertNotEqual(
                context.send.call_args.kwargs["embed"].color.value, 10038562
            )

    async def rhyme_command(self):
        context = helpers.MockContext()

        with self.subTest(command="rhyme"):
            await self.cog.rhyme(self.cog, context, word="forgetful")

            embed = context.send.call_args.kwargs["embed"]

            self.assertNotEqual(embed.color.value, 10038562)
            self.assertNotEqual(embed.description, "```No results found```")

    async def spelling_command(self):
        context = helpers.MockContext()

        with self.subTest(command="spelling"):
            await self.cog.spelling(self.cog, context, word="hipopatamus")

            embed = context.send.call_args.kwargs["embed"]

            self.assertNotEqual(embed.color.value, 10038562)
            self.assertNotEqual(embed.description, "```No results found```")

    async def meaning_command(self):
        context = helpers.MockContext()

        with self.subTest(command="meaning"):
            await self.cog.meaning(self.cog, context, words="ringing in the ears")

            embed = context.send.call_args.kwargs["embed"]

            self.assertNotEqual(embed.color.value, 10038562)
            self.assertNotEqual(embed.description, "```No results found```")

    async def apis_command(self):
        context = helpers.MockContext()
        context.invoked_subcommand = None

        with self.subTest(command="apis"):
            await self.cog.apis(self.cog, context)

            self.assertNotEqual(
                context.send.call_args.kwargs["embed"].color.value, 10038562
            )

    async def apis_categories_command(self):
        context = helpers.MockContext()

        with self.subTest(command="apis categories"):
            await self.cog.categories(self.cog, context)

            self.assertNotEqual(
                context.send.call_args.kwargs["embed"].color.value, 10038562
            )

    async def apis_random_command(self):
        context = helpers.MockContext()

        with self.subTest(command="apis random"):
            await self.cog.random(self.cog, context)

            self.assertNotEqual(
                context.send.call_args.kwargs["embed"].color.value, 10038562
            )

    async def apis_search_command(self):
        context = helpers.MockContext()

        with self.subTest(command="apis search"):
            await self.cog.search(self.cog, context, search="cat")

            self.assertNotEqual(
                context.send.call_args.kwargs["embed"].color.value, 10038562
            )

    async def nationalize_command(self):
        context = helpers.MockContext()

        with self.subTest(command="nationalize"):
            await self.cog.nationalize(self.cog, context, first_name="Joe")

            self.assertNotEqual(
                context.send.call_args.kwargs["embed"].color.value, 10038562
            )

    async def game_command(self):
        context = helpers.MockContext()
        context.invoked_subcommand = None

        with self.subTest(command="game"):
            await self.cog.game(self.cog, context)

            self.assertNotEqual(
                context.send.call_args.kwargs["embed"].color.value, 10038562
            )

    async def game_category_command(self):
        context = helpers.MockContext()

        with self.subTest(command="game category"):
            await self.cog.category(self.cog, context, category="open-world")

            self.assertNotEqual(
                context.send.call_args.kwargs["embed"].color.value, 10038562
            )

    async def apod_command(self):
        context = helpers.MockContext()

        with self.subTest(command="apod"):
            await self.cog.apod(self.cog, context)

            self.assertNotEqual(
                context.send.call_args.kwargs["embed"].color.value, 10038562
            )

    async def github_trending_command(self):
        context = helpers.MockContext()

        with self.subTest(command="github_trending"):
            await self.cog.github_trending(self.cog, context)

            self.assertNotEqual(
                context.send.call_args.kwargs["embed"].color.value, 10038562
            )

    async def gender_command(self):
        context = helpers.MockContext()

        with self.subTest(command="gender"):
            await self.cog.gender(self.cog, context, first_name="Joe")

            self.assertNotEqual(
                context.send.call_args.kwargs["embed"].color.value, 10038562
            )

    async def trends_command(self):
        context = helpers.MockContext()

        with self.subTest(command="trends"):
            await self.cog.trends(self.cog, context)

            embed = context.send.call_args.kwargs["embed"]

            self.assertNotEqual(embed.color.value, 10038562)
            self.assertNotEqual(
                embed.description, "```Country New Zealand not found.```"
            )

    async def fake_user_command(self):
        context = helpers.MockContext()

        with self.subTest(command="fake_user"):
            await self.cog.fake_user(self.cog, context)

            self.assertNotEqual(
                context.send.call_args.kwargs["embed"].color.value, 10038562
            )

    async def dad_joke_command(self):
        context = helpers.MockContext()

        with self.subTest(command="dad_joke"):
            await self.cog.dad_joke(self.cog, context)

            self.assertIs(context.reply.call_args.kwargs.get("embed"), None)

    async def cocktail_command(self):
        context = helpers.MockContext()

        with self.subTest(command="cocktail"):
            await self.cog.cocktail(self.cog, context)

            embed = context.send.call_args.kwargs["embed"]

            self.assertNotEqual(embed.color.value, 10038562)
            self.assertNotEqual(embed.description, "```No cocktails found.```")

    async def trivia_command(self):
        context = helpers.MockContext()

        with self.subTest(command="trivia"), self.assertRaises(TypeError):
            await self.cog.trivia(self.cog, context)

    async def minecraft_command(self):
        context = helpers.MockContext()

        with self.subTest(command="minecraft"):
            await self.cog.minecraft(self.cog, context, ip="ntgc.ddns.net")

            embed = context.send.call_args.kwargs["embed"]

            self.assertNotEqual(embed.color.value, 10038562)
            self.assertNotEqual(embed.description, "```Pinging failed.```")
            self.assertNotEqual(embed.description, "```Pinging timed out.```")

    async def define_command(self):
        context = helpers.MockContext()

        with self.subTest(command="define"):
            await self.cog.define(self.cog, context, word="cat")

            embed = context.send.call_args.kwargs["embed"]

            self.assertNotEqual(embed.color.value, 10038562)
            self.assertNotEqual(embed.description, "```No definition found```")

    async def latex_command(self):
        context = helpers.MockContext()

        with self.subTest(command="latex"):
            await self.cog.latex(self.cog, context, latex="Latex")

            self.assertIs(context.send.call_args.kwargs.get("embed"), None)

    async def xkcd_command(self):
        context = helpers.MockContext()

        with self.subTest(command="xkcd"):
            await self.cog.xkcd(self.cog, context)

            self.assertIs(context.send.call_args.kwargs.get("embed"), None)

    async def urban_command(self):
        context = helpers.MockContext()

        with self.subTest(command="urban"):
            await self.cog.urban(self.cog, context, search="cat")

            embed = context.send.call_args.kwargs["embed"]

            self.assertNotEqual(embed.color.value, 10038562)
            self.assertNotEqual(embed.title, "Timed out try again later")
            self.assertNotEqual(embed.title, "No results found")

    async def wikir_command(self):
        context = helpers.MockContext()

        with self.subTest(command="wikir"):
            await self.cog.wikir(self.cog, context)

            self.assertNotEqual(
                context.send.call_args.kwargs["embed"].color.value, 10038562
            )

    async def wikipedia_command(self):
        context = helpers.MockContext()

        with self.subTest(command="wikipedia"):
            await self.cog.wikipedia(self.cog, context, search="cat")

            embed = context.send.call_args.kwargs["embed"]

            self.assertNotEqual(embed.color.value, 10038562)
            self.assertNotEqual(embed.description, "```Couldn't find any results```")

    async def covid_command(self):
        context = helpers.MockContext()

        with self.subTest(command="covid"):
            await self.cog.covid(self.cog, context)

            embed = context.send.call_args.kwargs["embed"]

            self.assertNotEqual(embed.color.value, 10038562)
            self.assertNotEqual(
                embed.description,
                "```Not a valid country\nExamples: NZ, New Zealand, all```",
            )

    async def github_command(self):
        context = helpers.MockContext()

        with self.subTest(command="github"):
            await self.cog.github(self.cog, context, username="Singularitat")

            self.assertNotEqual(
                context.send.call_args.kwargs["embed"].color.value, 10038562
            )

    async def tenor_command(self):
        context = helpers.MockContext()

        with self.subTest(command="tenor"):
            await self.cog.tenor(self.cog, context, search="cat")

            self.assertIs(context.send.call_args.kwargs.get("embed"), None)


class Background_TasksCogTests(unittest.IsolatedAsyncioTestCase):
    pass


class CryptoCogTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.cog = crypto(bot=bot)

    async def test_crypto_command(self):
        context = helpers.MockContext()
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
        context = helpers.MockContext()

        await self.cog.yeah(self.cog, context)

        context.send.assert_called_with("Oh yeah its all coming together")

    async def test_convert_command(self):
        context = helpers.MockContext()

        await self.cog.convert(self.cog, context, number=32)

        self.assertEqual(
            context.send.call_args.kwargs["embed"].description,
            "```32°F is 0.00°C```",
        )

    async def test_ones_command(self):
        context = helpers.MockContext()

        await self.cog.ones(self.cog, context, number=32)

        self.assertEqual(
            context.send.call_args.kwargs["embed"].description,
            "```011111```",
        )

    async def test_twos_command(self):
        context = helpers.MockContext()

        await self.cog.twos(self.cog, context, number=32, bits=8)

        self.assertEqual(
            context.send.call_args.kwargs["embed"].description,
            "```00100000```",
        )

    async def test_nato_command(self):
        context = helpers.MockContext()

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
        context = helpers.MockContext()

        await self.cog.embed_json(self.cog, context, message=helpers.MockMessage())

        self.assertEqual(
            context.send.call_args.kwargs["embed"].description[:61],
            '```json\n<MagicMock name="mock.embeds.__getitem__().to_dict()"',
        )

    async def test_rate_command(self):
        context = helpers.MockContext()

        await self.cog.rate(self.cog, context)

        self.assertIs(context.send.call_args.kwargs.get("embed"), None)

    async def test_ship_command(self):
        context = helpers.MockContext(
            guild=helpers.MockGuild(
                members=[helpers.MockMember(), helpers.MockMember()]
            )
        )

        await self.cog.ship(self.cog, context)

        self.assertIs(context.send.call_args.kwargs.get("embed"), None)

    async def test_match_command(self):
        context = helpers.MockContext()

        await self.cog.match(
            self.cog,
            context,
            user1=helpers.MockMember(name="Snake Bot", id=744747000293228684),
        )

        self.assertIs(context.send.call_args.kwargs.get("embed"), None)

    async def test_rle_command(self):
        context = helpers.MockContext()
        context.invoked_subcommand = None

        await self.cog.rle(self.cog, context)

        self.assertEqual(
            context.send.call_args.kwargs["embed"].description,
            f"```Usage: {context.prefix}rle [de/en]```",
        )

    async def test_rle_en_command(self):
        context = helpers.MockContext()

        await self.cog.en(self.cog, context, text="aaaabbbccd")

        self.assertEqual(context.send.call_args.args[0], "4a3b2c1d")

    async def test_rle_de_command(self):
        context = helpers.MockContext()

        await self.cog.de(self.cog, context, text="4a3b2c1d")

        self.assertEqual(context.send.call_args.args[0], "aaaabbbccd")


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
        context = helpers.MockContext()
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
        context = helpers.MockContext()

        await self.cog.calc(self.cog, context, num_base="hex", args="0x7d * 0x7d")

        self.assertEqual(
            context.send.call_args.kwargs["embed"].description,
            "```ml\n125 * 125\n\n3d09\n\nDecimal: 15625```",
        )
