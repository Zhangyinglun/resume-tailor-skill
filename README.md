# resume-tailor

[中文说明](README.zh-CN.md)

A personal AI Skill for truthfully tailoring a resume to a job description or target role and delivering a verified single-page A4 PDF.

## Install

Requires Python 3.9 or newer.

```bash
git clone https://github.com/Zhangyinglun/resume-tailor-skill.git
cd resume-tailor-skill
python3 -m pip install -r requirements.txt
python3 scripts/check_agent_platform_support.py
```

Register the repository with your agent:

| Platform | Location or workflow |
|---|---|
| Codex | Copy to `$CODEX_HOME/skills/resume-tailor/`; the default is `~/.codex/skills/resume-tailor/`. |
| Claude Code | Open this repository so `CLAUDE.md` is loaded. Use a separate directory as the personal resume workspace. |
| OpenCode | Copy to `~/.config/opencode/skills/resume-tailor/`. |

## Use

Provide an existing resume plus a JD or target direction, then ask:

```text
Use $resume-tailor to tailor my resume for this role and generate a verified single-page PDF.
```

The Skill keeps personal data in the active user workspace:

```text
cache/base-resume.json             immutable Source Snapshot
cache/candidate-evidence.json       cross-JD Candidate Evidence Ledger
cache/candidate-profile.json        long-term presentation preferences
cache/jd-analysis.json              dual-axis JD Capability analysis
cache/resume-working.json           current Tailored Resume projection
cache/resume-changes.json           field-level Tailoring Manifest
resume_output/
```

Run bundled scripts from the installed Skill directory while passing the user workspace explicitly. The package directory itself remains free of personal runtime data.

## Safety Model

- Never fabricate experience, ownership, tools, dates, or metrics.
- Reuse prior candidate-confirmed evidence across JDs so clarification questions decrease over time.
- Require a complete field-level manifest and factual audit before rendering.
- Auto-fit changes layout only; PDF QA uses rendered word coordinates.
- Generate into a staging directory and publish only after all blocking gates pass.
- Preserve accepted PDFs when a new candidate fails; rejected candidates go to `resume_output/rejected/`.
- Produce A4, one-page, extractable-text output by default.

## Development Checks

```bash
python3 -m pip install -r requirements-dev.txt
ruff check scripts templates tests
python3 -m unittest discover -s tests -v
python3 /path/to/skill-creator/scripts/quick_validate.py .
```

Core package layout:

```text
SKILL.md                 Agent workflow
agents/openai.yaml       Codex UI metadata
scripts/                 Cache, extraction, quality, and PDF tools
templates/               ReportLab PDF layout
references/              Conditional workflow guidance
```

## License

MIT. Third-party Python packages are installed separately through `requirements.txt` and are not vendored in this repository.
