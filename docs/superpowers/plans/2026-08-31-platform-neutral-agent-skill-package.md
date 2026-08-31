# Platform-Neutral Agent Skill Package Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert MonkeyResume into a client-neutral Agent Skills package while preserving generic development safeguards and all resume behavior.

**Architecture:** Keep `SKILL.md` and reusable resources as the runtime package contract. Keep generic repository maintenance files, but remove client-specific adapters, probes, and active documentation references; enforce the boundary with structural tests and CI.

**Tech Stack:** Agent Skills open format, Markdown/YAML, Python 3.9+, unittest, Ruff, GitHub Actions

**Spec:** `docs/superpowers/specs/2026-08-31-platform-neutral-agent-skill-package-design.md`

## Global Constraints

- Preserve all existing MonkeyResume evidence, projection, language, PDF, and publication behavior.
- Preserve the user's existing uncommitted MonkeyResume rename work and edit only overlapping files required by this cleanup.
- Keep `AGENTS.md` as client-neutral repository development guidance.
- Install through `~/.agents/skills/monkey-resume`; do not document client-owned skill directories.
- Do not add client-specific commands, UI metadata, plugin manifests, or runtime probes.

---

### Task 1: Enforce the portable package boundary

**Files:**
- Modify: `tests/test_skill_metadata.py`
- Delete: `CLAUDE.md`
- Delete: `.claude/commands/check-resume-tailor-setup.md`
- Delete: `.claude/commands/resume-tailor.md`
- Delete: `.claude/commands/check-monkey-resume-setup.md`
- Delete: `.claude/commands/monkey-resume.md`
- Delete: `.opencode/command/install-skill-deps.md`
- Delete: `.opencode/package.json`
- Delete: `.opencode/package-lock.json`
- Delete: `.opencode/.gitignore`
- Delete: `agents/openai.yaml`
- Delete: `install/agent-install.yaml`
- Delete: `scripts/check_agent_platform_support.py`

**Interfaces:**
- Consumes: the existing repository file tree and `SKILL.md` frontmatter
- Produces: a client-neutral package structure verified by `SkillMetadataTests.test_package_has_no_client_specific_adapters`

- [ ] **Step 1: Replace client-metadata assertions with a failing package-boundary test**

```python
def test_package_has_no_client_specific_adapters(self) -> None:
    client_specific_paths = (
        "CLAUDE.md",
        ".claude",
        ".opencode",
        "agents/openai.yaml",
        "install/agent-install.yaml",
        "scripts/check_agent_platform_support.py",
    )
    present = [
        path
        for path in client_specific_paths
        if (self.repo_root / path).exists()
    ]
    self.assertEqual(present, [])
```

- [ ] **Step 2: Run the focused test and verify RED**

Run: `python3 -m unittest tests.test_skill_metadata.SkillMetadataTests.test_package_has_no_client_specific_adapters -v`

Expected: FAIL listing the current client-specific paths.

- [ ] **Step 3: Delete the client-specific adapter files**

Use an explicit patch that removes only the paths listed in this task. Do not remove `AGENTS.md`, tests, CI, requirements, scripts used by the resume workflow, or historical research.

- [ ] **Step 4: Run the focused test and verify GREEN**

Run: `python3 -m unittest tests.test_skill_metadata.SkillMetadataTests.test_package_has_no_client_specific_adapters -v`

Expected: PASS.

### Task 2: Make active development and installation guidance client-neutral

**Files:**
- Modify: `AGENTS.md`
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `docs/guide/installation.md`
- Modify: `references/execution-checklist.md`
- Modify: `.github/workflows/ci.yml`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: the package boundary produced by Task 1
- Produces: shared-directory installation instructions and generic validation commands with no dependency on removed files

- [ ] **Step 1: Update active guidance**

Remove platform names and removed paths from current setup, development, validation, and package-layout sections. Keep the shared install path `~/.agents/skills/monkey-resume`, Ruff, unittest, and format validation.

- [ ] **Step 2: Update CI**

Check out the repository into a `monkey-resume` directory, run the Agent Skills format validator from that package path, then run Ruff and unittest from the same working directory. Remove the deleted platform probe command.

- [ ] **Step 3: Confirm active references are clean**

Run:

```bash
grep -RInE --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=.ruff_cache --exclude-dir=__pycache__ \
  '(CLAUDE\.md|\.claude/|\.opencode/|agents/openai\.yaml|agent-install\.yaml|check_agent_platform_support\.py|Codex-facing)' \
  AGENTS.md README.md README.zh-CN.md docs/guide references SKILL.md .github tests
```

Expected: no active setup, installation, CI, or package-contract reference. Historical implementation plans may be reviewed separately and retained when clearly historical.

### Task 3: Verify the complete package

**Files:**
- Modify only if a verification failure identifies an in-scope defect

**Interfaces:**
- Consumes: the client-neutral package and documentation from Tasks 1–2
- Produces: fresh format, lint, and test evidence

- [ ] **Step 1: Validate the Skill format**

Run the available official validator against a directory named `monkey-resume`. If `skills-ref` is unavailable locally, use the bundled Skill Creator `quick_validate.py` and ensure CI installs/runs the official validator.

Expected: exit 0 and valid frontmatter.

- [ ] **Step 2: Run Ruff**

Run: `ruff check scripts templates tests`

Expected: exit 0 with no lint errors.

- [ ] **Step 3: Run the complete test suite**

Run: `python3 -m unittest discover -s tests -v`

Expected: exit 0 with zero failures and zero errors.

- [ ] **Step 4: Review the final diff**

Run: `git status --short` and `git diff --check`.

Expected: only the approved MonkeyResume rename work, client-neutral package cleanup, design, and plan files remain; whitespace checks pass.
