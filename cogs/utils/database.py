import pathlib
import plyvel
import orjson


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
)


class Database:
    def __init__(self):
        self.main = plyvel.DB(
            f"{pathlib.Path(__file__).parent.parent.parent}/db", create_if_missing=True
        )
        for db in prefixed_dbs:
            setattr(self, db, self.main.prefixed_db(f"{db}-".encode()))

    def delete_cache(self, search, cache):
        """Deletes a search from the cache.

        search: str
        """
        try:
            cache.pop(search)
        except KeyError:
            return
        self.main.put(b"cache", orjson.dumps(cache))

    async def add_karma(self, member_id, amount):
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

    async def get_blacklist(self, member_id, guild=None):
        """Returns whether someone is blacklisted.

        member_id: int
        """
        if state := self.blacklist.get(str(member_id).encode()):
            return state

        if guild and (state := self.blacklist.get(f"{guild}-{member_id}".encode())):
            return state

    async def get_bal(self, member_id):
        """Gets the balance of an member.

        member_id: bytes
        """
        balance = self.bal.get(member_id)

        if balance:
            return float(balance)

        return 1000.0

    async def put_bal(self, member_id, amount: float):
        """Sets the balance of an member.

        member_id: bytes
        amount: int
        """
        self.bal.put(member_id, str(amount).encode())
        return amount

    async def add_bal(self, member_id, amount: float):
        """Adds to the balance of an member.

        member_id: bytes
        amount: int
        """
        if amount < 0:
            raise ValueError("You can't pay a negative amount")
        return await self.put_bal(member_id, await self.get_bal(member_id) + amount)

    async def withdraw_bal(self, member_id, amount: float):
        """Withdraws from the balance of an member.

        member_id: bytes
        amount: int
        """
        if amount < 0:
            raise ValueError("You can't pay a negative amount")
        return await self.put_bal(member_id, await self.get_bal(member_id) - amount)

    async def transfer(self, _from, to, amount: float):
        """Transfers money from one member to another.

        _from: bytes
        to: bytes
        amount: int
        """
        from_bal = await self.get_bal(_from)

        if from_bal > amount:
            await self.add_bal(to, amount)
            return await self.withdraw_bal(_from, amount)

    async def get_stock(self, symbol):
        """Returns the data of a stock.

        symbol: bytes
        """
        stock = self.stocks.get(symbol.encode())

        if stock:
            return orjson.loads(stock)
        return None

    async def put_stock(self, symbol, data):
        """Sets the data of a stock.

        symbol: bytes
        data: dict
        """
        self.stocks.put(symbol.encode(), orjson.dumps(data))

    async def get_stockbal(self, member_id):
        """Returns a members stockbal.

        member_id: bytes
        """
        data = self.stockbal.get(member_id)

        if data:
            return orjson.loads(data)
        return {}

    async def put_stockbal(self, member_id, data):
        """Sets a members stockbal.

        member_id: bytes
        data: dict
        """
        self.stockbal.put(member_id, orjson.dumps(data))

    async def get_crypto(self, symbol):
        """Returns the data of a crypto.

        symbol: bytes
        """
        data = self.crypto.get(symbol.encode())

        if data:
            return orjson.loads(data)
        return None

    async def put_crypto(self, symbol, data):
        """Sets the data of a crypto.

        symbol: bytes
        data: dict
        """
        data = orjson.dumps(data)
        self.crypto.put(symbol.encode(), data)

    async def get_cryptobal(self, member_id):
        """Returns a members cryptobal.

        member_id: bytes
        """
        data = self.cryptobal.get(member_id)

        if data:
            return orjson.loads(data)
        return {}

    async def put_cryptobal(self, member_id, data):
        """Sets a members cryptobal.

        member_id: bytes
        data: dict
        """
        self.cryptobal.put(member_id, orjson.dumps(data))
