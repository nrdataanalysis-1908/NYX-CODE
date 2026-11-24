"""Static semantic analysis and conservative type inference for NYX 0.8."""
from dataclasses import dataclass

from .ast_nodes import (
    AssignStatement, Binary, BlockStatement, Call, ExpressionStatement,
    ForStatement, FunctionStatement, Grouping, IfStatement, Index,
    IndexAssign, LetStatement, ListLiteral, Literal, PrintStatement,
    ReturnStatement, Unary, Variable, WhileStatement,
)
from .errors import SemanticError
from .tokens import TokenType


@dataclass(frozen=True, slots=True)
class TypeInfo:
    name: str
    element: "TypeInfo | None" = None
    members: frozenset["TypeInfo"] = frozenset()
    arity: int | None = None
    callable_name: str | None = None


INTEGER = TypeInfo("Integer")
FLOAT = TypeInfo("Float")
STRING = TypeInfo("String")
BOOLEAN = TypeInfo("Boolean")
NULL = TypeInfo("Null")
UNKNOWN = TypeInfo("Unknown")
FUNCTION = TypeInfo("Function")
LIST_UNKNOWN = TypeInfo("List", element=UNKNOWN)


def _union(types):
    flattened = set()
    for item in types:
        if item == UNKNOWN:
            return UNKNOWN
        if item.name == "Union":
            flattened.update(item.members)
        else:
            flattened.add(item)
    if not flattened:
        return UNKNOWN
    if len(flattened) == 1:
        return next(iter(flattened))
    return TypeInfo("Union", members=frozenset(flattened))


def _display(type_info):
    if type_info.name == "List":
        return f"List[{_display(type_info.element or UNKNOWN)}]"
    if type_info.name == "Union":
        return " | ".join(sorted(_display(item) for item in type_info.members))
    return type_info.name


def _is_numeric(type_info):
    if type_info in (INTEGER, FLOAT):
        return True
    return type_info.name == "Union" and all(
        item in (INTEGER, FLOAT) for item in type_info.members
    )


def _contains_numeric(type_info):
    if type_info == UNKNOWN:
        return True
    if type_info.name == "Union":
        return all(_contains_numeric(item) for item in type_info.members)
    return type_info in (INTEGER, FLOAT)


def _contains_float(type_info):
    if type_info == FLOAT:
        return True
    return type_info.name == "Union" and FLOAT in type_info.members


