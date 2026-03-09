# resume-tailor

[中文说明](README.zh-CN.md)

A distributable **AI skill** for Claude Code, Codex, and OpenCode. Give it your resume + a JD — it delivers an ATS-optimized single-page A4 PDF.

---

## 1-Minute Quickstart

### Step 1 — Install

```bash
git clone https://github.com/your-org/resume-tailor-skill
cd resume-tailor-skill
python3 -m pip install -r requirements.txt
```

### Step 2 — Register with your AI agent

| Platform | What to do |
|---|---|
| **Claude Code** | Open this repo in Claude Code. Done — `CLAUDE.md` auto-loads. |
| **Codex** | Copy repo to `~/.agents/skills/resume-tailor/` |
| **OpenCode** | Copy repo to `~/.config/opencode/skills/resume-tailor/` |

### Step 3 — Use it

Paste your JD and resume into the chat and say:

```
Tailor my resume for this JD and output a single-page PDF.
```

The agent handles everything: keyword alignment, content rewrite, layout, and PDF delivery.

---

## How It Works

```
You provide: existing resume + target JD
      │
      ▼
[A] Initialize workspace cache
      │
      ▼
[B] Analyze JD → rewrite bullets (no fabrication)
      │
      ▼
[C] Volume gate → compress to 1 page → humanize language
      │
      ▼
[D] Generate PDF → quality check → deliver with summary report
```

The skill is **stateless** — your data stays in your workspace's `cache/` and `resume_output/` folders, never inside the skill package.

---

## Repository Layout

```
resume-tailor/
├── SKILL.md                   # Main skill definition (agent reads this)
├── CLAUDE.md                  # Claude Code auto-load config
├── AGENTS.md                  # Codex entry point
├── requirements.txt
├── scripts/                   # resume_cache_manager.py, generate_final_resume.py, ...
├── templates/                 # .docx base template (Calibri / Helvetica fallback)
├── references/                # Optimization action codes, schema notes, prompt helpers
├── vendor/skills/             # Bundled dependencies: pdf, docx, humanizer
├── .claude/commands/          # /resume-tailor and /check-resume-tailor-setup
├── .opencode/command/
└── docs/guide/installation.md
```

---

## Verify Installation

```bash
python3 scripts/check_agent_platform_support.py
```

Optional lint:

## Key Constraints

- **No fabrication** — only rewrites and rearranges what you actually have.
- **`--auto-fit`** only adjusts layout parameters, never rewrites content.
- Output is always A4, one page, extractable-text PDF.

## License

MIT. See `LICENSE`.
