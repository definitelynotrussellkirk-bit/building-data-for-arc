"""Behavioral tests for the color-2 / center-cue self-tile family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import types

import pytest

try:
    from reviewer_support import canonical_path, find_root, load_selected_generator
except ModuleNotFoundError:
    for parent in Path(__file__).resolve().parents:
        runtime = parent / "shared/runtime"
        if (runtime / "reviewer_support.py").is_file():
            sys.path.insert(0, str(runtime))
            break
    from reviewer_support import canonical_path, find_root, load_selected_generator

TASK = "7e03da0eb439"
ROOT = find_root(__file__)
HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"
PROTOTYPE = PARAMETRIC / "prototype.py"
PROBE = PARAMETRIC / "probe.py"


def load_prototype():
    assert PROTOTYPE.is_file(), "runnable parametric prototype is missing"
    spec = importlib.util.spec_from_file_location("_7e03_parametric_test_subject", PROTOTYPE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_probe():
    assert PROBE.is_file(), "bounded self-review probe is missing"
    spec = importlib.util.spec_from_file_location("_7e03_parametric_probe_test_subject", PROBE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def p():
    return load_prototype()


def _canonical_program() -> str:
    rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines() if line.strip()]
    sources = {row["program_solution"] for row in rows if row["task_id"] == TASK}
    assert len(sources) == 1
    return sources.pop()


def _tile(output, side, tile_r, tile_c):
    return [
        row[tile_c * side : (tile_c + 1) * side]
        for row in output[tile_r * side : (tile_r + 1) * side]
    ]


def test_existing_base_draws_are_valid_and_expose_high_nontrigger_colors():
    generator, _path, _sha = load_selected_generator(TASK, root=ROOT)
    saw_high = False
    for difficulty in (None, "medium"):
        for sample_index in range(8):
            grid = generator.generate(103, sample_index, difficulty=difficulty)
            assert generator.self_check(grid, difficulty=difficulty) == []
            saw_high = saw_high or any(value > 2 for row in grid for value in row)
    assert saw_high


def test_default_program_is_exact_catalog_authority(p):
    assert p.program({"trigger_mode": "color_2"}) == _canonical_program()


def test_center_cue_is_consumed_as_the_tile_predicate(p):
    grid = [
        [3, 2, 8],
        [0, 3, 2],
        [3, 1, 6],
    ]
    canonical = p.apply_python(grid, {"trigger_mode": "color_2"})
    center_cue = p.apply_python(grid, {"trigger_mode": "center_cue"})
    blank = [[0, 0, 0] for _ in range(3)]

    assert len(canonical) == len(canonical[0]) == 9
    assert _tile(canonical, 3, 0, 1) == grid
    assert _tile(canonical, 3, 1, 2) == grid
    assert _tile(canonical, 3, 1, 1) == blank

    assert _tile(center_cue, 3, 0, 0) == grid
    assert _tile(center_cue, 3, 1, 1) == grid
    assert _tile(center_cue, 3, 2, 0) == grid
    assert _tile(center_cue, 3, 0, 1) == blank


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_counts_unique_inputs_and_demo_only_identification(p, demos):
    for mode in ("color_2", "center_cue"):
        settings = {"trigger_mode": mode}
        episode = p.generate(17, settings, demos, 4)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
        assert len({json.dumps(grid) for grid in inputs}) == demos + 4
        report = p.teaching_report(episode["train"], settings)
        assert report["setting_survivors"] == [mode]
        assert report["plausible_rival_survivors"] == []
        assert report["fit_scope"] == "demonstrations_only"


@pytest.mark.parametrize("seed", [0, 9, 17, 23])
@pytest.mark.parametrize("mode", ["color_2", "center_cue"])
def test_two_constructive_demos_reject_every_declared_rival(p, seed, mode):
    settings = {"trigger_mode": mode}
    inputs = p._all_train_inputs(seed)[:2]
    train = [{"input": grid, "output": p.apply_python(grid, settings)} for grid in inputs]
    report = p.teaching_report(train, settings)
    assert report["setting_survivors"] == [mode]
    assert report["plausible_rival_survivors"] == []
    assert all(
        p.apply_rival(pair["input"], "value_gt_one") != pair["output"]
        for pair in train
    )


def test_teaching_cues_change_and_occur_away_from_center(p):
    inputs = p._all_train_inputs(0)[:2]
    cues = []
    for grid in inputs:
        mid = len(grid) // 2
        cue = grid[mid][mid]
        cues.append(cue)
        assert cue not in (0, 2)
        assert sum(value == cue for row in grid for value in row) >= 2
        assert any(value == 2 for row in grid for value in row)
        assert any(value > 2 and value != cue for row in grid for value in row)
    assert cues[0] != cues[1]


def test_setting_independent_inputs_query_prefix_and_maximum_output(p):
    a = p.generate(23, {"trigger_mode": "color_2"}, 3, 4)
    b = p.generate(23, {"trigger_mode": "center_cue"}, 3, 4)
    one = p.generate(23, {"trigger_mode": "color_2"}, 3, 1)
    for split in ("train", "test"):
        assert [x["input"] for x in a[split]] == [x["input"] for x in b[split]]
    assert one["train"] == a["train"]
    assert one["test"][0] == a["test"][0]

    maximum_input = a["test"][3]["input"]
    maximum_output = a["test"][3]["output"]
    assert len(maximum_input) == len(maximum_input[0]) == 5
    assert len(maximum_output) == len(maximum_output[0]) == 25
    for r0 in (0, 12):
        for c0 in (0, 12):
            assert sum(
                value != 0
                for row in maximum_output[r0 : r0 + 13]
                for value in row[c0 : c0 + 13]
            ) >= 4


def _mode_value(values, tie):
    counts = {value: values.count(value) for value in set(values)}
    best = max(counts.values())
    if tie == "first":
        return next(value for value in values if counts[value] == best)
    tied = [value for value, count in counts.items() if count == best]
    return min(tied) if tie == "min" else max(tied)


@pytest.mark.parametrize("seed", [0, 1, 2, 9, 17, 23, 100])
@pytest.mark.parametrize("mode", ["color_2", "center_cue"])
def test_two_demo_certificate_rejects_every_noncenter_fixed_anchor_cue(p, seed, mode):
    settings = {"trigger_mode": mode}
    inputs = p._all_train_inputs(seed)[:2]
    expected = [p.apply_python(grid, settings) for grid in inputs]
    anchors = [
        (row_anchor, col_anchor)
        for row_anchor in range(3)
        for col_anchor in range(3)
        if (row_anchor, col_anchor) != (1, 1)
    ]

    for row_anchor, col_anchor in anchors:
        actual = []
        for grid in inputs:
            row = row_anchor * (len(grid) - 1) // 2
            col = col_anchor * (len(grid[0]) - 1) // 2
            actual.append(p._self_tile_value(grid, grid[row][col]))
        assert actual != expected, (seed, mode, row_anchor, col_anchor)


@pytest.mark.parametrize("seed", [0, 1, 2, 9, 17, 23, 100])
@pytest.mark.parametrize("mode", ["color_2", "center_cue"])
def test_two_demo_certificate_rejects_global_and_fixed_line_modes(p, seed, mode):
    settings = {"trigger_mode": mode}
    inputs = p._all_train_inputs(seed)[:2]
    expected = [p.apply_python(grid, settings) for grid in inputs]

    candidates = []
    for tie in ("first", "min", "max"):
        candidates.append(
            (
                f"global_mode_{tie}",
                lambda grid, tie=tie: _mode_value(
                    [value for row in grid for value in row], tie
                ),
            )
        )
        for row_anchor in range(3):
            candidates.append(
                (
                    f"row_{row_anchor}_mode_{tie}",
                    lambda grid, tie=tie, row_anchor=row_anchor: _mode_value(
                        grid[row_anchor * (len(grid) - 1) // 2], tie
                    ),
                )
            )
        for col_anchor in range(3):
            candidates.append(
                (
                    f"col_{col_anchor}_mode_{tie}",
                    lambda grid, tie=tie, col_anchor=col_anchor: _mode_value(
                        [
                            row[col_anchor * (len(grid[0]) - 1) // 2]
                            for row in grid
                        ],
                        tie,
                    ),
                )
            )

    for name, trigger in candidates:
        actual = [p._self_tile_value(grid, trigger(grid)) for grid in inputs]
        assert actual != expected, (seed, mode, name)


@pytest.mark.parametrize(
    "patch",
    [
        {"seed": True},
        {"seed": -1},
        {"demos": 1},
        {"demos": 7},
        {"demos": 2.0},
        {"queries": 0},
        {"queries": 5},
        {"queries": True},
        {"settings": {}},
        {"settings": {"trigger_mode": "wrong"}},
        {"settings": {"trigger_mode": "color_2", "extra": 1}},
    ],
)
def test_invalid_requests_are_rejected(p, patch):
    args = {
        "seed": 0,
        "settings": {"trigger_mode": "color_2"},
        "demos": 2,
        "queries": 4,
    }
    args.update(patch)
    with pytest.raises(ValueError):
        p.generate(**args)


def test_adapter_loads_adjacent_implementation_not_cached_module(p):
    previous = sys.modules.get("prototype")
    sys.modules["prototype"] = types.ModuleType("prototype")
    try:
        spec = importlib.util.spec_from_file_location(
            "_7e03_native_adapter_test", PARAMETRIC / "adapter.py"
        )
        assert spec is not None and spec.loader is not None
        adapter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(adapter)
        settings = {"trigger_mode": "center_cue"}
        assert adapter.program(settings) == p.program(settings)
        assert adapter.generate(9, settings, 2, 4) == p.generate(9, settings, 2, 4)
    finally:
        if previous is None:
            sys.modules.pop("prototype", None)
        else:
            sys.modules["prototype"] = previous


def test_bounded_probe_covers_every_setting_count_and_maximum_query(p):
    probe = load_probe()
    report = probe.build_study(p, seeds=[0, 17])
    assert report["schema"] == "7e03da0eb439-parametric-self-review-v1"
    assert report["jobs"] == 20
    assert report["successes"] == 20
    assert report["failures"] == []
    assert report["settings"] == ["color_2", "center_cue"]
    assert report["demo_counts"] == [2, 3, 4, 5, 6]
    assert report["matched_inputs_across_settings"] is True
    assert report["query_prefix_stable"] is True
    assert report["max_input_shape"] == [5, 5]
    assert report["max_output_shape"] == [25, 25]
    assert report["all_declared_rivals_rejected"] is True
    assert probe.DEFAULT_SEEDS == (0, 1, 2, 9, 17, 23, 100)
    assert report["declared_rival_count"] == len(p.RIVALS) == 40
    assert report["rival_family_counts"] == {
        "fixed_anchor_cue": 8,
        "fixed_color": 8,
        "global_or_line_mode": 21,
        "other": 3,
    }
    assert report["teaching_pair_coordinate_certificate_passed"] is True
