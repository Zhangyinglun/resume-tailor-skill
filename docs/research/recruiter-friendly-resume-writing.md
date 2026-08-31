# 招聘官友好、自然可信的简历文案：证据综述与 Prompt 规范

- 文档状态：已复核
- 最后复核：2026-08-28
- 适用范围：英语技术岗位简历的内容选择、改写、ATS 可读性与质量检查
- 不适用范围：声称存在统一的 ATS 排名算法，或承诺某种格式对所有招聘系统均 100% 兼容

## 1. 结论摘要

本研究支持以下设计方向：

1. **事实保真优先于措辞强度。** 公司、职位、日期、工具、职责范围和指标必须有候选人证据；缺失信息应追问、保留为 gap，或改用准确的定性结果，不能估算。[CONSENSUS PRACTICE] `R6` `R7` `G2` `G3`
2. **自然感主要来自具体事实和清晰因果，而不是“人类化”同义词替换。** 通用语料研究确实观察到指令模型更偏好分词从句、名词化和短语并列，但这些统计不能直接变成简历禁用语法。[EVIDENCE] `R1`
3. **禁词表只能作为提醒。** `delve`、`pivotal` 等词在 LLM 辅助写作后出现超额增长，但研究对象主要是学术或生物医学文本，不是简历；单词本身也可能在合适语境中成立。[EVIDENCE，迁移需谨慎] `R2`
4. **招聘官需要快速找到关键信息，但“只有 6 或 7.4 秒”不是可靠的通用定律。** 可采用清楚的标题层级、倒序经历、相关信息前置和可快速辨认的技术/结果；不要围绕一个精确秒数优化。[QUALIFIED EVIDENCE] `R4` `R5` `R6` `R8`
5. **成就公式是组织工具，不是必填模板。** `Action + Project/Scope + Result` 和 XYZ 公式有助于发现缺失信息，但没有数字时不能为了套公式造数字。[CONSENSUS PRACTICE] `R7` `R9`
6. **不要用 AI 检测分数评价候选人文案。** 2026 年一项 420 份 IT 简历语料研究显示，两款通用商业检测器在该数据集上的总体准确率分别只有 55.7% 和 25.0%；另一项研究显示检测器对非母语英语写作者存在严重误判风险。[EVIDENCE，限于各自数据集] `R3` `R10`
7. **ATS 友好应通过本系统可验证的属性定义。** 本项目可以可靠检查单页 A4、文本可提取、必需板块、联系方式、占位符和版面边界；不应宣称外部 ATS 的统一“通过率”或神秘评分。[PROJECT DECISION]

## 2. 研究方法与证据等级

本综述交叉检查了四类来源：

- 同行评议论文和论文原文；
- 大学职业中心与职业指导机构的第一方指南；
- 原始开源仓库中的 Prompt、校验器和测试；
- 当前项目的代码、参考文档和测试接口。

证据标签：

| 标签 | 含义 | 使用边界 |
| --- | --- | --- |
| `[EVIDENCE]` | 来源直接研究了所述现象 | 仍需保留样本、领域和因果限制 |
| `[QUALIFIED EVIDENCE]` | 来源支持相邻现象，但不是简历专用或不是因果证明 | 只能转化为保守设计建议 |
| `[CONSENSUS PRACTICE]` | 多个职业指导来源给出一致建议 | 属于实践规范，不等于实验定律 |
| `[HEURISTIC]` | 便于生成或 QA 的工程规则 | 必须允许上下文审查，不应伪装成科学结论 |
| `[PROJECT DECISION]` | 为本项目目标和实现边界作出的选择 | 不外推为行业统一规则 |

## 3. 来源矩阵

