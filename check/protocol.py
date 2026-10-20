#!/usr/bin/env python3
"""Deterministically validate a repository against ai-workflow's canonical protocol grammar."""
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

MARKER_RE = re.compile(r"^protocol: (\d+)$")
WORKFLOW_VERSION_RE = re.compile(r"^Protocol: `ai-workflow v(\d+)`$")
FIELD_RE = re.compile(r"^([A-Za-z][A-Za-z-]*): (.+)$")
REVISION_RE = re.compile(r"^[0-9a-fA-F]{7,64}$")
MAP_CHANGE_RE = re.compile(r"^- `([^`]+)` — (.+)$")
MAP_ENTRY_RE = re.compile(r"^- `([^`]+)` — (Target|Realized)$")
INDEX_ROW_RE = re.compile(
    r"^\| \[([^\]]+)\]\(([^)]+/DESIGN\.md)\) \| "
    r"(Proposed|Accepted|Implementing|Realized) \| (.+) \|$"
)
INDEX_AREAS_RE = re.compile(r"^`[^`]+`(?:, `[^`]+`)*$")
BACKTICK_VALUE_RE = re.compile(r"`([^`]+)`")

INDEX_HEADER = "| Design | Design status | Realized source areas |"
INDEX_DELIMITER = "| --- | --- | --- |"
MAP_LABELS = ("Changes:", "Areas:", "Tests:", "Current-truth docs:")
MAPPED_SECTIONS = ("Areas:", "Tests:", "Current-truth docs:")


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
        return {
            mapped_path
            for mapped_path, state in self.entries.get("Areas:", [])
            if state == "Realized"
        }


@dataclass(frozen=True)
class IndexRow:
    design_path: str
    status: str
    areas: frozenset[str]


def shipped_version() -> str:
    return VERSION_PATH.read_text(encoding="utf-8").strip()


def first_section_index(lines: list[str]) -> int | None:
    for index, line in enumerate(lines):
        if line.startswith("## "):
            return index
    return None


def canonical_header(
    text: str,
    path: str,
) -> tuple[dict[str, str], list[Violation], int | None]:
    """Parse the canonical top-of-file metadata block.

    This intentionally does not interpret Markdown. Before the first canonical
    level-two heading, only a level-one title, blank lines, and canonical
    `Key: value` fields are valid protocol header syntax. Field names are
    extensible; the validator extracts only the fields it needs.
    """
    lines = text.splitlines()
    section_index = first_section_index(lines)
    header_lines = lines if section_index is None else lines[:section_index]

    fields: dict[str, str] = {}
    violations: list[Violation] = []
    saw_title = False

    for line in header_lines:
        if not line:
            continue
        if not saw_title:
            if line.startswith("# ") and not line.startswith("## "):
                saw_title = True
                continue
            violations.append(Violation(path, "canonical header must begin with a level-one title"))
            saw_title = True
            continue

        match = FIELD_RE.match(line)
        if not match:
            violations.append(Violation(path, f"noncanonical metadata line: {line}"))
            continue

        key, value = match.groups()
        if key in fields:
            violations.append(Violation(path, f"duplicate metadata field: {key}"))
            continue
        fields[key] = value

    if not saw_title:
        violations.append(Violation(path, "canonical header is missing a level-one title"))

    return fields, violations, section_index


def first_section_heading(text: str) -> str | None:
    lines = text.splitlines()
    index = first_section_index(lines)
    return None if index is None else lines[index]


def exact_section_lines(text: str, heading: str) -> list[str] | None:
    """Return one canonical section bounded by exact column-zero level-two headings."""
    lines = text.splitlines()
    start = None
    for index, line in enumerate(lines):
        if line == heading:
            start = index + 1
            break
    if start is None:
        return None

    section: list[str] = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        section.append(line)
    return section


def safe_relative_path(value: str) -> bool:
    path = Path(value)
    return not path.is_absolute() and ".." not in path.parts and value not in {"", "."}


def resolves_within(root: Path, candidate: Path) -> bool:
    try:
        candidate.resolve().relative_to(root.resolve())
        return True
    except (OSError, ValueError):
        return False


