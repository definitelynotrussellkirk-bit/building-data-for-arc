"""Reproduce audit finding A1 without editing the audited target."""
from __future__ import annotations
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TARGET = ROOT / "repo/generators/71e2e99645f4/generator.py"
spec = importlib.util.spec_from_file_location("audit_71e2e99645f4", TARGET)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)
requested = ["no_hole"] * 3
grid = module.generate(0, 0, hole_patterns=requested)
print({"requested": requested, "grid": grid, "self_check": module.self_check(grid)})
