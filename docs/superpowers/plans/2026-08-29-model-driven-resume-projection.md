# 模型驱动简历投影与自然语言优化 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立模型驱动的 Projection Plan、逐项可审计的动态 Skills、Resume Language Optimizer 契约和真实 PDF Content Fit 反馈，使同一 Candidate Evidence Ledger 能针对不同 JD 自动生成自然、可信的单页 A4 简历。

**Architecture:** 宿主模型通过 `projection-plan.json` 决定写什么，通过 `projection-language.json` 决定怎么写；新的 Projection Plan Manager 负责确定性验证、Tailored Resume 与 Tailoring Manifest 原子生成。事实审计、内容 QA、真实 PDF geometry 和 layout-only auto-fit 继续作为发布闸门，Python 包不调用模型 API。

**Tech Stack:** Python 3、标准库 `dataclasses/json/pathlib/re/typing`、ReportLab、pdfplumber、`unittest`、现有 Evidence Ledger / Manifest / PDF QA 模块。

**Spec:** `docs/superpowers/specs/2026-08-29-model-driven-projection-and-language-optimization-design.zh-CN.md`

## Global Constraints

- `1 USER_WORKSPACE = 1 Candidate`，所有个性化缓存和 PDF 必须位于 Skill 包外部。
- 仓库测试只能使用合成候选人数据；不得提交 Yinglun Zhang 或其他真实候选人的缓存、联系方式或 PDF。
- Projection Planner 和 Resume Language Optimizer 由宿主模型执行；随包 Python 不增加模型 SDK、API Key、供应商 Adapter 或网络调用。
- 每段正式工作经历必须保留，并包含 1–5 条 bullet。
- Skills 必须包含 2–4 个 Skill Presentation Group，并在优选布局下渲染为 2–4 行正文。
- 每个 Skill item 必须独立绑定 active `sourced` 或 `candidate_confirmed` claim。
- Clarification 最多 5 个；Content Fit 最多修订 3 次。
- `--auto-fit` 只能修改字体、行距、间距和安全范围内的 margin，不得修改内容。
- 语言优化不得改变工具、指标、scope、ownership、environment、production state 或 completion state。
- 所有 changed function 添加类型注解；CLI 入口保持 `main() -> int`。
- 使用 `pathlib.Path` 和 UTF-8 I/O；不得加入不必要依赖。
- 测试框架使用仓库现有 `unittest`，命令使用 `python3 -m unittest`。

---

### Task 1: Skills item-level display schema 与向后兼容渲染

**Files:**

- Modify: `scripts/resume_shared.py:104-198,284-322`
- Modify: `templates/modern_resume_template.py:300-330`
- Modify: `tests/test_resume_shared.py`
- Modify: `tests/test_pdf_pipeline.py`

**Interfaces:**

- Produces: `normalize_skill_items(value: Any) -> list[str]`
- Produces: `iter_resume_text_fields()` 对数组 Skills 输出 `skills[i].items[j]`，对旧字符串继续输出 `skills[i].items`
- Consumes: existing `validate_resume_content()`, `generate_resume()`

- [ ] **Step 1: 为数组 Skills 写失败测试**

在 `tests/test_resume_shared.py` 增加：

```python
from scripts.resume_shared import (
    iter_resume_text_fields,
    normalize_skill_items,
    validate_resume_content,
)


def test_normalize_skill_items_accepts_list_and_legacy_string() -> None:
    assert normalize_skill_items(["Azure OpenAI", "MCP", "RAG"]) == [
        "Azure OpenAI",
        "MCP",
        "RAG",
    ]
    assert normalize_skill_items("Azure OpenAI, MCP, RAG") == [
        "Azure OpenAI",
        "MCP",
        "RAG",
    ]


def test_iter_resume_text_fields_emits_item_level_skill_paths() -> None:
    resume = sample_resume()
    resume["skills"] = [
        {
            "category": "AI Platforms & Tooling",
            "items": ["Azure OpenAI", "MCP", "RAG"],
        }
    ]
    validate_resume_content(resume, require_non_empty=True)

    fields = {path: text for path, text, _, _ in iter_resume_text_fields(resume)}

    assert fields["skills[0].category"] == "AI Platforms & Tooling"
    assert fields["skills[0].items[0]"] == "Azure OpenAI"
    assert fields["skills[0].items[1]"] == "MCP"
    assert fields["skills[0].items[2]"] == "RAG"
    assert "skills[0].items" not in fields


def test_iter_resume_text_fields_preserves_legacy_skill_path() -> None:
    resume = sample_resume()
    resume["skills"] = [{"category": "Languages", "items": "Python, Go"}]

    fields = {path: text for path, text, _, _ in iter_resume_text_fields(resume)}

    assert fields["skills[0].items"] == "Python, Go"
```

将这些函数放入现有 `ResumeSharedTests(unittest.TestCase)` 时，改写成 `self.assertEqual` / `self.assertIn` 风格，保持仓库一致性。

- [ ] **Step 2: 运行测试并确认失败**

Run:

```bash
python3 -m unittest tests.test_resume_shared -v
```

Expected: FAIL，原因包含 `cannot import name 'normalize_skill_items'` 或 list 类型不被接受。

- [ ] **Step 3: 实现 Skills 规范化和字段遍历**

在 `scripts/resume_shared.py` 增加：

```python
def normalize_skill_items(value: Any) -> list[str]:
    """Return non-empty Skill display terms from list or legacy comma text."""
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, list):
        items: list[str] = []
        for index, item in enumerate(value):
            if not isinstance(item, str) or not item.strip():
                raise ValueError(f"Skill item at index {index} must be a non-empty string.")
            items.append(item.strip())
        return items
    raise ValueError("Skill items must be a comma-delimited string or an array of strings.")
```

修改 `validate_resume_content()`：Skills 的 `items` 接受 string 或 string array，并调用 `normalize_skill_items()`；空数组失败。

修改 `iter_resume_text_fields()`：

```python
if section == "skills" and field == "items" and isinstance(value, list):
    for item_index, item in enumerate(normalize_skill_items(value)):
        yield f"{entity_key}.items[{item_index}]", item, "skill", entity_key
    continue
```

旧字符串保持现有 `skills[i].items` 路径，避免旧 workspace 的 Manifest 立即失效。

- [ ] **Step 4: 让 ReportLab Renderer 兼容数组**

在 `templates/modern_resume_template.py` Skills 渲染处调用：

```python
from scripts.resume_shared import normalize_skill_items

items = ", ".join(normalize_skill_items(skill.get("items", [])))
story.append(
    Paragraph(
        f"<b>{_safe_text(skill.get('category', ''))}:</b> {_safe_text(items)}",
        styles["Body"],
    )
)
```

保持当前 `styles["Body"]` 和既有 design token 不变，只替换 `items` 文本生成方式。

- [ ] **Step 5: 增加 PDF 文本层回归测试**

在 `tests/test_pdf_pipeline.py` 复制现有最小 resume fixture，将 Skills 改为数组，生成 PDF 后使用 `pdfplumber` 断言：

```python
resume["skills"] = [
    {
        "category": "AI Platforms & Tooling",
        "items": ["Azure OpenAI", "MCP", "RAG"],
    }
]
rendered_path = Path(generate_resume("skills-array.pdf", resume, base_dir=temp_dir))
with pdfplumber.open(rendered_path) as pdf:
    text = "\n".join(page.extract_text() or "" for page in pdf.pages)
self.assertIn("AI Platforms & Tooling", text)
self.assertIn("Azure OpenAI, MCP, RAG", text)
```

- [ ] **Step 6: 运行相关测试**

