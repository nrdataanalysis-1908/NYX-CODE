import pytest

from nyx import run
from nyx.errors import LexError, ParseError, RuntimeNyxError
from nyx.lexer import Lexer
from nyx.tokens import TokenType


def execute(source):
    output = []
    run(source, output=output.append)
    return output


def test_lexer_recognizes_keywords_and_numbers():
    tokens = Lexer('let value = 12.5; print(value);').scan_tokens()
    assert [t.type for t in tokens[:4]] == [TokenType.LET, TokenType.IDENTIFIER, TokenType.EQUAL, TokenType.FLOAT]


def test_declaration_arithmetic_and_print():
    assert execute('let x = 2 + 3 * 4; print(x);') == [14]


def test_newline_separates_statements_without_semicolons():
    assert execute('let nome = "NYX"\nlet versao = 0.1\nprint(nome)\nprint(versao)') == ["NYX", 0.1]


def test_semicolons_remain_valid_and_optional():
    assert execute('let x = 2;\nprint(x)\nprint(x + 1);') == [2, 3]


def test_expression_can_continue_on_next_line():
    assert execute('let total = 10 +\n    5 * 2\nprint(total)') == [20]


def test_utf8_bom_is_ignored_at_source_start():
    assert execute('\ufefflet nome = "NYX"\nprint(nome)') == ["NYX"]


def test_operator_precedence_and_grouping():
    assert execute('print((2 + 3) * 4);') == [20]


def test_boolean_logic_and_comparison():
    assert execute('print(10 > 3 and not false);') == [True]


def test_logical_operators_use_short_circuit_evaluation():
    assert execute('print(false and missing)\nprint(true or missing)') == [False, True]


def test_unary_numeric_operators():
    assert execute('print(-5)\nprint(+3.5)') == [-5, 3.5]


def test_string_and_null_literals():
    assert execute('let message = "hello\\nworld"; print(message); print(null);') == ["hello\nworld", None]


def test_comments_are_ignored():
    assert execute('# comment\nprint(7); # trailing comment') == [7]


def test_undefined_variable_is_reported():
    with pytest.raises(RuntimeNyxError, match="Undefined variable"):
        execute('print(missing);')


def test_duplicate_declaration_is_rejected():
    with pytest.raises(RuntimeNyxError, match="already declared"):
        execute('let x = 1; let x = 2;')


def test_assignment_updates_nearest_visible_scope():
    source = 'let value = 1\n{\n let value = 2\n value = 3\n print(value)\n}\nprint(value)'
    assert execute(source) == [3, 1]


def test_assignment_updates_outer_scope_when_not_shadowed():
    assert execute('let value = 1\n{\n value = 8\n}\nprint(value)') == [8]


def test_assignment_to_undefined_variable_is_rejected():
    with pytest.raises(RuntimeNyxError, match="undefined variable"):
        execute('missing = 10')


def test_division_by_zero_is_reported():
    with pytest.raises(RuntimeNyxError, match="Division by zero"):
        execute('print(1 / 0);')


def test_modulo_by_zero_is_reported():
    with pytest.raises(RuntimeNyxError, match="Modulo by zero"):
        execute('print(5 % 0)')


def test_strict_boolean_types():
    with pytest.raises(RuntimeNyxError, match="boolean operands"):
        execute('print(1 and true);')


def test_non_boolean_if_condition_is_rejected():
    with pytest.raises(RuntimeNyxError, match="boolean operands"):
        execute('if (1) { print("invalid") }')


def test_non_boolean_while_condition_is_rejected():
    with pytest.raises(RuntimeNyxError, match="boolean operands"):
        execute('while (1) { print("invalid") }')


def test_invalid_character_is_reported():
    with pytest.raises(LexError, match="NYX:L1:C1"):
        Lexer("@").scan_tokens()


def test_missing_statement_separator_is_reported_on_same_line():
    with pytest.raises(ParseError, match="Expected ';' or a line break"):
        execute('print(1) print(2)')


def test_if_true_branch():
    assert execute('if (true) {\n print("yes")\n} else {\n print("no")\n}') == ["yes"]


def test_if_else_false_branch():
    assert execute('if (false) { print("yes") } else { print("no") }') == ["no"]


