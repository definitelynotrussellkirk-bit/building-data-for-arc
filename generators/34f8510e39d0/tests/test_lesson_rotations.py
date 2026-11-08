"""Regressions for losing the sole thin-target witness to a query holdout."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

from reviewer_support import find_root


TASK_ID = "34f8510e39d0"


def _load_generator():
    root = find_root(__file__)
    candidates = (
        root / "generators" / TASK_ID / "generator.py",
        root / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py",
    )
    path = next(path for path in candidates if path.is_file())
    spec = importlib.util.spec_from_file_location("rotation_test_34f8510e39d0", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
@pytest.mark.parametrize("start", range(4))
def test_every_four_pair_window_keeps_a_refutation_after_any_holdout(band, start):
    """Returning to one thin slot per three draws must fail this contract."""
    pairs = []
    for index in range(start, start + 4):
        grid = gen.generate(17000 + start, index, difficulty=band)
        pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
    for query_index, query in enumerate(pairs):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        for name, rival in gen.LESSON_COMPETITORS.items():
            assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                band, start, query_index, name,
                "holding out a pair removed every demonstration of the distinction",
            )
        assert gen.lesson_identifiable(demos, query) == []


def test_canonical_shortcut_declarations_really_fit_every_canonical_pair():
    """A refuted hypothesis belongs among rivals, not canonical shortcuts."""
    from reviewer_support import canonical_pairs

    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name
