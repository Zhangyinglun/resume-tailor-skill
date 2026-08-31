# 简历深度定制与事实证据账本系统重构方案 (Comprehensive Architecture Plan)

> **版本**：v2.0 (Full Replacement)  
> **状态**：Approved Design Specification  
> **依据**：`CONTEXT.md`、ADR-0001 ~ ADR-0004 及 Grilling 确认结果；招聘研究证据见 `docs/research/recruiter-friendly-resume-writing.md`

---

## 1. 核心目标与产品愿景

构建以**“长期事实沉淀（Evidence Ledger）”**为核心、以**“JD 驱动靶向追问”**为飞轮、以**“确定性事实审计与真实几何 QA”**为底线的高性能简历定制系统。

### 核心演进逻辑

```
[ 用户原始简历 / 文本 ]
         │
         ▼
[ Source Snapshot: base-resume.json ] (不可变快照)
         │
         ▼ (初始化抽取)
[ Candidate Evidence Ledger: candidate-evidence.json ] ◄──┐ (长期事实积累)
[ Candidate Profile: candidate-profile.json ]             │
         │                                               │
         ▼                                               │ (静默解析入账)
[ Target JD ] ──► [ 靶向分析 & 3-5 个高价值追问 ] ────────┘ (跨 JD 智能复用)
         │
         ▼
[ Tailored Resume: resume-working.json ] (纯净展示投影)
[ Tailoring Manifest: resume-changes.json ] (全字段溯源清单)
         │
         ▼ (强制门禁阻断)
[ 事实审计 + 内容 QA + pdfplumber 真实几何 QA ]
         │
         ▼ (发布)
[ Single-Page A4 Accepted PDF + 结构化质量报告 ]
```

---

## 2. 领域数据契约与存储架构 (Data Contracts)

严格遵循 `1 USER_WORKSPACE = 1 Candidate`。Skill 仓库本身保持无状态，所有个人数据均在 `USER_WORKSPACE` 隔离。

### 2.1 `base-resume.json` (Source Snapshot)

原始简历的结构化不可变快照。包含解析出的原始字段及源文本的 SHA-256 哈希指纹。更新 base resume 时触发增量同步而非直接覆盖。

### 2.2 `candidate-evidence.json` (Candidate Evidence Ledger)

候选人的长期事实账本，以 `entities`（公司经历、项目、教育、技能簇）为锚点组织 `atomic_claims`：

```json
{
  "candidate_id": "c-default",
  "version": 1,
  "updated_at": "2025-02-18T10:00:00Z",
  "entities": [
    {
      "entity_id": "ent_exp_01",
      "type": "experience",
      "organization": "Acme Corp",
      "role": "Senior Backend Engineer",
      "date_range": "2022.03 - Present",
      "claims": [
        {
          "claim_id": "clm_001",
          "claim_type": "metric",
          "text": "通过引入二级缓存和连接池优化，将核心服务 P99 延迟从 120ms 降低至 35ms",
          "state": "sourced",
          "provenance": { "source": "base_resume", "original_excerpt": "optimized latency to 35ms" },
          "metrics": [{ "value": "35ms", "baseline": "120ms", "metric_type": "latency" }],
          "tools": ["Redis", "Go"],
          "role_level": "implemented",
          "confirmed_at": "2025-02-18T10:00:00Z",
          "supersedes": null,
          "revoked": false
        }
      ]
    }
  ]
}
```

### 2.3 `candidate-profile.json` (Candidate Profile)

全局偏好与画像，跨 JD 共享：

```json
{
  "target_direction": "Senior Distributed Systems / LLM Infrastructure",
  "tech_bias": ["Go", "Kubernetes", "Distributed Storage", "PyTorch"],
  "naming_preferences": {
    "proj_rag": "Enterprise Document Cognitive Engine"
  },
  "presentation_defaults": {
    "summary_tone": "senior_technical_lead",
    "exclude_sensitive": ["age", "marital_status", "photo"]
  }
}
```

### 2.4 `resume-working.json` (Tailored Resume Projection)

针对具体 JD 的纯净展示结构，**完全剥离内部 ID**，专注于排版与渲染。

### 2.5 `resume-changes.json` (Tailoring Manifest)

记录本次投影中针对各字段的所有实质改写与 Claim 绑定：

```json
{
  "target_jd_hash": "sha256_...",
  "generated_at": "2025-02-18T10:15:00Z",
  "substantive_changes": [
    {
      "projection_path": "experience[0].bullets[0]",
      "operation": "EMPHASIZE",
      "rendered_text": "使用 Redis 实现二级缓存，将核心接口 P99 延迟从 120ms 降至 35ms",
      "entity_id": "ent_exp_01",
      "source_claim_ids": ["clm_001"],
      "match_type": "direct",
      "semantic_normalizations": [],
      "reason": "针对 JD P1 性能调优要求，突出同一经历中已有的缓存实现与延迟指标"
    }
  ]
}
```

---

## 3. 靶向追问、静默入账与跨 JD 智能复用协议

### 3.1 提问预算与触发逻辑 (Clarification Protocol)

1. **P1/P2 靶向触发**：仅当当前 JD 要求的核心能力属于 `needs_confirmation`（缺少关键量化或架构细节）或 `transferable`（有底层技术背景但需确认在具体项目中的落地形态）时触发。
2. **预算控制**：单次交互严格控制在 **3–5 个最高杠杆问题**。
3. **问题结构**：
   - 明确指向具体 Entity（如“在项目 A 中……”）；
   - 聚焦高价值要素（具体使用工具、性能指标/吞吐规模、实际承担职责等级）。

