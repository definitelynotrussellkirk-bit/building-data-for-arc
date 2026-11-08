"""Focused semantic, override, and curriculum regressions for 395201c95f9d."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random

import pytest

TASK_ID = "395201c95f9d"
REPO_ROOT = Path(__file__).resolve().parents[3]
GEN_PATH = REPO_ROOT / "generators" / TASK_ID / "generator.py"
SPEC = importlib.util.spec_from_file_location(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator", GEN_PATH
)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _canonical_record() -> dict:
    path = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("task_id") == TASK_ID:
                return record
    raise AssertionError("canonical record missing")


def _canonical_pairs() -> list[dict]:
    record = _canonical_record()
    test = record["test"]
    return list(record["train"]) + (list(test) if isinstance(test, list) else [test])


def _canonical_rule_hash() -> str:
    source = _canonical_record()["program_solution"]
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _pair(seed: int, sample_index: int, difficulty: str) -> dict:
    grid = GEN.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def _profile(grid: list[list[int]]) -> tuple[int, int, int]:
    return (len(grid), len(grid[0]), len({value for row in grid for value in row}))


def test_rule_hash_is_pinned_to_selected_authority():
    assert GEN.RULE_HASH == _canonical_rule_hash() == "a99b04260a01"


def test_canonical_inputs_are_accepted_and_python_mirror_matches_outputs():
    pairs = _canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        grid = copy.deepcopy(pair["input"])
        original = copy.deepcopy(grid)
        assert GEN.self_check(grid) == []
        assert GEN.strict_canonical_like(grid) == []
        assert GEN.rule_mirror(grid) == pair["output"]
        assert grid == original


def test_unknown_overrides_and_unknown_difficulty_are_rejected():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, difficulty="medium", typo_axis=7)
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(1, 0, difficulty="impossible")


@pytest.mark.parametrize("panel_h,panel_w", [(4, 4), (5, 5), (8, 7)])
@pytest.mark.parametrize("cell_count", [4, 5, 6])
@pytest.mark.parametrize("match_panel", [0, 1])
@pytest.mark.parametrize("transform", ["id", "r1", "r2", "r3", "fh", "fv", "tr", "atr"])
def test_exact_axes_are_observable(panel_h, panel_w, cell_count, match_panel, transform):
    requested = {
        "panel_h": panel_h,
        "panel_w": panel_w,
        "cell_count": cell_count,
        "match_panel": match_panel,
        "transform": transform,
    }
    grid = GEN.generate(901, 17, difficulty="hard", **requested)
    assert GEN.self_check(grid, meta={"overrides": requested}) == []
    assert GEN.observe_overrides(grid) == requested
    assert len(grid) == panel_h
    assert len(grid[0]) == 3 * panel_w + 2


def test_natural_sweep_owns_rule_and_breaks_the_exact_coordinate_shortcut():
    exact_rival = GEN.SEMANTIC_RIVALS["exact_coordinates_else_panel_1"]
    canonical_profile = (5, 17, 7)
    for band in ("easy", "medium", "hard"):
        facts_by_index = []
        profiles = set()
        exact_rival_refuted = 0
        for sample_index in range(32):
            grid = GEN.generate(40_000 + sample_index, sample_index, difficulty=band)
            facts = GEN.semantic_observables(grid)
            facts_by_index.append(facts)
            profiles.add(_profile(grid))
            assert facts["errors"] == []
            assert facts["matched_transform_count"] == 1
            assert len(set(facts["prototype_counts"] + (facts["query_count"],))) == 1
            assert facts["query_color"] not in facts["label_colors"]
            assert facts["query_raw_cells"] != facts["prototype_raw_cells"][facts["matched_panel"]]
            assert GEN.self_check(grid) == []
            if exact_rival(grid) != GEN.rule_mirror(grid):
                exact_rival_refuted += 1
        assert {facts["matched_panel"] for facts in facts_by_index} == {0, 1}
        assert {facts["cell_count"] for facts in facts_by_index} == {
            {"easy": 4, "medium": 5, "hard": 6}[band]
        }
        assert any(facts["transform"] in GEN._REFLECTION_CODES for facts in facts_by_index)
        assert exact_rival_refuted > 0
        assert canonical_profile in profiles
        assert len(profiles) > 1


def test_schedule_crosses_every_d4_transform_with_both_panels():
    expected = {(panel, code) for panel in (0, 1) for code in GEN._CODES}
    observed = {
        GEN.schedule_profile(123, sample_index, "medium")
        for sample_index in range(16)
    }
    assert set(GEN.SCHEDULE_PROFILES) == expected
    assert observed == expected


def test_four_example_windows_refute_panel_transform_shortcuts():
    expected_shortcuts = {
        "panel1_rotations_else_panel0",
        "panel1_reflections_else_panel0",
        "panel0_rotations_else_panel1",
        "panel0_reflections_else_panel1",
    }
    assert expected_shortcuts <= set(GEN.LESSON_COMPETITORS)
    for band in ("easy", "medium", "hard"):
        for start in range(len(GEN.SCHEDULE_PROFILES)):
            demos = [_pair(76_000 + start, start + offset, band) for offset in range(4)]
            profiles = {
                (
                    GEN.observe_overrides(pair["input"])["match_panel"],
                    GEN.observe_overrides(pair["input"])["transform"] in GEN._REFLECTION_CODES,
                )
                for pair in demos
            }
            assert profiles == {(0, False), (0, True), (1, False), (1, True)}
            for name in expected_shortcuts:
                rival = GEN.LESSON_COMPETITORS[name]
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                    band,
                    start,
                    name,
                )


def test_every_four_example_lesson_refutes_declared_competitors():
    for band in ("easy", "medium", "hard"):
        for start in range(len(GEN.SCHEDULE_PROFILES)):
            demos = [
                _pair(77_000 + start, start + offset, band)
                for offset in range(GEN.EXAMPLES_NEEDED)
            ]
            query = _pair(77_000 + start, start + GEN.EXAMPLES_NEEDED, band)
            assert {
                GEN.observe_overrides(pair["input"])["match_panel"]
                for pair in demos
            } == {0, 1}
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                    band,
                    start,
                    name,
                )
            assert GEN.lesson_identifiable(demos, query) == []


def test_canonical_data_refutes_the_old_exact_coordinate_shortcut():
    shortcut = GEN.CANONICAL_SHORTCUTS["exact_coordinates_else_panel_1"]
    pairs = _canonical_pairs()
    assert any(shortcut(pair["input"]) != pair["output"] for pair in pairs)
    assert all(GEN.rule_mirror(pair["input"]) == pair["output"] for pair in pairs)


def test_validator_rejects_task_local_near_misses():
    fixtures = GEN.mutation_fixtures()
    assert fixtures
    for name, grid in fixtures:
        assert GEN.self_check(grid), name


def test_replay_is_deterministic_fresh_and_global_rng_pure():
    random.seed(1927)
    before = random.getstate()
    first = GEN.generate(42, 7, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(42, 7, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second
