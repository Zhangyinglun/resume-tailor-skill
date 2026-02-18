# ATS Keyword Matching Strategy

## How ATS Works

ATS (Applicant Tracking System) filters resumes through the following methods:

1. **Keyword Matching**: Exact/fuzzy match resume text against JD keywords
2. **Frequency Statistics**: Higher keyword occurrence increases score (but avoid keyword stuffing)
3. **Context Analysis**: Advanced ATS analyzes context where keywords appear (module, paired verbs)
4. **Format Parsing**: Extracts structured information (name, contact, education, work experience, etc.)

## Keyword Extraction Methods

### Priority for Extracting Keywords from JD

1. **Words in job title**: Highest weight (e.g., "Senior Backend Engineer" → Backend, Engineer)
2. **Words in Requirements / Qualifications**: Core hard requirements
3. **Recurring words in Responsibilities**: Core job duties
4. **Words in Preferred / Nice-to-have**: Bonus points, include if available, not forced
5. **Industry terms in company description**: Demonstrates industry knowledge

### Keyword Strategy Without JD (Direction-driven)

When JD is unavailable, build a synthetic keyword pool from three layers:

1. **Target role keywords**: e.g., Software Engineer, Backend Engineer, SDE
2. **Capability intent keywords**: e.g., AI model engineering, productionization, model serving, RAG
3. **System context keywords**: e.g., data platform, distributed systems, streaming, reliability, observability

Then prioritize keywords by recurrence in the user prompt and by evidence availability in resume experience.

### Keyword Categories

| Category | Extraction Strategy | Embedding Strategy |
|----------|---------------------|-------------------|
| **Hard Skills (Tech Stack)** | Directly extract technical terms: Python, React, AWS, SQL, etc. | Place in Skills module + naturally mention in experience descriptions |
| **Soft Skills** | Extract capability descriptions: leadership, communication, problem-solving | Demonstrate through specific examples, don't just list |
| **Industry Terms** | Extract domain-specific words: CI/CD, microservices, agile, scrum | Use JD original words to replace generic expressions in experience descriptions |
| **Tools/Platforms** | Extract specific tool names: Jira, Confluence, Figma, Terraform | Place in Skills or mention in project descriptions |
| **Education/Certifications** | Extract explicit requirements: Bachelor's, Master's, PMP, CKA | Place in Education / Certifications module |
| **Quantitative Metrics** | Extract number-related descriptions: team of 5+, 99.9% uptime | Echo with data in experience descriptions |

## Keyword Embedding Strategy

### Principles

1. **Natural Integration**: Keywords must appear in meaningful sentences, not stuffed
2. **Multi-location Distribution**: Same keyword appearing once each in Skills and Experience is more effective than appearing twice in one place
3. **Exact Match Priority**: Use original words and spelling from JD (e.g., if JD says "Kubernetes" don't write "K8s")
4. **Synonym Supplement**: On top of exact matches, supplement common synonyms/abbreviations (e.g., write both "Amazon Web Services (AWS)")

### Embedding Location Priority

1. **Skills Module**: Directly list all matching technical/tool keywords
2. **Experience Module**: Naturally use keywords in achievement descriptions
3. **Summary Module**: Use 2-3 sentences to summarize core matches
4. **Projects Module**: Supplement keywords not covered in Skills/Experience

### Achievement Description Formula (Four Elements)

```
[Strong Verb] + [What was done (embed keywords)] + [Method/tool used] + [Quantified result]
```

Element Explanation:
- **Action**: Start with strong verb, demonstrate proactive contribution and responsibility level.
- **What**: Clarify what was done, naturally embed JD keywords and core scenarios.
- **How**: Supplement methods, processes, or tools used (frameworks, platforms, collaboration mechanisms).
- **Result**: Provide quantifiable results (efficiency, quality, cost, revenue, stability, etc.).

Examples:
- "Designed microservices for payment APIs aligned with scalability requirements, using Python/FastAPI and domain-driven design, reducing P95 latency by 40%"
- "Led a 6-engineer DevOps initiative for CI/CD reliability goals, using Jenkins, Terraform, and blue-green deployment, increasing deployment success rate to 99.9%"
- "Optimized user growth experiment workflows for A/B testing operations, using SQL, Python, and Tableau dashboards, cutting analysis cycle time by 35%"

### Strong Verb List (By Scenario)

| Scenario | Recommended Verbs |
|----------|-------------------|
| Development/Building | Developed, Built, Implemented, Engineered, Architected |
| Optimization/Improvement | Optimized, Improved, Enhanced, Streamlined, Refactored |
| Leadership/Management | Led, Managed, Directed, Coordinated, Mentored |
| Analysis/Research | Analyzed, Evaluated, Assessed, Investigated, Researched |
| Design/Planning | Designed, Planned, Proposed, Conceptualized |
| Delivery/Release | Delivered, Launched, Deployed, Released, Shipped |
| Automation | Automated, Scripted, Orchestrated, Configured |

## Common ATS Format Pitfalls

### Must Avoid

- **Table Layouts**: ATS may not correctly parse text order in tables
- **Images/Icons**: ATS cannot read text in images (including skill bars, star ratings)
- **Key Information in Headers/Footers**: Some ATS ignore header/footer areas
- **Multi-column Layouts**: May cause text order confusion
- **Fancy Fonts**: Use standard fonts (Arial, Calibri, Times New Roman)
- **Non-standard File Names**: Use "Name_Resume.docx" or "Name_Resume.pdf"

### Recommended Practices

- **Single-column Layout**: Content arranged linearly from top to bottom
- **Standard Module Headers**: Use ATS-recognizable standard headers (Experience, Education, Skills, Summary)
- **Plain Text Friendly**: Ensure resume is still readable after converting to plain text
- **Unified Date Format**: Use "MMM YYYY" or "MM/YYYY" format
- **Contact Info in Body Area**: Don't place in header

## Keyword Density Control

- **Target**: Core keywords (words appearing 2+ times in JD) should appear at least 2 times in resume
- **Upper Limit**: Same keyword should not exceed 4-5 times, otherwise judged as keyword stuffing
- **Distribution**: Each keyword should appear in at least 2 different modules
- **Naturalness Check**: If sentence still reads smoothly after removing keywords, embedding is natural
