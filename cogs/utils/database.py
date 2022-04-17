import pathlib
from decimal import Decimal

import orjson
import plyvel

prefixed_dbs = (
    "infractions",
    "karma",
    "blacklist",
    "rrole",
    "deleted",
    "edited",
    "invites",
    "nicks",
    "cryptobal",
    "crypto",
    "stocks",
    "stockbal",
    "bal",
    "wins",
    "message_count",
    "cookies",
    "reminders",
    "docs",
    "trivia_wins",
)


class Database:
    def __init__(self):
        self.main = plyvel.DB(
            f"{pathlib.Path(__file__).parent.parent.parent}/db", create_if_missing=True
        )
        for db in prefixed_dbs:
            setattr(self, db, self.main.prefixed_db(f"{db}-".encode()))

    def add_karma(self, member_id, amount):
        """Adds or removes an amount from a members karma.

        member_id: int
        amount: int
        """
        member_id = str(member_id).encode()
        member_karma = self.karma.get(member_id)

        if not member_karma:
            member_karma = amount
        else:
            member_karma = int(member_karma) + amount

        self.karma.put(member_id, str(member_karma).encode())

    def get_blacklist(self, member_id, guild=None):
        """Returns whether someone is blacklisted.

        member_id: int
        """
        if state := self.blacklist.get(str(member_id).encode()):
            return state

        if guild and (state := self.blacklist.get(f"{guild}-{member_id}".encode())):
            return state

    def get_bal(self, member_id):
        """Gets the balance of an member.

        member_id: bytes
        """
        balance = self.bal.get(member_id)

        if balance:
            return Decimal(balance.decode())

        return Decimal(1000.0)

    def put_bal(self, member_id, balance: float):
        """Sets the balance of an member.

        member_id: bytes
        balance: float
        """
        self.bal.put(member_id, f"{balance:50f}".rstrip("0").encode())
        return balance

    def add_bal(self, member_id, amount: float):
        """Adds to the balance of an member.

        member_id: bytes
        amount: int
        """
        if amount < 0:
            raise ValueError("You can't pay a negative amount")
        return self.put_bal(member_id, self.get_bal(member_id) + Decimal(amount))

    def get_stock(self, symbol):
        """Returns the data of a stock.

        symbol: bytes
        """
        stock = self.stocks.get(symbol.encode())

        if stock:
            return orjson.loads(stock)
        return None

    def put_stock(self, symbol, data):
        """Sets the data of a stock.

        symbol: bytes
        data: dict
        """
        self.stocks.put(symbol.encode(), orjson.dumps(data))

    def get_stockbal(self, member_id):
        """Returns a members stockbal.

        member_id: bytes
        """
        data = self.stockbal.get(member_id)

        if data:
            return orjson.loads(data)
        return {}

    def put_stockbal(self, member_id, data):
        """Sets a members stockbal.

        member_id: bytes
        data: dict
        """
        self.stockbal.put(member_id, orjson.dumps(data))

    def get_crypto(self, symbol):
        """Returns the data of a crypto.

        symbol: bytes
        """
        data = self.crypto.get(symbol.encode())

        if data:
            return orjson.loads(data)
        return None

    def put_crypto(self, symbol, data):
        """Sets the data of a crypto.

        symbol: bytes
        data: dict
        """
        data = orjson.dumps(data)
        self.crypto.put(symbol.encode(), data)

    def get_cryptobal(self, member_id):
        """Returns a members cryptobal.

        member_id: bytes
        """
        data = self.cryptobal.get(member_id)

        if data:
            return orjson.loads(data)
        return {}

    def put_cryptobal(self, member_id, data):
        """Sets a members cryptobal.

        member_id: bytes
        data: dict
        """
        self.cryptobal.put(member_id, orjson.dumps(data))
