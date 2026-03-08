# resume-tailor

[English](README.md)

`resume-tailor` 是一个面向岗位定制简历的 Python 工具集，同时也提供给 OpenCode / Claude Code 这类 agent 使用的技能工作流。它的目标是把基础简历整理成 ATS 友好、单页 A4、可投递的 PDF。

它主要包含：

- 工作区级别的简历缓存管理
- 基于 ReportLab 的 PDF 生成
- PDF 质量检查
- 内容质量检查
- 只调版式、不改语义的 auto-fit 自动调参

## 核心能力

- 围绕目标 JD 或岗位方向改写简历内容
- 维护长期复用的基础模板 `cache/base-resume.json`
- 为每次投递生成工作副本 `cache/resume-working.json`
- 输出单页 A4、文本可提取的 PDF
- 自动检查页数、尺寸、边距、文本层、占位符、模块完整性、联系方式等问题
- 支持 layout auto-fit，在不改内容的前提下搜索更合适的版式参数
- 将历史 PDF 自动归档到 `resume_output/backup/{Position}/`

## 仓库结构

```text
resume-tailor/
|-- README.md
|-- README.zh-CN.md
|-- SKILL.md
|-- AGENTS.md
|-- scripts/
|   |-- resume_cache_manager.py
|   |-- generate_final_resume.py
|   |-- check_pdf_quality.py
|   |-- check_content_quality.py
|   |-- layout_auto_tuner.py
|   `-- resume_shared.py
|-- templates/
|   |-- modern_resume_template.py
|   |-- layout_settings.py
|   |-- design_tokens.py
|   `-- README.md
|-- references/
|-- tests/
|-- docs/guide/
`-- vendor/skills/
```

## 安装

```bash
python3 -m pip install -r requirements.txt
```

依赖很少，主要是：

- `reportlab`：PDF 生成
- `pdfplumber`：PDF 质检
- `pytest`：测试执行

仓库已经内联了依赖技能，不需要额外安装：

- `vendor/skills/pdf`
- `vendor/skills/docx`
- `vendor/skills/humanizer`

## 快速开始

### 1. 重置工作缓存

```bash
python3 scripts/resume_cache_manager.py reset
```

### 2. 从纯文本简历初始化长期模板

```bash
python3 scripts/resume_cache_manager.py template-init --workspace . --input raw_resume.txt
```

说明：

- `template-init` 接收的是提取后的纯文本简历。
- 如果你的原始简历是 PDF 或 DOCX，先走 `vendor/skills/pdf` 或 `vendor/skills/docx` 的读取流程，再导入文本。

### 3. 从模板生成工作副本

```bash
python3 scripts/resume_cache_manager.py template-use --workspace .
```

这一步会在工作区里维护两份关键文件：

- `cache/base-resume.json`：长期基线模板
- `cache/resume-working.json`：当前投递版本

### 4. 生成 PDF

```bash
python3 scripts/generate_final_resume.py --input-json cache/resume-working.json --output-file 02_10_Name_Backend_Engineer_resume.pdf --output-dir resume_output
```

### 5. 使用 auto-fit 自动调版

```bash
python3 scripts/generate_final_resume.py --input-json cache/resume-working.json --output-file 02_10_Name_Backend_Engineer_resume.pdf --output-dir resume_output --auto-fit
```

`--auto-fit` 只会调整版式参数：

- 字号缩放
- 行高缩放
- 模块间距缩放
- 条目间距缩放
- 页边距

不会改写简历内容。

### 6. 运行 PDF 质量检查

```bash
python3 scripts/check_pdf_quality.py resume_output/02_10_Name_Backend_Engineer_resume.pdf
```

也支持 JSON 输出：

```bash
python3 scripts/check_pdf_quality.py resume_output/02_10_Name_Backend_Engineer_resume.pdf --json
```

## 典型工作流

如果是 agent 驱动，推荐按这个顺序执行：

1. 清理旧的 working cache。
2. 检查 `cache/base-resume.json` 是否存在。
3. 如果不存在，就从用户提供的简历文本初始化模板。
4. 用 `template-use` 生成 `cache/resume-working.json`。
5. 分析 JD，并把结构化结果写入 `cache/jd-analysis.json`。
6. 按目标岗位修改 working cache。
7. 跑内容质量检查，并把内容压缩到单页体量。
8. 生成 PDF，优先使用 `--auto-fit`。
9. 跑 PDF QA，并交付最终文件的绝对路径。

常用命令：

```bash
# 检查模板是否存在
python3 scripts/resume_cache_manager.py template-check --workspace .

