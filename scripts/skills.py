#!/usr/bin/env python3
"""Validate and synchronize this repository's Agent Skills."""

from __future__ import annotations

import argparse
import os
import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = REPO_ROOT / "skills"
TARGETS_FILE = REPO_ROOT / "harnesses.toml"
NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SUPPORTED_FIELDS = {
    "argument-hint",
    "allowed-tools",
    "compatibility",
    "description",
    "disable-model-invocation",
    "license",
    "metadata",
    "name",
}


class FleetError(ValueError):
    """Fleet input or synchronized state is invalid."""


@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    path: Path


@dataclass(frozen=True)
class Target:
    id: str
    name: str
    relative_path: Path
    harnesses: tuple[str, ...]

    def root(self, home: Path) -> Path:
        return home / self.relative_path


def clean_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def read_skill(skill_dir: Path) -> Skill:
    skill_file = skill_dir / "SKILL.md"
    try:
        text = skill_file.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise FleetError(f"{skill_file}: must be UTF-8") from error
    lines = text.splitlines()

    if not lines or lines[0] != "---":
        raise FleetError(f"{skill_file}: must start with YAML frontmatter")

    try:
        frontmatter_end = lines.index("---", 1)
    except ValueError as error:
        raise FleetError(f"{skill_file}: missing closing frontmatter delimiter") from error

    fields: dict[str, str] = {}
    for line_number, raw_line in enumerate(lines[1:frontmatter_end], start=2):
        if not raw_line or raw_line[0].isspace():
            continue
        if ":" not in raw_line:
            raise FleetError(f"{skill_file}:{line_number}: invalid frontmatter entry")
        key, value = raw_line.split(":", 1)
        key = key.strip()
        if key not in SUPPORTED_FIELDS:
            raise FleetError(
                f"{skill_file}:{line_number}: unsupported frontmatter field {key!r}"
            )
        if key in fields:
            raise FleetError(f"{skill_file}:{line_number}: duplicate field {key!r}")
        fields[key] = clean_scalar(value)

    name = fields.get("name", "")
    description = fields.get("description", "")
    folder_name = skill_dir.name

    if not NAME_PATTERN.fullmatch(folder_name) or len(folder_name) > 64:
        raise FleetError(f"{skill_dir}: invalid skill folder name")
    if name != folder_name:
        raise FleetError(
            f"{skill_file}: name {name!r} must match folder {folder_name!r}"
        )
    if not description or description in {">", "|", ">-", "|-"}:
        raise FleetError(f"{skill_file}: description must be a non-empty single line")
    if len(description) > 1024:
        raise FleetError(f"{skill_file}: description exceeds 1024 characters")
    if not any(line.strip() for line in lines[frontmatter_end + 1 :]):
        raise FleetError(f"{skill_file}: instruction body is empty")
    if "REPLACE_ME" in text:
        raise FleetError(f"{skill_file}: contains unfinished scaffold text")

    return Skill(name=name, description=description, path=skill_dir.resolve())


def load_skills() -> list[Skill]:
    if not SKILLS_ROOT.is_dir():
        raise FleetError(f"missing skills directory: {SKILLS_ROOT}")

    skill_dirs = sorted(
        path
        for path in SKILLS_ROOT.iterdir()
        if path.is_dir() and not path.name.startswith(".")
    )
    if not skill_dirs:
        raise FleetError("no skills found")

    skills: list[Skill] = []
    for skill_dir in skill_dirs:
        if not (skill_dir / "SKILL.md").is_file():
            raise FleetError(f"{skill_dir}: missing SKILL.md")
        skills.append(read_skill(skill_dir))
    return skills


def required_string(entry: dict[str, object], key: str, context: str) -> str:
    value = entry.get(key)
    if not isinstance(value, str) or not value.strip():
        raise FleetError(f"{context}: {key!r} must be a non-empty string")
    return value


def load_targets() -> list[Target]:
    try:
        with TARGETS_FILE.open("rb") as targets_file:
            data = tomllib.load(targets_file)
    except FileNotFoundError as error:
        raise FleetError(f"missing harness registry: {TARGETS_FILE}") from error
    except tomllib.TOMLDecodeError as error:
        raise FleetError(f"{TARGETS_FILE}: {error}") from error

    if data.get("version") != 1:
        raise FleetError(f"{TARGETS_FILE}: unsupported or missing version")
    raw_targets = data.get("targets")
    if not isinstance(raw_targets, list) or not raw_targets:
        raise FleetError(f"{TARGETS_FILE}: no targets configured")

    targets: list[Target] = []
    seen_ids: set[str] = set()
    seen_paths: set[Path] = set()
    for index, raw_target in enumerate(raw_targets, start=1):
        context = f"{TARGETS_FILE}: target {index}"
        if not isinstance(raw_target, dict):
            raise FleetError(f"{context}: must be a table")

        target_id = required_string(raw_target, "id", context)
        name = required_string(raw_target, "name", context)
        raw_path = required_string(raw_target, "path", context)
        raw_harnesses = raw_target.get("harnesses")
        if not NAME_PATTERN.fullmatch(target_id):
            raise FleetError(f"{context}: invalid id {target_id!r}")
        if target_id in seen_ids:
            raise FleetError(f"{context}: duplicate id {target_id!r}")

        pure_path = PurePosixPath(raw_path)
        if pure_path.is_absolute() or ".." in pure_path.parts or not pure_path.parts:
            raise FleetError(f"{context}: path must stay inside the user home")
        relative_path = Path(*pure_path.parts)
        if relative_path in seen_paths:
            raise FleetError(f"{context}: duplicate path {raw_path!r}")
        if not isinstance(raw_harnesses, list) or not raw_harnesses:
            raise FleetError(f"{context}: harnesses must be a non-empty list")
        if not all(isinstance(item, str) and item.strip() for item in raw_harnesses):
            raise FleetError(f"{context}: every harness must be a non-empty string")

        seen_ids.add(target_id)
        seen_paths.add(relative_path)
        targets.append(
            Target(
                id=target_id,
                name=name,
                relative_path=relative_path,
                harnesses=tuple(raw_harnesses),
            )
        )
    return targets