def mapping_exists(target: Path, pattern: str) -> bool:
    if not safe_relative_path(pattern):
        return False

    root = target.resolve()
    if any(char in pattern for char in "*?["):
        matches = list(target.glob(pattern))
        return bool(matches) and all(
            match.exists() and resolves_within(root, match)
            for match in matches
        )

    candidate = target / pattern
    return candidate.exists() and resolves_within(root, candidate)


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
        matches = [
            match.group(1)
            for line in marker.read_text(encoding="utf-8").splitlines()
            if (match := MARKER_RE.match(line))
        ]
        if len(matches) != 1:
            violations.append(Violation(".ai-workflow.yml", "must contain exactly one canonical `protocol: N` marker"))
        elif matches[0] != expected:
            violations.append(
                Violation(".ai-workflow.yml", f"declares protocol {matches[0]}; validator supports {expected}")
            )

    workflow = target / "WORKFLOW.md"
    if workflow.is_file():
        lines = workflow.read_text(encoding="utf-8").splitlines()
        section_index = first_section_index(lines)
        header_lines = lines if section_index is None else lines[:section_index]
        matches = [
            match.group(1)
            for line in header_lines
            if (match := WORKFLOW_VERSION_RE.match(line))
        ]
        if len(matches) != 1:
            violations.append(
                Violation("WORKFLOW.md", "top-of-file header must contain exactly one canonical `Protocol: ai-workflow vN` declaration")
            )
        elif matches[0] != expected:
            violations.append(
                Violation("WORKFLOW.md", f"declares protocol v{matches[0]}; expected v{expected}")
            )

    return violations


def parse_realization_map(
    target: Path,
    design_path: str,
    text: str,
) -> tuple[dict[str, list[tuple[str, str]]], list[Violation], bool]:
    violations: list[Violation] = []
    if first_section_heading(text) != "## Realization Map":
        return {}, violations, False

    section = exact_section_lines(text, "## Realization Map")
    if section is None:
        return {}, violations, False

    entries: dict[str, list[tuple[str, str]]] = {name: [] for name in MAPPED_SECTIONS}
    expected_label_index = 0
    current: str | None = None
    canonical_structure = True
    change_ids: set[str] = set()

    for raw_line in section:
        if raw_line == "":
            continue

        if raw_line in MAP_LABELS:
            expected = MAP_LABELS[expected_label_index] if expected_label_index < len(MAP_LABELS) else None
            if raw_line != expected:
                violations.append(
                    Violation(design_path, f"noncanonical Realization Map section order: expected {expected}, found {raw_line}")
                )
                canonical_structure = False
            else:
                expected_label_index += 1
            current = raw_line
            continue

        if current is None:
            violations.append(Violation(design_path, f"unexpected Realization Map line before Changes: {raw_line}"))
            canonical_structure = False
            continue

        if current == "Changes:":
            match = MAP_CHANGE_RE.match(raw_line)
            if not match:
                violations.append(
                    Violation(
                        design_path,
                        "noncanonical Changes entry; use: - `<change-id>` — <state>",
                    )
                )
                canonical_structure = False
                continue

            change_id, _ = match.groups()
            if change_id in change_ids:
                violations.append(
                    Violation(design_path, f"duplicate Changes entry for change-id: {change_id}")
                )
                canonical_structure = False
                continue
            change_ids.add(change_id)
            continue

        if current in MAPPED_SECTIONS:
            match = MAP_ENTRY_RE.match(raw_line)
            if not match:
                violations.append(
                    Violation(
                        design_path,
                        f"noncanonical {current[:-1]} entry; use: - `<path>` — Target|Realized",
                    )
                )
                canonical_structure = False
                continue

            mapped_path, state = match.groups()
            if any(existing_path == mapped_path for existing_path, _ in entries[current]):
                violations.append(
                    Violation(
                        design_path,
                        f"duplicate {current[:-1]} mapping for path: {mapped_path}",
                    )
                )
                canonical_structure = False
                continue

            entries[current].append((mapped_path, state))

            if not safe_relative_path(mapped_path):
                violations.append(
                    Violation(design_path, f"mapped path must stay inside the repository: {mapped_path}")
                )
            elif state == "Realized" and not mapping_exists(target, mapped_path):
                violations.append(
                    Violation(design_path, f"Realized mapping does not match current repository state: {mapped_path}")
                )
            continue

        violations.append(Violation(design_path, f"unexpected Realization Map line: {raw_line}"))
        canonical_structure = False

    if expected_label_index != len(MAP_LABELS):
        missing = ", ".join(MAP_LABELS[expected_label_index:])
        violations.append(Violation(design_path, f"Realization Map is missing canonical sections: {missing}"))
        canonical_structure = False

    return entries, violations, canonical_structure


