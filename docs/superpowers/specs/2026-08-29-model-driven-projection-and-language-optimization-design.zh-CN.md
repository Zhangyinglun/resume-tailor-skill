# 模型驱动的简历投影与自然语言优化

- 状态：设计已批准，等待实施计划
- 日期：2026-08-29
- 范围：`monkey-resume` Skill 包
- 验收样例：Yinglun Zhang 申请 OpenAI Applied AI Engineer, Plugins

## 1. 背景

当前 Skill 已能将职位描述拆解为 P1/P2/P3 的 JD Capability，将候选人证据保存在 Candidate Evidence Ledger 中，在 Tailoring Manifest 中记录简历定制动作，执行事实完整性审计，并生成经过验证的单页 A4 PDF。

但项目目前缺少一个明确且可验证的流程接缝，无法让模型稳定地完成内容预算分配。Agent 可以人工把相关经历提前、删除低价值内容并改写 Skills，但脚本本身不会自动把 JD Capability 的证据链接转换成面向特定岗位的 Projection Plan。现有 `score_all_bullets()` 辅助函数会按照 P1/P2/P3 词面命中进行评分，但它未接入投影生成流程；当 JD 与简历使用不同表达时，它也无法识别语义匹配证据。

项目还需要一个简历专用的自然语言优化层。即使内容完全真实，通用模型生成的文字仍可能显得模板化、营销化或带有明显 AI 痕迹。通用 Humanizer Skill 中有一些值得采用的编辑模式，但其中许多用于注入个人语气或规避检测器的做法并不适合简历。

## 2. 目标

1. 使用宿主模型判断哪些证据对目标 JD 最重要，不依赖固定关键词权重公式。
2. 为高价值 Evidence Entity 分配更多内容，为低价值实体分配更少内容，同时保留完整的正式工作履历。
3. 动态生成 Skills，只保留与目标岗位相关、有证据支持或属于岗位基础能力的技能。
4. 生成简洁、自然、面向招聘官的英文，同时不改变任何候选人事实。
5. 在压缩布局之前先调整内容，把最强证据放入单页 A4。
6. 保留完整的 Tailoring Manifest 覆盖和强制事实审计。
7. 将模型供应商集成留在 Python 包之外：由宿主 Agent 提供结构化规划和语言产物。
8. 当规划、审计、Content Fit、渲染或 QA 失败时，保留之前的 Accepted Resume。

## 3. 非目标

- 预测或操纵第三方 ATS 的排名算法。
- 针对 GPTZero、Turnitin、ZeroGPT 或其他 AI 检测器进行优化。
- 通过错别字、俚语、生僻同义词、人为句长波动或语法错误制造所谓“人味”。
- 允许模型从 JD 推断候选人使用过的工具、指标、范围、ownership、环境、生产状态或完成状态。
- 删除整段正式工作经历并制造无法解释的职业时间空档。
- 允许 `--auto-fit` 修改简历内容。
- 在随包 Python 脚本中加入模型 SDK、API Key、供应商 Adapter 或网络调用。

## 4. 已批准的产品决策

1. 使用基于 Capability Link 的模型规划，而不是固定词面相关性分数。
2. 保留每一段正式工作经历，包括公司、职位、日期和至少一条 bullet。
3. 当 Projects、Awards、Patents 等可选内容的边际价值较低时，允许整体删除。
4. 在最终规划前，最多提出 3–5 个高价值 Clarification。
5. 始终以单页 A4 为目标。
6. 自动应用内容决策，并在 Tailoring Manifest 和最终报告中解释所有实质性新增、合并、重排、弱化和删除。
7. 按证据链策略动态生成 2–4 个 Skills 组。
8. Skills 中的标准工具名和编程语言名保持不变。
9. 在证据选择后、事实审计前增加独立的 Resume Language Optimizer。
10. 将 AI 写作模式检查视为可解释的编辑信号，而不是作者身份分类器。
11. 将 Skills 从一个逗号分隔字符串演进为可逐项审计的展示项，同时继续兼容旧字符串输入格式。

## 5. 领域模型

### Projection Plan

