from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK = "aae03e82a263"
ROOT = find_root(__file__)

try:
    from puzzle_generators.per_puzzle.aae03e82a263 import generator as gen
except ModuleNotFoundError:
    import importlib.util

    source = ROOT / "generators" / TASK / "generator.py"
    spec = importlib.util.spec_from_file_location(f"review_{TASK}_generator", source)
    assert spec is not None and spec.loader is not None
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)


def _data_file(relative: str) -> Path:
    for prefix in (Path("data"), Path("shared/data")):
        candidate = ROOT / prefix / relative
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(relative)


def _canonical_row() -> dict:
    path = _data_file("canonical/puzzles.jsonl")
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise AssertionError("canonical task not found")


def _pairs() -> list[dict]:
    return canonical_pairs(TASK, root=ROOT)


def _labelled_lesson(seed: int, band: str) -> list[dict]:
    return [
        {
            "input": grid,
            "output": gen.rule_mirror(grid),
        }
        for index in range(gen.LESSON_SCHEDULE_PERIOD)
        for grid in [gen.generate(seed, index, difficulty=band)]
    ]


def _component_sizes(grid) -> list[int]:
    return sorted(component["size"] for component in gen._components(grid))


def test_rule_pin_and_selected_authorities_are_exactly_synced():
    row = _canonical_row()
    source = row["program_solution"]
    digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
    assert gen.RULE_HASH == digest == "69eaaa031800"

    base = json.loads(
        _data_file("base/solutions/banks/4e772fa039b8/H62__aae03e82a263.json").read_text(
            encoding="utf-8"
        )
    )
    assert base["racket_target"]["raw_code"] == source
    assert base["racket_target"]["target_code"] == source


def test_all_canonical_pairs_are_accepted_and_rule_mirror_is_exact():
    pairs = _pairs()
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_generation_is_deterministic_fresh_and_global_rng_pure(band):
    random.seed(9417)
    before = random.getstate()
    first = gen.generate(271, 9, difficulty=band)
    untouched = copy.deepcopy(first)
    first[0][0] = 9 if first[0][0] != 9 else 8
    second = gen.generate(271, 9, difficulty=band)

    assert random.getstate() == before
    assert second == untouched
    assert second is not first
    assert all(left is not right for left, right in zip(second, first))
    assert gen.self_check(second) == []


@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 12},
        {"grid_h": 18},
        {"grid_w": 12},
        {"grid_w": 18},
        {"n_objects": 3},
        {"n_objects": 5},
        {"median_size": 4},
        {"median_size": 6},
        {"grid_h": 12, "grid_w": 12, "n_objects": 5, "median_size": 6},
        {"grid_h": 18, "grid_w": 18, "n_objects": 3, "median_size": 4},
    ],
)
def test_exact_overrides_are_consumed_and_observable_in_every_band(overrides):
    for band in ("easy", "medium", "hard"):
        grid = gen.generate(719, 7, difficulty=band, **overrides)
        assert gen.self_check(grid) == []
        observed = gen.observe_overrides(grid)
        for name, value in overrides.items():
            assert observed[name] == value


@pytest.mark.parametrize(
    "overrides",
    [
        {"made_up_axis": 1},
        {"grid_h": 11},
        {"grid_w": 19},
        {"n_objects": 4},
        {"median_size": 3},
        {"grid_h": True},
        {"n_objects": "3"},
    ],
)
def test_invalid_and_unknown_overrides_fail_loudly(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 2, **overrides)


def test_self_check_rejects_empty_single_tied_even_and_wrong_color_impostors():
    empty = [[0] * 12 for _ in range(12)]

    singleton = [[0] * 12 for _ in range(12)]
    singleton[1][1] = singleton[1][2] = singleton[2][1] = 6

    tied = [[0] * 12 for _ in range(12)]
    for top, left in ((1, 1), (1, 6), (7, 1)):
        tied[top][left] = tied[top][left + 1] = 6

    even = gen.generate(31, 1, n_objects=3)
    even[10][10] = 6

    wrong_color = gen.generate(37, 2)
    first = next((r, c) for r, row in enumerate(wrong_color) for c, value in enumerate(row) if value == 6)
    wrong_color[first[0]][first[1]] = 7

    for grid in (empty, singleton, tied, even, wrong_color):
        assert gen.self_check(grid), grid


