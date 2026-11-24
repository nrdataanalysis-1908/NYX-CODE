"""Lexer for the NYX language."""
from .errors import LexError
from .tokens import Token, TokenType


_KEYWORDS = {
    "let": TokenType.LET, "print": TokenType.PRINT,
    "fn": TokenType.FN, "return": TokenType.RETURN,
    "if": TokenType.IF, "else": TokenType.ELSE, "while": TokenType.WHILE,
    "for": TokenType.FOR, "in": TokenType.IN,
    "true": TokenType.TRUE, "false": TokenType.FALSE, "null": TokenType.NULL,
    "and": TokenType.AND, "or": TokenType.OR, "not": TokenType.NOT,
}


class Lexer:
    def __init__(self, source: str):
        self.source = source[1:] if source.startswith("\ufeff") else source
        self.tokens: list[Token] = []
        self.start = self.current = 0
        self.line = self.column = 1
        self.start_line = self.start_column = 1

    def scan_tokens(self) -> list[Token]:
        while not self._at_end():
            self.start, self.start_line, self.start_column = self.current, self.line, self.column
            self._scan_token()
        self.tokens.append(Token(TokenType.EOF, "", None, self.line, self.column))
        return self.tokens

    def _at_end(self): return self.current >= len(self.source)

    def _advance(self):
        char = self.source[self.current]
        self.current += 1
        if char == "\n": self.line, self.column = self.line + 1, 1
        else: self.column += 1
        return char

    def _peek(self): return "\0" if self._at_end() else self.source[self.current]
    def _peek_next(self): return "\0" if self.current + 1 >= len(self.source) else self.source[self.current + 1]

    def _match(self, expected):
        if self._at_end() or self.source[self.current] != expected: return False
        self._advance()
        return True

    def _add(self, token_type, literal=None):
        self.tokens.append(Token(token_type, self.source[self.start:self.current], literal,
                                 self.start_line, self.start_column))

    def _scan_token(self):
        char = self._advance()
        single = {
            "+": TokenType.PLUS, "-": TokenType.MINUS, "*": TokenType.STAR,
            "/": TokenType.SLASH, "%": TokenType.PERCENT,
            "(": TokenType.LEFT_PAREN, ")": TokenType.RIGHT_PAREN,
            "[": TokenType.LEFT_BRACKET, "]": TokenType.RIGHT_BRACKET,
            "{": TokenType.LEFT_BRACE, "}": TokenType.RIGHT_BRACE,
            ",": TokenType.COMMA, ";": TokenType.SEMICOLON,
        }
        if char in single: self._add(single[char])
        elif char == "=": self._add(TokenType.EQUAL_EQUAL if self._match("=") else TokenType.EQUAL)
        elif char == "!":
            if self._match("="): self._add(TokenType.BANG_EQUAL)
            else: self._error("Use 'not' for logical negation; bare '!' is not supported.")
        elif char == "<": self._add(TokenType.LESS_EQUAL if self._match("=") else TokenType.LESS)
        elif char == ">": self._add(TokenType.GREATER_EQUAL if self._match("=") else TokenType.GREATER)
        elif char in " \r\t\n": return
        elif char == "#":
            while self._peek() not in ("\n", "\0"): self._advance()
        elif char == '"': self._string()
        elif char.isdigit(): self._number()
        elif char.isalpha() or char == "_": self._identifier()
        else: self._error(f"Unexpected character {char!r}.")

    def _string(self):
        value = []
        while self._peek() != '"' and not self._at_end():
            if self._peek() == "\n": self._error("String literals cannot span multiple lines.")
            if self._peek() == "\\":
                self._advance()
                escaped = self._advance() if not self._at_end() else "\0"
                translations = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}
                if escaped not in translations: self._error(f"Unsupported escape sequence \\{escaped}.")
                value.append(translations[escaped])
            else: value.append(self._advance())
        if self._at_end(): self._error("Unterminated string literal.")
        self._advance()
        self._add(TokenType.STRING, "".join(value))

    def _number(self):
        while self._peek().isdigit(): self._advance()
        is_float = False
        if self._peek() == "." and self._peek_next().isdigit():
            is_float = True
            self._advance()
            while self._peek().isdigit(): self._advance()
        raw = self.source[self.start:self.current]
        self._add(TokenType.FLOAT if is_float else TokenType.INTEGER,
                  float(raw) if is_float else int(raw))

    def _identifier(self):
        while self._peek().isalnum() or self._peek() == "_": self._advance()
        text = self.source[self.start:self.current]
        self._add(_KEYWORDS.get(text, TokenType.IDENTIFIER),
                  {"true": True, "false": False, "null": None}.get(text))

    def _error(self, message):
        raise LexError(f"[NYX:L{self.start_line}:C{self.start_column}] {message}")