def design_violations(target: Path) -> tuple[dict[str, DesignInfo], list[Violation]]:
    designs: dict[str, DesignInfo] = {}
    violations: list[Violation] = []
    design_root = target / "docs" / "designs"
    if not design_root.is_dir():
        return designs, violations

    for path in sorted(design_root.glob("*/DESIGN.md")):
        relative = path.relative_to(target).as_posix()
        text = path.read_text(encoding="utf-8")
        fields, header_errors, _ = canonical_header(
            text,
            relative,
        )
        violations.extend(header_errors)

        status = fields.get("Status")
        if status is None:
            violations.append(Violation(relative, "missing Design `Status:` metadata"))
            continue
        if status not in ALLOWED_DESIGN_STATUSES:
            violations.append(
                Violation(relative, f"invalid Design status {status!r}; expected one of {sorted(ALLOWED_DESIGN_STATUSES)}")
            )

        entries: dict[str, list[tuple[str, str]]] = {}
        if status in {"Implementing", "Realized"}:
            entries, map_errors, has_map = parse_realization_map(target, relative, text)
            violations.extend(map_errors)
            if not has_map:
                violations.append(
                    Violation(relative, f"{status} Design must use `## Realization Map` as its first canonical section")
                )

        if status == "Realized":
            targets = [
                mapped_path
                for section in MAPPED_SECTIONS
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

    lines = index_path.read_text(encoding="utf-8").splitlines()
    header_positions = [index for index, line in enumerate(lines) if line == INDEX_HEADER]
    if not header_positions:
        violations.append(Violation("docs/designs/INDEX.md", "missing canonical Design index table header"))
        return rows, violations
    if len(header_positions) != 1:
        violations.append(Violation("docs/designs/INDEX.md", "must contain exactly one canonical Design index table"))
        return rows, violations
    header_index = header_positions[0]

    if header_index + 1 >= len(lines) or lines[header_index + 1] != INDEX_DELIMITER:
        violations.append(Violation("docs/designs/INDEX.md", "Design index header must be followed immediately by the canonical delimiter"))
        return rows, violations

    for line in lines[header_index + 2 :]:
        if not line.startswith("|"):
            break

        match = INDEX_ROW_RE.match(line)
        if not match:
            violations.append(Violation("docs/designs/INDEX.md", f"noncanonical Design index row: {line}"))
            continue

        label, link, status, areas_cell = match.groups()
        design_id = Path(link).parent.name
        if label != design_id:
            violations.append(
                Violation(
                    "docs/designs/INDEX.md",
                    f"Design index label {label!r} does not match linked Design ID {design_id!r}",
                )
            )
            continue
        if not INDEX_AREAS_RE.match(areas_cell):
            violations.append(
                Violation(
                    "docs/designs/INDEX.md",
                    "noncanonical realized source areas cell; use comma-separated backticked paths",
                )
            )
            continue

        design_path = (Path("docs/designs") / link).as_posix()
        area_values = BACKTICK_VALUE_RE.findall(areas_cell)
        if len(area_values) != len(set(area_values)):
            violations.append(
                Violation(
                    "docs/designs/INDEX.md",
                    f"duplicate realized source area in row for {design_path}",
                )
            )
            continue
        areas = frozenset(area_values)
        if design_path in rows:
            violations.append(Violation("docs/designs/INDEX.md", f"duplicate row for {design_path}"))
            continue

        rows[design_path] = IndexRow(design_path, status, areas)

    return rows, violations


def index_violations(
    designs: dict[str, DesignInfo],
    rows: dict[str, IndexRow],
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
        fields, header_errors, _ = canonical_header(
            path.read_text(encoding="utf-8"),
            relative,
        )
        violations.extend(header_errors)

        design_path = fields.get("Design")
        revision = fields.get("Design-Revision")

        if revision and not design_path:
            violations.append(Violation(relative, "has Design-Revision but no Design field"))
            continue
        if not design_path:
            continue

        if design_path not in designs:
            violations.append(Violation(relative, f"Design does not exist: {design_path}"))

        if not revision:
            violations.append(Violation(relative, "Design-derived Change is missing Design-Revision"))
        elif not REVISION_RE.match(revision):
            violations.append(
                Violation(relative, f"Design-Revision is not a commit-like hex SHA: {revision}")
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
    parser = argparse.ArgumentParser(
        description="Validate an ai-workflow repository against the shipped canonical protocol grammar."
    )
    parser.add_argument(
        "--target",
        type=Path,
        default=Path.cwd(),
        help="Repository to validate (default: current directory)",
    )
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
