from compiler.parser import parse
from compiler.tokenizer import Location, tokenize
import compiler.ast as AST
import pytest

L = Location(line=-1, column=-1)


def test_int_literal() -> None:
    assert parse(tokenize("1")) == AST.Module(funcs=None,
                                              expr=AST.Literal(location=L,
                                                               value=1))

    assert parse(tokenize("1 + 2")) == AST.Module(funcs=None,
                                                  expr=AST.BinaryOp(
                                                      location=L,
                                                      left=AST.Literal(L, 1),
                                                      op="+",
                                                      right=AST.Literal(L, 2)))

    assert parse(tokenize("3 - 2")) == AST.Module(funcs=None,
                                                  expr=AST.BinaryOp(
                                                      location=L,
                                                      left=AST.Literal(L, 3),
                                                      op="-",
                                                      right=AST.Literal(L, 2)))


def test_identifier() -> None:
    assert parse(tokenize("a")) == AST.Module(funcs=None,
                                              expr=AST.Identifier(L, 'a'))

    assert parse(tokenize("x + y")) == AST.Module(
        funcs=None,
        expr=AST.BinaryOp(location=L,
                          left=AST.Identifier(L, 'x'),
                          op="+",
                          right=AST.Identifier(L, 'y')))

    assert parse(tokenize("b - 3")) == AST.Module(
        funcs=None,
        expr=AST.BinaryOp(location=L,
                          left=AST.Identifier(L, 'b'),
                          op="-",
                          right=AST.Literal(L, 3)))


def test_left_associativity() -> None:
    assert parse(tokenize("1 - 2 + 3")) == AST.Module(
        funcs=None,
        expr=AST.BinaryOp(location=L,
                          left=AST.BinaryOp(location=L,
                                            left=AST.Literal(L, 1),
                                            op="-",
                                            right=AST.Literal(L, 2)),
                          op="+",
                          right=AST.Literal(L, 3)))


def test_right_associativity() -> None:
    assert parse(tokenize("x = a + b - 3")) == AST.Module(
        funcs=None,
        expr=AST.BinaryOp(location=L,
                          left=AST.Identifier(L, 'x'),
                          op="=",
                          right=AST.BinaryOp(location=L,
                                             left=AST.BinaryOp(
                                                 location=L,
                                                 left=AST.Identifier(L, 'a'),
                                                 op="+",
                                                 right=AST.Identifier(L, 'b')),
                                             op="-",
                                             right=AST.Literal(L, 3))))

    assert parse(tokenize("x = a = b = 3")) == AST.Module(
        funcs=None,
        expr=AST.BinaryOp(location=L,
                          left=AST.Identifier(L, 'x'),
                          op="=",
                          right=AST.BinaryOp(location=L,
                                             left=AST.Identifier(L, 'a'),
                                             op="=",
                                             right=AST.BinaryOp(
                                                 location=L,
                                                 left=AST.Identifier(L, 'b'),
                                                 op="=",
                                                 right=AST.Literal(L, 3)))))


def test_logical_or_op() -> None:

    assert parse(tokenize("x = a or b")) == AST.Module(
        funcs=None,
        expr=AST.BinaryOp(location=L,
                          left=AST.Identifier(L, 'x'),
                          op="=",
                          right=AST.BinaryOp(location=L,
                                             left=AST.Identifier(L, 'a'),
                                             op="or",
                                             right=AST.Identifier(L, 'b'))))


def test_logical_and_op() -> None:

    assert parse(tokenize("x = a and b")) == AST.Module(
        funcs=None,
        expr=AST.BinaryOp(location=L,
                          left=AST.Identifier(L, 'x'),
                          op="=",
                          right=AST.BinaryOp(location=L,
                                             left=AST.Identifier(L, 'a'),
                                             op="and",
                                             right=AST.Identifier(L, 'b'))))


def test_equality_op() -> None:

    assert parse(tokenize("x = a and b == 5")) == AST.Module(
        funcs=None,
        expr=AST.BinaryOp(location=L,
                          left=AST.Identifier(L, 'x'),
                          op="=",
                          right=AST.BinaryOp(location=L,
                                             left=AST.Identifier(L, 'a'),
                                             op="and",
                                             right=AST.BinaryOp(
                                                 location=L,
                                                 left=AST.Identifier(L, 'b'),
                                                 op="==",
                                                 right=AST.Literal(L, 5)))))


