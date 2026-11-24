# NYX Language Specification

- Document ID: NYX-LANG-SPEC
- Specification version: 0.7
- Status: Alpha — custom frontend and tree-walk interpreter
- Project: NR TECH
- Normative language: English

## 1. Identity and scope

NYX stands for Numerical Yield eXchange. It is an independent programming language designed for scientific computing, data engineering, automation, and interoperability.

The current implementation provides its own lexer, recursive-descent parser, abstract syntax tree (AST), and interpreter. Python hosts the prototype but does not define NYX syntax or semantics.

## 2. Source code

- File extension: .nyx; UTF-8 encoding, with or without a byte-order mark (BOM).
- Line comments begin with #.
- Strings use double quotes and cannot span multiple lines.
- Supported escapes: \n, \t, \", and \\.
- Simple statements may end with a semicolon, a line break, a closing brace, or end-of-file, depending on parser context.
- Blocks are delimited by { and }.

## 3. Types and values

| Type | Examples |
|---|---|
| Integer | 0, 42 |
| Float | 3.14 |
| String | "NYX" |
| Boolean | true, false |
| Null | null |
| List | [], [1, 2], [[1], [2]] |

Integers use arbitrary precision in the host implementation. Float uses binary double-precision floating-point representation. Lists are mutable, may contain heterogeneous values, and may be nested.

## 4. Variables and output