| ID | 来源 | 类型 | 直接支持 | 主要限制 |
| --- | --- | --- | --- | --- |
| R1 | Reinhart et al., *Do LLMs write like humans?* | PNAS 2025 | GPT-4o 相对人类文本更常使用分词从句、主语 that 从句、名词化和短语并列 | 通用体裁实验，不是简历实验 |
| R2 | Kobak et al., *Delving into LLM-assisted writing in biomedical publications through excess vocabulary* | arXiv / 研究预印本 | 逾 1500 万篇 PubMed 摘要中的超额词汇变化 | 生物医学摘要，不可直接生成简历禁词表 |
| R3 | Loizidou et al., *Corpus and Baselines for Distinguishing Authentic, AI-Generated, and AI-Enhanced Resumes* | LREC 2026 | 420 份 IT 简历语料；真实、AI 增强、AI 生成文本存在统计差异；通用检测器发生领域失配 | 单一行业语料；结果不能外推到所有简历或检测器 |
| R4 | Pina et al., *Using Machine Learning with Eye-Tracking Data…* | Machine Learning and Knowledge Extraction 2023 | 221 名招聘者查看计算机专业简历；查看时长及 Experience/Education AOI 与结果相关 | 单一地点、入门级 CS 简历、无时间限制；“思考”是作者假设 |
| R5 | Nielsen Norman Group 扫读研究 | Web 眼动研究 | F、layer-cake、spotted 等网页扫描模式；标题、列表、数字和显著词便于定位 | 网页研究，不是简历 PDF 直接实验 |
| R6 | Harvard FAS MCS 简历指南 | 大学职业中心 | 具体、主动、基于事实、简洁、易扫读、按岗位定制、倒序排列 | 主要面向学生和早期职业人群 |
| R7 | Yale OCS “Writing Impactful Resume Bullets” | 大学职业中心 | Action + Project + Result；强调个人贡献、具体结果、能量化时量化 | 示例偏学生经历；量化建议不能凌驾于真实性 |
| R8 | MIT CAPD 简历工具包 | 大学职业中心 | 一至两页、突出相关信息、针对职位删减与排序 | “6–10 秒”是职业指导陈述，不是该页面公布的实验方法 |
| R9 | Laszlo Bock XYZ 公式 | 从业者文章 | “Accomplished [X] as measured by [Y] by doing [Z]” | 个人经验建议，不是同行评议研究 |
| R10 | Liang et al., *GPT detectors are biased against non-native English writers* | PNAS 2023 | 七种检测器对 91 篇 TOEFL 作文平均误报率 61.3% | 研究对象是作文，不是简历 |
| G1 | `santifer/career-ops` | MIT 开源仓库 | 把写作风格与事实准确性分层；事实优先于 voice 规则 | 工程案例，不是独立效果评测 |
| G2 | `ebarti/JobCtrl` | AGPL-3.0 开源仓库 | 对数字、日期、职称、公司和技术词做确定性 grounding；处理技术词同形冲突 | 实现复杂；AGPL 代码不可直接复制进本项目 |
| G3 | `varunr89/resume-tailoring-skill` | MIT 开源仓库 | direct/indirect/adjacent/gap 分支与追问协议 | Prompt 很长，不能整包照搬 |
| G4 | `srbhr/Resume-Matcher` | Apache-2.0 开源仓库 | 明确禁止新增工作经历、指标；包含简历 diff 测试 | 产品架构较重，部分规则依赖其数据模型 |
| G5 | `MadsLorentzen/ai-job-search` | MIT 开源仓库 | “interview backtrack test”；强调重排相关性而不改变事实 | 主要面向其完整求职工作流 |
| G6 | `shaokeyibb/anti-asu-skills` | MIT 开源仓库 | 区分项目领域与个人贡献；核验 scope、metric、ownership claim | 招聘方审计视角，不能直接当生成 Prompt |

## 4. 已核实的研究结论

### 4.1 招聘官阅读：优化“可定位性”，不要迷信秒数

Pina 等人的实验收集了 **221 名招聘者**的眼动数据，参与者查看面向计算机专业毕业生的简历，且没有时间限制。模型中较重要的特征包括总体查看时间、Experience 区域、Education 区域，以及简历内容区域之外的注视。[EVIDENCE] `R4`

