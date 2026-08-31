#!/usr/bin/env python3
"""Verify Codex, Claude Code, and OpenCode support for this skill package."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

EXPECTED_ASSETS = (
    Path("AGENTS.md"),
    Path("CLAUDE.md"),
    Path("SKILL.md"),
    Path(".claude/commands/resume-tailor.md"),
    Path(".claude/commands/check-resume-tailor-setup.md"),
    Path(".opencode/command/install-skill-deps.md"),
    Path("agents/openai.yaml"),
    Path("install/agent-install.yaml"),
    Path("requirements.txt"),
    Path("scripts/extract_resume_text.py"),
    Path("scripts/resume_cache_manager.py"),
    Path("scripts/generate_final_resume.py"),
    Path("scripts/check_pdf_quality.py"),
    Path("scripts/check_pdf_geometry.py"),
    Path("scripts/check_content_quality.py"),
    Path("scripts/evidence_ledger_manager.py"),
    Path("scripts/audit_factual_integrity.py"),
    Path("scripts/generate_quality_report.py"),
    Path("references/resume-language-quality.md"),
)

Runner = Callable[[list[str], Path, Optional[dict[str, str]]], dict[str, Any]]
Which = Callable[[str], Optional[str]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check platform support for Codex, Claude Code, and OpenCode."
    )
    parser.add_argument(
        "--workspace",
        default=".",
        help="Repository root to inspect (default: current directory)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Print the structured report as JSON",
    )
    parser.add_argument(
        "--report-file",
        help="Optional Markdown report output path",
    )
    return parser.parse_args()


def _run_command(
    command: list[str],
    cwd: Path,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    effective_env = os.environ.copy()
    if env:
        effective_env.update(env)
    try:
        result = subprocess.run(
            command,
            cwd=str(cwd),
            env=effective_env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=90,
            check=False,
        )
    except Exception as exc:  # CLI/platform failures should be captured, not crash the report.
        return {
            "returncode": None,
            "stdout": "",
            "stderr": str(exc),
        }

    return {
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def _contains_all(text: str, terms: list[str]) -> bool:
    haystack = text.lower()
    return all(term.lower() in haystack for term in terms)


def _asset_check(repo_root: Path) -> dict[str, Any]:
    missing = [
        str(path).replace("\\", "/")
        for path in EXPECTED_ASSETS
        if not (repo_root / path).exists()
    ]
    return {
        "name": "support_assets",
        "passed": not missing,
        "detail": {"missing": missing},
    }


def _command_check(
    name: str,
    command: list[str],
    cwd: Path,
    runner: Runner,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    result = runner(command, cwd, env)
    return {
        "name": name,
        "passed": result["returncode"] == 0,
        "detail": {
            "command": " ".join(command),
            "returncode": result["returncode"],
            "stdout": result["stdout"],
            "stderr": result["stderr"],
        },
    }


def _baseline_checks(repo_root: Path, runner: Runner) -> dict[str, Any]:
    checks: list[dict[str, Any]] = [
        _asset_check(repo_root),
        _command_check(
            "python_version",
            [sys.executable, "--version"],
            repo_root,
            runner,
        ),
        _command_check(
            "python_dependencies",
            [
                sys.executable,
                "-c",
                "import reportlab, pdfplumber; print('reportlab and pdfplumber available')",
            ],
            repo_root,
            runner,
        ),
        _command_check(
            "platform_script_help",
            [sys.executable, "scripts/check_agent_platform_support.py", "--help"],
            repo_root,
            runner,
        ),
    ]

    with tempfile.TemporaryDirectory(prefix="resume-tailor-smoke-") as temp_dir:
        external_cwd = Path(temp_dir)
        for script_name in (
            "resume_cache_manager.py",
            "check_content_quality.py",
            "generate_quality_report.py",
            "extract_resume_text.py",
            "generate_final_resume.py",
            "check_pdf_quality.py",
            "check_pdf_geometry.py",
            "evidence_ledger_manager.py",
            "audit_factual_integrity.py",
        ):
            checks.append(
                _command_check(
                    f"external_entrypoint_{Path(script_name).stem}",
                    [
                        sys.executable,
                        str(repo_root / "scripts" / script_name),
                        "--help",
                    ],
                    external_cwd,
                    runner,
                )
            )
    return {
        "status": "pass" if all(check["passed"] for check in checks) else "fail",
        "checks": checks,
    }


def _codex_result(repo_root: Path, runner: Runner, which: Which) -> dict[str, Any]:
    executable = which("codex")
    manual_steps = [
        "Open the repository in the Codex desktop app.",
        "Ask: '这个仓库的 agent 指令文件是什么？resume-tailor 的工作流主文档是什么？'",
        "Confirm the answer references AGENTS.md, SKILL.md, scripts/, and references/.",
        "Copy the repository to $CODEX_HOME/skills/resume-tailor/ (normally ~/.codex/skills/resume-tailor/) and repeat with a JD-driven resume prompt.",
    ]
    if not executable:
        return {
            "status": "blocked",
            "summary": "Codex CLI is not installed on this machine.",
            "command_available": False,
            "manual_steps": manual_steps,
        }

    probe = runner(["codex", "--help"], repo_root, None)
    stderr_text = (probe["stderr"] or probe["stdout"]).lower()
    if probe["returncode"] == 0:
        summary = "Codex CLI starts, but repo-mode and skill-mode discovery still require desktop-session validation."
    elif "access is denied" in stderr_text or "permission" in stderr_text:
        summary = "Codex CLI is installed, but direct shell launch is blocked; desktop-session validation is required."
    else:
        summary = "Codex CLI probe failed; manual validation is still required to verify repo-mode and skill-mode discovery."

    return {
        "status": "manual_required",
        "summary": summary,
        "command_available": True,
        "probe_command": "codex --help",
        "probe_returncode": probe["returncode"],
        "probe_stdout": probe["stdout"],
        "probe_stderr": probe["stderr"],
        "manual_steps": manual_steps,
    }


def _claude_result(repo_root: Path, runner: Runner, which: Which) -> dict[str, Any]:
    executable = which("claude")
    prompt = (
        "Which repository files define your workflow here, and which local scripts "
        "handle resume extraction and PDF generation?"
    )
    manual_steps = [
        "Open the repository in Claude Code.",
        "Confirm the project command list includes resume-tailor and check-resume-tailor-setup.",
        "Run check-resume-tailor-setup and verify it checks Python dependencies and external entry points.",
    ]
    if not executable:
        return {
            "status": "blocked",
            "summary": "Claude Code CLI is not installed on this machine.",
            "command_available": False,
            "manual_steps": manual_steps,
        }

    probe = runner(["claude", "-p", prompt], repo_root, None)
    combined = " ".join([probe["stdout"], probe["stderr"]]).strip()
    discovery_passed = _contains_all(combined, ["CLAUDE.md", "SKILL.md"])
    local_scripts_passed = _contains_all(combined, ["scripts"])
    status = (
        "pass"
        if probe["returncode"] == 0 and discovery_passed and local_scripts_passed
        else "blocked"
    )

    return {
        "status": status,
        "summary": (
            "Claude Code CLI detected repository workflow files and local script entry points."
            if status == "pass"
            else "Claude Code CLI probe did not confirm workflow file discovery and local script entry points."
        ),
        "command_available": True,
        "probe_command": f'claude -p "{prompt}"',
        "probe_returncode": probe["returncode"],
        "probe_stdout": probe["stdout"],
        "probe_stderr": probe["stderr"],
        "discovery_passed": discovery_passed,
        "local_scripts_passed": local_scripts_passed,
        "manual_steps": manual_steps,
    }


def _opencode_result(repo_root: Path, runner: Runner, which: Which) -> dict[str, Any]:
    executable = which("opencode")
    discovery_prompt = (
        "Which local skill should handle JD-driven resume optimization in this workspace?"
    )
    workflow_prompt = (
        "I have a JD and an existing resume. Which workflow should you use here, "
        "and which local scripts handle extraction and PDF generation?"
    )
    manual_steps = [
        "Install or copy the repository into ~/.config/opencode/skills/resume-tailor/ if the local setup does not already load it.",
        "Run the same two prompts in an interactive OpenCode session.",
        "Confirm the response uses resume-tailor and references local scripts/ instead of cloning dependency Skills.",
    ]
    if not executable:
        return {
            "status": "blocked",
            "summary": "OpenCode CLI is not installed on this machine.",
            "command_available": False,
            "manual_steps": manual_steps,
        }

    discovery = runner(["opencode", "run", discovery_prompt], repo_root, None)
    workflow = runner(["opencode", "run", workflow_prompt], repo_root, None)
    discovery_text = " ".join([discovery["stdout"], discovery["stderr"]]).strip()
    workflow_text = " ".join([workflow["stdout"], workflow["stderr"]]).strip()
    discovery_passed = _contains_all(discovery_text, ["resume-tailor"])
    workflow_passed = _contains_all(workflow_text, ["resume-tailor"])
    local_scripts_passed = _contains_all(workflow_text, ["scripts"])
    status = (
        "pass"
        if (
            discovery["returncode"] == 0
            and workflow["returncode"] == 0
            and discovery_passed
            and workflow_passed
            and local_scripts_passed
        )
        else "blocked"
    )

    return {
        "status": status,
        "summary": (
            "OpenCode CLI detected the local resume-tailor skill and script entry points."
            if status == "pass"
            else "OpenCode CLI probe did not confirm local skill discovery and script entry points."
        ),
        "command_available": True,
        "probe_command": f'opencode run "{discovery_prompt}"',
        "discovery_probe": discovery,
        "workflow_probe": workflow,
        "discovery_passed": discovery_passed,
        "workflow_passed": workflow_passed,
        "local_scripts_passed": local_scripts_passed,
        "manual_steps": manual_steps,
    }


def run_all_checks(
    repo_root: Path,
    *,
    runner: Runner = _run_command,
    which: Which = shutil.which,
) -> dict[str, Any]:
    repo_root = repo_root.expanduser().resolve()
    return {
        "workspace": str(repo_root),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "baseline": _baseline_checks(repo_root, runner),
        "platforms": {
            "codex": _codex_result(repo_root, runner, which),
            "claude": _claude_result(repo_root, runner, which),
            "opencode": _opencode_result(repo_root, runner, which),
        },
    }


def build_markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# Agent Platform Smoke Test Report",
        "",
        f"- Workspace: `{report['workspace']}`",
        f"- Generated at: `{report['generated_at']}`",
        f"- Baseline status: `{report['baseline']['status']}`",
        "",
        "## Baseline",
        "",
    ]

    for check in report["baseline"]["checks"]:
        status = "PASS" if check["passed"] else "FAIL"
        detail = check["detail"]
        lines.append(f"- `{check['name']}`: {status}")
        if "command" in detail:
            lines.append(f"  Command: `{detail['command']}`")
        if detail.get("stdout"):
            lines.append(f"  Stdout: `{detail['stdout']}`")
        if detail.get("stderr"):
            lines.append(f"  Stderr: `{detail['stderr']}`")
        if detail.get("missing"):
            lines.append(f"  Missing: {', '.join(detail['missing'])}")

    for platform_name, result in report["platforms"].items():
        lines.extend(
            [
                "",
                f"## {platform_name.capitalize()}",
                "",
                f"- Status: `{result['status']}`",
                f"- Summary: {result['summary']}",
            ]
        )
        if result.get("probe_command"):
            lines.append(f"- Probe: `{result['probe_command']}`")
        if "probe_returncode" in result:
            lines.append(f"- Return code: `{result['probe_returncode']}`")
        if result.get("probe_stdout"):
            lines.append(f"- Stdout: `{result['probe_stdout']}`")
        if result.get("probe_stderr"):
            lines.append(f"- Stderr: `{result['probe_stderr']}`")
        for key in ("discovery_passed", "workflow_passed", "local_scripts_passed"):
            if key in result:
                lines.append(f"- {key}: `{result[key]}`")
        if result.get("manual_steps"):
            lines.append("- Manual steps:")
            for step in result["manual_steps"]:
                lines.append(f"  - {step}")

    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    repo_root = Path(args.workspace)
    report = run_all_checks(repo_root)

    if args.report_file:
        report_path = Path(args.report_file).expanduser().resolve()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(build_markdown_report(report), encoding="utf-8")

    if args.json_output:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(build_markdown_report(report))
    return 0 if report["baseline"]["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
