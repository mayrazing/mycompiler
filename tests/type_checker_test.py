from compiler.parser import parse
from compiler.symtab import SymTab, top_level_type_locals
from compiler.tokenizer import tokenize
import pytest

from compiler.type_checker import typecheck
from compiler.types import Bool, Int, Unit


def fresh_symtab() -> SymTab:
    return SymTab(locals=dict(top_level_type_locals), parent=None)


def seeded_symtab() -> SymTab:
    symtab = fresh_symtab()
    typecheck(parse(tokenize('var x = 1')), symtab)
    typecheck(parse(tokenize('var b: Bool = true')), symtab)
    return symtab


def test_typecheck_var_declaration() -> None:
    symtab = fresh_symtab()
    assert typecheck(parse(tokenize('var x = 1')), symtab) == Unit
    assert typecheck(parse(tokenize('var b : Bool = true')), symtab) == Unit


def test_typecheck_type_expr() -> None:
    symtab = fresh_symtab()
    assert typecheck(parse(tokenize('var z: Int = 1')), symtab) == Unit
    assert typecheck(parse(tokenize('var s: (Int) => Unit = print_int')),
                     symtab) == Unit
    assert typecheck(parse(tokenize('var t: (Bool) => Unit = print_bool')),
                     symtab) == Unit


def test_typecheck_binary_op() -> None:
    symtab = seeded_symtab()
    assert typecheck(parse(tokenize('1 + 2 - 3')), symtab) == Int
    assert typecheck(parse(tokenize('1 + 2 * 3')), symtab) == Int
    assert typecheck(parse(tokenize('4 / 2')), symtab) == Int
    assert typecheck(parse(tokenize('4 / 2')), symtab) == Int
    assert typecheck(parse(tokenize('x + 3')), symtab) == Int
    assert typecheck(parse(tokenize('x < 3')), symtab) == Bool
    assert typecheck(parse(tokenize('x < 3 or x > 8')), symtab) == Bool
    assert typecheck(parse(tokenize('x > 3 and x < 8')), symtab) == Bool


def test_typecheck_block() -> None:
    symtab = seeded_symtab()
    assert typecheck(parse(tokenize('{}')), symtab) == Unit
    assert typecheck(parse(tokenize('{x = x + 2; x }')), symtab) == Int
    assert typecheck(parse(tokenize('{x = x + 1; x > 3}')), symtab) == Bool
    assert typecheck(parse(tokenize('{x = x + 1; x > 3; }')), symtab) == Unit


def test_typecheck_unary_op() -> None:
    symtab = seeded_symtab()
    assert typecheck(parse(tokenize('-x')), symtab) == Int
    assert typecheck(parse(tokenize('not (x > 3)')), symtab) == Bool
    assert typecheck(parse(tokenize('b = not not(x > 3)')), symtab) == Bool


def test_typecheck_if_expression() -> None:
    symtab = seeded_symtab()
    assert typecheck(parse(tokenize('if 1 > 2 then 3')), symtab) == Unit
    assert typecheck(parse(tokenize('if 1 < 2 then 3 else 4')), symtab) == Int
    assert typecheck(parse(tokenize('if 1 > 2 then true else false')),
                     symtab) == Bool
    assert typecheck(parse(tokenize('x = 10 + if 1 > 2 then 3 else 4')),
                     symtab) == Int


def test_typecheck_while_loop() -> None:
    symtab = fresh_symtab()
    assert typecheck(parse(tokenize('var y = 10; while y > 3 do y = y -1')),
                     symtab) == Unit


def test_typecheck_function_call() -> None:
    symtab = seeded_symtab()
    assert typecheck(parse(tokenize('print_int(x)')), symtab) == Unit


def test_typecheck_func_def() -> None:
    symtab = fresh_symtab()
    assert typecheck(
        parse(tokenize('fun cal_square(x: Int): Int {\nreturn x * x;\n}')),
        symtab) == Unit


def test_typecheck_return_type_mismatch() -> None:
    fresh = fresh_symtab()
    match_exception = r'.*return type mismatch.*'
    with pytest.raises(Exception, match=match_exception):
        typecheck(
            parse(tokenize('fun f(x: Int): Bool { return x * x; }')),
            fresh,
        )


def test_typecheck_return_outside_func() -> None:
    fresh = fresh_symtab()
    match_exception = r'.*return outside of a function.*'
    with pytest.raises(Exception, match=match_exception):
        typecheck(parse(tokenize('return 1')), fresh)


def test_typecheck_arg_scope_isolation() -> None:
    fresh = fresh_symtab()
    match_exception = r'.*"q" was not found in the context and all parent contexts'
    with pytest.raises(Exception, match=match_exception):
        typecheck(
            parse(tokenize('fun f(q: Int): Int { return q; } q + 1')),
            fresh,
        )


def test_typecheck_mutual_recursion() -> None:
    fresh = SymTab(locals=dict(top_level_type_locals), parent=None)
    result = typecheck(
        parse(tokenize(
            'fun is_even(n: Int): Bool {\n'
            '  if n == 0 then return true\n'
            '  else return is_odd(n - 1)\n'
            '}\n'
            'fun is_odd(n: Int): Bool {\n'
            '  if n == 0 then return false\n'
            '  else return is_even(n - 1)\n'
            '}\n'
            'is_even(4)'
        )),
        fresh,
    )
    assert result == Bool


def test_typecheck_while_true_return() -> None:
    fresh = fresh_symtab()
    result = typecheck(
        parse(tokenize('fun f(): Int { while true do return 1 }')),
        fresh,
    )
    assert result == Unit