面向特定目标岗位、受证据约束的决策记录。它选择 Content Intent、分配展示重要性和页面预算，并在生成最终展示文字前决定哪些可选内容需要保留、合并或删除。

### Content Intent

描述某个 Tailored Resume 元素必须表达什么、由哪些 Atomic Claim 和 JD Capability 支持、应获得多少展示空间的指令。它不包含最终文案。

### Resume Language Optimization

将 Content Intent 转换成简洁、自然、面向招聘官的简历文案，同时保持证据范围、标准技术词、指标和 ownership 不变的语义保真转换。

### Skill Presentation Group

面向特定目标岗位的展示分组，其 category label 用于组织可逐项绑定证据的 Skill item。Category 是展示元数据，不是 Evidence Entity，也不是关于候选人的事实 claim。

### Content Fit Feedback

由 Candidate PDF 的真实几何信息测得的反馈，用于判断内容是溢出、过少还是适配。它用于修订 Projection Plan，不是字符数估算，也不是 auto-fit 分数。

## 6. 架构

```text
Source Snapshot + Candidate Evidence Ledger + Candidate Profile
                              +
                        JD Analysis
                              |
                              v
                  宿主模型 Projection Planner
                  - 选择证据
                  - 判断模块重要性
                  - 分配内容预算
                  - 决定 Skills 和可选 Section
                              |
                              v
                   cache/projection-plan.json
                              |
                              v
                宿主模型 Resume Language Optimizer
                - 使用技术简历语域
                - 生成简洁自然的措辞
                - 执行 meaning-preservation 自检
                              |
                              v
                 cache/projection-language.json
                              |
                              v
                  Projection Plan Manager
                  - 确定性验证
                  - 生成 Tailored Resume
                  - 生成 Tailoring Manifest
                              |
                 +------------+------------+
                 |                         |
                 v                         v
       cache/resume-working.json  cache/resume-changes.json
                 |
                 v
             Mandatory Factual Audit
                 |
                 v
       使用优选可读布局进行临时渲染
                 |
                 v
          Content Fit Feedback
          - overflow：减少低价值内容
          - underfill：增加未使用的高价值证据
          - fit：进入下一阶段
                 |
         最多进行三次计划修订
                 |
                 v
          仅调整布局的 Auto-fit
                 |
                 v
     PDF QA + Visual QA + 发布
```

### 接缝位置

结构化文件 `projection-plan.json` 和 `projection-language.json` 构成宿主模型与确定性 Python 代码之间的接缝。项目不引入模型供应商 Interface，因为当前包没有第二种模型 Adapter，而且必须保持对不同 Agent 宿主的可移植性。

Projection Plan Manager 是一个深模块：调用者只提供 workspace 和两个模型产物；模块内部隐藏 schema 验证、证据链接验证、投影生成、Manifest 生成、fingerprint 计算和原子写入。

## 7. 外部 Interface

计划中的 Python Interface：

```python
build_projection(
    workspace: Path,
    plan_path: Path,
    language_path: Path,
) -> BuildResult
```

计划中的 CLI：

```bash
python3 scripts/projection_plan_manager.py build \
  --workspace "$USER_WORKSPACE" \
  --plan "$USER_WORKSPACE/cache/projection-plan.json" \
  --language "$USER_WORKSPACE/cache/projection-language.json"
```

该 Interface 必须：

- 只读取 active 且状态为 `sourced` 或 `candidate_confirmed` 的 claim；
- 验证当前 JD 和 Source Snapshot fingerprint；
- 拒绝不完整的计划或语言产物；
- 只有在所有验证通过后，才原子写入 Tailored Resume 和 Tailoring Manifest；
- 返回结构化结果，说明生成路径、clarification 状态和验证发现。

建议的 CLI 退出语义：

- `0`：投影和 Manifest 构建成功；
- `1`：计划无效、语言输出无效、输入过期或违反证据约束；
- `2`：必须先完成 Clarification，当前不能构建最终投影。

## 8. Projection Plan 契约

顶层字段：