def test_comparison_op() -> None:

    assert parse(tokenize("x = a == b <= 5")) == AST.Module(
        funcs=None,
        expr=AST.BinaryOp(location=L,
                          left=AST.Identifier(L, 'x'),
                          op="=",
                          right=AST.BinaryOp(location=L,
                                             left=AST.Identifier(L, 'a'),
                                             op="==",
                                             right=AST.BinaryOp(
                                                 location=L,
                                                 left=AST.Identifier(L, 'b'),
                                                 op="<=",
                                                 right=AST.Literal(L, 5)))))

    assert parse(tokenize("x = a <= b == 5")) == AST.Module(
        funcs=None,
        expr=AST.BinaryOp(location=L,
                          left=AST.Identifier(L, 'x'),
                          op="=",
                          right=AST.BinaryOp(location=L,
                                             left=AST.BinaryOp(
                                                 location=L,
                                                 left=AST.Identifier(L, 'a'),
                                                 op="<=",
                                                 right=AST.Identifier(L, 'b')),
                                             op="==",
                                             right=AST.Literal(L, 5))))


def test_factor_op() -> None:
    assert parse(tokenize("1 * 5 + 2 * 3")) == AST.Module(
        funcs=None,
        expr=AST.BinaryOp(location=L,
                          left=AST.BinaryOp(location=L,
                                            left=AST.Literal(L, 1),
                                            op="*",
                                            right=AST.Literal(L, 5)),
                          op="+",
                          right=AST.BinaryOp(location=L,
                                             left=AST.Literal(L, 2),
                                             op="*",
                                             right=AST.Literal(L, 3))))

    assert parse(tokenize("1 + 4 / 2")) == AST.Module(
        funcs=None,
        expr=AST.BinaryOp(location=L,
                          left=AST.Literal(L, 1),
                          op="+",
                          right=AST.BinaryOp(location=L,
                                             left=AST.Literal(L, 4),
                                             op="/",
                                             right=AST.Literal(L, 2))))

    assert parse(tokenize("1 + 4 % 3")) == AST.Module(
        funcs=None,
        expr=AST.BinaryOp(location=L,
                          left=AST.Literal(L, 1),
                          op="+",
                          right=AST.BinaryOp(location=L,
                                             left=AST.Literal(L, 4),
                                             op="%",
                                             right=AST.Literal(L, 3))))


def test_unary_op() -> None:

    assert parse(tokenize("a and - b")) == AST.Module(
        funcs=None,
        expr=AST.BinaryOp(location=L,
                          left=AST.Identifier(L, 'a'),
                          op="and",
                          right=AST.UnaryOp(location=L,
                                            op="-",
                                            unary_clause=AST.Identifier(
                                                L, 'b'))))

    assert parse(tokenize("a and not not b")) == AST.Module(
        funcs=None,
        expr=AST.BinaryOp(location=L,
                          left=AST.Identifier(L, 'a'),
                          op="and",
                          right=AST.UnaryOp(location=L,
                                            op="not",
                                            unary_clause=AST.UnaryOp(
                                                location=L,
                                                op="not",
                                                unary_clause=AST.Identifier(
                                                    L, 'b')))))


def test_bool_literal() -> None:

    assert parse(tokenize("true")) == AST.Module(funcs=None,
                                                 expr=AST.Literal(L, True))

    assert parse(tokenize("false")) == AST.Module(funcs=None,
                                                  expr=AST.Literal(L, False))


def test_parentheses() -> None:

    assert parse(tokenize("(1 + 4) / 2")) == AST.Module(
        funcs=None,
        expr=AST.BinaryOp(location=L,
                          left=AST.BinaryOp(location=L,
                                            left=AST.Literal(L, 1),
                                            op="+",
                                            right=AST.Literal(L, 4)),
                          op="/",
                          right=AST.Literal(L, 2)))


