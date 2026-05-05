from compiler.symtab import SymTab, look_up_context
from dataclasses import dataclass
from typing import Any, Callable
import compiler.ast as AST


class BreakException(Exception):
    def __init__(self, location: Any) -> None:
        self.location = location


class ContinueException(Exception):
    def __init__(self, location: Any) -> None:
        self.location = location


class ReturnException(Exception):
    def __init__(self, value: 'Value') -> None:
        self.value = value


Value = int | bool | None | Callable


def interpret(node: AST.Module, symtab: SymTab) -> Value:

    def interpret_expression(node: AST.Expression, symtab: SymTab) -> Value:

        def interpret_identifier(node: AST.Identifier,
                                 symtab: SymTab) -> Value:
            context = look_up_context(symtab, node.name)
            if context is None:
                raise Exception(
                    f'{node.location}: the identifier "{node.name}" was not found in the context and all parent contexts'
                )

            value = context.locals[node.name]
            return value

        def interpret_unary_op(node: AST.UnaryOp, symtab: SymTab) -> Value:
            op = node.op
            exp = interpret_expression(node.unary_clause, symtab)
            if op == '-' and isinstance(exp, int):
                return -exp
            elif op == 'not' and isinstance(exp, bool):
                return not (exp)
            else:
                raise Exception(
                    f'{node.location}: "{op}" was not matched to the value expression("-"=int, "not"=bool)'
                )

        def interpret_binary_op(node: AST.BinaryOp, symtab: SymTab) -> Value:
            a: Any
            b: Any
            if node.op == '=':
                a = node.left
                if isinstance(a, AST.Identifier):
                    context_op = look_up_context(symtab, a.name)
                    if context_op is None:
                        raise Exception(
                            f'{node.location}: "{a.name}" was not found in the context and all parent contexts'
                        )
                    b = interpret_expression(node.right, symtab)
                    context_op.locals[a.name] = b
                    return b
                else:
                    raise Exception(
                        f'{node.location}: left expression must be an identifier if the operator is "{node.op}"'
                    )
            elif node.op == 'or':
                a = interpret_expression(node.left, symtab)
                if a:
                    return True
                else:
                    b = interpret_expression(node.right, symtab)
                    return b
            elif node.op == 'and':
                a = interpret_expression(node.left, symtab)
                if not a:
                    return False
                else:
                    b = interpret_expression(node.right, symtab)
                    return b
            else:
                context_op = look_up_context(symtab, node.op)
                if context_op is None:
                    raise Exception(
                        f'{node.location}: the operator "{node.op}" was not found in the context and all parent contexts'
                    )

                op_value = context_op.locals[node.op]
                if not callable(op_value):
                    raise Exception(
                        f'{node.location}: the type of operator "{node.op}" must be a function, got "{op_value}"'
                    )

                a = interpret_expression(node.left, symtab)
                b = interpret_expression(node.right, symtab)
                return op_value(a, b)

        def interpret_block(node: AST.Block, symtab: SymTab) -> Value:
            context = SymTab({}, symtab)
            statements = node.statements

            if statements is None:
                return None

            value: Value = None
            for statement in statements:
                value = interpret_expression(statement, context)

            return value

        def interpret_var_declaration(node: AST.VarDeclaration,
                                      symtab: SymTab) -> Value:
            var_name: AST.Identifier = node.name
            """support shadow variables"""
            # context_op = look_up_context(symtab, var_name.name)
            # if context_op is not None:
            #     raise Exception(
            #         f'{node.location}: the context already has a local identifier "{var_name.name}"'
            #     )

            value = interpret_expression(node.initializer, symtab)
            symtab.locals[var_name.name] = value
            return None

        def interpret_if_expression(node: AST.IfExpression,
                                    symtab: SymTab) -> Value:
            cond_value = interpret_expression(node.cond, symtab)
            if not isinstance(cond_value, bool):
                raise Exception(
                    f'{node.location}: only support the bool value of condition expression, got "{cond_value}"'
                )

            if node.else_clause is None:
                if cond_value:
                    return interpret_expression(node.then_clause, symtab)
                return None
            else:
                if cond_value:
                    return interpret_expression(node.then_clause, symtab)
                else:
                    return interpret_expression(node.else_clause, symtab)

        def interpret_while_loop(node: AST.WhileLoop, symtab: SymTab) -> Value:
            while True:
                cond_value = interpret_expression(node.cond, symtab)
                if not isinstance(cond_value, bool):
                    raise Exception(
                        f'{node.location}: only support the bool value of condition expression, got "{cond_value}"'
                    )
                if not cond_value:
                    break
                try:
                    interpret_expression(node.body, symtab)
                except BreakException:
                    break
                except ContinueException:
                    continue
            return None

        def interpret_function_call(node: AST.FunctionCall,
                                    symtab: SymTab) -> Value:
            func_name: AST.Identifier = node.name
            context_op = look_up_context(symtab, func_name.name)
            if context_op is None:
                raise Exception(
                    f'{node.location}: function "{func_name.name}" was not defined in the context and all parent contexts'
                )

            op_value = context_op.locals[func_name.name]
            if not callable(op_value):
                raise Exception(
                    f'{node.location}: the type of function name must be a function, got "{op_value}"'
                )

            args = []
            if node.args is not None:
                num_args = len(node.args)
                if num_args > 6:
                    raise Exception(
                        f'{node.location}: the implementation is allowed to limit the number of allowed arguments to 6, got "{num_args}"'
                    )

                for i in range(num_args):
                    exp_value = interpret_expression(node.args[i], symtab)
                    args.append(exp_value)

            return op_value(*args)

        def interpret_return(node: AST.Return, symtab: SymTab) -> Value:
            val = interpret_expression(
                node.value, symtab) if node.value is not None else None
            raise ReturnException(val)

        match node:
            case AST.Literal():
                return node.value

            case AST.Identifier():
                return interpret_identifier(node, symtab)

            case AST.UnaryOp():
                return interpret_unary_op(node, symtab)

            case AST.BinaryOp():
                return interpret_binary_op(node, symtab)

            case AST.Block():
                return interpret_block(node, symtab)

            case AST.VarDeclaration():
                return interpret_var_declaration(node, symtab)

            case AST.IfExpression():
                return interpret_if_expression(node, symtab)

            case AST.WhileLoop():
                return interpret_while_loop(node, symtab)

            case AST.FunctionCall():
                return interpret_function_call(node, symtab)

            case AST.Return():
                return interpret_return(node, symtab)

            case AST.ControlFlow():
                if node.name == 'break':
                    raise BreakException(node.location)
                elif node.name == 'continue':
                    raise ContinueException(node.location)
                else:
                    raise Exception(
                        f'{node.location}: unsupported control flow "{node.name}"'
                    )

            case _:
                raise Exception(
                    f'{node.location}: unsupported AST expression node "{node}"'
                )

    def interpret_func_definition(node: AST.FuncDefinition,
                                  symtab: SymTab) -> Value:
        def func(*args: Value) -> Value:
            expected_num_args = len(node.args) if node.args is not None else 0
            if len(args) != expected_num_args:
                raise Exception(
                    f'function "{node.name.name}" expected {expected_num_args} arguments, got {len(args)}'
                )

            local: SymTab = SymTab({}, symtab)
            if node.args is not None:
                for (param, _), val in zip(node.args.items(), args):
                    local.locals[param.name] = val
            try:
                return interpret_expression(node.body, local)
            except ReturnException as e:
                return e.value
            except BreakException as exc:
                raise Exception(f'{exc.location}: break outside of a loop')
            except ContinueException as exc:
                raise Exception(f'{exc.location}: continue outside of a loop')

        symtab.locals[node.name.name] = func
        return None

    if node.funcs is not None:
        for func_def in node.funcs:
            interpret_func_definition(func_def, symtab)

    expr_value: Value = None
    if node.expr is not None:
        try:
            expr_value = interpret_expression(node.expr, symtab)
        except BreakException as exc:
            raise Exception(f'{exc.location}: break outside of a loop')
        except ContinueException as exc:
            raise Exception(f'{exc.location}: continue outside of a loop')
        except ReturnException:
            raise Exception('return outside of a function')

    return expr_value
