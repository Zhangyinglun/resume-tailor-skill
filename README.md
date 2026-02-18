# resume-tailor

An OpenCode Skill for job-targeted resume optimization. Quickly generate ATS-friendly single-page A4 PDF resumes based on target JD.

## Core Capabilities

- ✅ **ATS Keyword Alignment**: Automatically extract high-frequency JD keywords and integrate them into resume expressions
- ✅ **Job Match Diagnosis**: Analyze matching level between existing experience and target position (P1/P2/P3) and gaps
- ✅ **Smart Content Compression**: Optimize expression and compress to single page without fabricating facts
- ✅ **PDF Quality Assurance**: Generate A4 PDF with extractable text and auto-check format and text layer
- ✅ **AI Trace Removal**: Integrate `humanizer` skill to ensure natural expression and avoid common AI clichés

## Usage Scenarios

This skill automatically activates when you provide the following to OpenCode Agent:

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

---

### Method 2: Manual Installation

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
py -3 -m pip install -r requirements.txt
```

**4. Restart OpenCode**

Close and reopen OpenCode session, skill will take effect.

## Usage Flow

After skill activation, it automatically executes the following flow (no manual operation needed):

### 1. **JD Diagnosis**
- Analyze match level between your existing resume and target JD (or target direction if JD is absent)
- Output P1 (strong match), P2 (medium match), P3 (weak match) evidence chains
- Identify key capability gaps

### 2. **Iterative Optimization**
- Only change 1 decision point per round (use visual selection box)
- Auto-align ATS keywords and optimize expressions
- Compress redundant content, focus on job relevance

### 3. **Volume Gate**
- Ensure content meets single-page A4 target before outputting full review text
- Call `humanizer` skill to remove AI traces

### 4. **PDF Generation and QC**
- Generate A4 PDF after your approval
- Auto-check: page count, size, text extractability, HTML leakage
- Fine-tune and regenerate if needed

### 5. **Delivery and Cache**
- Final PDF saved to `resume_output/`
- Historical versions auto-backed up to `resume_output/backup/`
- Update user profile cache for next use

**Core Principles**:
- ✅ No fabrication (only rewrite, rearrange, compress)
- ✅ Review before export (must obtain explicit approval)
- ✅ One question at a time (only one decision point per round)

---

## Project Structure

```
resume-tailor/
├── SKILL.md                         # Skill main doc and workflow constraints
├── scripts/                         # Core scripts
│   ├── resume_cache_manager.py      # JSON cache management (reset/init/update/show)
│   ├── generate_final_resume.py     # PDF generation entry
│   └── check_pdf_quality.py         # PDF QC
├── templates/                       # PDF layout templates
│   ├── modern_resume_template.py    # ReportLab template
│   └── README.md                    # Template docs
├── references/                      # References
│   ├── execution-checklist.md       # Full process checklist
│   ├── ats-keywords-strategy.md     # ATS strategy
│   ├── prompt-recipes.md            # Prompt templates
│   ├── profile-cache-template.md    # User profile cache template
│   └── resume-working-schema.md     # Working cache structure spec
├── tests/                           # Tests
│   ├── test_resume_cache_flow.py
│   └── test_output_backup_policy.py
├── docs/guide/                      # Installation guide
│   └── installation.md              # Agent-executable install flow
├── install/                         # Install manifest
│   └── agent-install.yaml           # Machine-readable install manifest
├── .opencode/command/               # OpenCode commands
│   └── install-skill-deps.md        # Command-based install entry
└── requirements.txt                 # Python dependencies
```

## Development & Testing

### Run Tests

```bash
cd ~/.config/opencode/skills/resume-tailor
python3 -m pytest
```

### Verify Script Behavior

You can also run tools under `scripts/` individually for debugging:

```bash
# Cache management
python3 scripts/resume_cache_manager.py reset
python3 scripts/resume_cache_manager.py init

# Generate PDF
python3 scripts/generate_final_resume.py --input-json cache/resume-working.json --output-file resume.pdf --output-dir resume_output

