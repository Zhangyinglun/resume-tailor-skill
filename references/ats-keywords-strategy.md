# ATS 关键词匹配策略

## ATS 工作原理

ATS（Applicant Tracking System）通过以下方式筛选简历：

1. **关键词匹配**：将简历文本与 JD 中的关键词进行精确/模糊匹配
2. **频次统计**：关键词出现次数越多，得分越高（但不要堆砌）
3. **上下文分析**：高级 ATS 会分析关键词出现的上下文（如在哪个模块、与什么动词搭配）
4. **格式解析**：提取结构化信息（姓名、联系方式、学历、工作经历等）

## 关键词提取方法

### 从 JD 中提取关键词的优先级

1. **岗位标题中的词**：权重最高（如 "Senior Backend Engineer" → Backend, Engineer）
2. **Requirements / Qualifications 中的词**：核心硬性要求
3. **Responsibilities 中反复出现的词**：岗位核心职责
4. **Preferred / Nice-to-have 中的词**：加分项，有则加，没有不勉强
5. **公司描述中的行业术语**：体现行业认知

### 关键词分类

| 类别 | 提取策略 | 嵌入策略 |
|------|---------|---------|
| **硬技能（技术栈）** | 直接提取技术名词：Python, React, AWS, SQL 等 | 放入 Skills 模块 + 在经历描述中自然提及 |
| **软技能** | 提取能力描述：leadership, communication, problem-solving | 通过具体事例体现，不要直接罗列 |
| **行业术语** | 提取领域专有词：CI/CD, microservices, agile, scrum | 在经历描述中使用 JD 原词替换通用表述 |
| **工具/平台** | 提取具体工具名：Jira, Confluence, Figma, Terraform | 放入 Skills 或在项目描述中提及 |
| **学历/证书** | 提取明确要求：Bachelor's, Master's, PMP, CKA | 放入 Education / Certifications 模块 |
| **量化指标** | 提取数字相关描述：team of 5+, 99.9% uptime | 在经历描述中用数据呼应 |

## 关键词嵌入策略

### 原则

1. **自然融入**：关键词必须出现在有意义的句子中，不能堆砌
2. **多位置分布**：同一关键词在 Skills 和 Experience 中各出现一次，效果优于在一处出现两次
3. **精确匹配优先**：使用 JD 中的原词原拼写（如 JD 写 "Kubernetes" 就不要写 "K8s"）
4. **同义词补充**：在精确匹配基础上，可以补充常见同义词/缩写（如同时写 "Amazon Web Services (AWS)"）

### 嵌入位置优先级

1. **Skills 模块**：直接列出所有匹配的技术/工具关键词
2. **Experience 模块**：在成就描述中自然使用关键词
3. **Summary 模块**：用 2-3 句话概括核心匹配点
4. **Projects 模块**：补充覆盖 Skills/Experience 未能涵盖的关键词

### 成就描述公式（四要素）

```
[强动词] + [做了什么（嵌入关键词）] + [使用方法/工具] + [量化结果]
```

要素说明：
- **Action**：使用强动词开头，体现主动贡献与职责级别。
- **What**：明确做了什么，并自然嵌入 JD 关键词与核心场景。
- **How**：补充使用的方法、流程或工具（如框架、平台、协作机制）。
- **Result**：给出可量化结果（效率、质量、成本、营收、稳定性等）。

示例：
- "Designed microservices for payment APIs aligned with scalability requirements, using Python/FastAPI and domain-driven design, reducing P95 latency by 40%"
- "Led a 6-engineer DevOps initiative for CI/CD reliability goals, using Jenkins, Terraform, and blue-green deployment, increasing deployment success rate to 99.9%"
- "Optimized user growth experiment workflows for A/B testing operations, using SQL, Python, and Tableau dashboards, cutting analysis cycle time by 35%"

### 强动词列表（按场景）

| 场景 | 推荐动词 |
|------|---------|
| 开发/构建 | Developed, Built, Implemented, Engineered, Architected |
| 优化/改进 | Optimized, Improved, Enhanced, Streamlined, Refactored |
| 领导/管理 | Led, Managed, Directed, Coordinated, Mentored |
| 分析/研究 | Analyzed, Evaluated, Assessed, Investigated, Researched |
| 设计/规划 | Designed, Planned, Proposed, Conceptualized |
| 交付/发布 | Delivered, Launched, Deployed, Released, Shipped |
| 自动化 | Automated, Scripted, Orchestrated, Configured |

## 常见 ATS 格式陷阱

### 必须避免

- **表格布局**：ATS 可能无法正确解析表格中的文本顺序
- **图片/图标**：ATS 无法读取图片中的文字（包括技能条、星级评分）
- **页眉页脚中的关键信息**：部分 ATS 忽略页眉页脚区域
- **多列布局**：可能导致文本顺序混乱
- **花哨字体**：使用标准字体（Arial, Calibri, Times New Roman）
- **文件名不规范**：使用 "姓名_Resume.docx" 或 "Name_Resume.pdf"

### 推荐做法

- **单列布局**：内容从上到下线性排列
- **标准模块标题**：使用 ATS 能识别的标准标题（Experience, Education, Skills, Summary）
- **纯文本友好**：确保简历转为纯文本后仍然可读
- **日期格式统一**：使用 "MMM YYYY" 或 "MM/YYYY" 格式
- **联系信息在正文区域**：不要放在页眉中

## 关键词密度控制

- **目标**：核心关键词（JD 中出现 2 次以上的词）在简历中至少出现 2 次
- **上限**：同一关键词不要超过 4-5 次，否则会被判为关键词堆砌
- **分布**：每个关键词至少在 2 个不同模块中出现
- **自然度检查**：删掉关键词后句子仍然通顺，说明嵌入是自然的
