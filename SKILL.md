---
name: resume-tailor
description: Use when 用户需要基于目标 JD 优化或重写简历，并要求 ATS 关键词对齐、岗位匹配诊断、内容压缩到单页，以及最终交付可提取文本的 A4 PDF。
---

# 简历定制 Skill（Resume Tailor）

## 核心目标
- **ATS 命中率**：覆盖 JD 高频关键词且保持自然表达。
- **岗位相关性**：优先呈现最匹配岗位的证据链与量化结果。
- **交付质量**：输出可提取文本的 A4 PDF，并通过格式质检。

## 不可违反原则
- **不编造事实**：只重写、重排、压缩，不新增虚构经历/技术/数据。
- **先审阅后导出**：导出前必须提供完整审阅稿并获得明确批准。
- **先过体量门禁再审阅**：内容超限先收敛，再给用户看全文。
- **一次一问**：每轮只给一个决策点，使用 `question` 工具。
- **ATS 友好**：不用表格主布局，不用图片替代正文，不把关键信息放页眉页脚。
- **固定 A4 + 单页**：默认交付 210mm x 297mm、1 页。
- **仅 PDF 交付**：最终产物只交 PDF。
- **PDF 动作前先调用 `pdf` skill**：初次生成、微调重生成、最终导出都执行。

## Stateless 边界（强制）
- `resume-tailor` skill 目录只能存放“规则 + 模板 + 脚本 + 参考资料”。
- 不得在 skill 目录保存任何个性化缓存（用户偏好、历史 JD、联系方式、简历样本）。
- 统一目录（相对工作区）：
  - `resume_output/`：当前最新 PDF
  - `resume_output/backup/`：历史 PDF 备份
  - `cache/user-profile.md`：长期偏好缓存
  - `cache/resume-working.md`：当前会话简历正文

## 最小执行流程
1. **会话启动清理**：`scripts/resume_cache_manager.py reset`
2. **读取模板简历**：`template-check` → `template-show`（不存在则 `template-init`）
3. **JD 诊断**：输出 P1/P2/P3 匹配与 gap，用户确认后生成初版
4. **迭代更新**：每轮只改 1 个决策点，确认后 `update`
5. **体量门禁**：先收敛到单页目标，再输出审阅全文
6. **QA + 去 AI 化**：调用 `humanizer`，补齐结构/量化/ATS 检查
7. **PDF 生成与质检**：用户批准后调用 `pdf` 并生成、检测、必要时微调重生
8. **收尾**：更新画像缓存，保留工作缓存作为后续基线

完整检查项与阈值见 `references/execution-checklist.md`。

## 固定模板基线（逻辑结构）
始终按以下模块顺序组织内容：

```markdown
Header
Summary
Technical Skills
Professional Experience
Education
```

## 脚本职责边界
- `scripts/resume_cache_manager.py`：管理 `cache/resume-working.md` 的 reset/init/update/show（`cleanup` 仅手动按需使用），以及 `cache/base-resume.md` 模板的 template-init/template-use/template-show/template-check。
- `scripts/resume_md_to_json.py`：把标准化 Markdown 转为模板输入 JSON。
- `scripts/generate_final_resume.py`：接收 `--input-md` 或 `--input-json` 并生成最终 PDF。
- `scripts/check_pdf_quality.py`：做通用格式与文本质量检查。
- `templates/modern_resume_template.py`：仅负责 PDF 排版与导出。

## 依赖 Skill
- `docx`：读取 `.docx` 简历
- `pdf`：读取 PDF、执行所有 PDF 生成与复检动作
- `humanizer`：去除 AI 痕迹，提升自然表达

## Agent 安装与自动执行入口
- 安装总入口：`docs/guide/installation.md`
- 机器可读清单：`install/agent-install.yaml`
- OpenCode 命令入口：`.opencode/command/install-skill-deps.md`

## 参考资料
- 全流程检查与阈值：`references/execution-checklist.md`
- ATS 策略：`references/ats-keywords-strategy.md`
- 画像缓存模板：`references/profile-cache-template.md`
- 工作缓存结构：`references/resume-working-schema.md`
- 模板说明：`templates/README.md`