# Generate PDF with auto-fit layout tuning
python3 scripts/generate_final_resume.py --input-json cache/resume-working.json --output-file resume.pdf --output-dir resume_output --auto-fit

# QC PDF
python3 scripts/check_pdf_quality.py resume_output/resume.pdf
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
│   ├── resume_final.pdf         # Current latest PDF
│   └── backup/                  # Historical PDF backups
└── cache/
    ├── user-profile.md          # Long-term preference cache
    └── resume-working.json      # Current session resume body
```

---

## Open Source & Contribution

### License

MIT License - See `LICENSE` file

### Privacy & Security

- ✅ This repo contains no personal privacy data (contact info, real resume samples, etc.)
- ✅ `.gitignore` configured to exclude `cache/` and `resume_output/**/*.pdf`
- ✅ Only keep reusable rules, scripts, templates and references

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

A: Yes. Generated PDF auto-checks the following:
- ✅ A4 size (210mm x 297mm)
- ✅ Single page
- ✅ Text extractable (supports ATS systems)
- ✅ No HTML tag leakage

**Q: How to customize PDF template style?**

A: Edit `templates/modern_resume_template.py`, a ReportLab-based Python template. See `templates/README.md`.

**Q: Can layout be tuned automatically without rewriting resume content?**

A: Yes. Use `--auto-fit` in `scripts/generate_final_resume.py`. It searches layout parameters only and keeps JSON content unchanged.

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

一个用于岗位定向简历优化的 OpenCode Skill，帮助你根据目标 JD 快速生成 ATS 友好的单页 A4 PDF 简历。

## 核心能力

- ✅ **ATS 关键词对齐**：自动提取 JD 高频关键词并融入简历表达
- ✅ **岗位匹配诊断**：分析现有经历与目标岗位的匹配度（P1/P2/P3）与差距
- ✅ **智能内容压缩**：在不编造事实的前提下，优化表达并压缩到单页
- ✅ **PDF 质量保证**：生成可提取文本的 A4 PDF，并自动质检格式与文本层
- ✅ **去 AI 痕迹**：集成 `humanizer` skill，确保表达自然、避免 AI 常见套话

## 使用场景

当你向 OpenCode Agent 提供以下内容时，此 skill 会自动激活：

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

---

### 方式二：手动安装

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

## 使用流程

Skill 激活后会自动执行以下流程（无需手动操作）：

### 1. **JD 诊断**
- 分析你的现有简历与目标 JD 的匹配度（若无 JD，则按目标方向诊断）
- 输出 P1（强匹配）、P2（中匹配）、P3（弱匹配）证据链
- 识别关键能力差距（gap）

### 2. **迭代优化**
- 每轮只改 1 个决策点（使用可视化选择框）
- 自动对齐 ATS 关键词并优化表达
- 压缩冗余内容，聚焦岗位相关性

### 3. **体量门禁**
- 确保内容符合单页 A4 目标后再输出全文审阅
- 调用 `humanizer` skill 去除 AI 痕迹
- **体量阈值**（任一超标则触发压缩）：
  - 总词数：推荐 520-760
  - 非空行数：推荐 32-52
  - 经历要点数：推荐 8-14
  - 单条要点：不超过 2 行（约 28 个英文单词）

### 4. **PDF 生成与质检**
- 获得你的批准后生成 A4 PDF
- 自动检测：页数、尺寸、文本可提取性、HTML 泄漏
- 必要时微调重生

### 5. **交付与缓存**
- 最终 PDF 保存到 `resume_output/`
- 历史版本自动备份到 `resume_output/backup/`
- 更新用户画像缓存供下次使用

**核心原则**：
- ✅ 不编造事实（只重写、重排、压缩）
- ✅ 先审阅后导出（必须获得明确批准）
- ✅ 一次一问（每轮只给一个决策点）

---

## 项目结构

```
resume-tailor/
├── SKILL.md                         # Skill 主说明与工作流约束
├── AGENTS.md                        # Agent 执行规范与命令约定
├── scripts/                         # 核心脚本
│   ├── resume_cache_manager.py      # JSON 缓存管理（reset/init/update/show）
│   ├── generate_final_resume.py     # PDF 生成入口
│   └── check_pdf_quality.py         # PDF 质检
├── templates/                       # PDF 排版模板
│   ├── modern_resume_template.py    # ReportLab 模板
│   └── README.md                    # 模板说明
├── references/                      # 参考资料
│   ├── execution-checklist.md       # 全流程检查清单（含体量阈值）
│   ├── ats-keywords-strategy.md     # ATS 策略
│   ├── prompt-recipes.md            # Prompt 模板
│   ├── profile-cache-template.md    # 用户画像缓存模板
│   └── resume-working-schema.md     # 工作缓存结构规范
├── tests/                           # 测试
│   ├── test_resume_cache_flow.py
│   └── test_output_backup_policy.py
├── docs/guide/                      # 安装指南
│   └── installation.md              # Agent 可执行安装流程
├── install/                         # 安装清单
│   └── agent-install.yaml           # 机器可读安装清单
├── .opencode/command/               # OpenCode 命令
│   └── install-skill-deps.md        # 命令化安装入口
└── requirements.txt                 # Python 依赖
```

## 开发与测试

### 运行测试

```bash
cd ~/.config/opencode/skills/resume-tailor
python3 -m pytest
```

### 验证脚本行为

也可以单独运行 `scripts/` 下的工具进行调试：

```bash
# 缓存管理
python3 scripts/resume_cache_manager.py reset
python3 scripts/resume_cache_manager.py init

