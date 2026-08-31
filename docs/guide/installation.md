# Installation Guide

## Requirements

Use Python 3.9 or newer:

```bash
python3 -m pip install -r requirements.txt
```

Runtime dependencies include `reportlab` and `pdfplumber`. Keep candidate data and generated output outside the Skill directory.

## Agent Setup

Register MonkeyResume once in the shared Agent Skills directory:

```bash
mkdir -p ~/.agents/skills
ln -s /absolute/path/to/monkey-resume ~/.agents/skills/monkey-resume
```

No dependency Skills are vendored. PDF generation and text extraction use the open-source Python packages declared in `requirements.txt`.

## Agent Skills Format Validation

The official `skills-ref` validator currently requires Python 3.11 or newer. Install it from the Agent Skills specification repository, then validate a checkout or link whose directory name is `monkey-resume`:

```bash
python3.12 -m pip install "git+https://github.com/agentskills/agentskills.git@69ef37e9424c0a7ea9dd2293b559e43ec8176379#subdirectory=skills-ref"
skills-ref validate /absolute/path/to/monkey-resume
```

The validator version is pinned to the same official revision used by CI. MonkeyResume itself continues to support Python 3.9 and newer.

## Development Validation

```bash
python3 -m pip install -r requirements-dev.txt
skills-ref validate "$PWD"
ruff check scripts templates tests
python3 -m unittest discover -s tests -v
```
