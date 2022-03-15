import ast
import math
from decimal import Decimal


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


def logical_implication(a, b):
    return (not a) or b


def invert(a):
    return ~a


def _not(a):
    return not a


def negate(a):
    return -a


def pos(a):
    return +a


def _and(a, b):
    return a and b


def _or(a, b):
    return a or b


def safe_comb(n, k):
    if n > 10000:
        raise ValueError("Too large to calculate")
    return math.comb(n, k)


def safe_factorial(x):
    if x > 5000:
        raise ValueError("Too large to calculate")
    return math.factorial(x)


def safe_perm(n, k=None):
    if n > 5000:
        raise ValueError("Too large to calculate")
    return math.perm(n, k)


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
    ast.MatMult: logical_implication,  # This is used for the truth command for logical implications
}

BOOLOPS = {
    ast.And: _and,
    ast.Or: _or,
}

UNARYOPS = {
    ast.Invert: invert,
    ast.Not: _not,
    ast.USub: negate,
    ast.UAdd: pos,
}

CONSTANTS = {
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
}

FUNCTIONS = {
    "ceil": math.ceil,
    "comb": safe_comb,
    "fact": safe_factorial,
    "gcd": math.gcd,
    "lcm": math.lcm,
    "perm": safe_perm,
    "log": math.log,
    "log2": math.log2,
    "log10": math.log10,
    "sqrt": math.sqrt,
    "acos": math.acos,
    "asin": math.asin,
    "atan": math.atan,
    "cos": math.cos,
    "sin": math.sin,
    "tan": math.tan,
}


def bin_float(number: float):
    exponent = 0
    shifted_num = number

    while shifted_num != int(shifted_num):
        shifted_num *= 2
        exponent += 1

    if not exponent:
        return f"{int(number):b}"

    binary = f"{int(shifted_num):0{exponent + 1}b}"
    return f"{binary[:-exponent]}.{binary[-exponent:].rstrip('0')}"


def hex_float(number: float):
    exponent = 0
    shifted_num = number

    while shifted_num != int(shifted_num):
        shifted_num *= 16
        exponent += 1

    if not exponent:
        return f"{int(number):X}"

    hexadecimal = f"{int(shifted_num):0{exponent + 1}X}"
    return f"{hexadecimal[:-exponent]}.{hexadecimal[-exponent:]}"


def oct_float(number: float):
    exponent = 0
    shifted_num = number

    while shifted_num != int(shifted_num):
        shifted_num *= 8
        exponent += 1

    if not exponent:
        return f"{int(number):o}"

    octal = f"{int(shifted_num):0{exponent + 1}o}"
    return f"{octal[:-exponent]}.{octal[-exponent:]}"


def safe_eval(node):
    if isinstance(node, ast.Num):
        return node.n if isinstance(node.n, int) else Decimal(str(node.n))

    if isinstance(node, ast.UnaryOp):
        return UNARYOPS[node.op.__class__](safe_eval(node.operand))

    if isinstance(node, ast.BinOp):
        left = safe_eval(node.left)
        right = safe_eval(node.right)
        if isinstance(node.op, ast.Pow) and len(str(left)) * right > 1000:
            raise ValueError("Too large to calculate")
        return OPERATIONS[node.op.__class__](left, right)

    if isinstance(node, ast.BoolOp):
        return BOOLOPS[node.op.__class__](*[safe_eval(value) for value in node.values])

    if isinstance(node, ast.Compare):
        left = safe_eval(node.left)
        for op in node.ops:
            if not isinstance(op, ast.Eq):
                raise ValueError("Calculation failed")
        return all(left == safe_eval(comp) for comp in node.comparators)

    if isinstance(node, ast.Name):
        return CONSTANTS[node.id]

    if isinstance(node, ast.Call):
        return FUNCTIONS[node.func.id](*[safe_eval(arg) for arg in node.args])

    print(type(node))
    raise ValueError("Calculation failed")
