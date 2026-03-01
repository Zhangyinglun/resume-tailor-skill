# resume-tailor

An OpenCode / Claude Code Skill for job-targeted resume optimization. Quickly generate ATS-friendly single-page A4 PDF resumes based on target JD.

## Core Capabilities

- **ATS Keyword Alignment**: Automatically extract high-frequency JD keywords and integrate them into resume expressions
- **Job Match Diagnosis**: Analyze matching level between existing experience and target position (P1/P2/P3) and gaps
- **Autonomous Optimization**: Agent autonomously makes all optimization decisions (keyword alignment, content prioritization, compression, layout tuning) and records them in a summary report
- **Smart Content Compression**: Optimize expression and compress to single page without fabricating facts
- **Auto-fit Layout Tuning**: Search 12 preset layout candidates (font/line-height/spacing/margins), pick optimal by QA pass + readability score — never modifies resume content
- **12-Point PDF Quality Check**: Generate A4 PDF with extractable text and auto-check page count, size, margins, sections, contacts, placeholders, etc.
- **AI Trace Removal**: Integrate `humanizer` skill to ensure natural expression and avoid common AI cliches

## Usage Scenarios

This skill automatically activates when you provide the following to OpenCode / Claude Code Agent:

- Target position JD (Job Description)
- Your existing resume (PDF / DOCX / plain text all supported)
- Explicitly request: ATS keyword alignment, job match optimization, compress to single page, or deliver PDF

Typical trigger examples:

```
I have a Product Manager JD and my existing resume, help me optimize it into an ATS-friendly single-page PDF.
```

```
Based on this JD, analyze my resume match level and generate a targeted optimized version.
```

```
Based on my resume, generate a general SDE resume focused on AI model engineering productionization and data platform capabilities.
```

## Installation

### Method 1: Agent Auto-Install (Recommended)

#### OpenCode

Send this message directly to OpenCode Agent:

```
Please read and strictly execute docs/guide/installation.md to complete resume-tailor dependency skill installation and verification.
```

Agent will automatically:
1. Clone this repo to `~/.config/opencode/skills/resume-tailor`
2. Install 3 dependent skills (`pdf`, `docx`, `humanizer`)
3. Install Python dependencies (`reportlab`, `pdfplumber`, `pytest`)
4. Verify all components work properly

**Remote Repo Install**: If using GitHub, you can give Agent the raw link:

```
https://raw.githubusercontent.com/<owner>/<repo>/<branch>/docs/guide/installation.md
```

**OpenCode Command Entry**: If you use OpenCode command system, you can directly execute:

```
/install-skill-deps
```

#### Claude Code

In the project directory, run the slash command:

```
/install-skill-deps
```

Claude Code Agent will automatically:
1. Install 3 dependent skills (`pdf`, `docx`, `humanizer`) to project-local `_deps/skills/`
2. Install Python dependencies (`reportlab`, `pdfplumber`, `pytest`)
3. Verify all components work properly

---

### Method 2: Manual Installation

#### OpenCode

**1. Clone This Repo**

```bash
git clone <repository-url> ~/.config/opencode/skills/resume-tailor
cd ~/.config/opencode/skills/resume-tailor
```

**2. Install Dependent Skills**

Ensure the following 3 skills are installed to OpenCode skill directory:

| Skill | Source | Purpose |
|-------|--------|---------|
| `pdf` | https://github.com/anthropics/skills | Read & generate PDF |
| `docx` | https://github.com/anthropics/skills | Read `.docx` resumes |
| `humanizer` | https://github.com/blader/humanizer | Remove AI trace expressions |

```bash
# Install pdf and docx
cd ~/.config/opencode/skills
git clone https://github.com/anthropics/skills anthropic-skills
ln -s anthropic-skills/pdf pdf
ln -s anthropic-skills/docx docx

# Install humanizer
git clone https://github.com/blader/humanizer humanizer
```

**3. Install Python Dependencies**

```bash
cd ~/.config/opencode/skills/resume-tailor
python3 -m pip install -r requirements.txt
```