# 查看当前 working cache
python3 scripts/resume_cache_manager.py show --workspace .

# 查看模板内容
python3 scripts/resume_cache_manager.py template-show --workspace .

# 查看 JD 分析缓存
python3 scripts/resume_cache_manager.py jd-show --workspace .

# 对比 working cache 与模板差异
python3 scripts/resume_cache_manager.py diff --workspace .

# 用 JSON 更新 working cache
python3 scripts/resume_cache_manager.py update --workspace . --input reviewed_resume.json

# 保存 JD 分析结果
python3 scripts/resume_cache_manager.py jd-save --workspace . --input jd_analysis.json
```

## PDF 生成说明

- 输出固定为 A4。
- 模板目标是单页交付。
- PDF 文本可提取，便于 ATS 读取。
- 默认优先使用 Windows 上的 Calibri，缺失时回退到 Helvetica。
- 当 QA 通过时，旧的根目录 PDF 会被移动到 `resume_output/backup/{Position}/`。
- 当 QA 未通过时，旧的根目录 PDF 会被删除，不进入归档。

## 质量检查

### PDF QA

`scripts/check_pdf_quality.py` 会检查：

- 页数
- A4 尺寸
- 文本层是否可提取
- 是否有 HTML 标签泄漏
- 是否残留占位符
- 上下左右边距
- Summary / Skills / Experience / Education 是否齐全
- 联系方式是否完整
- 可选的关键词覆盖情况
- 版式预警

### 内容 QA

`scripts/check_content_quality.py` 会检查：

- bullet 是否过长
- bullet 是否以强动词开头
- 量化比例是否足够
- 是否重复出现高频 3-gram
- experience bullet 数量是否合理

示例：

```bash
python3 scripts/check_content_quality.py cache/resume-working.json
python3 scripts/check_content_quality.py cache/resume-working.json --json
```

## 测试

优先使用 `python3 -m pytest`，不要直接用 `pytest`，这样可以避免导入路径问题。

```bash
python3 -m pytest -q
```

常见定向命令：

```bash
python3 -m pytest tests/test_resume_cache_flow.py -q
python3 -m pytest tests/test_resume_cache_flow.py::ResumeCacheFlowTest::test_base_template_lifecycle -q
python3 -m pytest tests/test_generate_final_resume_cli_args.py::GenerateFinalResumeCliArgsTest::test_parse_args_layout_defaults -q
python3 -m pytest -k "layout and not auto" -q
python3 -m pytest --lf -q
```

可选 lint：

```bash
python3 -m ruff check scripts templates tests
```

## 工作区数据与隐私

这个仓库本身不应该保存用户个性化简历数据。运行时数据应放在工作区中，而不是版本库中：

- `cache/`
- `resume_output/`

仓库的 `.gitignore` 已排除常见运行产物，例如：

- `cache/`
- `resume_output/**/*.pdf`
- 根目录生成的 PDF

## 常见问题

### auto-fit 会不会改写简历内容？

不会。`--auto-fit` 只搜索版式候选并调整渲染参数。

### 可以直接从 PDF 或 DOCX 开始吗？

可以，但 `init` 和 `template-init` 期待的是纯文本输入。先通过内联的 `pdf` 或 `docx` 技能把内容提取出来，再导入缓存。

### 历史 PDF 存在哪里？

成功生成后的旧版本会移动到：

```text
resume_output/backup/{Position}/
```

文件名类似：

```text
02_10_Name_Backend_Engineer_resume_old_1.pdf
```

### 哪几个文件是主要入口？

- `scripts/resume_cache_manager.py`
- `scripts/generate_final_resume.py`
- `scripts/check_pdf_quality.py`
- `scripts/check_content_quality.py`
- `templates/modern_resume_template.py`

## 相关文档

- [SKILL.md](SKILL.md)
- [AGENTS.md](AGENTS.md)
- [templates/README.md](templates/README.md)
- [docs/guide/installation.md](docs/guide/installation.md)
- [references/execution-checklist.md](references/execution-checklist.md)

## License

MIT，见 [LICENSE](LICENSE)。
