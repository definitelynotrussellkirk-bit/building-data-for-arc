"""Portable collector for the retained quadrant parametric contract tests."""
from __future__ import annotations

import importlib.util
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "workspace/parametric/test_quadrant_parametric.py"
SPEC = importlib.util.spec_from_file_location("_quadrant_parametric_contract_tests", SOURCE)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

for NAME in dir(MODULE):
    if NAME.startswith("test_"):
        globals()[NAME] = getattr(MODULE, NAME)