def test_if_expression() -> None:

    assert parse(tokenize("if 1 then 2")) == AST.Module(
        funcs=None,
        expr=AST.IfExpression(location=L,
                              op='if',
                              cond=AST.Literal(L, 1),
                              then_clause=AST.Literal(L, 2),
                              else_clause=None))

    assert parse(tokenize("if 1 then 2 else 3")) == AST.Module(
        funcs=None,
        expr=AST.IfExpression(location=L,
                              op='if',
                              cond=AST.Literal(L, 1),
                              then_clause=AST.Literal(L, 2),
                              else_clause=AST.Literal(L, 3)))

    assert parse(tokenize("if 1 + 2 then 2 * 3 else 3 / 4")) == AST.Module(
        funcs=None,
        expr=AST.IfExpression(location=L,
                              op='if',
                              cond=AST.BinaryOp(L, AST.Literal(L, 1), "+",
                                                AST.Literal(L, 2)),
                              then_clause=AST.BinaryOp(L, AST.Literal(L, 2),
                                                       "*", AST.Literal(L, 3)),
                              else_clause=AST.BinaryOp(L, AST.Literal(L,
                                                                      3), "/",
                                                       AST.Literal(L, 4))))

    assert parse(
        tokenize(" 0 + if 1 + 2 then 2 * 3 else 3 / 4")) == AST.Module(
            funcs=None,
            expr=AST.BinaryOp(
                location=L,
                left=AST.Literal(L, 0),
                op="+",
                right=AST.IfExpression(
                    location=L,
                    op='if',
                    cond=AST.BinaryOp(L, AST.Literal(L, 1), "+",
                                      AST.Literal(L, 2)),
                    then_clause=AST.BinaryOp(L, AST.Literal(L, 2), "*",
                                             AST.Literal(L, 3)),
                    else_clause=AST.BinaryOp(L, AST.Literal(L, 3), "/",
                                             AST.Literal(L, 4)))))


def test_function_call() -> None:

    assert parse(tokenize("f(x, y + z)")) == AST.Module(
        funcs=None,
        expr=AST.FunctionCall(location=L,
                              op='call',
                              name=AST.Identifier(L, 'f'),
                              args=[
                                  AST.Identifier(L, 'x'),
                                  AST.BinaryOp(location=L,
                                               left=AST.Identifier(L, 'y'),
                                               op="+",
                                               right=AST.Identifier(L, 'z'))
                              ]))


def test_while_loop() -> None:

    assert parse(tokenize("while x do gcd(a, b)")) == AST.Module(
        funcs=None,
        expr=AST.WhileLoop(location=L,
                           op='while',
                           cond=AST.Identifier(L, 'x'),
                           body=AST.FunctionCall(location=L,
                                                 op='call',
                                                 name=AST.Identifier(L, 'gcd'),
                                                 args=[
                                                     AST.Identifier(L, 'a'),
                                                     AST.Identifier(L, 'b')
                                                 ])))


def test_var_declaration() -> None:

    assert parse(tokenize("var x = 123")) == AST.Module(
        funcs=None,
        expr=AST.VarDeclaration(location=L,
                                op='var',
                                name=AST.Identifier(L, 'x'),
                                declared_type_exp=None,
                                initializer=AST.Literal(L, 123)))

    assert parse(tokenize("var x: T = 123")) == AST.Module(
        funcs=None,
        expr=AST.VarDeclaration(location=L,
                                op='var',
                                name=AST.Identifier(L, 'x'),
                                declared_type_exp=AST.BasicTypeExpr(L, 'T'),
                                initializer=AST.Literal(L, 123)))

    assert parse(tokenize("var x: Int = 123")) == AST.Module(
        funcs=None,
        expr=AST.VarDeclaration(location=L,
                                op='var',
                                name=AST.Identifier(L, 'x'),
                                declared_type_exp=AST.BasicTypeExpr(L, 'Int'),
                                initializer=AST.Literal(L, 123)))

    assert parse(tokenize("var x: (a, b) => c = 123")) == AST.Module(
        funcs=None,
        expr=AST.VarDeclaration(
            location=L,
            op='var',
            name=AST.Identifier(L, 'x'),
            declared_type_exp=AST.FuncTypeExpr(
                location=L,
                params=[AST.BasicTypeExpr(L, 'a'),
                        AST.BasicTypeExpr(L, 'b')],
                result=AST.BasicTypeExpr(L, 'c')),
            initializer=AST.Literal(L, 123)))


