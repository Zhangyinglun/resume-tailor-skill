---
name: resume-tailor
description: Use when 用户提供 JD 与现有简历，希望进行岗位匹配优化、ATS 关键词对齐、语言润色，并交付一页 A4 PDF 简历。
---

# 简历定制 Skill（Resume Tailor）

## 适用场景
- 用户提供目标岗位 JD，希望基于现有简历进行定向优化。
- 用户需要提升 ATS 命中率，要求补齐并自然融入关键词。
- 用户准备海投或多岗位申请，需要快速生成岗位版本简历。
- 用户已有经历但表达偏弱，希望强化成果导向与量化表述。
- 用户担心简历篇幅过长，要求压缩到一页 A4 且保留关键信息。
- 用户需要最终交付可提取文本的 PDF 简历并通过格式质检。

## 使用示例

### 场景一：已有简历 + JD
```text
请基于我的现有简历和以下 JD 做定向优化：
- 简历文件：resume.pdf
- JD：Senior Backend Engineer（Python/FastAPI/AWS）
目标：一页 A4、ATS 友好、突出分布式系统与性能优化成果。
```

### 场景二：无简历，仅提供背景
```text
我没有现成简历，请根据我的背景先生成初版：
- 3 年数据分析经验，熟悉 SQL、Python、Tableau
- 做过用户增长分析与 A/B Test
- 希望投递 Business Analyst 岗位
请先给我一版可迭代的 Markdown 简历。
```

### 场景三：职业转型
```text
我想从测试开发转型到后端开发：
- 现岗位：Test Engineer（5 年）
- 可迁移技能：Python、自动化框架、CI/CD、Linux
- 目标岗位：Backend Engineer
请先做 JD 匹配度诊断，再给出转型导向的简历初稿。
```

## 核心目标
1. **ATS 通过率**：覆盖 JD 高频关键词并保持自然表达。
2. **岗位相关性**：优先突出与目标岗位最匹配的经历、技能和结果。
3. **交付质量**：输出可提取文本的一页 A4 PDF，内容与排版均可复检。

## 不可违反原则
- **不编造经历**：只允许重写、重排、压缩，不允许凭空新增经历/技术/数据。
- **最小化修改**：优先保留原事实，先做结构优化，再做措辞强化。
- **先审阅后导出**：生成文件前必须给出完整简历文本并获得用户明确批准。
- **审阅前体量门禁**：在给用户审阅前必须先检测全文体量；若内容过多，先删减、合并、优化到接近单页目标后再给用户审阅。
- **一次一问**：每次仅给一个决策点，使用 `question` 工具。
- **ATS 友好**：禁止表格主布局、图片代替正文、关键字段放页眉页脚。
- **固定 A4 + 单页**：最终必须为 210mm x 297mm 且 1 页。
- **仅 PDF 交付**：输出链路禁止 `.docx` 中间件。
- **PDF 动作强制 `pdf` skill**：初次生成、微调重生成、最终导出都要先调用 `pdf` skill。

## Stateless 边界（强制）
- `resume-tailor` skill 目录只能存放“规则 + 模板 + 脚本 + 参考资料”。
- 不得在 skill 目录保存任何个性化缓存（用户偏好、历史 JD、联系方式、简历样本）。
- 统一目录约定（相对当前工作区）：
  - `resume_output/`：简历 PDF 输出目录（根目录仅保留最新一份）
  - `resume_output/backup/`：历史简历备份目录
  - `cache/user-profile.md`：长期个性化画像缓存
  - `cache/resume-working.md`：当前会话简历正文缓存（临时）
- `cache/resume-working.md` 生命周期：
  1. **会话启动**：先删除旧缓存（每次重启即删除）
  2. **读取原始简历后**：立即写入标准化 Markdown
  3. **每轮确认修改后**：覆盖更新缓存
  4. **用户确认最终满意后**：保留缓存，作为后续迭代基线（不自动删除）

## 统一流程（合并版 Prompt）

### 阶段 0：会话启动缓存清理
1. 调用 `scripts/resume_cache_manager.py reset` 清理旧 `cache/resume-working.md`。
2. 清理结果写入日志（删除成功或无旧缓存）。

### 阶段 1：输入收集与诊断（4 步）
1. **全量读取模板简历**：
   - 调用 `scripts/resume_cache_manager.py template-check` 检查 `cache/base-resume.md` 是否存在。
   - 若模板不存在，要求用户上传简历（`.pdf` / `.docx`）并通过 `scripts/resume_cache_manager.py template-init` 初始化模板。
   - 调用 `scripts/resume_cache_manager.py template-show` 读取模板全文作为生成输入。
2. **JD 优先级分层与 Gap 分析**：
   - 收集 JD（文本/URL/文件，必填）。
   - 将要求分层为 P1 关键要求 / P2 重要资质 / P3 加分项。
   - 输出匹配度诊断报告：已命中、可迁移、缺口（缺口需附简短改进建议）。
   - 先向用户展示诊断结论并获得确认，再进入初版生成。
3. **根据 JD 生成初版 MD 简历**：
   - 基于“模板全文 + JD + 匹配度诊断”生成初版。
   - 确保 P1 全覆盖、P2 尽量覆盖。
   - 写入 `cache/resume-working.md`。
