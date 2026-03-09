# resume-tailor

[English](README.md)

`resume-tailor` 是一个可分发的多平台 skill 包，面向 Codex、Claude Code 和 OpenCode。它使用仓库内置的脚本、模板和依赖技能，把现有简历和目标 JD 转成 ATS 友好的单页 A4 PDF。

## 包含内容

- `SKILL.md`：主工作流与行为约束
- `scripts/resume_cache_manager.py`：工作区缓存管理
- `scripts/generate_final_resume.py`：PDF 生成与 `--auto-fit` 调参
- `scripts/check_pdf_quality.py`、`scripts/check_content_quality.py`：内容与 PDF 质量检查
- `vendor/skills/`：内联依赖技能，包含 `pdf`、`docx`、`humanizer`
- Codex、Claude Code、OpenCode 的入口文件

## 典型触发

适用于用户提供目标 JD 或岗位方向，以及一份现有简历，并要求输出定向优化后的 PDF。

```text
我有一份 Product Manager JD 和当前简历，帮我整理成 ATS 友好的单页 PDF。
```

```text
根据这份 JD 分析我的简历匹配度，改写内容，并生成最终 PDF。
```

## 安装

```bash
python3 -m pip install -r requirements.txt
```

仓库已经内联依赖技能，不需要额外 clone。

## 平台入口

| 平台 | 入口文件 | 推荐位置 |
| --- | --- | --- |
| Codex | `SKILL.md`、`AGENTS.md` | `~/.agents/skills/resume-tailor/` |
| Claude Code | `SKILL.md`、`CLAUDE.md`、`.claude/commands/` | 仓库 checkout |
| OpenCode | `SKILL.md`、`.opencode/command/`、`install/agent-install.yaml` | `~/.config/opencode/skills/resume-tailor/` |

安装细节见 `docs/guide/installation.md`。

## 最小工作流

1. 用 `scripts/resume_cache_manager.py` 初始化工作区缓存。
2. 分析 JD，更新 `cache/resume-working.json`，只做事实内的重写和重排。
3. 在生成 PDF 前先做内容和体量检查。
4. 用 `scripts/generate_final_resume.py` 生成 PDF，需要时加 `--auto-fit`。
5. 用 `scripts/check_pdf_quality.py` 做最终检查。

Skill 本身保持无状态。用户数据只放在工作区运行目录，例如 `cache/` 和 `resume_output/`。

## 常用命令

在 Windows PowerShell 中，直接运行脚本时建议优先使用 `$env:PYTHONPATH='.'; py -3 ...`。

```bash
# 重置并加载缓存
python3 scripts/resume_cache_manager.py reset
python3 scripts/resume_cache_manager.py template-check --workspace .
python3 scripts/resume_cache_manager.py template-use --workspace .

# 生成并检查 PDF
python3 scripts/generate_final_resume.py --input-json cache/resume-working.json --output-file resume.pdf --output-dir resume_output --auto-fit
python3 scripts/check_pdf_quality.py resume_output/resume.pdf

# 检查平台入口和依赖资产
python3 scripts/check_agent_platform_support.py
```

## 目录结构

```text
resume-tailor/
├── SKILL.md
├── AGENTS.md
├── CLAUDE.md
├── scripts/
├── templates/
├── references/
├── vendor/skills/
├── .claude/commands/
├── .opencode/command/
├── install/
└── docs/guide/
```

## 说明

- `--auto-fit` 只会调整版式参数，不会改写简历内容。
- 输出目标是单页、A4、可提取文本的 PDF。
- 如果系统没有 Calibri，模板会回退到 Helvetica。
- `references/` 保留流程规则、缓存结构说明和提示词参考。

## 许可证

MIT，详见 `LICENSE`。
