# AGENTS.md

本文件面向在本仓库中工作的 agent（OpenCode/Cursor/Copilot 等）。
目标：统一执行方式、命令与代码风格，降低试错成本。

## 1) 仓库概览

- 技术栈：Python。
- 依赖：`requirements.txt`（`reportlab`、`pdfplumber`、`pytest`）。
- 测试：`unittest` 风格，使用 `pytest` 执行。
- 关键目录：
  - `scripts/`：JSON 缓存管理、PDF 生成、PDF 质检。
  - `templates/`：ReportLab 模板与 PDF 备份归档逻辑。
  - `tests/`：行为回归测试。
  - `docs/guide/`、`install/`：安装与 agent 执行规范。

## 2) 优先阅读文件

1. `README.md`
2. `SKILL.md`
3. `scripts/resume_cache_manager.py`
4. `scripts/generate_final_resume.py`
5. `scripts/check_pdf_quality.py`
6. `templates/modern_resume_template.py`
7. `tests/test_resume_cache_flow.py`

## 3) Build / Lint / Test 命令

> 重点：在本仓库优先使用 `python3 -m pytest`。
> 直接运行 `pytest` 在部分环境会出现 `ModuleNotFoundError`（导入 `scripts`/`templates` 失败）。

### 3.1 安装依赖

```bash
python3 -m pip install -r requirements.txt
```

### 3.2 测试命令（含单测）

```bash
# 全量
python3 -m pytest -q

# 单文件
python3 -m pytest tests/test_resume_cache_flow.py -q

# 单测试类
python3 -m pytest tests/test_resume_cache_flow.py::ResumeCacheFlowTest -q

# 单测试用例（推荐记住此格式）
python3 -m pytest tests/test_resume_cache_flow.py::ResumeCacheFlowTest::test_base_template_lifecycle -q

# 按关键字筛选
python3 -m pytest -k "template and not cleanup" -q

# 仅重跑上次失败
python3 -m pytest --lf -q
```

### 3.3 Lint（仓库未内置强制配置）

仓库中未发现 `pyproject.toml` / `ruff.toml` / `.flake8` / `mypy.ini`。
若本地安装了 Ruff，可运行：

```bash
python3 -m ruff check scripts templates tests
```

### 3.4 Build / 生成与质检

```bash
# JSON -> PDF
python3 scripts/generate_final_resume.py --input-json cache/resume-working.json --output-file 02_10_Name_Backend_Engineer_resume.pdf --output-dir resume_output

# PDF 质量检查
python3 scripts/check_pdf_quality.py resume_output/02_10_Name_Backend_Engineer_resume.pdf
```

## 4) 代码风格与实现约定

### 4.1 Imports

- 顺序：标准库 -> 第三方 -> 本地模块。
- 分组间保留一个空行。
- 禁止 `from x import *`。
- `# noqa` 仅在必要时使用，且保持最小范围。

### 4.2 Formatting

- 遵循 PEP 8，4 空格缩进。
- 长表达式用括号换行，不做无关 reformat。
- 保持现有 docstring 风格（简短、直接）。

### 4.3 Types

- 新代码默认写类型注解。
- 使用现代语法：`list[str]`、`dict[str, Any]`、`X | None`。
- 脚本文件保持 `from __future__ import annotations` 模式。
- 公共函数必须标注返回类型。

### 4.4 Naming

- 函数/变量：`snake_case`。
- 类：`PascalCase`。
- 常量：`UPPER_SNAKE_CASE`。
- 测试文件：`tests/test_*.py`。
- 测试函数：`test_*`，每个测试只验证一个核心行为。

### 4.5 Path 与文件读写

- 使用 `pathlib.Path`，避免 `os.path`。
- 文本读写显式 `encoding="utf-8"`。
- 写文件前先 `mkdir(parents=True, exist_ok=True)`。
- 用户输入路径先 `.expanduser().resolve()`。

### 4.6 CLI 结构

- 使用 `argparse` 解析参数。
- 使用 `main() -> int` 返回退出码。
- 入口固定为：

```python
if __name__ == "__main__":
    raise SystemExit(main())
```

### 4.7 错误处理

- 业务校验失败：抛 `ValueError`。
- CLI 边界层负责捕获异常、输出错误并返回非零退出码。
- 错误消息必须包含关键上下文（文件路径、缺失字段、动作）。
- 除 CLI 边界外，避免宽泛 `except Exception`。

### 4.8 业务约束（不可破坏）

- 保持“技能目录无状态”：不把个性化数据写入仓库。
- 保持现有 PDF 归档策略：
  - `resume_output/*.pdf` 历史文件归档到 `resume_output/backup/{Position}/..._old_N.pdf`。
- 改动 PDF 生成逻辑时，必须同步评估 `check_pdf_quality.py` 的检测规则。

## 5) 测试开发约定

- 修改功能时，优先先改/补测试，再改实现。
- 使用 `tempfile.TemporaryDirectory()` 隔离文件系统副作用。
- 新测试避免依赖外部服务、网络、系统字体。
- 对 CLI 参数、输出格式的变更，必须补回归测试。

## 6) 提交前最小检查

1. `python3 -m pytest -q` 通过。
2. 受影响脚本至少手动执行一条真实命令。
3. 不引入与需求无关的大范围格式化改动。
4. 输出/缓存路径符合 `.gitignore` 预期。

## 7) Cursor / Copilot 规则整合

- 未发现 `.cursorrules`。
- 未发现 `.cursor/rules/`。
- 未发现 `.github/copilot-instructions.md`。
- 当前无需额外合并 Cursor/Copilot 专用规则。

## 8) 平台说明

- 仓库常在 WSL/Linux 环境执行，优先使用 Linux 路径风格。
- `py -3` 在 WSL 可能不可用；默认使用 `python3`。
- 若在 Windows PowerShell，可将 `python3` 替换为 `py -3`。
