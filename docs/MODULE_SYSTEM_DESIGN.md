# NYX Module System — Design Proposal

- Document ID: NYX-MODULES-DESIGN
- Target milestone: NYX 0.9–0.10
- Status: Initial standard-library and project-local module loading implemented; package and export semantics remain limited
- Project: NR TECH
- Normative language: English

## 1. Purpose

The module system provides a stable mechanism for organizing NYX programs and exposing domain libraries such as `math`, `stats`, `science`, and `data`.

It must support a coherent language-level interface without making the NYX language dependent on Python package semantics. The first implementation should be deliberately small, deterministic, and secure.

## 2. Initial source syntax

The initial syntax is:

```nyx
import math
import stats

let magnitude = math.sqrt(81)
let average = stats.mean([10, 20, 30])

print(magnitude)
print(average)
```

The current prototype supports `import name` and qualified member access. Imports can be used in lexical blocks. Wildcard imports, aliases, dotted module names, and arbitrary object reflection are out of scope.

## 3. Module categories

The architecture distinguishes three categories:

1. Standard-library modules: shipped and versioned with the NYX distribution, such as `math` and `stats`.
2. Project modules: source files located inside the active project and resolved by the NYX module resolver.
3. External/native modules: future extensions registered through an explicit NYX module interface. They must not be loaded by arbitrary host-language import statements.

All categories expose the same language-level module contract.

## 4. Resolution rules

The initial resolver should:

- Resolve standard-library modules from a fixed registry.
- Resolve project modules relative to the directory containing the importing source file.
- Search deterministically for `name.nyx`, then `name/__init__.nyx`.
- Reject paths that resolve outside the importing directory.
- Do not search arbitrary process working directories or host-language package paths.
- Avoid implicit network downloads or package installation during program execution.

The resolver must not search arbitrary process working directories or host-language package paths.

## 5. Namespaces and exports

An imported module is bound to its declared module name. Public functions and values are accessed through qualified names, for example `math.sqrt`.

The first implementation should expose only explicitly declared public members. Private-member syntax and export declarations require a separate language decision; until then, the standard library registry defines the public surface of built-in modules, and project modules expose top-level declarations under a documented default rule.

Name collisions between local bindings and imported module names must produce deterministic diagnostics. The initial rule should reject a duplicate declaration in the same lexical scope.

## 6. Runtime model

The runtime should represent an imported module as a NYX module value, not as a raw host-language module object.

A project module is evaluated at most once per `run()` execution. Subsequent imports reuse the cached module instance. The cache is scoped to the module loader created for that execution.

The implementation must define behavior for:
- direct and indirect cyclic imports;
- initialization failure;
- partially initialized modules;
- repeated imports;
- module-level scope isolation.

The recommended initial policy is to detect cyclic imports and raise a source-located module error rather than expose partially initialized state.

## 7. Semantic analysis

The semantic analyzer must recognize imported module bindings and validate statically known qualified members where possible.

For standard-library modules, function names, arity, parameter constraints, and return types should be registered in declarative module metadata. This allows `math.sqrt()` and `stats.mean()` to participate in the same conservative type analysis as existing built-ins.

For project modules, unresolved or dynamically determined members remain Unknown and retain runtime checks. The analyzer must not claim complete inter-module type inference in the first milestone.

## 8. Error model

Module diagnostics must include source locations and distinguish at least:

- module not found;
- ambiguous module resolution;
- invalid module path;
- duplicate module binding;
- unknown public member;
- cyclic import;
- module initialization failure.

The diagnostic prefix should remain consistent with the language:
`[NYX:L<line>:C<column>]`.

## 9. Security and reproducibility

- Module resolution is confined to explicitly configured roots.
- Imports do not execute shell commands or install packages.
- Native modules require explicit registration and a documented trust boundary.
- Module resolution order is deterministic and recorded in diagnostic output when relevant.
- The same project tree and NYX runtime version should resolve the same module graph.
- No implicit network access is permitted.

## 10. Standard-library direction

The module system is a prerequisite for the scientific ecosystem:

| Module | Initial responsibility |
|---|---|
| `math` | Scalar mathematical functions, constants, numeric utilities |
| `stats` | Descriptive statistics, probability, distributions, sampling |
| `linear` | Vector and matrix operations, decompositions, linear algebra |
| `data` | Tabular structures, schemas, transformations, file formats |
| `plot` | Visualization interfaces and chart specifications |

These names describe the proposed standard-library organization. They are not implemented modules.

## 11. Implementation sequence

1. Add a module declaration/import AST node and a dedicated import syntax.
2. Add qualified-name/member-access syntax without enabling arbitrary object reflection.
3. Implement a deterministic module registry and project resolver.
4. Add module values and isolated module scopes to the runtime.
5. Add cycle detection, initialization caching, and source-located errors.
6. Integrate standard-library metadata with semantic analysis.
7. Add conformance tests for resolution, scope, caching, failures, and security boundaries.
8. Implement `math` as the first standard-library module.
9. Implement `stats` only after numerical definitions and edge-case behavior are specified.

## 12. Acceptance criteria

The module system is complete only when:

- Standard-library and project modules can be imported through documented syntax.
- Qualified access resolves only members present in the module namespace.
- Module initialization occurs once per execution.
- Cycles and resolution failures produce deterministic diagnostics.
- Project resolution cannot escape the importing directory.
- Semantic analysis validates known standard-library signatures.
- Existing NYX 0.8 programs remain compatible.
- Automated tests pass on all supported Python versions.
- Documentation clearly separates implemented behavior from planned capabilities.

## 13. Explicitly out of scope

- Wildcard imports and import aliases.
- Relative imports and package-manager integration.
- Remote module downloads.
- Arbitrary host-language module loading.
- Reflection and unrestricted member access.
- Dynamic plugin installation at runtime.
- Full inter-module type inference.
- Vector, matrix, tensor, and DataFrame implementations.

## 14. Implemented prototype boundary

The current NYX development branch contains an initial standard-library and project-module prototype:

- `import math` and `import stats`.
- Qualified member access such as `math.sqrt(9)` and `stats.mean(values)`.
- Registered scalar math functions and constants.
- Descriptive statistics: mean, median, population variance, and population standard deviation.
- Static validation for known module names, public members, function arity, and statically known argument types.
- Runtime validation for numeric domains, empty samples, and dynamic values.

Project-local modules are now resolved relative to the importing `.nyx` file. The resolver supports `name.nyx` and `name/__init__.nyx`, executes modules in isolated interpreter scopes, exposes top-level declarations through qualified access, caches successful module initialization for the duration of one program run, and detects direct or indirect import cycles. The CLI supplies the source path automatically; API callers must pass `source_path` to `run()` to enable project imports.

The current project-module implementation deliberately has limitations: no dotted module names, aliases, explicit `export`/private declarations, configurable package roots, cross-process cache, or external/native extension registration. Static analysis recognizes project-module namespaces but cannot yet validate their member names, signatures, or argument types; these are checked at runtime. Resolution is relative to the importing file, not a configurable project root.

The standard-library functions currently available are:

| Module | Members |
|---|---|
| `math` | `pi`, `e`, `sqrt`, `abs`, `floor`, `ceil`, `sin`, `cos`, `log`, `pow` |
| `stats` | `mean`, `median`, `variance`, `standard_deviation` |

Variance and standard deviation currently use population definitions. Sample estimators, configurable degrees of freedom, and missing-value policies require explicit future specifications.
