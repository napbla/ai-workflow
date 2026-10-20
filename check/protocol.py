#!/usr/bin/env python3
"""Deterministically validate a repository against the shipped ai-workflow protocol."""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

MODULE_DIR = Path(__file__).resolve().parent
REPO_ROOT = MODULE_DIR.parent
VERSION_PATH = REPO_ROOT / "spec" / "VERSION"

ALLOWED_DESIGN_STATUSES = {"Proposed", "Accepted", "Implementing", "Realized"}
REQUIRED_FILES = (
    ".ai-workflow.yml",
    "WORKFLOW.md",
    "AGENTS.md",
    "docs/WORK_TRACKING.md",
    "docs/designs/INDEX.md",
    "docs/status/CURRENT.md",
)
REQUIRED_DIRS = (
    ".agents",
    "docs/architecture",
    "docs/specs",
    "docs/adr",
    "docs/designs",
    "docs/changes",
    "docs/status",
)

MARKER_RE = re.compile(r"(?m)^protocol:\s*['\"]?(\d+)['\"]?\s*$")
WORKFLOW_VERSION_RE = re.compile(r"(?m)^Protocol:\s*`ai-workflow v(\d+)`\s*$")
DESIGN_STATUS_RE = re.compile(r"(?m)^Status:\s*(\w+)\s*$")
DESIGN_FIELD_RE = re.compile(r"(?m)^Design:\s*(\S+)\s*$")
REVISION_FIELD_RE = re.compile(r"(?m)^Design-Revision:\s*(\S+)\s*$")
REVISION_RE = re.compile(r"^[0-9a-fA-F]{7,64}$")
MAP_ENTRY_RE = re.compile(r"^[-*+]\s+(.+?)\s+—\s+(Target|Realized)\s*$")
INDEX_ROW_RE = re.compile(
    r"^\|\s*\[([^\]]+)\]\(([^)]+/DESIGN\.md)\)\s*\|\s*(\w+)\s*\|\s*(.*?)\s*\|\s*$"
)
BACKTICK_VALUE_RE = re.compile(r"`([^`]+)`")
INDEX_AREAS_CELL_RE = re.compile(r"^\s*`[^`]+`(?:\s*,\s*`[^`]+`)*\s*$")

MAP_SECTIONS = ("Areas:", "Tests:", "Current-truth docs:")
REQUIRED_MAP_LABELS = ("Changes:", *MAP_SECTIONS)
INDEX_HEADER = "| Design | Design status | Realized source areas |"


@dataclass(frozen=True)
class Violation:
    path: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}: {self.message}"


@dataclass
class DesignInfo:
    path: str
    status: str
    entries: dict[str, list[tuple[str, str]]]

    @property
    def realized_areas(self) -> set[str]:
        return {path for path, state in self.entries.get("Areas:", []) if state == "Realized"}


@dataclass(frozen=True)
class IndexRow:
    design_path: str
    status: str
    areas: frozenset[str]


def shipped_version() -> str:
    return VERSION_PATH.read_text(encoding="utf-8").strip()


def _strip_html_comments(line: str, in_comment: bool) -> tuple[str, bool]:
    """Remove HTML comments while preserving visible text outside them."""
    visible: list[str] = []
    rest = line
    while True:
        if in_comment:
            end = rest.find("-->")
            if end < 0:
                return "".join(visible), True
            rest = rest[end + 3 :]
            in_comment = False

        start = rest.find("<!--")
        if start < 0:
            visible.append(rest)
            return "".join(visible), False

        visible.append(rest[:start])
        rest = rest[start + 4 :]
        in_comment = True


def _fence_opening(line: str) -> tuple[str, int] | None:
    match = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
    if not match:
        return None
    marker, info = match.groups()
    if marker[0] == "`" and "`" in info:
        return None
    return marker[0], len(marker)


