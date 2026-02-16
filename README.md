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
- 你的现有简历（PDF / DOCX / Markdown 均可）
- 明确提出需要：ATS 关键词对齐、岗位匹配优化、压缩到单页、或交付 PDF

典型触发示例：

```
我有一份产品经理的 JD 和我的现有简历，帮我优化成 ATS 友好的单页 PDF。
```

```
根据这个 JD，分析我的简历匹配度，并生成针对性的优化版本。
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
py -3 -m pip install -r requirements.txt
```

**4. 重启 OpenCode**

关闭并重新打开 OpenCode 会话，skill 即可生效。

## 使用流程

Skill 激活后会自动执行以下流程（无需手动操作）：

### 1. **JD 诊断**
- 分析你的现有简历与目标 JD 的匹配度
- 输出 P1（强匹配）、P2（中匹配）、P3（弱匹配）证据链
- 识别关键能力差距（gap）

### 2. **迭代优化**
- 每轮只改 1 个决策点（使用可视化选择框）
- 自动对齐 ATS 关键词并优化表达
- 压缩冗余内容，聚焦岗位相关性

### 3. **体量门禁**
- 确保内容符合单页 A4 目标后再输出全文审阅
- 调用 `humanizer` skill 去除 AI 痕迹

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
├── scripts/                         # 核心脚本
│   ├── resume_cache_manager.py      # 缓存管理（reset/init/update）
│   ├── resume_md_to_json.py         # Markdown 转 JSON
│   ├── generate_final_resume.py     # PDF 生成入口
│   └── check_pdf_quality.py         # PDF 质检
├── templates/                       # PDF 排版模板
│   ├── modern_resume_template.py    # ReportLab 模板
│   └── README.md                    # 模板说明
├── references/                      # 参考资料
│   ├── execution-checklist.md       # 全流程检查清单
│   ├── ats-keywords-strategy.md     # ATS 策略
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
pytest
```

### 验证脚本行为

也可以单独运行 `scripts/` 下的工具进行调试：

```bash
# 缓存管理
python scripts/resume_cache_manager.py reset
python scripts/resume_cache_manager.py init

# Markdown 转 JSON
python scripts/resume_md_to_json.py cache/resume-working.md -o output.json

# 生成 PDF
python scripts/generate_final_resume.py --input-md cache/resume-working.md

# 质检 PDF
python scripts/check_pdf_quality.py resume_output/resume_final.pdf
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
    └── resume-working.md        # 当前会话简历正文
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

**Q: Skill 会保存我的简历吗？**

A: 不会。Skill 目录本身是 stateless 的，所有缓存和输出文件存放在你的工作区目录（`resume_output/` 和 `cache/`），不会提交到 Git 仓库。

---

## 致谢

本 Skill 参考了以下项目和最佳实践：

- [Anthropic Skills](https://github.com/anthropics/skills) - `pdf` 和 `docx` skill
- [blader/humanizer](https://github.com/blader/humanizer) - 去 AI 痕迹表达
- [oh-my-opencode](https://github.com/anomalyco/oh-my-opencode) - Agent 自动安装模式