def test_if_without_else():
    assert execute('if (2 > 1) { print("ok") }') == ["ok"]


def test_empty_block_is_valid():
    assert execute('if (true) { }\nprint("after")') == ["after"]


def test_while_repeats_until_condition_is_false():
    source = 'let index = 0\nwhile (index < 4) {\n print(index)\n index = index + 1\n}'
    assert execute(source) == [0, 1, 2, 3]


def test_nested_control_flow_and_block_scope():
    source = 'let visible = 7\nif (true) {\n let hidden = 9\n if (hidden > visible) { print(hidden) }\n}'
    assert execute(source) == [9]
    with pytest.raises(RuntimeNyxError, match="Undefined variable"):
        execute(source + '\nprint(hidden)')


def test_function_with_parameters_and_return_value():
    source = 'fn calcular_media(a, b) {\n return (a + b) / 2\n}\nlet resultado = calcular_media(10, 20)\nprint(resultado)'
    assert execute(source) == [15]


def test_function_without_return_returns_null():
    assert execute('fn announce() { print("ready") }\nprint(announce())') == ["ready", None]


def test_function_without_parameters():
    assert execute('fn answer() { return 42 }\nprint(answer())') == [42]


def test_recursive_function_factorial():
    source = 'fn factorial(n) {\n if (n <= 1) { return 1 }\n return n * factorial(n - 1)\n}\nprint(factorial(6))'
    assert execute(source) == [720]


def test_function_can_call_another_function():
    source = 'fn double(x) { return x * 2 }\nfn add_one(x) { return double(x) + 1 }\nprint(add_one(20))'
    assert execute(source) == [41]


def test_function_has_lexical_access_to_enclosing_scope():
    source = 'let factor = 3\nfn scale(value) { return value * factor }\nprint(scale(7))'
    assert execute(source) == [21]


def test_function_parameter_scope_does_not_leak():
    with pytest.raises(RuntimeNyxError, match="Undefined variable"):
        execute('fn identity(value) { return value }\nidentity(5)\nprint(value)')


def test_function_argument_count_is_validated():
    with pytest.raises(RuntimeNyxError, match="expects 2 argument"):
        execute('fn add(a, b) { return a + b }\nadd(1)')


def test_non_function_call_is_rejected():
    with pytest.raises(RuntimeNyxError, match="Only functions can be called"):
        execute('let value = 3\nvalue()')


def test_duplicate_function_parameter_is_rejected():
    with pytest.raises(ParseError, match="parameter cannot be declared"):
        execute('fn invalid(x, x) { return x }')


def test_return_outside_function_is_rejected():
    with pytest.raises(RuntimeNyxError, match="outside a function"):
        execute('return 10')


def test_empty_and_nested_list_literals():
    assert execute('let empty = []\nlet matrix = [[1, 2], [3, 4]]\nprint(len(empty))\nprint(matrix[1][0])') == [0, 3]


def test_heterogeneous_lists_and_zero_based_indexing():
    assert execute('let values = [10, "NYX", true, null]\nprint(values[0])\nprint(values[1])\nprint(values[2])\nprint(values[3])') == [10, "NYX", True, None]


def test_list_element_assignment():
    assert execute('let values = [1, 2, 3]\nvalues[1] = 20\nprint(values[1])') == [20]


def test_nested_list_element_assignment():
    assert execute('let matrix = [[1, 2], [3, 4]]\nmatrix[1][0] = 30\nprint(matrix[1][0])') == [30]


def test_list_aliases_share_mutations():
    assert execute('let first = [1]\nlet second = first\nappend(second, 2)\nprint(len(first))\nprint(first[1])') == [2, 2]


def test_append_mutates_and_returns_null():
    assert execute('let values = [1]\nlet result = append(values, "x")\nprint(values[1])\nprint(result)') == ["x", None]


def test_list_length_is_zero_for_empty_list():
    assert execute('print(len([]))') == [0]


def test_list_equality_is_structural_and_type_strict():
    assert execute('print([1, [2]] == [1, [2]])\nprint([1] == [true])') == [True, False]


