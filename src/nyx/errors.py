"""Source-aware diagnostics for NYX."""


class NyxError(Exception):
    """Base class for language errors."""


class LexError(NyxError):
    """Raised when source text cannot be tokenized."""


class ParseError(NyxError):
    """Raised when tokens do not match the grammar."""


class RuntimeNyxError(NyxError):
    """Raised when a valid program fails during evaluation."""


class SemanticError(RuntimeNyxError):
    """Raised when static semantic analysis detects an invalid program."""
