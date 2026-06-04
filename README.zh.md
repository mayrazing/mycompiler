# mycompiler

一个用 Python 实现的编译器，将静态类型的类 C 语言编译为原生 x86-64 二进制文件。

[English](README.md)

## 功能特性 

- 完整编译流水线：词法分析器 → 语法分析器 → 类型检查器 → IR 生成器 → 汇编生成器 → 汇编器
- 数据类型：`Int`、`Bool`、`Unit`
- 变量声明与赋值语句（右结合）
- 二元运算符：`+`、`-`、`*`、`/`、`%`、`==`、`!=`、`<`、`<=`、`>`、`>=`、`and`、`or`，支持优先级与左结合性
- 一元运算符：`-`、`not`
- `if/then/else` 表达式
- `while` 循环，支持 `break` 和 `continue`
- 函数定义与调用（支持递归与互递归）
- `return` 表达式
- 内置库函数：`print_int`、`read_int`、`print_bool`
- 块级作用域
- 单行注释（`//`）与多行注释（`/* */`）
- 单元测试与端对端测试支持

## 架构

```
源代码
    │
    ▼
词法分析器（Tokenizer）  →  token 列表
    │
    ▼
语法分析器（Parser）     →  AST
    │
    ▼
类型检查器（Type Checker）  →  带类型 AST
    │
    ▼
IR 生成器（IR Generator）  →  IR 指令（按函数）
    │
    ▼
汇编生成器（Assembly Generator）  →  x86-64 汇编
    │
    ▼
汇编器（Assembler）  →  原生二进制文件
```

## 快速开始

### 环境要求

- [Pyenv](https://github.com/pyenv/pyenv) — 安装 Python 3.11+
  - 推荐安装方式：`curl https://pyenv.run | bash`
- [Poetry](https://python-poetry.org/) — 管理依赖
  - 推荐安装方式：`curl -sSL https://install.python-poetry.org | python3 -`

### 安装

```bash
# 安装 .python-version 中指定的 Python 版本
pyenv install

# 安装依赖
poetry install
```

> 若 `pyenv install` 提示 `_tkinter` 相关警告，可忽略。
> 若 Poetry 无法识别 pyenv 的 Python，执行 `poetry env remove --all` 后再重新 `poetry install`。

## 使用方式

```bash
./compiler.sh <命令> [源文件]
```

若省略 `源文件`，则从标准输入读取源码。

| 命令 | 说明 |
|------|------|
| `tokenize` | 输出 token 列表 |
| `parse` | 输出 AST |
| `interpret` | 解释执行源代码 |
| `typecheck` | 类型检查并输出推断类型 |
| `ir` | 输出各函数的 IR 指令 |
| `asm` | 输出生成的 x86-64 汇编代码 |
| `compile` | 编译为原生二进制文件（`./compiled_program`） |

**示例：**

```bash
# 编译并运行源文件
./compiler.sh compile tests/test_programs/function_case.txt
./compiled_program
```

## 开发

运行类型检查与全部测试：

```bash
./check.sh
```

或分别执行：

```bash
poetry run mypy .
poetry run pytest -vv
```

### IDE 配置

推荐 VS Code 扩展：

- Python
- Pylance
- autopep8

## 许可证

采用 [Apache License 2.0](LICENSE) 授权。