# 生成 PDF
python3 scripts/generate_final_resume.py --input-json cache/resume-working.json --output-file resume.pdf --output-dir resume_output

# 自动调参后生成 PDF（仅调版式，不改内容）
python3 scripts/generate_final_resume.py --input-json cache/resume-working.json --output-file resume.pdf --output-dir resume_output --auto-fit

# 质检 PDF
python3 scripts/check_pdf_quality.py resume_output/resume.pdf
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
│   ├── resume_final.pdf         # 当前最新 PDF
│   └── backup/                  # 历史 PDF 备份
└── cache/
    ├── user-profile.md          # 长期偏好缓存
    └── resume-working.json      # 当前会话简历正文
```

---

## 开源与贡献

### 许可证

MIT License - 详见 `LICENSE` 文件

### 隐私与安全

- ✅ 本仓库不包含任何个人隐私数据（联系方式、真实简历样本等）
- ✅ `.gitignore` 已配置排除 `cache/` 和 `resume_output/**/*.pdf`
- ✅ 仅保留可复用的规则、脚本、模板与参考资料

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

A: 可以。生成的 PDF 会自动质检以下项目：
- ✅ A4 尺寸（210mm x 297mm）
- ✅ 单页
- ✅ 文本可提取（支持 ATS 系统）
- ✅ 无 HTML 标签泄漏

**Q: 如何自定义 PDF 模板样式？**

A: 编辑 `templates/modern_resume_template.py`，这是一个基于 ReportLab 的 Python 模板。详见 `templates/README.md`。

**Q: 可以自动调版式但不改简历内容吗？**

A: 可以。使用 `scripts/generate_final_resume.py` 的 `--auto-fit`。它只搜索版式参数，不会改写 JSON 内容。

**Q: Skill 会保存我的简历吗？**

A: 不会。Skill 目录本身是 stateless 的，所有缓存和输出文件存放在你的工作区目录（`resume_output/` 和 `cache/`），不会提交到 Git 仓库。

---

## 致谢

本 Skill 参考了以下项目和最佳实践：

- [Anthropic Skills](https://github.com/anthropics/skills) - `pdf` 和 `docx` skill
- [blader/humanizer](https://github.com/blader/humanizer) - 去 AI 痕迹表达
- [oh-my-opencode](https://github.com/anomalyco/oh-my-opencode) - Agent 自动安装模式
