# 简历自然语言优化层：Humanizer 方案调研

- 文档状态：已复核
- 最后复核：2026-08-29
- 适用范围：`resume-tailor` 中面向招聘官的英文 Summary、Experience/Project bullets 与 Skills 命名
- 不适用范围：规避 AI 检测器、制造虚假“人类错误”、改变候选人事实或写作成第一人称叙事

## 1. 结论

本项目不应接入通用“AI detector bypass”或以检测器分数作为目标。适合本项目的是一个**模型驱动、简历语域限定、事实保真的 Resume Language Optimizer**：

1. Projection Planner 先决定写什么、保留哪些 claims、各模块分配多少内容；
2. Language Optimizer 根据内容意图生成自然、具体、克制的简历英语；
3. 确定性代码验证 claim links、工具、指标、scope、ownership 与 Manifest 同步；
4. Factual Audit 在任何 PDF 渲染前阻断语言优化造成的事实漂移；
5. AI 写作 pattern 只用于编辑诊断，不用于判断作者身份或作为发布分数。

核心原则：**模型负责语义、节奏和措辞；代码负责事实、结构和发布边界。**

## 2. 调研来源与主要发现

### 2.1 `blader/humanizer`

原始 Skill 明确要求：

- 保留每项 claim，不为自然感编造事实；
- 根据文本语域匹配 voice；技术、事实和参考文本保持中性；
- 检查 inflated significance、sales language、vague claims、stock AI words、copula avoidance、forced groups of three、false ranges、passive voice 和 chatbot artifacts；
- 改写后重新核对是否新增或删除事实、名称、数字、日期或其他 claim；
- 不将原结构视为不可改变，可围绕主要事实重写。

这些规则与 Evidence Ledger、Manifest 和 Factual Audit 高度兼容。

来源：

- <https://github.com/blader/humanizer>
- <https://github.com/blader/humanizer/blob/main/SKILL.md>
- <https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing>

### 2.2 `shir-danishyar/humanize`

该 Skill 提供两个值得采用的设计：

- **Generation mode**：在初次生成时避免模板化表达，而不是先生成一版 AI 味文本再机械同义词替换；
- **Register awareness**：formal/technical 文本不应加入口语、片段句或第一人称；pattern 应按密度和上下文判断，而不是看到一个词就强制删除。

它还强调：数字、日期、proper nouns、引用和技术词必须保持；precision 优先于 style。

来源：

- <https://github.com/shir-danishyar/humanize>
- <https://github.com/shir-danishyar/humanize/blob/main/SKILL.md>

### 2.3 招聘与 Plain Language 指南

Harvard 和 Yale 的职业指导支持以下简历实践：

- 使用具体、主动、直接的表达；
- bullet 以候选人的实际动作开头；
- 表达 project/problem 和 evidenced result；
- 能量化时量化，不能为套公式编造数字；
- 删除 pronouns 和空泛职责描述；
- 根据目标岗位强调相关经历。

Digital.gov / Plain Language 指南支持：

- 使用 active voice 明确谁做了什么；
- 每句聚焦一个主要想法；
- 删除多余修饰、重复和名词化表达；
- 保留必要专业术语，避免无意义 jargon。

来源：

- <https://careerservices.fas.harvard.edu/resources/create-a-strong-resume/>
- <https://ocs.yale.edu/resources/writing-impactful-resume-bullets/>
- <https://ocs.yale.edu/resources/resume-formatting/>
- <https://digital.gov/guides/plain-language/writing>
- <https://digital.gov/guides/plain-language/writing/clear-short>
- <https://digital.gov/guides/plain-language/principles/short-simple>

### 2.4 AI 检测器不是合适目标

本项目已有研究综述指出：通用 AI 检测器存在领域失配，并可能对非母语英语写作者产生严重误判。检测器结果不能证明文本作者身份，也不应成为候选人文案的 PASS/FAIL 门禁。

项目决策：

- 不接入 GPTZero、ZeroGPT、Turnitin 等检测分数；
- 不为提高 perplexity 或 burstiness 注入生僻同义词、错别字、俚语或异常语法；
- 只优化招聘官能直接感知和解释的质量：具体性、事实密度、因果清晰、自然节奏、克制语气和可扫描性。

相关原始研究：

- Liang et al., *GPT detectors are biased against non-native English writers*: <https://doi.org/10.1073/pnas.2302083120>
- Sadasivan et al., *Can AI-Generated Text be Reliably Detected?*: <https://arxiv.org/abs/2303.11156>

## 3. 适合本项目的规则

### 3.1 必须采用

1. **保留事实边界**
   - 不改变公司、职位、日期、工具、指标、scope、ownership、environment 或 completion state；
   - 不把内部认证写成 OAuth，不把一般 API 写成 ChatGPT Plugin；
   - 不跨 Evidence Entity 借用指标或成果。

2. **用具体事实替代评价**
   - 优先系统、动作、方法、约束和结果；
   - 删除 `pivotal`、`groundbreaking`、`transformative`、`best-in-class` 等无证据意义夸张；
   - 删除 `successfully`、`strategically`、`seamlessly` 等不增加信息的副词。

3. **删除模板化结构**
   - 避免 `not only X, but Y`、`not just X, but Y`；
   - 避免为了完整感强行三项并列；
   - 删除无证据的尾部 `, ensuring... / fostering... / highlighting...`；
   - 避免 `serves as / stands as / boasts` 替代简单直接动词；
   - 删除 `in order to`、`responsible for`、`it is important to note` 等 filler。

4. **保持简历语域**
   - implicit first person，不出现 `I / me / my / we`；
   - 不使用聊天开场、反问、俚语、幽默、fake-candid opener；
   - 使用专业、技术、克制的英文；
   - 技术词保持 canonical spelling，例如 `Go`、`C#`、`.NET`、`Azure OpenAI`、`MCP`。

