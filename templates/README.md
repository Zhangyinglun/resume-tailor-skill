# Resume Template - Modern Design

## 概述

`modern_resume_template.py` 是 resume-tailor 的默认 PDF 模板，目标是：
- A4 单页输出
- ATS 友好（文本可提取、结构线性）
- 紧凑且可读（9.5pt 正文）

## 设计特点

- 字体：优先 Calibri，不可用时自动回退 Helvetica
- 头部：姓名与联系方式居中展示
- 结构：Summary → Technical Skills → Professional Experience → Education
- 经历区：第一行 Company（左）与 Dates（右）；第二行 Title | Location

## 页面与排版参数

- 页面：A4 (210mm x 297mm)
- 页边距：上 5mm，下 5mm，左右 0.6in
- 字号：正文 9.5pt，章节标题 10.5pt，姓名 15pt
- 行距：正文 11pt

## 生成方式

### 方式 1：Markdown 工作缓存（推荐）

```bash
py -3 scripts/generate_final_resume.py --input-md cache/resume-working.md --output-file 02_10_Name_Backend_Engineer_resume.pdf --output-dir resume_output
```

### 方式 2：JSON 数据

```bash
py -3 scripts/generate_final_resume.py --input-json resume_content.json --output-file 02_10_Name_Backend_Engineer_resume.pdf --output-dir resume_output
```

## 工作缓存相关脚本

### 长期模板管理（新增）

**一次性初始化长期模板**（首次使用或更新通用简历）：

```bash
py -3 scripts/resume_cache_manager.py template-init --workspace . --input my_full_resume.txt
```

**检查模板是否存在**：

```bash
py -3 scripts/resume_cache_manager.py template-check --workspace .
```

**查看模板内容**：

```bash
py -3 scripts/resume_cache_manager.py template-show --workspace .
```

**按 JD 生成初版简历（简化流程）**：

```text
步骤 1：全量读取 cache/base-resume.md
步骤 2：模型根据 JD 生成初版 cache/resume-working.md
步骤 3：根据问答不断更新 cache/resume-working.md
```

### 临时工作缓存管理

- 初始化缓存：

```bash
py -3 scripts/resume_cache_manager.py init --workspace . --input raw_resume.txt
```

- 更新缓存：

```bash
py -3 scripts/resume_cache_manager.py update --workspace . --input reviewed_resume.md
```

- 清理缓存（可选，手动触发）：

```bash
py -3 scripts/resume_cache_manager.py cleanup --workspace .
```

## 备份策略

每次生成新简历前，`resume_output/` 根目录中已有的 PDF 都会自动移动到：

`resume_output/backup/{Position}/{name}_old_N.pdf`

其中 `{Position}` 从文件名 `{MM}_{DD}_{Name}_{Position}_resume.pdf` 推断，`{name}` 使用原文件名（不含 `.pdf`）。因此生成完成后，`resume_output/` 根目录始终只保留最新一份简历。

## 维护建议

若内容溢出第二页，按以下顺序调整：
1. 段后间距
2. bullet 间距
3. 行距
4. 页边距
5. 字号（不低于 9.5pt）
