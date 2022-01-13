from TagScriptEngine import Interpreter
from TagScriptEngine.block import MathBlock

interpreter = Interpreter([MathBlock()])


def calc_from_string(s: str) -> float:
    """
    Calculate a mathematical expression from a string.

    Only accepts 0123456789.+-*/() and will otherwise error with RuntimeError.

    Possible math errors raised: ValueError, OverflowError, RuntimeError.

    ** is not supported.
    """
    safe_chars = "0123456789.+-*/()"
    if s.find("**") != -1:
        raise RuntimeError("** is not supported.")
    for char in s:
        if char not in safe_chars:
            raise RuntimeError(f"Invalid character '{char}' in expression.")

    return float(interpreter.process("{math:" + s + "}").body)