5. **避免机械重复，同时不强求同义词轮换**
   - 可以重复最准确的技术词；
   - 不把同一对象轮换成不准确的 synonym；
   - 调整句法、信息顺序和 bullet 重点，而不是只换动词。

6. **Meaning check**
   - 每次优化后回答：是否新增、删除、扩大或弱化任何事实？
   - 如果自然表达需要缺失信息，应产生 clarification question 或采用更简单的句子。

### 3.2 明确拒绝

- 用 typo、slang、口语片段或错误语法制造“人味”；
- 按 AI detector 分数反复 paraphrase；
- 为追求 burstiness 故意加入长短句波动；
- 将个人博客式 voice profile 直接用于技术简历；
- 强制禁止每一个 em dash、三项列表或常见词；单一 pattern 不是问题，密集模板化才是问题；
- 用随机稀有 action verbs 代替准确 ownership；
- 强制每条 bullet 都有数字；
- 把 ATS 必要技术词替换成通俗比喻；
- 生成第一人称叙事、营销口号或“个人品牌宣言”。

## 4. 推荐架构

### 4.1 Pipeline 位置

```text
JD Analysis + Evidence Ledger
            ↓
Projection Planner
- 选择 claims
- 分配模块内容预算
- 输出 content intents，不负责最终英文
            ↓
Resume Language Optimizer（模型驱动）
- technical resume register
- 生成 Summary / bullets / Skills display wording
- 输出 meaning-preservation report
            ↓
Projection Builder
- resume-working.json
- resume-changes.json
            ↓
Mandatory Factual Audit
            ↓
Content Fit / PDF Geometry loop
            ↓
Layout-only Auto-fit
```

语言层应在 Projection Planner 之后，因为只有入选证据值得优化；必须在 Factual Audit 之前，因为模型改写可能引入 tool、metric、scope 或 ownership drift。

### 4.2 Planner 与语言层分工

Planner 输出“写什么”：

```json
{
  "entity_id": "experience-microsoft-...",
  "claim_ids": ["claim-mcp", "claim-azure-openai"],
  "capability_ids": ["cap-p1-tool-calling"],
  "content_intent": "MCP diagnostics workflow using Azure OpenAI tool calling for incident investigation",
  "importance": "critical",
  "target_lines": 2
}
```

Language Optimizer 输出“怎么写”：

```json
{
  "rendered_text": "Built an MCP diagnostic workflow on Azure OpenAI, using tool calling to investigate incidents across GPU telemetry, technical documentation, and SQL data.",
  "source_claim_ids": ["claim-mcp", "claim-azure-openai"],
  "style_actions": ["remove_template_language", "lead_with_specific_system"],
  "meaning_check": {
    "facts_added": [],
    "facts_removed": [],
    "metrics_changed": [],
    "ownership_changed": false
  }
}
```

模型的 `meaning_check` 只用于解释和自检，不能代替确定性 Factual Audit。

### 4.3 Content Fit 集成

每轮几何反馈后：

- Planner 决定删除、恢复、合并哪些 content intents；
- Language Optimizer 只优化新增或发生预算变化的文本；
- 避免全篇重写导致无关措辞漂移；
- 最多 3 轮；失败时不覆盖 Accepted Resume。

页面 underfill 时，先从未使用的高价值 active claims 增加内容；没有可增加证据时才扩大布局。页面 overflow 时，先删低价值 section/skills/bullets，再进行句子压缩。

## 5. QA 设计

### 5.1 阻断项

- 语言层引入未知工具、指标、scope 或 ownership；
- `rendered_text` 与 Manifest 不同步；
- claim IDs 无效、inactive、revoked 或跨实体；
- Chatbot artifacts、placeholder、第一人称进入最终简历；
- 删除必要 ATS 技术词导致已选 capability 失去展示依据。

### 5.2 Advisory 项

可以增加确定性 pattern linter，但只能 WARN：

- stock AI vocabulary 密集出现；
- 多条 bullet 采用完全相同语法；
- forced tricolon；
- negative parallelism；
- trailing significance participle；
- filler、nominalization、empty qualifier；
- vague outcome 或不清楚因果；
- 相邻 bullet 重复同一结果。

单个词或单个 em dash 不应自动失败。最终判断针对 pattern cluster 和招聘语境。

### 5.3 不采用的指标

- AI probability；
- detector evasion score；
- 为模拟“人类 burstiness”而设计的句长方差目标；
- 强制词汇多样性；
- 固定 rare-action-verb 配额。

## 6. 测试建议

1. **Meaning preservation fixtures**：优化前后公司、职位、日期、数字、技术词、scope 和 ownership 完全一致；
2. **Resume register fixtures**：不出现 pronouns、chatbot phrases、slang 或营销口号；
3. **Pattern cleanup fixtures**：删除 significance inflation、forced tricolon、negative parallelism 和 empty `-ing` tail；
4. **False-positive fixtures**：准确的 `led`、必要的三项技术列表、canonical 技术词不得因 pattern 规则被删除；
5. **JD preservation fixtures**：P1/P2 技术词在语言优化后仍可检索；
6. **Selective rewrite fixtures**：仅优化变化的 content intents，不改动无关字段；
7. **End-to-end OpenAI fixture**：MCP、Azure OpenAI、tool calling、RAG、Evals、APIs 保持，表达自然克制，Factual Audit 和单页 A4 QA 通过。

## 7. 项目决策

该层的产品名称建议使用 **Resume Language Optimizer** 或 **Recruiter Voice Editor**，而不是 `Humanizer`。原因：项目目标是提升招聘官可读性和候选人可信度，不是隐藏模型参与或规避检测器。
