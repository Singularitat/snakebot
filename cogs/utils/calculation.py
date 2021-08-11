import ast


def add(a, b):
    return a + b


def sub(a, b):
    return a - b


def mul(a, b):
    return a * b


def truediv(a, b):
    return a / b


def floordiv(a, b):
    return a // b


def mod(a, b):
    return a % b


def lshift(a, b):
    return a << b


def rshift(a, b):
    return a >> b


def or_(a, b):
    return a | b


def and_(a, b):
    return a & b


def xor(a, b):
    return a ^ b


OPERATIONS = {
    ast.Add: add,
    ast.Sub: sub,
    ast.Mult: mul,
    ast.Div: truediv,
    ast.FloorDiv: floordiv,
    ast.Pow: pow,
    ast.Mod: mod,
    ast.LShift: lshift,
    ast.RShift: rshift,
    ast.BitOr: or_,
    ast.BitAnd: and_,
    ast.BitXor: xor,
}


def bin_float(number: float):
    exponent = 0
    shifted_num = number

    while shifted_num != int(shifted_num):
        shifted_num *= 2
        exponent += 1

    if not exponent:
        return bin(number).removeprefix("0b")

    binary = f"{int(shifted_num):0{exponent + 1}b}"
    return f"{binary[:-exponent]}.{binary[-exponent:].rstrip('0')}"


def hex_float(number: float):
    exponent = 0
    shifted_num = number

    while shifted_num != int(shifted_num):
        shifted_num *= 16
        exponent += 1

    if not exponent:
        return hex(number).removeprefix("0x")

    hexadecimal = f"{int(shifted_num):0{exponent + 1}x}"
    return f"{hexadecimal[:-exponent]}.{hexadecimal[-exponent:]}"


def oct_float(number: float):
    exponent = 0
    shifted_num = number

    while shifted_num != int(shifted_num):
        shifted_num *= 8
        exponent += 1

    if not exponent:
        return oct(number).removeprefix("0o")

    octal = f"{int(shifted_num):0{exponent + 1}o}"
    return f"{octal[:-exponent]}.{octal[-exponent:]}"


def safe_eval(node):
    if isinstance(node, ast.Num):
        return node.n

    if isinstance(node, ast.BinOp):
        left = safe_eval(node.left)
        right = safe_eval(node.right)
        if isinstance(node.op, ast.Pow) and len(str(left)) * right > 1000:
            raise ValueError("Too large to calculate")
        return OPERATIONS[node.op.__class__](left, right)

    raise ValueError("Calculation failed")


def calculate(expr):
    return safe_eval(ast.parse(expr, "<string>", "eval").body)
