from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

GUARD_PATH = Path(__file__).resolve().parents[1] / "protected_branch_guard.py"
spec = importlib.util.spec_from_file_location("protected_branch_guard", GUARD_PATH)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


def git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


class RepoTestCase(unittest.TestCase):
    """Runs each test inside a throwaway repo checked out on a feature branch."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        git(self.repo, "init", "-q", "-b", "develop")
        git(self.repo, "-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "--allow-empty", "-m", "init")
        git(self.repo, "checkout", "-q", "-b", "feature/x")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def assertAllowed(self, command: str) -> None:
        self.assertIsNone(guard.check_command(command, str(self.repo)), command)

    def assertDenied(self, command: str) -> None:
        self.assertIsNotNone(guard.check_command(command, str(self.repo)), command)


class AllowedCommandsTest(RepoTestCase):
    def test_feature_branch_pushes_are_allowed(self) -> None:
        for command in [
            "git push origin feature/x",
            "git push -u origin feature/x",
            "git push --set-upstream origin feature/x",
            "git push origin HEAD",
            "git push origin HEAD:feature/x",
            "git push --force-with-lease origin feature/x",
            "git push origin feature/x:feature/x",
            "git push",
            "git push origin",
            "git -C . push origin feature/x",
        ]:
            self.assertAllowed(command)

    def test_unrelated_commands_are_allowed(self) -> None:
        for command in [
            "git status && git log --oneline main..develop",
            "git fetch origin main develop",
            "git checkout develop",
            "git switch main",
            "git diff origin/develop...HEAD",
            "git checkout -b feature/y --no-track origin/develop",
            "git switch -c feature/y --no-track origin/develop",
            "git branch feature/y develop",
            "git branch --set-upstream-to=origin/feature/x",
            'git commit -m "docs: mention main and develop"',
            "echo git push origin main",
            "python3 -m unittest discover -s init/tests",
        ]:
            self.assertAllowed(command)

    def test_heredoc_commit_message_is_allowed(self) -> None:
        self.assertAllowed("git commit -q -F - <<'EOF'\nfeat: don't break develop\n\nIt's fine.\nEOF")

    def test_messages_describing_protected_pushes_are_allowed(self) -> None:
        for command in [
            "git commit -m \"$(cat <<'EOF'\nfeat: guard\n\nImplementers can't git push to main or develop.\nEOF\n)\"",
            "gh pr create --base develop --body \"$(cat <<'EOF'\n- Block git push to main; don't allow develop upstream\ngit push origin main\nEOF\n)\"",
            "git commit -m \"docs\n\nUse git checkout -b feature/x origin/develop --no-track\"",
            "cat > notes.md <<-EOF\n\tgit push origin develop\n\tEOF\ngit add notes.md",
        ]:
            self.assertAllowed(command)


class DeniedCommandsTest(RepoTestCase):
    def test_protected_destinations_are_denied(self) -> None:
        for command in [
            "git push origin main",
            "git push origin develop",
            "git push origin +main",
            "git push origin HEAD:main",
            "git push origin feature/x:develop",
            "git push origin feature/x:refs/heads/main",
            "git push origin :develop",
            "git push -u origin develop",
            "git push --force origin main",
            "git push origin 'refs/heads/*:refs/heads/*'",
            "git -C . push origin main",
            "GIT_TRACE=1 git push origin main",
        ]:
            self.assertDenied(command)

    def test_all_and_mirror_pushes_are_denied(self) -> None:
        for command in ["git push --all origin", "git push --mirror origin", "git push --branches origin"]:
            self.assertDenied(command)

    def test_matching_pushes_are_denied(self) -> None:
        for command in [
            "git push origin :",
            "git push origin +:",
            "git -c push.default=matching push",
            "git config push.default matching",
        ]:
            self.assertDenied(command)
        git(self.repo, "config", "push.default", "matching")
        self.assertDenied("git push")
        self.assertAllowed("git push origin feature/x")

    def test_commands_after_heredoc_are_still_checked(self) -> None:
        for command in [
            "cat > msg <<'EOF'\nnotes\nEOF\ngit push origin main",
            'git commit -m "fix <<EOF parsing"\ngit push origin main',
            "echo 'a <<EOF'\ngit push origin develop",
            "bash <<'EOF'\ngit push origin main\nEOF",
        ]:
            self.assertDenied(command)

    def test_inline_config_redirecting_push_is_denied(self) -> None:
        for command in [
            "git -c remote.origin.push=HEAD:refs/heads/main push origin",
            "git -c branch.feature/x.merge=refs/heads/develop push",
            "git -c remote.origin.mirror=true push origin",
            "git config set push.default matching",
            "git config set branch.feature/x.merge refs/heads/main",
            "git config remote.origin.mirror true",
        ]:
            self.assertDenied(command)
        self.assertAllowed("git -c user.name=x push origin feature/x")

    def test_attached_branch_creation_arguments_are_checked(self) -> None:
        for command in [
            "git checkout -bfeature/y origin/develop",
            "git switch -cfeature/y origin/main",
            "git switch --create=feature/y origin/develop",
            "git switch --force-create=feature/y origin/main",
        ]:
            self.assertDenied(command)
        self.assertAllowed("git checkout -bfeature/y --no-track origin/develop")
        self.assertAllowed("git switch --create=feature/y")

    def test_configured_remote_push_refspec_is_checked(self) -> None:
        git(self.repo, "config", "remote.origin.push", "HEAD:refs/heads/main")
        self.assertDenied("git push origin")
        self.assertDenied("git push")
        self.assertAllowed("git push origin feature/x")

    def test_configured_mirror_remote_is_denied(self) -> None:
        git(self.repo, "config", "remote.backup.mirror", "true")
        self.assertDenied("git push backup")

    def test_repository_selected_by_global_options_is_used(self) -> None:
        with tempfile.TemporaryDirectory() as other_tmp:
            other = Path(other_tmp)
            git(other, "init", "-q", "-b", "main")
            git(other, "-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "--allow-empty", "-m", "init")
            for command in [
                f"git --git-dir={other}/.git --work-tree={other} push",
                f"git --git-dir {other}/.git push origin",
                f"git -C {other} push",
            ]:
                self.assertDenied(command)
        self.assertAllowed("git push")

    def test_abbreviated_long_options_are_expanded(self) -> None:
        for command in [
            "git push --mir origin",
            "git push --br origin",
            "git push --al origin",
            "git branch --set-upstream=origin/develop",
            "git switch --cr=feature/y origin/main",
        ]:
            self.assertDenied(command)
        self.assertAllowed("git checkout -b feature/y --no-tr origin/develop")

    def test_repo_option_selects_remote_for_configured_push(self) -> None:
        git(self.repo, "config", "remote.other.push", "HEAD:refs/heads/main")
        self.assertDenied("git push --repo=other")
        self.assertDenied("git push --repo other")
        self.assertAllowed("git push --repo=origin")

    def test_config_value_options_are_skipped(self) -> None:
        for command in [
            "git config --file .git/config remote.origin.push HEAD:refs/heads/main",
            "git config -f .git/config branch.feature/x.merge refs/heads/develop",
            "git config --type bool remote.origin.mirror true",
        ]:
            self.assertDenied(command)
        self.assertAllowed("git config --file .git/config user.name x")

    def test_remote_head_upstream_is_denied(self) -> None:
        self.assertDenied("git branch -u origin/HEAD")
        self.assertDenied("git checkout -b feature/y origin/HEAD")

    def test_shell_option_terminator_is_skipped(self) -> None:
        self.assertDenied("bash -c -- 'git push origin main'")

    def test_attached_upstream_option_is_denied(self) -> None:
        self.assertDenied("git branch -uorigin/develop")
        self.assertAllowed("git branch -uorigin/feature/x")

    def test_compound_and_nested_commands_are_checked(self) -> None:
        for command in [
            "git status && git push origin main",
            "true; git push origin develop",
            "bash -c 'git push origin main'",
            "sh -lc \"git push origin develop\"",
            "git add -A\ngit push origin main",
        ]:
            self.assertDenied(command)

    def test_setting_protected_upstream_is_denied(self) -> None:
        for command in [
            "git branch --set-upstream-to=origin/main",
            "git branch -u origin/develop",
            "git branch --set-upstream-to origin/develop feature/x",
            "git config branch.feature/x.merge refs/heads/develop",
            "git config remote.origin.push refs/heads/feature/x:refs/heads/main",
            "git checkout -b feature/y origin/develop",
            "git switch -c feature/y origin/main",
            "git branch feature/y origin/develop",
            "git branch --track feature/y develop",
        ]:
            self.assertDenied(command)

    def test_refspecless_push_from_protected_branch_is_denied(self) -> None:
        git(self.repo, "checkout", "-q", "develop")
        for command in ["git push", "git push origin", "git push origin HEAD"]:
            self.assertDenied(command)

    def test_refspecless_push_with_protected_upstream_is_denied(self) -> None:
        git(self.repo, "config", "branch.feature/x.remote", "origin")
        git(self.repo, "config", "branch.feature/x.merge", "refs/heads/develop")
        self.assertDenied("git push")
        self.assertAllowed("git push origin feature/x")


class HookProtocolTest(unittest.TestCase):
    def run_hook(self, payload: dict) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(GUARD_PATH)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            timeout=30,
        )

    def test_denied_command_exits_2_with_reason(self) -> None:
        result = self.run_hook({"tool_name": "Bash", "tool_input": {"command": "git push origin main"}})
        self.assertEqual(result.returncode, 2)
        self.assertIn("protected branch policy", result.stderr)

    def test_allowed_command_exits_0(self) -> None:
        result = self.run_hook({"tool_name": "Bash", "tool_input": {"command": "git push origin feature/x"}})
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_non_bash_tool_is_ignored(self) -> None:
        result = self.run_hook({"tool_name": "Write", "tool_input": {"file_path": "x"}})
        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
