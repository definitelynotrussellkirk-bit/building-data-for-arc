from __future__ import annotations

import copy
import importlib
import json
from pathlib import Path
import random
import subprocess
import sys

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "2f7883fbd26f"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def _pairs() -> list[dict]:
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def _lesson(seed: int, start: int, band: str) -> tuple[list[dict], dict]:
    labelled: list[dict] = []
    for offset in range(GEN.EXAMPLES_NEEDED + 1):
        grid = GEN.generate(seed, start + offset, difficulty=band)
        labelled.append({"input": grid, "output": GEN._reference_output(grid)})
    return labelled[:-1], labelled[-1]


def test_rule_pin_reference_and_all_canonical_pairs_are_exact() -> None:
    assert GEN.RULE_HASH == "6de5b0b7a0a5"
    pairs = _pairs()
    assert len(pairs) == 4
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN._reference_output(pair["input"]) == pair["output"]
        assert pair["input"] == original

    assert GEN.CANONICAL_SHORTCUTS
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert all(rival(copy.deepcopy(pair["input"])) == pair["output"] for pair in pairs), name


def test_every_declared_override_is_exact_at_dense_and_sparse_boundaries() -> None:
    cases = [
        dict(grid_h=9, grid_w=9, n_target_blocks=0, n_decoy_blocks=1,
             n_singleton_ones=1, n_singleton_twos=0),
        dict(grid_h=9, grid_w=9, n_target_blocks=5, n_decoy_blocks=4,
             n_singleton_ones=4, n_singleton_twos=4),
        dict(grid_h=12, grid_w=9, n_target_blocks=2, n_decoy_blocks=4,
             n_singleton_ones=2, n_singleton_twos=3),
        dict(grid_h=9, grid_w=12, n_target_blocks=4, n_decoy_blocks=1,
             n_singleton_ones=4, n_singleton_twos=1),
        dict(grid_h=12, grid_w=12, n_target_blocks=5, n_decoy_blocks=4,
             n_singleton_ones=4, n_singleton_twos=4),
    ]
    for band in ("easy", "medium", "hard"):
        for sample_index in (20, 21):  # both schedule profiles
            for case_index, case in enumerate(cases):
                grid = GEN.generate(10_000 + case_index, sample_index, difficulty=band, **case)
                assert GEN.self_check(grid) == [], (band, sample_index, case, GEN.self_check(grid))
                assert GEN.strict_canonical_like(grid) == []
                observed = GEN.observe_overrides(grid)
                assert observed == case
                assert GEN._reference_output(grid) == [[1] * case["n_target_blocks"] + [0] * (5 - case["n_target_blocks"])]


def test_each_count_axis_round_trips_on_both_schedule_profiles() -> None:
    defaults = dict(
        grid_h=9,
        grid_w=9,
        n_target_blocks=3,
        n_decoy_blocks=2,
        n_singleton_ones=2,
        n_singleton_twos=2,
    )
    domains = {
        "n_target_blocks": range(0, 6),
        "n_decoy_blocks": range(1, 5),
        "n_singleton_ones": range(1, 5),
        "n_singleton_twos": range(0, 5),
    }
    for axis, values in domains.items():
        for value in values:
            case = dict(defaults)
            case[axis] = value
            for sample_index in (30, 31):
                grid = GEN.generate(2000 + value, sample_index, difficulty="hard", **case)
                assert GEN.self_check(grid) == []
                assert GEN.observe_overrides(grid) == case


def test_schedule_makes_every_two_demo_window_refute_declared_shortcuts() -> None:
    assert GEN.EXAMPLES_NEEDED == 2
    assert GEN.SCHEDULE_PERIOD == 3
    assert set(GEN.SCHEDULE_PROFILES) == {"canonical_separated", "overlap_counterexample"}
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for start in range(GEN.SCHEDULE_PERIOD):
            for seed_offset in range(5):
                demos, query = _lesson(30_000 + 100 * band_index + seed_offset, start, band)
                assert GEN.lesson_identifiable(demos, query) == []
                assert any(GEN.SEMANTIC_WITNESSES["overlapping_target_windows"](d["input"]) for d in demos)
                for name, rival in GEN.LESSON_COMPETITORS.items():
                    assert any(rival(copy.deepcopy(d["input"])) != d["output"] for d in demos), (
                        band, start, seed_offset, name
                    )


