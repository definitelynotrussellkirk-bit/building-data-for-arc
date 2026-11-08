from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest


TASK_ID = "155fb684795d"
gen = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)
ROOT = Path(__file__).resolve().parents[1]


def _canonical_inputs():
    rows = []
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            rows.extend(pair["input"] for pair in row["train"])
            test = row["test"] if isinstance(row["test"], list) else [row["test"]]
            rows.extend(pair["input"] for pair in test)
    return rows


def _panel_bounds(grid):
    h, w = len(grid), len(grid[0])
    separators = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    bounds = [-1] + separators + [w]
    return [(bounds[i] + 1, bounds[i + 1]) for i in range(len(bounds) - 1)]


def _replace_panel(dst, dst_index, src, src_index):
    out = copy.deepcopy(dst)
    dst_bounds = _panel_bounds(dst)
    src_bounds = _panel_bounds(src)
    dl, dr = dst_bounds[dst_index]
    sl, sr = src_bounds[src_index]
    assert dr - dl == sr - sl
    for r in range(len(out)):
        out[r][dl:dr] = src[r][sl:sr]
    return out


def test_rule_hash_is_pinned_to_current_authority():
    assert gen.RULE_HASH == "76d51e40d80e"


def test_all_canonical_inputs_are_owned():
    canonical = _canonical_inputs()
    assert len(canonical) == 3
    for grid in canonical:
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_declared_boundaries_are_exact_and_observable(band):
    for panel_h in (5, 6):
        for panel_w in (5, 6):
            for odd_index in range(4):
                grid = gen.generate(
                    123,
                    7,
                    difficulty=band,
                    panel_h=panel_h,
                    panel_w=panel_w,
                    odd_index=odd_index,
                )
                assert gen.observe_overrides(grid) == {
                    "panel_h": panel_h,
                    "panel_w": panel_w,
                    "odd_index": odd_index,
                }
                assert gen.self_check(grid) == []


def test_default_schedule_anchors_canonical_and_cycles_target_position():
    grids = [gen.generate(41, index, difficulty="hard") for index in range(4)]
    assert gen.strict_canonical_like(grids[0]) == []
    assert [gen.observe_overrides(grid)["odd_index"] for grid in grids] == [0, 1, 2, 3]
    assert gen.SEMANTIC_WITNESSES["plus_growth_required_raw_shape_ambiguous"](grids[1])
    assert gen.SEMANTIC_WITNESSES["cell_count_shortcut_rebutted"](grids[1])


def test_self_check_rejects_targeted_structural_impostors():
    grid = gen.generate(97, 1, difficulty="medium", panel_h=5, panel_w=5, odd_index=2)
    bounds = _panel_bounds(grid)

    broken_divider = copy.deepcopy(grid)
    first_divider = bounds[0][1]
    broken_divider[2][first_divider] = 0
    assert gen.self_check(broken_divider)

    disconnected = copy.deepcopy(grid)
    left, right = bounds[0]
    empty = next(
        (r, c) for r in range(1, len(grid) - 1) for c in range(left + 1, right - 1)
        if disconnected[r][c] == 0
        and all(
            not (0 <= r + dr < len(grid) and left <= c + dc < right)
            or disconnected[r + dr][c + dc] == 0
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
        )
    )
    disconnected[empty[0]][empty[1]] = 7
    assert any("disconnected" in message for message in gen.self_check(disconnected))

    mixed_color = copy.deepcopy(grid)
    object_cell = next(
        (r, c) for r in range(len(grid)) for c in range(bounds[1][0], bounds[1][1])
        if mixed_color[r][c] not in (0, 9)
    )
    mixed_color[object_cell[0]][object_cell[1]] = (
        1 if mixed_color[object_cell[0]][object_cell[1]] != 1 else 2
    )
    assert any("monochrome" in message for message in gen.self_check(mixed_color))

    edge_touch = copy.deepcopy(grid)
    left, _ = bounds[2]
    source = next(
        (r, c) for r in range(len(grid)) for c in range(left, bounds[2][1])
        if edge_touch[r][c] not in (0, 9)
    )
    edge_touch[0][left + 1] = edge_touch[source[0]][source[1]]
    assert any("boundary" in message or "disconnected" in message for message in gen.self_check(edge_touch))

    # Replace the odd panel with a common panel: the unique grown signature
    # disappears, so the lesson must be rejected even though dimensions and
    # palette remain plausible.
    analysis_errors, analysis = gen._analyze_grid(grid)
    assert analysis_errors == []
    odd = analysis["odd_index"]
    common = next(index for index in range(4) if index != odd)
    no_odd = _replace_panel(grid, odd, grid, common)
    assert any("plus-grown" in message for message in gen.self_check(no_odd))


def test_deterministic_fresh_and_global_rng_pure():
    random.seed(811)
    state = random.getstate()
    first = gen.generate(8, 3, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(8, 3, difficulty="hard")
    assert first == second
    assert first is not second
    first[0][0] = 9 if first[0][0] != 9 else 0
    assert second == gen.generate(8, 3, difficulty="hard")


def test_unknown_overrides_fail_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 1, bogus_axis=3)