```json
{
  "schema_version": 1,
  "revision": 1,
  "status": "ready",
  "target_jd_fingerprint": "sha256:current-jd-fingerprint",
  "source_snapshot_fingerprint": "sha256:current-source-fingerprint",
  "constraints": {
    "page_size": "A4",
    "page_count": 1,
    "experience_bullet_min": 1,
    "experience_bullet_max": 5,
    "skills_group_min": 2,
    "skills_group_max": 4,
    "skills_rendered_line_min": 2,
    "skills_rendered_line_max": 4,
    "clarification_question_max": 5,
    "content_fit_revision_max": 3
  },
  "clarifications": [],
  "summary_intent": {},
  "experience_plans": [],
  "skills_plan": {},
  "optional_sections": [],
  "next_cuts": []
}
```

### 计划状态

- `needs_clarification`：包含 1–5 个问题，不能生成最终投影。
- `ready`：证据链接完整，可以进入语言优化阶段。
- `revision_required`：之前的几何反馈要求修订内容。

### Experience Plan

```json
{
  "entity_id": "experience-microsoft-current-role",
  "importance": "critical",
  "target_bullet_count": 4,
  "reason": "Carries the strongest P1/P2 AI platform and tool-calling evidence.",
  "content_intents": [
    {
      "intent_id": "intent-ms-mcp-tool-calling",
      "claim_ids": ["claim-mcp", "claim-azure-openai"],
      "capability_ids": ["cap-p1-tool-calling"],
      "operation": "EMPHASIZE",
      "content_intent": "MCP diagnostics workflow using Azure OpenAI tool calling for incident investigation",
      "target_lines": 2
    }
  ]
}
```

`importance` 是模型给出的可解释决策，不是固定数值分数。允许值为 `critical`、`important` 和 `supporting`。

### 可选 Section 决策

```json
{
  "section": "awards",
  "entity_ids": ["award-chinese-patent"],
  "decision": "remove",
  "reason": "The patented algorithm remains represented in the selected JD.COM evidence and the standalone section does not cover a target P1/P2 capability."
}
```

## 9. Clarification 协议

只有当答案可能改变 P1/P2 内容选择、事实具体程度或模块预算时，Projection Planner 才能提出 1–5 个问题。

问题可以针对：

- 准确的工具或平台；
- 规模或指标；
- ownership level；
- partner 或 customer scope；
- production 或 completion state；
- evaluation 方法或结果。

不得为了增加关键词覆盖而针对 unsupported 的 P3 术语浪费问题预算。候选人答案必须作为绑定到 Evidence Entity 的 Candidate Confirmation 入账，并保留原始回答摘录。只有答案已入账，或明确决定保留 Gap 后，才能生成最终的 `ready` 计划。

## 10. 模型驱动的内容预算

模型使用完整 JD Capability、Match Type、Evidence State、关联 Atomic Claim、时间远近、证据独特性和内容重叠情况判断相对价值。Python 不维护 P1/P2/P3 数值排名公式。

硬性约束：

- Base Resume 中的每个正式工作 Evidence Entity 都必须出现；
- 每段正式工作必须有 1–5 条 bullet；
- 不得在同一条 bullet 中组合不同 Evidence Entity 的 claim；
- 指标必须继续绑定原始 Evidence Entity；
- 可选 Section 可以删除；
- Summary、联系方式、工作履历和教育信息必须完整；
- 每项实质性决策必须提供可用于 Tailoring Manifest 和最终报告的理由。

模型通常但不强制采用以下行为：

- critical experience：3–5 条 bullet；
- important experience：2–3 条 bullet；
- supporting experience：1 条 bullet；
- optional content：只有能增加独特的目标岗位价值时才保留。

这些范围用于指导模型。只有正式工作 1–5 条 bullet 是确定性约束。

## 11. Skills 证据链策略

模型动态生成 2–4 个 Skill Presentation Group。类别名称根据目标岗位决定，不要求固定分类体系。在优选可读布局下，Skills 正文必须占 2–4 条真实 PDF 文本行，不含 Section 标题。每个 Skills 组通常应渲染为一行；如果换行使正文超过四行，Content Fit 必须根据真实几何反馈删减、重新分组或删除低价值技能。

Tailored Resume 将 Skills 展示契约从逗号分隔字符串改为可逐项审计的 display term 数组：

