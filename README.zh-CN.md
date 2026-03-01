# resume-tailor

[English](README.md)

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

详细安装步骤（含 Agent 自动安装和手动安装）见 [`docs/guide/installation.md`](docs/guide/installation.md)。

### 快速开始

**OpenCode**：直接把下面这句话发给 OpenCode Agent：

```
请读取并严格执行 docs/guide/installation.md，完成 resume-tailor 依赖技能安装与验证。
```

**Claude Code**：在项目目录下执行斜杠命令：

```
/install-skill-deps
```

## 使用流程

Skill 激活后自动执行以下 4 阶段流程。Agent 自主完成所有优化决策 —— 执行过程中无需手动确认。流程结束后输出结构化总结报告供事后审阅。

### Phase A：初始化
- 通过 `resume_cache_manager.py reset` 重置工作缓存
- 检查模板简历（`template-check`）；若存在则通过 `template-use` 加载；若不存在则用用户提供的简历执行 `template-init`，再 `template-use`

### Phase B：分析与起草
- **JD 诊断**：分析 JD（或目标方向），产出 P1（关键）/ P2（重要）/ P3（加分）分级诊断与差距报告
- **一次性应用所有修改**：一轮完成所有优化决策 —— 关键词对齐、描述强化、内容重排、低相关内容移除 —— 然后持久化到工作缓存

### Phase C：压缩与质量
- **体量门禁**：通过 `score_all_bullets()` 对照 `cache/jd-analysis.json` 给 bullet 评分，检查工作缓存是否超过体量阈值，超标则优先移除最低分 bullet，然后 `update`
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
│   ├── check_content_quality.py     # 内容级质检（bullet 评分、动词强度、量化率）
│   ├── layout_auto_tuner.py         # 搜索 12 组版式预设，按质检 + 可读性评分选优
│   └── resume_shared.py             # 共享工具（校验、JSON I/O、解析辅助）
├── templates/                       # PDF 排版模板
│   ├── modern_resume_template.py    # ReportLab PDF 渲染器（字体、样式、模块布局）
│   ├── layout_settings.py           # 不可变 dataclass，版式参数（自动钳位 0.7–1.3）
│   ├── design_tokens.py             # 集中设计常量（基础字号、行距、间距）
│   └── README.md                    # 模板说明
├── references/                      # 参考资料
│   ├── execution-checklist.md       # 全流程检查清单（含体量阈值）
│   ├── ats-keywords-strategy.md     # ATS 策略
│   ├── prompt-recipes.md            # Prompt 模板
│   ├── optimization-actions.md      # 优化操作代码
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
│   ├── test_content_quality.py      # 内容质量检查
│   ├── test_bullet_scoring.py       # Bullet 评分逻辑
│   ├── test_jd_analysis.py          # JD 分析缓存操作
│   ├── test_schema_validation.py    # JSON schema 校验
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

A: 编辑 `templates/modern_resume_template.py`，这是一个基于 ReportLab 的 Python 模板。版式参数（字号、行高、间距、边距）由 `templates/layout_settings.py` 管理。设计常量集中在 `templates/design_tokens.py`。详见 `templates/README.md`。

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
