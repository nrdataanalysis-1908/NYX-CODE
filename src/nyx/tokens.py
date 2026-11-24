"""Token model for the NYX language frontend."""
from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    LET = auto()
    PRINT = auto()
    FN = auto()
    RETURN = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    IN = auto()
    IMPORT = auto()
    TRUE = auto()
    FALSE = auto()
    NULL = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    IDENTIFIER = auto()
    INTEGER = auto()
    FLOAT = auto()
    STRING = auto()
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    EQUAL = auto()
    EQUAL_EQUAL = auto()
    BANG_EQUAL = auto()
    LESS = auto()
    LESS_EQUAL = auto()
    GREATER = auto()
    GREATER_EQUAL = auto()
    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()
    LEFT_BRACE = auto()
    RIGHT_BRACE = auto()
    COMMA = auto()
    DOT = auto()
    LEFT_BRACKET = auto()
    RIGHT_BRACKET = auto()
    SEMICOLON = auto()
    EOF = auto()


@dataclass(frozen=True, slots=True)
class Token:
    type: TokenType
    lexeme: str
    literal: object
    line: int
    column: int
