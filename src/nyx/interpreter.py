"""Tree-walk interpreter for the NYX language."""
import math as _math
import statistics as _statistics
from dataclasses import dataclass
from .ast_nodes import (
    AssignStatement, Binary, BlockStatement, Call, ExpressionStatement, ForStatement, FunctionStatement, Grouping, ImportStatement, Index, IndexAssign, ListLiteral, MemberAccess,
    IfStatement, LetStatement, Literal, PrintStatement, ReturnStatement,
    Unary, Variable, WhileStatement,
)
from .errors import RuntimeNyxError
from .tokens import TokenType


class _NyxModule:
    """A restricted namespace of explicitly registered NYX members."""
    def __init__(self, name, members):
        self.name = name
        self.members = dict(members)

    def __repr__(self): return f"<module {self.name}>"


class _NyxList:
    """Mutable list value owned by the NYX runtime."""
    def __init__(self, items):
        self.items = list(items)

    def __repr__(self):
        return "[" + ", ".join(repr(item) for item in self.items) + "]"


@dataclass
class _NativeFunction:
    name: str
    arity: int
    implementation: object

    def __repr__(self): return f"<native fn {self.name}>"


class _ReturnSignal(Exception):
    def __init__(self, value): self.value = value


@dataclass
class _UserFunction:
    declaration: FunctionStatement
    closure: tuple[dict[str, object], ...]

    def __repr__(self): return f"<fn {self.declaration.name.lexeme}>"


