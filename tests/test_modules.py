import pytest

from nyx import run
from nyx.errors import RuntimeNyxError, SemanticError


def execute(source):
    output = []
    run(source, output=output.append)
    return output


def test_math_module_exposes_scalar_functions_and_constants():
    result = execute(
        "import math\n"
        "print(math.sqrt(81))\n"
        "print(math.pow(2, 3))\n"
        "print(math.pi)\n"
        "print(math.floor(3.9))"
    )
    assert result == [9.0, 8.0, pytest.approx(3.141592653589793), 3]


def test_stats_module_exposes_descriptive_statistics():
    result = execute(
        "import stats\n"
        "let values = [1, 2, 3, 4, 5]\n"
        "print(stats.mean(values))\n"
        "print(stats.median(values))\n"
        "print(stats.variance(values))\n"
        "print(stats.standard_deviation(values))"
    )
    assert result == [3, 3, 2, pytest.approx(1.4142135623730951)]


def test_imported_modules_are_available_inside_functions():
    source = "import math\nfn root(value) { return math.sqrt(value) }\nprint(root(49))"
    assert execute(source) == [7.0]


def test_module_import_is_rejected_when_name_is_unknown():
    with pytest.raises(SemanticError, match="Module 'unknown' was not found"):
        execute("import unknown")


def test_unknown_module_member_is_rejected_before_execution():
    with pytest.raises(SemanticError, match="has no public member 'secret'"):
        execute("import math\nprint(math.secret)")


def test_module_function_arity_is_checked_statically():
    with pytest.raises(SemanticError, match="expects 2 argument"):
        execute("import math\nprint(math.pow(2))")


def test_math_functions_reject_non_numeric_arguments_statically():
    with pytest.raises(SemanticError, match="numeric operands"):
        execute('import math\nprint(math.sqrt("nine"))')


def test_stats_functions_reject_non_numeric_lists_statically():
    with pytest.raises(SemanticError, match="only numeric values"):
        execute('import stats\nprint(stats.mean([1, "two"]))')


def test_stats_functions_reject_empty_lists_at_runtime():
    with pytest.raises(RuntimeNyxError, match="undefined for an empty List"):
        execute("import stats\nstats.mean([])")


def test_module_import_name_cannot_be_declared_twice():
    with pytest.raises(SemanticError, match="already declared"):
        execute("import math\nimport math")


def test_module_access_requires_an_imported_module():
    with pytest.raises(SemanticError, match="Undefined variable 'math'"):
        execute("print(math.sqrt(4))")


def test_math_domain_errors_are_source_located():
    with pytest.raises(RuntimeNyxError, match="math.sqrt"):
        execute("import math\nprint(math.sqrt(-1))")
