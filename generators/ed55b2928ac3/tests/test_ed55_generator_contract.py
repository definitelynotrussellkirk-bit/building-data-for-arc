from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
RUNTIME = ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def _load_generator():
    path = ROOT / "generators" / "ed55b2928ac3" / "generator.py"
    spec = importlib.util.spec_from_file_location("task_ed55_generator", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()
CANONICAL = ROOT / "shared/data/base/solutions/banks/fec6a16dfcc9/medium_p07__ed55b2928ac3.json"


def _canonical_inputs():
    row = json.loads(CANONICAL.read_text())
    visible = row["visible_context"]
    return [pair["input"] for pair in visible["train"]] + [pair["input"] for pair in visible["test_inputs"]]


def _content_cells(grid):
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
            if (r, c) != (0, 0) and value != 0]


def test_self_check_accepts_every_canonical_input():
    assert [GEN.self_check(grid) for grid in _canonical_inputs()] == [[], [], [], []]


def test_exact_controls_and_declared_boundary_sizes_are_observable():
    grid = GEN.generate(
        0,
        0,
        grid_h=6,
        grid_w=12,
        key=4,
        blob_size=3,
        palette_kind="warm",
        texture="warm",
        palette_size=2,
        n_distinct_colors=2,
        position_bias="key_corner_with_blob",
        density="sparse",
    )
    assert (len(grid), len(grid[0])) == (6, 12)
    assert grid[0][0] == 4
    cells = _content_cells(grid)
    assert len(cells) == 3
    assert {grid[r][c] for r, c in cells} <= {1, 2, 3, 7, 8, 9}
    assert not GEN.self_check(grid)


@pytest.mark.parametrize("bad", [True, 3.5, "3"])
def test_exact_integer_axes_reject_coercions(bad):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, key=bad)


def test_unknown_override_is_rejected():
    with pytest.raises((TypeError, ValueError), match="unknown"):
        GEN.generate(0, 0, typo_axis=3)


def test_generated_examples_keep_strong_teaching_properties():
    for key in range(1, 8):
        grid = GEN.generate(17, key, key=key, blob_size=6)
        assert grid[0][0] == key
        assert not GEN.self_check(grid)
        cells = _content_cells(grid)
        assert len(cells) == 6
        assert GEN._non_rect(cells)
        assert len(GEN._components4(cells)) == 1
