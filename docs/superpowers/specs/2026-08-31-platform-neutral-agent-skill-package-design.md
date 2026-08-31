# Platform-Neutral Agent Skill Package Design

- Status: Approved
- Date: 2026-08-31
- Scope: `monkey-resume` Skill package

## Goal

Make MonkeyResume a portable Agent Skills package whose runtime contract is defined by `SKILL.md` and reusable bundled resources, without maintaining client-specific commands, metadata, manifests, or compatibility probes.

## Package Boundary

The portable Skill consists of `SKILL.md` plus the scripts, references, and templates that implement its workflow. Python dependencies, tests, CI, README files, and repository development instructions remain because they support maintenance rather than any individual agent client.

`AGENTS.md` remains as repository development guidance. Its content must be client-neutral: it may define repository boundaries, editing rules, and verification commands, but it must not promise or configure special behavior for Codex, Claude Code, OpenCode, or another client.

## Removed Client-Specific Support

Remove the following surfaces and all active references to them:

- Claude Code commands and `CLAUDE.md`
- OpenCode command/configuration files
- OpenAI UI metadata in `agents/openai.yaml`
- the custom agent installation manifest
- the multi-client platform support probe

Historical research or implementation-plan documents may retain factual mentions of tools or removed files when they describe past work. They must not be presented as current installation or validation instructions.

## Installation and Validation

Users install the repository by linking or cloning it as `~/.agents/skills/monkey-resume`. The Skill name remains `monkey-resume`, so installed directory and frontmatter names match.

Validation has three layers:

1. Agent Skills format validation for `SKILL.md` metadata and package naming.
2. Ruff for Python source quality.
3. The complete unittest suite for scripts, evidence rules, projection, PDF behavior, and package structure.

CI must not invoke a client executable or require a client-specific metadata file.

## Compatibility and Non-Goals

The package remains usable by any client that implements the Agent Skills open format. This change does not add client-specific discovery, UI metadata, slash commands, plugin manifests, or runtime probes. It does not change resume evidence, projection, language, PDF, or publication behavior.

## Acceptance Criteria

- `SKILL.md` remains the portable entrypoint with `name: monkey-resume`.
- Generic runtime resources and repository development infrastructure remain.
- No active client-specific adapter file remains in the package.
- README, installation guidance, `AGENTS.md`, CI, and active workflow references describe only the shared Agent Skills installation and generic validation flow.
- Focused structural tests fail before the cleanup and pass afterward.
- Ruff, the complete unittest suite, and an Agent Skills format validator pass on the final package.
