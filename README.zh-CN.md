# MonkeyResume

[English](README.md)

**基于证据定制简历，让每项声明可追溯，并交付经过校验的 PDF。**

MonkeyResume 是一个开源 Agent Skill。它根据候选人的真实经历生成岗位定制简历，同时避免虚构技能、职责、指标或成果。证据、内容规划、语言优化、排版和发布被拆分成明确阶段，因此每一项实质性简历声明都可以复核。

## 为什么使用 MonkeyResume

多数 AI 简历工具先改写，再检查是否准确。MonkeyResume 先建立可长期复用的事实账本；任何无法追溯到有效证据的声明都会阻断发布。

- **先证据，后措辞**——候选人事实保存在跨 JD 的 Evidence Ledger 中，带有原始摘录和验证状态。
- **根据 JD 选择内容**——先把岗位要求区分为直接匹配、语义等价、可迁移或无证据，再开始写作。
- **限制生成边界**——模型根据绑定证据的 Content Intent 写作，而不是自由发挥整份简历。
- **变更可审计**——字段级 Manifest 将新增、改写、合并和删除映射回 Claim ID，并保留原因。
- **交付受保护**——事实、内容、PDF 和页面几何门禁全部通过后，候选文件才能替换上一份合格简历。

## 工作流程

1. **保存来源**——从 PDF、DOCX、Markdown 或文本简历提取不可变 Source Snapshot。
2. **建立事实账本**——将经历规范化为绑定实体的 Atomic Claims，并跨 JD 保留候选人确认的信息。
3. **分析目标岗位**——把 JD Capability 映射到证据，明确真实缺口，只追问高价值问题。
4. **规划与写作**——Projection Plan 先决定证据和篇幅，再生成简洁、面向招聘者且不扩大事实范围的语言。
5. **审计与发布**——检查事实追溯关系、渲染 PDF、测量页面几何，仅在所有阻断门禁通过后发布。

## 快速开始

MonkeyResume 需要 Python 3.9 或更高版本。

GitHub 仓库在改名过渡期间仍使用旧 URL。克隆时直接指定新的本地目录名：

```bash
git clone https://github.com/Zhangyinglun/resume-tailor-skill.git ~/Projects/monkey-resume
cd ~/Projects/monkey-resume
python3 -m pip install -r requirements.txt
```

将仓库注册到统一的 Agent Skills 公共目录：

```bash
mkdir -p ~/.agents/skills
ln -s ~/Projects/monkey-resume ~/.agents/skills/monkey-resume
```

然后提供现有简历以及 JD 或目标方向：

```text
使用 $monkey-resume 根据这个岗位定制我的简历，并生成经过校验的单页 PDF。
```

## 个人数据与 Skill 分离

MonkeyResume 是可复用的软件包。候选人数据和生成文件必须保存在单独的用户工作区，并通过参数显式传给脚本。

```text
USER_WORKSPACE/
├── cache/
│   ├── base-resume.json          不可变 Source Snapshot
│   ├── candidate-evidence.json   跨 JD Candidate Evidence Ledger
│   ├── candidate-profile.json    长期展示偏好
│   ├── jd-analysis.json          双轴 JD Capability 分析
│   ├── projection-plan.json      绑定证据的内容决策
│   ├── projection-language.json  各 Content Intent 的最终语言
│   ├── resume-working.json       当前 Tailored Resume 投影
│   └── resume-changes.json       字段级 Tailoring Manifest
└── resume_output/
```

Skill 仓库保存可复用的运行资源，以及用于维护它们的通用文档、测试和 CI。

## 安全与质量门禁

- 候选人证据是事实依据；JD 只能改变表达重点，不能改变经历。
- 无证据的岗位要求保留为 Gap，不会变成虚构的简历声明。
- 每个实质性投影字段都必须绑定同一 Evidence Entity 下的有效证据。
- 渲染前执行事实完整性审计，最终生成命令会再次执行同一审计。
- 内容修订次数有限且有明确记录；自动排版只调整间距、边距和字号。
- PDF 先在暂存目录生成，通过可提取文本和单页 A4 几何检查后再以事务方式发布。
- 失败候选保存在 `resume_output/rejected/`，不会覆盖上一份 Accepted Resume。
- Host Agent 必须检查实际渲染页面，之后才能把 PDF 报告为视觉验证通过。

## 项目结构

```text
SKILL.md                 Agent 工作流与发布契约
AGENTS.md                客户端中立的仓库开发规则
scripts/                 证据、投影、审计与 PDF 工具
templates/               ReportLab 排版与设计参数
references/              Schema 与按需加载的工作流说明
tests/                   回归与端到端测试
```

## 开发验证

安装开发依赖并运行完整验证：

```bash
python3 -m pip install -r requirements-dev.txt
skills-ref validate .
ruff check scripts templates tests
python3 -m unittest discover -s tests -v
```

修改证据、投影或 Manifest 行为前，请先阅读[安装说明](docs/guide/installation.md)和[领域模型](CONTEXT.md)。

## 许可证

MIT。第三方 Python 包通过 `requirements.txt` 单独安装，不复制到本仓库中。
