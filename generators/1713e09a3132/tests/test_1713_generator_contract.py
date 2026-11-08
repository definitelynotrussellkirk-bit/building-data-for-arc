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
    path = ROOT / "generators" / "1713e09a3132" / "generator.py"
    spec = importlib.util.spec_from_file_location("task_1713_generator", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()
CANONICAL = ROOT / "shared/data/base/solutions/banks/50e2f7e22580/medium_49_draw_rectangles_from_opposite_corners__1713e09a3132.json"


def _canonical_inputs():
    row = json.loads(CANONICAL.read_text())
    visible = row["visible_context"]
    return [pair["input"] for pair in visible["train"]] + [pair["input"] for pair in visible["test_inputs"]]


def _pairs(grid):
    by_color = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                by_color.setdefault(value, []).append((r, c))
    return by_color


def _boxes(grid):
    boxes = []
    for color, points in _pairs(grid).items():
        assert len(points) == 2
        (r0, c0), (r1, c1) = points
        boxes.append((min(r0, r1), min(c0, c1), max(r0, r1), max(c0, c1), color))
    return boxes


def _has_overlap(grid):
    boxes = _boxes(grid)
    for i, (ar0, ac0, ar1, ac1, _) in enumerate(boxes):
        for br0, bc0, br1, bc1, _ in boxes[i + 1:]:
            if max(ar0, br0) <= min(ar1, br1) and max(ac0, bc0) <= min(ac1, bc1):
                return True
    return False


def test_self_check_accepts_every_canonical_input_including_overlap():
    assert [GEN.self_check(grid) for grid in _canonical_inputs()] == [[], [], [], [], []]
    assert _has_overlap(_canonical_inputs()[1])


def test_exact_controls_cover_overlap_both_orientations_and_long_span():
    grid = GEN.generate(
        0,
        0,
        grid_h=8,
        grid_w=14,
        n_pairs=4,
        palette_size=4,
        n_distinct_colors=4,
        palette_kind="cool",
        texture="cool",
        position_bias="overlap",
        density="wide",
    )
    assert (len(grid), len(grid[0])) == (8, 14)
    pairs = _pairs(grid)
    assert len(pairs) == 4 and all(len(points) == 2 for points in pairs.values())
    signs = {(r1 - r0) * (c1 - c0) > 0 for (r0, c0), (r1, c1) in pairs.values()}
    assert signs == {False, True}
    assert _has_overlap(grid)
    assert any(max(abs(r1 - r0), abs(c1 - c0)) >= 8 for (r0, c0), (r1, c1) in pairs.values())
    assert not GEN.self_check(grid)


@pytest.mark.parametrize("bad", [True, 2.5, "2"])
def test_pair_count_rejects_coercions(bad):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, n_pairs=bad)


def test_unknown_override_is_rejected():
    with pytest.raises((TypeError, ValueError), match="unknown"):
        GEN.generate(0, 0, typo_axis=3)


def test_default_production_includes_long_spans_and_overlap_profiles():
    grids = [GEN.generate(23, i) for i in range(32)]
    assert all(not GEN.self_check(grid) for grid in grids)
    assert any(_has_overlap(grid) for grid in grids)
    assert any(
        max(abs(r1 - r0), abs(c1 - c0)) >= 8
        for grid in grids
        for points in _pairs(grid).values()
        for (r0, c0), (r1, c1) in [points]
    )