```json
{
  "category": "AI Platforms & Tooling",
  "items": ["Azure OpenAI", "MCP", "RAG", "Evals"]
}
```

读取器、验证器和 Renderer 必须继续接受旧字符串格式。旧输入在规划或审计前被规范化为数组；渲染时用 `,` 连接，不在 Tailored Resume 中暴露证据元数据。

Skill item 至少满足以下一个条件才能展示：

1. 直接或语义等价地支持 P1/P2 JD Capability；
2. 被最终选中的 Experience 或 Project Content Intent 使用；
3. 属于目标角色的基础能力，并由 active Atomic Claim 支持。

以下情况应删除 Skill item：

- 没有证据支持；
- 只是低价值 P3 术语，并且挤占更强证据；
- 与另一个展示术语重复，或被另一个术语严格包含；
- 只与已删除的可选内容有关，并且没有独立岗位价值；
- 仅用于重复关键词。

每个展示 Skill item 都必须有独立 claim link 和依据：

```json
{
  "display_term": "Azure OpenAI",
  "claim_ids": ["claim-microsoft-azure-openai"],
  "capability_ids": ["cap-p2-llm-api"],
  "basis": "P2 direct and used by a selected MCP diagnostic Content Intent"
}
```

标准名称和大小写在语言优化期间被冻结。模型可以组织、排序、去重并进行严格 Semantic Normalization，但不能把内部认证替换为 OAuth、把一般 API 替换为 ChatGPT Plugin，也不能用只存在于 JD 中的技术替换已有证据技术。

每个 `skills[i].items[j]` 路径使用普通 single-entity Manifest binding，绑定到真正拥有支持 Atomic Claim 的 Evidence Entity。动态 `skills[i].category` 是 presentation label：其 Manifest entry 使用 `binding_mode: "presentation"`，记录组内 item path 和理由，不得伪装成 Evidence Entity。事实审计器只允许 Skill Presentation Group category 使用这种模式，并检查 category 中的技术术语至少受到组内一个已绑定 item 支持。

## 12. Resume Language Optimizer

### 职责

Projection Planner 决定写什么；Resume Language Optimizer 决定怎么写。它将 Content Intent 转换成最终的 Summary、bullet、可选 Section 和 Skills category 展示文本。

该转换由宿主模型完成。Python 只验证结果，不调用外部模型。

### Language Output 契约

```json
{
  "schema_version": 1,
  "plan_revision": 1,
  "target_jd_fingerprint": "sha256:current-jd-fingerprint",
  "items": [
    {
      "intent_id": "intent-ms-mcp-tool-calling",
      "rendered_text": "Built an MCP diagnostic workflow on Azure OpenAI, using tool calling to investigate incidents across GPU telemetry, technical documentation, and SQL data.",
      "source_claim_ids": ["claim-mcp", "claim-azure-openai"],
      "style_actions": [
        "lead_with_specific_system",
        "remove_template_language"
      ],
      "meaning_check": {
        "facts_added": [],
        "facts_removed": [],
        "metrics_changed": [],
        "ownership_changed": false
      }
    }
  ]
}
```

`meaning_check` 是解释性自检。它不能授权文本，也不能替代事实审计器。

### 简历语域

- 专业、技术、克制；
- 使用隐含第一人称，不出现 `I`、`me`、`my`、`we` 或 `our`；
- 不使用 contraction、聊天式开场、幽默、假装坦率、chatbot offer 或个人故事语气；
- 保留标准技术词汇；
- 每条 bullet 聚焦一个主要贡献；
- 使用简洁的证据优先结构，但不强制每条 bullet 套用同一个公式。

### 采用的 Humanizer 模式

- 删除夸大重要性和营销式描述；
- 删除空洞副词和限定词；
- 用直接表达替换 `serves as`、`stands as` 和 `boasts`；
- 避免 `not only X, but Y` 等 negative parallelism；
- 当第三项不增加证据时，避免强行三项并列；
- 删除无证据的尾部 `ensuring`、`fostering`、`highlighting` 或类似分词从句；
- 删除 `in order to`、`responsible for`、`it is important to note` 等 filler；
- 避免改变技术精度的 synonym cycling；
- 保留 proper noun、标准工具名、指标、日期、scope 和 ownership。

