# resume-tailor

[English](README.md)

一个可分发的 **AI Skill**，支持 Claude Code、Codex 和 OpenCode。给它你的简历和 JD，它会输出 ATS 优化的单页 A4 PDF。

---

## 一分钟上手

### 第一步 — 安装

```bash
git clone https://github.com/your-org/resume-tailor-skill
cd resume-tailor-skill
python3 -m pip install -r requirements.txt
```

### 第二步 — 注册到你的 AI 助手

| 平台 | 操作 |
|---|---|
| **Claude Code** | 直接在 Claude Code 中打开本仓库，`CLAUDE.md` 会自动加载，无需额外配置。 |
| **Codex** | 将本仓库复制到 `~/.agents/skills/resume-tailor/` |
| **OpenCode** | 将本仓库复制到 `~/.config/opencode/skills/resume-tailor/` |

### 第三步 — 使用

把 JD 和简历粘贴到对话框，然后说：

```
根据这份 JD 优化我的简历，输出单页 PDF。
```

Agent 会自动完成全部工作：关键词对齐、内容改写、版式调整、PDF 输出。

---

## 工作原理

```
你提供：现有简历 + 目标 JD
      │
      ▼
[A] 初始化工作区缓存
      │
      ▼
[B] 分析 JD → 改写 bullet（不捏造经历）
      │
      ▼
[C] 体量检查 → 压缩至单页 → 语言自然化
      │
      ▼
[D] 生成 PDF → 质量检查 → 输出摘要报告
```

Skill 本身**无状态**，你的数据只写入工作区的 `cache/` 和 `resume_output/` 目录，不会进入 skill 包。

---

## 目录结构

```
resume-tailor/
├── SKILL.md                   # Skill 主定义（agent 读取此文件）
├── CLAUDE.md                  # Claude Code 自动加载配置
├── AGENTS.md                  # Codex 入口
├── requirements.txt
├── scripts/                   # resume_cache_manager.py、generate_final_resume.py 等
├── templates/                 # .docx 基础模板（Calibri / Helvetica 回退）
├── references/                # 优化动作代码、缓存结构说明、提示词参考
├── vendor/skills/             # 内联依赖：pdf、docx、humanizer
├── .claude/commands/          # /resume-tailor 和 /check-resume-tailor-setup
├── .opencode/command/
└── docs/guide/installation.md
```

---

## 验证安装

```bash
python3 scripts/check_agent_platform_support.py
```

---

## 关键约束

- **不捏造**：只对你已有的内容进行改写和重排。
- **`--auto-fit`** 只调整版式参数，不改写简历内容。
- 输出固定为单页、A4、可提取文本的 PDF。

## 许可证

MIT，详见 `LICENSE`。
