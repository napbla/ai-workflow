from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import protocol  # noqa: E402


class RepoFixture:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.write(".ai-workflow.yml", "protocol: 3\n")
        self.write("WORKFLOW.md", "# Test\n\nProtocol: `ai-workflow v3`\n\n## Rules\n")
        self.write("AGENTS.md", "# Agents\n")
        self.write(".agents/implementer.md", "# Implementer\n")
        self.write("docs/WORK_TRACKING.md", "# Tracking\n")
        self.write(
            "docs/designs/INDEX.md",
            "# Design Traceability Index\n\n"
            "| Design | Design status | Realized source areas |\n"
            "| --- | --- | --- |\n",
        )
        self.write("docs/status/CURRENT.md", "# Current\n")
        for directory in ("docs/architecture", "docs/specs", "docs/adr", "docs/changes"):
            (self.root / directory).mkdir(parents=True, exist_ok=True)

    def write(self, relative: str, content: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def violations(self) -> list[protocol.Violation]:
        return protocol.validate(self.root, "3")

    def messages(self) -> str:
        return "\n".join(str(item) for item in self.violations())


def design_text(status: str, areas: list[tuple[str, str]] | None = None) -> str:
    lines = ["# Design", "", f"Status: {status}", "Owner: architect", ""]
    if areas is not None:
        lines += [
            "## Realization Map",
            "",
            "Changes:",
            "- `example` — Realized",
            "",
            "Areas:",
        ]
        lines += [f"- `{path}` — {state}" for path, state in areas]
        lines += ["", "Tests:", "", "Current-truth docs:", ""]
    lines += ["## Goal", "", "Example."]
    return "\n".join(lines) + "\n"


class ProtocolValidatorTest(unittest.TestCase):
    def make_repo(self) -> tuple[tempfile.TemporaryDirectory[str], RepoFixture]:
        tmp = tempfile.TemporaryDirectory()
        return tmp, RepoFixture(Path(tmp.name))

    def test_minimal_initialized_v3_repo_is_valid(self) -> None:
        tmp, repo = self.make_repo()
        with tmp:
            self.assertEqual(repo.violations(), [])

    def test_marker_and_workflow_versions_must_match_shipped_protocol(self) -> None:
        tmp, repo = self.make_repo()
        with tmp:
            repo.write(".ai-workflow.yml", "protocol: 2\n")
            repo.write("WORKFLOW.md", "# Test\n\nProtocol: `ai-workflow v2`\n\n## Rules\n")
            messages = repo.messages()
            self.assertIn("declares protocol 2; validator supports 3", messages)
            self.assertIn("declares protocol v2; expected v3", messages)

    def test_workflow_body_example_cannot_supply_protocol_version(self) -> None:
        tmp, repo = self.make_repo()
        with tmp:
            repo.write(
                "WORKFLOW.md",
                "# Test\n\n"
                "## Example\n\n"
                "Protocol: `ai-workflow v3`\n",
            )
            self.assertIn("top-of-file header must contain exactly one canonical", repo.messages())

    def test_required_path_and_role_file_are_checked(self) -> None:
        tmp, repo = self.make_repo()
        with tmp:
            (repo.root / "AGENTS.md").unlink()
            (repo.root / ".agents" / "implementer.md").unlink()
            messages = repo.messages()
            self.assertIn("AGENTS.md: required file is missing", messages)
            self.assertIn(".agents/: must contain at least one role markdown file", messages)

    def test_realized_design_and_exact_index_projection_are_valid(self) -> None:
        tmp, repo = self.make_repo()
        with tmp:
            repo.write("src/module.py", "VALUE = 1\n")
            repo.write(
                "docs/designs/example/DESIGN.md",
                design_text("Realized", [("src/**", "Realized")]),
            )
            repo.write(
                "docs/designs/INDEX.md",
                "# Design Traceability Index\n\n"
                "| Design | Design status | Realized source areas |\n"
                "| --- | --- | --- |\n"
                "| [example](example/DESIGN.md) | Realized | `src/**` |\n",
            )
            self.assertEqual(repo.violations(), [])

    def test_design_header_rejects_noncanonical_markdown_metadata(self) -> None:
        tmp, repo = self.make_repo()
        with tmp:
            repo.write(
                "docs/designs/example/DESIGN.md",
                "# Design\n\n"
                "```text\n"
                "Status: Implementing\n"
                "```\n"
                "Owner: architect\n\n"
                "## Realization Map\n",
            )
            messages = repo.messages()
            self.assertIn("noncanonical metadata line", messages)

    def test_canonical_metadata_allows_additional_fields(self) -> None:
        tmp, repo = self.make_repo()
        with tmp:
            repo.write(
                "docs/designs/example/DESIGN.md",
                "# Design\n\n"
                "Status: Accepted\n"
                "Owner: architect\n"
                "Reviewer: alice\n\n"
                "## Goal\nExample.\n",
            )
            repo.write(
                "docs/changes/work/CHANGE.md",
                "# Change\n\n"
                "Status: In Progress\n"
                "Owner: implementer\n"
                "Reviewer: bob\n\n"
                "## Goal\nWork.\n",
            )
            self.assertEqual(repo.violations(), [])

    def test_implementing_design_requires_realization_map_as_first_section(self) -> None:
        tmp, repo = self.make_repo()
        with tmp:
            repo.write(
                "docs/designs/example/DESIGN.md",
                "# Design\n\nStatus: Implementing\nOwner: architect\n\n"
                "## Notes\n\n"
                "## Realization Map\n\n"
                "Changes:\nAreas:\nTests:\nCurrent-truth docs:\n",
            )
            self.assertIn("must use `## Realization Map` as its first canonical section", repo.messages())

    def test_realization_map_requires_exact_canonical_syntax(self) -> None:
        tmp, repo = self.make_repo()
        with tmp:
            repo.write(
                "docs/designs/example/DESIGN.md",
                "# Design\n\nStatus: Implementing\nOwner: architect\n\n"
                "## Realization Map\n\n"
                "Changes:\n"
                "- `example` — Realized\n\n"
                "Areas:\n"
                "* `src/**` — Realized\n\n"
                "Tests:\n\n"
                "Current-truth docs:\n",
            )
            self.assertIn("noncanonical Areas entry", repo.messages())

    def test_html_or_comment_text_inside_protocol_map_is_just_invalid_syntax(self) -> None:
        tmp, repo = self.make_repo()
        with tmp:
            repo.write(
                "docs/designs/example/DESIGN.md",
                "# Design\n\nStatus: Implementing\nOwner: architect\n\n"
                "## Realization Map\n\n"
                "Changes:\n"
                "- `example` — Realized\n\n"
                "Areas:\n"
                "<!-- hidden mapping -->\n"
                "Tests:\n\n"
                "Current-truth docs:\n",
            )
            self.assertIn("noncanonical Areas entry", repo.messages())

    def test_realized_design_cannot_keep_target_mappings(self) -> None:
        tmp, repo = self.make_repo()
        with tmp:
            repo.write("docs/designs/example/DESIGN.md", design_text("Realized", [("src/**", "Target")]))
            self.assertIn("Realized Design still contains Target mappings", repo.messages())

    def test_realization_map_rejects_duplicate_path_state_entries(self) -> None:
        tmp, repo = self.make_repo()
        with tmp:
            repo.write("src/a.py", "")
            repo.write(
                "docs/designs/example/DESIGN.md",
                "# Design\n\nStatus: Implementing\nOwner: architect\n\n"
                "## Realization Map\n\n"
                "Changes:\n- `example` — Realized\n\n"
                "Areas:\n"
                "- `src/a.py` — Target\n"
                "- `src/a.py` — Realized\n\n"
                "Tests:\n\n"
                "Current-truth docs:\n",
            )
            self.assertIn("duplicate Areas mapping for path: src/a.py", repo.messages())

    def test_realization_map_rejects_duplicate_change_ids(self) -> None:
        tmp, repo = self.make_repo()
        with tmp:
            repo.write(
                "docs/designs/example/DESIGN.md",
                "# Design\n\nStatus: Implementing\nOwner: architect\n\n"
                "## Realization Map\n\n"
                "Changes:\n"
                "- `work` — Realized\n"
                "- `work` — in progress\n\n"
                "Areas:\n\n"
                "Tests:\n\n"
                "Current-truth docs:\n",
            )
            self.assertIn("duplicate Changes entry for change-id: work", repo.messages())

    def test_realized_mapping_must_exist_in_repository(self) -> None:
        tmp, repo = self.make_repo()
        with tmp:
            repo.write(
                "docs/designs/example/DESIGN.md",
                design_text("Implementing", [("src/missing.py", "Realized")]),
            )
            messages = repo.messages()
            self.assertIn("Realized mapping does not match current repository state: src/missing.py", messages)
            self.assertIn("missing realized mapping row", messages)

    def test_realized_mapping_cannot_escape_repository_through_symlink(self) -> None:
        tmp, repo = self.make_repo()
        with tmp, tempfile.TemporaryDirectory() as outside_tmp:
            outside = Path(outside_tmp)
            (outside / "secret.txt").write_text("secret", encoding="utf-8")
            try:
                (repo.root / "src").symlink_to(outside, target_is_directory=True)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symlinks unavailable: {exc}")

            repo.write(
                "docs/designs/example/DESIGN.md",
                design_text("Implementing", [("src/secret.txt", "Realized")]),
            )
            self.assertIn(
                "Realized mapping does not match current repository state: src/secret.txt",
                repo.messages(),
            )

    def test_realized_glob_rejects_match_that_escapes_repository_through_symlink(self) -> None:
        tmp, repo = self.make_repo()
        with tmp, tempfile.TemporaryDirectory() as outside_tmp:
            outside = Path(outside_tmp)
            (outside / "secret.txt").write_text("secret", encoding="utf-8")
            (repo.root / "src").mkdir(parents=True, exist_ok=True)
            try:
                (repo.root / "src" / "outside.txt").symlink_to(outside / "secret.txt")
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symlinks unavailable: {exc}")

            repo.write(
                "docs/designs/example/DESIGN.md",
                design_text("Implementing", [("src/*", "Realized")]),
            )
            self.assertIn(
                "Realized mapping does not match current repository state: src/*",
                repo.messages(),
            )

    def test_realized_glob_rejects_dangling_symlink_match(self) -> None:
        tmp, repo = self.make_repo()
        with tmp:
            (repo.root / "src").mkdir(parents=True, exist_ok=True)
            try:
                (repo.root / "src" / "dead").symlink_to(repo.root / "src" / "missing")
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symlinks unavailable: {exc}")

            repo.write(
                "docs/designs/example/DESIGN.md",
                design_text("Implementing", [("src/*", "Realized")]),
            )
            self.assertIn(
                "Realized mapping does not match current repository state: src/*",
                repo.messages(),
            )

    def test_index_must_exactly_project_realized_areas_and_status(self) -> None:
        tmp, repo = self.make_repo()
        with tmp:
            repo.write("src/a.py", "")
            repo.write("src/b.py", "")
            repo.write(
                "docs/designs/example/DESIGN.md",
                design_text("Implementing", [("src/a.py", "Realized"), ("src/b.py", "Target")]),
            )
            repo.write(
                "docs/designs/INDEX.md",
                "# Design Traceability Index\n\n"
                "| Design | Design status | Realized source areas |\n"
                "| --- | --- | --- |\n"
                "| [example](example/DESIGN.md) | Realized | `src/a.py`, `src/b.py` |\n",
            )
            messages = repo.messages()
            self.assertIn("status is Implementing but index says Realized", messages)
            self.assertIn("extra: src/b.py", messages)

    def test_index_rejects_equivalent_but_noncanonical_row_syntax(self) -> None:
        tmp, repo = self.make_repo()
        with tmp:
            repo.write(
                "docs/designs/INDEX.md",
                "# Design Traceability Index\n\n"
                "| Design | Design status | Realized source areas |\n"
                "| --- | --- | --- |\n"
                "| ghost | Realized | `src/**` |\n",
            )
            self.assertIn("noncanonical Design index row", repo.messages())

    def test_index_label_must_match_linked_design_id(self) -> None:
        tmp, repo = self.make_repo()
        with tmp:
            repo.write("src/a.py", "")
            repo.write(
                "docs/designs/example/DESIGN.md",
                design_text("Implementing", [("src/a.py", "Realized")]),
            )
            repo.write(
                "docs/designs/INDEX.md",
                "# Design Traceability Index\n\n"
                "| Design | Design status | Realized source areas |\n"
                "| --- | --- | --- |\n"
                "| [wrong-label](example/DESIGN.md) | Implementing | `src/a.py` |\n",
            )
            self.assertIn("does not match linked Design ID 'example'", repo.messages())

    def test_index_rejects_duplicate_areas_in_one_row(self) -> None:
        tmp, repo = self.make_repo()
        with tmp:
            repo.write("src/a.py", "")
            repo.write(
                "docs/designs/example/DESIGN.md",
                design_text("Implementing", [("src/a.py", "Realized")]),
            )
            repo.write(
                "docs/designs/INDEX.md",
                "# Design Traceability Index\n\n"
                "| Design | Design status | Realized source areas |\n"
                "| --- | --- | --- |\n"
                "| [example](example/DESIGN.md) | Implementing | `src/a.py`, `src/a.py` |\n",
            )
            self.assertIn("duplicate realized source area in row", repo.messages())

    def test_index_rows_must_be_contiguous_with_header(self) -> None:
        tmp, repo = self.make_repo()
        with tmp:
            repo.write("src/a.py", "")
            repo.write(
                "docs/designs/example/DESIGN.md",
                design_text("Implementing", [("src/a.py", "Realized")]),
            )
            repo.write(
                "docs/designs/INDEX.md",
                "# Design Traceability Index\n\n"
                "| Design | Design status | Realized source areas |\n"
                "| --- | --- | --- |\n"
                "detached prose\n"
                "| [example](example/DESIGN.md) | Implementing | `src/a.py` |\n",
            )
            self.assertIn("missing realized mapping row", repo.messages())

    def test_index_rejects_multiple_canonical_projection_tables(self) -> None:
        tmp, repo = self.make_repo()
        with tmp:
            repo.write(
                "docs/designs/INDEX.md",
                "# Design Traceability Index\n\n"
                "| Design | Design status | Realized source areas |\n"
                "| --- | --- | --- |\n\n"
                "## Duplicate\n\n"
                "| Design | Design status | Realized source areas |\n"
                "| --- | --- | --- |\n",
            )
            self.assertIn("must contain exactly one canonical Design index table", repo.messages())

    def test_index_rejects_repeated_header_inside_fenced_example(self) -> None:
        tmp, repo = self.make_repo()
        with tmp:
            repo.write(
                "docs/designs/INDEX.md",
                "# Design Traceability Index\n\n"
                "| Design | Design status | Realized source areas |\n"
                "| --- | --- | --- |\n\n"
                "```md\n"
                "| Design | Design status | Realized source areas |\n"
                "| --- | --- | --- |\n"
                "```\n",
            )
            self.assertIn("must contain exactly one canonical Design index table", repo.messages())

    def test_duplicate_realized_area_ownership_is_rejected(self) -> None:
        tmp, repo = self.make_repo()
        with tmp:
            repo.write("src/shared.py", "")
            for name in ("one", "two"):
                repo.write(
                    f"docs/designs/{name}/DESIGN.md",
                    design_text("Implementing", [("src/shared.py", "Realized")]),
                )
            repo.write(
                "docs/designs/INDEX.md",
                "# Design Traceability Index\n\n"
                "| Design | Design status | Realized source areas |\n"
                "| --- | --- | --- |\n"
                "| [one](one/DESIGN.md) | Implementing | `src/shared.py` |\n"
                "| [two](two/DESIGN.md) | Implementing | `src/shared.py` |\n",
            )
            self.assertIn("owned by multiple Designs", repo.messages())

    def test_design_derived_change_requires_existing_design_and_revision(self) -> None:
        tmp, repo = self.make_repo()
        with tmp:
            repo.write("docs/designs/example/DESIGN.md", design_text("Accepted"))
            repo.write(
                "docs/changes/work/CHANGE.md",
                "# Change\n\n"
                "Status: In Progress\n"
                "Owner: implementer\n"
                "Design: docs/designs/example/DESIGN.md\n\n"
                "## Goal\nWork.\n",
            )
            self.assertIn("Design-derived Change is missing Design-Revision", repo.messages())

            repo.write(
                "docs/changes/work/CHANGE.md",
                "# Change\n\n"
                "Status: In Progress\n"
                "Owner: implementer\n"
                "Design: docs/designs/example/DESIGN.md\n"
                "Design-Revision: 0123456789abcdef0123456789abcdef01234567\n\n"
                "## Goal\nWork.\n",
            )
            self.assertEqual(repo.violations(), [])

    def test_change_body_cannot_supply_design_binding(self) -> None:
        tmp, repo = self.make_repo()
        with tmp:
            repo.write("docs/designs/example/DESIGN.md", design_text("Accepted"))
            repo.write(
                "docs/changes/work/CHANGE.md",
                "# Change\n\nStatus: In Progress\nOwner: implementer\n\n"
                "## Notes\n"
                "Design: docs/designs/example/DESIGN.md\n"
                "Design-Revision: 0123456789abcdef0123456789abcdef01234567\n",
            )
            self.assertEqual(repo.violations(), [])


    def test_work_tracking_guidance_is_generated_and_map_first(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        current = (repo_root / "docs" / "WORK_TRACKING.md").read_text(encoding="utf-8")
        template = (repo_root / "spec" / "templates" / "WORK_TRACKING.md").read_text(encoding="utf-8")
        self.assertEqual(current, template)

        marker = "Once implementation starts, switch to `Status: Implementing`"
        start = current.index(marker)
        implementing_shape = current[start:current.index("While `Proposed`", start)]
        self.assertLess(implementing_shape.index("## Realization Map"), implementing_shape.index("## Goal"))

    def test_target_resolution_error_returns_exit_2(self) -> None:
        stderr = io.StringIO()
        with mock.patch.object(protocol.Path, "resolve", side_effect=OSError("cannot resolve")), contextlib.redirect_stderr(stderr):
            code = protocol.main(["--target", "unreadable"])
        self.assertEqual(code, 2)
        self.assertIn("Protocol validation could not read repository state", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