**4. Restart OpenCode**

Close and reopen OpenCode session, skill will take effect.

#### Claude Code

**1. Clone This Repo (or open existing project)**

```bash
git clone <repository-url> resume-tailor
cd resume-tailor
```

**2. Install Dependent Skills**

```bash
mkdir -p _deps/skills
cd _deps/skills
git clone https://github.com/anthropics/skills _upstream_anthropic_skills
cp -r _upstream_anthropic_skills/skills/pdf pdf
cp -r _upstream_anthropic_skills/skills/docx docx
git clone https://github.com/blader/humanizer _upstream_humanizer
cp -r _upstream_humanizer humanizer
cd ../..
```

**3. Install Python Dependencies**

```bash
python3 -m pip install -r requirements.txt
```

**4. Verify**

Confirm `_deps/skills/pdf/SKILL.md`, `_deps/skills/docx/SKILL.md`, `_deps/skills/humanizer/SKILL.md` exist.

## Usage Flow

After skill activation, it automatically executes the following 4-phase flow. Agent autonomously makes all optimization decisions — no manual confirmation needed during execution. A structured summary report is delivered at the end for post-hoc review.

### Phase A: Initialize
- Reset working cache via `resume_cache_manager.py reset`
- Check template resume (`template-check`); if exists, load via `template-use`; if not, run `template-init` with user-provided resume, then `template-use`

### Phase B: Analyze & Draft
- **JD Diagnosis**: Analyze JD (or target direction) and produce P1 (critical) / P2 (important) / P3 (nice-to-have) tier classification with gap report
- **Apply All Modifications**: Apply all optimization decisions in one pass — keyword alignment, description strengthening, content reordering, low-relevance removal — then persist to working cache

### Phase C: Compress & Quality
- **Volume Gate**: Check working cache against volume thresholds; if exceeded, compress following consolidation order and constraints
  - Total word count: recommended 520–760
  - Non-empty lines: recommended 32–52
  - Total experience bullets: recommended 8–14
  - Single bullet: no more than 2 lines (~28 English words)
- **QA & De-AI**: Call `humanizer` for natural expression, then run structure / quantification / ATS checks

### Phase D: Generate & Deliver
- **PDF Generation**: Call `pdf` skill, then generate with `--auto-fit`. If QC fails, retry up to 3 times with escalating layout parameters
- **Summary Report**: Output a structured summary report covering all decisions made (job analysis, modifications, compression, QA results)
- **Wrap-up**: Update `cache/user-profile.md`, retain working cache for future iterations

**Core Principles**:
- No fabrication (only rewrite, rearrange, compress)
- Autonomous decision making with transparent reporting
- ATS friendly (no table-based layout, no images replacing text)

---

## Data Flow

```
Raw text / DOCX → resume_cache_manager.py → cache/resume-working.json
                                                      |
                                          generate_final_resume.py
                                            (+ layout_auto_tuner.py)
                                                      |
                                          modern_resume_template.py (ReportLab)
                                                      |
                                              resume_output/*.pdf
                                                      |
                                            check_pdf_quality.py → PASS / NEED-ADJUSTMENT
```

## Project Structure