def test_every_query_rotation_of_a_three_pair_lesson_is_identifiable() -> None:
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for start in range(GEN.SCHEDULE_PERIOD):
            for seed_offset in range(4):
                labelled = []
                seed = 60_000 + 100 * band_index + 10 * start + seed_offset
                for offset in range(GEN.EXAMPLES_NEEDED + 1):
                    grid = GEN.generate(seed, start + offset, difficulty=band)
                    labelled.append({"input": grid, "output": GEN._reference_output(grid)})
                for query_index in range(len(labelled)):
                    query = labelled[query_index]
                    demos = [pair for index, pair in enumerate(labelled) if index != query_index]
                    assert GEN.lesson_identifiable(demos, query) == [], (
                        band, start, seed_offset, query_index
                    )
                    for name, rival in GEN.LESSON_COMPETITORS.items():
                        assert any(rival(copy.deepcopy(d["input"])) != d["output"] for d in demos), (
                            band, start, seed_offset, query_index, name
                        )


def test_overlap_counterexample_disagrees_with_both_canonical_shortcuts() -> None:
    grid = GEN.generate(
        77,
        1,
        difficulty="medium",
        grid_h=9,
        grid_w=9,
        n_target_blocks=2,
        n_decoy_blocks=2,
        n_singleton_ones=2,
        n_singleton_twos=1,
    )
    expected = [[1, 1, 0, 0, 0]]
    assert GEN.schedule_profile(77, 1, "medium") == "overlap_counterexample"
    assert GEN._reference_output(grid) == expected
    assert GEN.SEMANTIC_WITNESSES["overlapping_target_windows"](grid)
    for name in GEN.WITNESS_RIVALS["overlapping_target_windows"]:
        assert GEN.SEMANTIC_RIVALS[name](copy.deepcopy(grid)) != expected


def test_default_schedule_reaches_all_six_encodable_outputs() -> None:
    outputs = {
        tuple(GEN._reference_output(GEN.generate(91_000, index, difficulty="medium"))[0])
        for index in range(120)
    }
    assert outputs == {
        (0, 0, 0, 0, 0),
        (1, 0, 0, 0, 0),
        (1, 1, 0, 0, 0),
        (1, 1, 1, 0, 0),
        (1, 1, 1, 1, 0),
        (1, 1, 1, 1, 1),
    }


def test_unknown_invalid_controls_determinism_freshness_and_rng_purity() -> None:
    with pytest.raises((TypeError, ValueError), match="unknown override"):
        GEN.generate(1, 2, invented_axis="accepted")
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(1, 2, difficulty="extreme")
    with pytest.raises(ValueError, match="n_target_blocks"):
        GEN.generate(1, 2, n_target_blocks=6)
    with pytest.raises(ValueError, match="n_decoy_blocks"):
        GEN.generate(1, 2, n_decoy_blocks=0)

    random.seed(20261004)
    state = random.getstate()
    first = GEN.generate(777, 999, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(777, 999, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9
    assert first != second


def test_mutation_fixtures_are_rejected_and_do_not_mutate_inputs() -> None:
    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 5
    for name, grid in fixtures:
        original = copy.deepcopy(grid)
        assert GEN.self_check(grid), name
        assert grid == original


def test_workspace_probe_covers_every_schedule_residue(tmp_path: Path) -> None:
    script = Path(__file__).resolve().parents[1] / "workspace" / "lesson_window_probe.py"
    report_path = tmp_path / "lesson-window-report.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(script),
            "--seeds-per-start",
            "2",
            "--out",
            str(report_path),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(report_path.read_text())
    expected_windows = 3 * GEN.SCHEDULE_PERIOD * 2
    assert report["status"] == "pass"
    assert report["windows_total"] == expected_windows
    assert report["failures"] == []
    assert set(report["canonical_shortcut_fits"]) == set(GEN.CANONICAL_SHORTCUTS)
    assert set(report["rival_refuted_in_demos"]) == set(GEN.LESSON_COMPETITORS)
    assert set(report["rival_refuted_in_demos"].values()) == {expected_windows}
    assert report["witness_present_in_demos"]["overlapping_target_windows"] == expected_windows
