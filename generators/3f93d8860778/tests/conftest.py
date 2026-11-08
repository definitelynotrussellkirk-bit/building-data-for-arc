"""Portable compatibility for the immutable legacy fixture.

The frozen fixture predates ``reviewer_support`` and looks for
``ROOT/data/canonical/puzzles.jsonl``.  Point only that module's ``ROOT`` at the
runtime's public ``shared`` directory after collection; the fixture bytes stay
unchanged.
"""
from __future__ import annotations

from pathlib import Path

from reviewer_support import find_root


_FROZEN_FIXTURE = "test_generator_3f93d8860778.py"


def pytest_collection_modifyitems(items) -> None:
    for item in items:
        module = getattr(item, "module", None)
        filename = Path(getattr(module, "__file__", ""))
        if filename.name == _FROZEN_FIXTURE and hasattr(module, "ROOT"):
            module.ROOT = find_root(filename) / "shared"
