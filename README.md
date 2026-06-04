# mycompiler

A compiler written in Python that translates a statically-typed, C-like language all the way to native x86-64 binaries.

[中文](README.zh.md)

## Features

- Full compilation pipeline: Tokenizer → Parser → Type Checker → IR Generator → Assembly Generator → Assembler
- Data types: `Int`, `Bool`, `Unit`
- Variables with initializers and assignment statements (right-associative)
- Binary operators: `+`, `-`, `*`, `/`, `%`, `==`, `!=`, `<`, `<=`, `>`, `>=`, `and`, `or` with precedence and left-associativity
- Unary operators: `-`, `not`
- `if/then/else` expressions
- `while` loops with `break` and `continue`
- Function definitions and calls (recursion and mutual recursion supported)
- `return` expressions
- Built-in library functions: `print_int`, `read_int`, `print_bool`
- Block scoping
- Single-line (`//`) and multi-line (`/* */`) comments
- Unit tests and end-to-end tests

## Architecture

```
Source Code
    │
    ▼
Tokenizer  →  token list
    │
    ▼
Parser     →  AST
    │
    ▼
Type Checker  →  typed AST
    │
    ▼
IR Generator  →  IR instructions (per function)
    │
    ▼
Assembly Generator  →  x86-64 assembly
    │
    ▼
Assembler  →  native binary
```

## Getting Started

### Requirements

- [Pyenv](https://github.com/pyenv/pyenv) — install Python 3.11+
  - Recommended: `curl https://pyenv.run | bash`
- [Poetry](https://python-poetry.org/) — manage dependencies
  - Recommended: `curl -sSL https://install.python-poetry.org | python3 -`

### Install

```bash
# Install the Python version specified in .python-version
pyenv install

# Install dependencies
poetry install
```

> If `pyenv install` warns about `_tkinter`, you can safely ignore it.
> If Poetry doesn't pick up pyenv's Python, run `poetry env remove --all` then `poetry install` again.

## Usage

```bash
./compiler.sh <command> [source_file]
```

If `source_file` is omitted, source code is read from stdin.

| Command | Description |
|---------|-------------|
| `tokenize` | Print the token list |
| `parse` | Print the AST |
| `interpret` | Interpret and run the source code |
| `typecheck` | Type-check and print the inferred type |
| `ir` | Print IR instructions per function |
| `asm` | Print generated x86-64 assembly |
| `compile` | Compile to a native binary (`./compiled_program`) |

**Example:**

```bash
# Compile and run a source file
./compiler.sh compile examples/hello.txt
./compiled_program
```

## Development

Run type checks and all tests:

```bash
./check.sh
```

Or individually:

```bash
poetry run mypy .
poetry run pytest -vv
```

### IDE Setup

Recommended VS Code extensions:

- Python
- Pylance
- autopep8

## License

Licensed under the [Apache License 2.0](LICENSE).