### 拒绝采用的 Humanizer 模式

- 人为错误、俚语或异常语法；
- detector-evasion score；
- 强制 burstiness 或句长方差；
- 随机使用罕见 action verb；
- 自动禁止每一个 em dash、每一个三项列表或每一个孤立的常见 AI 词；
- 博客式 voice injection、第一人称、玩笑、反问或制造个性；
- 改写 ATS 关键技术词；
- 为满足成就公式而添加指标。

### 选择性改写规则

Content Fit 修订不能触发全篇简历重写。未改变的 `intent_id` 必须保持相同 `rendered_text`，除非修订后的 Projection Plan 明确改变其空间预算或 Content Intent。这样可以限制无关措辞漂移，并产生稳定的 diff。

## 13. 投影生成和 Manifest 生成

Projection Plan Manager 合并当前 Projection Plan 和 Language Output。

对于 Tailored Resume 中每个非空字段，必须生成且只生成一条 Manifest entry，其中包含：

- `projection_path`；
- `rendered_text`；
- `binding_mode`，默认为 `single_entity`，只有动态 Skills category label 可以使用 `presentation`；
- 每条 `single_entity` entry 的 `entity_id` 和 active `source_claim_ids`；
- `presentation` category entry 对应的组内 Skill item path；
- operation；
- Match Type；
- 声明的 Semantic Normalization；
- reason。

Skill item 使用 `skills[0].items[0]` 这类路径，因此 Azure OpenAI、MCP、RAG 和 Evals 可以分别绑定到真正拥有证据的 Evidence Entity。审计器不能对任何其他字段类型放宽 single-entity 绑定。

Source Snapshot 或上一次投影中每个被删除的字段，都必须存在 removed-entry 记录。仅有可选 Section 决策并不足够；最终 Manifest 必须列出确切被删除的 source field。

模块先写入临时 JSON，执行验证和 fingerprint 计算，然后原子替换 `resume-working.json` 与 `resume-changes.json`。无效输入不得部分更新任何文件。

## 14. Content Fit 循环

### 优选布局渲染

在 layout auto-fit 之前，使用项目优选可读布局渲染 Candidate PDF。必须使用真实 PDF geometry，不得依赖源文本字符数估算。

计划中的 geometry feedback：

```json
{
  "schema_version": 1,
  "plan_revision": 1,
  "verdict": "overflow",
  "page_count": 2,
  "bottom_whitespace_mm": 6.2,
  "section_geometry": {
    "summary": {"line_count": 4, "height_mm": 16.1},
    "experience[0]": {"line_count": 11, "height_mm": 47.8},
    "skills": {"line_count": 7, "height_mm": 31.2}
  },
  "sparse_trailing_bullets": ["experience[2].bullets[1]"]
}
```

### Overflow 修订顺序

模型按以下顺序考虑：

1. 删除低价值可选 Section；
2. 删除低价值或重复 Skills；
3. 合并同一 Evidence Entity 内重叠的 Content Intent；
4. 缩短 supporting bullet，但不能删除必要证据；
5. 将 supporting employment entry 压缩到一条 bullet；
6. 只有低价值选项用尽后，才压缩 important content。

该顺序是模型指令，不是固定数值删除算法。模型必须记录每项决策和理由。

### Underfill 修订顺序

扩大字体或间距之前，模型先检查是否存在未使用的高价值 active claim：

1. 向最相关的 Evidence Entity 添加独特 Content Intent；
2. 恢复被过度压缩的 P1/P2 贡献；
3. 添加必要且有证据支持的 Skill；
4. 当不存在更多高价值证据时停止添加。

此后 layout auto-fit 才能扩大字体和间距。

### 迭代限制

最多允许三次内容修订。每次修订都重新执行计划验证、语言验证、投影生成、事实审计、临时渲染和 geometry inspection。

## 15. Layout Auto-fit

现有 `auto_fit_layout()` 继续保持仅调整布局。它可以调整：

- font scale；
- line height；
- section spacing；
- item spacing；
- 项目安全范围内的 margin；
- compact mode。

它不能新增、删除、合并、重排或改写内容。PDF QA 报告的内容问题必须返回 Content Fit 工作流，不能交给 layout tuner 解决。

