from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

INIT_SCRIPT = Path(__file__).resolve().parents[1] / "init.py"
VERSION_PATH = Path(__file__).resolve().parents[2] / "spec" / "VERSION"


class VersionFlagTest(unittest.TestCase):
    def run_init(self, *args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(INIT_SCRIPT), *args],
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=30,
        )

    def test_version_prints_protocol_version_from_spec(self) -> None:
        expected = f"ai-workflow protocol v{VERSION_PATH.read_text(encoding='utf-8').strip()}\n"
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_init("--version", cwd=Path(tmp))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, expected)

    def test_version_writes_no_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            target = cwd / "target"
            for args in (["--version"], ["--version", "--target", str(target)]):
                result = self.run_init(*args, cwd=cwd)
                self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(list(cwd.iterdir()), [])


class GeneratedProjectTest(unittest.TestCase):
    def generate(self, target: Path, answers: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(INIT_SCRIPT), "--target", str(target), "--conflict", "abort"],
            input=answers,
            capture_output=True,
            text=True,
            timeout=30,
        )

    def test_default_roles_use_runtime_neutral_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "proj"
            result = self.generate(target, "proj\n\n")
            self.assertEqual(result.returncode, 0, result.stderr)

            version = VERSION_PATH.read_text(encoding="utf-8").strip()
            self.assertEqual((target / ".ai-workflow.yml").read_text(encoding="utf-8"), f"protocol: {version}\n")
            self.assertEqual(sorted(p.name for p in (target / ".agents").iterdir()), ["architect.md", "implementer.md", "reviewer.md"])
            self.assertIn("**Role ID:** `implementer`", (target / ".agents" / "implementer.md").read_text(encoding="utf-8"))
            self.assertIn("- **Reviewer** — `reviewer` (`.agents/reviewer.md`)", (target / "AGENTS.md").read_text(encoding="utf-8"))

            workflow = (target / "WORKFLOW.md").read_text(encoding="utf-8")
            self.assertIn(f"Protocol: `ai-workflow v{version}`", workflow)
            self.assertIn("## Core Lifecycle: Design → Change → Source", workflow)
            self.assertIn("design/<design-id>", workflow)
            self.assertIn("Design-Revision:", workflow)
            self.assertIn("### Merge-safe status", workflow)

            for path in target.rglob("*.md"):
                text = path.read_text(encoding="utf-8")
                for vendor in ("ChatGPT", "Claude", "Codex"):
                    self.assertNotIn(vendor, text, f"{vendor} in {path}")

    def test_v3_design_registry_is_initialized(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "proj"
            result = self.generate(target, "proj\n\n")
            self.assertEqual(result.returncode, 0, result.stderr)

            index = target / "docs" / "designs" / "INDEX.md"
            self.assertTrue(index.is_file())
            index_text = index.read_text(encoding="utf-8")
            self.assertIn("# Design Traceability Index", index_text)
            self.assertIn("realized Design mappings only", index_text)
            self.assertNotIn("Target-only", "\n".join(line for line in index_text.splitlines() if line.startswith("| ")))

            status = (target / "docs" / "status" / "CURRENT.md").read_text(encoding="utf-8")
            self.assertIn("## Designs", status)
            self.assertIn("docs/designs/INDEX.md", status)

    def test_selected_roles_and_unknown_role_retry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "proj"
            result = self.generate(target, "proj\nnope\ngeneralist, reviewer\n")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Unknown role IDs: nope", result.stdout)
            self.assertEqual(sorted(p.name for p in (target / ".agents").iterdir()), ["generalist.md", "reviewer.md"])

    def test_non_string_role_id_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            roles = Path(tmp) / "roles.yaml"
            roles.write_text("roles:\n  123:\n    name: Numeric\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(INIT_SCRIPT), "--target", str(Path(tmp) / "proj"), "--roles", str(roles)],
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("Invalid role IDs", result.stderr)

    def test_self_bootstrap_matches_repository(self) -> None:
        repo_root = INIT_SCRIPT.parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "self"
            agents = sorted(p.stem for p in (repo_root / ".agents").glob("*.md"))
            result = self.generate(target, f"ai-workflow\n{','.join(agents)}\n")
            self.assertEqual(result.returncode, 0, result.stderr)

            generated = [".ai-workflow.yml", "WORKFLOW.md", "AGENTS.md", "docs/WORK_TRACKING.md"]
            generated += [f".agents/{agent}.md" for agent in agents]
            for relative in generated:
                self.assertEqual(
                    (repo_root / relative).read_text(encoding="utf-8"),
                    (target / relative).read_text(encoding="utf-8"),
                    f"{relative} differs from init output; regenerate it from spec/templates",
                )


if __name__ == "__main__":
    unittest.main()