Run:

```bash
python3 -m unittest tests.test_resume_shared tests.test_pdf_pipeline -v
```

Expected: PASS。

- [ ] **Step 7: 提交 Task 1**

```bash
git add scripts/resume_shared.py templates/modern_resume_template.py tests/test_resume_shared.py tests/test_pdf_pipeline.py
git commit -m "feat: support itemized skill display terms"
```

---

### Task 2: Skills presentation binding 与逐项事实审计

**Files:**

- Modify: `scripts/audit_factual_integrity.py:209-449`
- Modify: `scripts/evidence_ledger_manager.py:376-486`
- Modify: `tests/test_factual_audit.py`
- Modify: `tests/test_evidence_ledger.py`

**Interfaces:**

- Consumes: Task 1 `normalize_skill_items()` 与 item-level `iter_resume_text_fields()`
- Produces: Manifest `binding_mode`，默认 `single_entity`；仅 `skills[i].category` 可用 `presentation`
- Produces: presentation entry 的 `grouped_item_paths: list[str]`

- [ ] **Step 1: 写跨实体动态 Skills 的失败审计测试**

在 `tests/test_factual_audit.py` 增加合成 Ledger：一个 Azure OpenAI claim 绑定 Experience Entity，一个 RAG claim 绑定 Skill Entity。构建：

```python
resume["skills"] = [
    {
        "category": "AI Platforms & Tooling",
        "items": ["Azure OpenAI", "RAG"],
    }
]
manifest["entries"] = [
    {
        "projection_path": "skills[0].category",
        "operation": "REWORD",
        "rendered_text": "AI Platforms & Tooling",
        "binding_mode": "presentation",
        "entity_id": None,
        "source_claim_ids": [],
        "grouped_item_paths": ["skills[0].items[0]", "skills[0].items[1]"],
        "match_type": "direct",
        "semantic_normalizations": [],
        "reason": "Groups selected AI platform evidence for display.",
    },
    {
        "projection_path": "skills[0].items[0]",
        "operation": "LEAD_WITH",
        "rendered_text": "Azure OpenAI",
        "binding_mode": "single_entity",
        "entity_id": experience_entity_id,
        "source_claim_ids": [azure_claim_id],
        "match_type": "direct",
        "semantic_normalizations": [],
        "reason": "Direct target capability.",
    },
    {
        "projection_path": "skills[0].items[1]",
        "operation": "KEEP",
        "rendered_text": "RAG",
        "binding_mode": "single_entity",
        "entity_id": skill_entity_id,
        "source_claim_ids": [rag_claim_id],
        "match_type": "direct",
        "semantic_normalizations": [],
        "reason": "Used by selected experience evidence.",
    },
]
```

为 name、contact、summary、experience、education 继续使用测试 helper 生成正常 Manifest entry，然后执行完整审计：

```python
report = audit_resume(resume, manifest, ledger, base_resume=base_resume)
self.assertEqual(report["verdict"], "PASS")
```

再增加两个失败测试：

```python
category_entry["projection_path"] = "summary"
report = audit_resume(resume, manifest, ledger, base_resume=base_resume)
self.assertIn(
    "INVALID_PRESENTATION_BINDING",
    {finding["code"] for finding in report["findings"]},
)
```

以及 category 写成 `OAuth & AI Platforms`、组内没有 OAuth claim，断言 `UNSUPPORTED_PRESENTATION_TERM`。

- [ ] **Step 2: 运行测试并确认失败**

```bash
python3 -m unittest tests.test_factual_audit -v
```

Expected: FAIL，现有审计会报告 `MISSING_ENTITY_BINDING`、`PATH_ENTITY_MISMATCH` 或 `UNSUPPORTED_FIELD`。

- [ ] **Step 3: 实现审计 binding mode**

在 `scripts/audit_factual_integrity.py` 增加：

```python
_SKILL_CATEGORY_PATH_RE = re.compile(r"^skills\[(\d+)\]\.category$")
_SKILL_ITEM_PATH_RE = re.compile(r"^skills\[(\d+)\]\.items\[(\d+)\]$")


def _binding_mode(entry: dict[str, Any]) -> str:
    mode = str(entry.get("binding_mode", "single_entity"))
    if mode not in {"single_entity", "presentation"}:
        return "invalid"
    return mode
```

在逐字段审计时：

1. `presentation` 只允许 `_SKILL_CATEGORY_PATH_RE`；
2. 必须有非空 `grouped_item_paths`；
3. 每个 grouped path 必须属于同一个 Skills group，且存在 Manifest item entry；
4. category 不要求 `entity_id` 或 claim IDs；
5. 聚合 item entry 的 claims/tools 后，使用现有 `_mentioned_terms()` 验证 category 技术词；
6. item path 使用 entry 声明的 Evidence Entity，不再根据动态 category 计算 skill entity ID；
7. 其他字段继续执行现有 expected entity 严格检查。

将 presentation 特殊处理封装为：

```python
def _audit_skill_presentation_entry(
    path: str,
    text: str,
    entry: dict[str, Any],
    by_path: dict[str, dict[str, Any]],
    claim_index: dict[str, tuple[dict[str, Any], dict[str, Any]]],
) -> list[dict[str, str]]:
    """Validate a dynamic Skills category against its item bindings."""
```

- [ ] **Step 4: 更新 Manifest rebuild**

在 `rebuild_tailoring_manifest()` 中：

- 数组 Skill item 继续按 exact active claim 匹配并生成 `single_entity` entry；
- 数组 Skill category 生成 `presentation` entry；
- `grouped_item_paths` 来自同一 index 下已生成的 item paths；
- 旧字符串 Skills 保持当前单实体逻辑。

Presentation entry 模板：

```python
{
    "projection_path": path,
    "operation": "REWORD",
    "rendered_text": text,
    "binding_mode": "presentation",
    "entity_id": None,
    "source_claim_ids": [],
    "grouped_item_paths": item_paths,
    "match_type": "direct",
    "semantic_normalizations": [],
    "reason": "Target-specific Skill Presentation Group label.",
}
```

- [ ] **Step 5: 增加 Manifest rebuild 回归测试**

在 `tests/test_evidence_ledger.py`：

1. 初始化 synthetic resume；
2. 将工作投影 Skills 改为 item array；
3. 确保每个 item 文本与某个 active claim 精确一致；
4. 调用 `rebuild_tailoring_manifest()`；
5. 断言 category 为 presentation binding；
6. 断言 item entries 分别绑定其 claim；
7. 断言 `unresolved_paths == []`。

- [ ] **Step 6: 运行事实和 Ledger 测试**

```bash
python3 -m unittest tests.test_factual_audit tests.test_evidence_ledger -v
```

Expected: PASS。

- [ ] **Step 7: 提交 Task 2**

```bash
git add scripts/audit_factual_integrity.py scripts/evidence_ledger_manager.py tests/test_factual_audit.py tests/test_evidence_ledger.py
git commit -m "feat: audit dynamic skill item bindings"
```

---

### Task 3: Projection Plan schema 与证据链接验证

**Files:**

- Create: `scripts/projection_plan_manager.py`
- Create: `tests/test_projection_plan_manager.py`

**Interfaces:**

- Produces: `BuildResult`
- Produces: `validate_projection_plan(workspace: Path, plan: dict[str, Any]) -> dict[str, Any]`
- Task 4 extends the module with `validate_language_output(plan: dict[str, Any], language: dict[str, Any], ledger: dict[str, Any]) -> dict[str, dict[str, Any]]`
- Task 4 extends the module with `build_projection(workspace: Path, plan_path: Path, language_path: Path) -> BuildResult`
- Consumes: `load_json_file`, `canonical_json_fingerprint`, `stable_identifier`, `validate_jd_analysis`