需要保留两个限制：

- “看向空白区域代表招聘者在思考”是论文作者的**解释性假设**，不是直接测量到的认知状态；
- 更长查看时间与进入下一阶段相关，不证明增加空白本身会提高通过率。

NN/g 的网页研究表明，扫描模式取决于任务、布局和内容。缺少标题和列表时可能出现 F 型扫描；清晰标题产生 layer-cake 模式，显眼的数字、词或项目符号可产生 spotted 模式。[QUALIFIED EVIDENCE] `R5`

因此，本项目采用以下保守规则：

- `[CONSENSUS PRACTICE]` 用稳定标题、倒序经历和一致日期格式帮助定位；
- `[CONSENSUS PRACTICE]` 将与 JD 最相关的贡献放在每段前面；
- `[HEURISTIC]` Bullet 开头尽快出现“候选人做了什么”和“作用对象”，但不强制“前三个词必须包含技术名词”；
- `[PROJECT DECISION]` 不把 6 秒、7.4 秒或 80% 注视比例写入 Prompt 或验收标准。

### 4.2 “AI 味”：有统计信号，但不能机械反推

Reinhart 等人报告：在其通用体裁实验中，GPT-4o 使用 present participial clauses 的频率为人类文本的 5.3 倍，主语 that 从句为 2.6 倍，名词化为 2.1 倍，短语并列为 1.9 倍。[EVIDENCE] `R1`

这些数字可以支持“检查句末 `, ensuring…` 等低信息附加从句”的设计，但**不能证明任何一个分词从句就是 AI 生成，也不能证明删除所有分词从句会让简历更好**。

Kobak 等人通过逾 1500 万篇生物医学摘要研究 LLM 辅助写作后的超额词汇。[EVIDENCE] `R2` 这支持对 `delve`、`pivotal` 等词保持警觉，但不支持将普通技术词或所有领导力动词永久禁用。

更可靠的去模板化方法是：

1. 删除不增加事实的修饰词；
2. 用具体系统、动作、约束和结果替代抽象评价；
3. 一条 Bullet 只承载一个主要贡献；
4. 检查结果与方法之间是否有真实因果关系；
5. 保持职责强度，不为了“强动词”把 `supported` 改成 `led`；
6. 不为制造变化而轮换不准确的同义词。

### 4.3 AI 检测器不应进入质量门禁

Loizidou 等人的 LREC 2026 论文建立了 420 份 IT 简历语料。在该数据集上，Originality 和 Writer 两款通用检测器的总体准确率分别为 55.7% 和 25.0%。论文同时表明，针对该语料训练的分类器可以取得高得多的结果，因此正确结论是**通用检测器存在领域失配**，而不是“AI 文本永远无法检测”。[EVIDENCE] `R3`

Liang 等人的论文发现，七种检测器对 91 篇非母语英语 TOEFL 作文的平均误报率为 61.3%。该数字不能直接用于简历，但足以说明把检测分数用于候选人质量门禁存在公平性风险。[EVIDENCE，迁移需谨慎] `R10`

项目决策：不接入 AI detector，不以“像不像 AI”的概率作为 PASS/FAIL；只检查可解释的问题，如事实漂移、空洞措辞、重复、因果不清和版面缺陷。

### 4.4 Bullet 结构：公式用于补全思考，不用于补造内容

Harvard 建议语言应具体、主动、基于事实、简洁并适合快速扫描；Yale 给出 `Action + Project + Result`，并强调描述“你”的贡献；Bock 的 XYZ 公式则是：

> Accomplished [X] as measured by [Y] by doing [Z].

这些来源共同支持以下写法：[CONSENSUS PRACTICE] `R6` `R7` `R9`

```text
Action or contribution + specific system/scope + method (if useful) + supported outcome/proof
```

但各部分是可选信息槽，不是语法模板：

- 没有可靠数字：写具体定性变化，或提出澄清问题；
- 方法不重要：省略方法；
- 职责本身就是贡献：可以准确地用 `Supported`、`Maintained`、`Monitored`；
- 同一成果不要在主句和尾句重复表达。