class Interpreter:
    def __init__(self, output=print):
        self.scopes: list[dict[str, object]] = [{}]
        self.output = output
        self.modules = self._build_standard_modules()
        self.builtins = {
            "len": _NativeFunction("len", 1, self._builtin_len),
            "append": _NativeFunction("append", 2, self._builtin_append),
            "sum": _NativeFunction("sum", 1, self._builtin_sum),
            "mean": _NativeFunction("mean", 1, self._builtin_mean),
            "min": _NativeFunction("min", 1, self._builtin_min),
            "max": _NativeFunction("max", 1, self._builtin_max),
        }


    def _build_standard_modules(self):
        def native(name, arity, implementation):
            return _NativeFunction(name, arity, implementation)

        def numeric_unary(name, function):
            def invoke(args, token):
                value = args[0]
                if type(value) not in (int, float):
                    self._runtime_error(token, f"math.{name}() expects a numeric value.")
                try:
                    return function(value)
                except (ValueError, OverflowError) as exc:
                    self._runtime_error(token, f"math.{name}(): {exc}.")
            return native(f"math.{name}", 1, invoke)

        def numeric_binary(name, function):
            def invoke(args, token):
                if any(type(value) not in (int, float) for value in args):
                    self._runtime_error(token, f"math.{name}() expects numeric values.")
                try:
                    return function(*args)
                except (ValueError, OverflowError, ZeroDivisionError) as exc:
                    self._runtime_error(token, f"math.{name}(): {exc}.")
            return native(f"math.{name}", 2, invoke)

        def numeric_values(args, token, name):
            value = args[0]
            if not isinstance(value, _NyxList):
                self._runtime_error(token, f"stats.{name}() expects a List value.")
            if any(type(item) not in (int, float) for item in value.items):
                self._runtime_error(token, f"stats.{name}() requires only numeric values.")
            if not value.items:
                self._runtime_error(token, f"stats.{name}() is undefined for an empty List.")
            return value.items

        def statistic(name, function):
            def invoke(args, token):
                values = numeric_values(args, token, name)
                try:
                    return function(values)
                except ValueError as exc:
                    self._runtime_error(token, f"stats.{name}(): {exc}.")
            return native(f"stats.{name}", 1, invoke)

        math_members = {
            "pi": _math.pi,
            "e": _math.e,
            "sqrt": numeric_unary("sqrt", _math.sqrt),
            "abs": numeric_unary("abs", abs),
            "floor": numeric_unary("floor", _math.floor),
            "ceil": numeric_unary("ceil", _math.ceil),
            "sin": numeric_unary("sin", _math.sin),
            "cos": numeric_unary("cos", _math.cos),
            "log": numeric_unary("log", _math.log),
            "pow": numeric_binary("pow", _math.pow),
        }
        stats_members = {
            "mean": statistic("mean", _statistics.mean),
            "median": statistic("median", _statistics.median),
            "variance": statistic("variance", _statistics.pvariance),
            "standard_deviation": statistic("standard_deviation", _statistics.pstdev),
        }
        return {"math": _NyxModule("math", math_members), "stats": _NyxModule("stats", stats_members)}

    def interpret(self, statements):
        try:
            for statement in statements: self._execute(statement)
        except _ReturnSignal:
            raise RuntimeNyxError("Return statement used outside a function.")

    def _execute(self, statement):
        if isinstance(statement, ImportStatement):
            name = statement.module.lexeme
            if name not in self.modules:
                self._runtime_error(statement.module, f"Module '{name}' was not found.")
            if name in self.scopes[-1]:
                self._runtime_error(statement.module, f"Name '{name}' is already declared in this scope.")
            self.scopes[-1][name] = self.modules[name]
        elif isinstance(statement, LetStatement):
            scope, name = self.scopes[-1], statement.name.lexeme
            if name in scope: self._runtime_error(statement.name, f"Variable '{name}' is already declared in this scope.")
            scope[name] = self._evaluate(statement.initializer)
        elif isinstance(statement, FunctionStatement):
            scope, name = self.scopes[-1], statement.name.lexeme
            if name in scope: self._runtime_error(statement.name, f"Name '{name}' is already declared in this scope.")
            scope[name] = _UserFunction(statement, tuple(self.scopes))
        elif isinstance(statement, ReturnStatement):
            if statement.value is None: raise _ReturnSignal(None)
            raise _ReturnSignal(self._evaluate(statement.value))
        elif isinstance(statement, AssignStatement):
            name = statement.name.lexeme
            for scope in reversed(self.scopes):
                if name in scope:
                    scope[name] = self._evaluate(statement.value)
                    break
            else: self._runtime_error(statement.name, f"Cannot assign to undefined variable '{name}'.")
        elif isinstance(statement, IndexAssign):
            target = self._evaluate(statement.object)
            index = self._evaluate(statement.index)
            value = self._evaluate(statement.value)
            self._set_index(target, index, value, statement.bracket)
        elif isinstance(statement, PrintStatement): self.output(self._evaluate(statement.expression))
        elif isinstance(statement, ExpressionStatement): self._evaluate(statement.expression)
        elif isinstance(statement, BlockStatement):
            self.scopes.append({})
            try:
                for child in statement.statements: self._execute(child)
            finally: self.scopes.pop()
        elif isinstance(statement, IfStatement):
            condition = self._evaluate(statement.condition)
            self._require_bool(condition, statement.keyword)
            if condition: self._execute(statement.then_branch)
            elif statement.else_branch is not None: self._execute(statement.else_branch)
        elif isinstance(statement, ForStatement):
            iterable = self._evaluate(statement.iterable)
            if not isinstance(iterable, _NyxList):
                self._runtime_error(statement.keyword, "The for loop requires a List iterable.")
            loop_scope = {statement.variable.lexeme: None}
            self.scopes.append(loop_scope)
            try:
                for item in tuple(iterable.items):
                    loop_scope[statement.variable.lexeme] = item
                    self._execute(statement.body)
            finally:
                self.scopes.pop()
        elif isinstance(statement, WhileStatement):
            while True:
                condition = self._evaluate(statement.condition)
                self._require_bool(condition, statement.keyword)
                if not condition: break
                self._execute(statement.body)
        else: raise RuntimeNyxError("Unsupported statement node.")

    def _evaluate(self, expression):
        if isinstance(expression, Literal): return expression.value
        if isinstance(expression, MemberAccess):
            target = self._evaluate(expression.object)
            if not isinstance(target, _NyxModule):
                self._runtime_error(expression.name, "Qualified member access requires a module value.")
            if expression.name.lexeme not in target.members:
                self._runtime_error(expression.name, f"Module '{target.name}' has no public member '{expression.name.lexeme}'.")
            return target.members[expression.name.lexeme]
        if isinstance(expression, Grouping): return self._evaluate(expression.expression)
        if isinstance(expression, Variable):
            name = expression.name.lexeme
            for scope in reversed(self.scopes):
                if name in scope: return scope[name]
            if name in self.builtins: return self.builtins[name]
            self._runtime_error(expression.name, f"Undefined variable '{name}'.")
        if isinstance(expression, Unary):
            right = self._evaluate(expression.right)
            if expression.operator.type == TokenType.NOT:
                self._require_bool(right, expression.operator)
                return not right
            self._require_number(right, expression.operator)
            return -right if expression.operator.type == TokenType.MINUS else right
        if isinstance(expression, Binary): return self._binary(expression)
        if isinstance(expression, ListLiteral):
            return _NyxList([self._evaluate(element) for element in expression.elements])
        if isinstance(expression, Index):
            target = self._evaluate(expression.object)
            index = self._evaluate(expression.index)
            return self._get_index(target, index, expression.bracket)
        if isinstance(expression, Call): return self._call(expression)
        raise RuntimeNyxError("Unsupported expression node.")

    def _call(self, expression):
        callee = self._evaluate(expression.callee)
        if isinstance(callee, _NativeFunction):
            if len(expression.arguments) != callee.arity:
                self._runtime_error(expression.paren, f"Function '{callee.name}' expects {callee.arity} argument(s), got {len(expression.arguments)}.")
            arguments = [self._evaluate(arg) for arg in expression.arguments]
            return callee.implementation(arguments, expression.paren)
        if not isinstance(callee, _UserFunction):
            self._runtime_error(expression.paren, "Only functions can be called.")
        expected = len(callee.declaration.parameters)
        if len(expression.arguments) != expected:
            self._runtime_error(expression.paren, f"Function '{callee.declaration.name.lexeme}' expects {expected} argument(s), got {len(expression.arguments)}.")
        arguments = [self._evaluate(arg) for arg in expression.arguments]
        parameter_scope = {p.lexeme: value for p, value in zip(callee.declaration.parameters, arguments)}
        previous_scopes = self.scopes
        self.scopes = [*callee.closure, parameter_scope]
        try:
            try:
                self._execute(callee.declaration.body)
            except _ReturnSignal as signal:
                return signal.value
            return None
        finally:
            self.scopes = previous_scopes

    def _builtin_len(self, arguments, token):
        value = arguments[0]
        if not isinstance(value, _NyxList):
            self._runtime_error(token, "len() expects a List value.")
        return len(value.items)

    def _builtin_append(self, arguments, token):
        target, value = arguments
        if not isinstance(target, _NyxList):
            self._runtime_error(token, "append() expects its first argument to be a List value.")
        target.items.append(value)
        return None

    def _numeric_list(self, value, token, function_name):
        if not isinstance(value, _NyxList):
            self._runtime_error(token, f"{function_name}() expects a List value.")
        if any(type(item) not in (int, float) for item in value.items):
            self._runtime_error(token, f"{function_name}() requires a List containing only numeric values.")
        return value.items

    def _builtin_sum(self, arguments, token):
        values = self._numeric_list(arguments[0], token, "sum")
        return sum(values)

    def _builtin_mean(self, arguments, token):
        values = self._numeric_list(arguments[0], token, "mean")
        if not values:
            self._runtime_error(token, "mean() is undefined for an empty List.")
        return sum(values) / len(values)

    def _builtin_min(self, arguments, token):
        values = self._numeric_list(arguments[0], token, "min")
        if not values:
            self._runtime_error(token, "min() is undefined for an empty List.")
        return min(values)

    def _builtin_max(self, arguments, token):
        values = self._numeric_list(arguments[0], token, "max")
        if not values:
            self._runtime_error(token, "max() is undefined for an empty List.")
        return max(values)

    def _get_index(self, target, index, token):
        if not isinstance(target, _NyxList):
            self._runtime_error(token, "Indexing requires a List value.")
        if type(index) is not int:
            self._runtime_error(token, "List indices must be Integer values.")
        if index < 0 or index >= len(target.items):
            self._runtime_error(token, f"List index {index} is out of range for length {len(target.items)}.")
        return target.items[index]

    def _set_index(self, target, index, value, token):
        if not isinstance(target, _NyxList):
            self._runtime_error(token, "Indexed assignment requires a List value.")
        if type(index) is not int:
            self._runtime_error(token, "List indices must be Integer values.")
        if index < 0 or index >= len(target.items):
            self._runtime_error(token, f"List index {index} is out of range for length {len(target.items)}.")
        target.items[index] = value

    def _binary(self, expression):
        op = expression.operator
        left = self._evaluate(expression.left)
        if op.type == TokenType.OR:
            self._require_bool(left, op)
            return left or self._logical_right(expression.right, op)
        if op.type == TokenType.AND:
            self._require_bool(left, op)
            return left and self._logical_right(expression.right, op)
        right = self._evaluate(expression.right)
        if op.type in (TokenType.PLUS, TokenType.MINUS, TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            self._require_number(left, op)
            self._require_number(right, op)
            if op.type == TokenType.PLUS: return left + right
            if op.type == TokenType.MINUS: return left - right
            if op.type == TokenType.STAR: return left * right
            if op.type == TokenType.SLASH:
                if right == 0: self._runtime_error(op, "Division by zero.")
                return left / right
            if right == 0: self._runtime_error(op, "Modulo by zero.")
            return left % right
        if op.type in (TokenType.LESS, TokenType.LESS_EQUAL, TokenType.GREATER, TokenType.GREATER_EQUAL):
            if type(left) not in (int, float) or type(right) not in (int, float):
                self._runtime_error(op, "Comparison operators require numeric operands.")
            return {TokenType.LESS: left < right, TokenType.LESS_EQUAL: left <= right,
                    TokenType.GREATER: left > right, TokenType.GREATER_EQUAL: left >= right}[op.type]
        if op.type in (TokenType.EQUAL_EQUAL, TokenType.BANG_EQUAL):
            equal = self._values_equal(left, right)
            return equal if op.type == TokenType.EQUAL_EQUAL else not equal
        self._runtime_error(op, "Unsupported binary operator.")

    def _values_equal(self, left, right):
        if isinstance(left, _NyxList) and isinstance(right, _NyxList):
            return len(left.items) == len(right.items) and all(
                self._values_equal(a, b) for a, b in zip(left.items, right.items)
            )
        return type(left) is type(right) and left == right

    def _logical_right(self, expression, operator):
        value = self._evaluate(expression)
        self._require_bool(value, operator)
        return value
    def _require_number(self, value, token):
        if type(value) not in (int, float): self._runtime_error(token, "Arithmetic operators require numeric operands.")
    def _require_bool(self, value, token):
        if type(value) is not bool: self._runtime_error(token, "Conditions and logical operators require boolean operands.")
    def _runtime_error(self, token, message):
        raise RuntimeNyxError(f"[NYX:L{token.line}:C{token.column}] {message}")