def destination_state(skill: Skill, target_root: Path) -> str:
    destination = target_root / skill.name
    if destination.is_symlink():
        if destination.resolve(strict=False) == skill.path:
            return "linked"
        return "conflict"
    if destination.exists():
        return "conflict"
    return "missing"


def symlink_target(link: Path) -> Path:
    target = Path(os.readlink(link))
    if not target.is_absolute():
        target = link.parent / target
    return target.resolve(strict=False)


def stale_links(skills: list[Skill], target_root: Path) -> list[Path]:
    if not target_root.is_dir():
        return []
    skill_names = {skill.name for skill in skills}
    canonical_root = SKILLS_ROOT.resolve()
    stale: list[Path] = []
    for destination in target_root.iterdir():
        if destination.name in skill_names or not destination.is_symlink():
            continue
        target = symlink_target(destination)
        if target.parent == canonical_root:
            stale.append(destination)
    return sorted(stale)


def preflight(skills: list[Skill], targets: list[Target], home: Path) -> None:
    conflicts: list[Path] = []
    for target in targets:
        target_root = target.root(home)
        for skill in skills:
            if destination_state(skill, target_root) == "conflict":
                conflicts.append(target_root / skill.name)
    if conflicts:
        formatted = "\n".join(f"  {path}" for path in conflicts)
        raise FleetError(f"refusing to replace existing paths:\n{formatted}")


def sync_targets(
    skills: list[Skill], targets: list[Target], home: Path, dry_run: bool
) -> None:
    preflight(skills, targets, home)
    for target in targets:
        target_root = target.root(home)
        print(f"{target.name} ({', '.join(target.harnesses)})")
        for stale in stale_links(skills, target_root):
            if dry_run:
                print(f"  prune   {stale}")
            else:
                stale.unlink()
                print(f"  pruned  {stale}")
        for skill in skills:
            destination = target_root / skill.name
            if destination_state(skill, target_root) == "linked":
                print(f"  ok      {destination}")
            elif dry_run:
                print(f"  link    {destination} -> {skill.path}")
            else:
                target_root.mkdir(parents=True, exist_ok=True)
                destination.symlink_to(skill.path, target_is_directory=True)
                print(f"  linked  {destination} -> {skill.path}")


def command_check(skills: list[Skill], targets: list[Target]) -> None:
    harness_count = len({name for target in targets for name in target.harnesses})
    print(
        f"OK: {len(skills)} skill{'s' if len(skills) != 1 else ''}, "
        f"{harness_count} harness{'es' if harness_count != 1 else ''}"
    )


def command_list(skills: list[Skill]) -> None:
    for skill in skills:
        print(f"{skill.name}\t{skill.description}")


def command_targets(targets: list[Target], home: Path) -> None:
    for target in targets:
        print(f"{target.root(home)}\t{', '.join(target.harnesses)}")


def command_status(skills: list[Skill], targets: list[Target], home: Path) -> bool:
    synchronized = True
    for target in targets:
        target_root = target.root(home)
        print(f"{target.name} ({', '.join(target.harnesses)})")
        for skill in skills:
            state = destination_state(skill, target_root)
            print(f"  {state:<8}{target_root / skill.name}")
            synchronized = synchronized and state == "linked"
        for stale in stale_links(skills, target_root):
            print(f"  {'stale':<8}{stale}")
            synchronized = False
    return synchronized


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("check", help="validate skills and harness targets")
    subparsers.add_parser("list", help="list canonical skills")
    subparsers.add_parser("targets", help="list synchronized harness paths")
    subparsers.add_parser("status", help="check synchronization state")
    sync_parser = subparsers.add_parser("sync", help="synchronize every harness")
    sync_parser.add_argument(
        "--dry-run", action="store_true", help="show changes without writing them"
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        skills = load_skills()
        targets = load_targets()
        home = Path.home()
        if args.command == "check":
            command_check(skills, targets)
        elif args.command == "list":
            command_list(skills)
        elif args.command == "targets":
            command_targets(targets, home)
        elif args.command == "status":
            return 0 if command_status(skills, targets, home) else 1
        elif args.command == "sync":
            sync_targets(skills, targets, home, args.dry_run)
    except FleetError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