### 4.5 ATS：只承诺可验证属性

没有公开证据支持“所有 ATS 都使用相同布尔算法”“单栏有固定解析成功率”或“某种破折号会导致 Workday 崩溃”。这些说法不应进入项目文档。

本项目可验证并应持续保证：

- PDF 为单页 A4（项目默认目标）；
- 存在可提取文本层；
- 姓名、联系方式、主要板块和关键词可以从生成 PDF 中检索；
- 无占位符、HTML 泄漏、裁切或重叠；
- 阅读顺序和视觉层级经人工渲染检查。

`%` 在 LaTeX 源码中需要转义是 LaTeX 语法事实，但当前项目使用 ReportLab；因此它不是本项目的 ATS 规则，也不应进入当前实现计划。[PROJECT DECISION]

## 5. 开源 Prompt 与实现模式

### 5.1 值得吸收

1. **Prompt 后再做确定性核验。** `JobCtrl` 明确指出模型可能忽略“不许编造”的指令，因此对数字、日期、职称、公司和已命名技术进行后置 grounding。 `G2`
2. **把风格与事实分层。** `career-ops` 的写作规则明确规定 accuracy 优先于 voice，写作样本不能成为新事实来源。 `G1`
3. **信息缺失走分支追问。** `resume-tailoring-skill` 区分 direct、indirect、adjacent、personal-learning 和 no-experience，再决定深挖或记录 gap。 `G3`
4. **针对性修改并展示 diff。** `Resume-Matcher` 的测试覆盖原文与改写后的结构化差异；这比不可追踪的全篇重写更便于审核。 `G4`
5. **使用面试可辩护性测试。** 如果候选人需要在面试中说“我其实不是这个意思”，改写就越界了。 `G5`
6. **拆开 scope、metric 和 ownership。** 团队项目规模不等于候选人的个人贡献规模。 `G6`

### 5.2 不照搬

- 不复制 AGPL-3.0 仓库代码；只借鉴经过独立实现的设计思想；
- 不采用超长禁词表作为主规则；
- 不把所有 Bullet 强制变成同一公式；
- 不采用 `[verify: ~20%]` 一类估算占位符进入最终简历；
- 不把“ATS match score”当作外部招聘系统真实排名；
- 不让 LLM 自己证明自己的输出没有幻觉。

## 6. 可复用 Prompt 规范

该规范应作为 Agent 内部写作合同，而不是用户入口 Prompt。

### 6.1 输入

```text
BASE_PROFILE: 候选人已经确认的事实来源
TARGET_JD: 目标职位描述，可为空
JD_ANALYSIS: P1/P2/P3、matched/transferable/gap
LAYOUT_BUDGET: 单页目标、当前字数和版面警告
```

### 6.2 硬性不变量

```text
1. Do not add or alter employers, titles, dates, degrees, tools, responsibilities, or metrics without candidate evidence.
2. Do not estimate missing numbers. Ask a clarification question, use a precise qualitative outcome, or leave the item as a gap.
3. Preserve responsibility level. Supported/assisted/contributed must not become led/owned/architected.
4. Do not treat the JD as evidence that the candidate used a technology.
5. Preserve the original meaning of untouched content.
6. Every material rewrite must be traceable to a source bullet or an explicit candidate clarification.
```

### 6.3 决策顺序

1. **提取事实：** 标记不可变实体、候选人动作、系统范围、方法、结果和指标。
2. **分析 JD：** 将要求分为 `matched`、`transferable`、`gap`；gap 不进入简历事实。
3. **选择内容：** 先按相关性和证据强度排序，再删除重复和低价值内容。
4. **改写：** 只修改需要改善的 Bullet；先保留事实，再改善顺序和密度。
5. **生成 diff：** 对每项改写记录来源、动作和理由。
6. **自检：** 对照事实、职责边界、因果、重复和版面预算。

### 6.4 Bullet 规则