def test_block() -> None:
    assert parse(tokenize("{}")) == AST.Module(funcs=None,
                                               expr=AST.Block(location=L,
                                                              op='{}',
                                                              statements=None))

    assert parse(tokenize("{f(x) = x * 3}")) == AST.Module(
        funcs=None,
        expr=AST.Block(location=L,
                       op='{}',
                       statements=[
                           AST.BinaryOp(location=L,
                                        left=AST.FunctionCall(
                                            location=L,
                                            op='call',
                                            name=AST.Identifier(L, 'f'),
                                            args=[AST.Identifier(L, 'x')]),
                                        op='=',
                                        right=AST.BinaryOp(
                                            location=L,
                                            left=AST.Identifier(L, 'x'),
                                            op='*',
                                            right=AST.Literal(L, 3)))
                       ]))

    assert parse(tokenize("f(a); \nb; \n ")) == AST.Module(
        funcs=None,
        expr=AST.Block(location=L,
                       op='{}',
                       statements=[
                           AST.FunctionCall(location=L,
                                            op='call',
                                            name=AST.Identifier(L, 'f'),
                                            args=[AST.Identifier(L, 'a')]),
                           AST.Identifier(L, 'b'),
                           AST.Literal(L, None)
                       ]))

    assert parse(tokenize("x = { f(a); b }")) == AST.Module(
        funcs=None,
        expr=AST.BinaryOp(
            location=L,
            left=AST.Identifier(L, 'x'),
            op='=',
            right=AST.Block(location=L,
                            op='{}',
                            statements=[
                                AST.FunctionCall(location=L,
                                                 op='call',
                                                 name=AST.Identifier(L, 'f'),
                                                 args=[AST.Identifier(L,
                                                                      'a')]),
                                AST.Identifier(L, 'b')
                            ])))

    assert parse(tokenize("x = { f(a); }")) == AST.Module(
        funcs=None,
        expr=AST.BinaryOp(
            location=L,
            left=AST.Identifier(L, 'x'),
            op='=',
            right=AST.Block(location=L,
                            op='{}',
                            statements=[
                                AST.FunctionCall(location=L,
                                                 op='call',
                                                 name=AST.Identifier(L, 'f'),
                                                 args=[AST.Identifier(L,
                                                                      'a')]),
                                AST.Literal(L, None)
                            ])))

    assert parse(tokenize("{ { x } { y } }")) == AST.Module(
        funcs=None,
        expr=AST.Block(location=L,
                       op='{}',
                       statements=[
                           AST.Block(location=L,
                                     op='{}',
                                     statements=[AST.Identifier(L, 'x')]),
                           AST.Block(location=L,
                                     op='{}',
                                     statements=[AST.Identifier(L, 'y')])
                       ]))

    assert parse(tokenize("{ if true then { a } b }")) == AST.Module(
        funcs=None,
        expr=AST.Block(location=L,
                       op='{}',
                       statements=[
                           AST.IfExpression(
                               location=L,
                               op='if',
                               cond=AST.Literal(L, True),
                               then_clause=AST.Block(
                                   location=L,
                                   op='{}',
                                   statements=[AST.Identifier(L, 'a')]),
                               else_clause=None),
                           AST.Identifier(L, 'b')
                       ]))

    assert parse(tokenize("{ if true then { a } ; b }")) == AST.Module(
        funcs=None,
        expr=AST.Block(location=L,
                       op='{}',
                       statements=[
                           AST.IfExpression(
                               location=L,
                               op='if',
                               cond=AST.Literal(L, True),
                               then_clause=AST.Block(
                                   location=L,
                                   op='{}',
                                   statements=[AST.Identifier(L, 'a')]),
                               else_clause=None),
                           AST.Identifier(L, 'b')
                       ]))

    assert parse(tokenize("{ if true then { a } b; c }")) == AST.Module(
        funcs=None,
        expr=AST.Block(location=L,
                       op='{}',
                       statements=[
                           AST.IfExpression(
                               location=L,
                               op='if',
                               cond=AST.Literal(L, True),
                               then_clause=AST.Block(
                                   location=L,
                                   op='{}',
                                   statements=[AST.Identifier(L, 'a')]),
                               else_clause=None),
                           AST.Identifier(L, 'b'),
                           AST.Identifier(L, 'c')
                       ]))

    assert parse(
        tokenize("{ if true then { a } else { b } 3 }")) == AST.Module(
            funcs=None,
            expr=AST.Block(location=L,
                           op='{}',
                           statements=[
                               AST.IfExpression(
                                   location=L,
                                   op='if',
                                   cond=AST.Literal(L, True),
                                   then_clause=AST.Block(
                                       location=L,
                                       op='{}',
                                       statements=[AST.Identifier(L, 'a')]),
                                   else_clause=AST.Block(
                                       location=L,
                                       op='{}',
                                       statements=[AST.Identifier(L, 'b')])),
                               AST.Literal(L, 3)
                           ]))

    assert parse(tokenize("x = { { f(a) } { b } }")) == AST.Module(
        funcs=None,
        expr=AST.BinaryOp(
            location=L,
            left=AST.Identifier(L, 'x'),
            op='=',
            right=AST.Block(location=L,
                            op='{}',
                            statements=[
                                AST.Block(
                                    location=L,
                                    op='{}',
                                    statements=[
                                        AST.FunctionCall(
                                            location=L,
                                            op='call',
                                            name=AST.Identifier(L, 'f'),
                                            args=[AST.Identifier(L, 'a')])
                                    ]),
                                AST.Block(location=L,
                                          op='{}',
                                          statements=[AST.Identifier(L, 'b')]),
                            ])))

    assert parse(
        tokenize(
            "{ while f()  do { x = 1; y = { if g(x) then { x = x + 1; x } else g(x) } } var a = 2}"
        )) == AST.Module(
            funcs=None,
            expr=AST.Block(
                location=L,
                op='{}',
                statements=[
                    AST.WhileLoop(
                        location=L,
                        op='while',
                        cond=AST.FunctionCall(location=L,
                                              op='call',
                                              name=AST.Identifier(L, 'f'),
                                              args=None),
                        body=AST.Block(
                            location=L,
                            op='{}',
                            statements=[
                                AST.BinaryOp(location=L,
                                             left=AST.Identifier(location=L,
                                                                 name='x'),
                                             op='=',
                                             right=AST.Literal(location=L,
                                                               value=1)),
                                AST.BinaryOp(
                                    location=L,
                                    left=AST.Identifier(location=L, name='y'),
                                    op='=',
                                    right=AST.Block(
                                        location=L,
                                        op='{}',
                                        statements=[
                                            AST.IfExpression(
                                                location=L,
                                                op='if',
                                                cond=AST.FunctionCall(
                                                    location=L,
                                                    op='call',
                                                    name=AST.Identifier(
                                                        L, 'g'),
                                                    args=[
                                                        AST.Identifier(
                                                            location=L,
                                                            name='x')
                                                    ]),
                                                then_clause=AST.Block(
                                                    location=L,
                                                    op='{}',
                                                    statements=[
                                                        AST.BinaryOp(
                                                            location=L,
                                                            left=AST.
                                                            Identifier(
                                                                location=L,
                                                                name='x'),
                                                            op='=',
                                                            right=AST.BinaryOp(
                                                                location=L,
                                                                left=AST.
                                                                Identifier(
                                                                    location=L,
                                                                    name='x'),
                                                                op='+',
                                                                right=AST.
                                                                Literal(
                                                                    location=L,
                                                                    value=1))),
                                                        AST.Identifier(
                                                            location=L,
                                                            name='x')
                                                    ]),
                                                else_clause=AST.FunctionCall(
                                                    location=L,
                                                    op='call',
                                                    name=AST.Identifier(
                                                        L, 'g'),
                                                    args=[
                                                        AST.Identifier(
                                                            location=L,
                                                            name='x')
                                                    ]))
                                        ]))
                            ])),
                    AST.VarDeclaration(location=L,
                                       op='var',
                                       name=AST.Identifier(L, 'a'),
                                       declared_type_exp=None,
                                       initializer=AST.Literal(location=L,
                                                               value=2))
                ]))


