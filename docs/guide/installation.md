# Installation Guide

## For Humans

### OpenCode

If you want to manually install `resume-tailor` dependency skills for OpenCode, follow these steps:

1. Install Python dependencies.

```bash
python3 -m pip install -r requirements.txt
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

### Claude Code

If you want to manually install `resume-tailor` dependency skills for Claude Code, follow these steps:

1. Install Python dependencies.

```bash
python3 -m pip install -r requirements.txt
```

2. Pull upstream skill repositories into project-local `_deps/skills/`.

```bash
git clone https://github.com/anthropics/skills _deps/skills/_upstream_anthropic_skills
git clone https://github.com/blader/humanizer _deps/skills/_upstream_humanizer
```

If directories already exist, use instead:

```bash
git -C _deps/skills/_upstream_anthropic_skills pull --ff-only
git -C _deps/skills/_upstream_humanizer pull --ff-only
```

3. Copy skill directories to `_deps/skills/`:

- `_deps/skills/_upstream_anthropic_skills/skills/pdf` → `_deps/skills/pdf`
- `_deps/skills/_upstream_anthropic_skills/skills/docx` → `_deps/skills/docx`
- `_deps/skills/_upstream_humanizer` (repo root) → `_deps/skills/humanizer`

4. Verify installation results:

- `_deps/skills/pdf/SKILL.md` exists
- `_deps/skills/docx/SKILL.md` exists
- `_deps/skills/humanizer/SKILL.md` exists

`humanizer-zh` is not within this project's dependency scope.

## For LLM Agents

If you are an LLM Agent, use this file as installation specification and also read:

- `install/agent-install.yaml`

### Step 0: Preconditions

1. Check command availability: `python3`, `git`. (On Windows non-WSL, use `py -3` instead of `python3`.)
2. Determine the platform profile:
   - **OpenCode**: use `opencode` profile → `skills_dir = ~/.config/opencode/skills`
   - **Claude Code**: use `claude-code` profile → `skills_dir = ./_deps/skills`
3. If skills root directory doesn't exist, create it first.

### Step 1: Install Python dependencies

Execute:

```bash
python3 -m pip install -r requirements.txt
```

### Step 2: Sync upstream repositories (pull-or-clone)

For each source, execute the following strategy:

- If `cache_dir/.git` exists: `git -C <cache_dir> pull --ff-only`
- Otherwise: `git clone <repo> <cache_dir>`

All `<cache_dir>` paths are relative to `<skills_dir>` as defined by the chosen platform profile.

sources:

- `anthropics-skills` → `https://github.com/anthropics/skills`
- `blader-humanizer` → `https://github.com/blader/humanizer`

### Step 3: Install required skills

Copy the following directories to `<skills_dir>/` (overwrite existing directories with same name):

- `<anthropics cache>/skills/pdf` → `<skills_dir>/pdf`
- `<anthropics cache>/skills/docx` → `<skills_dir>/docx`
- `<humanizer cache>` (repo root) → `<skills_dir>/humanizer`

### Step 4: Post-check

Must confirm the following files exist:

- `<skills_dir>/pdf/SKILL.md`
- `<skills_dir>/docx/SKILL.md`
- `<skills_dir>/humanizer/SKILL.md`

And confirm:

- `humanizer-zh` is not installed as a dependency target for this project.

### Step 5: Report

Output installation report, including at least:

1. Python and Git versions
2. Platform profile used (`opencode` or `claude-code`)
3. Sync method for each source (pull or clone)
4. Installation results for `pdf/docx/humanizer`
5. Post-check verification results

### Failure handling

- If any step fails, first do one minimal fix and retry once.
- If still failing after retry, stop process and report failed step, error message, suggested fix action.
- Do not silently skip post-check.
