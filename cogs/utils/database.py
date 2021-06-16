import pathlib
import plyvel
import orjson


db = plyvel.DB(
    f"{pathlib.Path(__file__).parent.parent.parent}/db", create_if_missing=True
)
infractions = db.prefixed_db(b"infractions-")
karma = db.prefixed_db(b"karma-")
blacklist = db.prefixed_db(b"blacklist-")
rrole = db.prefixed_db(b"rrole-")
deleted = db.prefixed_db(b"deleted-")
edited = db.prefixed_db(b"edited-")
invites = db.prefixed_db(b"invites-")
nicks = db.prefixed_db(b"nicks-")
cryptobal = db.prefixed_db(b"cryptobal-")
crypto = db.prefixed_db(b"crypto-")
stocks = db.prefixed_db(b"stocks-")
stockbal = db.prefixed_db(b"stockbal-")
bal = db.prefixed_db(b"bal-")
wins = db.prefixed_db(b"wins-")
message_count = db.prefixed_db(b"message_count-")


@staticmethod
def delete_cache(search, cache):
    """Deletes a search from the cache.

    search: str
    """
    try:
        cache.pop(search)
    except KeyError:
        return
    DB.db.put(b"cache", orjson.dumps(cache))


async def add_karma(member_id, amount):
    """Adds or removes an amount from a members karma.

    member_id: int
    amount: int
    """
    member_id = str(member_id).encode()
    member_karma = karma.get(member_id)

    if not member_karma:
        member_karma = amount
    else:
        member_karma = int(member_karma) + amount

    karma.put(member_id, str(member_karma).encode())


async def get_blacklist(member_id, guild=None):
    """Returns whether someone is blacklisted.

    member_id: int
    """
    if state := blacklist.get(str(member_id).encode()):
        return state

    if guild and (state := blacklist.get(f"{guild}-{member_id}".encode())):
        return state


async def get_bal(member_id):
    """Gets the balance of an member.

    member_id: bytes
    """
    balance = bal.get(member_id)

    if balance:
        return float(balance)

    return 1000.0


async def get_baltop(amount: int):
    """Gets the top [amount] balances.

    amount: int
    """
    return sorted([(float(b), int(m)) for m, b in bal], reverse=True)[:amount]


async def put_bal(member_id, amount: float):
    """Sets the balance of an member.

    member_id: bytes
    amount: int
    """
    bal.put(member_id, str(amount).encode())
    return amount


async def add_bal(member_id, amount: float):
    """Adds to the balance of an member.

    member_id: bytes
    amount: int
    """
    if amount < 0:
        raise ValueError("You can't pay a negative amount")
    return await put_bal(member_id, await get_bal(member_id) + amount)


async def withdraw_bal(member_id, amount: float):
    """Withdraws from the balance of an member.

    member_id: bytes
    amount: int
    """
    if amount < 0:
        raise ValueError("You can't pay a negative amount")
    return await put_bal(member_id, await get_bal(member_id) - amount)


async def transfer(_from, to, amount: float):
    """Transfers money from one member to another.

    _from: bytes
    to: bytes
    amount: int
    """
    from_bal = await get_bal(_from)

    if from_bal > amount:
        await add_bal(to, amount)
        return await withdraw_bal(_from, amount)


async def get_stock(symbol):
    """Returns the data of a stock.

    symbol: bytes
    """
    stock = stocks.get(symbol.encode())

    if stock:
        return orjson.loads(stock)
    return None


async def put_stock(symbol, data):
    """Sets the data of a stock.

    symbol: bytes
    data: dict
    """
    stocks.put(symbol.encode(), orjson.dumps(data))


async def get_stockbal(member_id):
    """Returns a members stockbal.

    member_id: bytes
    """
    data = stockbal.get(member_id)

    if data:
        return orjson.loads(data)
    return {}


async def put_stockbal(member_id, data):
    """Sets a members stockbal.

    member_id: bytes
    data: dict
    """
    stockbal.put(member_id, orjson.dumps(data))


async def get_crypto(symbol):
    """Returns the data of a crypto.

    symbol: bytes
    """
    data = crypto.get(symbol.encode())

    if data:
        return orjson.loads(data)
    return None


async def put_crypto(symbol, data):
    """Sets the data of a crypto.

    symbol: bytes
    data: dict
    """
    data = orjson.dumps(data)
    crypto.put(symbol.encode(), data)


async def get_cryptobal(member_id):
    """Returns a members cryptobal.

    member_id: bytes
    """
    data = cryptobal.get(member_id)

    if data:
        return orjson.loads(data)
    return {}


async def put_cryptobal(member_id, data):
    """Sets a members cryptobal.

    member_id: bytes
    data: dict
    """
    cryptobal.put(member_id, orjson.dumps(data))
