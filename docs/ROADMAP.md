# NYX Development Roadmap

This roadmap describes intended deliverables. An item is marked complete only after implementation, tests, and review.

## Phase 0 — Foundation

- [x] Create the public repository.
- [x] Define the project identity and purpose.
- [x] Record independence and incremental-evolution principles.
- [x] Establish the initial language frontend and runtime prototype.
- [ ] Define contribution and release conventions.

## Phase 1 — Core language

- [x] Define the implemented grammar and reserved keywords.
- [x] Implement literals, identifiers, operators, and comments.
- [x] Implement a lexer with source locations.
- [x] Implement a recursive-descent parser and AST.
- [x] Implement declarations, expressions, and diagnostics.
- [x] Add positive, negative, and edge-case tests.

## Phase 2 — Semantics and execution

- [x] Implement lexical scopes and evaluation rules for the current core.
- [x] Implement primitive values and numeric operations.
- [x] Implement the tree-walk runtime.
- [x] Provide a local command-line interface.
- [x] Execute supported examples end to end.
- [x] Implement functions, recursion, mutable lists, and list indexing.
- [x] Implement for-in iteration and numeric list aggregations.
- [ ] Specify and implement modules and imports.
- [x] Specify the NYX 0.8 type-system design.
- [x] Implement conservative static type inference and semantic analysis.

## Phase 3 — NYX Science

- [x] Scalar arithmetic and basic numeric list aggregations.
- [ ] Vector and matrix types.
- [ ] Validated descriptive-statistics library.
- [ ] Random-state control and reproducibility contracts.
- [ ] Linear algebra and tensor operations.

## Phase 4 — NYX Data

- [ ] Native tabular structures and schemas.
- [ ] Read and write common data formats.
- [ ] Filtering, projection, joins, grouping, and aggregations.
- [ ] Data-quality rules and lineage.
- [ ] Database and API connectors.

## Phase 5 — IR and optimization

- [ ] Specify an intermediate representation.
- [ ] Implement execution planning.
- [ ] Expand reproducible benchmark workloads.
- [ ] Implement optimizations with tested semantic equivalence.
- [ ] Evaluate concurrency, parallelism, and memory management.

## Phase 6 — NYX AI

- [ ] Define provider- and model-independent interfaces.
- [ ] Integrate model inference and machine-learning workflows.
- [ ] Keep AI capabilities optional and decoupled from the language core.
- [ ] Document privacy, cost, and operational limits.

## Completion criteria

A deliverable is complete only when it has a functional implementation, automated tests, English-language documentation, and reproducible execution instructions. Performance claims additionally require a documented benchmark protocol and reproducible measurements.
