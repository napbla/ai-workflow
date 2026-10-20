from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import protocol  # noqa: E402


class RepoFixture:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.write(".ai-workflow.yml", "protocol: 3\n")
        self.write("WORKFLOW.md", "# Test\n\nProtocol: `ai-workflow v3`\n")
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
        lines += ["## Realization Map", "", "Changes:", "- `example` — Realized", "", "Areas:"]
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
            repo.write("WORKFLOW.md", "# Test\n\nProtocol: `ai-workflow v2`\n")
            messages = repo.messages()
            self.assertIn("declares protocol 2; validator supports 3", messages)
            self.assertIn("declares protocol v2; expected v3", messages)

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

    def test_realized_design_cannot_keep_target_mappings(self) -> None:
        tmp, repo = self.make_repo()
        with tmp:
            repo.write("docs/designs/example/DESIGN.md", design_text("Realized", [("src/**", "Target")]))
            self.assertIn("Realized Design still contains Target mappings", repo.messages())

    def test_implementing_design_requires_instance_level_map_not_fenced_example(self) -> None:
        tmp, repo = self.make_repo()
        with tmp:
            repo.write(
                "docs/designs/example/DESIGN.md",
                "# Design\n\nStatus: Implementing\nOwner: architect\n\n"
                "## Notes\n\n```md\n## Realization Map\nAreas:\n- `src/**` — Realized\n```\n",
            )
            self.assertIn("Implementing Design must have an instance-level Realization Map", repo.messages())

    def test_realization_map_heading_without_required_structure_is_rejected(self) -> None:
        tmp, repo = self.make_repo()
        with tmp:
            repo.write(
                "docs/designs/example/DESIGN.md",
                "# Design\n\nStatus: Implementing\nOwner: architect\n\n"
                "## Realization Map\n\n"
                "This heading alone is not a structured map.\n",
            )
            messages = repo.messages()
            self.assertIn("Realization Map is missing required sections", messages)
            self.assertIn("Implementing Design must have an instance-level Realization Map", messages)

    def test_realization_map_accepts_documented_unbackticked_paths(self) -> None:
        tmp, repo = self.make_repo()
        with tmp:
            repo.write("providers/contracts/provider.py", "")
            repo.write(
                "docs/designs/example/DESIGN.md",
                "# Design\n\nStatus: Realized\nOwner: architect\n\n"
                "## Realization Map\n\n"
                "Changes:\n- provider-contract — Realized\n\n"
                "Areas:\n- providers/contracts/** — Realized\n\n"
                "Tests:\n\n"
                "Current-truth docs:\n\n"
                "## Goal\nExample.\n",
            )
            repo.write(
                "docs/designs/INDEX.md",
                "# Design Traceability Index\n\n"
                "| Design | Design status | Realized source areas |\n"
                "| --- | --- | --- |\n"
                "| [example](example/DESIGN.md) | Realized | `providers/contracts/**` |\n",
            )
            self.assertEqual(repo.violations(), [])

    def test_indented_code_block_does_not_count_as_realization_map(self) -> None:
        tmp, repo = self.make_repo()
        with tmp:
            repo.write(
                "docs/designs/example/DESIGN.md",
                "# Design\n\nStatus: Implementing\nOwner: architect\n\n"
                "## Notes\n\n"
                "    ## Realization Map\n"
                "    Changes:\n"
                "    - example — Realized\n"
                "    Areas:\n"
                "    - src/** — Realized\n"
                "    Tests:\n"
                "    Current-truth docs:\n",
            )
            self.assertIn("Implementing Design must have an instance-level Realization Map", repo.messages())

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
                "# Index\n"
                "| Design | Design status | Realized source areas |\n"
                "| --- | --- | --- |\n"
                "| [example](example/DESIGN.md) | Realized | `src/a.py`, `src/b.py` |\n",
            )
            messages = repo.messages()
            self.assertIn("status is Implementing but index says Realized", messages)
            self.assertIn("extra: src/b.py", messages)


    def test_malformed_index_data_row_is_rejected(self) -> None:
        tmp, repo = self.make_repo()
        with tmp:
            repo.write(
                "docs/designs/INDEX.md",
                "# Design Traceability Index\n\n"
                "| Design | Design status | Realized source areas |\n"
                "| --- | --- | --- |\n"
                "| ghost | Realized | `src/**` |\n",
            )
            self.assertIn("invalid Design index row", repo.messages())

    def test_index_areas_cell_must_be_entirely_well_formed(self) -> None:
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
                "| [example](example/DESIGN.md) | Implementing | `src/a.py`, src/stale.py |\n",
            )
            self.assertIn("invalid realized source areas cell", repo.messages())

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
                "# Index\n"
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
                "# Change\n\nStatus: In Progress\nOwner: implementer\n"
                "Design: docs/designs/example/DESIGN.md\n\n## Goal\nWork.\n",
            )
            self.assertIn("Design-derived Change is missing Design-Revision", repo.messages())

            repo.write(
                "docs/changes/work/CHANGE.md",
                "# Change\n\nStatus: In Progress\nOwner: implementer\n"
                "Design: docs/designs/example/DESIGN.md\n"
                "Design-Revision: 0123456789abcdef0123456789abcdef01234567\n\n"
                "## Goal\nWork.\n",
            )
            self.assertEqual(repo.violations(), [])

    def test_revision_without_design_is_rejected(self) -> None:
        tmp, repo = self.make_repo()
        with tmp:
            repo.write(
                "docs/changes/work/CHANGE.md",
                "# Change\n\nStatus: In Progress\nOwner: implementer\n"
                "Design-Revision: 0123456789abcdef0123456789abcdef01234567\n\n"
                "## Goal\nWork.\n",
            )
            self.assertIn("has Design-Revision but no Design field", repo.messages())


    def test_target_resolution_error_returns_exit_2(self) -> None:
        stderr = io.StringIO()
        with mock.patch.object(protocol.Path, "resolve", side_effect=OSError("cannot resolve")), contextlib.redirect_stderr(stderr):
            code = protocol.main(["--target", "unreadable"])
        self.assertEqual(code, 2)
        self.assertIn("Protocol validation could not read repository state", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
