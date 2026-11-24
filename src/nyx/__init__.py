"""NYX — Numerical Yield eXchange language prototype."""
from .interpreter import Interpreter
from .lexer import Lexer
from .parser import Parser
from .semantic import SemanticAnalyzer

__version__ = "0.1.0a1"


def run(source: str, output=print, source_path=None) -> None:
    """Tokenize, analyze, and execute source; source_path enables local imports."""
    tokens = Lexer(source).scan_tokens()
    statements = Parser(tokens).parse()
    SemanticAnalyzer(allow_project_modules=source_path is not None).analyze(statements)
    Interpreter(output=output, source_path=source_path).interpret(statements)


__all__ = ["Interpreter", "Lexer", "Parser", "SemanticAnalyzer", "run", "__version__"]
