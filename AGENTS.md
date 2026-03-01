# AGENTS.md
本文件面向在本仓库工作的 agent（OpenCode / Claude Code / Cursor / Copilot 等）。
目标：统一命令入口、避免环境踩坑、保持实现风格一致。

## 1) 仓库定位
- 技术栈：Python（脚本 + PDF 模板 + 测试）。
- 核心功能：缓存管理、PDF 生成、PDF 质检、auto-fit 布局调参。
- 依赖：`requirements.txt`（`reportlab`、`pdfplumber`、`pytest`）。
- 测试风格：`unittest` 编写，`pytest` 执行。

## 2) 目录速览
- `scripts/`：`resume_cache_manager.py`、`generate_final_resume.py`、`check_pdf_quality.py`、`layout_auto_tuner.py`
- `templates/`：`modern_resume_template.py`、`layout_settings.py`
- `tests/`：回归测试
- `references/`：策略和流程资料
- `docs/guide/`、`install/`：安装和执行入口

## 3) 推荐阅读顺序
1. `README.md`
2. `SKILL.md`
3. `scripts/resume_cache_manager.py`
4. `scripts/generate_final_resume.py`
5. `scripts/check_pdf_quality.py`
6. `templates/modern_resume_template.py`
7. `tests/test_resume_cache_flow.py`

## 4) Build / Lint / Test 命令

### 4.1 安装依赖
```bash
python3 -m pip install -r requirements.txt
```

### 4.2 测试（优先 `python3 -m pytest`）
说明：直接 `pytest` 常出现 `ModuleNotFoundError: scripts/templates`。

```bash
# 全量
python3 -m pytest -q

# 单文件
python3 -m pytest tests/test_resume_cache_flow.py -q

# 单类
python3 -m pytest tests/test_resume_cache_flow.py::ResumeCacheFlowTest -q

# 单用例（重点掌握）
python3 -m pytest tests/test_resume_cache_flow.py::ResumeCacheFlowTest::test_base_template_lifecycle -q

# 另一个单用例示例
python3 -m pytest tests/test_generate_final_resume_cli_args.py::GenerateFinalResumeCliArgsTest::test_parse_args_layout_defaults -q

# 关键字筛选
python3 -m pytest -k "layout and not auto" -q

# 重跑上次失败
python3 -m pytest --lf -q
```

### 4.3 Lint（可选）
未发现 `pyproject.toml`、`ruff.toml`、`.flake8`、`mypy.ini`。

```bash
python3 -m ruff check scripts templates tests
```

### 4.4 运行脚本（生成/质检）
```bash
# 重置工作缓存
python3 scripts/resume_cache_manager.py reset

# 从 base 模板生成 working 缓存
python3 scripts/resume_cache_manager.py template-use --workspace .

# 生成 PDF（普通模式）
python3 scripts/generate_final_resume.py --input-json cache/resume-working.json --output-file 02_10_Name_Backend_Engineer_resume.pdf --output-dir resume_output

# 生成 PDF（auto-fit 模式）
python3 scripts/generate_final_resume.py --input-json cache/resume-working.json --output-file 02_10_Name_Backend_Engineer_resume.pdf --output-dir resume_output --auto-fit

# PDF 质量检查
python3 scripts/check_pdf_quality.py resume_output/02_10_Name_Backend_Engineer_resume.pdf

# 质量检查 JSON 报告
python3 scripts/check_pdf_quality.py resume_output/02_10_Name_Backend_Engineer_resume.pdf --json
```

## 5) 代码风格指南

### 5.1 Imports
- 顺序：标准库 -> 第三方 -> 本地模块。
- 分组间一个空行。
- 禁止 `from x import *`。
- `# noqa` 仅用于必要行，最小化范围。

### 5.2 Formatting
- 遵循 PEP 8，4 空格缩进。
- 长表达式优先括号换行，避免无关 reformat。
- 保持当前 docstring 风格：简洁、可执行。

### 5.3 Types
- 新增/修改函数默认加类型注解。
- 使用 `list[str]`、`dict[str, Any]`、`X | None`。
- 脚本保持 `from __future__ import annotations`。
- 公共函数必须标注返回类型。

### 5.4 Naming
- 函数/变量：`snake_case`
- 类：`PascalCase`
- 常量：`UPPER_SNAKE_CASE`
- 测试文件：`tests/test_*.py`
- 测试方法：`test_*`，每个测试只验证一个核心行为

### 5.5 Path 与 I/O
- 使用 `pathlib.Path`，避免 `os.path`。
- 文本读写显式 `encoding="utf-8"`。
- 写入前先 `mkdir(parents=True, exist_ok=True)`。
- 用户输入路径统一 `.expanduser().resolve()`。

### 5.6 CLI 结构
- 使用 `argparse`。
- 采用 `main() -> int` 并返回退出码。
- 入口保持：

```python
if __name__ == "__main__":
    raise SystemExit(main())
```

### 5.7 错误处理
- 参数/数据校验失败：`ValueError`。
- 文件缺失：`FileNotFoundError`，消息包含具体路径。
- 仅在 CLI 边界层做统一捕获并返回非零码。
- 避免在核心逻辑中使用宽泛 `except Exception`。

## 6) 业务约束（不可破坏）
- Skill 目录保持无状态，不存用户个性化数据。
- `cache/`、`resume_output/` 视为工作区数据，不应版本化。
- 保持 PDF 备份策略：`resume_output/*.pdf` -> `resume_output/backup/{Position}/..._old_N.pdf`。
- `--auto-fit` 只能调版式参数，不能改简历语义内容。
- 改动 PDF 生成逻辑时，同步验证 `scripts/check_pdf_quality.py` 检测规则。

## 7) 测试开发约定
- 修改功能时优先补测试，再改实现。
- 使用 `tempfile.TemporaryDirectory()` 隔离文件副作用。
- 新测试避免依赖网络、外部服务、系统字体稳定性。
- CLI 参数或输出变化必须补回归测试。

## 8) Cursor / Copilot 规则整合
仓库检查结果：
- 未发现 `.cursorrules`
- 未发现 `.cursor/rules/`
- 未发现 `.github/copilot-instructions.md`

结论：当前无额外 Cursor/Copilot 规则需要合并。

## 9) 提交前最小检查
1. `python3 -m pytest -q` 通过。
2. 至少执行一条受影响 CLI 的真实命令。
3. 不引入与需求无关的大范围格式化改动。
4. 输出/缓存路径符合 `.gitignore` 预期。

## 10) 平台说明
- 常见运行环境为 WSL/Linux，优先 Linux 路径。
- 在 WSL 默认使用 `python3`，不要依赖 `py -3`。
- 若在 PowerShell 运行，可将命令替换为 `py -3`。

### OpenCode
- 全局技能目录：`~/.config/opencode/skills/`
- 技能通过 `SKILL.md` frontmatter 自动发现
- 依赖技能安装到全局目录
- 命令入口：`.opencode/command/install-skill-deps.md`

### Claude Code
- 无全局技能目录，通过项目级 `CLAUDE.md` + `.claude/commands/` 斜杠命令工作
- 依赖技能安装到项目本地 `_deps/skills/` 目录，保持项目自包含
- 命令入口：`.claude/commands/install-skill-deps.md`
- 安装依赖技能：`/install-skill-deps`