\`\`\`nyx
let samples = 120
let ratio = 0.875
let title = "NYX"
samples = samples + 1

print(title)
print(samples * ratio)
\`\`\`

A declaration using let creates a binding in the current scope. Redeclaration in the same scope is rejected. Assignment updates the nearest visible declaration. print(expression) sends the evaluated value to the output handler.

## 5. Expressions and operators

From lower to higher precedence:

1. or
2. and
3. == and !=
4. Relational comparisons: <, <=, >, >=
5. + and -
6. *, /, and %
7. Unary not, +, and -
8. Function calls, indexing, and primary expressions

Rules:

- Arithmetic and relational comparisons require numeric operands.
- and, or, and not require Boolean operands. and and or use short-circuit evaluation.
- Equality compares both type and value.
- Division and modulo by zero raise runtime errors.
- A standalone ! operator is not supported; use not.

## 6. Control flow

\`\`\`nyx
if (temperature > 30) {
    print("high")
} else {
    print("normal")
}

let index = 0
while (index < 3) {
    print(index)
    index = index + 1
}
\`\`\`

Conditions must evaluate to Boolean. Each block creates a local scope. Names are resolved from the innermost scope to the outermost scope.

## 7. Functions

Functions are declared with fn, accept positional parameters, and may return a value with return.

\`\`\`nyx
fn calculate_mean(a, b) {
    return (a + b) / 2
}

let result = calculate_mean(10, 20)
print(result)
\`\`\`

Functions may have no parameters. A function that completes without executing return evaluates to null. A return statement without an expression also returns null. The number of arguments must match the number of parameters.

Name resolution is lexical: a function retains access to the scopes that existed when it was declared. A function call creates an isolated parameter scope. Recursion and calls between functions are supported.

\`\`\`nyx
fn factorial(n) {
    if (n <= 1) {
        return 1
    }
    return n * factorial(n - 1)
}

print(factorial(6))
\`\`\`

Not currently supported: named arguments, default parameter values, overloading, anonymous functions, first-class mutable closures as a separately specified feature, or user-defined native functions.

## 8. Collections and lists

NYX provides a native mutable List type. Lists may be empty, heterogeneous, and nested.

\`\`\`nyx
let samples = [12, 18, 24]
let matrix = [[1, 2], [3, 4]]
let mixed = ["NYX", 0.6, true, null]

print(samples[0])
samples[1] = 20
append(samples, 30)
print(len(samples))
print(matrix[1][0])
\`\`\`

- Indices are integers and start at zero.
- Negative, fractional, Boolean, and out-of-range indices raise runtime errors.
- Read an element with list[index]; assign an element with list[index] = value.
- len(list) returns the number of elements.
- append(list, value) appends an element and returns null.
- Lists are mutable and assigned by reference. Variables that refer to the same list observe the same mutations.
- Passing a list to a function preserves shared identity.
- List equality is recursive and structural; scalar values still require matching types and values.
- Slicing, removal, sorting, comprehensions, and vectorized operations are not implemented.

## 9. Iteration and numeric aggregations

The for statement iterates over a list in its original order.

\`\`\`nyx
let measurements = [18.2, 19.1, 20.4]

for (let measurement in measurements) {
    print(measurement)
}

print(sum(measurements))
print(mean(measurements))
print(min(measurements))
print(max(measurements))
\`\`\`

The iterable expression is evaluated exactly once and must produce a List. Iteration uses a snapshot of the elements present when the loop begins; elements appended later do not extend the active iteration. The variable declared with let exists only within the loop scope. Each execution of the loop body receives its own inner block scope. An empty list does not execute the body.

Native aggregation functions accept exactly one list:

- sum(list): returns the sum; an empty list produces 0.
- mean(list): returns the arithmetic mean; the list must not be empty and the result is Float.
- min(list) and max(list): return the smallest and largest values; the list must not be empty.
- All four functions require elements whose types are exclusively Integer or Float. Boolean is not treated as a number.
- Non-numeric elements and non-list arguments raise source-located runtime errors.

break, continue, iteration over other collection types, and user-defined iterators are not implemented.

## 10. Grammar (EBNF)

\`\`\`ebnf
program          = { statement } , EOF ;
statement        = function_decl | declaration | assignment | print_stmt
                 | expression_stmt | return_stmt | if_stmt | while_stmt | for_stmt | block ;
function_decl    = "fn" , identifier , "(" , [ parameters ] , ")" , block ;
parameters       = identifier , { "," , identifier } ;
arguments        = expression , { "," , expression } ;
declaration      = "let" , identifier , "=" , expression , terminator ;
assignment       = ( identifier | indexed_target ) , "=" , expression , terminator ;
indexed_target   = identifier , { "[" , expression , "]" } ;
expression_stmt  = call , terminator ;
print_stmt       = "print" , "(" , expression , ")" , terminator ;
return_stmt      = "return" , [ expression ] , terminator ;
if_stmt          = "if" , "(" , expression , ")" , block , [ "else" , block ] ;
while_stmt       = "while" , "(" , expression , ")" , block ;
for_stmt         = "for" , "(" , "let" , identifier , "in" , expression , ")" , block ;
block            = "{" , { statement } , "}" ;
terminator       = ";" | line_terminator | "}" | EOF ;
expression       = logical_or ;
logical_or       = logical_and , { "or" , logical_and } ;
logical_and      = equality , { "and" , equality } ;
equality         = comparison , { ( "==" | "!=" ) , comparison } ;
comparison       = term , { ( "<" | "<=" | ">" | ">=" ) , term } ;
term             = factor , { ( "+" | "-" ) , factor } ;
factor           = unary , { ( "*" | "/" | "%" ) , unary } ;
unary            = ( "not" | "+" | "-" ) , unary | call ;
call             = primary , { "(" , [ arguments ] , ")" | "[" , expression , "]" } ;
primary          = number | string | "true" | "false" | "null"
                 | identifier | list_literal | "(" , expression , ")" ;
list_literal     = "[" , [ expression , { "," , expression } , [ "," ] ] , "]" ;
\`\`\`

line_terminator is a parser condition based on token source-line positions; it is not an independent lexical token.

## 11. Execution pipeline and diagnostics

The current pipeline is:

Source code → Lexer → Tokens → Parser → AST → Tree-walk interpreter.

Lexical, syntactic, and runtime errors identify the source line and column using the format [NYX:Lx:Cy]. The first error stops execution.

## 12. Explicit limitations

The following capabilities are not implemented: modules and imports, a static type system, type inference, generics, classes and traits, break, continue, slicing and advanced collection operations, language-level exceptions, static semantic analysis, intermediate representation (IR), compiler, bytecode or virtual machine, concurrency, parallelism, custom memory management, scientific libraries, a tabular data engine, and native AI integrations.

These items are plans, not current capabilities.

## 13. Evolution principles

NYX syntax, semantics, and conformance tests belong to the language and must remain independent of the host technology. Language design, runtime, scientific libraries, and external integrations will evolve as separate but interoperable layers.