```text
- Lead with the candidate's actual contribution when natural.
- Name a specific system, feature, process, dataset, or user group.
- Add method/tool only if evidenced and useful to the target role.
- State one supported outcome or proof point; do not repeat it in a trailing clause.
- Omit any missing component instead of fabricating it.
- Prefer one primary idea per bullet.
- Keep wording compact, but judge final line length after rendering rather than by character count alone.
```

### 6.5 去模板化规则

```text
- Remove adjectives/adverbs that add no verifiable information.
- Flag, rather than automatically ban, trailing “, ensuring/driving/enabling…” clauses; rewrite when they merely restate impact or imply unsupported causality.
- Replace noun-heavy phrases with accurate verbs when meaning is preserved.
- Do not cycle through inflated synonyms to avoid repetition.
- Allow ordinary words such as “led”, “supported”, or “leveraged” when they are the most accurate description.
- Do not explain what common technologies are; describe what the candidate did with them.
```

### 6.6 输出合同

```json
{
  "resume": "complete resume-working payload",
  "changes": [
    {
      "path": "experience[0].bullets[1]",
      "source": "original bullet text",
      "replacement": "rewritten bullet text",
      "reason": ["lead_with_relevant_work", "remove_repetition"],
      "evidence": ["base_profile:experience[0].bullets[1]"]
    }
  ],
  "clarifications": [],
  "gaps": []
}
```

## 7. Few-shot 示例

示例中的改写只能复用原文已有事实。

### 示例 A：有可靠指标

```text
Raw:
Updated PostgreSQL queries and added Redis caching. API p95 went from 420 ms to 110 ms.

Good:
Optimized PostgreSQL queries and cached hot API responses in Redis, reducing p95 latency from 420 ms to 110 ms.
```

### 示例 B：没有数字

```text
Raw:
Moved the billing service without downtime. I helped plan the cutover and monitored it.

Bad:
Led a zero-downtime billing migration that improved reliability by 35%.

Good:
Supported the billing-service cutover plan and monitored production during a migration completed without downtime.
```

### 示例 C：JD 中出现候选人未使用的工具

```text
Base profile: RabbitMQ
JD: Kafka

Bad:
Built Kafka event pipelines for order processing.

Good handling:
Keep RabbitMQ in the resume; classify Kafka as a gap. Do not substitute one tool for the other.
```

### 示例 D：删除空洞尾句

```text
Before:
Built an internal deployment dashboard, enabling seamless collaboration and driving operational excellence.

After, when no further evidence exists:
Built an internal deployment dashboard for release status and rollback visibility.
```

## 8. QA 规则分层

### ERROR：必须阻断

- 新增或改变未经证实的公司、职位、日期、学历、工具、责任或指标；
- 工作 JSON 含未解决占位符；
- PDF 不是项目要求的单页 A4，或没有可提取文本；
- 必需板块、联系方式缺失；
- 出现裁切、重叠或不可读字形。

### WARN：需要上下文复核

- 模糊结果：`significantly improved`、`drove success`；
- 句末分词从句重复结果或制造未经证实的因果；
- 同一 Bullet 承载多个无关贡献；
- 重复开头、重复三元短语、过多抽象名词；
- Bullet 超出当前 28 词审阅目标；
- 经验 Bullet 数量与候选人阶段不匹配。

### INFO：不应制造改写压力

- 量化 Bullet 的实际占比；
- 同一动词的出现次数；
- 可能需要候选人补充的规模或结果问题。

### 人工终审

- 候选人是否能在面试中逐句解释；
- 是否准确表达了个人而非团队的贡献；
- 相关信息是否容易定位；
- 最新渲染是否视觉平衡。

## 9. 明确拒绝的说法

以下说法缺少足够证据或被过度外推，不进入项目规则：

