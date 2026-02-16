# resume-tailor

`resume-tailor` 是一个用于岗位定向简历优化的独立 Skill 项目。

它的目标是：在不编造经历的前提下，根据目标 JD 对现有简历进行关键词对齐、表达优化与篇幅收敛，并最终交付 ATS 友好的 PDF 简历。

## 目录结构

- `SKILL.md`：Skill 主说明与工作流约束
- `scripts/`：缓存管理、Markdown 转换、PDF 生成与质检脚本
- `references/`：ATS 策略与缓存结构参考
- `templates/`：PDF 排版模板
- `tests/`：核心脚本行为测试

## 本地安装到 OpenCode

1. 克隆本仓库。
2. 将仓库目录放到（或软链接到）本机 skills 目录：

```bash
~/.config/opencode/skills/resume-tailor
```

3. 重启 OpenCode 会话后即可按技能描述触发使用。

## 依赖与协作技能

- `pdf`：读取与生成 PDF
- `docx`：读取 `.docx` 简历
- `humanizer` / `humanizer-zh`：去除 AI 痕迹表达

## 开发与验证

在项目根目录可运行：

```bash
pytest
```

如需验证脚本行为，也可以单独运行 `scripts/` 下工具。

## 开源发布建议

- 提交前确认不包含个人隐私数据（联系方式、真实简历样本等）。
- 仅保留可复用的规则、脚本、模板与参考资料。
- 可按需要补充 `LICENSE` 与发布标签，便于后续公开维护。