def test_typecheck_non_unit_function_must_always_return() -> None:
    fresh = fresh_symtab()
    match_exception = r'.*must execute a return expression.*'
    with pytest.raises(Exception, match=match_exception):
        typecheck(
            parse(
                tokenize(
                    'fun f(b: Bool): Int { if b then return 1 else 2 }\n'
                    'print_int(f(false))')),
            fresh,
        )


def test_typecheck_failed_function_does_not_pollute_symtab() -> None:
    fresh = fresh_symtab()
    match_exception = r'.*return type mismatch.*'
    with pytest.raises(Exception, match=match_exception):
        typecheck(parse(tokenize('fun bad(x: Int): Bool { return x; }')), fresh)

    assert 'bad' not in fresh.locals

    match_exception = r'.*function "bad" was not defined.*'
    with pytest.raises(Exception, match=match_exception):
        typecheck(parse(tokenize('bad(1)')), fresh)


def test_typecheck_unknown_return_type() -> None:
    fresh = fresh_symtab()
    match_exception = r'.*unknown return type.*'
    with pytest.raises(Exception, match=match_exception):
        typecheck(parse(tokenize('fun f(): Foo { return 1; }')), fresh)


def test_typecheck_unknown_arg_type() -> None:
    fresh = fresh_symtab()
    match_exception = r'.*unknown argument type "Foo".*'
    with pytest.raises(Exception, match=match_exception):
        typecheck(parse(tokenize('fun f(x: Foo): Int { return 1; }')), fresh)


def test_typecheck_control_flow_outside_loop() -> None:
    fresh = fresh_symtab()
    match_exception = r'.*break outside of a loop.*'
    with pytest.raises(Exception, match=match_exception):
        typecheck(parse(tokenize('break')), fresh)

    match_exception = r'.*continue outside of a loop.*'
    with pytest.raises(Exception, match=match_exception):
        typecheck(parse(tokenize('fun f(): Unit { continue } f()')), fresh)


"""
Here are some test cases for inputs that should fail to parse
Matching exception messages: not very care about location info
"""


def test_typecheck_binary_op_exception() -> None:
    symtab = fresh_symtab()
    match_exception = r'.*"mk" was not found in the context and all parent contexts'
    with pytest.raises(Exception, match=match_exception):
        typecheck(parse(tokenize('mk = 7')), symtab)

    match_exception = r'.*expected "(.*?)" type, got "(.*?)"'
    with pytest.raises(Exception, match=match_exception):
        typecheck(parse(tokenize('var a = 0; not a = 7')), symtab)


def test_typecheck_var_declaration_exception() -> None:
    symtab = fresh_symtab()
    match_exception = r'.*variable "x" expected type "(.*?)", got type "(.*?)"'
    with pytest.raises(Exception, match=match_exception):
        typecheck(parse(tokenize('var x: Int = true')), symtab)


def test_typecheck_if_expression_exception() -> None:
    symtab = seeded_symtab()
    match_exception = r'.*if condition expression expected type "(.*?)", got type "(.*?)"'
    with pytest.raises(Exception, match=match_exception):
        typecheck(parse(tokenize('if x then 1')), symtab)


def test_typecheck_while_loop_exception() -> None:
    symtab = seeded_symtab()
    match_exception = r'.*while-loop expression expected type "(.*?)", got type "(.*?)"'
    with pytest.raises(Exception, match=match_exception):
        typecheck(parse(tokenize('while - x do x = x + 1')), symtab)


def test_typecheck_function_call_exception() -> None:
    symtab = seeded_symtab()
    match_exception = r'.*"ss" was not found in the context and all parent contexts'
    with pytest.raises(Exception, match=match_exception):
        typecheck(parse(tokenize('x = ss + 1; print_int(x)')), symtab)

    match_exception = r'.*type of function "x" expected "(.*?)", got "(.*?)"'
    with pytest.raises(Exception, match=match_exception):
        typecheck(parse(tokenize('x = x + 1; x(x)')), symtab)

    match_exception = r'.*function expression expected the type of 1-th parameter is "(.*?)", got "(.*?)"'
    with pytest.raises(Exception, match=match_exception):
        typecheck(parse(tokenize('print_int(true)')), symtab)

    match_exception = r'.*number of parameters of the function "print_int" cannot exceed 6, got "7"'
    with pytest.raises(Exception, match=match_exception):
        typecheck(parse(tokenize('print_int(1,2,3,4,5,6,7)')), symtab)


def test_typecheck_func_def_exception() -> None:
    symtab = fresh_symtab()
    typecheck(
        parse(tokenize('fun cal_square(x: Int): Int {\nreturn x * x;\n}')),
        symtab)
    match_exception = r'.*function definition "cal_square" was defined in the context and all parent contexts'
    with pytest.raises(Exception, match=match_exception):
        typecheck(
            parse(tokenize('fun cal_square(x: Int): Int {\nreturn x * x;\n}')),
            symtab)

    match_exception = r'.*return type mismatch.*'
    with pytest.raises(Exception, match=match_exception):
        typecheck(
            parse(
                tokenize('fun cal_square2(x: Int): Bool {\nreturn x * x;\n}')),
            symtab)

    fresh = fresh_symtab()
    match_exception = r'.*function definition "dup" was defined in the context and all parent contexts'
    with pytest.raises(Exception, match=match_exception):
        typecheck(
            parse(
                tokenize(
                    'fun dup(x: Int): Int { return x; }\n'
                    'fun dup(y: Int): Int { return y; }'
                )),
            fresh)
