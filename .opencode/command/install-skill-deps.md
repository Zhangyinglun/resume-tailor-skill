请执行 resume-tailor 的依赖技能自动安装流程。

必做步骤：

1. 读取并遵循 `docs/guide/installation.md` 的 `For LLM Agents` 部分。
2. 读取 `install/agent-install.yaml`，将其中 `sources`、`install_plan`、`post_check` 全量执行。
3. 对上游仓库使用 `pull-or-clone` 策略，避免目录已存在导致安装失败。
4. 只安装以下技能：`pdf`、`docx`、`humanizer`。
5. 明确不安装 `humanizer-zh`。
6. 必须输出安装报告（版本信息、同步方式、安装结果、post-check 结果）。

执行要求：

- 默认先做最小可行方案，不修改与安装无关的配置。
- 遇到失败先重试一次；仍失败时停止并给出可执行修复建议。
- 禁止在未完成 post-check 的情况下宣称安装成功。
