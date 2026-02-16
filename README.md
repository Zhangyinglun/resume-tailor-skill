# resume-tailor

`resume-tailor` 是一个用于岗位定向简历优化的独立 Skill 项目。

它的目标是：在不编造经历的前提下，根据目标 JD 对现有简历进行关键词对齐、表达优化与篇幅收敛，并最终交付 ATS 友好的 PDF 简历。

## 目录结构

- `SKILL.md`：Skill 主说明与工作流约束
- `scripts/`：缓存管理、Markdown 转换、PDF 生成与质检脚本
- `references/`：ATS 策略与缓存结构参考
- `templates/`：PDF 排版模板
- `tests/`：核心脚本行为测试
- `docs/guide/installation.md`：Agent 与人工统一安装指南
- `install/agent-install.yaml`：Agent 机器可读安装清单
- `.opencode/command/install-skill-deps.md`：OpenCode 命令化安装入口

## 本地安装到 OpenCode

1. 克隆本仓库。
2. 将仓库目录放到（或软链接到）本机 skills 目录：

```bash
~/.config/opencode/skills/resume-tailor
```

3. 安装 Python 依赖：

```bash
py -3 -m pip install -r requirements.txt
```

4. 重启 OpenCode 会话后即可按技能描述触发使用。

## 依赖与协作技能

- `pdf`：读取与生成 PDF
- `docx`：读取 `.docx` 简历
- `humanizer`：去除 AI 痕迹表达

来源说明：
- `pdf`、`docx` 来自 `https://github.com/anthropics/skills`
- `humanizer` 来自 `https://github.com/blader/humanizer`

请确保以上协作技能已安装到 OpenCode 技能目录，否则相关流程会在调用阶段失败。

## Agent 自动安装（类似 oh-my-opencode）

推荐把下面这句话直接发给 Agent：

```text
请读取并严格执行 docs/guide/installation.md，完成 resume-tailor 依赖技能安装与验证。
```

若在 GitHub 远程仓库使用，可给 Agent 传 raw 链接：

```text
https://raw.githubusercontent.com/<owner>/<repo>/<branch>/docs/guide/installation.md
```

仓库内提供两个安装模块，供 Agent 直接读取执行：

- `docs/guide/installation.md`：面向 Agent 的可执行安装流程（含失败重试与验收）
- `install/agent-install.yaml`：机器可读安装清单（repo 来源、pull-or-clone 策略、post-check）

如果你使用 OpenCode 命令体系，也可以直接让 Agent 执行：

```text
/install-skill-deps
```

## Python 依赖

- `reportlab`：PDF 生成
- `pdfplumber`：PDF 质量检查
- `pytest`：测试执行

依赖统一维护在 `requirements.txt`。

## 开发与验证

在项目根目录可运行：

```bash
pytest
```

如需验证脚本行为，也可以单独运行 `scripts/` 下工具。

## 字体与跨平台说明

- 模板优先使用 Windows 的 Calibri 字体。
- 若当前系统不存在 Calibri，将自动回退到 Helvetica，不影响 PDF 生成。
- 若你需要固定字体效果，建议在目标系统安装等价字体后再导出。

## 开源发布建议

- 提交前确认不包含个人隐私数据（联系方式、真实简历样本等）。
- 仅保留可复用的规则、脚本、模板与参考资料。
- 已提供 `LICENSE`（MIT），可按需要补充发布标签，便于后续公开维护。