```
resume-tailor/
├── SKILL.md                         # Skill main doc and workflow constraints
├── AGENTS.md                        # Agent coding standards and command reference
├── CLAUDE.md                        # Claude Code project instructions
├── scripts/                         # Core scripts
│   ├── resume_cache_manager.py      # JSON cache CRUD (reset/init/update/show/diff/template-*)
│   ├── generate_final_resume.py     # PDF generation entry point with CLI args
│   ├── check_pdf_quality.py         # 12-check PDF QA
│   ├── layout_auto_tuner.py         # Search 12 layout presets, pick optimal by QA + readability
│   └── resume_shared.py             # Shared utilities (validation, JSON I/O, parsing)
├── templates/                       # PDF layout templates
│   ├── modern_resume_template.py    # ReportLab PDF renderer (fonts, styles, sections)
│   ├── layout_settings.py           # Immutable dataclass for layout params (auto-clamp 0.7–1.3)
│   └── README.md                    # Template docs
├── references/                      # References
│   ├── execution-checklist.md       # Full process checklist (with volume thresholds)
│   ├── ats-keywords-strategy.md     # ATS strategy
│   ├── prompt-recipes.md            # Prompt templates
│   ├── profile-cache-template.md    # User profile cache template
│   └── resume-working-schema.md     # Working cache structure spec
├── tests/                           # Tests
│   ├── test_resume_cache_flow.py    # Cache lifecycle and template management
│   ├── test_output_backup_policy.py # PDF backup policy
│   ├── test_layout_auto_tuner.py    # Auto-fit layout tuning
│   ├── test_layout_settings.py      # Layout param clamping
│   ├── test_layout_integration.py   # Layout integration
│   ├── test_extended_sections.py    # Optional sections (projects, certs, awards)
│   ├── test_cache_diff.py           # Cache diff functionality
│   ├── test_quality_json_output.py  # QA JSON output format
│   ├── test_pdf_margin_checks.py    # PDF margin boundary regression
│   └── test_generate_final_resume_cli_args.py  # CLI arg parsing
├── docs/guide/                      # Installation guide
│   └── installation.md              # Agent-executable install flow
├── install/                         # Install manifest
│   └── agent-install.yaml           # Machine-readable install manifest
├── .opencode/command/               # OpenCode commands
│   └── install-skill-deps.md        # Command-based install entry
├── .claude/commands/                # Claude Code commands
│   └── install-skill-deps.md        # Command-based install entry
└── requirements.txt                 # Python dependencies
```

## Development & Testing

### Run Tests

```bash
python3 -m pytest -q
```

### Verify Script Behavior

You can also run tools under `scripts/` individually for debugging:

```bash
# Cache management
python3 scripts/resume_cache_manager.py reset
python3 scripts/resume_cache_manager.py template-init --workspace . --input raw_resume.txt
python3 scripts/resume_cache_manager.py template-use --workspace .

# Generate PDF
python3 scripts/generate_final_resume.py --input-json cache/resume-working.json --output-file resume.pdf --output-dir resume_output

# Generate PDF with auto-fit layout tuning
python3 scripts/generate_final_resume.py --input-json cache/resume-working.json --output-file resume.pdf --output-dir resume_output --auto-fit

# QC PDF
python3 scripts/check_pdf_quality.py resume_output/resume.pdf

# QC PDF with JSON report
python3 scripts/check_pdf_quality.py resume_output/resume.pdf --json
```

---

## Technical Notes

### Python Dependencies

- `reportlab`: PDF generation
- `pdfplumber`: PDF quality check
- `pytest`: Test execution

All dependencies maintained in `requirements.txt`.

### Fonts & Cross-Platform

- Template prioritizes Windows **Calibri** font
- If Calibri doesn't exist on system, auto-fallback to **Helvetica** (doesn't affect PDF generation)
- For fixed font effect, recommend installing equivalent font on target system before export

### Cache & Output Directories

Skill directory itself stores no personalized data. All cache and output files are in workspace:

```
Workspace/
├── resume_output/
│   ├── *.pdf                   # Current latest PDF
│   └── backup/                 # Historical PDF backups
└── cache/
    ├── base-resume.json        # Template resume (long-term baseline)
    ├── user-profile.md         # Long-term preference cache
    └── resume-working.json     # Current session resume body
```

---

## Open Source & Contribution

### License

MIT License - See `LICENSE` file

### Privacy & Security

- This repo contains no personal privacy data (contact info, real resume samples, etc.)
- `.gitignore` configured to exclude `cache/` and `resume_output/**/*.pdf`
- Only keep reusable rules, scripts, templates and references

### Contribution Guidelines

Welcome to submit Issues and Pull Requests to improve this Skill!

---

## FAQ

**Q: Why install 3 dependent skills?**