def test_func_def() -> None:
    assert parse(
        tokenize("fun square(x: Int): Int {\nreturn x * x;\n}")) == AST.Module(
            funcs=[
                AST.FuncDefinition(
                    location=L,
                    name=AST.Identifier(L, 'square'),
                    args={AST.Identifier(L, 'x'): AST.BasicTypeExpr(L, 'Int')},
                    return_type=AST.BasicTypeExpr(L, 'Int'),
                    body=AST.Block(location=L,
                                   op='{}',
                                   statements=[
                                       AST.Return(
                                           location=L,
                                           op='return',
                                           value=AST.BinaryOp(
                                               location=L,
                                               left=AST.Identifier(L, 'x'),
                                               op='*',
                                               right=AST.Identifier(L, 'x')))
                                   ]))
            ],
            expr=None)

    assert parse(
        tokenize("fun fact(n: Int): Int {\n"
                 "if n <= 1 then return 1\n"
                 "else return n * fact(n - 1)\n"
                 "}")) == AST.Module(
                     funcs=[
                         AST.FuncDefinition(
                             location=L,
                             name=AST.Identifier(L, 'fact'),
                             args={
                                 AST.Identifier(L, 'n'):
                                 AST.BasicTypeExpr(L, 'Int')
                             },
                             return_type=AST.BasicTypeExpr(L, 'Int'),
                             body=AST.Block(
                                 location=L,
                                 op='{}',
                                 statements=[
                                     AST.IfExpression(
                                         location=L,
                                         op='if',
                                         cond=AST.BinaryOp(
                                             location=L,
                                             left=AST.Identifier(L, 'n'),
                                             op='<=',
                                             right=AST.Literal(
                                                 location=L, value=1)),
                                         then_clause=AST.Return(
                                             location=L,
                                             op='return',
                                             value=AST.Literal(
                                                 location=L, value=1)),
                                         else_clause=AST.Return(
                                             location=L,
                                             op='return',
                                             value=AST.BinaryOp(
                                                 location=L,
                                                 left=AST.Identifier(
                                                     L, 'n'),
                                                 op='*',
                                                 right=AST.FunctionCall(
                                                     location=L,
                                                     op='call',
                                                     name=AST.Identifier(
                                                         L, 'fact'),
                                                     args=[
                                                         AST.BinaryOp(
                                                             location=L,
                                                             left=AST.Identifier(
                                                                 L, 'n'),
                                                             op='-',
                                                             right=AST.Literal(
                                                                 location=L,
                                                                 value=1))
                                                     ]))))
                                 ]))
                     ],
                     expr=None)