- [ ] **Step 1: 建立 synthetic workspace test helper**

在 `tests/test_projection_plan_manager.py` 使用 `tempfile.TemporaryDirectory()`，调用 `initialize_workspace()` 创建 Source Snapshot 和 Ledger，再写入 synthetic JD：

```python
def sample_jd() -> dict[str, Any]:
    return {
        "position": "Applied AI Engineer",
        "keywords": {"P1": ["MCP"], "P2": ["RAG"], "P3": []},
        "capabilities": [
            {
                "capability_id": "cap-mcp",
                "priority": "P1",
                "name": "MCP tool integration",
                "match_type": "direct",
                "evidence_state": "sourced",
                "claim_ids": [],
            }
        ],
        "alignment": {"matched": [], "transferable": [], "gaps": []},
    }
```

初始化后从 Ledger 取真实 entity/claim IDs，填入 JD 和 plan，避免测试硬编码无效 ID。

- [ ] **Step 2: 写 `needs_clarification` 与 ready plan 失败测试**

```python
def test_needs_clarification_returns_questions_without_building(self) -> None:
    workspace, plan = self.make_workspace_and_plan(status="needs_clarification")
    plan["clarifications"] = [
        {
            "question_id": "q-evals",
            "capability_ids": ["cap-mcp"],
            "question": "Did the platform include a repeatable evaluation suite?",
        }
    ]

    result = validate_projection_plan(workspace, plan)

    self.assertEqual(result["status"], "needs_clarification")
    self.assertEqual(len(result["clarifications"]), 1)
```

其他具体测试：

- 6 个 clarifications 抛出 `ValueError`；
- stale `target_jd_fingerprint` 抛出包含 `stale JD` 的错误；
- stale Source Snapshot fingerprint 失败；
- 缺少正式工作 entity 失败；
- `target_bullet_count` 为 0 或 6 失败；
- Skills group 为 1 或 5 失败；
- unknown/inactive/revoked claim 失败；
- unknown capability ID 失败；
- Content Intent 跨两个 entity 的 claim 失败；
- duplicate `intent_id` 失败；
- `revision > 3` 失败。

- [ ] **Step 3: 运行测试并确认失败**

```bash
python3 -m unittest tests.test_projection_plan_manager -v
```

Expected: FAIL，`scripts.projection_plan_manager` 不存在。

- [ ] **Step 4: 创建模块、类型和路径常量**

```python
#!/usr/bin/env python3
"""Validate and materialize model-produced resume projection artifacts."""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.resume_cache_manager import validate_jd_analysis
from scripts.resume_shared import (
    canonical_json_fingerprint,
    load_json_file,
    stable_identifier,
    write_json_file,
)

CACHE_DIR = "cache"
PLAN_NAME = "projection-plan.json"
LANGUAGE_NAME = "projection-language.json"
WORKING_NAME = "resume-working.json"
MANIFEST_NAME = "resume-changes.json"
LEDGER_NAME = "candidate-evidence.json"
SNAPSHOT_NAME = "base-resume.json"
JD_NAME = "jd-analysis.json"

PlanStatus = Literal["needs_clarification", "ready", "revision_required"]


@dataclass(frozen=True)
class BuildResult:
    status: str
    resume_path: Path | None
    manifest_path: Path | None
    clarifications: tuple[dict[str, Any], ...]
```

- [ ] **Step 5: 实现 Projection Plan 验证**

实现以下 private helper：

```python
def _workspace_paths(workspace: Path) -> dict[str, Path]
def _active_claim_index(ledger: dict[str, Any]) -> dict[str, tuple[str, dict[str, Any]]]
def _capability_index(jd_analysis: dict[str, Any]) -> dict[str, dict[str, Any]]
def _base_experience_entity_ids(snapshot: dict[str, Any]) -> list[str]
def _intent_records(plan: dict[str, Any]) -> list[dict[str, Any]]
def _validate_constraints(plan: dict[str, Any]) -> None
def _validate_clarifications(plan: dict[str, Any]) -> None
def _validate_experience_coverage(plan: dict[str, Any], expected_ids: list[str]) -> None
def _validate_intents(
    plan: dict[str, Any],
    claim_index: dict[str, tuple[str, dict[str, Any]]],
    capability_index: dict[str, dict[str, Any]],
) -> None
def _validate_skill_groups(plan: dict[str, Any], claim_index: dict[str, tuple[str, dict[str, Any]]]) -> None
```

Public validation：

```python
def validate_projection_plan(workspace: Path, plan: dict[str, Any]) -> dict[str, Any]:
    paths = _workspace_paths(workspace.resolve())
    jd_analysis = load_json_file(paths["jd"])
    validate_jd_analysis(jd_analysis)
    snapshot = load_json_file(paths["snapshot"])
    ledger = load_json_file(paths["ledger"])

    if plan.get("target_jd_fingerprint") != canonical_json_fingerprint(jd_analysis):
        raise ValueError("Projection Plan has a stale JD fingerprint.")
    source_fingerprint = str(snapshot.get("source_fingerprint", ""))
    if plan.get("source_snapshot_fingerprint") != source_fingerprint:
        raise ValueError("Projection Plan has a stale Source Snapshot fingerprint.")

    _validate_constraints(plan)
    _validate_clarifications(plan)
    _validate_experience_coverage(plan, _base_experience_entity_ids(snapshot))
    claim_index = _active_claim_index(ledger)
    capability_index = _capability_index(jd_analysis)
    _validate_intents(plan, claim_index, capability_index)
    _validate_skill_groups(plan, claim_index)

    return {
        "status": str(plan["status"]),
        "clarifications": copy.deepcopy(plan.get("clarifications", [])),
        "intent_count": len(_intent_records(plan)),
    }
```

- [ ] **Step 6: 增加 CLI `--help` 和 validate action**

CLI 支持：

```bash
python3 scripts/projection_plan_manager.py validate \
  --workspace /external/workspace \
  --plan /external/workspace/cache/projection-plan.json
```

`main() -> int` 捕获 `FileNotFoundError/OSError/ValueError`，错误写 stderr 并返回 1；valid plan 输出 JSON 并返回 0；`needs_clarification` 返回 2。

- [ ] **Step 7: 运行 Task 3 测试**

```bash
python3 -m unittest tests.test_projection_plan_manager -v
python3 scripts/projection_plan_manager.py --help
```

Expected: PASS；help exit 0。

- [ ] **Step 8: 提交 Task 3**

```bash
git add scripts/projection_plan_manager.py tests/test_projection_plan_manager.py
git commit -m "feat: validate model projection plans"
```

---

### Task 4: Language Output 验证、投影生成和原子 Manifest 构建

**Files:**

- Modify: `scripts/projection_plan_manager.py`
- Modify: `tests/test_projection_plan_manager.py`

**Interfaces:**

- Consumes: Task 3 `validate_projection_plan()`
- Produces: `validate_language_output(plan: dict[str, Any], language: dict[str, Any], ledger: dict[str, Any], *, previous_plan: dict[str, Any] | None = None, previous_language: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]`
- Produces: `build_projection(workspace: Path, plan_path: Path, language_path: Path) -> BuildResult`

- [ ] **Step 1: 写 Language Output 验证失败测试**

具体测试名称和预期：

