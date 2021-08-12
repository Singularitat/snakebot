import asyncio
import unittest

from aiohttp import ClientSession

from bot import Bot
from tests.helpers import MockBot, MockContext


async def create_session():
    return ClientSession()


class BotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bot = Bot(MockBot())
        bot.load_extensions()
        cls.bot = bot
        cls.loop = asyncio.get_event_loop()
        bot.client_session = cls.loop.run_until_complete(create_session())

    def test_yeah_command(self):
        mocked_context = MockContext()

        command = self.bot.get_command("yeah")

        self.loop.run_until_complete(command.callback(self.bot, mocked_context))

        mocked_context.send.assert_called_with("Oh yeah its all coming together")

    def test_calc_command(self):
        mocked_context = MockContext()

        command = self.bot.get_command("calc")

        self.loop.run_until_complete(
            command.callback(
                self.bot, mocked_context, num_base="hex", args="0x7d * 0x7d"
            )
        )

        self.assertEqual(
            mocked_context.send.call_args.kwargs["embed"].description,
            "```ml\n125 * 125\n\n3d09\n\nDecimal: 15625```",
        )

    def test_cat_commands(self):
        mocked_context = MockContext()

        for command in ("cat", "cat2", "cat3", "cat4"):

            command = self.bot.get_command(command)

            self.loop.run_until_complete(command.callback(self.bot, mocked_context))

            self.assertEqual(
                mocked_context.send.call_args.args[0][:4],
                "http",
            )


unittest.main()
