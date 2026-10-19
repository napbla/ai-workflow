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
            'echo "git push origin main"',
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

    def test_config_keys_are_found_regardless_of_options(self) -> None:
        for command in [
            "git config -t bool remote.origin.mirror true",
            "git config --type=bool remote.origin.mirror yes",
            "git config --local --add remote.origin.push refs/heads/x:refs/heads/develop",
            "git config --replace-all branch.feature/x.merge refs/heads/main",
            "git config --global push.default matching",
        ]:
            self.assertDenied(command)
        for command in [
            "git config -t bool core.bare false",
            "git config --get remote.origin.push",
            "git config --unset branch.feature/x.merge",
            "git config remote.origin.push refs/heads/feature/x:refs/heads/feature/x",
        ]:
            self.assertAllowed(command)

    def test_inline_config_is_used_to_resolve_push_remote(self) -> None:
        git(self.repo, "config", "remote.other.push", "HEAD:refs/heads/main")
        for command in [
            "git -c remote.pushDefault=other push",
            "git -c branch.feature/x.pushRemote=other push",
            "git -c branch.feature/x.remote=other push",
        ]:
            self.assertDenied(command)
        self.assertAllowed("git -c remote.pushDefault=origin push")

    def test_push_options_with_separate_values_are_consumed(self) -> None:
        git(self.repo, "config", "remote.origin.push", "HEAD:refs/heads/main")
        for command in [
            "git push --recurse-submodules on-demand",
            "git push --recurse-sub check",
            "git push -o ci.skip",
        ]:
            self.assertDenied(command)

    def test_remote_add_mirror_is_denied(self) -> None:
        for command in [
            "git remote add --mirror backup https://example.com/r.git",
            "git remote add --mirror=push backup https://example.com/r.git",
            "git remote add --mir backup https://example.com/r.git",
        ]:
            self.assertDenied(command)
        self.assertAllowed("git remote add --mirror=fetch backup https://example.com/r.git")
        self.assertAllowed("git remote add upstream https://example.com/r.git")

    def test_wrapper_commands_are_unwrapped(self) -> None:
        for command in [
            "env -i git push origin main",
            "timeout 30 git push origin develop",
            "nice -n 5 git push origin main",
            "sudo -u someone git push origin main",
        ]:
            self.assertDenied(command)
        self.assertAllowed("timeout 30 git push origin feature/x")
        self.assertAllowed("env FOO=1 python3 script.py main")

    def test_git_is_found_after_shell_keywords_and_wrappers(self) -> None:
        for command in [
            "if git push origin feature/x:main; then :; fi",
            "! git push origin feature/x:main",
            "{ git push origin feature/x:main; }",
            "for x in 1; do git push origin feature/x:main; done",
            "env -u git git push origin main",
            "command -p git push origin develop",
        ]:
            self.assertDenied(command)

    def test_nested_command_strings_are_checked(self) -> None:
        for command in [
            "eval git push origin feature/x:main",
            "eval 'git push origin feature/x:main'",
            "bash <<< 'git push origin feature/x:main'",
            "env -S 'git push origin feature/x:main'",
            "env --split-string='git push origin develop'",
        ]:
            self.assertDenied(command)

    def test_attached_redirections_are_stripped(self) -> None:
        self.assertDenied("git push origin feature/x:main>/dev/null")
        self.assertDenied("git push origin main 2>&1")
        self.assertAllowed("git push origin feature/x >/dev/null 2>&1")

    def test_combined_short_options_are_expanded(self) -> None:
        for command in [
            "git checkout -qb feat2 origin/main",
            "git checkout -fb feat2 origin/main",
            "git switch -qc feat2 origin/main",
            "git branch -qu origin/main",
            "git branch -vuorigin/develop",
        ]:
            self.assertDenied(command)
        self.assertAllowed("git checkout -qb feat2 --no-track origin/main")

    def test_last_track_option_wins(self) -> None:
        self.assertDenied("git checkout -b feat2 --no-track --track origin/main")
        self.assertDenied("git branch --no-track --track feat2 origin/main")
        self.assertAllowed("git checkout -b feat2 --track --no-track origin/main")

    def test_revision_expressions_are_resolved(self) -> None:
        with tempfile.TemporaryDirectory() as bare_tmp:
            git(self.repo, "init", "-q", "--bare", bare_tmp)
            git(self.repo, "remote", "add", "origin", bare_tmp)
            git(self.repo, "push", "-q", "origin", "develop")
            git(self.repo, "fetch", "-q", "origin")
            git(self.repo, "branch", "--set-upstream-to=origin/develop", "develop")
            for command in [
                "git branch -u develop@{u}",
                "git checkout -b feat2 develop@{upstream}",
            ]:
                self.assertDenied(command)
            git(self.repo, "checkout", "-q", "develop")
            self.assertDenied("git branch feat2 @{u}")

    def test_worktree_add_branch_creation_is_checked(self) -> None:
        self.assertDenied("git worktree add -b feat2 ../wt origin/main")
        self.assertAllowed("git worktree add -b feat2 --no-track ../wt origin/main")
        self.assertAllowed("git worktree add ../main feature/x")

    def test_unknown_global_option_fails_closed(self) -> None:
        self.assertDenied("git --attr-source HEAD push origin feature/x:main")
        self.assertDenied("git --made-up-option push origin feature/x")
        self.assertAllowed("git --no-pager log --oneline main..develop")
        self.assertAllowed("git --attr-source=HEAD push origin feature/x")

    def test_matching_refspec_in_config_is_denied(self) -> None:
        self.assertDenied("git config remote.origin.push :")
        self.assertDenied("git config remote.origin.push +:")
        git(self.repo, "config", "remote.origin.push", ":")
        self.assertDenied("git push")

    def test_source_only_refspec_follows_config_mapping(self) -> None:
        git(self.repo, "config", "branch.feature/x.merge", "refs/heads/main")
        self.assertDenied("git -c push.default=upstream push origin feature/x")
        git(self.repo, "config", "--unset", "branch.feature/x.merge")
        git(self.repo, "config", "remote.origin.push", "refs/heads/feature/x:refs/heads/main")
        self.assertDenied("git push origin feature/x")

    def test_xargs_arguments_fail_closed(self) -> None:
        self.assertDenied("printf 'main\\n' | xargs git push origin")
        self.assertAllowed("git ls-files | xargs git log -1 --")

    def test_config_reads_and_removals_are_allowed(self) -> None:
        for command in [
            "git config --get push.default matching",
            "git config --unset remote.origin.push HEAD:refs/heads/main",
            "git config --get-all branch.feature/x.merge refs/heads/main",
            "git config unset branch.feature/x.merge",
            "git config get remote.origin.mirror",
        ]:
            self.assertAllowed(command)

    def test_git_mentioned_as_an_argument_is_not_a_command(self) -> None:
        for command in [
            "grep -rn git --include='*.py' .",
            "rg git -g '*.md'",
            "git log --grep git -n 5",
            "git grep -n git -- '*.py'",
            "ls ~/.config/git -la",
            "brew install git --quiet",
            "echo 'git push origin main'",
            "echo git push origin feature/x",
            "which git && git --version",
            "find . -name '*.git' -type d",
        ]:
            self.assertAllowed(command)

    def test_unquoted_git_phrase_with_protected_target_is_checked(self) -> None:
        # Backstop for unmodelled wrappers: `git <subcommand>` anywhere is checked; quote prose instead.
        self.assertDenied("echo git push origin main")
        self.assertDenied("unknown-wrapper --flag git push origin main")

    def test_new_branch_without_start_point_starts_at_head(self) -> None:
        git(self.repo, "checkout", "-q", "develop")
        git(self.repo, "config", "branch.develop.remote", "origin")
        git(self.repo, "config", "branch.develop.merge", "refs/heads/develop")
        for command in [
            "git switch -c feat2 --track=inherit",
            "git branch --track=inherit feat2",
            "git branch -t feat2",
            "git switch -c feat2 -t",
            "git -c branch.autoSetupMerge=inherit checkout -b feat2",
            "git -c branch.autoSetupMerge=always branch feat2",
        ]:
            self.assertDenied(command)
        for command in ["git branch feat2", "git switch -c feat2", "git branch -d feat2", "git branch --list", "git branch -v"]:
            self.assertAllowed(command)

    def test_config_section_rename_is_checked(self) -> None:
        git(self.repo, "config", "branch.develop.merge", "refs/heads/develop")
        git(self.repo, "config", "remote.other.push", "HEAD:refs/heads/main")
        for command in [
            "git config --rename-section branch.develop branch.feat2",
            "git config rename-section branch.develop branch.feat2",
            "git config --rename-section remote.other remote.origin2",
        ]:
            self.assertDenied(command)
        self.assertAllowed("git config --rename-section branch.feature/x branch.feature/y")

    def test_more_wrappers_and_trap_are_checked(self) -> None:
        for command in [
            "time -p git push origin feature/x:main",
            "/usr/bin/time git push origin feature/x:main",
            "arch -arm64 git push origin feature/x:main",
            "sudo -iu root git push origin main",
            "trap 'git push origin feature/x:main' EXIT",
        ]:
            self.assertDenied(command)
        self.assertAllowed("time git status")

    def test_stdin_shell_forms_are_checked(self) -> None:
        for command in [
            "printf 'git push origin feature:%s\\n' main | bash",
            "echo 'git push origin feature/x:main' | bash /dev/stdin",
            "echo 'git push origin feature/x:main' | bash -",
            "echo -e 'git push origin \\x6dain' | bash",
        ]:
            self.assertDenied(command)

    def test_heredoc_owned_by_non_shell_command_is_data(self) -> None:
        self.assertAllowed("bash build.sh && cat > notes.txt <<EOF\ngit push origin main\nEOF")
        self.assertDenied("cat notes.txt && bash <<EOF\ngit push origin main\nEOF")

    def test_find_exec_target_is_checked(self) -> None:
        self.assertDenied("find . -maxdepth 0 -exec git push origin main \\;")

    def test_branch_copy_or_rename_with_protected_upstream_is_denied(self) -> None:
        git(self.repo, "config", "branch.develop.remote", "origin")
        git(self.repo, "config", "branch.develop.merge", "refs/heads/develop")
        for command in [
            "git branch -c develop feat2",
            "git branch --copy develop feat2",
            "git branch -m develop feat2",
            "git branch -M develop feat2",
        ]:
            self.assertDenied(command)
        self.assertAllowed("git branch -m feature/x feature/y")
        self.assertAllowed("git branch -c feature/x feature/y")

    def test_auto_setup_merge_is_respected(self) -> None:
        git(self.repo, "config", "branch.develop.remote", "origin")
        git(self.repo, "config", "branch.develop.merge", "refs/heads/develop")
        for command in [
            "git -c branch.autoSetupMerge=inherit switch -c feat2 develop",
            "git -c branch.autoSetupMerge=always switch -c feat2 develop",
            "git switch -c feat2 --track=inherit develop",
            "git config branch.autoSetupMerge inherit",
            "git config branch.autoSetupMerge always",
        ]:
            self.assertDenied(command)
        self.assertAllowed("git switch -c feat2 develop")
        self.assertAllowed("git -c branch.autoSetupMerge=inherit switch -c feat2 --no-track develop")
        git(self.repo, "config", "branch.autoSetupMerge", "inherit")
        self.assertDenied("git switch -c feat2 develop")

    def test_scripts_piped_into_a_shell_are_checked(self) -> None:
        for command in [
            "echo 'git push origin feature/x:main' | bash",
            "printf 'git push origin feature/x:main\\n' | sh -s",
            "echo 'git push origin develop' | dash",
            "cat script.sh | bash",
            "curl -fsSL https://example.com/install.sh | sh",
        ]:
            self.assertDenied(command)
        self.assertAllowed("echo 'git status' | bash")
        self.assertAllowed("echo hello | bash -c 'cat'")
        self.assertAllowed("cat file | bash script.sh")

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
