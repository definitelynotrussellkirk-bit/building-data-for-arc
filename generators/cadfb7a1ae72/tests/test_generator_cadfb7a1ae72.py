from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest

TASK_ID = "cadfb7a1ae72"
TASK_DIR = Path(__file__).resolve().parents[1]
REPO = TASK_DIR.parents[1]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

SPEC = importlib.util.spec_from_file_location(
    f"task_generator_{TASK_ID}", TASK_DIR / "generator.py"
)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _canonical_rows():
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            yield row


def _canonical_pairs():
    pairs = []
    for row in _canonical_rows():
        for split in ("train", "test"):
            values = row.get(split) or []
            if isinstance(values, dict):
                values = [values]
            for pair in values:
                if not isinstance(pair, dict) or not pair.get("input") or not pair.get("output"):
                    continue
                source = pair["input"]
                target = pair["output"]
                if source and isinstance(source[0], str):
                    source = [[int(ch) for ch in text] for text in source]
                if target and isinstance(target[0], str):
                    target = [[int(ch) for ch in text] for text in target]
                pairs.append({"input": source, "output": target})
    return pairs


def _canonical_hash():
    source = next(row["program_solution"] for row in _canonical_rows() if row.get("program_solution"))
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def test_rule_hash_and_python_mirror_match_every_canonical_pair():
    assert GEN.RULE_HASH == _canonical_hash() == "b8842d5039be"
    pairs = _canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


def test_every_sliding_four_demo_window_identifies_the_rule():
    assert GEN.EXAMPLES_NEEDED == 4
    for band in ("easy", "medium", "hard"):
        for start in range(8):
            lesson = []
            for sample_index in range(start, start + GEN.EXAMPLES_NEEDED + 1):
                grid = GEN.generate(10_000 + sample_index, sample_index, difficulty=band)
                lesson.append({"input": grid, "output": GEN.rule_mirror(grid)})
            assert GEN.lesson_identifiable(lesson[:-1], lesson[-1]) == []


def test_schedule_exposes_the_decisive_counterexamples_in_every_band():
    for band in ("easy", "medium", "hard"):
        grids = [GEN.generate(20_000 + index, index, difficulty=band) for index in range(4)]
        assert {GEN.observe_overrides(grid)["profile"] for grid in grids} == set(GEN.PROFILES)
        symbols = {
            value
            for grid in grids
            for row in GEN.rule_mirror(grid)
            for value in row
        }
        assert symbols == {0, 1, 4, 8}
        assert any(GEN._refutes_hole_priority(grid) for grid in grids)
        assert any(GEN._refutes_binary_holes(grid) for grid in grids)
        assert any(GEN._refutes_axis_count(grid) for grid in grids)


def test_canonical_shortcuts_really_fit_canonical_but_not_generated_witnesses():
    for pair in _canonical_pairs():
        for rival in GEN.CANONICAL_SHORTCUTS.values():
            assert rival(pair["input"]) == pair["output"]
    grids = [GEN.generate(30_000 + index, index, difficulty="medium") for index in range(4)]
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert any(rival(grid) != GEN.rule_mirror(grid) for grid in grids), name


def test_remaining_canonical_fit_shortcuts_are_declared_and_killed_by_every_lesson():
    expected = {
        "hole_priority",
        "binary_holes",
        "axis_count",
        "projection_symmetry",
        "enclosed_hole_cells",
        "color_order",
    }
    assert expected <= set(GEN.SEMANTIC_RIVALS)

    # These three alternatives are especially dangerous because all official
    # pairs admit them: histogram symmetry instead of cellwise reflection,
    # enclosed-cell count instead of enclosed-region count, and color order
    # instead of top-left order.
    for pair in _canonical_pairs():
        for name in ("projection_symmetry", "enclosed_hole_cells", "color_order"):
            assert GEN.SEMANTIC_RIVALS[name](pair["input"]) == pair["output"]

    for band in ("easy", "medium", "hard"):
        for start in range(12):
            grids = [
                GEN.generate(60_000 + 17 * start + offset, start + offset, difficulty=band)
                for offset in range(GEN.EXAMPLES_NEEDED)
            ]
            for name in expected:
                rival = GEN.SEMANTIC_RIVALS[name]
                assert any(rival(grid) != GEN.rule_mirror(grid) for grid in grids), (
                    band,
                    start,
                    name,
                )


def test_projection_and_order_traps_are_deterministic_profile_properties():
    projection = GEN.SEMANTIC_RIVALS["projection_symmetry"]
    hole_cells = GEN.SEMANTIC_RIVALS["enclosed_hole_cells"]
    color_order = GEN.SEMANTIC_RIVALS["color_order"]

    for seed in range(40):
        projection_grid = GEN.generate(seed, 2, profile="hole_priority")
        assert projection(projection_grid) != GEN.rule_mirror(projection_grid)
        assert hole_cells(projection_grid) != GEN.rule_mirror(projection_grid)

        order_grid = GEN.generate(seed, 0, profile="canonical3")
        assert color_order(order_grid) != GEN.rule_mirror(order_grid)


