# Installation Guide

## For Humans

如果你希望手动安装 `resume-tailor` 依赖技能，请按以下步骤执行：

1. 安装 Python 依赖。

```bash
py -3 -m pip install -r requirements.txt
```

2. 拉取上游技能仓库。

```bash
git clone https://github.com/anthropics/skills ~/.config/opencode/skills/_upstream_anthropic_skills
git clone https://github.com/blader/humanizer ~/.config/opencode/skills/_upstream_humanizer
```

若目录已存在，请改用：

```bash
git -C ~/.config/opencode/skills/_upstream_anthropic_skills pull --ff-only
git -C ~/.config/opencode/skills/_upstream_humanizer pull --ff-only
```

3. 将技能目录复制或软链接到 OpenCode skills 目录：

- `pdf`
- `docx`
- `humanizer`

4. 验证安装结果：

- `~/.config/opencode/skills/pdf/SKILL.md` 存在
- `~/.config/opencode/skills/docx/SKILL.md` 存在
- `~/.config/opencode/skills/humanizer/SKILL.md` 存在

`humanizer-zh` 不在本项目依赖范围内。

## For LLM Agents

如果你是 LLM Agent，请把本文件作为安装规范执行，并同时读取：

- `install/agent-install.yaml`

### Step 0: Preconditions

1. 检查命令可用：`py -3`、`git`。
2. 若 OpenCode skills 根目录不存在，先创建 `~/.config/opencode/skills`。

### Step 1: Install Python dependencies

执行：

```bash
py -3 -m pip install -r requirements.txt
```

### Step 2: Sync upstream repositories (pull-or-clone)

对每个 source 执行以下策略：

- 若 `cache_dir/.git` 存在：`git -C <cache_dir> pull --ff-only`
- 否则：`git clone <repo> <cache_dir>`

sources:

- `anthropics-skills` → `https://github.com/anthropics/skills`
- `blader-humanizer` → `https://github.com/blader/humanizer`

### Step 3: Install required skills

将以下目录复制到 `~/.config/opencode/skills/`（覆盖同名旧目录）：

- `<anthropics cache>/pdf` → `~/.config/opencode/skills/pdf`
- `<anthropics cache>/docx` → `~/.config/opencode/skills/docx`
- `<humanizer cache>/humanizer` → `~/.config/opencode/skills/humanizer`

### Step 4: Post-check

必须确认以下文件存在：

- `~/.config/opencode/skills/pdf/SKILL.md`
- `~/.config/opencode/skills/docx/SKILL.md`
- `~/.config/opencode/skills/humanizer/SKILL.md`

并确认：

- `humanizer-zh` 不作为本项目依赖安装目标。

### Step 5: Report

输出安装报告，至少包含：

1. Python 与 Git 版本
2. 每个 source 的同步方式（pull 或 clone）
3. `pdf/docx/humanizer` 安装结果
4. post-check 验证结果

### Failure handling

- 任一步骤失败时，先做一次最小修复并重试一次。
- 重试后仍失败时，停止流程并报告失败步骤、错误信息、建议修复动作。
- 禁止静默跳过 post-check。
