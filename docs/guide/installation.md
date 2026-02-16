# Installation Guide

## For Humans

If you want to manually install `resume-tailor` dependency skills, follow these steps:

1. Install Python dependencies.

```bash
py -3 -m pip install -r requirements.txt
```

2. Pull upstream skill repositories.

```bash
git clone https://github.com/anthropics/skills ~/.config/opencode/skills/_upstream_anthropic_skills
git clone https://github.com/blader/humanizer ~/.config/opencode/skills/_upstream_humanizer
```

If directories already exist, use instead:

```bash
git -C ~/.config/opencode/skills/_upstream_anthropic_skills pull --ff-only
git -C ~/.config/opencode/skills/_upstream_humanizer pull --ff-only
```

3. Copy or symlink skill directories to OpenCode skills directory:

- `pdf`
- `docx`
- `humanizer`

4. Verify installation results:

- `~/.config/opencode/skills/pdf/SKILL.md` exists
- `~/.config/opencode/skills/docx/SKILL.md` exists
- `~/.config/opencode/skills/humanizer/SKILL.md` exists

`humanizer-zh` is not within this project's dependency scope.

## For LLM Agents

If you are an LLM Agent, use this file as installation specification and also read:

- `install/agent-install.yaml`

### Step 0: Preconditions

1. Check command availability: `py -3`, `git`.
2. If OpenCode skills root directory doesn't exist, first create `~/.config/opencode/skills`.

### Step 1: Install Python dependencies

Execute:

```bash
py -3 -m pip install -r requirements.txt
```

### Step 2: Sync upstream repositories (pull-or-clone)

For each source, execute the following strategy:

- If `cache_dir/.git` exists: `git -C <cache_dir> pull --ff-only`
- Otherwise: `git clone <repo> <cache_dir>`

sources:

- `anthropics-skills` → `https://github.com/anthropics/skills`
- `blader-humanizer` → `https://github.com/blader/humanizer`

### Step 3: Install required skills

Copy the following directories to `~/.config/opencode/skills/` (overwrite existing directories with same name):

- `<anthropics cache>/pdf` → `~/.config/opencode/skills/pdf`
- `<anthropics cache>/docx` → `~/.config/opencode/skills/docx`
- `<humanizer cache>/humanizer` → `~/.config/opencode/skills/humanizer`

### Step 4: Post-check

Must confirm the following files exist:

- `~/.config/opencode/skills/pdf/SKILL.md`
- `~/.config/opencode/skills/docx/SKILL.md`
- `~/.config/opencode/skills/humanizer/SKILL.md`

And confirm:

- `humanizer-zh` is not installed as a dependency target for this project.

### Step 5: Report

Output installation report, including at least:

1. Python and Git versions
2. Sync method for each source (pull or clone)
3. Installation results for `pdf/docx/humanizer`
4. Post-check verification results

### Failure handling

- If any step fails, first do one minimal fix and retry once.
- If still failing after retry, stop process and report failed step, error message, suggested fix action.
- Do not silently skip post-check.
