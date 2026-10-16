#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path
from string import Template
from typing import Any

try:
    import yaml
except ImportError:
    print("Missing dependency: PyYAML. Install with: pip install -r requirements.txt", file=sys.stderr)
    raise SystemExit(2)

MODULE_DIR = Path(__file__).resolve().parent
REPO_ROOT = MODULE_DIR.parent
SPEC_DIR = REPO_ROOT / "spec"
DEFAULT_ROLES_PATH = SPEC_DIR / "roles.yaml"
TEMPLATES_DIR = SPEC_DIR / "templates"
VERSION_PATH = SPEC_DIR / "VERSION"


def protocol_version() -> str:
    return VERSION_PATH.read_text(encoding="utf-8").strip()


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "agent"


def load_roles(path: Path) -> dict[str, dict[str, Any]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    roles = data.get("roles")
    if not isinstance(roles, dict) or not roles:
        raise ValueError(f"No roles found in {path}")
    return roles


def load_template(name: str) -> Template:
    return Template((TEMPLATES_DIR / name).read_text(encoding="utf-8"))


def ask(prompt: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{prompt}{suffix}: ").strip()
    return value or (default or "")


def choose_role(roles: dict[str, dict[str, Any]]) -> tuple[str, dict[str, Any]]:
    items = list(roles.items())
    print("\nRoles:")
    for index, (_, role) in enumerate(items, start=1):
        print(f"  {index}. {role.get('name', 'Unnamed')}")

    while True:
        raw = input("Select role: ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(items):
            return items[int(raw) - 1]
        if raw in roles:
            return raw, roles[raw]
        print("Invalid role. Enter a number or role key.")


def bullets(values: Any) -> str:
    if not values:
        return "- None"
    return "\n".join(f"- {value}" for value in values)


def authority_lines(authority: Any) -> str:
    if not isinstance(authority, dict) or not authority:
        return "- Not specified"
    return "\n".join(f"- **{key}**: `{value}`" for key, value in authority.items())


def render_agent(agent: dict[str, Any]) -> str:
    role = agent["role"]
    return load_template("agent.md").substitute(
        agent_name=agent["name"],
        agent_slug=agent["slug"],
        role_name=role.get("name", agent["role_key"]),
        responsibilities=bullets(role.get("responsibilities")),
        capabilities=bullets(role.get("capabilities")),
        authority=authority_lines(role.get("authority")),
    )


def resolve_conflict(path: Path, mode: str) -> str:
    if not path.exists():
        return "write"
    if mode in {"skip", "overwrite", "abort"}:
        return mode

    while True:
        choice = input(f"{path} exists — [s]kip / [o]verwrite / [a]bort [s]: ").strip().lower() or "s"
        mapping = {
            "s": "skip", "skip": "skip",
            "o": "overwrite", "overwrite": "overwrite",
            "a": "abort", "abort": "abort",
        }
        if choice in mapping:
            return mapping[choice]
        print("Choose skip, overwrite, or abort.")


def write_file(path: Path, content: str, conflict_mode: str) -> bool:
    action = resolve_conflict(path, conflict_mode)
    if action == "abort":
        raise KeyboardInterrupt
    if action == "skip":
        print(f"skip   {path}")
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"write  {path}")
    return True


def collect_agents(roles: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    agents: list[dict[str, Any]] = []
    used_slugs: set[str] = set()

    while True:
        name = input("\nAgent name (blank to finish): ").strip()
        if not name:
            break

        slug = slugify(name)
        if slug in used_slugs:
            print(f"Agent ID '{slug}' already exists. Choose a different name.")
            continue

        role_key, role = choose_role(roles)
        agents.append({"name": name, "slug": slug, "role_key": role_key, "role": role})
        used_slugs.add(slug)

    return agents


class ProtocolVersionAction(argparse.Action):
    """Print the protocol version and exit; reads spec/VERSION only when invoked."""

    def __init__(self, option_strings: list[str], dest: str, **kwargs: Any) -> None:
        super().__init__(option_strings, dest, nargs=0, default=argparse.SUPPRESS, **kwargs)

    def __call__(self, parser: argparse.ArgumentParser, namespace: argparse.Namespace, values: Any, option_string: str | None = None) -> None:
        try:
            version = protocol_version()
        except OSError as exc:
            parser.exit(2, f"Failed to load protocol: {exc}\n")
        print(f"ai-workflow protocol v{version}")
        parser.exit()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Initialize an ai-workflow project from the local protocol spec.")
    parser.add_argument("--version", action=ProtocolVersionAction, help="Show the protocol version shipped with this checkout and exit")
    target_group = parser.add_mutually_exclusive_group()
    target_group.add_argument("--target", type=Path, help="Target repository directory (default: current directory)")
    target_group.add_argument("--self", action="store_true", help="Initialize the ai-workflow monorepo itself")
    parser.add_argument("--roles", type=Path, default=DEFAULT_ROLES_PATH, help="Role configuration YAML")
    parser.add_argument("--conflict", choices=["ask", "skip", "overwrite", "abort"], default="ask", help="How to handle existing generated files")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    target = REPO_ROOT if args.self else (args.target or Path.cwd()).resolve()
    target.mkdir(parents=True, exist_ok=True)

    try:
        version = protocol_version()
        roles = load_roles(args.roles)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"Failed to load protocol: {exc}", file=sys.stderr)
        return 2

    print(f"AI Workflow Initializer — protocol v{version}")
    print(f"Target: {target}")
    if args.self:
        print("Mode: self-bootstrap monorepo")

    default_project_name = "AI Workflow" if args.self else target.name
    project_name = ask("Project name", default_project_name)
    agents = collect_agents(roles)

    workflow = load_template("WORKFLOW.md").substitute(
        project_name=project_name,
        protocol_version=version,
    )
    registry = "\n".join(
        f"- **{a['name']}** — {a['role'].get('name', a['role_key'])} (`.agents/{a['slug']}.md`)"
        for a in agents
    ) or "_No agents configured yet._"
    agents_md = load_template("AGENTS.md").substitute(agent_registry=registry)
    work_tracking_md = load_template("WORK_TRACKING.md").substitute()
    status_md = load_template("STATUS.md").substitute(
        project_name=project_name,
        updated_date=date.today().isoformat(),
    )
    marker = f"protocol: {version}\n"

    conflict_mode = args.conflict
    try:
        write_file(target / ".ai-workflow.yml", marker, conflict_mode)
        write_file(target / "WORKFLOW.md", workflow, conflict_mode)
        write_file(target / "AGENTS.md", agents_md, conflict_mode)
        for agent in agents:
            write_file(target / ".agents" / f"{agent['slug']}.md", render_agent(agent), conflict_mode)

        write_file(target / "docs" / "WORK_TRACKING.md", work_tracking_md, conflict_mode)
        write_file(target / "docs" / "status" / "CURRENT.md", status_md, conflict_mode)

        for directory in ["docs/architecture", "docs/specs", "docs/adr", "docs/changes"]:
            path = target / directory
            path.mkdir(parents=True, exist_ok=True)
            (path / ".gitkeep").touch(exist_ok=True)
            print(f"mkdir  {path}")
    except KeyboardInterrupt:
        print("\nAborted. Existing files were not rolled back.", file=sys.stderr)
        return 130

    print("\nInitialization complete.")
    if agents:
        print("Bootstrap an agent with its agent ID, then have it read WORKFLOW.md, AGENTS.md, docs/WORK_TRACKING.md, and .agents/<id>.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