## 16. 语言质量诊断

可以新增确定性 AI pattern linter，但只能作为 advisory diagnostic。它必须报告可解释模式，不能输出 AI probability。

可能的 advisory check：

- stock AI vocabulary 密集出现；
- 重复 bullet 句法；
- negative parallelism；
- forced tricolon；
- 无证据的尾部分词从句；
- filler 和 empty qualifier；
- 过度名词化；
- vague outcome 或不清楚的因果；
- 相邻 bullet 重复同一结果。

Blocking check：

- chatbot artifact；
- 未解决 placeholder；
- 最终简历字段中出现第一人称叙事；
- language artifact 缺少或增加 plan intent；
- Manifest text mismatch；
- unknown、inactive、revoked 或跨实体 claim；
- tool、metric、scope、environment、completion state 或 ownership drift；
- 删除选中 Capability 所需的标准术语。

一个孤立词、单个 em dash 或有效的三项技术列表不能单独阻止发布。

## 17. 错误处理与发布安全

### 规划失败

- 计划无效或过期：失败且不修改当前投影。
- `needs_clarification`：返回问题，不构建最终投影。
- 未知 claim 或 capability link：失败并报告准确的 intent。

### 语言失败

- 缺少 intent 输出、额外 intent 输出、claim link 被改变或 plan revision 不匹配：失败。
- Meaning self-check 报告事实变化：在投影生成前失败。
- 确定性事实审计发现 drift：在渲染前失败。

### Content Fit 失败

- 三次修订后仍无法获得可接受 geometry：在可用时把最后一份 Candidate PDF 保留到 `rejected/`，并保留当前 Accepted Resume。
- 页面过空但没有未使用的高价值证据：接受当前内容选择，并允许 layout auto-fit 在可读范围内扩大布局。

### 发布失败

现有 PDF QA 和 Visual QA 行为继续作为权威。失败的 Candidate 永远不能替换 Accepted Resume。

## 18. 计划中的代码和文档修改

新增文件：

- `scripts/projection_plan_manager.py`
- `tests/test_projection_plan_manager.py`
- `docs/research/humanized-resume-language-layer.md`
- `references/projection-planning-protocol.md`

修改文件：

- `SKILL.md`
- `CONTEXT.md`
- `references/resume-working-schema.md`
- `references/prompt-recipes.md`
- `references/execution-checklist.md`
- `references/resume-language-quality.md`
- `scripts/resume_shared.py`
- `scripts/evidence_ledger_manager.py`
- `scripts/audit_factual_integrity.py`
- `scripts/check_content_quality.py`
- `scripts/check_pdf_geometry.py`
- `scripts/generate_quality_report.py`
- `templates/modern_resume_template.py`
- `tests/test_resume_shared.py`
- `tests/test_evidence_ledger.py`
- `tests/test_factual_audit.py`
- `tests/test_content_quality.py`
- `tests/test_pdf_geometry.py`
- `tests/test_pdf_pipeline.py`
- `tests/test_quality_report.py`

只有集成确实需要传递已计算 artifact 或 diagnostic 时，才修改 `generate_final_resume.py` 和 `layout_auto_tuner.py`。它们不得改变“不能修改内容”的职责边界。

## 19. 测试策略

### Plan Validation

- JD 或 Source Snapshot fingerprint 过期时失败；
- `needs_clarification` 计划不能构建；
- 超过五个 clarification question 时失败；
- 省略正式工作 Evidence Entity 时失败；
- 正式工作 bullet 少于一条或多于五条时失败；
- Skill Presentation Group 少于两个或多于四个时失败；
- 旧的逗号分隔 Skills 输入在不改变展示文本的情况下规范化为 item 数组；
- 每个 `skills[i].items[j]` 都有独立的 single-entity Manifest binding；
- 动态 Skills category 可以使用 presentation binding，其他字段类型不能使用；
- Skills 正文实际少于两行或多于四行时，必须进入 Content Fit 修订；
- 允许删除可选 Awards 或 Projects；
- inactive、revoked、unknown 或跨实体 claim 时失败；
- 构建失败后，现有 projection 和 Manifest 保持不变。