```python
def test_language_output_requires_exactly_one_record_per_intent(self) -> None:
    workspace, plan, language = self.make_ready_artifacts()
    language["items"].pop()

    with self.assertRaisesRegex(ValueError, "missing intent"):
        validate_language_output(
            plan,
            language,
            load_json_file(workspace / "cache" / "candidate-evidence.json"),
        )


def test_language_output_rejects_changed_claim_links(self) -> None:
    workspace, plan, language = self.make_ready_artifacts()
    language["items"][0]["source_claim_ids"] = ["claim-unknown"]

    with self.assertRaisesRegex(ValueError, "claim links"):
        validate_language_output(
            plan,
            language,
            load_json_file(workspace / "cache" / "candidate-evidence.json"),
        )
```

另外覆盖：

- plan revision mismatch；
- JD fingerprint mismatch；
- duplicate/extra intent；
- revision 2 或 3 中未改变 Content Intent 却改变 rendered text；
- `facts_added`、`facts_removed` 或 `metrics_changed` 非空；
- `ownership_changed` 为 true；
- rendered text 为空；
- `I`, `my`, `we`, `our` 第一人称；
- `I hope this helps`, `Would you like`, `[To be filled` 和 HTML placeholder。

- [ ] **Step 2: 写原子构建失败测试**

先在 workspace 写入 sentinel `resume-working.json` 和 `resume-changes.json`。提供 invalid language output，调用 `build_projection()`，断言两文件内容未改变。

```python
old_resume = {"sentinel": "resume"}
old_manifest = {"sentinel": "manifest"}
write_json_file(cache / "resume-working.json", old_resume)
write_json_file(cache / "resume-changes.json", old_manifest)

with self.assertRaises(ValueError):
    build_projection(workspace, plan_path, language_path)

self.assertEqual(load_json_file(cache / "resume-working.json"), old_resume)
self.assertEqual(load_json_file(cache / "resume-changes.json"), old_manifest)
```

- [ ] **Step 3: 运行测试并确认失败**

```bash
python3 -m unittest tests.test_projection_plan_manager -v
```

Expected: FAIL，缺少 `validate_language_output` 和 `build_projection`。

- [ ] **Step 4: 实现 Language Output 验证**

在模块 import 区增加：

```python
from scripts.audit_factual_integrity import audit_resume
from scripts.resume_shared import validate_resume_content
```

增加 blocking pattern：

```python
_FIRST_PERSON_RE = re.compile(r"(?<!\w)(?:I|me|my|mine|we|our|ours)(?!\w)", re.IGNORECASE)
_CHATBOT_RE = re.compile(
    r"\b(?:I hope this helps|Would you like|Let me know|Great question|Certainly!)\b",
    re.IGNORECASE,
)
_PLACEHOLDER_RE = re.compile(r"\[(?:To be filled|Insert|Placeholder)[^\]]*\]", re.IGNORECASE)
```

验证返回 intent ID 到 language item 的 index。它必须严格比较 plan Content Intent 的 `claim_ids` 和 language 的 `source_claim_ids`，不能只比较集合中的部分值。

将函数签名定义为：

```python
def validate_language_output(
    plan: dict[str, Any],
    language: dict[str, Any],
    ledger: dict[str, Any],
    *,
    previous_plan: dict[str, Any] | None = None,
    previous_language: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
```

当 `plan["revision"] > 1` 时必须提供上一轮 plan/language。若同一 `intent_id` 的 `claim_ids`、`capability_ids`、`content_intent` 和 `target_lines` 均未改变，则本轮 `rendered_text` 必须与上一轮完全一致；否则抛出包含 `unrelated wording drift` 的 `ValueError`。

- [ ] **Step 5: 实现 Tailored Resume materialization**

增加：

```python
def _source_payload(snapshot: dict[str, Any]) -> dict[str, Any]:
    payload = copy.deepcopy(snapshot)
    payload.pop("source_fingerprint", None)
    payload.pop("captured_at", None)
    return payload


def _materialize_resume(
    snapshot: dict[str, Any],
    plan: dict[str, Any],
    language_by_intent: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    resume = _source_payload(snapshot)
    resume["summary"] = language_by_intent[plan["summary_intent"]["intent_id"]][
        "rendered_text"
    ]
    resume["skills"] = _materialize_skill_groups(plan["skills_plan"])
    resume["experience"] = _materialize_experience(
        resume.get("experience", []),
        plan["experience_plans"],
        language_by_intent,
    )
    _apply_optional_section_decisions(resume, plan.get("optional_sections", []))
    validate_resume_content(resume, require_non_empty=True)
    return resume
```

Formal experience 顺序来自 Source Snapshot，不由 plan 改变。Plan 只决定每段 bullet 的内容和顺序。

- [ ] **Step 6: 实现 Manifest materialization**

增加 helper：

```python
def _materialize_manifest(
    resume: dict[str, Any],
    snapshot: dict[str, Any],
    ledger: dict[str, Any],
    jd_analysis: dict[str, Any],
    plan: dict[str, Any],
    language_by_intent: dict[str, dict[str, Any]],
) -> dict[str, Any]:
```

规则：

- Summary 和 bullet 使用对应 Content Intent 的 entity/claims/action/reason；
- Skills item 使用 plan item 的 entity/claims；
- Skills category 使用 Task 2 presentation binding；
- 公司、职位、日期、联系方式、教育等未改字段通过 exact source path claim 绑定；
- 被替换或删除的 Source Snapshot 字段进入 `removed_entries`；
- 设置 JD fingerprint、resume fingerprint、generated_at 和空 `warning_dispositions`；
- 在写盘前调用 `audit_resume()`，verdict 非 PASS 时抛出 `ValueError` 并包含 finding code。

- [ ] **Step 7: 实现原子 build**

```python
def build_projection(
    workspace: Path,
    plan_path: Path,
    language_path: Path,
) -> BuildResult:
    workspace = workspace.expanduser().resolve()
    plan = load_json_file(plan_path.expanduser().resolve())
    validation = validate_projection_plan(workspace, plan)
    if validation["status"] == "needs_clarification":
        return BuildResult(
            status="needs_clarification",
            resume_path=None,
            manifest_path=None,
            clarifications=tuple(validation["clarifications"]),
        )

    paths = _workspace_paths(workspace)
    language = load_json_file(language_path.expanduser().resolve())
    ledger = load_json_file(paths["ledger"])
    snapshot = load_json_file(paths["snapshot"])
    jd_analysis = load_json_file(paths["jd"])
    previous_plan_path = paths["last_plan"]
    previous_language_path = paths["last_language"]
    previous_plan = load_json_file(previous_plan_path) if previous_plan_path.exists() else None
    previous_language = (
        load_json_file(previous_language_path)
        if previous_language_path.exists()
        else None
    )
    language_by_intent = validate_language_output(
        plan,
        language,
        ledger,
        previous_plan=previous_plan,
        previous_language=previous_language,
    )
    resume = _materialize_resume(snapshot, plan, language_by_intent)
    manifest = _materialize_manifest(
        resume,
        snapshot,
        ledger,
        jd_analysis,
        plan,
        language_by_intent,
    )

    write_json_file(paths["working"], resume)
    write_json_file(paths["manifest"], manifest)
    write_json_file(paths["last_plan"], plan)
    write_json_file(paths["last_language"], language)
    return BuildResult(
        status="built",
        resume_path=paths["working"],
        manifest_path=paths["manifest"],
        clarifications=(),
    )
```

所有验证和 audit 在首次 `write_json_file()` 之前完成。`_workspace_paths()` 同时定义 `last_plan = cache/projection-plan.last-built.json` 和 `last_language = cache/projection-language.last-built.json`。Revision 2 或 3 缺少上一轮 artifact 时构建失败；成功后才更新 last-built artifact。

