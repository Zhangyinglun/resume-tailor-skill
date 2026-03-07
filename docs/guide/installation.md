# Installation Guide

## Python Dependencies

```bash
python3 -m pip install -r requirements.txt
```

On Windows (non-WSL), use `py -3` instead of `python3`.

## Bundled Skills

All dependent skills (`pdf`, `docx`, `humanizer`) are bundled in the `vendor/skills/` directory and distributed with the project. No separate installation or cloning is required.

To verify:

- `vendor/skills/pdf/SKILL.md` exists
- `vendor/skills/docx/SKILL.md` exists
- `vendor/skills/humanizer/SKILL.md` exists