A:
- `pdf`: Read existing PDF resumes and generate final PDF
- `docx`: Read `.docx` format resumes
- `humanizer`: Remove common AI-generated text traces, enhance natural expression

**Q: Can generated PDF be submitted directly?**

A: Yes. Generated PDF auto-runs a 12-point quality check covering:
- A4 size (210mm x 297mm)
- Single page
- Text extractable (supports ATS systems)
- Margin compliance (bottom margin 3–8mm)
- Section completeness and contact info presence
- No HTML tag leakage or placeholder content

**Q: How to customize PDF template style?**

A: Edit `templates/modern_resume_template.py`, a ReportLab-based Python template. Layout parameters (font size, line-height, spacing, margins) are managed in `templates/layout_settings.py`. See `templates/README.md`.

**Q: Can layout be tuned automatically without rewriting resume content?**

A: Yes. Use `--auto-fit` in `scripts/generate_final_resume.py`. It searches 12 preset layout candidates (font/line-height/spacing/margin scales) and picks the optimal one by QA pass + readability score, keeping JSON content unchanged.

**Q: Will skill save my resume?**

A: No. Skill directory itself is stateless. All cache and output files are in your workspace directory (`resume_output/` and `cache/`), won't commit to Git repo.

---

## Acknowledgments

This skill references the following projects and best practices:

- [Anthropic Skills](https://github.com/anthropics/skills) - `pdf` and `docx` skills
- [blader/humanizer](https://github.com/blader/humanizer) - AI trace removal
- [oh-my-opencode](https://github.com/anomalyco/oh-my-opencode) - Agent auto-install pattern

---
---

# resume-tailor

一个用于岗位定向简历优化的 OpenCode / Claude Code Skill，帮助你根据目标 JD 快速生成 ATS 友好的单页 A4 PDF 简历。

## 核心能力

- **ATS 关键词对齐**：自动提取 JD 高频关键词并融入简历表达
- **岗位匹配诊断**：分析现有经历与目标岗位的匹配度（P1/P2/P3）与差距
- **自主优化决策**：Agent 自主完成所有优化决策（关键词对齐、内容优先级、压缩、版式调参），决策记录在结构化总结报告中
- **智能内容压缩**：在不编造事实的前提下，优化表达并压缩到单页
- **Auto-fit 版式调参**：搜索 12 组预设版式候选（字号/行高/间距/边距），按质检通过率 + 可读性评分选出最优方案 —— 不修改简历内容
- **12 项 PDF 质量检查**：生成可提取文本的 A4 PDF，自动检查页数、尺寸、边距、模块完整性、联系方式、占位符等
- **去 AI 痕迹**：集成 `humanizer` skill，确保表达自然、避免 AI 常见套话

## 使用场景

当你向 OpenCode / Claude Code Agent 提供以下内容时，此 skill 会自动激活：

- 目标岗位的 JD（职位描述）
- 你的现有简历（PDF / DOCX / 纯文本 均可）
- 明确提出需要：ATS 关键词对齐、岗位匹配优化、压缩到单页、或交付 PDF

典型触发示例：

```
我有一份产品经理的 JD 和我的现有简历，帮我优化成 ATS 友好的单页 PDF。
```

```
根据这个 JD，分析我的简历匹配度，并生成针对性的优化版本。
```

```
根据我的简历，生成一份通用 SDE 简历，重点突出 AI 模型工程化落地和 data platform 能力。
```

## 安装方法

### 方式一：Agent 自动安装（推荐）

#### OpenCode

直接把下面这句话发给 OpenCode Agent：

```
请读取并严格执行 docs/guide/installation.md，完成 resume-tailor 依赖技能安装与验证。
```

Agent 会自动完成：
1. 克隆本仓库到 `~/.config/opencode/skills/resume-tailor`
2. 安装 3 个依赖 skill（`pdf`、`docx`、`humanizer`）
3. 安装 Python 依赖（`reportlab`、`pdfplumber`、`pytest`）
4. 验证所有组件正常工作

**远程仓库安装**：如果在 GitHub 使用，可以给 Agent 传 raw 链接：

```
https://raw.githubusercontent.com/<owner>/<repo>/<branch>/docs/guide/installation.md
```

**OpenCode 命令入口**：如果你使用 OpenCode 命令体系，也可以直接执行：

```
/install-skill-deps
```

#### Claude Code

在项目目录下执行斜杠命令：

```
/install-skill-deps
```

Claude Code Agent 会自动完成：
1. 安装 3 个依赖 skill（`pdf`、`docx`、`humanizer`）到项目本地 `_deps/skills/`
2. 安装 Python 依赖（`reportlab`、`pdfplumber`、`pytest`）
3. 验证所有组件正常工作

---

### 方式二：手动安装

#### OpenCode

**1. 克隆本仓库**

```bash
git clone <repository-url> ~/.config/opencode/skills/resume-tailor
cd ~/.config/opencode/skills/resume-tailor
```

**2. 安装依赖 Skill**

确保以下 3 个 skill 已安装到 OpenCode 技能目录：

| Skill | 来源 | 作用 |
|-------|------|------|
| `pdf` | https://github.com/anthropics/skills | 读取与生成 PDF |
| `docx` | https://github.com/anthropics/skills | 读取 `.docx` 简历 |
| `humanizer` | https://github.com/blader/humanizer | 去除 AI 痕迹表达 |

```bash
# 安装 pdf 和 docx
cd ~/.config/opencode/skills
git clone https://github.com/anthropics/skills anthropic-skills
ln -s anthropic-skills/pdf pdf
ln -s anthropic-skills/docx docx

# 安装 humanizer
git clone https://github.com/blader/humanizer humanizer
```

**3. 安装 Python 依赖**

```bash
cd ~/.config/opencode/skills/resume-tailor
python3 -m pip install -r requirements.txt
```

**4. 重启 OpenCode**

关闭并重新打开 OpenCode 会话，skill 即可生效。

#### Claude Code

**1. 克隆本仓库（或打开已有项目）**

```bash
git clone <repository-url> resume-tailor
cd resume-tailor
```

**2. 安装依赖 Skill**

```bash
mkdir -p _deps/skills
cd _deps/skills
git clone https://github.com/anthropics/skills _upstream_anthropic_skills
cp -r _upstream_anthropic_skills/skills/pdf pdf
cp -r _upstream_anthropic_skills/skills/docx docx
git clone https://github.com/blader/humanizer _upstream_humanizer
cp -r _upstream_humanizer humanizer
cd ../..
```

**3. 安装 Python 依赖**

```bash
python3 -m pip install -r requirements.txt
```

**4. 验证**

确认 `_deps/skills/pdf/SKILL.md`、`_deps/skills/docx/SKILL.md`、`_deps/skills/humanizer/SKILL.md` 存在。

## 使用流程

Skill 激活后自动执行以下 4 阶段流程。Agent 自主完成所有优化决策 —— 执行过程中无需手动确认。流程结束后输出结构化总结报告供事后审阅。

### Phase A：初始化
- 通过 `resume_cache_manager.py reset` 重置工作缓存
- 检查模板简历（`template-check`）；若存在则通过 `template-use` 加载；若不存在则用用户提供的简历执行 `template-init`，再 `template-use`

### Phase B：分析与起草
- **JD 诊断**：分析 JD（或目标方向），产出 P1（关键）/ P2（重要）/ P3（加分）分级诊断与差距报告
- **一次性应用所有修改**：一轮完成所有优化决策 —— 关键词对齐、描述强化、内容重排、低相关内容移除 —— 然后持久化到工作缓存

### Phase C：压缩与质量
- **体量门禁**：检查工作缓存是否超过体量阈值，超标则按合并顺序和约束执行压缩
  - 总词数：推荐 520–760
  - 非空行数：推荐 32–52
  - 经历要点数：推荐 8–14
  - 单条要点：不超过 2 行（约 28 个英文单词）
- **QA & 去 AI 痕迹**：调用 `humanizer` 增强自然表达，然后执行结构 / 量化 / ATS 检查

### Phase D：生成与交付
- **PDF 生成**：调用 `pdf` skill，使用 `--auto-fit` 生成。若质检失败，最多重试 3 次并逐步提升版式参数
- **总结报告**：输出结构化总结报告，覆盖所有决策（岗位分析、修改内容、压缩操作、QA 结果）
- **收尾**：更新 `cache/user-profile.md`，保留工作缓存供下次迭代

**核心原则**：
- 不编造事实（只重写、重排、压缩）
- 自主决策 + 透明报告
- ATS 友好（无表格布局、无图片替代正文）

---

## 数据流

```
Raw text / DOCX → resume_cache_manager.py → cache/resume-working.json
                                                      |
                                          generate_final_resume.py
                                            (+ layout_auto_tuner.py)
                                                      |
                                          modern_resume_template.py (ReportLab)
                                                      |
                                              resume_output/*.pdf
                                                      |
                                            check_pdf_quality.py → PASS / NEED-ADJUSTMENT
```

## 项目结构

```
resume-tailor/
├── SKILL.md                         # Skill 主说明与工作流约束
├── AGENTS.md                        # Agent 编码规范与命令参考
├── CLAUDE.md                        # Claude Code 项目级指引
├── scripts/                         # 核心脚本
│   ├── resume_cache_manager.py      # JSON 缓存 CRUD（reset/init/update/show/diff/template-*）
│   ├── generate_final_resume.py     # PDF 生成入口（含 CLI 参数）
│   ├── check_pdf_quality.py         # 12 项 PDF 质检
│   ├── layout_auto_tuner.py         # 搜索 12 组版式预设，按质检 + 可读性评分选优
│   └── resume_shared.py             # 共享工具（校验、JSON I/O、解析辅助）
├── templates/                       # PDF 排版模板
│   ├── modern_resume_template.py    # ReportLab PDF 渲染器（字体、样式、模块布局）
│   ├── layout_settings.py           # 不可变 dataclass，版式参数（自动钳位 0.7–1.3）
│   └── README.md                    # 模板说明
├── references/                      # 参考资料
│   ├── execution-checklist.md       # 全流程检查清单（含体量阈值）
│   ├── ats-keywords-strategy.md     # ATS 策略
│   ├── prompt-recipes.md            # Prompt 模板
│   ├── profile-cache-template.md    # 用户画像缓存模板
│   └── resume-working-schema.md     # 工作缓存结构规范
├── tests/                           # 测试
│   ├── test_resume_cache_flow.py    # 缓存生命周期与模板管理
│   ├── test_output_backup_policy.py # PDF 备份策略
│   ├── test_layout_auto_tuner.py    # Auto-fit 版式调参
│   ├── test_layout_settings.py      # 版式参数钳位
│   ├── test_layout_integration.py   # 版式集成测试
│   ├── test_extended_sections.py    # 可选模块（projects, certs, awards）
│   ├── test_cache_diff.py           # 缓存 diff 功能
│   ├── test_quality_json_output.py  # 质检 JSON 输出格式
│   ├── test_pdf_margin_checks.py    # PDF 边距边界回归
│   └── test_generate_final_resume_cli_args.py  # CLI 参数解析
├── docs/guide/                      # 安装指南
│   └── installation.md              # Agent 可执行安装流程
├── install/                         # 安装清单
│   └── agent-install.yaml           # 机器可读安装清单
├── .opencode/command/               # OpenCode 命令
│   └── install-skill-deps.md        # 命令化安装入口
├── .claude/commands/                # Claude Code 命令
│   └── install-skill-deps.md        # 命令化安装入口
└── requirements.txt                 # Python 依赖
```

## 开发与测试

### 运行测试

```bash
python3 -m pytest -q
```

### 验证脚本行为

也可以单独运行 `scripts/` 下的工具进行调试：

```bash
# 缓存管理
python3 scripts/resume_cache_manager.py reset
python3 scripts/resume_cache_manager.py template-init --workspace . --input raw_resume.txt
python3 scripts/resume_cache_manager.py template-use --workspace .

# 生成 PDF
python3 scripts/generate_final_resume.py --input-json cache/resume-working.json --output-file resume.pdf --output-dir resume_output

# 自动调参后生成 PDF（仅调版式，不改内容）
python3 scripts/generate_final_resume.py --input-json cache/resume-working.json --output-file resume.pdf --output-dir resume_output --auto-fit

# 质检 PDF
python3 scripts/check_pdf_quality.py resume_output/resume.pdf

# 质检 PDF（JSON 报告）
python3 scripts/check_pdf_quality.py resume_output/resume.pdf --json
```

---

## 技术说明

### Python 依赖

- `reportlab`：PDF 生成
- `pdfplumber`：PDF 质量检查
- `pytest`：测试执行

所有依赖维护在 `requirements.txt`。

### 字体与跨平台

- 模板优先使用 Windows 的 **Calibri** 字体
- 若系统不存在 Calibri，自动回退到 **Helvetica**（不影响 PDF 生成）
- 若需固定字体效果，建议在目标系统安装等价字体后再导出

### 缓存与输出目录

Skill 目录本身不存储任何个性化数据，所有缓存与输出文件存放在工作区：

```
工作区/
├── resume_output/
│   ├── *.pdf                   # 当前最新 PDF
│   └── backup/                 # 历史 PDF 备份
└── cache/
    ├── base-resume.json        # 模板简历（长期基线）
    ├── user-profile.md         # 长期偏好缓存
    └── resume-working.json     # 当前会话简历正文
```

---

## 开源与贡献

### 许可证

MIT License - 详见 `LICENSE` 文件

### 隐私与安全

- 本仓库不包含任何个人隐私数据（联系方式、真实简历样本等）
- `.gitignore` 已配置排除 `cache/` 和 `resume_output/**/*.pdf`
- 仅保留可复用的规则、脚本、模板与参考资料

### 贡献指南

欢迎提交 Issue 和 Pull Request 来改进此 Skill！

---

## 常见问题

**Q: 为什么需要安装 3 个依赖 skill？**

A:
- `pdf`：用于读取现有 PDF 简历和生成最终 PDF
- `docx`：用于读取 `.docx` 格式的简历
- `humanizer`：用于去除 AI 生成文本的常见痕迹，提升表达自然度

**Q: 生成的 PDF 可以直接投递吗？**

A: 可以。生成的 PDF 会自动运行 12 项质检，覆盖：
- A4 尺寸（210mm x 297mm）
- 单页
- 文本可提取（支持 ATS 系统）
- 边距合规（底部边距 3–8mm）
- 模块完整性与联系方式
- 无 HTML 标签泄漏或占位符内容

**Q: 如何自定义 PDF 模板样式？**

A: 编辑 `templates/modern_resume_template.py`，这是一个基于 ReportLab 的 Python 模板。版式参数（字号、行高、间距、边距）由 `templates/layout_settings.py` 管理。详见 `templates/README.md`。

**Q: 可以自动调版式但不改简历内容吗？**

A: 可以。使用 `scripts/generate_final_resume.py` 的 `--auto-fit`。它搜索 12 组预设版式候选（字号/行高/间距/边距缩放），按质检通过率 + 可读性评分选出最优方案，不会改写 JSON 内容。

**Q: Skill 会保存我的简历吗？**

A: 不会。Skill 目录本身是 stateless 的，所有缓存和输出文件存放在你的工作区目录（`resume_output/` 和 `cache/`），不会提交到 Git 仓库。

---

## 致谢

本 Skill 参考了以下项目和最佳实践：

- [Anthropic Skills](https://github.com/anthropics/skills) - `pdf` 和 `docx` skill
- [blader/humanizer](https://github.com/blader/humanizer) - 去 AI 痕迹表达
- [oh-my-opencode](https://github.com/anomalyco/oh-my-opencode) - Agent 自动安装模式