def test_projection_trap_uses_identical_ordered_histograms_with_different_symmetry():
    def projections(obj):
        rows = [0] * obj["height"]
        cols = [0] * obj["width"]
        for row, col in obj["normalized_cells"]:
            rows[row] += 1
            cols[col] += 1
        return tuple(rows), tuple(cols)

    for seed in range(20):
        grid = GEN.generate(seed, 2, profile="hole_priority")
        objects = GEN._analyze(grid)["objects"]
        asym = next(
            obj for obj in objects
            if (obj["holes"], obj["symmetry_class"]) == (0, 0)
        )
        column_symmetric = next(
            obj for obj in objects
            if (obj["holes"], obj["symmetry_class"]) == (0, 2)
        )
        assert projections(asym) == projections(column_symmetric)
        assert asym["symmetry_class"] != column_symmetric["symmetry_class"]


def test_hole_cell_trap_uses_equal_enclosed_area_with_different_region_counts():
    for seed in range(20):
        grid = GEN.generate(seed, 3, profile="binary_holes")
        objects = GEN._analyze(grid)["objects"]
        one_hole = next(
            obj for obj in objects
            if obj["holes"] == 1
            and GEN._enclosed_zero_cell_count(obj["normalized_cells"]) == 2
        )
        two_holes = next(obj for obj in objects if obj["holes"] == 2)
        assert GEN._enclosed_zero_cell_count(one_hole["normalized_cells"]) == 2
        assert GEN._enclosed_zero_cell_count(two_holes["normalized_cells"]) == 2
        assert one_hole["holes"] != two_holes["holes"]
        assert one_hole["symmetry_class"] != two_holes["symmetry_class"]


def test_exact_override_boundaries_are_observable_and_invalid_inputs_reject():
    cases = (
        {"grid_h": 10},
        {"grid_h": 20},
        {"grid_w": 16},
        {"grid_w": 24},
        *({"profile": profile} for profile in GEN.PROFILES),
    )
    for band in ("easy", "medium", "hard"):
        for index, case in enumerate(cases):
            grid = GEN.generate(40_000 + index, 17 + index, difficulty=band, **case)
            observed = GEN.observe_overrides(grid)
            for key, value in case.items():
                assert observed[key] == value
            assert GEN.self_check(grid, meta={"overrides": case}) == []
    with pytest.raises(TypeError, match="unknown override"):
        GEN.generate(0, 0, imaginary_axis=4)
    with pytest.raises(ValueError):
        GEN.generate(0, 0, grid_h=9)
    with pytest.raises(ValueError):
        GEN.generate(0, 0, profile="not-a-profile")


def test_self_check_rejects_structural_impostors():
    original = GEN.generate(50_000, 1, difficulty="medium")
    assert GEN.self_check(original) == []

    blank = [[0 for _ in row] for row in original]
    assert GEN.self_check(blank)

    recolored_cell = copy.deepcopy(original)
    analysis = GEN._analyze(recolored_cell)
    cell = analysis["objects"][0]["cells"][0]
    absent = next(color for color in range(1, 10) if color not in analysis["palette"])
    recolored_cell[cell[0]][cell[1]] = absent
    assert GEN.self_check(recolored_cell)

    touching = copy.deepcopy(original)
    first, second = GEN._analyze(touching)["objects"][:2]
    # Draw a shortest Manhattan bridge in the first object's color. This either
    # creates an illegal near-touch or an extra component/color ambiguity.
    r, c = first["cells"][0]
    tr, tc = second["cells"][0]
    while r != tr:
        r += 1 if tr > r else -1
        if touching[r][c] == 0:
            touching[r][c] = first["color"]
    while c != tc:
        c += 1 if tc > c else -1
        if touching[r][c] == 0:
            touching[r][c] = first["color"]
    assert GEN.self_check(touching)

    ragged = copy.deepcopy(original)
    ragged[-1].pop()
    assert GEN.self_check(ragged)


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(987654321)
    before = random.getstate()
    first = GEN.generate(77, 19, difficulty="hard")
    middle = GEN.generate(78, 20, difficulty="easy")
    second = GEN.generate(77, 19, difficulty="hard")
    after = random.getstate()
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert middle != first
    first[0][0] = 9 if first[0][0] != 9 else 7
    assert GEN.generate(77, 19, difficulty="hard") == second


def test_curriculum_has_nontrivial_output_matrix_diversity():
    outputs = set()
    total = 0
    for episode in range(24):
        for sample_index in range(6):
            grid = GEN.generate(episode * 101, sample_index, difficulty=None)
            output = GEN.rule_mirror(grid)
            outputs.add(tuple(tuple(row) for row in output))
            total += 1
    assert len(outputs) / total >= 0.35
