# NYX Type System and Semantic Analysis Design

- Document ID: NYX-TYPE-DESIGN
- Target milestone: NYX 0.8
- Status: Implemented incrementally in the NYX 0.8 alpha
- Project: NR TECH
- Normative language: English

## 1. Purpose

NYX 0.8 introduces a semantic-analysis layer between parsing and execution. Its purpose is to detect statically knowable program errors before the interpreter evaluates the program, while establishing type contracts that can support numerical, statistical, and scientific abstractions in later releases.

The initial conservative analyzer and type-inference layer described here are implemented in the NYX 0.8 development branch. The design remains a living specification: inference is intentionally partial, and the limitations below are still applicable.

## 2. Design principles

1. Preserve the independence of NYX syntax, semantics, and runtime from its Python-hosted prototype.
2. Reject errors only when the analyzer has sufficient static evidence.
3. Preserve runtime checks for values whose types cannot be established statically.
4. Make numeric promotion explicit and deterministic.
5. Keep heterogeneous general-purpose lists distinct from future homogeneous scientific vectors and matrices.
6. Attach diagnostics to source locations and keep messages actionable.
7. Avoid implicit conversions that silently lose precision or change meaning.

## 3. Initial type model

The initial semantic model recognizes:

| Type | Meaning |
|---|---|
| Integer | Exact integer value |
| Float | IEEE 754 binary64 value |
| String | UTF-8 text |
| Boolean | true or false |
| Null | Absence of a value |
| List | Mutable, potentially heterogeneous collection |
| Function | Callable user-defined or native function |
| Unknown | Type cannot currently be established statically |

Unknown is an analysis state, not a runtime value. It prevents the analyzer from inventing certainty for dynamic inputs.

Future scientific types such as Vector, Matrix, Tensor, and DataFrame must have their own documented contracts. They must not be aliases for the existing heterogeneous List type.

## 4. Numeric rules

- Integer and Float are numeric types.
- Mixed Integer/Float arithmetic promotes to Float.
- Integer-only addition, subtraction, and multiplication produce Integer.
- Division produces Float.
- Modulo follows the numeric promotion rule of its operands.
- Boolean is never a numeric subtype of Integer.
- No implicit conversion from String, Boolean, or Null to a numeric type is permitted.
- Runtime checks remain mandatory for division and modulo by zero.

The analyzer must not promise exact decimal arithmetic: Float remains binary64 unless a future Decimal type is specified.

## 5. Inference and compatibility

The initial release uses inference rather than requiring type annotations in source code.

- Literal expressions have known types.
- Arithmetic, comparisons, logical expressions, and list literals derive types from their operands.
- An empty list has element type Unknown.
- A heterogeneous list is represented as List with an element-type set or Unknown element type; it is not forced into a homogeneous numeric type.
- Variables and assignments are analyzed using lexical scopes.
- Where control-flow paths produce different possible types, the analyzer must conservatively retain the union or Unknown rather than selecting one path arbitrarily.
- Function parameters and return values remain Unknown unless they can be inferred safely from the available program. Runtime validation remains authoritative for unresolved cases.

The first implementation must document exactly which inferences it supports. It must not claim full interprocedural inference.

## 6. Semantic checks

The analyzer is expected to validate, where statically knowable:

- use of undefined identifiers;
- duplicate declarations in the same lexical scope;
- return statements outside functions;
- Boolean requirements for if, while, and logical operators;
- numeric requirements for arithmetic and ordered comparisons;
- list requirements for for-in iteration and list indexing;
- Integer requirements for list indices;
- function callability and known arity;
- native function arity and statically knowable argument constraints;
- incompatible operations between known operand types.

Checks involving dynamic values must remain guarded by runtime validation.

## 7. Execution pipeline

The target pipeline is:

Source -> Lexer -> Tokens -> Parser -> AST -> Semantic Analyzer -> Typed/validated AST metadata -> Interpreter

The first implementation may keep the existing AST immutable and store inferred types in analyzer-owned metadata keyed by node identity. The analyzer must not mutate runtime values or duplicate execution semantics. The current implementation keeps inferred type metadata inside the analyzer and does not mutate the AST.

The interpreter remains responsible for execution, mutation, bounds checking, division by zero, and any condition the analyzer cannot prove statically.

## 8. Diagnostics

Semantic errors must use the same source-location convention as lexical and parsing diagnostics:

`[NYX:L<line>:C<column>]`

A diagnostic should identify:
- the offending expression or identifier;
- the expected type or semantic rule;
- the actual known type, when available;
- the source location.

The analyzer should report the first deterministic error initially. Multi-error recovery can be introduced only with explicit parser/analyzer recovery rules.

## 9. Compatibility and migration

NYX 0.8 must preserve valid programs from 0.7 unless a behavior is explicitly documented as a language correction. Static checks should not reject a program merely because its type is Unknown.

Existing runtime checks remain in place. The analyzer is an additional validation stage, not a replacement for runtime safety.

## 10. Acceptance criteria

The initial semantic-analysis increment is considered complete only when:

1. The analyzer is a separate module and does not depend on interpreter internals.
2. Scope resolution follows the language's lexical-scope rules.
3. Supported type inference and operator rules are documented.
4. Statically provable invalid programs fail before interpreter execution.
5. Dynamic or Unknown cases continue to use runtime checks.
6. Diagnostics include line and column.
7. Regression tests cover existing 0.7 behavior and new positive, negative, and edge cases.
8. CI passes on all supported Python versions.
9. README, language specification, and roadmap accurately distinguish implemented features from planned work.

## 11. Explicitly out of scope for the first 0.8 increment

- Mandatory type annotations in source code;
- generics and parametric polymorphism;
- classes, traits, and user-defined types;
- module/import resolution;
- compile-time evaluation;
- vector, matrix, tensor, and DataFrame implementations;
- optimizer, intermediate representation, bytecode, or native compiler;
- complete interprocedural type inference.
