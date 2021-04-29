import pathlib
import plyvel
import ujson


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


async def get_bal(member_id):
    """Gets the balance of an member.

    member_id: bytes
    """
    balance = bal.get(member_id)

    if balance is None:
        balance = 1000
    else:
        balance = float(balance)

    return balance


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
    encoded = str(amount).encode()
    bal.put(member_id, encoded)
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
        return ujson.loads(stock)
    return None


async def put_stock(symbol, data):
    """Sets the data of a stock.

    symbol: bytes
    """
    data = ujson.dumps(data).encode()
    stocks.put(symbol.encode(), data)


async def get_stockbal(member_id):
    """Returns a members stockbal.

    member_id: bytes
    """
    data = stockbal.get(member_id)

    if data:
        return ujson.loads(data)
    return {}


async def put_stockbal(member_id, data):
    """Sets a members stockbal.

    member_id: bytes
    """
    data = ujson.dumps(data).encode()
    stockbal.put(member_id, data)


async def get_crypto(symbol):
    """Returns the data of a crypto.

    symbol: bytes
    """
    data = crypto.get(symbol.encode())

    if data:
        return ujson.loads(data)
    return None


async def put_crypto(symbol, data):
    """Sets the data of a crypto.

    symbol: bytes
    """
    data = ujson.dumps(data).encode()
    crypto.put(symbol.encode(), data)


async def get_cryptobal(member_id):
    """Returns a members cryptobal.

    member_id: bytes
    """
    data = cryptobal.get(member_id)

    if data:
        return ujson.loads(data)
    return {}


async def put_cryptobal(member_id, data):
    """Sets a members cryptobal.

    member_id: bytes
    """
    data = ujson.dumps(data).encode()
    cryptobal.put(member_id, data)