### 3.2 静默入账机制 (Silent Ingestion)

- Agent 接收用户的对话回答后，自动将其提炼为符合 Schema 的 `Atomic Claim`，并写入 `candidate-evidence.json`（标记 `state: "candidate_confirmed"`，记录用户原话摘要与时间戳）。
- 同时提取出全局偏好写入 `candidate-profile.json`。
- 无需额外的二次确认交互，直接进入定制改写。

### 3.3 跨 JD 语义自动复用 (Auto-Reuse)

- **直接复用（免问）**：当后续新 JD 涉及与 Ledger 中已有 Claim 严格同义、概念包含或已确认的技术时（如“知识库检索”与“RAG”、“vLLM 推理部署”与“大模型服务化”），直接调用已有 Claim，不再重复追问。
- **保护边界**：若涉及新工具替换、新业务指标或职责升级（如 Assisted → Owned），必须重新确认，严防私自推定。

---

## 4. 事实审计与质量门禁体系 (Factual Audit & QA Gates)

在 `generate_final_resume.py` 中建立强制性的多重验证门禁：

```
[ resume-working.json + resume-changes.json + candidate-evidence.json ]
                              │
                              ▼
┌────────────────────────────────────────────────────────────┐
│ Step 1: 机械事实审计 (audit_factual_integrity.py)          │
│ - 全量字段溯源覆盖校验 (Traceability Check)               │
│ - 零指标幻觉检查 (Zero Metric Fabrication Check)           │
│ - 技术栈漂移检查 (Tool Drift Check)                        │
│ - 职责级别夸大检查 (Role Inflation Check)                  │
└─────────────────────────────┬──────────────────────────────┘
                              │ Exit 0 (Pass) / Exit 1 (Block)
                              ▼
┌────────────────────────────────────────────────────────────┐
│ Step 2: 文风与动作质检 (check_content_quality.py 重构版)    │
│ - 统一强动作动词词典校验 (Unified Action Verb Lexicon)     │
│ - 移除硬性数字要求与 40-60% 僵化指标比例                   │
│ - 自适应 Bullet 密度与结构校验                             │
└─────────────────────────────┬──────────────────────────────┘
                              │ Exit 0 (Pass) / Exit 2 (Advisory Warn)
                              ▼
┌────────────────────────────────────────────────────────────┐
│ Step 3: PDF 编译与真实几何检查 (check_pdf_geometry.py)      │
│ - pdfplumber 真实 Bounding Box / 坐标分析                  │
│ - 末行孤字/寡词 (Widow/Orphan Words) 排版瑕疵检测          │
│ - 单页 A4 绝对溢出与页面边界安全裕度检测                   │
└─────────────────────────────┬──────────────────────────────┘
                              │ Exit 0 (Success)
                              ▼
           [ 归档旧版 -> 发布新版 Accepted PDF ]
```

---

## 5. Prompt Recipes 流水线重构 (5-Step Pipeline)

1. **Recipe 1: Cold Start & Evidence Ledger Init**
   - 提取原始文本 → 生成不可变 `base-resume.json` → 抽取原子 Claim 初始化 `candidate-evidence.json` + `candidate-profile.json`。
2. **Recipe 2: JD Capability Analysis & Targeted Inquiries**
   - 结构化分析 JD 能力（P1/P2/P3）→ 比对 Ledger → 如有高价值缺失，输出 3–5 个靶向问题；无缺失则直接进入 Recipe 4。
3. **Recipe 3: Silent Conversational Fact Ingestion**
   - 解析用户回答 → 结构化为 Atomic Claims / Profile Defaults → 静默入账。
4. **Recipe 4: Tailored Projection & Manifest Generation**
   - 结合目标 JD 与有效证据 → 生成纯净 `resume-working.json` 和全字段溯源 `resume-changes.json`。
5. **Recipe 5: Multi-Gate Verification & Publication**
   - 运行事实审计、文风 QA 与 PDF 真实几何排版 QA → 自动归档并输出详细质量报告。

---

## 6. 实施路线图 (Implementation Phases)

### 阶段 1：领域模型、契约与文档 (`CONTEXT.md`, `ADR`, `references/`)

- [x] 创建 `CONTEXT.md`
- [x] 创建 `docs/adr/0001` ~ `0004`
- [x] 更新 `references/resume-working-schema.md`、`references/prompt-recipes.md`、`references/ats-keywords-strategy.md`、`references/execution-checklist.md`

### 阶段 2：账本管理与事实审计模块 (`scripts/`)

- [x] 编写 `scripts/evidence_ledger_manager.py`（初始化、增量同步、静默入账接口）
- [x] 编写 `scripts/audit_factual_integrity.py`（四大确定性事实审计规则）
- [x] 编写配套单元测试：`tests/test_evidence_ledger.py`、`tests/test_factual_audit.py`

### 阶段 3：内容 QA 与 PDF 真实几何检查重构

- [x] 重构 `scripts/resume_shared.py` 与 `scripts/check_content_quality.py`（统一动词库，移除强制数字压力）
- [x] 基于 `pdfplumber` 编写 `scripts/check_pdf_geometry.py`（坐标级断行与孤字检测）
- [x] 更新 `tests/test_content_quality.py` 与 `tests/test_pdf_geometry.py`

### 阶段 4：生成器集成与发布报告升级

- [x] 重构 `scripts/generate_final_resume.py`（接入事实审计前置阻塞门禁与几何 QA）
- [x] 升级 `scripts/generate_quality_report.py`（输出 Evidence 覆盖度、Gap 提示与排版评分）
- [x] 完善 Skill 交互规范 `SKILL.md` 与 `AGENTS.md`
