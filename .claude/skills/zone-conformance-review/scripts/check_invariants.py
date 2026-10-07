#!/usr/bin/env python3
"""
Scans the FitBase app repo for violations of the invariants architecture.md
declares non-negotiable.

These are the rules whose breach causes cross-tenant data leaks, money errors or
silent data loss — not style preferences. Each is mechanically detectable, so it
is checked here rather than left to a reviewer's attention budget.

Judgment-based conformance (does the code actually satisfy the story's acceptance
criteria?) is the agent's job; this script only covers what a regex can prove.

Usage:
    check_invariants.py --repo-root /path/to/fitbase [--diff-base main] [--json]

Exit codes:
    0  no violations
    1  one or more violations
    2  could not run (bad path, no repo)
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class Violation:
    rule: str
    severity: str  # CRITICAL | HIGH | MEDIUM
    file: str
    line: int
    excerpt: str
    why: str
    fix: str


@dataclass
class Rule:
    name: str
    severity: str
    why: str
    fix: str
    pattern: re.Pattern
    # Only files whose path matches this are scanned.
    applies_to: re.Pattern
    # A line matching this is exempt (e.g. the legitimate definition site).
    exempt: re.Pattern | None = None


TS_FILES = re.compile(r"\.tsx?$")

RULES: list[Rule] = [
    Rule(
        name="tenant-scope-from-input",
        severity="CRITICAL",
        why=(
            "businessId taken from caller-controlled input lets any authenticated "
            "user read or write another gym's data."
        ),
        fix="Read it from the verified JWT via getRequestContext(req) / getTenantContext(req).",
        pattern=re.compile(
            r"""(?x)
            (?:businessId|business_id)\s*[=:]\s*
            (?:
              (?:await\s+)?req(?:uest)?\.(?:json\(\)|body|query)
              | body\.
              | params\.
              | searchParams\.get\(
            )
            """
        ),
        applies_to=re.compile(r"src/app/api/.*\.ts$"),
    ),
    Rule(
        name="search-params-business-id",
        severity="CRITICAL",
        why="Reading businessId from the query string bypasses tenant scoping entirely.",
        fix="Remove the parameter; the JWT already carries the tenant.",
        pattern=re.compile(r"""searchParams\.get\(\s*['"]businessId['"]"""),
        applies_to=re.compile(r"src/.*\.tsx?$"),
    ),
    Rule(
        name="float-money",
        severity="CRITICAL",
        why=(
            "Money as a float accumulates rounding error. All amounts are integer "
            "kobo (₦35,000 -> 3500000)."
        ),
        fix="Store integers in kobo; use toKobo/fromKobo/formatCurrency.",
        pattern=re.compile(
            r"""(?x)
            (?:amount|price|total|fee)\s*[:=]\s*\d+\.\d+
            | parseFloat\s*\(\s*[^)]*(?:amount|price|total)
            """,
            re.IGNORECASE,
        ),
        applies_to=re.compile(r"src/.*\.tsx?$"),
    ),
    Rule(
        name="float-money-schema",
        severity="CRITICAL",
        why="A Float/Decimal column for money reintroduces rounding error at the database.",
        fix="Use Int and store kobo.",
        pattern=re.compile(
            r"^\s*(?:amount|price|total|fee)\w*\s+(?:Float|Decimal)\b", re.IGNORECASE
        ),
        applies_to=re.compile(r"prisma/schema\.prisma$"),
    ),
    Rule(
        name="auth-guard-in-page",
        severity="CRITICAL",
        why=(
            "An auth guard in page.tsx protects only that page. A sibling page added "
            "later ships unprotected because nothing forces the author to repeat it."
        ),
        fix="Move the guard to the route group's layout.tsx.",
        # A role check or a bounce to /login is a guard. Merely reading the
        # session to get an id is a data access and belongs in a page — the
        # earlier, broader pattern flagged every such page as a violation.
        pattern=re.compile(r"""hasRole\s*\(|redirect\(\s*['"]/login"""),
        applies_to=re.compile(r"src/app/.*/page\.tsx$"),
    ),
    Rule(
        name="hard-delete",
        severity="CRITICAL",
        why=(
            "Members, businesses and payments are never hard-deleted — NDPR retention "
            "and the financial audit trail both depend on the row surviving."
        ),
        fix="Set archivedAt, or for payments set voidedAt with a reason.",
        pattern=re.compile(
            r"prisma\.(?:member|business|payment|checkIn|membership)\.delete(?:Many)?\s*\(",
            re.IGNORECASE,
        ),
        applies_to=re.compile(r"src/.*\.tsx?$"),
    ),
    Rule(
        name="inline-query-key",
        severity="HIGH",
        why=(
            "An inline query key cannot be invalidated by the factory, so two call "
            "sites silently maintain caches that never refresh each other."
        ),
        fix="Use the queryKeys factory in src/lib/queryKeys.ts.",
        pattern=re.compile(r"""queryKey\s*:\s*\[\s*['"]"""),
        applies_to=re.compile(r"src/.*\.tsx?$"),
        exempt=re.compile(r"src/lib/queryKeys\.ts$"),
    ),
    Rule(
        name="raw-fetch-in-component",
        severity="HIGH",
        why=(
            "A raw fetch in a component skips the cache, the loading state and the "
            "error envelope handling that useQuery/useMutation provide."
        ),
        fix="Call through a hook in src/hooks/ using useQuery or useMutation.",
        pattern=re.compile(r"\bfetch\s*\("),
        applies_to=re.compile(r"src/components/.*\.tsx$"),
        # The auth flow predates the query layer and calls the OTP endpoint directly.
        exempt=re.compile(r"src/components/auth/LoginFlow\.tsx$"),
    ),
    Rule(
        name="mutation-isLoading",
        severity="MEDIUM",
        why="TanStack Query v5 mutations expose isPending; isLoading is always undefined.",
        fix="Use isPending.",
        # Both orders occur: `useMutation({...}).isLoading` and the far more common
        # `const { isLoading } = useMutation(...)`, where the destructure comes first.
        pattern=re.compile(r"^(?=.*useMutation)(?=.*\bisLoading\b).*$"),
        applies_to=re.compile(r"src/.*\.tsx?$"),
    ),
    Rule(
        name="colocated-test",
        severity="MEDIUM",
        why="Tests live in tests/ mirroring src/, never beside the source file.",
        fix="Move it under tests/unit/ or tests/integration/.",
        pattern=re.compile(r".*"),
        applies_to=re.compile(r"src/.*\.(?:test|spec)\.tsx?$"),
    ),
    Rule(
        name="plaintext-secret",
        severity="CRITICAL",
        why="A literal credential in source is a leaked credential.",
        fix="Read it from process.env and document it in .env.example.",
        pattern=re.compile(
            r"""(?x)
            (?:api_?key|secret|password|token)\s*[:=]\s*
            ['"](?!\s*$)(?!process\.env)[A-Za-z0-9_\-]{16,}['"]
            """,
            re.IGNORECASE,
        ),
        applies_to=re.compile(r"src/.*\.tsx?$|prisma/.*\.prisma$"),
    ),
]