- [ ] **Step 8: 增加 build CLI action**

```bash
python3 scripts/projection_plan_manager.py build \
  --workspace /external/workspace \
  --plan /external/workspace/cache/projection-plan.json \
  --language /external/workspace/cache/projection-language.json
```

输出 `asdict(BuildResult)`，Path 转 string；`needs_clarification` 返回 2；成功返回 0。

- [ ] **Step 9: 运行 Projection Manager 与审计测试**

```bash
python3 -m unittest tests.test_projection_plan_manager tests.test_factual_audit -v
```

Expected: PASS。

- [ ] **Step 10: 提交 Task 4**

```bash
git add scripts/projection_plan_manager.py tests/test_projection_plan_manager.py
git commit -m "feat: build evidence-bound resume projections"
```

---

### Task 5: Resume Language Optimizer 的可解释 advisory diagnostics

**Files:**

- Modify: `scripts/check_content_quality.py:30-134`
- Modify: `tests/test_content_quality.py`

**Interfaces:**

- Produces: `check_resume_language_patterns(texts: list[str]) -> dict[str, str]`
- Consumes: existing `run_all_checks()`

- [ ] **Step 1: 写 pattern-cluster 失败测试**

```python
def test_language_pattern_cluster_warns_without_claiming_ai_authorship(self) -> None:
    resume = resume_with(
        [
            {
                "company": "Example",
                "title": "Engineer",
                "dates": "2020 - Present",
                "bullets": [
                    "Successfully leveraged a cutting-edge platform, fostering seamless collaboration.",
                    "Not only improved reliability, but also transformed the engineering landscape.",
                ],
            }
        ]
    )

    check = next(
        item for item in run_all_checks(resume)
        if item["name"] == "language_pattern_cluster"
    )

    self.assertEqual(check["status"], "WARN")
    self.assertIn("promotional_language", check["detail"])
    self.assertIn("negative_parallelism", check["detail"])
    self.assertNotIn("probability", check["detail"].casefold())
    self.assertNotIn("detector", check["detail"].casefold())
```

再增加 false-positive 测试：

- `Led API design, SDK documentation, and launch reviews.` 只有有效三项列表，不 WARN；
- `Built Go, C#, and Python services.` 保留标准技术列表；
- 单个 `robust` 不单独触发 cluster；
- 现有 qualitative-result 测试继续 PASS。

- [ ] **Step 2: 运行测试并确认失败**

```bash
python3 -m unittest tests.test_content_quality -v
```

Expected: FAIL，找不到 `language_pattern_cluster`。

- [ ] **Step 3: 实现 pattern 检测**

在 `scripts/check_content_quality.py` 定义命名规则，不生成 AI score：

```python
_LANGUAGE_PATTERNS: dict[str, re.Pattern[str]] = {
    "promotional_language": re.compile(
        r"\b(?:cutting-edge|groundbreaking|transformative|best-in-class|seamless(?:ly)?)\b",
        re.IGNORECASE,
    ),
    "empty_qualifier": re.compile(
        r"\b(?:successfully|strategically|efficiently)\b",
        re.IGNORECASE,
    ),
    "negative_parallelism": re.compile(
        r"\b(?:not only\b.{0,80}\bbut also|not just\b.{0,80}\bbut)\b",
        re.IGNORECASE,
    ),
    "trailing_participle": re.compile(
        r",\s+(?:ensuring|fostering|highlighting|underscoring)\b",
        re.IGNORECASE,
    ),
    "copula_avoidance": re.compile(
        r"\b(?:serves as|stands as|boasts)\b",
        re.IGNORECASE,
    ),
    "filler": re.compile(
        r"\b(?:in order to|responsible for|it is important to note)\b",
        re.IGNORECASE,
    ),
}
```

`check_resume_language_patterns()` 只有检测到至少两个不同 pattern family，或同一 family 在两个以上 bullet 出现时才 WARN。Detail 输出 pattern 名称和路径/文本片段，不使用 `AI-generated`、概率或 detector 分数。

- [ ] **Step 4: 接入 `run_all_checks()`**

将 Summary、Experience/Project bullets 作为输入；Skills canonical terms 不参与语言 pattern 检查。

```python
prose = [str(resume.get("summary", ""))]
prose.extend(all_bullets)
checks.append(check_resume_language_patterns([text for text in prose if text.strip()]))
```

- [ ] **Step 5: 运行内容质量测试**

```bash
python3 -m unittest tests.test_content_quality -v
```

Expected: PASS。

- [ ] **Step 6: 提交 Task 5**

```bash
git add scripts/check_content_quality.py tests/test_content_quality.py
git commit -m "feat: flag formulaic resume language"
```

---

### Task 6: 真实 PDF Content Fit Feedback

**Files:**

- Modify: `scripts/check_pdf_geometry.py:18-163`
- Modify: `scripts/check_pdf_quality.py:18-25,121-144`
- Modify: `tests/test_pdf_geometry.py`

**Interfaces:**

- Produces: `build_content_fit_feedback(pdf_path: Path, resume: dict[str, Any], *, plan_revision: int, preferred_max_bottom_mm: float = 8.0) -> dict[str, Any]`
- Produces: `_section_geometry(lines: list[dict[str, Any]], resume: dict[str, Any]) -> dict[str, dict[str, float | int]]`
- Consumes: `extract_page_lines()`, `detect_sparse_bullet_endings()`

- [ ] **Step 1: 写 section geometry 和 fit 分类失败测试**

在 `tests/test_pdf_geometry.py` 构造合成 lines：

```python
resume = {
    "name": "Alex Chen",
    "contact": "alex@example.com | +1 206-555-0100",
    "summary": "Backend engineer.",
    "skills": [{"category": "Languages", "items": ["Python", "Go"]}],
    "experience": [
        {
            "company": "Example Corp",
            "title": "Engineer",
            "dates": "2020 - Present",
            "bullets": ["Built a Python service."],
        }
    ],
    "education": [{"school": "Example", "degree": "B.S.", "dates": "2020"}],
}
lines = [
    {"text": "SUMMARY", "top": 20.0, "bottom": 30.0, "x0": 50.0, "x1": 120.0, "words": ["SUMMARY"]},
    {"text": "Backend engineer.", "top": 32.0, "bottom": 42.0, "x0": 50.0, "x1": 180.0, "words": ["Backend", "engineer."]},
    {"text": "PROFESSIONAL EXPERIENCE", "top": 50.0, "bottom": 60.0, "x0": 50.0, "x1": 240.0, "words": ["PROFESSIONAL", "EXPERIENCE"]},
    {"text": "Example Corp", "top": 62.0, "bottom": 72.0, "x0": 50.0, "x1": 130.0, "words": ["Example", "Corp"]},
    {"text": "• Built a Python service.", "top": 74.0, "bottom": 84.0, "x0": 55.0, "x1": 220.0, "words": ["•", "Built", "a", "Python", "service."]},
    {"text": "TECHNICAL SKILLS", "top": 90.0, "bottom": 100.0, "x0": 50.0, "x1": 180.0, "words": ["TECHNICAL", "SKILLS"]},
    {"text": "Languages: Python, Go", "top": 102.0, "bottom": 112.0, "x0": 50.0, "x1": 210.0, "words": ["Languages:", "Python,", "Go"]},
]
geometry = _section_geometry(lines, resume)
self.assertEqual(geometry["summary"]["line_count"], 1)
self.assertEqual(geometry["experience[0]"]["line_count"], 2)
self.assertEqual(geometry["skills"]["line_count"], 1)
```

再用 mock PDF 或临时 ReportLab fixture 测试：

