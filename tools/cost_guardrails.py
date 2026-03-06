#!/usr/bin/env python3
import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Finding:
    severity: str  # ERROR | WARN | INFO
    rule_id: str
    message: str
    path: str | None = None


def repo_read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def add(findings: list[Finding], severity: str, rule_id: str, message: str, path: Path | None = None) -> None:
    findings.append(
        Finding(
            severity=severity,
            rule_id=rule_id,
            message=message,
            path=str(path.relative_to(REPO_ROOT)) if path else None,
        )
    )


def check_required_docs(findings: list[Finding]) -> None:
    required = [
        REPO_ROOT / "README.md",
        REPO_ROOT / "docs" / "ops" / "slo.md",
        REPO_ROOT / "docs" / "security" / "threat-model.md",
        REPO_ROOT / "docs" / "runbooks" / "backup-and-restore.md",
    ]
    for p in required:
        if not p.exists():
            add(findings, "ERROR", "docs.required", "Required documentation file is missing.", p)


def check_readme_cost_section(findings: list[Finding]) -> None:
    readme = REPO_ROOT / "README.md"
    if not readme.exists():
        return
    text = repo_read(readme)
    if "Cost guardrails" not in text:
        add(
            findings,
            "WARN",
            "docs.cost_guardrails_section",
            "README should include a 'Cost guardrails' section to explain the checks and how to use them.",
            readme,
        )
    if "TEST_MODE" not in text:
        add(
            findings,
            "WARN",
            "docs.test_mode",
            "README should document TEST_MODE=demo|production and how to run both modes safely.",
            readme,
        )


def check_docker_compose_image_pinning(findings: list[Finding]) -> None:
    compose = REPO_ROOT / "docker-compose.yml"
    if not compose.exists():
        return

    text = repo_read(compose)
    images = re.findall(r"(?m)^\\s*image:\\s*([^\\s#]+)\\s*$", text)
    if not images:
        add(findings, "WARN", "compose.images", "No container images detected in docker-compose.yml.", compose)
        return

    for image in images:
        if ":" not in image:
            add(findings, "WARN", "compose.image_tag", f"Image has no tag pinned: {image}", compose)
            continue
        tag = image.split(":", 1)[1]
        if tag == "latest":
            add(findings, "ERROR", "compose.image_latest", f"Image uses a floating tag: {image}", compose)
        if re.fullmatch(r"\\d+", tag):
            add(
                findings,
                "WARN",
                "compose.image_major_only",
                f"Image is pinned only to a major version ({tag}). Consider pinning a patch tag for reproducibility: {image}",
                compose,
            )


def check_terraform_cost_attribution(findings: list[Finding]) -> None:
    tf_files = sorted((REPO_ROOT / "infra").rglob("*.tf"))
    if not tf_files:
        add(findings, "INFO", "tf.none", "No Terraform files found under infra/; skipping Terraform guardrails.")
        return

    combined = "\n".join(repo_read(p) for p in tf_files)
    if "required_version" not in combined:
        add(findings, "WARN", "tf.required_version", "Terraform should define required_version to avoid drift.")

    if not re.search(r'variable\\s+\"owner\"\\s*\\{', combined):
        add(
            findings,
            "WARN",
            "tf.owner_variable",
            "Terraform examples should include an `owner` (or equivalent) tag variable for cost attribution.",
        )

    has_aws = re.search(r'\\bresource\\s+\"aws_[^\"]+\"', combined) is not None
    if has_aws:
        if "tags" not in combined:
            add(
                findings,
                "WARN",
                "tf.tags",
                "AWS resources detected but no obvious `tags` usage found. Ensure cost attribution tags are applied.",
            )
    else:
        add(findings, "INFO", "tf.no_aws_resources", "No AWS resources detected in Terraform examples (guardrails limited).")


def check_gitignore_job_files(findings: list[Finding]) -> None:
    ignore = REPO_ROOT / ".gitignore"
    if not ignore.exists():
        add(findings, "WARN", "gitignore.missing", ".gitignore is missing; add rules for artifacts and private inputs.")
        return
    text = repo_read(ignore)
    if ".[0-9][0-9]_*.txt" not in text:
        add(
            findings,
            "WARN",
            "gitignore.job_descriptions",
            "Add a .gitignore rule to prevent committing private job description .txt files (e.g., `.[0-9][0-9]_*.txt`).",
            ignore,
        )


def summarize(findings: list[Finding]) -> dict:
    errors = sum(1 for f in findings if f.severity == "ERROR")
    warns = sum(1 for f in findings if f.severity == "WARN")
    infos = sum(1 for f in findings if f.severity == "INFO")
    return {"errors": errors, "warnings": warns, "info": infos}


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline, deterministic cost guardrails for this repo.")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--out", default="", help="Write output to a file (optional).")
    args = parser.parse_args()

    findings: list[Finding] = []
    check_required_docs(findings)
    check_readme_cost_section(findings)
    check_docker_compose_image_pinning(findings)
    check_terraform_cost_attribution(findings)
    check_gitignore_job_files(findings)

    report = {
        "summary": summarize(findings),
        "findings": [asdict(f) for f in findings],
    }

    if args.format == "json":
        output = json.dumps(report, indent=2, sort_keys=True)
    else:
        lines = []
        for f in findings:
            where = f" ({f.path})" if f.path else ""
            lines.append(f"{f.severity} {f.rule_id}{where}: {f.message}")
        lines.append("")
        lines.append(f"Summary: {report['summary']}")
        output = "\n".join(lines)

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(output + "\n", encoding="utf-8")
    else:
        print(output)

    return 1 if report["summary"]["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