4. **根据问答不断更新简历**：
   - 每轮基于用户反馈修改 `cache/resume-working.md`。
   - 通过 `scripts/resume_cache_manager.py update` 覆盖写回，直到用户确认满意。

### 阶段 2：逐条协商修改（迭代）
- 每轮只提 1 条建议，等待用户确认后再进入下一条。
- 优先级：
  1. 补齐核心缺失关键词
  2. 用 JD 原词强化描述
  3. 调整内容顺序（相关内容前置）
  4. 删减低相关内容（默认先征得同意；若用户已明确授权自动收敛，则可直接执行并在报告披露）
- 每次用户确认后：
  - 基于当前 `cache/resume-working.md` 更新内容
  - 通过 `scripts/resume_cache_manager.py update` 覆盖写回缓存

### 阶段 3：审阅前内容体量检测与收敛（新增）
- 在输出“简历全文预览”给用户前，必须先对 `cache/resume-working.md` 执行体量检测。
- 检测指标（任一超限即触发收敛）：
  1. 总字数建议 520-760（英文简历可按等价词数估算）
  2. 非空行建议 32-52 行
  3. Experience bullet 总数建议 8-14 条
  4. 单条 bullet 建议不超过 2 行（约 28 个英文词）
- 触发收敛后必须按顺序处理：
  1. 删除低相关或重复信息（优先删除与 JD 关联弱内容）
  2. 合并同类 bullet（同一职责/同类结果合并为 1 条）
  3. 压缩句式（保留四要素：action + keyword + method/tool + result）
- 收敛约束：
  - 不得编造事实，不得删除关键资质（联系方式、核心技能、最高相关经历）。
  - 必须保留 JD 核心关键词命中与量化结果。
  - 当用户已明确授权“内容过多就删减合并优化”时，可先执行收敛，再通过审阅稿说明变更。
- 每轮收敛后必须重新检测，直到进入目标区间，才允许输出审阅版全文。
- 输出审阅版时必须附“压缩报告”：原始体量、当前体量、删减/合并摘要、保留关键词清单。

### 阶段 4：质量保证与去 AI 化
进入排版前，必须完成 4 类检查并输出 QA 报告：
1. **结构逻辑**：Summary 聚焦度、证据链、时间线一致性
2. **自然表达**：调用 `humanizer` / `humanizer-zh` skill 去除 AI 痕迹词
3. **量化结果**：检查每条经历是否含四要素（action + keyword + method/tool + result），缺数字或缺方法/工具则标注
4. **ATS 细节**：关键词原词命中、时态统一、联系信息完整

通过体量门禁后输出“简历全文预览”时，必须直接读取 `cache/resume-working.md`，不得用记忆重构。

### 阶段 5：PDF 生成、检测与微调
1. 用户明确批准全文后，才进入生成。
2. 先调用 `pdf` skill，再生成 A4 单页 PDF。
3. 生成时优先走 Markdown 真源：
   - `scripts/generate_final_resume.py --input-md cache/resume-working.md ...`
4. 质检必须覆盖：A4、1 页、模块完整性、文本层可提取、HTML 标签泄漏、底部留白 3-8mm。
5. 不通过则按单参数顺序微调并重生成。
6. 命名与备份规则：`{MM}_{DD}_{Name}_{Position}_resume.pdf`；每次生成前将 `resume_output/` 根目录中其他 PDF 统一迁移到 `resume_output/backup/{Position}/`，并按 `_old_N` 递增命名。

### 阶段 6：收尾与缓存保留（4 步）
1. 更新 `cache/user-profile.md`（长期偏好与方向日志）。
2. 保留 `cache/resume-working.md` 作为后续迭代基线（不自动删除）。
3. 延伸建议（可选）：面试准备要点 / Cover Letter 开头建议 / Gap 应对策略；用户未要求则跳过。
4. 隐私提醒：提交前检查联系方式、地址等个人信息准确性和敏感信息。

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
- `humanizer` / `humanizer-zh`：去除 AI 痕迹，提升自然表达

## 特殊场景策略

### 职业转型者
- 采用混合格式：保留时间线，同时前置“目标岗位相关能力”与代表性项目。
- 强化转型叙事：说明转型动机、学习路径与目标岗位连接点。
- 突出可迁移技能：把原岗位中的方法、工具和结果映射到目标岗位关键词。

### 应届生 / 早期职业者
- Education 前置：当全职经历不足时，将 Education 放在 Experience 之前。
- 强化实习与项目：用课程项目、实习成果、竞赛或开源贡献补足证据链。
- GPA 规则：仅在 GPA 较高或 JD 明确要求时展示，并保持格式统一。

### 高管 / 资深管理者
- 聚焦战略影响：优先展示业务战略、组织升级与跨部门协同成果。
- 强化管理指标：明确团队规模、预算体量、营收增长、利润改善等关键数字。
- 篇幅策略：在信息密度高且确有必要时，可放宽到 2 页，但仍需保持 ATS 可解析。

## 参考资料
- ATS 策略：`references/ats-keywords-strategy.md`
- 画像缓存模板：`references/profile-cache-template.md`
- 工作缓存结构：`references/resume-working-schema.md`
- 模板说明：`templates/README.md`