@pytest.mark.parametrize("source,message", [
    ('let values = [1]\nprint(values[1])', "out of range"),
    ('let values = [1]\nprint(values[-1])', "out of range"),
    ('let values = [1]\nprint(values[0.5])', "Integer values"),
    ('let values = [1]\nprint(values[true])', "Integer values"),
    ('let value = 1\nprint(value[0])', "requires a List"),
    ('append(1, 2)', "append\\(\\) expects"),
    ('len("text")', "len\\(\\) expects"),
    ('len()', "expects 1 argument"),
    ('append([], 1, 2)', "expects 2 argument"),
])
def test_list_runtime_errors_are_explicit(source, message):
    with pytest.raises(RuntimeNyxError, match=message):
        execute(source)


def test_indexed_assignment_rejects_out_of_range_index():
    with pytest.raises(RuntimeNyxError, match="out of range"):
        execute('let values = [1]\nvalues[2] = 9')


def test_indexed_assignment_rejects_non_list_target():
    with pytest.raises(RuntimeNyxError, match="requires a List"):
        execute('let value = 1\nvalue[0] = 9')


def test_list_expression_can_be_passed_to_user_function():
    assert execute('fn first(values) { return values[0] }\nprint(first([42]))') == [42]


def test_append_can_receive_nested_list():
    assert execute('let values = []\nappend(values, [1, 2])\nprint(values[0][1])') == [2]



def test_for_iterates_over_list_in_order():
    source = 'let values = [4, 7, 9]\nfor (let value in values) {\n print(value)\n}'
    assert execute(source) == [4, 7, 9]


def test_for_supports_empty_list():
    assert execute('for (let value in []) { print(value) }\nprint("done")') == ["done"]


def test_for_iteration_variable_has_its_own_scope():
    source = 'let value = 100\nfor (let value in [1, 2]) { print(value) }\nprint(value)'
    assert execute(source) == [1, 2, 100]
    with pytest.raises(RuntimeNyxError, match="Undefined variable"):
        execute('for (let item in [1]) { print(item) }\nprint(item)')


def test_for_can_iterate_nested_lists():
    source = 'let rows = [[1, 2], [3, 4]]\nfor (let row in rows) { print(row[0]) }'
    assert execute(source) == [1, 3]


def test_for_rejects_non_list_iterable():
    with pytest.raises(RuntimeNyxError, match="requires a List"):
        execute('for (let item in 42) { print(item) }')


def test_for_loop_variable_can_be_used_in_nested_functions():
    source = 'fn double(value) { return value * 2 }\nfor (let item in [2, 3]) { print(double(item)) }'
    assert execute(source) == [4, 6]


def test_numeric_aggregations():
    source = 'let values = [2, 4, 6, 8]\nprint(sum(values))\nprint(mean(values))\nprint(min(values))\nprint(max(values))'
    assert execute(source) == [20, 5.0, 2, 8]


def test_numeric_aggregations_support_mixed_integer_and_float():
    assert execute('print(sum([1, 2.5, 3]))\nprint(mean([1, 2.5, 3]))') == [6.5, 2.1666666666666665]


def test_sum_of_empty_list_is_zero():
    assert execute('print(sum([]))') == [0]


@pytest.mark.parametrize("function_name", ["mean", "min", "max"])
def test_non_sum_aggregations_reject_empty_lists(function_name):
    with pytest.raises(RuntimeNyxError, match="empty List"):
        execute(f'{function_name}([])')


@pytest.mark.parametrize("function_name", ["sum", "mean", "min", "max"])
def test_numeric_aggregations_reject_non_numeric_elements(function_name):
    with pytest.raises(RuntimeNyxError, match="only numeric values"):
        execute(f'{function_name}([1, "two", 3])')


@pytest.mark.parametrize("function_name", ["sum", "mean", "min", "max"])
def test_numeric_aggregations_reject_non_list_values(function_name):
    with pytest.raises(RuntimeNyxError, match="expects a List"):
        execute(f'{function_name}(10)')


def test_numeric_aggregations_reject_boolean_values():
    with pytest.raises(RuntimeNyxError, match="only numeric values"):
        execute('sum([true, 1])')



def test_for_uses_a_fixed_iteration_snapshot_when_list_is_mutated():
    source = 'let values = [1, 2]\nfor (let value in values) {\n print(value)\n append(values, value + 10)\n}\nprint(len(values))'
    assert execute(source) == [1, 2, 4]
