"""Recursive-descent parser for NYX."""
from .ast_nodes import (
    AssignStatement, Binary, BlockStatement, Call, ExpressionStatement, ForStatement, FunctionStatement, Grouping, Index, IndexAssign, ListLiteral,
    IfStatement, LetStatement, Literal, PrintStatement, ReturnStatement,
    Unary, Variable, WhileStatement,
)
from .errors import ParseError
from .tokens import Token, TokenType


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens, self.current = tokens, 0

    def parse(self):
        statements = []
        while not self._check(TokenType.EOF): statements.append(self._statement())
        return statements

    def _statement(self):
        if self._match(TokenType.FN):
            name = self._consume(TokenType.IDENTIFIER, "Expected a function name after 'fn'.")
            self._consume(TokenType.LEFT_PAREN, "Expected '(' after function name.")
            parameters = []
            if not self._check(TokenType.RIGHT_PAREN):
                while True:
                    parameters.append(self._consume(TokenType.IDENTIFIER, "Expected parameter name."))
                    if not self._match(TokenType.COMMA): break
            if len({p.lexeme for p in parameters}) != len(parameters):
                self._error(self._previous(), "A parameter cannot be declared more than once.")
            self._consume(TokenType.RIGHT_PAREN, "Expected ')' after parameters.")
            return FunctionStatement(name, parameters, self._block())
        if self._match(TokenType.RETURN):
            keyword = self._previous()
            value = None if self._check(TokenType.RIGHT_BRACE, TokenType.EOF) or self._peek().type == TokenType.SEMICOLON or self._peek().line > keyword.line else self._expression()
            self._consume_terminator("Expected ';' or a line break after return.")
            return ReturnStatement(keyword, value)
        if self._match(TokenType.LET):
            name = self._consume(TokenType.IDENTIFIER, "Expected a variable name after 'let'.")
            self._consume(TokenType.EQUAL, "Expected '=' after the variable name.")
            value = self._expression()
            self._consume_terminator("Expected ';' or a line break after the declaration.")
            return LetStatement(name, value)
        if self._match(TokenType.PRINT):
            self._consume(TokenType.LEFT_PAREN, "Expected '(' after 'print'.")
            value = self._expression()
            self._consume(TokenType.RIGHT_PAREN, "Expected ')' after the value.")
            self._consume_terminator("Expected ';' or a line break after the print statement.")
            return PrintStatement(value)
        if self._check(TokenType.IDENTIFIER):
            expression = self._expression()
            if self._match(TokenType.EQUAL):
                value = self._expression()
                self._consume_terminator("Expected ';' or a line break after the assignment.")
                if isinstance(expression, Variable):
                    return AssignStatement(expression.name, value)
                if isinstance(expression, Index):
                    return IndexAssign(expression.object, expression.bracket, expression.index, value)
                self._error(self._previous(), "The assignment target must be a variable or list element.")
            if isinstance(expression, Call):
                self._consume_terminator("Expected ';' or a line break after the function call.")
                return ExpressionStatement(expression)
            self._error(self._peek(), "Expected an assignment or function call.")
        if self._match(TokenType.IF):
            keyword = self._previous()
            self._consume(TokenType.LEFT_PAREN, "Expected '(' after 'if'.")
            condition = self._expression()
            self._consume(TokenType.RIGHT_PAREN, "Expected ')' after the if condition.")
            then_branch = self._block()
            else_branch = self._block() if self._match(TokenType.ELSE) else None
            return IfStatement(keyword, condition, then_branch, else_branch)
        if self._match(TokenType.FOR):
            keyword = self._previous()
            self._consume(TokenType.LEFT_PAREN, "Expected '(' after 'for'.")
            self._consume(TokenType.LET, "Expected 'let' before the iteration variable.")
            variable = self._consume(TokenType.IDENTIFIER, "Expected an iteration variable name.")
            self._consume(TokenType.IN, "Expected 'in' after the iteration variable.")
            iterable = self._expression()
            self._consume(TokenType.RIGHT_PAREN, "Expected ')' after the for iterable.")
            return ForStatement(keyword, variable, iterable, self._block())
        if self._match(TokenType.WHILE):
            keyword = self._previous()
            self._consume(TokenType.LEFT_PAREN, "Expected '(' after 'while'.")
            condition = self._expression()
            self._consume(TokenType.RIGHT_PAREN, "Expected ')' after the while condition.")
            return WhileStatement(keyword, condition, self._block())
        if self._match(TokenType.LEFT_BRACE): return self._block_body()
        self._error(self._peek(), "Expected a statement: declaration, function, return, assignment, print, control flow or block.")

    def _block(self):
        self._consume(TokenType.LEFT_BRACE, "Expected '{' before block.")
        return self._block_body()

    def _block_body(self):
        statements = []
        while not self._check(TokenType.RIGHT_BRACE) and not self._check(TokenType.EOF):
            statements.append(self._statement())
        self._consume(TokenType.RIGHT_BRACE, "Expected '}' after block.")
        return BlockStatement(statements)

    def _consume_terminator(self, message):
        if self._match(TokenType.SEMICOLON): return
        previous, current = self._previous(), self._peek()
        if current.type in (TokenType.EOF, TokenType.RIGHT_BRACE) or current.line > previous.line: return
        self._error(current, message)

    def _expression(self): return self._or()
    def _or(self):
        expr = self._and()
        while self._match(TokenType.OR):
            op = self._previous()
            expr = Binary(expr, op, self._and())
        return expr
    def _and(self):
        expr = self._equality()
        while self._match(TokenType.AND):
            op = self._previous()
            expr = Binary(expr, op, self._equality())
        return expr
    def _equality(self):
        expr = self._comparison()
        while self._match(TokenType.EQUAL_EQUAL, TokenType.BANG_EQUAL):
            op = self._previous()
            expr = Binary(expr, op, self._comparison())
        return expr
    def _comparison(self):
        expr = self._term()
        while self._match(TokenType.LESS, TokenType.LESS_EQUAL, TokenType.GREATER, TokenType.GREATER_EQUAL):
            op = self._previous()
            expr = Binary(expr, op, self._term())
        return expr
    def _term(self):
        expr = self._factor()
        while self._match(TokenType.PLUS, TokenType.MINUS):
            op = self._previous()
            expr = Binary(expr, op, self._factor())
        return expr
    def _factor(self):
        expr = self._unary()
        while self._match(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op = self._previous()
            expr = Binary(expr, op, self._unary())
        return expr
    def _unary(self):
        if self._match(TokenType.NOT, TokenType.MINUS, TokenType.PLUS):
            op = self._previous()
            return Unary(op, self._unary())
        return self._call()
    def _call(self):
        expr = self._primary()
        while True:
            if self._match(TokenType.LEFT_PAREN):
                paren = self._previous()
                arguments = []
                if not self._check(TokenType.RIGHT_PAREN):
                    while True:
                        arguments.append(self._expression())
                        if not self._match(TokenType.COMMA): break
                self._consume(TokenType.RIGHT_PAREN, "Expected ')' after arguments.")
                expr = Call(expr, paren, arguments)
            elif self._match(TokenType.LEFT_BRACKET):
                bracket = self._previous()
                index = self._expression()
                self._consume(TokenType.RIGHT_BRACKET, "Expected ']' after the list index.")
                expr = Index(expr, bracket, index)
            else:
                break
        return expr
    def _primary(self):
        if self._match(TokenType.FALSE): return Literal(False)
        if self._match(TokenType.TRUE): return Literal(True)
        if self._match(TokenType.NULL): return Literal(None)
        if self._match(TokenType.INTEGER, TokenType.FLOAT, TokenType.STRING): return Literal(self._previous().literal)
        if self._match(TokenType.IDENTIFIER): return Variable(self._previous())
        if self._match(TokenType.LEFT_PAREN):
            expr = self._expression()
            self._consume(TokenType.RIGHT_PAREN, "Expected ')' after expression.")
            return Grouping(expr)
        if self._match(TokenType.LEFT_BRACKET):
            elements = []
            if not self._check(TokenType.RIGHT_BRACKET):
                while True:
                    elements.append(self._expression())
                    if not self._match(TokenType.COMMA): break
                    if self._check(TokenType.RIGHT_BRACKET): break
            self._consume(TokenType.RIGHT_BRACKET, "Expected ']' after list elements.")
            return ListLiteral(elements)
        self._error(self._peek(), "Expected a literal, list, variable, call or parenthesized expression.")

    def _match(self, *types):
        if any(self._check(t) for t in types):
            self._advance()
            return True
        return False
    def _consume(self, token_type, message):
        if self._check(token_type): return self._advance()
        self._error(self._peek(), message)
    def _check(self, *types): return self._peek().type in types
    def _check_next(self, token_type):
        return self.current + 1 < len(self.tokens) and self.tokens[self.current + 1].type == token_type
    def _advance(self):
        if not self._check(TokenType.EOF): self.current += 1
        return self._previous()
    def _peek(self): return self.tokens[self.current]
    def _previous(self): return self.tokens[self.current - 1]
    def _error(self, token, message):
        raise ParseError(f"[NYX:L{token.line}:C{token.column}] {message}")