- page_count 2 -> `overflow`；
- page_count 1、bottom whitespace > 8mm -> `underfill`；
- page_count 1、margin 合适、Skills 2–4 行 -> `fit`；
- Skills 5 行 -> `revision_required` issue；
- 返回 plan revision 和 sparse trailing findings。

- [ ] **Step 2: 运行测试并确认失败**

```bash
python3 -m unittest tests.test_pdf_geometry -v
```

Expected: FAIL，缺少 `_section_geometry` 和 `build_content_fit_feedback`。

- [ ] **Step 3: 实现 section mapping**

使用已渲染标题定位范围：

```python
_SECTION_HEADERS = {
    "SUMMARY": "summary",
    "PROFESSIONAL EXPERIENCE": "experience",
    "PROJECTS": "projects",
    "TECHNICAL SKILLS": "skills",
    "AWARDS": "awards",
    "CERTIFICATIONS": "certifications",
    "EDUCATION": "education",
}
```

Experience 内使用 Source Snapshot 顺序和 company/date 文本定位 entry 开始；重复公司时使用 dates 消歧。找不到 entry 时，将行计入 aggregate `experience` 并增加 `mapping_warnings`，不得伪造 section geometry。

- [ ] **Step 4: 实现 feedback**

```python
def build_content_fit_feedback(
    pdf_path: Path,
    resume: dict[str, Any],
    *,
    plan_revision: int,
    preferred_max_bottom_mm: float = 8.0,
) -> dict[str, Any]:
    validate_resume_content(resume, require_non_empty=True)
    with pdfplumber.open(pdf_path) as pdf:
        page_lines = [extract_page_lines(page) for page in pdf.pages]
        page_count = len(pdf.pages)
        first_page = pdf.pages[0]
        margins = estimate_page_margins_mm(first_page)
        section_geometry = _section_geometry(page_lines[0], resume)
        sparse = detect_sparse_bullet_endings(
            page_lines[0], page_width=float(first_page.width)
        )

    skills_lines = int(section_geometry.get("skills", {}).get("line_count", 0))
    issues: list[str] = []
    if skills_lines and not 2 <= skills_lines <= 4:
        issues.append("skills_rendered_line_budget")
    if page_count > 1:
        verdict = "overflow"
    elif margins is not None and margins["bottom"] > preferred_max_bottom_mm:
        verdict = "underfill"
    elif issues:
        verdict = "revision_required"
    else:
        verdict = "fit"
    return {
        "schema_version": 1,
        "plan_revision": plan_revision,
        "verdict": verdict,
        "page_count": page_count,
        "bottom_whitespace_mm": None if margins is None else round(margins["bottom"], 2),
        "section_geometry": section_geometry,
        "sparse_trailing_bullets": sparse,
        "issues": issues,
    }
```

把纯几何函数 `estimate_page_margins_mm(page: Any) -> dict[str, float] | None` 从 `scripts/check_pdf_quality.py` 移到 `scripts/check_pdf_geometry.py`。`check_pdf_quality.py` 从 `check_pdf_geometry.py` 导入该函数，与现有 `check_pdf_geometry` 导入保持同一方向，避免循环依赖并保持单一实现。

- [ ] **Step 5: 扩展 CLI**

为 `check_pdf_geometry.py` 增加可选 `--resume`、`--plan-revision` 和 `--feedback-output`。未传 `--resume` 时保持当前 sparse ending 报告行为。

- [ ] **Step 6: 运行 geometry 与 PDF QA 测试**

```bash
python3 -m unittest tests.test_pdf_geometry tests.test_pdf_pipeline -v
```

Expected: PASS。

- [ ] **Step 7: 提交 Task 6**

```bash
git add scripts/check_pdf_geometry.py scripts/check_pdf_quality.py tests/test_pdf_geometry.py tests/test_pdf_pipeline.py
git commit -m "feat: report projection content fit geometry"
```

---

### Task 7: Quality Report 展示规划、语言和 Content Fit 决策

**Files:**

- Modify: `scripts/generate_quality_report.py:290-417`
- Modify: `tests/test_quality_report.py`

**Interfaces:**

- Extends: `generate_report(resume: dict[str, Any], jd_analysis: dict[str, Any] | None, *, pdf_report: dict[str, Any] | None = None, factual_report: dict[str, Any] | None = None, projection_plan: dict[str, Any] | None = None, language_output: dict[str, Any] | None = None, content_fit_feedback: dict[str, Any] | None = None) -> str`
- Produces: `format_projection_plan_section()`, `format_language_optimization_section()`, `format_content_fit_section()`

- [ ] **Step 1: 写报告 section 失败测试**

```python
def test_report_includes_projection_language_and_content_fit_sections(self) -> None:
    resume = {
        "name": "Alex Chen",
        "contact": "alex@example.com | +1 206-555-0100",
        "summary": "Backend engineer.",
        "skills": [{"category": "AI Platforms", "items": ["MCP", "RAG"]}],
        "experience": [
            {
                "company": "Example",
                "title": "Engineer",
                "dates": "2020 - Present",
                "bullets": ["Built an MCP integration for service diagnostics."],
            }
        ],
        "education": [{"school": "Example", "degree": "B.S.", "dates": "2020"}],
    }
    jd_analysis = {
        "position": "Applied AI Engineer",
        "keywords": {"P1": ["MCP"], "P2": ["RAG"], "P3": []},
        "capabilities": [],
        "alignment": {"matched": [], "transferable": [], "gaps": []},
    }
    report = generate_report(
        resume,
        jd_analysis,
        projection_plan={
            "revision": 2,
            "experience_plans": [
                {
                    "entity_id": "experience-example",
                    "importance": "critical",
                    "target_bullet_count": 4,
                    "reason": "Carries direct P1 evidence.",
                }
            ],
            "optional_sections": [
                {
                    "section": "awards",
                    "decision": "remove",
                    "reason": "Duplicates selected experience evidence.",
                }
            ],
            "skills_plan": {
                "groups": [
                    {"category": "AI Platforms", "items": [{"display_term": "MCP"}]}
                ]
            },
        },
        language_output={
            "items": [
                {
                    "intent_id": "intent-1",
                    "style_actions": ["remove_template_language"],
                    "meaning_check": {
                        "facts_added": [],
                        "facts_removed": [],
                        "metrics_changed": [],
                        "ownership_changed": False,
                    },
                }
            ]
        },
        content_fit_feedback={
            "plan_revision": 2,
            "verdict": "fit",
            "page_count": 1,
            "bottom_whitespace_mm": 7.5,
            "issues": [],
        },
    )

    self.assertIn("Projection Plan", report)
    self.assertIn("critical", report)
    self.assertIn("Removed optional sections", report)
    self.assertIn("Resume Language Optimization", report)
    self.assertIn("remove_template_language", report)
    self.assertIn("Content Fit", report)
    self.assertIn("7.5", report)
```

- [ ] **Step 2: 运行测试并确认失败**

```bash
python3 -m unittest tests.test_quality_report -v
```

Expected: FAIL，`generate_report()` 不接受新参数。

- [ ] **Step 3: 实现格式化 section**

报告必须展示：

- Plan revision；
- 每段 Experience importance、目标 bullet 数和 reason；
- Skills group 与保留 item；
- Optional section 的 keep/remove 及 reason；
- Language style actions 汇总；
- Meaning check 是否声明零变化；
- Content Fit verdict、页数、bottom whitespace、Skills 行数、issues 和修订次数。

不要把 lexical keyword coverage 替换成模型评分；保留现有 coverage 作为诊断。

