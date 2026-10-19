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


if __name__ == "__main__":
    unittest.main()