def changed_files(repo: Path, base: str | None) -> list[Path] | None:
    """Files changed against `base`, or None to scan everything."""
    if not base:
        return None
    try:
        out = subprocess.run(
            ["git", "diff", "--name-only", f"{base}...HEAD"],
            cwd=repo,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return [repo / line for line in out.splitlines() if line.strip()]


def iter_files(repo: Path, base: str | None):
    subset = changed_files(repo, base)
    if subset is not None:
        for path in subset:
            if path.is_file():
                yield path
        return

    skip = {"node_modules", ".next", ".git", "dist", "coverage"}
    for path in repo.rglob("*"):
        if path.is_file() and not skip.intersection(path.parts):
            yield path


def strip_comments(line: str) -> str:
    """Crude comment strip so documentation of an anti-pattern is not a violation."""
    for marker in ("//", "*", "#"):
        stripped = line.lstrip()
        if stripped.startswith(marker):
            return ""
    return line


def scan(repo: Path, base: str | None) -> list[Violation]:
    violations: list[Violation] = []

    for path in iter_files(repo, base):
        rel = str(path.relative_to(repo))

        applicable = [r for r in RULES if r.applies_to.search(rel)]
        if not applicable:
            continue

        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        lines = text.splitlines()

        for rule in applicable:
            if rule.exempt and rule.exempt.search(rel):
                continue

            # Whole-file rules (e.g. a test file in the wrong place).
            if rule.name == "colocated-test":
                violations.append(
                    Violation(
                        rule=rule.name,
                        severity=rule.severity,
                        file=rel,
                        line=1,
                        excerpt=rel,
                        why=rule.why,
                        fix=rule.fix,
                    )
                )
                continue

            for index, raw in enumerate(lines, start=1):
                line = strip_comments(raw)
                if not line.strip():
                    continue
                if rule.pattern.search(line):
                    violations.append(
                        Violation(
                            rule=rule.name,
                            severity=rule.severity,
                            file=rel,
                            line=index,
                            excerpt=raw.strip()[:160],
                            why=rule.why,
                            fix=rule.fix,
                        )
                    )

    order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2}
    violations.sort(key=lambda v: (order.get(v.severity, 9), v.file, v.line))
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument(
        "--diff-base",
        help="Only scan files changed against this ref (e.g. main). Omit to scan everything.",
    )
    parser.add_argument("--json", action="store_true", help="Machine-readable output.")
    args = parser.parse_args()

    repo = Path(args.repo_root).expanduser().resolve()
    if not repo.is_dir():
        print(f"error: {repo} is not a directory", file=sys.stderr)
        return 2

    violations = scan(repo, args.diff_base)

    if args.json:
        counts = {sev: 0 for sev in ("CRITICAL", "HIGH", "MEDIUM")}
        for v in violations:
            counts[v.severity] = counts.get(v.severity, 0) + 1
        print(
            json.dumps(
                {
                    "violations": [asdict(v) for v in violations],
                    "counts": counts,
                    "passed": len(violations) == 0,
                },
                indent=2,
            )
        )
        return 1 if violations else 0

    if not violations:
        print("Architecture invariants: no violations.")
        return 0

    current = None
    for v in violations:
        if v.severity != current:
            current = v.severity
            print(f"\n{v.severity}")
        print(f"  {v.file}:{v.line}  [{v.rule}]")
        print(f"    {v.excerpt}")
        print(f"    why: {v.why}")
        print(f"    fix: {v.fix}")

    print(f"\n{len(violations)} violation(s).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
