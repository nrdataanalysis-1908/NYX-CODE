# NYX Language Design Draft

- Document ID: NYX-LANG-DESIGN
- Draft version: 0.1.0
- Status: Historical design proposal; not the normative specification
- Project: NR TECH
- Language of documentation: English

> This document preserves the initial language-design proposal. It does not describe the current implementation and is not a frozen grammar. The normative, implementation-aligned document is [Language Specification 0.7](LANGUAGE_SPECIFICATION.md).

## 1. Objective

NYX is an independent programming language intended for data science, scientific computing, and artificial intelligence. Its syntax should support readability, semantic precision, reproducibility, and composable operations.

The grammar must not be a syntactic layer over Python. The lexer, parser, syntax tree, type system, intermediate representation, and runtime are intended to be independent components.

## 2. Initial syntax decisions

| Element | Initial proposal |
|---|---|
| Encoding | UTF-8 |
| Case sensitivity | Yes |
| Identifiers | ASCII initially; Unicode may be evaluated later |
| Blocks | Curly braces { and } |
| Statement termination | Newline or semicolon |
| Line comments | # |
| Block comments | /* ... */ |
| Assignment | = |
| Equality comparison | == |
| Type annotation | : |
| Pipeline composition | |> |
| Immutable declaration | let |
| Mutable declaration | var |
| Function declaration | fn |
| Return | return |

A newline should terminate a statement only when the parser is not inside delimiters or a construct that requires continuation. The exact continuation rule must be validated by the lexer and parser implementation.

## 3. Reserved words

### 3.1 Language core

The initial proposal considered: module, import, as, let, var, const, fn, return, if, else, for, in, while, break, continue, true, false, null, and, or, and not.

### 3.2 Scientific domains

Names such as science, statistics, math, data, ai, Array, Matrix, Tensor, Series, and DataFrame should not be reserved words by default. They may be module names, types, or standard-library symbols. This preserves the user namespace.

## 4. Lexical rules

### 4.1 Identifiers

The initial proposal uses the following grammar:

\`\`\`ebnf
identifier = (letter | "_"), { letter | digit | "_" } ;
letter     = "A"…"Z" | "a"…"z" ;
digit      = "0"…"9" ;
\`\`\`

Identifiers are case-sensitive. Therefore, value, Value, and VALUE are distinct symbols.

### 4.2 Literals

The initial design considered integer, floating-point, string, Boolean, and null literals. Numeric syntax and overflow behavior must be specified independently of the host implementation.

### 4.3 Comments

Line comments begin with #. Block comments were proposed as /* ... */ but are not part of the current implemented specification.

## 5. Type-system direction

The initial proposal considered primitive types and future scientific types such as Array, Matrix, Tensor, Series, and DataFrame. These names should be introduced through explicit type and module definitions rather than reserved-word expansion.

Type inference, generic types, nullability, numeric promotion, and user-defined types require separate design decisions.

## 6. Composition and data operations

The pipeline operator |> was proposed to express readable data transformations. Its precedence, associativity, evaluation strategy, and interaction with function calls must be formally specified before implementation.

A possible data workflow may include reading a source, filtering rows, selecting columns, grouping records, aggregating values, and inspecting the result. Such syntax remains conceptual until supported by an implementation and conformance tests.

## 7. Design decisions still requiring formalization

- module and import resolution;
- mutable and immutable bindings;
- type annotations and inference;
- numeric promotion and precision;
- null propagation;
- pipeline precedence and evaluation;
- function overloading and higher-order functions;
- recoverable errors and exception semantics;
- scientific collection types and vectorized operations.

No decision should be introduced implicitly during implementation. Each decision must be documented and accompanied by examples and tests.

## 8. Acceptance criteria for a stable specification

A specification revision should be accepted only when:

- the grammar has no known unresolved ambiguity;
- every construct has defined semantics;
- valid and invalid examples are available;
- precedence and associativity are explicit;
- types and conversions are bounded;
- conformance tests can be derived from the document without informal interpretation.
