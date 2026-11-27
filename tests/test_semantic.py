import pytest

from nyx import run
from nyx.errors import RuntimeNyxError, SemanticError


def execute(source):
    output = []
    run(source, output=output.append)
    return output


def test_semantic_errors_are_reported_before_execution():
    with pytest.raises(SemanticError, match="numeric operands"):
        execute('print(10 + "five")')


def test_semantic_analyzer_rejects_non_boolean_condition():
    with pytest.raises(SemanticError, match="boolean operands"):
        execute('if (42) { print("no") }')


def test_semantic_analyzer_rejects_undefined_names():
    with pytest.raises(SemanticError, match="Undefined variable 'missing'"):
        execute('print(missing)')


def test_semantic_analyzer_rejects_duplicate_declarations():
    with pytest.raises(SemanticError, match="already declared"):
        execute('let value = 1\nlet value = 2')


def test_semantic_analyzer_rejects_return_outside_function():
    with pytest.raises(SemanticError, match="outside a function"):
        execute('return 1')


def test_semantic_analyzer_checks_list_index_type():
    with pytest.raises(SemanticError, match="Integer values"):
        execute('let values = [10]\nprint(values[0.5])')


def test_semantic_analyzer_checks_for_iterable_type():
    with pytest.raises(SemanticError, match="requires a List iterable"):
        execute('for (let value in 10) { print(value) }')


def test_semantic_analyzer_checks_native_aggregation_element_types():
    with pytest.raises(SemanticError, match="only numeric values"):
        execute('sum([1, "two", 3])')


def test_semantic_analyzer_checks_known_function_arity():
    with pytest.raises(SemanticError, match="expects 2 argument"):
        execute('fn add(a, b) { return a + b }\nadd(1)')


def test_unknown_function_parameter_types_remain_runtime_checked():
    with pytest.raises(RuntimeNyxError, match="numeric operands"):
        execute('fn increment(value) { return value + 1 }\nprint(increment("x"))')


def test_numeric_promotion_remains_valid():
    assert execute('let result = 2 + 3.5\nprint(result)') == [5.5]


def test_heterogeneous_lists_remain_valid_general_collections():
    assert execute('let values = [1, "NYX", true, null]\nprint(values[1])') == ["NYX"]


def test_list_mutation_keeps_runtime_aggregation_validation():
    with pytest.raises(RuntimeNyxError, match="only numeric values"):
        execute('let values = [1, 2]\nappend(values, "three")\nsum(values)')


def test_dynamic_function_return_is_not_guessed():
    assert execute('fn identity(value) { return value }\nprint(identity("NYX"))') == ["NYX"]



def test_semantic_analyzer_rejects_undefined_name_inside_function():
    with pytest.raises(SemanticError, match="Undefined variable 'missing'"):
        execute('fn broken() { return missing }')


def test_function_can_reference_a_later_binding_in_its_captured_scope():
    source = 'fn read_value() { return later }\nlet later = 42\nprint(read_value())'
    assert execute(source) == [42]


def test_numeric_union_promotes_to_float():
    source = 'let value = 1\nvalue = 2.5\nprint(value + 1)'
    assert execute(source) == [3.5]



def test_semantic_analysis_preserves_constant_short_circuiting():
    source = 'print(false and missing)\nprint(true or (1 + "invalid"))'
    assert execute(source) == [False, True]



def test_list_reassignment_merges_element_types_without_losing_list_identity():
    assert execute('let values = [1, 2]\nvalues = ["a", "b"]\nprint(len(values))') == [2]


def test_list_reassignment_preserves_union_element_validation():
    with pytest.raises(SemanticError, match="numeric operands"):
        execute('let values = [1, 2]\nvalues = ["a", "b"]\nprint(values[0] + 1)')
