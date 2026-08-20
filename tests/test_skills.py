from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "skills.py"
SPEC = importlib.util.spec_from_file_location("fleet_skills", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
fleet_skills = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = fleet_skills
SPEC.loader.exec_module(fleet_skills)


class SyncTests(unittest.TestCase):
    def setUp(self) -> None:
        self.skills = fleet_skills.load_skills()
        self.target = fleet_skills.Target(
            id="test",
            name="Test harness",
            relative_path=Path("harness/skills"),
            harnesses=("Test",),
        )

    def sync(self, home: Path) -> None:
        with contextlib.redirect_stdout(io.StringIO()):
            fleet_skills.sync_targets(
                self.skills, [self.target], home=home, dry_run=False
            )

    def test_sync_links_skills_and_prunes_stale_fleet_links(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_home:
            home = Path(temporary_home)
            self.sync(home)
            target_root = self.target.root(home)
            destination = target_root / self.skills[0].name
            self.assertTrue(destination.is_symlink())
            self.assertEqual(destination.resolve(), self.skills[0].path)

            stale = target_root / "removed-skill"
            stale.symlink_to(fleet_skills.SKILLS_ROOT / "removed-skill")
            self.sync(home)
            self.assertFalse(stale.is_symlink())

    def test_sync_refuses_conflicts_before_pruning(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_home:
            home = Path(temporary_home)
            target_root = self.target.root(home)
            target_root.mkdir(parents=True)
            conflict = target_root / self.skills[0].name
            conflict.mkdir()
            stale = target_root / "removed-skill"
            stale.symlink_to(fleet_skills.SKILLS_ROOT / "removed-skill")

            with self.assertRaises(fleet_skills.FleetError):
                self.sync(home)
            self.assertTrue(stale.is_symlink())


if __name__ == "__main__":
    unittest.main()
