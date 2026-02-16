# resume-working.md 结构规范

工作缓存文件路径：`cache/resume-working.md`

说明：
- 该文件是“当前简历内容唯一真源”。
- 所有迭代修改、QA 预览、最终导出都基于该文件。
- 会话启动时先清理旧缓存；生成后保留当前缓存，供后续继续迭代。

## 固定结构

```markdown
# HEADER
Name: FULL NAME
Contact: City, State | Phone | Email | LinkedIn

## SUMMARY
Summary sentence 1. Summary sentence 2.

## TECHNICAL SKILLS
- Programming Languages: Python, Go, Java
- Cloud & DevOps: AWS, Kubernetes

## PROFESSIONAL EXPERIENCE
### Company | Title | Location | Dates
- Bullet 1
- Bullet 2

## EDUCATION
- School | Degree | Dates
```

## 约束

- 标题必须是以下 5 个区块：
  - `# HEADER`
  - `## SUMMARY`
  - `## TECHNICAL SKILLS`
  - `## PROFESSIONAL EXPERIENCE`
  - `## EDUCATION`
- Experience 使用三级标题 `###` 表示单个经历条目。
- Education 使用 `- School | Degree | Dates` 单行结构。
- Skills 使用 `- Category: items` 结构。
- 不允许在缓存文件中插入与简历无关的分析文本。