class SemanticAnalyzer:
    """Validate statically knowable rules without replacing runtime checks."""

    _BUILTINS = {
        "len": TypeInfo("Function", arity=1, callable_name="len"),
        "append": TypeInfo("Function", arity=2, callable_name="append"),
        "sum": TypeInfo("Function", arity=1, callable_name="sum"),
        "mean": TypeInfo("Function", arity=1, callable_name="mean"),
        "min": TypeInfo("Function", arity=1, callable_name="min"),
        "max": TypeInfo("Function", arity=1, callable_name="max"),
    }

    def __init__(self):
        self.scopes = [{}]
        self.function_depth = 0
        self.function_closures = []
        self.pending_names = []

    def analyze(self, statements):
        for statement in statements:
            self._statement(statement)
        for token, closure_scopes in self.pending_names:
            if token.lexeme not in self._BUILTINS and not any(
                token.lexeme in scope for scope in closure_scopes
            ):
                self._error(token, f"Undefined variable '{token.lexeme}'.")

    def _error(self, token, message):
        raise SemanticError(
            f"[NYX:L{token.line}:C{token.column}] {message}"
        )

    def _declare(self, token, type_info):
        scope = self.scopes[-1]
        name = token.lexeme
        if name in scope:
            self._error(token, f"Name '{name}' is already declared in this scope.")
        scope[name] = type_info

    def _resolve(self, token):
        name = token.lexeme
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        if name in self._BUILTINS:
            return self._BUILTINS[name]
        if self.function_depth:
            # Captured scope dictionaries remain live in the interpreter, so
            # declarations later in an enclosing scope may still be visible.
            self.pending_names.append((token, self.function_closures[-1]))
            return UNKNOWN
        self._error(token, f"Undefined variable '{name}'.")

    def _assign(self, token, type_info):
        name = token.lexeme
        for scope in reversed(self.scopes):
            if name in scope:
                scope[name] = _union((scope[name], type_info))
                return
        self._error(token, f"Cannot assign to undefined variable '{name}'.")

    def _statement(self, statement):
        if isinstance(statement, LetStatement):
            self._declare(statement.name, self._infer(statement.initializer))
        elif isinstance(statement, FunctionStatement):
            self._declare(
                statement.name,
                TypeInfo("Function", arity=len(statement.parameters),
                         callable_name=statement.name.lexeme),
            )
            self.function_closures.append(tuple(self.scopes))
            self.scopes.append({
                parameter.lexeme: UNKNOWN
                for parameter in statement.parameters
            })
            self.function_depth += 1
            try:
                self._statement(statement.body)
            finally:
                self.function_depth -= 1
                self.scopes.pop()
                self.function_closures.pop()
        elif isinstance(statement, ReturnStatement):
            if not self.function_depth:
                self._error(statement.keyword, "Return statement used outside a function.")
            if statement.value is not None:
                self._infer(statement.value)
        elif isinstance(statement, AssignStatement):
            self._assign(statement.name, self._infer(statement.value))
        elif isinstance(statement, IndexAssign):
            target_type = self._infer(statement.object)
            index_type = self._infer(statement.index)
            self._require_list(target_type, statement.bracket, "Indexed assignment requires a List value.")
            self._require_integer(index_type, statement.bracket)
            self._infer(statement.value)
            self._invalidate_list_element_types()
        elif isinstance(statement, PrintStatement):
            self._infer(statement.expression)
        elif isinstance(statement, ExpressionStatement):
            self._infer(statement.expression)
        elif isinstance(statement, BlockStatement):
            self.scopes.append({})
            try:
                for child in statement.statements:
                    self._statement(child)
            finally:
                self.scopes.pop()
        elif isinstance(statement, IfStatement):
            self._require_boolean(self._infer(statement.condition), statement.keyword)
            self._statement(statement.then_branch)
            if statement.else_branch is not None:
                self._statement(statement.else_branch)
        elif isinstance(statement, WhileStatement):
            self._require_boolean(self._infer(statement.condition), statement.keyword)
            self._statement(statement.body)
        elif isinstance(statement, ForStatement):
            iterable_type = self._infer(statement.iterable)
            self._require_list(
                iterable_type, statement.keyword,
                "The for loop requires a List iterable.",
            )
            element_type = (
                iterable_type.element
                if iterable_type.name == "List" and iterable_type.element
                else UNKNOWN
            )
            self.scopes.append({statement.variable.lexeme: element_type})
            try:
                self._statement(statement.body)
            finally:
                self.scopes.pop()

    def _infer(self, expression):
        if isinstance(expression, Literal):
            value = expression.value
            if type(value) is bool:
                return BOOLEAN
            if type(value) is int:
                return INTEGER
            if type(value) is float:
                return FLOAT
            if type(value) is str:
                return STRING
            if value is None:
                return NULL
        elif isinstance(expression, Grouping):
            return self._infer(expression.expression)
        elif isinstance(expression, Variable):
            return self._resolve(expression.name)
        elif isinstance(expression, ListLiteral):
            return TypeInfo(
                "List",
                element=_union(self._infer(item) for item in expression.elements),
            )
        elif isinstance(expression, Unary):
            operand = self._infer(expression.right)
            if expression.operator.type == TokenType.NOT:
                self._require_boolean(operand, expression.operator)
                return BOOLEAN
            self._require_numeric(operand, expression.operator)
            return operand
        elif isinstance(expression, Binary):
            return self._infer_binary(expression)
        elif isinstance(expression, Index):
            target_type = self._infer(expression.object)
            index_type = self._infer(expression.index)
            self._require_list(target_type, expression.bracket, "Indexing requires a List value.")
            self._require_integer(index_type, expression.bracket)
            if target_type.name == "List" and target_type.element:
                return target_type.element
            return UNKNOWN
        elif isinstance(expression, Call):
            return self._infer_call(expression)
        return UNKNOWN

    def _infer_binary(self, expression):
        operator = expression.operator
        left = self._infer(expression.left)
        kind = operator.type

        if kind in (TokenType.AND, TokenType.OR):
            self._require_boolean(left, operator)
            constant = self._constant_boolean(expression.left)
            if (kind == TokenType.AND and constant is False) or (
                kind == TokenType.OR and constant is True
            ):
                return BOOLEAN
            right = self._infer(expression.right)
            self._require_boolean(right, operator)
            return BOOLEAN

        right = self._infer(expression.right)
        if kind in (
            TokenType.PLUS, TokenType.MINUS, TokenType.STAR,
            TokenType.SLASH, TokenType.PERCENT,
        ):
            self._require_numeric(left, operator)
            self._require_numeric(right, operator)
            if kind == TokenType.SLASH or _contains_float(left) or _contains_float(right):
                return FLOAT
            if left == UNKNOWN or right == UNKNOWN:
                return UNKNOWN
            return INTEGER
        if kind in (
            TokenType.LESS, TokenType.LESS_EQUAL,
            TokenType.GREATER, TokenType.GREATER_EQUAL,
        ):
            self._require_numeric(left, operator, comparison=True)
            self._require_numeric(right, operator, comparison=True)
            return BOOLEAN
        if kind in (TokenType.EQUAL_EQUAL, TokenType.BANG_EQUAL):
            return BOOLEAN
        return UNKNOWN

    def _constant_boolean(self, expression):
        if isinstance(expression, Grouping):
            return self._constant_boolean(expression.expression)
        if isinstance(expression, Literal) and type(expression.value) is bool:
            return expression.value
        return None

    def _infer_call(self, expression):
        callee_type = self._infer(expression.callee)
        argument_types = [self._infer(arg) for arg in expression.arguments]
        if callee_type == UNKNOWN:
            return UNKNOWN
        if callee_type.name != "Function":
            self._error(expression.paren, "Only functions can be called.")
        if callee_type.arity is not None and len(argument_types) != callee_type.arity:
            self._error(
                expression.paren,
                f"Function '{callee_type.callable_name}' expects "
                f"{callee_type.arity} argument(s), got {len(argument_types)}.",
            )

        name = callee_type.callable_name
        if name == "len":
            self._require_list(argument_types[0], expression.paren, "len() expects a List value.")
            return INTEGER
        if name == "append":
            self._require_list(
                argument_types[0], expression.paren,
                "append() expects its first argument to be a List value.",
            )
            # Mutation can invalidate element-type assumptions for aliases.
            self._invalidate_list_element_types()
            return NULL
        if name in ("sum", "mean", "min", "max"):
            self._require_list(
                argument_types[0], expression.paren,
                f"{name}() expects a List value.",
            )
            list_type = argument_types[0]
            if list_type.name == "List" and list_type.element and not _contains_numeric(list_type.element):
                self._error(
                    expression.paren,
                    f"{name}() requires a List containing only numeric values.",
                )
            if name == "mean":
                return FLOAT
            if name == "sum" and list_type.name == "List" and list_type.element:
                return FLOAT if _contains_float(list_type.element) else INTEGER
            if list_type.name == "List" and list_type.element:
                return list_type.element
            return UNKNOWN
        return UNKNOWN

    def _require_numeric(self, type_info, token, comparison=False):
        if type_info != UNKNOWN and not _is_numeric(type_info):
            message = (
                "Comparison operators require numeric operands."
                if comparison else
                "Arithmetic operators require numeric operands."
            )
            self._error(token, message)

    def _require_boolean(self, type_info, token):
        if type_info not in (BOOLEAN, UNKNOWN):
            self._error(
                token,
                "Conditions and logical operators require boolean operands.",
            )

    def _require_integer(self, type_info, token):
        if type_info not in (INTEGER, UNKNOWN):
            self._error(token, "List indices must be Integer values.")

    def _require_list(self, type_info, token, message):
        if type_info not in (UNKNOWN,) and type_info.name != "List":
            self._error(token, message)

    def _invalidate_list_element_types(self):
        # Without alias analysis, any list mutation makes static element
        # assumptions unsafe. Runtime validation remains authoritative.
        for scope in self.scopes:
            for name, type_info in tuple(scope.items()):
                if type_info.name == "List":
                    scope[name] = LIST_UNKNOWN