"""
Here are some test cases for inputs that should fail to parse
Matching exception messages: not very care about location info
"""


def test_end_exceptions() -> None:
    match_exception = r'.*expected ";" at "c"'
    with pytest.raises(Exception, match=match_exception):
        parse(tokenize("a + b c"))


def test_int_literal_exceptions() -> None:
    match_exception = r'.*Integer literal value must be between -2\*\*64 and 2\*\*63 - 1'
    with pytest.raises(Exception, match=match_exception):
        a: int = 2**64
        parse(tokenize(str(a)))


def test_unary_op_exceptions() -> None:
    match_exception = r'.*expected expression at "<end of file>"'
    with pytest.raises(Exception, match=match_exception):
        parse(tokenize("not not "))


def test_primary_exceptions() -> None:
    match_exception = r'.*expected expression at ";"'
    with pytest.raises(Exception, match=match_exception):
        parse(tokenize("a = ;"))


def test_function_call_exceptions() -> None:
    match_exception = r'.*expected "," at ";"'
    with pytest.raises(Exception, match=match_exception):
        parse(tokenize("a = f( x ; y ) "))


def test_if_exceptions() -> None:
    match_exception = r'.*expected "then" at "else"'
    with pytest.raises(Exception, match=match_exception):
        parse(tokenize("if 1 else 3"))


def test_block_exceptions() -> None:
    match_exception = r'.*expected expression at ";"'
    with pytest.raises(Exception, match=match_exception):
        parse(tokenize("x = { f(a) ;;}"))

    match_exception = r'.*expected "}" at "b"'
    with pytest.raises(Exception, match=match_exception):
        parse(tokenize("x = { f(a) b }"))

    match_exception = r'.*expected "}" at "b"'
    with pytest.raises(Exception, match=match_exception):
        parse(tokenize("{ a b }"))

    match_exception = r'.*expected "}" at "c"'
    with pytest.raises(Exception, match=match_exception):
        parse(tokenize("{ if true then { a } b c }"))


def test_var_declaration_exceptions() -> None:
    match_exception = r'.*Initializer required for variable declaration'
    with pytest.raises(Exception, match=match_exception):
        parse(tokenize("var x b"))

    match_exception = r'.*expected "," at "b"'
    with pytest.raises(Exception, match=match_exception):
        parse(tokenize("var x : (a b) = 7"))

    match_exception = r'.*expected "=>" at "c"'
    with pytest.raises(Exception, match=match_exception):
        parse(tokenize("var x : (a , b) c = 7"))


def test_func_def_exceptions() -> None:
    match_exception = r'.*function definitions must appear before top-level expressions'
    with pytest.raises(Exception, match=match_exception):
        parse(tokenize("print_int(f()); fun f(): Int {\nreturn 1;\n}"))

    match_exception = r'.*return expression cannot be followed by any other expression, got "x"'
    with pytest.raises(Exception, match=match_exception):
        parse(tokenize("fun square(x: Int): Int {\nreturn x * x; x\n}"))