def unfenced_lines(text: str) -> list[str]:
    """Return structurally visible Markdown lines.

    This is intentionally a small structural scanner, not a full Markdown
    renderer. It only distinguishes constructs that could otherwise masquerade
    as protocol metadata, headings, maps, or index rows.
    """
    result: list[str] = []
    in_fence = False
    fence_char = ""
    fence_len = 0
    in_comment = False

    for raw_line in text.splitlines():
        if in_fence:
            close = re.match(r"^ {0,3}(`{3,}|~{3,})[ \t]*$", raw_line)
            if close:
                marker = close.group(1)
                if marker[0] == fence_char and len(marker) >= fence_len:
                    in_fence = False
                    fence_char = ""
                    fence_len = 0
            result.append("")
            continue

        if in_comment:
            _, in_comment = _strip_html_comments(raw_line, True)
            result.append("")
            continue

        # Indented code is classified before starting new HTML comments.
        if raw_line.startswith("    ") or raw_line.startswith("\t"):
            result.append("")
            continue

        # Fences are recognized before HTML comment parsing because comment
        # markers inside a valid fence info string are literal info text.
        opening = _fence_opening(raw_line)
        if opening is not None:
            fence_char, fence_len = opening
            in_fence = True
            result.append("")
            continue

        line, in_comment = _strip_html_comments(raw_line, False)
        if in_comment and not line:
            result.append("")
            continue

        result.append(line)
    return result


def metadata_text(text: str) -> str:
    lines = unfenced_lines(text)
    head: list[str] = []
    level_two_re = re.compile(r"^ {0,3}##(?:[ \t]+|$)")
    for line in lines:
        if level_two_re.match(line):
            break
        head.append(line)
    return "\n".join(head)


def section_lines(text: str, heading: str) -> list[str] | None:
    lines = unfenced_lines(text)
    start: int | None = None
    heading_re = re.compile(r"^ {0,3}" + re.escape(heading) + r"[ \t]*$")
    level_two_re = re.compile(r"^ {0,3}##(?:[ \t]+|$)")

    for index, line in enumerate(lines):
        if heading_re.match(line):
            start = index + 1
            break
    if start is None:
        return None

    section: list[str] = []
    for line in lines[start:]:
        if level_two_re.match(line):
            break
        section.append(line)
    return section


def safe_relative_path(value: str) -> bool:
    path = Path(value)
    return not path.is_absolute() and ".." not in path.parts and value not in {"", "."}


def mapping_exists(target: Path, pattern: str) -> bool:
    if not safe_relative_path(pattern):
        return False
    if any(char in pattern for char in "*?["):
        return any(target.glob(pattern))
    return (target / pattern).exists()


def required_state_violations(target: Path) -> list[Violation]:
    violations: list[Violation] = []
    for relative in REQUIRED_FILES:
        if not (target / relative).is_file():
            violations.append(Violation(relative, "required file is missing"))
    for relative in REQUIRED_DIRS:
        if not (target / relative).is_dir():
            violations.append(Violation(relative + "/", "required directory is missing"))
    if (target / ".agents").is_dir() and not any((target / ".agents").glob("*.md")):
        violations.append(Violation(".agents/", "must contain at least one role markdown file"))
    return violations


def version_violations(target: Path, expected: str) -> list[Violation]:
    violations: list[Violation] = []

    marker = target / ".ai-workflow.yml"
    if marker.is_file():
        text = marker.read_text(encoding="utf-8")
        match = MARKER_RE.search(text)
        if not match:
            violations.append(Violation(".ai-workflow.yml", "missing integer `protocol:` marker"))
        elif match.group(1) != expected:
            violations.append(
                Violation(".ai-workflow.yml", f"declares protocol {match.group(1)}; validator supports {expected}")
            )

    workflow = target / "WORKFLOW.md"
    if workflow.is_file():
        text = workflow.read_text(encoding="utf-8")
        visible = "\n".join(unfenced_lines(text))
        match = WORKFLOW_VERSION_RE.search(visible)
        if not match:
            violations.append(Violation("WORKFLOW.md", "missing `Protocol: ai-workflow vN` declaration"))
        elif match.group(1) != expected:
            violations.append(
                Violation("WORKFLOW.md", f"declares protocol v{match.group(1)}; expected v{expected}")
            )

    return violations