- “招聘官只看 6 秒/7.4 秒，因此前 3 个词决定成败”；
- “F 型扫描证明简历右半边 80% 一定无人阅读”；
- “单栏 ATS 解析率是 93%，双栏是 67%–86%”；
- “en-dash 会导致 Workday 日期解析崩溃”；
- “所有 ATS 的核心都是同一套布尔关键词淘汰算法”；
- “某些单词出现就能证明简历由 AI 生成”；
- “每条 Bullet 都必须有数字”；
- “可以先填估算数字，再让候选人确认”；
- “达到 100 分 ATS 分数即可保证进入面试”。

## 10. 参考资料

### 论文与原始研究

- `R1` Reinhart et al. (2025), [Do LLMs write like humans? Variation in grammatical and rhetorical styles](https://doi.org/10.1073/pnas.2422455122).
- `R2` Kobak et al. (2024/2025), [Delving into LLM-assisted writing in biomedical publications through excess vocabulary](https://arxiv.org/abs/2406.07016).
- `R3` Loizidou et al. (2026), [Corpus and Baselines for Distinguishing Authentic, AI-Generated, and AI-Enhanced Resumes](https://users.cs.fiu.edu/~markaf/doc/c18.loizidou.2026.proclrec.v15.p7331_archival.pdf).
- `R4` Pina et al. (2023), [Using Machine Learning with Eye-Tracking Data to Predict if a Recruiter Will Approve a Resume](https://doi.org/10.3390/make5030038).
- `R5` Nielsen Norman Group, [F-Shaped Pattern of Reading](https://www.nngroup.com/articles/f-shaped-pattern-reading-web-content/) and [Text Scanning Patterns](https://www.nngroup.com/articles/text-scanning-patterns-eyetracking/).
- `R10` Liang et al. (2023), [GPT detectors are biased against non-native English writers](https://doi.org/10.1073/pnas.2302083120).

### 职业指导

- `R6` Harvard FAS MCS, [Create a Strong Resume](https://careerservices.fas.harvard.edu/resources/create-a-strong-resume/).
- `R7` Yale OCS, [Writing Impactful Resume Bullets](https://ocs.yale.edu/resources/writing-impactful-resume-bullets/).
- `R8` MIT CAPD, [Career toolkit: Crafting an effective resume](https://capd.mit.edu/resources/career-toolkit-crafting-an-effective-resume/).
- `R9` Laszlo Bock, [My personal formula for a better resume](https://qz.com/273818/how-to-write-a-resume-that-gets-you-hired-at-google).

### 开源实现（固定到复核时提交）

- `G1` [`santifer/career-ops` writing guardrail](https://github.com/santifer/career-ops/blob/8af93cd4c297e6153dfbb6f056833f45d58e8726/modes/_writing.md)（MIT）。
- `G2` [`ebarti/JobCtrl` fabrication detector](https://github.com/ebarti/JobCtrl/blob/e2e56f3554f872d65d50ed82c708782712b1b83f/workers/automation/src/jobctrl/domain/materials/fabrication_detector.py)（AGPL-3.0，仅参考设计）。
- `G3` [`varunr89/resume-tailoring-skill` branching questions](https://github.com/varunr89/resume-tailoring-skill/blob/9a4a0f20f5983d1b533627b8c5191acd1ca0cd89/branching-questions.md)（MIT）。
- `G4` [`srbhr/Resume-Matcher` refinement prompt](https://github.com/srbhr/Resume-Matcher/blob/116f9cc3b00e1ac91734a6c2679bf41ea64a0edc/apps/backend/app/prompts/refinement.py)（Apache-2.0）。
- `G5` [`MadsLorentzen/ai-job-search` writing style](https://github.com/MadsLorentzen/ai-job-search/blob/79cd383e58f0af7948c7c6462a3a289e9b67421e/.claude/skills/job-application-assistant/03-writing-style.md)（MIT）。
- `G6` [`shaokeyibb/anti-asu-skills` resume audit](https://github.com/shaokeyibb/anti-asu-skills/blob/e663ea71bf9cf6b2c20441407c39184fbf361dfd/skills/resume-audit/SKILL.md)（MIT）。