### Language Validation

- 每个 Content Intent 必须且只能有一条 Language Item；
- unknown 或 duplicate intent 时失败；
- claim link 被改变时失败；
- 数字、标准工具、日期、scope、environment 和 ownership 必须继续受到证据支持；
- 第一人称、chatbot residue 和 placeholder 阻止发布；
- stock wording 和 formulaic structure 产生 advisory finding；
- 准确的孤立词和有效技术列表不能误报；
- Content Fit 修订期间，未改变 intent 的文本必须保持一致。

### Materialization 与 Audit

- 有效 fixture 生成完整 Tailored Resume 和 100% Manifest coverage；
- 所有删除字段均被记录；
- 每个有效 fixture 的事实审计通过；
- Semantic Normalization 保持显式，且不能引入工具或 scope。

### Geometry Feedback

- 使用真实 PDF 坐标识别单页适配、多页 overflow 和稀疏 underfill；
- fixture PDF 的 section line count 和 height 保持稳定；
- 继续提供 sparse trailing bullet finding；
- geometry calculation 永远不依赖源文本字符数。

### 端到端验收 Fixture

使用同一候选人和至少两个 JD。

OpenAI Plugins fixture：

- Microsoft MCP、Azure OpenAI、tool calling、Evals、developer documentation、RAG、production APIs 和 reliability 获得优先展示；
- Skills 包含 2–4 个相关组，并实际占 2–4 行；
- 删除独立 Patent/Awards，但 JD.COM bullet 可以保留 `patented` 信号；
- 每段正式工作至少保留一条 bullet；
- 事实审计、Content QA、单页 A4、PDF QA 和 Visual QA 全部通过。

Distributed Systems fixture：

- Skills 转向 Java、Go、C#、Kafka、Kubernetes、Redis、high availability 和 observability；
- TikTok 和 JD.COM 的高吞吐证据获得更多空间；
- 当 MCP 和 Evals 不再值得占用页面时进行压缩；
- 同样通过所有发布闸门。

单元测试不通过网络调用测试模型行为。使用静态 Projection Plan 和 Language Output fixture 测试契约。支持的 Agent 平台通过手动端到端运行验证宿主模型是否遵循协议。

## 20. 验收标准

1. 同一 Candidate Evidence Ledger 面对不同 JD 时，生成明显不同的内容预算和 Skills。
2. 词汇、重要性和删除顺序由模型推理决定，而不是固定关键词分数。
3. 每段正式工作均被保留，并包含 1–5 条 bullet。
4. Skills 包含 2–4 个动态、有证据支持的 Skill Presentation Group，提供可逐项审计的 item path，并在优选布局下实际渲染为 2–4 行正文。
5. 高价值证据最多触发五个 Clarification。
6. Projection Plan 与 Language Output 分别结构化并独立验证。
7. 简历语言具体、自然、克制，没有密集 chatbot pattern，且不使用 detector-evasion 方法。
8. Tailored Resume 每个字段都有有效 Manifest entry，所有删除均被记录。
9. Content Fit 使用真实 PDF geometry，并且最多修订三次。
10. Layout auto-fit 不修改内容。
11. 输出为单页 A4，具有可提取文本和可读 geometry。
12. 任意失败均保留之前的 Accepted Resume。

## 21. 研究依据

- [`docs/research/humanized-resume-language-layer.md`](../../research/humanized-resume-language-layer.md)
- `blader/humanizer`：<https://github.com/blader/humanizer>
- `shir-danishyar/humanize`：<https://github.com/shir-danishyar/humanize>
- Wikipedia WikiProject AI Cleanup patterns：<https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing>
- Harvard FAS resume guidance：<https://careerservices.fas.harvard.edu/resources/create-a-strong-resume/>
- Yale OCS resume bullet guidance：<https://ocs.yale.edu/resources/writing-impactful-resume-bullets/>
- Digital.gov Plain Language：<https://digital.gov/guides/plain-language/writing>
- Liang et al., detector bias：<https://doi.org/10.1073/pnas.2302083120>
- Sadasivan et al., detector limitations：<https://arxiv.org/abs/2303.11156>
