from __future__ import annotations

import importlib.util
import json
import random
from pathlib import Path

import pytest

TASK_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location(
    "generator_27bc4c66eed7_under_test", TASK_DIR / "generator.py"
)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _canonical_pairs():
    path = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == GEN.TASK_ID:
                return list(row["train"]) + list(row["test"])
    raise AssertionError("canonical task row not found")


def _run_lengths(grid):
    return [end - start + 1 for _, start, end, _ in GEN._horizontal_runs(grid)]


def _has_shared_row(grid):
    rows = [r for r, *_ in GEN._horizontal_runs(grid)]
    return len(rows) != len(set(rows))


def test_rule_pin_and_executable_semantic_contract_are_declared():
    assert GEN.RULE_HASH == "a6711bc4802c"
    assert "one_midpoint_per_color" in GEN.SEMANTIC_RIVALS
    assert "one_midpoint_per_color" in GEN.CANONICAL_SHORTCUTS
    assert GEN.WITNESS_RIVALS["repeated_color_runs"] == (
        "one_midpoint_per_color",
    )


def test_every_canonical_input_is_owned_and_python_mirror_matches_outputs():
    for pair in _canonical_pairs():
        assert GEN.self_check(pair["input"]) == []
        assert GEN.apply_rule(pair["input"]) == pair["output"]


def test_self_check_accepts_lawful_edge_cases_authority_handles():
    grid = [
        [1, 1, 1, 0, 2, 2, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [3, 0, 3, 3, 3, 3, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [4, 4, 4, 4, 4, 0, 0, 0, 0],
    ]
    assert GEN.self_check(grid) == []
    output = GEN.apply_rule(grid)
    # singleton, right-middle of even runs, and both repeated-color runs survive.
    assert output[2][0] == 3
    assert output[2][4] == 3
    assert output[0][5] == 2
    assert sum(cell != 0 for row in output for cell in row) == 5


def test_exact_overrides_round_trip_and_unknown_key_is_rejected():
    requested = {
        "grid_h": 5,
        "grid_w": 7,
        "n_runs": 4,
        "color_mode": "repeat",
        "run_length": 0,
    }
    grid = GEN.generate(41, 9, difficulty="hard", **requested)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == requested
    with pytest.raises((TypeError, ValueError), match="unknown"):
        GEN.generate(0, 0, typo_axis=1)


@pytest.mark.parametrize("grid_h", [5, 7])
@pytest.mark.parametrize("grid_w", [7, 10])
@pytest.mark.parametrize("n_runs", [2, 5])
@pytest.mark.parametrize("color_mode", ["distinct", "repeat"])
@pytest.mark.parametrize("run_length", [0, 1, 5])
def test_boundary_override_matrix_is_constructive(
    grid_h, grid_w, n_runs, color_mode, run_length
):
    requested = {
        "grid_h": grid_h,
        "grid_w": grid_w,
        "n_runs": n_runs,
        "color_mode": color_mode,
        "run_length": run_length,
    }
    grid = GEN.generate(991, 23, difficulty="medium", **requested)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == requested


def test_declared_rival_fits_canonical_but_loses_on_exact_counterexample():
    rival = GEN.SEMANTIC_RIVALS["one_midpoint_per_color"]
    for pair in _canonical_pairs():
        assert rival(pair["input"]) == pair["output"]

    counterexample = [
        [5, 5, 5, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 5, 5, 5, 5, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [2, 2, 0, 0, 0, 0, 0],
    ]
    assert GEN.SEMANTIC_WITNESSES["repeated_color_runs"](counterexample)
    expected = GEN.apply_rule(counterexample)
    shortcut = rival(counterexample)
    assert expected != shortcut
    assert expected[0][1] == 5 and expected[2][3] == 5
    assert shortcut[0][1] == 5 and shortcut[2][3] == 0


def test_default_census_has_canonical_anchors_and_adversarial_coverage():
    canonical_profiles = {
        (len(pair["input"]), len(pair["input"][0]), len({c for row in pair["input"] for c in row}))
        for pair in _canonical_pairs()
    }
    all_grids = []
    for band_index, band in enumerate(("easy", "medium", "hard")):
        grids = [GEN.generate(7000 + band_index, i, difficulty=band) for i in range(100)]
        all_grids.extend(grids)
        assert all(GEN.self_check(grid) == [] for grid in grids)
        assert sum(GEN.SEMANTIC_WITNESSES["repeated_color_runs"](g) for g in grids) >= 18
        assert sum(_has_shared_row(g) for g in grids) >= 35
        assert sum(any(length % 2 == 0 for length in _run_lengths(g)) for g in grids) >= 35
        assert sum(any(length == 1 for length in _run_lengths(g)) for g in grids) >= 18
        assert sum(
            (len(g), len(g[0]), len({c for row in g for c in row})) in canonical_profiles
            for g in grids
        ) >= 70

    assert len({tuple(map(tuple, grid)) for grid in all_grids}) >= 290
    assert any(1 in {c for row in grid for c in row} for grid in all_grids)


def test_generation_does_not_mutate_global_random_state():
    random.seed(123456)
    before = random.getstate()
    GEN.generate(11, 12, difficulty="hard")
    after = random.getstate()
    assert after == before


def test_ambiguous_monochrome_solid_2x2_is_outside_teaching_grammar():
    grid = [[0] * 7 for _ in range(5)]
    for row in (0, 1):
        for column in (0, 1):
            grid[row][column] = 6
    assert any("solid 2x2" in reason for reason in GEN.self_check(grid))
    for seed in range(40):
        generated = GEN.generate(
            seed,
            seed,
            grid_h=5,
            grid_w=7,
            n_runs=2,
            color_mode="repeat",
            run_length=2,
        )
        assert GEN.self_check(generated) == []


def test_default_sampler_exercises_full_run_length_axis():
    observed = {
        GEN.observe_overrides(GEN.generate(99, sample_index))["run_length"]
        for sample_index in range(30)
    }
    assert observed == {0, 2, 3, 4, 5}


def test_ordinary_sampler_never_emits_identity_only_all_singleton_scene():
    for sample_index in range(60):
        grid = GEN.generate(1234, sample_index, difficulty="medium")
        assert GEN.apply_rule(grid) != grid
