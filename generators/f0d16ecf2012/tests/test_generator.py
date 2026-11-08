from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

TASK_ID = "f0d16ecf2012"
REPO_ROOT = Path(__file__).resolve().parents[3]
gen = importlib.import_module(f"generators.{TASK_ID}.generator")


def _rows_to_grid(rows):
    return [[int(value) for value in row] for row in rows]


def _canonical_pairs():
    with (REPO_ROOT / "shared/data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("task_id") != TASK_ID:
                continue
            pairs = list(record["train"]) + [record["test"]]
            return [
                {
                    "input": _rows_to_grid(pair["input"]),
                    "output": _rows_to_grid(pair["output"]),
                }
                for pair in pairs
            ]
    raise AssertionError(f"canonical task {TASK_ID} not found")


def _wall_only_output(grid):
    """Reference rival: ignore the object's static source footprint."""
    h, w = len(grid), len(grid[0])
    walls = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9
    }
    out = [[0 for _ in range(w)] for _ in range(h)]
    for r, c in walls:
        out[r][c] = 9
    for obj in gen._components(grid):
        current = list(obj["cells"])
        while gen._can_shift(
            current,
            h=h,
            w=w,
            static_occupied=walls,
        ):
            current = gen._shift_once(current)
        for r, c in current:
            out[r][c] = obj["color"]
    return out


def _component_motion_distances(grid, obj):
    h, w = len(grid), len(grid[0])
    walls = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9
    }
    original = list(obj["cells"])
    authority = gen._move_component(
        original,
        h=h,
        w=w,
        walls=walls,
        steps=None,
    )
    wall_only = gen._move_component_wall_only(
        original,
        h=h,
        w=w,
        walls=walls,
    )
    original_left = min(c for _, c in original)
    return (
        min(c for _, c in authority) - original_left,
        min(c for _, c in wall_only) - original_left,
    )


def test_rule_hash_and_axes_are_pinned_and_observable():
    assert gen.RULE_HASH == "4e0031784e59"
    assert set(gen.AXES) == {"grid_w", "n_compartments", "comp_h"}


@pytest.mark.parametrize("pair", _canonical_pairs())
def test_canonical_pairs_are_accepted_and_python_mirror_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_default_draws_teach_each_declared_semantic_distinction(difficulty):
    assert set(gen.SEMANTIC_WITNESSES) == {
        "multi_step_motion",
        "rigid_shape_translation",
        "independent_components",
        "source_footprint_blocking",
    }
    for sample_index in range(12):
        grid = gen.generate(31001, sample_index, difficulty=difficulty)
        assert gen.self_check(grid, difficulty=difficulty) == []
        for name, witness in gen.SEMANTIC_WITNESSES.items():
            assert witness(grid), (difficulty, sample_index, name)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_declared_overrides_are_exact_and_unknown_keys_reject(difficulty):
    cases = [
        {"grid_w": 9, "n_compartments": 2, "comp_h": 2},
        {"grid_w": 13, "n_compartments": 3, "comp_h": 3},
        {"grid_w": 22, "n_compartments": 5, "comp_h": 4},
    ]
    for sample_index, overrides in enumerate(cases):
        grid = gen.generate(9917, sample_index, difficulty=difficulty, **overrides)
        assert gen.observe_overrides(grid) == overrides
        assert gen.self_check(grid, difficulty=difficulty, meta={"overrides": overrides}) == []

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(9917, 99, difficulty=difficulty, typo_axis=1)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_band_retains_canonical_profile_support(difficulty):
    draws = [gen.generate(17731, index, difficulty=difficulty) for index in range(60)]
    hits = sum(not gen.strict_canonical_like(grid) for grid in draws)
    assert hits >= 18, (difficulty, hits)


def test_canonical_anchor_schedule_is_balanced_but_not_fixed():
    observed_slots = set()
    for seed in (20261008, 20261009):
        for block in range(24):
            flags = [
                gen._is_canonical_anchor(
                    seed,
                    block * 3 + slot,
                    has_overrides=False,
                )
                for slot in range(3)
            ]
            assert sum(flags) == 1
            observed_slots.add(flags.index(True))
    assert observed_slots == {0, 1, 2}
    assert not gen._is_canonical_anchor(20261008, 0, has_overrides=True)


