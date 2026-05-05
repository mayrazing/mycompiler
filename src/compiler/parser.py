from compiler.tokenizer import Location, Token, tokenize
from typing import Dict, Literal
import compiler.ast as AST
"""
Given the well-defined precedence and associativity of the operators
(from lowest precedence to highest precedence)
------------------------------------------------------------------------
Name                       Operators                       Associativity
Assignment                    =                               Right
Logical or                    or                              Left
Logical and                   and                             Left
Equality                    ==  !=                            Left
Comparison                 > >= < <=                          Left
Term                         +  -                             Left
Factor                       * / %                            Left
Unary                       not  -                            Right
"""
left_associative_binary_operators = [
    ['or'],
    ['and'],
    ['==', '!='],
    ['<', '<=', '>', '>='],
    ['+', '-'],
    ['*', '/', '%'],
]


def parse(tokens: list[Token]) -> AST.Module:
    # This keeps track of which token we're looking at.
    pos = 0

    # 'peek()' returns the token at 'pos', or a special 'end' token if we're past the end of the token list.
    # This way we don't have to worry about going past the end elsewhere.
    def peek() -> Token:
        if pos < len(tokens):
            return tokens[pos]

        return Token(type='END',
                     text='<end of file>',
                     location=tokens[-1].location)

    # 'backtrack_peek()' returns the token before 'pos', or tokens[0] if we're at the first of the token list.
    def backtrack_peek() -> Token:
        if pos == 0:
            return tokens[0]

        return tokens[pos - 1]

    # 'consume(expected)' returns the token at 'pos' and moves 'pos' forward.
    # If the optional parameter 'expected' is given, it checks that the token being consumed has that text.
    # If 'expected' is a list, then the token must have one of the texts in the list.
    def consume(expected: str | list[str] | None = None) -> Token:
        token = peek()
        if isinstance(expected, str) and token.text != expected:
            raise Exception(f'{token.location}: expected "{expected}"')

        if isinstance(expected, list) and token.text not in expected:
            comma_separated = ", ".join([f'"{e}"' for e in expected])
            raise Exception(
                f'{token.location}: expected one of: {comma_separated}')

        nonlocal pos
        pos += 1
        return token

    # This is the parsing function for integer literals.
    # It checks that we're looking at an integer literal token,
    # moves past it, and returns a 'Literal' AST node
    # containing the integer from the token.
    def parse_int_literal() -> AST.Literal:
        token = consume()
        return AST.Literal(token.location, int(token.text))

    def parse_identifier() -> AST.Identifier:
        token = consume()
        return AST.Identifier(token.location, str(token.text))

    def parse_bool_literal() -> AST.Literal:
        token = consume()
        if token.text == 'true':
            return AST.Literal(token.location, True)
        return AST.Literal(token.location, False)

    def parse_parentheses() -> AST.Expression:
        consume('(')
        expr = parse_expression()
        consume(')')
        return expr

    def parse_block() -> AST.Block:
        location = peek().location
        block = AST.Block(location, '{}', None)
        consume('{')

        while peek().text != '}':
            if block.statements is None:
                block.statements = []

            if peek().type == 'END':
                raise Exception(
                    f'{peek().location}: expected "}}" at "{peek().text}"')

            if peek().text == ';':
                raise Exception(
                    f'{peek().location}: expected expression at "{peek().text}"'
                )

            block.statements.append(parse_expression())
            if peek().text == ';':
                consume(';')
                if peek().text == '}':
                    location = peek().location
                    block.statements.append(AST.Literal(location, None))
                continue

            if peek().text in ['{', '}']:
                continue

            if backtrack_peek().text != '}':
                raise Exception(
                    f'{peek().location}: expected "}}" at "{peek().text}"')

        consume('}')
        return block

    def parse_if_expression() -> AST.Expression:
        location = peek().location
        operator_token = consume('if')
        operator = operator_token.text
        cond = parse_expression()
        if peek().text != 'then':
            raise Exception(
                f'{peek().location}: expected "then" at "{peek().text}"')
        consume('then')
        then_clause = parse_expression()
        else_clause = None
        if peek().text == 'else':
            consume('else')
            else_clause = parse_expression()

        return AST.IfExpression(location, operator, cond, then_clause,
                                else_clause)

    def parse_while_loop() -> AST.Expression:
        location = peek().location
        operator_token = consume('while')
        operator = operator_token.text
        if peek().text == 'do':
            raise Exception(
                f'{peek().location}: expected expression except the keyword "do"'
            )

        cond = parse_expression()
        if peek().text != 'do':
            raise Exception(
                f'{peek().location}: expected the keyword "do" at "{peek().text}"'
            )

        consume('do')
        if peek().type == "END":
            raise Exception(
                f'{peek().location}: expected expression at "{peek().text}"')

        body = parse_expression()
        return AST.WhileLoop(location, operator, cond, body)

    def parse_declared_type_expr() -> AST.TypeExpr:
        if peek().text != '(':
            return get_basic_type_expr()
        else:
            return get_func_type_expr()

    def get_basic_type_expr() -> AST.BasicTypeExpr:
        location = peek().location
        type_token = consume()
        return AST.BasicTypeExpr(location, type_token.text)

    def get_func_type_expr() -> AST.FuncTypeExpr:
        location = peek().location
        params: list[AST.BasicTypeExpr] | None = None
        consume('(')

        while peek().text != ')':
            if params is None:
                params = []

            params.append(get_basic_type_expr())
            if peek().text == ',':
                consume(',')
                continue

            if peek().text != ')':
                raise Exception(
                    f'{peek().location}: expected "," at "{peek().text}"')

        consume(')')

        if peek().text != '=>':
            raise Exception(
                f'{peek().location}: expected "=>" at "{peek().text}"')

        consume('=>')
        result = get_basic_type_expr()
        return AST.FuncTypeExpr(location, params, result)

    def parse_var_declaration() -> AST.Expression:
        location = peek().location
        operator_token = consume('var')
        operator = operator_token.text
        var_name = parse_identifier()
        declared_type_exp = None

        if peek().text == ':':
            consume(':')
            declared_type_exp = parse_declared_type_expr()

        if peek().text != '=':
            raise Exception(
                f'{peek().location}: Initializer required for variable declaration'
            )
        consume('=')
        initializer = parse_expression()
        return AST.VarDeclaration(location, operator, var_name,
                                  declared_type_exp, initializer)

    def parse_function_call(expected: AST.Identifier) -> AST.FunctionCall:
        location = peek().location
        operator = "call"
        args = None
        consume('(')

        while peek().text != ')':
            if args is None:
                args = []

            args.append(parse_expression())
            if peek().text == ',':
                consume(',')
                continue

            if peek().text != ')':
                raise Exception(
                    f'{peek().location}: expected "," at "{peek().text}"')

        consume(')')
        return AST.FunctionCall(location, operator, expected, args)

    def parse_return() -> AST.Expression:
        location = peek().location
        operator_token = consume('return')
        operator = operator_token.text

        if peek().text == '}':
            value = None
        else:
            value = parse_expression()
        """The return expression can only be followed by a semicolon, 
        which consumes the semicolon, does not parse to Unit, 
        and throws an error if there is anything else"""
        if peek().text == ';':
            consume(';')

        if peek().type != 'END' and peek().text not in ['}', 'else']:
            raise Exception(
                f'{peek().location}: return expression cannot be followed by any other expression, got "{peek().text}"'
            )

        return AST.Return(location, operator, value)

    def parse_break_and_continue() -> AST.ControlFlow:
        token = consume()
        return AST.ControlFlow(token.location, token.text)

    def parse_primary() -> AST.Expression:
        if peek().text == '(':
            return parse_parentheses()

        if peek().text == '{':
            block = parse_block()
            return block

        if peek().text == 'if':
            return parse_if_expression()

        if peek().text == 'while':
            return parse_while_loop()

        if peek().text == 'var':
            return parse_var_declaration()

        if peek().text == 'return':
            return parse_return()

        if peek().text in ['break', 'continue']:
            return parse_break_and_continue()

        if peek().text in ['-', 'not']:
            return parse_unary_op()

        if peek().type == 'BOOL':
            return parse_bool_literal()

        if peek().type == 'INTEGER':
            return parse_int_literal()

        if peek().type == 'IDENTIFIER':
            identifier = parse_identifier()
            if peek().text == '(':
                return parse_function_call(identifier)

            return identifier

        raise Exception(
            f'{peek().location}: expected expression at "{peek().text}"')

    def parse_unary_op() -> AST.Expression:
        location = peek().location
        operator_token = consume()
        operator = operator_token.text

        if peek().type == "END":
            raise Exception(
                f'{peek().location}: expected expression at "{peek().text}"')

        unary_clause = parse_primary()
        unary_op = AST.UnaryOp(location, operator, unary_clause)
        return unary_op

    # def parse_factor_op() -> AST.Expression:
    #     left = parse_primary()

    #     while peek().text in ['*', '/', '%']:
    #         location = peek().location
    #         operator_token = consume()
    #         operator = operator_token.text
    #         right = parse_primary()
    #         left = AST.BinaryOp(location, left, operator, right)

    #     return left

    # def parse_term_op() -> AST.Expression:
    #     left = parse_factor_op()

    #     while peek().text in ['+', '-']:
    #         location = peek().location
    #         operator_token = consume()
    #         operator = operator_token.text
    #         right = parse_factor_op()
    #         left = AST.BinaryOp(location, left, operator, right)

    #     return left

    # def parse_comparison_op() -> AST.Expression:
    #     left = parse_term_op()

    #     while peek().text in ['<', '>', '<=', '>=']:
    #         location = peek().location
    #         operator_token = consume()
    #         operator = operator_token.text
    #         right = parse_term_op()
    #         left = AST.BinaryOp(location, left, operator, right)

    #     return left

    # def parse_equality_op() -> AST.Expression:
    #     left = parse_comparison_op()

    #     while peek().text in ['==', '!=']:
    #         location = peek().location
    #         operator_token = consume()
    #         operator = operator_token.text
    #         right = parse_comparison_op()
    #         left = AST.BinaryOp(location, left, operator, right)

    #     return left

    # def parse_logical_and_op() -> AST.Expression:
    #     left = parse_equality_op()

    #     while peek().text == 'and':
    #         location = peek().location
    #         operator_token = consume()
    #         operator = operator_token.text
    #         right = parse_equality_op()
    #         left = AST.BinaryOp(location, left, operator, right)

    #     return left

    # def parse_logical_or_op() -> AST.Expression:
    #     left = parse_logical_and_op()

    #     while peek().text == 'or':
    #         location = peek().location
    #         operator_token = consume()
    #         operator = operator_token.text
    #         right = parse_logical_and_op()
    #         left = AST.BinaryOp(location, left, operator, right)

    #     return left

    def parse_left_associative_op(index: int) -> AST.Expression:
        left_index = index + 1
        if left_index < len(left_associative_binary_operators):
            return parse_left_associativity(left_index)
        return parse_primary()

    def parse_left_associativity(index: int) -> AST.Expression:
        left = parse_left_associative_op(index)
        expected_op = left_associative_binary_operators[index]
        while peek().text in expected_op:
            location = peek().location
            operator_token = consume()
            operator = operator_token.text
            right = parse_left_associative_op(index)
            left = AST.BinaryOp(location, left, operator, right)

        return left

    def parse_right_associativity() -> AST.Expression:
        left = parse_left_associativity(0)

        if peek().text == '=':
            # right-associative
            location = peek().location
            operator_token = consume()
            operator = operator_token.text
            right = parse_right_associativity()
            left = AST.BinaryOp(location, left, operator, right)

        return left

    def parse_expression() -> AST.Expression:
        # Parse the first term.
        left = parse_left_associativity(0)

        if peek().text == '=':
            # right-associative
            location = peek().location
            operator_token = consume()
            operator = operator_token.text
            right = parse_right_associativity()
            left = AST.BinaryOp(location, left, operator, right)

        return left

    def parser_func_definition() -> AST.FuncDefinition:
        location = peek().location
        consume('fun')
        name = parse_identifier()
        args: Dict[AST.Identifier, AST.BasicTypeExpr] = {}
        consume('(')

        while peek().text != ')':
            arg_name = parse_identifier()
            consume(':')
            arg_type = get_basic_type_expr()
            args[arg_name] = arg_type

            if peek().text == ',':
                consume(',')
                continue

            if peek().text != ')':
                raise Exception(
                    f'{peek().location}: expected "," at "{peek().text}"')

        loc = peek().location
        consume(')')
        if peek().text == ':':
            consume(':')
            return_type = get_basic_type_expr()
        else:
            loc.column = -1
            return_type = AST.BasicTypeExpr(loc, 'Unit')

        if peek().text == '{':
            body = parse_block()
            if not args:
                return AST.FuncDefinition(location, name, None, return_type,
                                          body)

            return AST.FuncDefinition(location, name, args, return_type, body)

        raise Exception(
            f'{peek().location}: expected a block expression started with"{{" at "{peek().text}"'
        )

    def parser_top_level_expression(
            exprs: list[AST.Expression]) -> AST.Expression:
        if len(exprs) == 1:
            # only one expression
            return exprs[0]

        # Construct the bolck expression to store many expressions
        location = tokens[0].location
        location.column = -1
        block = AST.Block(location, '{}', exprs)
        return block

    # This is our main parsing function for this example.
    def parser_module() -> AST.Module:
        funcs: list[AST.FuncDefinition] = []
        exprs: list[AST.Expression] = []

        while peek().type != 'END':
            if peek().text == 'fun':
                if len(exprs) != 0:
                    raise Exception(
                        f'{peek().location}: function definitions must appear before top-level expressions'
                    )
                funcs.append(parser_func_definition())
                continue

            exprs.append(parse_expression())
            if peek().text == ';':
                consume(';')

                if peek().type == 'END':
                    location = peek().location
                    exprs.append(AST.Literal(location, None))

            elif peek().type != 'END':
                raise Exception(
                    f'{peek().location}: expected ";" at "{peek().text}"')

        if len(exprs) == 0:
            if len(funcs) == 0:
                raise Exception(
                    f'{peek().location}: expected some content at "{peek().text}"'
                )

            return AST.Module(funcs, None)
        else:
            if len(funcs) == 0:
                return AST.Module(None, parser_top_level_expression(exprs))

            return AST.Module(funcs, parser_top_level_expression(exprs))

    """parser start here"""
    return parser_module()
