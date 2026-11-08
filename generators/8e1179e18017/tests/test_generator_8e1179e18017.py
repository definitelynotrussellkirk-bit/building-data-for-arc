"""Focused semantic regressions for generator 8e1179e18017."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
from pathlib import Path
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs

ROOT = Path(__file__).resolve().parents[1]
TASK = "8e1179e18017"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
BASE = ROOT / "data/base/solutions/banks/3cb9777539c7/M146__8e1179e18017.json"


def _canonical_source() -> str:
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row["program_solution"]
    raise AssertionError(f"missing canonical source for {TASK}")


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


def test_rule_hash_is_pinned_and_task_local_selected_source_is_semantically_synced():
    canonical = _canonical_source()
    digest = hashlib.sha256(" ".join(canonical.split()).encode()).hexdigest()[:12]
    assert digest == GEN.RULE_HASH == "a7b22243a1df"
    target = json.loads(BASE.read_text())["racket_target"]["target_code"]
    assert target == canonical
    assert ";;" in target
    target_meta = json.loads(BASE.read_text())["racket_target"]
    assert target_meta["target_code_role"] == "selected_task_rule"
    assert target_meta["raw_code_role"] == "archival_executable_source"


def test_all_canonical_inputs_are_accepted_and_outputs_mirror_exactly_and_purely():
    pairs = canonical_pairs(TASK)
    assert len(pairs) == 5
    for pair in pairs:
        grid = copy.deepcopy(pair["input"])
        snapshot = copy.deepcopy(grid)
        assert GEN.self_check(grid) == []
        assert GEN.strict_canonical_like(grid) == []
        assert GEN.rule_mirror(grid) == pair["output"]
        assert grid == snapshot


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize(
    ("axis", "value"),
    [
        ("grid_h", 9),
        ("grid_h", 18),
        ("grid_w", 11),
        ("grid_w", 20),
        ("n_blue", 2),
        ("n_blue", 4),
        ("distractor_area", 1),
        ("distractor_area", 8),
    ],
)
def test_declared_override_boundaries_are_exact_and_observable(axis, value, band):
    grid = GEN.generate(191, 37, difficulty=band, **{axis: value})
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid)[axis] == value


def test_small_canvas_full_boundary_combination_is_feasible_in_every_band():
    requested = {"grid_h": 9, "grid_w": 11, "n_blue": 4, "distractor_area": 8}
    for band in ("easy", "medium", "hard"):
        grid = GEN.generate(3, 7, difficulty=band, **requested)
        assert GEN.self_check(grid) == []
        assert GEN.observe_overrides(grid) == requested


def test_unknown_override_is_rejected_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 2, typo_axis=3)


def test_default_schedule_covers_and_verifies_every_rival_claim_per_band():
    always_refuted = {
        "bounding_box_area_sort", "all_nonzero_objects", "fill_each_bounding_box"
    }
    for band in ("easy", "medium", "hard"):
        witness_hits = {name: 0 for name in GEN.SEMANTIC_WITNESSES}
        rival_refutations = {name: 0 for name in GEN.LESSON_COMPETITORS}
        profiles = set()
        for index in range(40):
            grid = GEN.generate(411 + index, index, difficulty=band)
            official = GEN.rule_mirror(grid)
            assert GEN.strict_canonical_like(grid) == []
            profiles.add(GEN.schedule_profile(411 + index, index, band))
            for name, witness in GEN.SEMANTIC_WITNESSES.items():
                if witness(grid):
                    witness_hits[name] += 1
                    claimed = GEN.WITNESS_RIVALS[name]
                    assert any(GEN.SEMANTIC_RIVALS[r](grid) != official for r in claimed)
            for name, competitor in GEN.LESSON_COMPETITORS.items():
                rival_refutations[name] += competitor(grid) != official
        assert all(value > 0 for value in witness_hits.values())
        assert all(value > 0 for value in rival_refutations.values())
        assert all(rival_refutations[name] == 40 for name in always_refuted)
        assert len(profiles) == len(GEN.SCHEDULE_PROFILES) == 8


def test_three_demo_lessons_refute_every_named_competitor():
    for band in ("easy", "medium", "hard"):
        pairs = []
        for index in range(GEN.EXAMPLES_NEEDED + 1):
            grid = GEN.generate(881, 97 + index, difficulty=band)
            pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
        demos, query = pairs[: GEN.EXAMPLES_NEEDED], pairs[-1]
        assert GEN.lesson_identifiable(demos, query) == []
        for name, competitor in GEN.LESSON_COMPETITORS.items():
            assert not all(competitor(pair["input"]) == pair["output"] for pair in demos), name


def test_self_check_rejects_targeted_structural_impostors_without_mutation():
    valid = GEN.generate(17, 1, difficulty="medium", n_blue=2, distractor_area=4)
    cases = {}

    bad_color = copy.deepcopy(valid)
    bad_color[0][0] = 9
    cases["unexpected_color"] = bad_color

    no_orange = [[0 if value == 7 else value for value in row] for row in valid]
    cases["missing_orange"] = no_orange

    tied_blue = [[1 if value == 7 else value for value in row] for row in valid]
    cases["tied_blue_areas"] = tied_blue

    touching = [[0] * 11 for _ in range(9)]
    touching[1][1] = 1
    touching[4][4] = touching[4][5] = 1
    touching[1][2] = 7
    cases["cardinal_touch"] = touching

    for name, grid in cases.items():
        snapshot = copy.deepcopy(grid)
        assert GEN.self_check(grid), name
        assert grid == snapshot

    assert GEN.self_check([])
    assert GEN.self_check([[0, 1], [0]])
    assert GEN.self_check([[True] * 11 for _ in range(9)])


def test_generation_is_deterministic_fresh_mutation_safe_and_global_rng_pure():
    random.seed(987654321)
    state = random.getstate()
    first = GEN.generate(111, 222, difficulty="hard")
    second = GEN.generate(111, 222, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second and first[0] is not second[0]

    frozen = _frozen(second)
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert _frozen(GEN.generate(111, 222, difficulty="hard")) == frozen

    by_seed = {_frozen(GEN.generate(seed, 17, difficulty="medium")) for seed in range(20)}
    by_index = {_frozen(GEN.generate(17, index, difficulty="medium")) for index in range(20)}
    assert len(by_seed) >= 18
    assert len(by_index) >= 18


def test_python_rule_returns_fresh_rows_and_does_not_mutate_input():
    grid = GEN.generate(92, 1, difficulty="medium")
    snapshot = copy.deepcopy(grid)
    output = GEN.rule_mirror(grid)
    assert grid == snapshot
    output_snapshot = copy.deepcopy(output)
    output[0][0] = 9 if output[0][0] != 9 else 8
    assert GEN.rule_mirror(grid) == output_snapshot