def parse_realization_map(
    target: Path, design_path: str, text: str
) -> tuple[dict[str, list[tuple[str, str]]], list[Violation], bool]:
    violations: list[Violation] = []
    section = section_lines(text, "## Realization Map")
    if section is None:
        return {}, violations, False

    entries: dict[str, list[tuple[str, str]]] = {name: [] for name in MAP_SECTIONS}
    current: str | None = None
    labels_seen: set[str] = set()

    for raw_line in section:
        line = raw_line.strip()
        if not line:
            continue
        if line in REQUIRED_MAP_LABELS:
            current = line
            labels_seen.add(line)
            continue
        if current not in MAP_SECTIONS:
            continue
        if not re.match(r"^[-*+]\s+", line):
            continue

        match = MAP_ENTRY_RE.match(line)
        if not match:
            violations.append(
                Violation(design_path, f"invalid {current[:-1]} Realization Map entry: {line}")
            )
            continue
        mapped_path, state = match.groups()
        mapped_path = mapped_path.strip()
        if mapped_path.startswith("`") and mapped_path.endswith("`") and len(mapped_path) >= 2:
            mapped_path = mapped_path[1:-1].strip()
        entries[current].append((mapped_path, state))

        if not safe_relative_path(mapped_path):
            violations.append(
                Violation(design_path, f"mapped path must stay inside the repository: {mapped_path}")
            )
        elif state == "Realized" and not mapping_exists(target, mapped_path):
            violations.append(
                Violation(design_path, f"Realized mapping does not match current repository state: {mapped_path}")
            )

    missing_labels = [label for label in REQUIRED_MAP_LABELS if label not in labels_seen]
    if missing_labels:
        violations.append(
            Violation(
                design_path,
                "Realization Map is missing required sections: " + ", ".join(missing_labels),
            )
        )
    return entries, violations, not missing_labels


def design_violations(target: Path) -> tuple[dict[str, DesignInfo], list[Violation]]:
    designs: dict[str, DesignInfo] = {}
    violations: list[Violation] = []
    design_root = target / "docs" / "designs"
    if not design_root.is_dir():
        return designs, violations

    for path in sorted(design_root.glob("*/DESIGN.md")):
        relative = path.relative_to(target).as_posix()
        text = path.read_text(encoding="utf-8")
        meta = metadata_text(text)
        status_match = DESIGN_STATUS_RE.search(meta)
        if not status_match:
            violations.append(Violation(relative, "missing Design `Status:` metadata"))
            continue

        status = status_match.group(1)
        if status not in ALLOWED_DESIGN_STATUSES:
            violations.append(
                Violation(relative, f"invalid Design status {status!r}; expected one of {sorted(ALLOWED_DESIGN_STATUSES)}")
            )

        entries, map_violations, has_map = parse_realization_map(target, relative, text)
        violations.extend(map_violations)

        if status in {"Implementing", "Realized"} and not has_map:
            violations.append(Violation(relative, f"{status} Design must have an instance-level Realization Map"))

        if status == "Realized":
            targets = [
                mapped_path
                for section in MAP_SECTIONS
                for mapped_path, state in entries.get(section, [])
                if state == "Target"
            ]
            if targets:
                violations.append(
                    Violation(relative, f"Realized Design still contains Target mappings: {', '.join(targets)}")
                )

        designs[relative] = DesignInfo(relative, status, entries)

    return designs, violations


def parse_index(target: Path) -> tuple[dict[str, IndexRow], list[Violation]]:
    index_path = target / "docs" / "designs" / "INDEX.md"
    rows: dict[str, IndexRow] = {}
    violations: list[Violation] = []
    if not index_path.is_file():
        return rows, violations

    lines = unfenced_lines(index_path.read_text(encoding="utf-8"))
    header_index: int | None = None
    for index, line in enumerate(lines):
        if line.strip() == INDEX_HEADER:
            header_index = index
            break

    if header_index is None:
        violations.append(Violation("docs/designs/INDEX.md", "missing Design index table header"))
        return rows, violations

    table_lines = lines[header_index + 1 :]
    if not table_lines:
        violations.append(Violation("docs/designs/INDEX.md", "Design index table is missing delimiter row"))
        return rows, violations

    delimiter = table_lines[0].strip()
    if not re.match(r"^\|\s*:?-+\s*\|\s*:?-+\s*\|\s*:?-+\s*\|$", delimiter):
        violations.append(Violation("docs/designs/INDEX.md", "Design index table has invalid or detached delimiter row"))
        return rows, violations

    for line in table_lines[1:]:
        stripped = line.strip()
        if not stripped or not stripped.startswith("|"):
            break

        match = INDEX_ROW_RE.match(stripped)
        if not match:
            violations.append(Violation("docs/designs/INDEX.md", f"invalid Design index row: {stripped}"))
            continue

        _, link, status, areas_cell = match.groups()
        if not INDEX_AREAS_CELL_RE.match(areas_cell):
            violations.append(
                Violation("docs/designs/INDEX.md", f"invalid realized source areas cell: {areas_cell.strip()}")
            )
            continue
        design_path = (Path("docs/designs") / link).as_posix()
        areas = frozenset(BACKTICK_VALUE_RE.findall(areas_cell))
        if design_path in rows:
            violations.append(Violation("docs/designs/INDEX.md", f"duplicate row for {design_path}"))
            continue
        rows[design_path] = IndexRow(design_path, status, areas)

    return rows, violations


