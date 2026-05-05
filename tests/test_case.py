from dataclasses import dataclass
import os
import subprocess
import sys

from compiler.assembler import assemble
from compiler.assembly_generator import generate_assembly
from compiler.ir_generator import generate_ir
from compiler.parser import parse
from compiler.symtab import SymTab, top_level_type_locals
from compiler.tokenizer import tokenize
from compiler.type_checker import typecheck
from compiler.types import root_types


@dataclass(frozen=True)
class Case:
    name: str
    inputs: str
    outputs: list[str]
    source_code: str


def find_test_cases(directory: str) -> list[Case]:
    test_cases = []
    current_path = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_path)
    for filename in os.listdir(f'{current_dir}/{directory}'):
        if filename.endswith('.txt'):
            testfile = os.path.join(f'{current_dir}/{directory}', filename)

            with open(testfile, 'r') as f:
                l_input = ''
                l_output: list[str] = []
                l_source_code = ''

                for line_number, line in enumerate(f, start=1):
                    line = line.strip()
                    if line.startswith('---'):
                        testcase = Case(f'{filename}_{line_number}',
                                            l_input, l_output, l_source_code)
                        test_cases.append(testcase)
                        l_input = ''
                        l_output = []
                        l_source_code = ''

                    elif line.startswith('input'):
                        start_line = len('input ')
                        l_input += f'{line[start_line:]}\n'

                    elif line.startswith('prints'):
                        start_line = len('prints ')
                        l_output.append(f'{line[start_line:]}')

                    else:
                        l_source_code += f'{line}\n'

    return test_cases


dir_testcase = 'test_programs'
for test_case in find_test_cases(dir_testcase):

    def run_test_case(testcase: Case = test_case) -> None:
        tokens = tokenize(testcase.source_code)
        ast_node = parse(tokens)
        symtab = SymTab(locals=dict(top_level_type_locals), parent=None)
        typecheck(ast_node, symtab)
        ir_instructions = generate_ir(root_types, ast_node)
        asm_code = generate_assembly(ir_instructions)
        assemble(asm_code, './compiled_program_test')

        compiled_outputs = subprocess.check_output(
            './compiled_program_test', input=testcase.inputs,
            text=True).strip().split('\n')

        assert ''.join(compiled_outputs) == ''.join(
            testcase.outputs), f"Test case {testcase.name} failed"

    sys.modules[__name__].__setattr__(f'test_{test_case.name}', run_test_case)
