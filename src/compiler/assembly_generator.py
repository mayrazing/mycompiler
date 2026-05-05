from compiler.intrinsics import IntrinsicArgs, all_intrinsics
import dataclasses
import compiler.ir as IR


def generate_assembly(instructions: dict[str, list[IR.Instruction]]) -> str:
    assembly_code_lines = []

    def emit(line: str) -> None:
        assembly_code_lines.append(line)

    param_registers = ['%rdi', '%rsi', '%rdx', '%rcx', '%r8', '%r9']

    # Emit initial declarations and stack setup here
    emit('.global main')
    emit('.type main, @function')
    emit('.extern print_int')
    emit('.extern print_bool')
    emit('.extern read_int')

    emit('.section .text')

    for func_name, func_instructions in instructions.items():
        func_locals = Locals(variables=get_func_ir_variables(func_instructions))
        param_count = 0

        emit(f'{func_name}:')
        emit('pushq %rbp')
        emit('movq %rsp, %rbp')
        emit(f'subq ${func_locals.stack_used()}, %rsp')

        for insn in func_instructions:
            emit('# ' + str(insn))
            match insn:
                case IR.Label():
                    #emit('')
                    emit(f'.L{insn.name}:')

                case IR.LoadIntConst():
                    if -2**31 <= insn.value < 2**31:
                        emit(
                            f'movq ${insn.value}, {func_locals.get_ref(insn.dest)}')
                    else:
                        # Due to a quirk of x86-64, we must use a different instruction for large integers.
                        # It can only write to a register, not a memory location,
                        # so we use %rax as a temporary.
                        emit(f'movabsq ${insn.value}, %rax')
                        emit(f'movq %rax, {func_locals.get_ref(insn.dest)}')

                case IR.LoadBoolConst():
                    emit(
                        f'movq ${int(insn.value)}, {func_locals.get_ref(insn.dest)}'
                    )

                case IR.Copy():
                    emit(f'movq {func_locals.get_ref(insn.source)}, %rax')
                    emit(f'movq %rax, {func_locals.get_ref(insn.dest)}')

                case IR.Call():
                    if (instrinsic :=
                            all_intrinsics.get(insn.func.name)) is not None:
                        args = IntrinsicArgs(
                            arg_refs=[func_locals.get_ref(a) for a in insn.args],
                            result_register='%rax',
                            emit=emit)
                        instrinsic(args)
                        emit(f'movq %rax, {func_locals.get_ref(insn.dest)}')
                    else:
                        for i, arg in enumerate(insn.args):
                            emit(
                                f'movq {func_locals.get_ref(arg)}, {param_registers[i]}'
                            )

                        emit(f'call {insn.func.name}')
                        emit(f'movq %rax, {func_locals.get_ref(insn.dest)}')

                case IR.Jump():
                    emit(f'jmp .L{insn.label.name}')

                case IR.CondJump():
                    emit(f'cmpq $0, {func_locals.get_ref(insn.cond)}')
                    emit(f'jne .L{insn.then_label.name}')
                    emit(f'jmp .L{insn.else_label.name}')

                case IR.LoadParam():
                    dest_ref = func_locals.get_ref(insn.dest)
                    emit(f'movq {param_registers[param_count]}, {dest_ref}')
                    param_count += 1

                case IR.Return():
                    if insn.value == IR.IRVar('Unit'):
                        emit('movq $0, %rax')
                    else:
                        emit(f'movq {func_locals.get_ref(insn.value)}, %rax')
                    emit('movq %rbp, %rsp')
                    emit('popq %rbp')
                    emit('ret')

                case _:
                    raise Exception(f'Unknown instruction: {type(insn)}')

        if func_name == 'main':
            emit('movq $0, %rax')

        emit('movq %rbp, %rsp')
        emit('popq %rbp')
        emit('ret')
        emit('')

    return "\n".join(assembly_code_lines)


def get_func_ir_variables(insns: list[IR.Instruction]) -> list[IR.IRVar]:
    result_list: list[IR.IRVar] = []
    result_set: set[IR.IRVar] = set()

    def add(v: IR.IRVar) -> None:
        if v not in result_set:
            result_list.append(v)
            result_set.add(v)

    for insn in insns:
        for field in dataclasses.fields(insn):
            value = getattr(insn, field.name)
            if isinstance(value, IR.IRVar):
                add(value)
            elif isinstance(value, list):
                for v in value:
                    if isinstance(v, IR.IRVar):
                        add(v)

    return result_list


class Locals:
    """Knows the memory location of every local variable."""
    _var_to_location: dict[IR.IRVar, str]
    _stack_used: int

    def __init__(self, variables: list[IR.IRVar]) -> None:
        self._var_to_location = {}
        self._stack_used = 8
        for v in variables:
            if v not in self._var_to_location:
                self._var_to_location[v] = f'-{self._stack_used}(%rbp)'
                self._stack_used += 8

    def get_ref(self, v: IR.IRVar) -> str:
        """Returns an Assembly reference like `-24(%rbp)`
        for the memory location that stores the given variable"""
        return self._var_to_location[v]

    def stack_used(self) -> int:
        """Returns the number of bytes of stack space needed for the local variables."""
        return self._stack_used