def test_every_schedule_slot_is_valid_and_teaches_noncanonical_axes():
    seen_counts = set()
    seen_medians = set()
    for band in ("easy", "medium", "hard"):
        for seed in range(8):
            lesson = _labelled_lesson(seed, band)
            assert len(lesson) == 5
            for pair in lesson:
                grid = pair["input"]
                assert gen.self_check(grid) == []
                assert gen.rule_mirror(grid) == pair["output"]
                observed = gen.observe_overrides(grid)
                seen_counts.add(observed["n_objects"])
                seen_medians.add(observed["median_size"])
    assert seen_counts == {3, 5}
    assert seen_medians == {4, 5, 6}


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_query_rotation_refutes_all_declared_rivals(band):
    for seed in range(12):
        lesson = _labelled_lesson(seed, band)
        for query_index, query in enumerate(lesson):
            demos = [pair for index, pair in enumerate(lesson) if index != query_index]
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(
                    rival(pair["input"]) != pair["output"] for pair in demos
                ), (band, seed, query_index, name)


def test_canonical_shortcuts_really_fit_canonical_and_schedule_refutes_them():
    pairs = _pairs()
    assert set(gen.CANONICAL_SHORTCUTS) >= {
        "fixed_size_five",
        "second_smallest",
    }
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name

    lesson = _labelled_lesson(413, "medium")
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert sum(rival(pair["input"]) != pair["output"] for pair in lesson) >= 2, name


def test_dimension_domains_bound_the_quadratic_override_matrix():
    assert gen.DIMENSION_VALUES == (12, 13, 18)
    assert gen.AXES["grid_h"]["valid"] == "12|13|18"
    assert gen.AXES["grid_w"]["valid"] == "12|13|18"

def test_distribution_varies_inputs_outputs_counts_sizes_and_dimensions():
    inputs = set()
    outputs = set()
    dimensions = set()
    count_profiles = set()
    median_sizes = set()
    for sample_index in range(180):
        band = ("easy", "medium", "hard")[sample_index % 3]
        grid = gen.generate(991, sample_index, difficulty=band)
        assert gen.self_check(grid) == []
        output = gen.rule_mirror(grid)
        inputs.add(tuple(map(tuple, grid)))
        outputs.add(tuple(map(tuple, output)))
        dimensions.add((len(grid), len(grid[0])))
        sizes = _component_sizes(grid)
        count_profiles.add(len(sizes))
        median_sizes.add(sizes[len(sizes) // 2])

    assert len(inputs) >= 170
    assert len(outputs) >= 25
    assert len(dimensions) >= 8
    assert count_profiles == {3, 5}
    assert median_sizes == {4, 5, 6}


def _counterexample_file(name: str) -> Path:
    return ROOT / "generators" / TASK / "counterexamples" / name


def test_retained_degenerate_counterexamples_remain_rejected():
    fixture = json.loads(_counterexample_file("degenerate_impostors.json").read_text())
    assert fixture["task_id"] == TASK
    assert fixture["generator_rule_hash"] == gen.RULE_HASH
    for case in fixture["cases"]:
        assert gen.self_check(case["input"]), case["name"]


def test_retained_canonical_shortcut_counterexamples_remain_refuted_by_lessons():
    fixture = json.loads(_counterexample_file("canonical_shortcuts.json").read_text())
    assert fixture["task_id"] == TASK
    pairs = _pairs()
    lesson_spec = fixture["refuting_lesson"]
    lesson = _labelled_lesson(lesson_spec["seed"], lesson_spec["difficulty"])
    for name in fixture["shortcut_names"]:
        rival = gen.CANONICAL_SHORTCUTS[name]
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name
        assert any(rival(pair["input"]) != pair["output"] for pair in lesson), name
