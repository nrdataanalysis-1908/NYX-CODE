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


def test_project_module_exports_functions_and_values(tmp_path):
    (tmp_path / "geometry.nyx").write_text(
        "let unit = 12\n"
        "fn area_square(side) { return side * side }\n",
        encoding="utf-8",
    )
    source = "import geometry\nprint(geometry.area_square(5))\nprint(geometry.unit)"
    output = []
    run(source, output=output.append, source_path=tmp_path / "main.nyx")
    assert output == [25, 12]


def test_project_module_can_import_a_sibling_module(tmp_path):
    (tmp_path / "constants.nyx").write_text("let factor = 3\n", encoding="utf-8")
    (tmp_path / "geometry.nyx").write_text(
        "import constants\n"
        "fn scaled_area(side) { return side * side * constants.factor }\n",
        encoding="utf-8",
    )
    source = "import geometry\nprint(geometry.scaled_area(4))"
    output = []
    run(source, output=output.append, source_path=tmp_path / "main.nyx")
    assert output == [48]


def test_project_module_package_entrypoint_is_resolved(tmp_path):
    package = tmp_path / "geometry"
    package.mkdir()
    (package / "__init__.nyx").write_text(
        "fn double(value) { return value * 2 }\n", encoding="utf-8"
    )
    output = []
    run(
        "import geometry\nprint(geometry.double(9))",
        output=output.append,
        source_path=tmp_path / "main.nyx",
    )
    assert output == [18]


def test_project_module_is_executed_only_once_per_run(tmp_path):
    (tmp_path / "counter.nyx").write_text("print(99)\n", encoding="utf-8")
    output = []
    source = "{ import counter }\n{ import counter }"
    run(source, output=output.append, source_path=tmp_path / "main.nyx")
    assert output == [99]


def test_project_module_cycles_are_reported(tmp_path):
    (tmp_path / "alpha.nyx").write_text("import beta\n", encoding="utf-8")
    (tmp_path / "beta.nyx").write_text("import alpha\n", encoding="utf-8")
    with pytest.raises(RuntimeNyxError, match="Circular module dependency"):
        run(
            "import alpha",
            output=lambda value: None,
            source_path=tmp_path / "main.nyx",
        )


def test_project_module_missing_file_has_actionable_error(tmp_path):
    with pytest.raises(RuntimeNyxError, match="Project module 'missing' was not found"):
        run(
            "import missing",
            output=lambda value: None,
            source_path=tmp_path / "main.nyx",
        )


def test_project_module_unknown_member_is_rejected_at_runtime(tmp_path):
    (tmp_path / "geometry.nyx").write_text(
        "fn area(value) { return value * value }\n", encoding="utf-8"
    )
    with pytest.raises(RuntimeNyxError, match="has no public member 'secret'"):
        run(
            "import geometry\nprint(geometry.secret)",
            output=lambda value: None,
            source_path=tmp_path / "main.nyx",
        )
