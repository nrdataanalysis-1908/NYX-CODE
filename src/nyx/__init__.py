"""NYX — Numerical Yield eXchange language prototype."""
from .interpreter import Interpreter
from .lexer import Lexer
from .parser import Parser
from .semantic import SemanticAnalyzer

__version__ = "0.1.0a1"


def run(source: str, output=print) -> None:
    """Tokenize, parse and execute a NYX source string."""
    tokens = Lexer(source).scan_tokens()
    statements = Parser(tokens).parse()
    SemanticAnalyzer().analyze(statements)
    Interpreter(output=output).interpret(statements)


__all__ = ["Interpreter", "Lexer", "Parser", "SemanticAnalyzer", "run", "__version__"]
