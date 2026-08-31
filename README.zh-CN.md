# resume-tailor

[English](README.md)

一个用于个人简历优化的 AI Skill：根据 JD 或目标方向，在不捏造事实的前提下改写简历，并输出经过校验的单页 A4 PDF。

## 安装

需要 Python 3.9 或更高版本。

```bash
git clone https://github.com/Zhangyinglun/resume-tailor-skill.git
cd resume-tailor-skill
python3 -m pip install -r requirements.txt
python3 scripts/check_agent_platform_support.py
```

注册到 Agent：

| 平台 | 安装位置或使用方式 |
|---|---|
| Codex | 复制到 `$CODEX_HOME/skills/resume-tailor/`；默认目录是 `~/.codex/skills/resume-tailor/`。 |
| Claude Code | 打开本仓库以加载 `CLAUDE.md`，并使用独立目录保存个人简历数据。 |
| OpenCode | 复制到 `~/.config/opencode/skills/resume-tailor/`。 |

## 使用

提供现有简历以及 JD 或目标方向，然后说：

```text
使用 $resume-tailor 根据这个岗位优化我的简历，并生成经过校验的单页 PDF。
```

个人数据只保存在当前用户工作区：

```text
cache/base-resume.json             不可变 Source Snapshot
cache/candidate-evidence.json       跨 JD 长期事实账本
cache/candidate-profile.json        长期展示偏好
cache/jd-analysis.json              双轴 JD 能力分析
cache/resume-working.json           当前定制简历投影
cache/resume-changes.json           全字段 Tailoring Manifest
resume_output/
```

运行脚本时，从 Skill 安装目录调用脚本，并明确传入用户工作区。Skill 包本身不保存个人运行数据。

## 安全保证

- 不捏造经历、职责、技术、日期或指标。
- 跨 JD 复用候选人已确认事实，让追问逐次减少。
- PDF 渲染前强制执行全字段 Manifest 与事实审计。
- 自动排版只调整布局；PDF QA 使用真实渲染坐标。
- PDF 先在临时目录生成，所有阻断门禁通过后才发布。
- 新候选失败时保留上一份合格 PDF；失败候选进入 `resume_output/rejected/`。
- 默认输出单页 A4、可提取文本的 PDF。

## 开发验证

```bash
python3 -m pip install -r requirements-dev.txt
ruff check scripts templates tests
python3 -m unittest discover -s tests -v
python3 /path/to/skill-creator/scripts/quick_validate.py .
```

## 许可证

MIT。第三方 Python 包通过 `requirements.txt` 单独安装，不再复制到本仓库中。
