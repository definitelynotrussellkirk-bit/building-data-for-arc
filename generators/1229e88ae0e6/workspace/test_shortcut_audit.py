"""Regression tests for the reusable episode-shortcut audit."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


HERE = Path(__file__).resolve().parent
LIBRARY = HERE.parents[2]


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ShortcutAuditTests(unittest.TestCase):
    def test_standard_episodes_refute_every_built_in_shortcut(self):
        audit = _load(HERE / "shortcut_audit.py", "shortcut_audit_under_test")
        generator = audit.load_generator(
            LIBRARY,
            LIBRARY / "generators/1229e88ae0e6/generator.py",
        )
        report = audit.audit(generator, bands=("easy", "medium", "hard"), seeds=range(16))
        self.assertEqual(report["schema"], "centering-episode-shortcut-audit-v1")
        self.assertEqual(report["episodes_checked"], 48)
        self.assertFalse(report["failures"], report["failures"])
        self.assertIn("sort_colors_ascending", report["rivals"])
        self.assertIn("sort_colors_descending", report["rivals"])
        self.assertIn("pack_nonzeros_in_centered_bbox", report["rivals"])
        self.assertTrue(all(row["demo_survivals"] == 0 for row in report["rivals"].values()))


if __name__ == "__main__":
    unittest.main()