- [ ] **Step 4: 扩展 CLI 参数**

增加：

```text
--projection-plan
--language-output
--content-fit-feedback
```

参数均可选。存在时加载 JSON 并加入报告；不存在时保持当前报告完全兼容。

- [ ] **Step 5: 运行报告测试**

```bash
python3 -m unittest tests.test_quality_report -v
```

Expected: PASS。

- [ ] **Step 6: 提交 Task 7**

```bash
git add scripts/generate_quality_report.py tests/test_quality_report.py
git commit -m "feat: report model projection decisions"
```

---

### Task 8: 模型协议、Skill 工作流和平台入口文档

**Files:**

- Create: `references/projection-planning-protocol.md`
- Modify: `SKILL.md`
- Modify: `CONTEXT.md`
- Modify: `references/resume-working-schema.md`
- Modify: `references/prompt-recipes.md`
- Modify: `references/execution-checklist.md`
- Modify: `references/resume-language-quality.md`
- Modify: `scripts/check_agent_platform_support.py:14-39,137-192`
- Modify: `tests/test_external_entrypoints.py:11-35`
- Modify: `tests/test_skill_metadata.py`

**Interfaces:**

- Documents: Projection Plan / Language Output schemas and host-model prompt contracts
- Exposes: `projection_plan_manager.py --help` outside repository cwd

- [ ] **Step 1: 写平台入口失败测试**

在 `tests/test_external_entrypoints.py` 的 scripts tuple 增加 `projection_plan_manager.py`。

在 `tests/test_skill_metadata.py` 增加断言，要求 `SKILL.md` 包含：

```python
for term in (
    "projection-plan.json",
    "projection-language.json",
    "Resume Language Optimizer",
    "Content Fit Feedback",
    "projection_plan_manager.py",
):
    self.assertIn(term, skill_text)
```

- [ ] **Step 2: 运行测试并确认失败**

```bash
python3 -m unittest tests.test_external_entrypoints tests.test_skill_metadata -v
```

Expected: FAIL，因为平台脚本列表和 Skill 工作流尚未更新。

- [ ] **Step 3: 编写 `projection-planning-protocol.md`**

文档必须完整包含：

1. 输入：JD Analysis、active Ledger、Candidate Profile、Source Snapshot、页面约束；
2. 模型阶段：Clarification -> Projection Plan -> Resume Language Optimization；
3. 完整 Projection Plan JSON schema 和 status；
4. 完整 Language Output JSON schema；
5. Skills item array 与 presentation binding；
6. employment 1–5 bullet、Skills 2–4 group/line、最多 5 个问题和 3 次 revision；
7. overflow/underfill 模型决策顺序；
8. selective rewrite 规则；
9. 失败分支；
10. OpenAI-like 与 distributed-systems-like 合成示例。

不得写入真实候选人个人数据。

- [ ] **Step 4: 更新 `SKILL.md` 工作流**

将原“Generate Projection and Manifest”拆成：

1. Produce Clarifications or ready Projection Plan；
2. Ingest answers；
3. Produce Language Output；
4. Run Projection Plan Manager；
5. Run factual audit；
6. Run preferred-layout temporary render and Content Fit Feedback；
7. Revise at most three times；
8. Run layout-only auto-fit；
9. Quality report and visual QA。

明确：模型生成 artifact，Python 不调用模型；AI detector 不进入 QA。

- [ ] **Step 5: 更新 schema、语言和 checklist 文档**

- `resume-working-schema.md`：Skills `items` 新数组格式、legacy string 兼容、item-level Manifest path、presentation category binding；
- `prompt-recipes.md`：Projection Planner 和 Resume Language Optimizer 两个独立 prompt recipe；
- `execution-checklist.md`：Content Fit 三轮、Skills 实际 2–4 行、旧 Accepted Resume 保护；
- `resume-language-quality.md`：采用/拒绝 Humanizer 规则、meaning check、advisory pattern cluster；
- `CONTEXT.md`：确保 Projection Plan、Content Intent、Resume Language Optimization、Skill Presentation Group 和 Content Fit Feedback 定义与规格一致。

- [ ] **Step 6: 更新平台支持检查**

把以下加入 `EXPECTED_ASSETS`：

```python
Path("scripts/projection_plan_manager.py"),
Path("references/projection-planning-protocol.md"),
```

把 `projection_plan_manager.py` 加入 `_baseline_checks()` 外部入口列表。

- [ ] **Step 7: 运行文档与入口测试**

```bash
python3 -m unittest tests.test_external_entrypoints tests.test_skill_metadata -v
python3 scripts/check_agent_platform_support.py
```

Expected: PASS。

- [ ] **Step 8: 提交 Task 8**

```bash
git add SKILL.md CONTEXT.md references/projection-planning-protocol.md references/resume-working-schema.md references/prompt-recipes.md references/execution-checklist.md references/resume-language-quality.md scripts/check_agent_platform_support.py tests/test_external_entrypoints.py tests/test_skill_metadata.py
git commit -m "docs: add model projection workflow protocol"
```

---

### Task 9: 双 JD 合成验收与全量发布验证

**Files:**

- Create: `tests/test_projection_end_to_end.py`
- Create: `tests/fixtures/projection/jd-applied-ai.json`
- Create: `tests/fixtures/projection/jd-distributed-systems.json`
- Create: `tests/fixtures/projection/plan-applied-ai.json`
- Create: `tests/fixtures/projection/plan-distributed-systems.json`
- Create: `tests/fixtures/projection/language-applied-ai.json`
- Create: `tests/fixtures/projection/language-distributed-systems.json`
- Modify: `tests/test_pdf_pipeline.py`

**Interfaces:**

- Consumes: all previous tasks
- Proves: same synthetic Ledger yields materially different Tailored Resumes for two JDs

- [ ] **Step 1: 创建不含个人信息的 fixture**

Synthetic candidate 使用：

- `Alex Chen`；
- `Example Cloud` 当前 AI diagnostics role；
- `Example Social` API platform role；
- `Example Commerce` Java distributed-systems role；
- synthetic email/phone；
- synthetic metrics such as 10M requests、20K QPS，并确保所有数字在 Ledger claim 中产生。

两个 JD fixture 必须有完整 `capabilities`、`keywords` 和 `alignment`。

Applied AI plan 选择：MCP、Azure OpenAI、RAG、Evals、API、observability，删除 standalone synthetic Award。

Distributed plan 选择：Java、Go、Kafka、Kubernetes、Redis、high availability，减少 MCP/Evals 展示。

Fixture 中 fingerprint 不能手写静态错误值。测试加载 fixture template 后，根据 runtime workspace 的 JD 和 Source Snapshot 计算并写入 plan copy。Entity/claim IDs 使用 `initialize_workspace()` 对固定 synthetic resume 生成的确定性 ID；测试首先断言 fixture 引用的每个 ID 都存在于 runtime Ledger。

在 `tests/test_projection_end_to_end.py` 定义完整 helper：

