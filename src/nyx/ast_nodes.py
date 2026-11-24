"""Immutable syntax tree nodes for NYX."""
from dataclasses import dataclass
from .tokens import Token


@dataclass(frozen=True, slots=True)
class Literal: value: object
@dataclass(frozen=True, slots=True)
class Variable: name: Token
@dataclass(frozen=True, slots=True)
class Unary:
    operator: Token
    right: object
@dataclass(frozen=True, slots=True)
class Binary:
    left: object
    operator: Token
    right: object
@dataclass(frozen=True, slots=True)
class Grouping: expression: object
@dataclass(frozen=True, slots=True)
class ListLiteral:
    elements: list[object]
@dataclass(frozen=True, slots=True)
class Index:
    object: object
    bracket: Token
    index: object
@dataclass(frozen=True, slots=True)
class IndexAssign:
    object: object
    bracket: Token
    index: object
    value: object
@dataclass(frozen=True, slots=True)
class Call:
    callee: object
    paren: Token
    arguments: list[object]
@dataclass(frozen=True, slots=True)
class LetStatement:
    name: Token
    initializer: object
@dataclass(frozen=True, slots=True)
class AssignStatement:
    name: Token
    value: object
@dataclass(frozen=True, slots=True)
class ExpressionStatement: expression: object
@dataclass(frozen=True, slots=True)
class PrintStatement: expression: object
@dataclass(frozen=True, slots=True)
class BlockStatement: statements: list[object]
@dataclass(frozen=True, slots=True)
class IfStatement:
    keyword: Token
    condition: object
    then_branch: BlockStatement
    else_branch: BlockStatement | None
@dataclass(frozen=True, slots=True)
class WhileStatement:
    keyword: Token
    condition: object
    body: BlockStatement
@dataclass(frozen=True, slots=True)
class FunctionStatement:
    name: Token
    parameters: list[Token]
    body: BlockStatement
@dataclass(frozen=True, slots=True)
class ReturnStatement:
    keyword: Token
    value: object | None


@dataclass(frozen=True, slots=True)
class ForStatement:
    keyword: Token
    variable: Token
    iterable: object
    body: BlockStatement
