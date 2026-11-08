"""Source-bound regressions for the red-marker quadrant generator."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import itertools
import json
from pathlib import Path
import random
import subprocess
import sys

import pytest

TASK_ID = "637229802e6f"
HOME = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "shared" / "runtime"))

from reviewer_support import canonical_pairs, find_root  # noqa: E402


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"reviewed_{TASK_ID}", HOME / "generator.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()
ROOT = find_root(__file__)


def _pairs():
    return canonical_pairs(TASK_ID, root=ROOT)


def independent_rule(grid):
    positions = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    ]
    assert len(positions) == 1
    marker_r, marker_c = positions[0]
    top = marker_r < 2
    left = marker_c < 2
    output = [[6 for _ in range(4)] for _ in range(4)]
    r0 = 0 if top else 2
    c0 = 0 if left else 2
    for r in range(r0, r0 + 2):
        for c in range(c0, c0 + 2):
            output[r][c] = 2
    return output


def _quadrant(grid):
    marker = next(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    )
    return (
        ("top" if marker[0] < 2 else "bottom")
        + "_"
        + ("left" if marker[1] < 2 else "right")
    )


def _profile(grid):
    decorations = [value for row in grid for value in row if value not in (2, 6)]
    return len(decorations), len(set(decorations))


def test_declares_truthful_source_bound_contract():
    assert gen.GENERATOR_ID == TASK_ID
    assert gen.TASK_ID == TASK_ID
    assert gen.VERSION == "4.0.0"
    assert gen.RULE_HASH == "315e7341b297"
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.LESSON_SCHEDULE_PERIOD == 4
    assert gen.MIN_STRICT_FRAC == 1.0
    assert gen.EXPECTED_OUTPUT_CODOMAIN == 4
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert set(gen.AXES) == {
        "marker_quadrant",
        "marker_slot",
        "decoration_profile",
    }


def test_all_canonical_pairs_are_accepted_and_match_independent_oracle():
    pairs = _pairs()
    assert len(pairs) == 4
    assert {_profile(pair["input"]) for pair in pairs} == {
        (3, 3),
        (4, 4),
        (7, 4),
        (7, 6),
    }
    for pair in pairs:
        original = deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert independent_rule(pair["input"]) == pair["output"]
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize(
    "quadrant,slot,profile",
    itertools.product(
        ("top_left", "top_right", "bottom_left", "bottom_right"),
        range(4),
        ("sparse3", "sparse4", "dense4", "dense6"),
    ),
)
def test_every_advertised_override_combination_is_exact(quadrant, slot, profile):
    requested = {
        "marker_quadrant": quadrant,
        "marker_slot": slot,
        "decoration_profile": profile,
    }
    grid = gen.generate(8123, 17, difficulty="hard", **requested)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == requested
    assert gen.rule_mirror(grid) == independent_rule(grid)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo": 1},
        {"marker_quadrant": "center"},
        {"marker_slot": -1},
        {"marker_slot": 4},
        {"marker_slot": True},
        {"marker_slot": 1.0},
        {"marker_slot": "1"},
        {"decoration_profile": "tiny"},
        {"difficulty": "expert"},
        {"sample_index": -1},
        {"sample_index": True},
        {"sample_index": 1.0},
        {"sample_index": "1"},
    ],
)
def test_rejects_unknown_out_of_range_and_wrong_type_requests(kwargs):
    call = {"seed": 0, "sample_index": 0}
    call.update(kwargs)
    with pytest.raises((TypeError, ValueError)):
        gen.generate(**call)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_generation_is_strict_deterministic_and_rule_lawful(band):
    for index in range(80):
        first = gen.generate(5000 + index, index, difficulty=band)
        second = gen.generate(5000 + index, index, difficulty=band)
        assert first == second
        assert first is not second
        assert all(a is not b for a, b in zip(first, second))
        assert gen.self_check(first) == []
        assert gen.strict_canonical_like(first) == []
        assert gen.rule_mirror(first) == independent_rule(first)
        assert _profile(first) in {(3, 3), (4, 4), (7, 4), (7, 6)}


def test_difficulty_bands_are_not_byte_identical():
    for index in range(24):
        grids = [
            gen.generate(9000 + index, index, difficulty=band)
            for band in ("easy", "medium", "hard")
        ]
        assert len({tuple(map(tuple, grid)) for grid in grids}) == 3


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("start", range(12))
def test_every_three_demo_window_covers_both_quadrant_bits_and_refutes_competitors(
    band, start
):
    seed = 6100 + start
    demos = []
    for offset in range(gen.EXAMPLES_NEEDED):
        index = start + offset
        grid = gen.generate(seed, index, difficulty=band)
        demos.append({"input": grid, "output": independent_rule(grid)})
    query_grid = gen.generate(seed, start + gen.EXAMPLES_NEEDED, difficulty=band)
    query = {"input": query_grid, "output": independent_rule(query_grid)}

    seen = {_quadrant(pair["input"]) for pair in demos}
    assert {name.split("_")[0] for name in seen} == {"top", "bottom"}
    assert {name.split("_")[1] for name in seen} == {"left", "right"}
    assert gen.lesson_identifiable(demos, query) == []
    for name, rival in gen.LESSON_COMPETITORS.items():
        assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_schedule_profile_matches_generated_quadrant_for_full_period():
    for band in ("easy", "medium", "hard"):
        for seed in (0, 1, 987654):
            observed = []
            for index in range(gen.LESSON_SCHEDULE_PERIOD):
                grid = gen.generate(seed, index, difficulty=band)
                profile = gen.schedule_profile(seed, index, band)
                assert profile == _quadrant(grid)
                observed.append(profile)
            assert set(observed) == set(gen.SCHEDULE_PROFILES)


def test_semantic_witnesses_fire_and_named_wrong_rules_disagree():
    for quadrant in gen.QUADRANTS:
        grid = gen.generate(42, 3, marker_quadrant=quadrant)
        expected = independent_rule(grid)
        assert gen.SEMANTIC_WITNESSES[quadrant](grid)
        for rival_name in gen.WITNESS_RIVALS[quadrant]:
            assert gen.SEMANTIC_RIVALS[rival_name](grid) != expected


def test_self_check_rejects_minimal_impostors_and_malformed_grids():
    singleton = [[6] * 4 for _ in range(4)]
    singleton[0][0] = 2
    assert gen.self_check(singleton)
    for bad in (None, [], [[]], [[6], [6, 6]], [[True] * 4 for _ in range(4)]):
        assert gen.self_check(bad)
        assert gen.strict_canonical_like(bad)


def test_rule_and_rivals_do_not_mutate_input():
    grid = gen.generate(77, 9, difficulty="hard")
    original = deepcopy(grid)
    gen.rule_mirror(grid)
    for rival in gen.SEMANTIC_RIVALS.values():
        rival(grid)
    assert grid == original


def test_generation_does_not_touch_global_random_state():
    state = random.getstate()
    for band in (None, "easy", "medium", "hard"):
        for index in range(20):
            gen.generate(111 + index, index, difficulty=band)
    assert random.getstate() == state


def test_maintainer_contract_probe_is_runnable_and_complete(tmp_path):
    report_path = tmp_path / "contract-report.json"
    probe = HOME / "workspace" / "probe_contract.py"
    result = subprocess.run(
        [sys.executable, str(probe), "--out", str(report_path)],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(report_path.read_text())
    assert report["ok"] is True
    assert report["canonical_pairs"] == 4
    assert report["exact_axis_combinations"] == 64
    assert report["distinct_outputs"] == gen.EXPECTED_OUTPUT_CODOMAIN == 4
    assert report["schedule_cases"] == 48
    assert report["schedule_failures"] == []


def test_retained_two_quadrant_schedule_counterexample_matches_current_contract():
    path = HOME / "counterexamples" / "two-quadrant-schedule.json"
    witness = json.loads(path.read_text())
    assert witness["task_id"] == TASK_ID
    assert witness["before"]["quadrants"] == [
        "top_left",
        "bottom_left",
        "top_left",
        "bottom_left",
    ]
    assert witness["before"]["unique_quadrants"] == 2
    current = [gen.schedule_profile(0, index, "easy") for index in range(4)]
    assert witness["after"]["quadrants"] == current
    assert witness["after"]["unique_quadrants"] == 4