```python
def synthetic_resume() -> dict[str, Any]:
    return {
        "name": "Alex Chen",
        "contact": "Seattle, WA | alex@example.com | +1 206-555-0100",
        "summary": "Software engineer building AI diagnostics and distributed APIs.",
        "skills": [
            {"category": "AI", "items": "Azure OpenAI, MCP, RAG, Evals"},
            {"category": "Backend", "items": "Java, Go, Python, Kafka, Redis, Kubernetes"},
        ],
        "experience": [
            {
                "company": "Example Cloud",
                "title": "Software Engineer",
                "location": "Seattle, WA",
                "dates": "2024 - Present",
                "bullets": [
                    "Built an MCP diagnostic workflow on Azure OpenAI with tool calling.",
                    "Created RAG evaluations for incident diagnostics.",
                ],
            },
            {
                "company": "Example Social",
                "title": "Software Engineer",
                "location": "Seattle, WA",
                "dates": "2021 - 2024",
                "bullets": [
                    "Built Go APIs serving 10M daily requests on Kubernetes.",
                    "Reduced data latency with Kafka and Redis.",
                ],
            },
            {
                "company": "Example Commerce",
                "title": "Software Engineer",
                "location": "Beijing, China",
                "dates": "2018 - 2021",
                "bullets": [
                    "Built Java services handling 20K QPS with high availability.",
                ],
            },
        ],
        "awards": [
            {
                "name": "Synthetic Distributed Scheduling Patent",
                "organization": "Example Commerce",
                "dates": "2021",
            }
        ],
        "education": [
            {
                "school": "Example University",
                "degree": "B.S. Computer Science",
                "dates": "2018",
                "location": "Seattle, WA",
            }
        ],
    }


def build_fixture_projection(
    workspace: Path,
    jd_name: str,
    plan_name: str,
    language_name: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    fixture_root = Path(__file__).resolve().parent / "fixtures" / "projection"
    jd = load_json_file(fixture_root / jd_name)
    write_json_file(workspace / "cache" / "jd-analysis.json", jd)
    snapshot = load_json_file(workspace / "cache" / "base-resume.json")
    ledger = load_json_file(workspace / "cache" / "candidate-evidence.json")
    active_ids = {
        str(claim["claim_id"])
        for entity in ledger["entities"]
        for claim in entity["claims"]
        if entity["state"] == "active" and claim["status"] == "active"
    }

    plan = load_json_file(fixture_root / plan_name)
    referenced_ids = {
        str(claim_id)
        for experience in plan["experience_plans"]
        for intent in experience["content_intents"]
        for claim_id in intent["claim_ids"]
    }
    referenced_ids.update(
        str(claim_id)
        for group in plan["skills_plan"]["groups"]
        for item in group["items"]
        for claim_id in item["claim_ids"]
    )
    if not referenced_ids <= active_ids:
        raise AssertionError(f"Fixture references unknown claims: {sorted(referenced_ids - active_ids)}")

    plan["target_jd_fingerprint"] = canonical_json_fingerprint(jd)
    plan["source_snapshot_fingerprint"] = str(snapshot["source_fingerprint"])
    language = load_json_file(fixture_root / language_name)
    language["target_jd_fingerprint"] = plan["target_jd_fingerprint"]
    plan_path = workspace / "cache" / "projection-plan.json"
    language_path = workspace / "cache" / "projection-language.json"
    write_json_file(plan_path, plan)
    write_json_file(language_path, language)
    result = build_projection(workspace, plan_path, language_path)
    if result.status != "built":
        raise AssertionError(f"Projection did not build: {result.status}")
    return (
        load_json_file(workspace / "cache" / "resume-working.json"),
        load_json_file(workspace / "cache" / "resume-changes.json"),
    )
```

- [ ] **Step 2: 写端到端失败测试**

```python
def test_same_ledger_produces_distinct_ai_and_distributed_projections(self) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = Path(temp_dir)
        initialize_workspace(workspace, synthetic_resume())

        ai_resume, ai_manifest = build_fixture_projection(
            workspace,
            "jd-applied-ai.json",
            "plan-applied-ai.json",
            "language-applied-ai.json",
        )
        distributed_resume, distributed_manifest = build_fixture_projection(
            workspace,
            "jd-distributed-systems.json",
            "plan-distributed-systems.json",
            "language-distributed-systems.json",
        )

        ai_skills = {
            item
            for group in ai_resume["skills"]
            for item in group["items"]
        }
        distributed_skills = {
            item
            for group in distributed_resume["skills"]
            for item in group["items"]
        }
        self.assertIn("MCP", ai_skills)
        self.assertIn("Evals", ai_skills)
        self.assertNotIn("Evals", distributed_skills)
        self.assertIn("Kafka", distributed_skills)
        self.assertNotEqual(ai_skills, distributed_skills)
        self.assertTrue(all(entry["bullets"] for entry in ai_resume["experience"]))
        self.assertTrue(all(entry["bullets"] for entry in distributed_resume["experience"]))
        ledger = load_json_file(workspace / "cache" / "candidate-evidence.json")
        base_resume = load_json_file(workspace / "cache" / "base-resume.json")
        self.assertEqual(
            audit_resume(
                ai_resume,
                ai_manifest,
                ledger,
                base_resume=base_resume,
            )["verdict"],
            "PASS",
        )
        self.assertEqual(
            audit_resume(
                distributed_resume,
                distributed_manifest,
                ledger,
                base_resume=base_resume,
            )["verdict"],
            "PASS",
        )
```

- [ ] **Step 3: 运行端到端测试并修正 fixture**

```bash
python3 -m unittest tests.test_projection_end_to_end -v
```

Expected: PASS。任何 fixture 证据不完整都必须修 fixture claim，不得放宽 audit。

- [ ] **Step 4: 加入临时 PDF 生成和几何断言**

对两个 projection：

1. factual audit PASS；
2. `run_all_checks()` 没有未 disposition warning；
3. 生成临时 PDF；
4. `check_pdf_file()` PASS；
5. `build_content_fit_feedback()` page_count 为 1；
6. Skills body line count 为 2–4。

如果 synthetic content 太长，按真实产品规则减少低价值 fixture content，不得在测试中降低字体/边距底线。

- [ ] **Step 5: 运行主动诊断**

在运行完整测试前：

```bash
python3 scripts/check_agent_platform_support.py
ruff check scripts templates tests
python3 -m unittest tests.test_projection_plan_manager tests.test_projection_end_to_end -v
```

然后运行：

```bash
python3 -m unittest discover -s tests -v
```

Expected: 全部 PASS。

- [ ] **Step 6: 运行项目级诊断**

```bash
python3 -m compileall -q scripts templates tests
```

使用 Pi Lens：

```text
lens_diagnostics(mode="all")
```

Expected: edited files 无 blocking errors。

- [ ] **Step 7: 外部真实 workspace 手动验收，不提交产物**

在 `/Users/yinglun/Projects/LocalWork` 或用户明确指定的外部 workspace：

1. 用 OpenAI JD 生成 Projection Plan 和 Language Output；
2. 运行 Projection Plan Manager；
3. 检查 standalone Patent/Awards 被删除，但 JD.COM bullet 可保留 `patented`；
4. 检查 Skills 为 2–4 行且只保留必要项；
5. 运行 factual audit、Content QA、Content Fit、auto-fit 和 PDF QA；
6. 用 host PDF skill 目检所有页面；
7. 确认失败不会替换之前 Accepted Resume。

不得把该 workspace 的 JSON、联系方式、PDF 或截图复制到仓库。

- [ ] **Step 8: 提交 Task 9**

```bash
git add tests/test_projection_end_to_end.py tests/fixtures/projection tests/test_pdf_pipeline.py
git commit -m "test: verify JD-specific model projections"
```

- [ ] **Step 9: 最终变更审查**

```bash
git status --short
git diff --stat HEAD~9..HEAD
python3 scripts/check_agent_platform_support.py
ruff check scripts templates tests
python3 -m unittest discover -s tests -v
```

确认：

- 没有个人 workspace 文件进入 Git；
- 没有 staged/generated PDF；
- 没有网络模型依赖；
- `auto_fit_layout()` 没有内容 mutation；
- Manifest coverage 为 100%；
- 所有测试通过。