def test_every_consecutive_three_demo_window_is_identifiable():
    for difficulty in ("easy", "medium", "hard"):
        pairs = []
        for sample_index in range(18):
            grid = gen.generate(44119, sample_index, difficulty=difficulty)
            pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
        for start in range(len(pairs) - 3):
            demos = pairs[start : start + 3]
            query = pairs[start + 3]
            assert gen.lesson_identifiable(demos, query) == [], (difficulty, start)


def _normalized_cells(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _two_lane_probe_draws():
    return [
        gen.generate(
            20261002,
            sample_index,
            difficulty="hard",
            grid_w=13,
            n_compartments=2,
            comp_h=3,
        )
        for sample_index in range(160)
    ]


def test_split_witness_can_occupy_either_lane():
    observed = set()
    for grid in _two_lane_probe_draws():
        analysis = gen._analysis(grid)
        assert analysis["errors"] == []
        observed.update(
            lane_index
            for lane_index, lane in enumerate(analysis["lanes"])
            if len(lane["components"]) > 1
        )
    assert observed == {0, 1}


def test_split_witness_uses_both_diagonal_slopes():
    slopes = set()
    for grid in _two_lane_probe_draws():
        analysis = gen._analysis(grid)
        split_lane = next(lane for lane in analysis["lanes"] if len(lane["components"]) > 1)
        points = sorted(obj["cells"][0] for obj in split_lane["components"])
        slopes.add("down_right" if points[-1][1] > points[0][1] else "down_left")
    assert slopes == {"down_left", "down_right"}


def test_rigid_witness_uses_varied_east_edge_profiles():
    observed = set()
    for grid in _two_lane_probe_draws():
        analysis = gen._analysis(grid)
        connected_lane = next(lane for lane in analysis["lanes"] if len(lane["components"]) == 1)
        observed.add(_normalized_cells(connected_lane["components"][0]["cells"]))
    assert observed == {
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 3)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 3)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 2), (1, 3)),
        ((0, 0), (0, 1), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3)),
        ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3)),
        ((0, 0), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3)),
    }


def test_canonical_authority_contains_static_source_footprint_blocking():
    counterexamples = [
        pair
        for pair in _canonical_pairs()
        if gen.rule_mirror(pair["input"]) != _wall_only_output(pair["input"])
    ]
    assert len(counterexamples) == 1


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_default_draw_teaches_static_source_footprint_blocking(difficulty):
    for sample_index in range(24):
        grid = gen.generate(20261005, sample_index, difficulty=difficulty)
        assert gen.rule_mirror(grid) != _wall_only_output(grid), (
            difficulty,
            sample_index,
        )


def test_source_footprint_witness_varies_its_stopping_distance():
    observed = set()
    for grid in _two_lane_probe_draws():
        for obj in gen._components(grid):
            authority_distance, wall_only_distance = _component_motion_distances(
                grid,
                obj,
            )
            if authority_distance < wall_only_distance:
                observed.add(authority_distance)
    assert observed == {1, 2}


def test_noncanonical_palette_covers_every_movable_arc_color():
    observed = set()
    for sample_index in range(320):
        grid = gen.generate(
            20261006,
            sample_index,
            difficulty="hard",
            grid_w=13,
            n_compartments=3,
            comp_h=3,
        )
        observed.update(
            value
            for row in grid
            for value in row
            if value not in (0, 9)
        )
    assert observed == set(range(1, 9))


def test_palette_includes_reused_and_distinct_lane_colors():
    modes = set()
    for sample_index in range(200):
        grid = gen.generate(
            20261003,
            sample_index,
            difficulty="hard",
            grid_w=13,
            n_compartments=3,
            comp_h=3,
        )
        analysis = gen._analysis(grid)
        assert analysis["errors"] == []
        colors = [lane["colors"][0] for lane in analysis["lanes"]]
        modes.add("reused" if len(set(colors)) < len(colors) else "distinct")
    assert modes == {"distinct", "reused"}


def test_workspace_correlation_probe_reports_full_coverage():
    probe_path = Path(gen.__file__).parent / "workspace/correlation_probe.py"
    spec = importlib.util.spec_from_file_location("f0d16ecf2012_correlation_probe", probe_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = module.collect(seed=20261004, draws=120, difficulty="hard")
    assert module.coverage_findings(report) == []


def test_workspace_motion_semantics_probe_reports_full_coverage():
    probe_path = Path(gen.__file__).parent / "workspace/motion_semantics_probe.py"
    spec = importlib.util.spec_from_file_location("f0d16ecf2012_motion_probe", probe_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = module.collect(seed=20261007, draws=120, difficulty="hard")
    assert module.coverage_findings(report) == []
