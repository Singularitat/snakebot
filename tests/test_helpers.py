import asyncio
import unittest
import unittest.mock

import discord
import helpers


class DiscordMocksTests(unittest.TestCase):
    def test_mock_role_default_initialization(self):
        role = helpers.MockRole()

        # The `spec` argument makes sure `isistance` checks with `discord.Role` pass
        self.assertIsInstance(role, discord.Role)

        self.assertEqual(role.name, "role")
        self.assertEqual(role.position, 1)
        self.assertEqual(role.mention, "&role")

    def test_mock_role_alternative_arguments(self):
        role = helpers.MockRole(
            name="Admins",
            id=90210,
            position=10,
        )

        self.assertEqual(role.name, "Admins")
        self.assertEqual(role.id, 90210)
        self.assertEqual(role.position, 10)
        self.assertEqual(role.mention, "&Admins")

    def test_mock_role_accepts_dynamic_arguments(self):
        role = helpers.MockRole(
            guild="Dino Man",
            hoist=True,
        )

        self.assertEqual(role.guild, "Dino Man")
        self.assertTrue(role.hoist)

    def test_mock_role_uses_position_for_less_than_greater_than(self):
        role_one = helpers.MockRole(position=1)
        role_two = helpers.MockRole(position=2)
        role_three = helpers.MockRole(position=3)

        self.assertLess(role_one, role_two)
        self.assertLess(role_one, role_three)
        self.assertLess(role_two, role_three)
        self.assertGreater(role_three, role_two)
        self.assertGreater(role_three, role_one)
        self.assertGreater(role_two, role_one)

    def test_mock_member_default_initialization(self):
        member = helpers.MockMember()

        # The `spec` argument makes sure `isistance` checks with `discord.Member` pass
        self.assertIsInstance(member, discord.Member)

        self.assertEqual(member.name, "member")
        self.assertListEqual(
            member.roles, [helpers.MockRole(name="@everyone", position=1, id=0)]
        )
        self.assertEqual(member.mention, "@member")

    def test_mock_member_alternative_arguments(self):
        core_developer = helpers.MockRole(name="Core Developer", position=2)
        member = helpers.MockMember(name="Mark", id=12345, roles=[core_developer])

        self.assertEqual(member.name, "Mark")
        self.assertEqual(member.id, 12345)
        self.assertListEqual(
            member.roles,
            [helpers.MockRole(name="@everyone", position=1, id=0), core_developer],
        )
        self.assertEqual(member.mention, "@Mark")

    def test_mock_member_accepts_dynamic_arguments(self):
        member = helpers.MockMember(
            nick="Dino Man",
            colour=discord.Colour.default(),
        )

        self.assertEqual(member.nick, "Dino Man")
        self.assertEqual(member.colour, discord.Colour.default())

    def test_mock_guild_default_initialization(self):
        guild = helpers.MockGuild()

        # The `spec` argument makes sure `isistance` checks with `discord.Guild` pass
        self.assertIsInstance(guild, discord.Guild)

        self.assertListEqual(
            guild.roles, [helpers.MockRole(name="@everyone", position=1, id=0)]
        )
        self.assertListEqual(guild.members, [])

    def test_mock_guild_alternative_arguments(self):
        core_developer = helpers.MockRole(name="Core Developer", position=2)
        guild = helpers.MockGuild(
            roles=[core_developer],
            members=[helpers.MockMember(id=54321)],
        )

        self.assertListEqual(
            guild.roles,
            [helpers.MockRole(name="@everyone", position=1, id=0), core_developer],
        )
        self.assertListEqual(guild.members, [helpers.MockMember(id=54321)])

    def test_mock_guild_accepts_dynamic_arguments(self):
        guild = helpers.MockGuild(
            emojis=(":hyperjoseph:", ":pensive_ela:"),
            premium_subscription_count=15,
        )

        self.assertTupleEqual(guild.emojis, (":hyperjoseph:", ":pensive_ela:"))
        self.assertEqual(guild.premium_subscription_count, 15)

    def test_mock_bot_default_initialization(self):
        bot = helpers.MockBot()

        # The `spec` argument makes sure `isistance` checks with `discord.ext.commands.Bot` pass
        self.assertIsInstance(bot, discord.ext.commands.Bot)

    def test_mock_context_default_initialization(self):
        context = helpers.MockContext()

        # The `spec` argument makes sure `isistance` checks with `discord.ext.commands.Context` pass
        self.assertIsInstance(context, discord.ext.commands.Context)

        self.assertIsInstance(context.bot, helpers.MockBot)
        self.assertIsInstance(context.guild, helpers.MockGuild)
        self.assertIsInstance(context.author, helpers.MockMember)

    def test_mocks_allows_access_to_attributes_part_of_spec(self):
        mocks = (
            (helpers.MockGuild(), "name"),
            (helpers.MockRole(), "hoist"),
            (helpers.MockMember(), "display_name"),
            (helpers.MockBot(), "user"),
            (helpers.MockContext(), "invoked_with"),
            (helpers.MockTextChannel(), "last_message"),
            (helpers.MockMessage(), "mention_everyone"),
        )

        for mock, valid_attribute in mocks:
            with self.subTest(mock=mock):
                try:
                    getattr(mock, valid_attribute)
                except AttributeError:
                    msg = f"accessing valid attribute `{valid_attribute}` raised an AttributeError"
                    self.fail(msg)

    @unittest.mock.patch(f"{__name__}.DiscordMocksTests.subTest")
    @unittest.mock.patch(f"{__name__}.getattr")
    def test_mock_allows_access_to_attributes_test(self, mock_getattr, mock_subtest):
        mock_getattr.side_effect = AttributeError

        msg = "accessing valid attribute `name` raised an AttributeError"
        with self.assertRaises(AssertionError, msg=msg):
            self.test_mocks_allows_access_to_attributes_part_of_spec()

    def test_mocks_rejects_access_to_attributes_not_part_of_spec(self):
        mocks = (
            helpers.MockGuild(),
            helpers.MockRole(),
            helpers.MockMember(),
            helpers.MockBot(),
            helpers.MockContext(),
            helpers.MockTextChannel(),
            helpers.MockMessage(),
        )

        for mock in mocks:
            with self.subTest(mock=mock), self.assertRaises(AttributeError):
                mock.the_cake_is_a_lie

    def test_mocks_use_mention_when_provided_as_kwarg(self):
        test_cases = (
            (helpers.MockRole, "role mention"),
            (helpers.MockMember, "member mention"),
            (helpers.MockTextChannel, "channel mention"),
        )

        for mock_type, mention in test_cases:
            with self.subTest(mock_type=mock_type, mention=mention):
                mock = mock_type(mention=mention)
                self.assertEqual(mock.mention, mention)

    def test_create_test_on_mock_bot_closes_passed_coroutine(self):
        async def dementati():
            """Dummy coroutine for testing purposes."""

        coroutine_object = dementati()

        bot = helpers.MockBot()
        bot.loop.create_task(coroutine_object)
        with self.assertRaises(
            RuntimeError, msg="cannot reuse already awaited coroutine"
        ):
            asyncio.run(coroutine_object)

    def test_user_mock_uses_explicitly_passed_mention_attribute(self):
        user = helpers.MockUser(mention="hello")
        self.assertEqual(user.mention, "hello")


class MockObjectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hashable_mocks = (helpers.MockRole, helpers.MockMember, helpers.MockGuild)

    def test_colour_mixin(self):
        class MockHemlock(unittest.mock.MagicMock, helpers.ColourMixin):
            pass

        hemlock = MockHemlock()
        hemlock.color = 1
        self.assertEqual(hemlock.colour, 1)
        self.assertEqual(hemlock.colour, hemlock.color)

    def test_hashable_mixin_hash_returns_id(self):
        class MockScragly(unittest.mock.Mock, helpers.HashableMixin):
            pass

        scragly = MockScragly()
        scragly.id = 10
        self.assertEqual(hash(scragly), scragly.id)

    def test_hashable_mixin_uses_id_for_equality_comparison(self):
        class MockScragly(helpers.HashableMixin):
            pass

        scragly = MockScragly()
        scragly.id = 10
        eevee = MockScragly()
        eevee.id = 10
        python = MockScragly()
        python.id = 20

        self.assertTrue(scragly == eevee)
        self.assertFalse(scragly == python)

    def test_hashable_mixin_uses_id_for_nonequality_comparison(self):
        class MockScragly(helpers.HashableMixin):
            pass

        scragly = MockScragly()
        scragly.id = 10
        eevee = MockScragly()
        eevee.id = 10
        python = MockScragly()
        python.id = 20

        self.assertTrue(scragly != python)
        self.assertFalse(scragly != eevee)

    def test_mock_class_with_hashable_mixin_uses_id_for_hashing(self):
        for mock in self.hashable_mocks:
            with self.subTest(mock_class=mock):
                instance = helpers.MockRole(id=100)
                self.assertEqual(hash(instance), instance.id)

    def test_mock_class_with_hashable_mixin_uses_id_for_equality(self):
        for mock_class in self.hashable_mocks:
            with self.subTest(mock_class=mock_class):
                instance_one = mock_class()
                instance_two = mock_class()
                instance_three = mock_class()

                instance_one.id = 10
                instance_two.id = 10
                instance_three.id = 20

                self.assertTrue(instance_one == instance_two)
                self.assertFalse(instance_one == instance_three)

    def test_mock_class_with_hashable_mixin_uses_id_for_nonequality(self):
        for mock_class in self.hashable_mocks:
            with self.subTest(mock_class=mock_class):
                instance_one = mock_class()
                instance_two = mock_class()
                instance_three = mock_class()

                instance_one.id = 10
                instance_two.id = 10
                instance_three.id = 20

                self.assertFalse(instance_one != instance_two)
                self.assertTrue(instance_one != instance_three)

    def test_custom_mock_mixin_accepts_mock_seal(self):
        class MyMock(helpers.CustomMockMixin, unittest.mock.MagicMock):
            child_mock_type = unittest.mock.MagicMock

        mock = MyMock()
        unittest.mock.seal(mock)
        with self.assertRaises(AttributeError, msg="MyMock.shirayuki"):
            mock.shirayuki = "hello!"

    def test_spec_propagation_of_mock_subclasses(self):
        test_values = (
            (helpers.MockRole, "mentionable"),
            (helpers.MockMember, "display_name"),
            (helpers.MockBot, "owner_id"),
            (helpers.MockContext, "command_failed"),
            (helpers.MockMessage, "mention_everyone"),
            (helpers.MockEmoji, "managed"),
            (helpers.MockPartialEmoji, "url"),
            (helpers.MockReaction, "me"),
        )

        for mock_type, valid_attribute in test_values:
            with self.subTest(mock_type=mock_type, attribute=valid_attribute):
                mock = mock_type()
                self.assertTrue(isinstance(mock, mock_type))
                attribute = getattr(mock, valid_attribute)
                self.assertTrue(isinstance(attribute, mock_type.child_mock_type))

    def test_custom_mock_mixin_mocks_async_magic_methods_with_async_mock(self):
        class MyMock(helpers.CustomMockMixin, unittest.mock.MagicMock):
            pass

        mock = MyMock()
        self.assertIsInstance(mock.__aenter__, unittest.mock.AsyncMock)


if __name__ == "__main__":
    unittest.main()