def index_violations(
    designs: dict[str, DesignInfo], rows: dict[str, IndexRow]
) -> list[Violation]:
    violations: list[Violation] = []

    area_owners: dict[str, list[str]] = {}
    for design in designs.values():
        for area in design.realized_areas:
            area_owners.setdefault(area, []).append(design.path)
    for area, owners in sorted(area_owners.items()):
        if len(owners) > 1:
            violations.append(
                Violation(
                    "docs/designs/INDEX.md",
                    f"Realized source area {area!r} is owned by multiple Designs: {', '.join(owners)}",
                )
            )

    for design_path, design in designs.items():
        expected = design.realized_areas
        row = rows.get(design_path)
        if expected and row is None:
            violations.append(
                Violation("docs/designs/INDEX.md", f"missing realized mapping row for {design_path}")
            )
            continue
        if not expected and row is not None:
            violations.append(
                Violation("docs/designs/INDEX.md", f"row for {design_path} has no realized source Areas")
            )
            continue
        if row is None:
            continue
        if row.status != design.status:
            violations.append(
                Violation(
                    "docs/designs/INDEX.md",
                    f"{design_path} status is {design.status} but index says {row.status}",
                )
            )
        if set(row.areas) != expected:
            missing = sorted(expected - set(row.areas))
            extra = sorted(set(row.areas) - expected)
            detail: list[str] = []
            if missing:
                detail.append("missing: " + ", ".join(missing))
            if extra:
                detail.append("extra: " + ", ".join(extra))
            violations.append(
                Violation(
                    "docs/designs/INDEX.md",
                    f"{design_path} realized Areas projection differs ({'; '.join(detail)})",
                )
            )

    for design_path in sorted(set(rows) - set(designs)):
        violations.append(
            Violation("docs/designs/INDEX.md", f"row references missing Design: {design_path}")
        )

    return violations


def change_violations(target: Path, designs: dict[str, DesignInfo]) -> list[Violation]:
    violations: list[Violation] = []
    change_root = target / "docs" / "changes"
    if not change_root.is_dir():
        return violations

    for path in sorted(change_root.glob("*/CHANGE.md")):
        relative = path.relative_to(target).as_posix()
        meta = metadata_text(path.read_text(encoding="utf-8"))
        design_match = DESIGN_FIELD_RE.search(meta)
        revision_match = REVISION_FIELD_RE.search(meta)

        if revision_match and not design_match:
            violations.append(Violation(relative, "has Design-Revision but no Design field"))
            continue
        if not design_match:
            continue

        design_path = design_match.group(1)
        if design_path not in designs:
            violations.append(Violation(relative, f"Design does not exist: {design_path}"))

        if not revision_match:
            violations.append(Violation(relative, "Design-derived Change is missing Design-Revision"))
        elif not REVISION_RE.match(revision_match.group(1)):
            violations.append(
                Violation(relative, f"Design-Revision is not a commit-like hex SHA: {revision_match.group(1)}")
            )

    return violations


def validate(target: Path, expected_version: str) -> list[Violation]:
    violations = required_state_violations(target)
    violations.extend(version_violations(target, expected_version))

    designs, design_errors = design_violations(target)
    violations.extend(design_errors)

    rows, index_errors = parse_index(target)
    violations.extend(index_errors)
    violations.extend(index_violations(designs, rows))
    violations.extend(change_violations(target, designs))

    return violations


def report(target: Path, expected_version: str, violations: Iterable[Violation]) -> str:
    items = list(violations)
    if not items:
        return f"Protocol validation passed: {target} (ai-workflow v{expected_version})"
    lines = [f"Protocol validation failed: {target} (ai-workflow v{expected_version})"]
    lines.extend(f"  - {item}" for item in items)
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate an ai-workflow repository against the shipped protocol.")
    parser.add_argument("--target", type=Path, default=Path.cwd(), help="Repository to validate (default: current directory)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        target = args.target.resolve()
        if not target.is_dir():
            print(f"Target is not a directory: {target}", file=sys.stderr)
            return 2
        expected = shipped_version()
        violations = validate(target, expected)
    except (OSError, UnicodeError) as exc:
        print(f"Protocol validation could not read repository state: {exc}", file=sys.stderr)
        return 2

    print(report(target, expected, violations))
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
