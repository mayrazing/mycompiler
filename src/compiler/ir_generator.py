from typing import Dict
from compiler.ir import IRVar
from compiler.symtab import SymTab
from compiler.tokenizer import Location
from compiler.types import Bool, Int, Type, Unit
import compiler.ast as AST
import compiler.ir as IR


# 'root_types' parameter should map all global names
# 'root_node' parameter is the Module AST node.
def generate_ir(root_types: dict[IRVar, Type],
                root_node: AST.Module) -> dict[str, list[IR.Instruction]]:
    var_types: dict[IRVar, Type] = root_types.copy()

    # 'var_unit' is used when an expression's type is 'Unit'.
    var_unit = IRVar('Unit')
    var_types[var_unit] = Unit

    next_var_number = 1
    next_label_number = 1

    def new_var(type: Type) -> IRVar:
        # Create a new unique IR variable and add it to var_types
        nonlocal next_var_number
        var = IRVar(f'x{next_var_number}')
        var_types[var] = type
        next_var_number += 1
        return var

    def new_label(location: Location, name: str) -> IR.Label:
        nonlocal next_label_number
        #location = Location(1, 1)
        label = IR.Label(location, f'{next_label_number}_{name}')
        next_label_number += 1
        return label

    # We collect the IR instructions dictionary that we generate into this list.
    ins: dict[str, list[IR.Instruction]] = {'main': []}

    control_labels: list[IR.ControlFlow] = []

    # This function visits an AST node, appends IR instructions to 'ins',
    # and returns the IR variable where the emitted IR instructions put the result.
    #
    # It uses a symbol table to map local variables (which may be shadowed) to unique IR variables.
    # The symbol table will be updated in the same way as in the interpreter and type checker.
    def visit_expression(st: SymTab[IRVar], node: AST.Expression,
                         dict_key: str) -> IRVar:
        loc = node.location

        def ir_literal(node: AST.Literal) -> IRVar:
            # Create an IR variable to hold the value,
            # and emit the correct instruction to load the constant value.
            match node.value:
                case bool():
                    var = new_var(Bool)
                    ins[dict_key].append(IR.LoadBoolConst(
                        loc, node.value, var))
                case int():
                    var = new_var(Int)
                    ins[dict_key].append(IR.LoadIntConst(loc, node.value, var))
                case None:
                    var = var_unit
                case _:
                    raise Exception(
                        f"{node.location}: unsupported literal: {type(node.value)}"
                    )

            # Return the variable that holds the loaded value.
            return var

        def ir_identifier(symtab: SymTab[IRVar],
                          node: AST.Identifier) -> IRVar:
            try:
                value_type = symtab.require(node.name)
            except ValueError:
                raise Exception(
                    f'{node.location}: identifier variable "{node.name}" was not found in the context and all parent contexts'
                )

            return value_type

        def ir_unary_op(symtab: SymTab[IRVar], node: AST.UnaryOp) -> IRVar:
            key_op: str = 'unary_' + node.op

            try:
                var_op = symtab.require(key_op)
            except ValueError:
                raise Exception(
                    f'{node.location}: unary operator "{key_op}" was not found in the context and all parent contexts'
                )

            var_unary_clause = visit_expression(symtab, node.unary_clause,
                                                dict_key)
            var_result = new_var(var_types[var_unary_clause])
            ins[dict_key].append(
                IR.Call(node.location, var_op, [var_unary_clause], var_result))
            return var_result

        def ir_binary_op(symtab: SymTab[IRVar], node: AST.BinaryOp) -> IRVar:
            if node.op == '=':
                var_left = visit_expression(symtab, node.left, dict_key)
                var_right = visit_expression(symtab, node.right, dict_key)
                ins[dict_key].append(
                    IR.Copy(node.location, var_right, var_left))
                return var_unit

            elif node.op in ['or', 'and']:
                l_right = new_label(node.location, f'{node.op}_right')
                l_skip = new_label(node.location, f'{node.op}_skip')
                l_end = new_label(node.location, f'{node.op}_end')

                var_left = visit_expression(symtab, node.left, dict_key)
                ins[dict_key].append(
                    IR.CondJump(node.location, var_left, l_right, l_skip))

                ins[dict_key].append(l_right)
                var_right = visit_expression(symtab, node.right, dict_key)
                var_result = new_var(var_types[var_right])
                ins[dict_key].append(
                    IR.Copy(node.location, var_right, var_result))
                ins[dict_key].append(IR.Jump(node.location, l_end))

                ins[dict_key].append(l_skip)
                skip_value = node.op == 'or'
                ins[dict_key].append(
                    IR.LoadBoolConst(node.location, skip_value, var_result))
                ins[dict_key].append(IR.Jump(node.location, l_end))

                ins[dict_key].append(l_end)
                return var_result

            else:
                var_op = st.require(node.op)
                var_left = visit_expression(symtab, node.left, dict_key)
                var_right = visit_expression(symtab, node.right, dict_key)
                var_result = new_var(node.type)
                ins[dict_key].append(
                    IR.Call(loc, var_op, [var_left, var_right], var_result))
            return var_result

        def ir_block(symtab: SymTab[IRVar], node: AST.Block) -> IRVar:
            context = SymTab[IRVar]({}, symtab)
            statements = node.statements

            if statements is None:
                return var_unit

            for statement in statements:
                var_result = visit_expression(context, statement, dict_key)

            return var_result

        def ir_var_declaration(symtab: SymTab[IRVar],
                               node: AST.VarDeclaration) -> IRVar:
            initial_value = visit_expression(symtab, node.initializer,
                                             dict_key)
            var_result = new_var(var_types[initial_value])
            ins[dict_key].append(
                IR.Copy(node.location, initial_value, var_result))
            symtab.add_local(node.name.name, var_result)
            return var_unit

        def ir_if_expression(symtab: SymTab[IRVar],
                             node: AST.IfExpression) -> IRVar:
            if node.else_clause is None:
                l_then = new_label(node.location, 'then')
                l_end = new_label(node.location, 'if_end')

                var_cond = visit_expression(symtab, node.cond, dict_key)
                ins[dict_key].append(
                    IR.CondJump(node.location, var_cond, l_then, l_end))

                ins[dict_key].append(l_then)
                visit_expression(symtab, node.then_clause, dict_key)

                ins[dict_key].append(l_end)
                return var_unit
            else:
                # "if-then-else" case
                l_then = new_label(node.location, 'then')
                l_else = new_label(node.location, 'else')
                l_end = new_label(node.location, 'if_end')

                var_cond = visit_expression(symtab, node.cond, dict_key)
                ins[dict_key].append(
                    IR.CondJump(node.location, var_cond, l_then, l_else))

                ins[dict_key].append(l_then)
                var_then_result = visit_expression(symtab, node.then_clause,
                                                   dict_key)
                ins[dict_key].append(IR.Jump(node.location, l_end))

                ins[dict_key].append(l_else)
                var_else_result = visit_expression(symtab, node.else_clause,
                                                   dict_key)
                ins[dict_key].append(
                    IR.Copy(node.location, var_else_result, var_then_result))

                ins[dict_key].append(l_end)

                return var_then_result

        def ir_while_loop(symtab: SymTab[IRVar], node: AST.WhileLoop) -> IRVar:
            l_start = new_label(node.location, 'while_start')
            l_body = new_label(node.location, 'while_body')
            l_end = new_label(node.location, 'while_end')

            ctrl_label = IR.ControlFlow(node.location, l_start, l_end)
            control_labels.append(ctrl_label)

            ins[dict_key].append(l_start)
            var_cond = visit_expression(symtab, node.cond, dict_key)
            ins[dict_key].append(
                IR.CondJump(node.location, var_cond, l_body, l_end))

            ins[dict_key].append(l_body)
            visit_expression(symtab, node.body, dict_key)
            ins[dict_key].append(IR.Jump(node.location, l_start))

            ins[dict_key].append(l_end)

            control_labels.pop()

            return var_unit

        def ir_function_call(symtab: SymTab[IRVar],
                             node: AST.FunctionCall) -> IRVar:
            context = symtab.require(node.name.name)

            args = []
            if node.args is not None:
                for arg in node.args:
                    args.append(visit_expression(symtab, arg, dict_key))

            var_result = new_var(node.type)
            ins[dict_key].append(
                IR.Call(node.location, context, args, var_result))
            return var_result

        def ir_return(symtab: SymTab[IRVar], node: AST.Return) -> IRVar:
            if node.value is None:
                ins[dict_key].append(IR.Return(node.location, var_unit))
                return var_unit
            else:
                var_result = visit_expression(symtab, node.value, dict_key)
                ins[dict_key].append(IR.Return(node.location, var_result))
                return var_result

        def ir_control_flow(symtab: SymTab[IRVar],
                            node: AST.ControlFlow) -> IRVar:

            if len(control_labels) == 0:
                raise Exception(
                    f'{node.location}: expected at least one while-loop in the outer expression'
                )

            last_ctrl = control_labels[len(control_labels) - 1]
            if node.name == 'break':
                ins[dict_key].append(
                    IR.Jump(node.location, last_ctrl.end_label))
            else:
                ins[dict_key].append(
                    IR.Jump(node.location, last_ctrl.start_label))

            return var_unit

        match node:
            case AST.Literal():
                return ir_literal(node)

            case AST.Identifier():
                return ir_identifier(st, node)

            case AST.UnaryOp():
                return ir_unary_op(st, node)

            case AST.BinaryOp():
                return ir_binary_op(st, node)

            case AST.Block():
                return ir_block(st, node)

            case AST.VarDeclaration():
                return ir_var_declaration(st, node)

            case AST.IfExpression():
                return ir_if_expression(st, node)

            case AST.WhileLoop():
                return ir_while_loop(st, node)

            case AST.FunctionCall():
                return ir_function_call(st, node)

            case AST.Return():
                return ir_return(st, node)

            case AST.ControlFlow():
                return ir_control_flow(st, node)

            case _:
                raise Exception(
                    f"{node.location}: unsupported AST node {node}")

    def visit_func_def(st: SymTab[IRVar], node: AST.FuncDefinition) -> IRVar:
        location = node.location
        func_name = node.name.name
        st_body = SymTab[IRVar](locals={}, parent=st)

        ins[func_name] = []
        if node.args is not None:
            for arg_name, arg_type in node.args.items():
                var_arg = new_var(arg_type.type)
                ins[func_name].append(
                    IR.LoadParam(location, IRVar(arg_name.name), var_arg))
                st_body.add_local(arg_name.name, var_arg)

        visit_expression(st_body, node.body, func_name)
        return var_unit

    # Convert 'root_types' into a SymTab that maps all available global names to IR variables of the same name.
    # In the Assembly generator stage, we will give definitions for these globals.
    # For now, they just need to exist.
    root_symtab = SymTab[IRVar](locals={}, parent=None)
    for v in root_types.keys():
        root_symtab.add_local(v.name, v)

    if root_node.funcs is not None:
        for func_def in root_node.funcs:
            root_symtab.add_local(func_def.name.name, IRVar(func_def.name.name))
        for func_def in root_node.funcs:
            visit_func_def(root_symtab, func_def)

    if root_node.expr is not None:
        var_final_result = visit_expression(root_symtab, root_node.expr,
                                            'main')
        L = Location(line=-1, column=-1)
        if var_types[var_final_result] == Int:
            ins['main'].append(
                IR.Call(L, IRVar('print_int'), [var_final_result],
                        new_var(Int)))

        elif var_types[var_final_result] == Bool:
            ins['main'].append(
                IR.Call(L, IRVar('print_bool'), [var_final_result],
                        new_var(Bool)))

        elif var_types[var_final_result] == Unit:
            ins['main'].append(IR.Return(L, var_unit))

    return ins
