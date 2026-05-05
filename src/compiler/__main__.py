import sys

from compiler.assembler import assemble
from compiler.assembly_generator import generate_assembly
from compiler.interpreter import interpret
from compiler.ir_generator import generate_ir
from compiler.parser import parse
from compiler.symtab import SymTab, global_interpreter_locals, top_level_type_locals
from compiler.tokenizer import tokenize
from compiler.type_checker import typecheck
from compiler.types import root_types

# TODO(student): add more commands as needed
usage = f"""
Usage: {sys.argv[0]} <command> [source_code_file]

Command 'interpret':
    Runs the interpreter on source code.

Common arguments:
    source_code_file        Optional. Defaults to standard input if missing.
 """.strip() + "\n"


def main() -> int:
    command: str | None = None
    input_file: str | None = None
    for arg in sys.argv[1:]:
        if arg in ['-h', '--help']:
            print(usage)
            return 0
        elif arg.startswith('-'):
            raise Exception(f"Unknown argument: {arg}")
        elif command is None:
            command = arg
        elif input_file is None:
            input_file = arg
        else:
            raise Exception("Multiple input files not supported")

    def read_source_code() -> str:
        if input_file is not None:
            with open(input_file) as f:
                return f.read()
        else:
            return sys.stdin.read()

    if command is None:
        print(f"Error: command argument missing\n\n{usage}", file=sys.stderr)
        return 1

    source_code = read_source_code()
    if command == 'tokenize':
        tokens = tokenize(source_code)
        tokens_output = "".join(str(item) for item in tokens)
        print(f'{tokens_output}')

    elif command == 'parse':
        tokens = tokenize(source_code)
        ast_node = parse(tokens)
        print(f'{ast_node}')

    elif command in ['interpret', 'interprete']:
        tokens = tokenize(source_code)
        ast_node = parse(tokens)
        interpreter_symtab: SymTab = SymTab(
            locals=dict(global_interpreter_locals), parent=None)
        executed_result = interpret(ast_node, interpreter_symtab)
        print(f'{executed_result}')

    elif command == 'typecheck':
        tokens = tokenize(source_code)
        ast_node = parse(tokens)
        symtab: SymTab = SymTab(locals=dict(top_level_type_locals), parent=None)
        verified_result = typecheck(ast_node, symtab)
        print(f'{verified_result}')

    elif command == 'ir':
        tokens = tokenize(source_code)
        ast_node = parse(tokens)
        symtab = SymTab(locals=dict(top_level_type_locals), parent=None)
        typecheck(ast_node, symtab)
        ir_instructions = generate_ir(root_types, ast_node)
        for func_name, func_instructions in ir_instructions.items():
            print(f'{func_name}:')
            print("\n".join([str(ins) for ins in func_instructions]))

    elif command == 'asm':
        tokens = tokenize(source_code)
        ast_node = parse(tokens)
        symtab = SymTab(locals=dict(top_level_type_locals), parent=None)
        typecheck(ast_node, symtab)
        ir_instructions = generate_ir(root_types, ast_node)
        asm_code = generate_assembly(ir_instructions)
        print(asm_code)

    elif command == 'compile':
        tokens = tokenize(source_code)
        ast_node = parse(tokens)
        symtab = SymTab(locals=dict(top_level_type_locals), parent=None)
        typecheck(ast_node, symtab)
        ir_instructions = generate_ir(root_types, ast_node)
        asm_code = generate_assembly(ir_instructions)
        assemble(asm_code, 'compiled_program')

    else:
        print(f"Error: unknown command: {command}\n\n{usage}", file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
