from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

TASK_ROOT = Path(__file__).resolve().parents[1]
_RUNTIME_CANDIDATES = (
    TASK_ROOT.parents[1] / "shared" / "runtime",  # review-packet source layout
    TASK_ROOT.parents[2],  # prepared portable runtime layout
)
RUNTIME_ROOT = next(
    root for root in _RUNTIME_CANDIDATES
    if (root / "puzzle_generators" / "base.py").is_file()
)
sys.path.insert(0, str(RUNTIME_ROOT))

spec = importlib.util.spec_from_file_location(
    "generator_c9b2eae14052_geometry_test", TASK_ROOT / "generator.py"
)
assert spec is not None and spec.loader is not None
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def _binary_signature(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    """Ignore palette so color shuffles cannot masquerade as geometric variety."""
    return tuple(tuple(int(value != 0) for value in row) for row in grid)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_each_schedule_profile_has_seed_driven_geometry_diversity(difficulty: str):
    for sample_index in range(12):
        grids = [
            gen.generate(seed, sample_index, difficulty=difficulty)
            for seed in range(12_000, 12_012)
        ]
        assert len({_binary_signature(grid) for grid in grids}) >= 6, (
            difficulty,
            sample_index,
        )
        assert len({tuple(gen.observe_overrides(grid).items()) for grid in grids}) == 1
