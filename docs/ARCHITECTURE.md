# NYX Architecture

## 1. Architectural direction

NYX is intended to remain an independent programming language. Its implementation must not delegate language semantics to Python or treat external libraries as substitutes for core language components.

The initial implementation may use Python as the compiler/interpreter prototyping environment. This is an implementation choice, not a semantic dependency. The architecture should allow gradual replacement of the host infrastructure with native components, including Rust, without changing NYX programs.

## 2. Execution pipeline

The conceptual long-term pipeline is:

\`\`\`text
Source Code → Lexer → Parser → AST → Semantic Analysis → IR → Planner / Optimizer → Runtime
\`\`\`

Each stage must have explicit contracts and independent tests.

### Lexer

Converts source characters into tokens while preserving file positions for precise diagnostics.

### Parser

Recognizes the language grammar and builds an Abstract Syntax Tree (AST). Syntax errors should report line, column, and context.

### Semantic analysis and type system

Validates declarations, scopes, types, function calls, and semantic constraints. A separate static semantic-analysis stage is planned; it is not implemented in the current alpha.

### Intermediate representation (IR)

Provides a stable representation between the frontend and execution backends. The IR should support optimization and multiple execution targets without changing source-language semantics.

### Planner and optimizer

Selects execution strategies and applies optimizations only when semantic equivalence can be demonstrated by tests and benchmarks.

### Runtime

Owns values, memory, function calls, errors, resource limits, and execution. The current runtime is a Python-hosted tree-walk interpreter.

## 3. Standard-library domains

The intended ecosystem is divided into domains with explicit boundaries:

| Domain | Responsibility |
|---|---|
| NYX Core | Language syntax, semantics, types, modules, and execution |
| NYX Math | Numeric primitives and mathematical functions |
| NYX Science | Statistics, probability, linear algebra, and tensors |
| NYX Data | Schemas, tabular data, ingestion, and transformations |
| NYX AI | Optional machine-learning and model interfaces |
| NYX Connect | Database, API, file, and language interoperability |
| NYX Runtime | Execution backends, optimization, and performance |

These domains are architectural targets. Only the language core described in the Language Specification is currently implemented.

## 4. Interoperability

Interoperability should be built through explicit adapters and stable contracts.

Potential boundaries include:

- Python, C, Rust, and other languages through ABI or FFI mechanisms;
- CSV, JSON, Parquet, and Arrow for data interchange;
- PostgreSQL and other SQL systems;
- HTTP/REST APIs and external services;
- queues, event streams, and messaging systems;
- machine-learning frameworks and model providers.

Adapters must not change the grammar, type system, or core runtime semantics.

## 5. Non-functional requirements

The architecture should account for:

- numerical and semantic correctness;
- reproducibility and explicit random-state control;
- performance measured through reproducible benchmarks;
- useful and traceable diagnostics;
- safe memory management and predictable resource use;
- documented concurrency and parallelism semantics;
- local installation and execution;
- explicit security boundaries for external operations.

## 6. Evolution strategy

1. Specify syntax and semantics.
2. Implement lexer, parser, and AST.
3. Implement values, scopes, and a minimal runtime.
4. Build conformance tests and diagnostics.
5. Introduce validated mathematical and statistical operations.
6. Introduce data structures and data operations.
7. Design IR and optimization using measurable evidence.
8. Integrate AI through decoupled interfaces.

A stage is not complete merely because code exists. It must have tests, documentation, and objective acceptance criteria.
