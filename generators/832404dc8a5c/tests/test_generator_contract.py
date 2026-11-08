"""Behavior regressions for the selected anchored-lane family.

Racket labels are authoritative; Python rivals are only explicit alternatives.
"""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator


ROOT = find_root(__file__)
TASK = "832404dc8a5c"
GEN, SOURCE, SOURCE_SHA = load_selected_generator(TASK, root=ROOT)


@pytest.mark.parametrize("field,value", [
    ("seed", True), ("seed", 1.5), ("seed", "1"),
    ("sample_index", False), ("sample_index", 1.5), ("sample_index", "1"),
    ("sample_index", -1), ("difficulty", True), ("difficulty", 0),
    ("difficulty", "unknown"), ("grid_h", 6.5), ("grid_h", "8"),
    ("grid_w", 9.5), ("grid_w", "9"), ("n_anchored_rows", True),
    ("n_anchored_cols", 1.5), ("n_anchored_rows", -1),
    ("n_anchored_cols", 5), ("zero_density", "0.5"),
    ("zero_density", float("nan")), ("zero_density", float("inf")),
    ("lane_palette", "unknown"), ("texture", "unknown"),
])
def test_invalid_controls_are_rejected(field, value):
    call = {"seed": 17, "sample_index": 0, "difficulty": "medium", field: value}
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(**call)


def test_unknown_control_is_rejected_even_when_none():
    with pytest.raises((TypeError, ValueError), match="[Uu]nknown"):
        GEN.generate(17, 0, typoed_lane_palette=None)


@pytest.mark.parametrize("height,width", [(6, 8), (6, 30), (30, 8), (30, 30), (21, 29)])
def test_exact_dimensions_and_joint_lane_counts(height, width):
    grid = GEN.generate(17, 2, difficulty="easy", grid_h=height, grid_w=width,
                        n_anchored_rows=4, n_anchored_cols=4, lane_palette="base")
    assert (len(grid), len(grid[0])) == (height, width)
    assert GEN.observe_overrides(grid) == {"n_anchored_rows": 4, "n_anchored_cols": 4}
    assert GEN.self_check(grid) == []


def test_canonical_inputs_remain_in_domain():
    pairs = canonical_pairs(TASK, root=ROOT)
    assert len(pairs) == 4
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert not GEN.strict_canonical_like(pair["input"])


def test_canonical_authority_text_is_synchronized():
    records = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines()]
    canonical = next(row for row in records if row["task_id"] == TASK)
    candidates = [ROOT / "shared/data/base/solutions/training/d2acf2cb__832404dc8a5c.json",
                  ROOT / "data/base/solutions/training/d2acf2cb__832404dc8a5c.json"]
    selected = next(path for path in candidates if path.is_file())
    record = json.loads(selected.read_text())
    assert record["racket_target"]["target_code"] == canonical["program_solution"]


def test_semantic_contract_has_real_counterexamples():
    assert callable(getattr(GEN, "lesson_identifiable", None))
    assert getattr(GEN, "LESSON_SCHEDULE_PERIOD", None) == 20
    assert "double_swap_intersections" in GEN.CANONICAL_SHORTCUTS
    assert len(GEN.LESSON_COMPETITORS) >= 7


@pytest.fixture(scope="module")
def reference():
    from arc_repl.racket_bridge import RacketBridge
    canonical = next(json.loads(line) for line in canonical_path(ROOT).read_text().splitlines()
                     if json.loads(line).get("task_id") == TASK)
    source = canonical["program_solution"]
    assert source.startswith("(rule! ") and source.endswith(")")
    with RacketBridge(timeout=20) as bridge:
        bridge.eval_text("(define reviewed-rule " + source[len("(rule! "):-1] + ")")
        cache = {}
        def label(grid):
            key = json.dumps(grid)
            if key not in cache:
                bridge.define_grid("reviewed-input", grid)
                cache[key] = bridge.eval_text("(reviewed-rule reviewed-input)")
            return deepcopy(cache[key])
        yield label


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("start", range(20))
def test_each_scheduled_lesson_and_rotation_disambiguates_declared_rivals(band, start, reference):
    rivals = getattr(GEN, "LESSON_COMPETITORS", {})
    assert rivals, "Lesson claims require executable rivals"
    grids = [GEN.generate(0, start + offset, difficulty=band) for offset in range(4)]
    pairs = [{"input": grid, "output": reference(grid)} for grid in grids]
    for query_index in range(4):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        query = pairs[query_index]
        assert GEN.lesson_identifiable(deepcopy(demos), deepcopy(query)) == []
        for name, solve in rivals.items():
            survives = all(solve(deepcopy(pair["input"])) == pair["output"] for pair in demos)
            assert not survives or solve(deepcopy(query["input"])) == query["output"], name


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_size_mixture_preserves_canonical_anchors_and_grows_lanes(band):
    grids = [GEN.generate(17, index, difficulty=band) for index in range(20)]
    assert sum((len(g), len(g[0])) == (30, 30) for g in grids) == 4
    assert sum(max(len(g), len(g[0])) > 20 for g in grids) == 8
    assert sum(len(g[0]) == 9 and len(g) in (6, 7, 9, 10) for g in grids) == 12
    for grid in grids:
        assert GEN.self_check(grid) == []


@pytest.mark.parametrize("texture", ["no_anchors", "all_anchored", "single_anchor"])
def test_explicit_lawful_edge_cases_have_reference_labels(texture, reference):
    grid = GEN.generate(71, 3, difficulty="hard", grid_h=30, grid_w=30,
                        texture=texture, zero_density=0.1)
    assert GEN.self_check(grid) == []
    output = reference(grid)
    if texture == "no_anchors":
        assert output == grid
    else:
        assert output != grid


def test_lane_free_sparse_impostors_and_noninteger_cells_rejected():
    plain = [[6] * 9 for _ in range(7)]
    assert GEN.self_check(plain)
    plain[2][2] = 0
    assert GEN.self_check(plain)
    grid = GEN.generate(17, 0)
    grid[0][0] = True
    assert GEN.self_check(grid)


def test_intersections_swap_once_and_shortcut_is_really_canonical(reference):
    rival = GEN.CANONICAL_SHORTCUTS["double_swap_intersections"]
    for pair in canonical_pairs(TASK, root=ROOT):
        assert rival(deepcopy(pair["input"])) == pair["output"]
    grid = GEN.generate(19, 0, grid_h=30, grid_w=30,
                        n_anchored_rows=2, n_anchored_cols=3, lane_palette="swapped")
    expected = reference(grid)
    assert rival(deepcopy(grid)) != expected
    for r in range(1, len(grid) - 1):
        for c in range(1, len(grid[0]) - 1):
            if grid[r][0] == grid[r][-1] == grid[0][c] == grid[-1][c] == 4:
                assert expected[r][c] == {0: 8, 8: 0, 6: 7, 7: 6}[grid[r][c]]
