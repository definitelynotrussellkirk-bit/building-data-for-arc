from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root

TASK_ID = "e410357cf67e"
ROOT = find_root(__file__)
GENERATOR_PATH = ROOT / "generators" / TASK_ID / "generator.py"
if not GENERATOR_PATH.exists():
    GENERATOR_PATH = (
        ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
    )
SPEC = importlib.util.spec_from_file_location(f"generator_{TASK_ID}_under_test", GENERATOR_PATH)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)
PAIRS = canonical_pairs(TASK_ID, root=ROOT)

EXPECTED_PROFILES = (
    "corner_complex_wall",
    "complex_boundary",
    "corner_single_wall",
    "single_boundary",
    "straight_wall_decoys",
)
CANONICAL_PROFILES = {(7, 10, 4), (7, 11, 4), (8, 9, 5), (8, 10, 3)}


def _canonical_rule_source() -> str:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row["program_solution"]
    raise AssertionError("canonical rule source missing")


def _label(grid):
    return {"input": copy.deepcopy(grid), "output": GEN.rule_mirror(grid)}


def _lesson(seed: int, start: int, difficulty: str):
    pairs = [
        _label(GEN.generate(seed, start + offset, difficulty=difficulty))
        for offset in range(GEN.EXAMPLES_NEEDED + 1)
    ]
    return pairs[:-1], pairs[-1]


def _palette_size(grid) -> int:
    return len({value for row in grid for value in row})


def test_metadata_rule_hash_and_axes_are_truthful():
    expected_hash = hashlib.sha256(
        " ".join(_canonical_rule_source().split()).encode()
    ).hexdigest()[:12]
    assert GEN.RULE_HASH == expected_hash == "ca02c94ead8c"
    assert GEN.VERSION == "4.0.0"
    assert GEN.EXAMPLES_NEEDED == 4
    assert GEN.LESSON_SCHEDULE_PERIOD == 5
    assert tuple(GEN.SCHEDULE_PROFILES) == EXPECTED_PROFILES
    assert set(GEN.AXES) == {"grid_h", "grid_w", "profile"}
    assert GEN.AXES["profile"]["valid"] == "|".join(EXPECTED_PROFILES)


def test_all_canonical_inputs_are_owned_and_python_mirror_matches_labels():
    assert len(PAIRS) == 4
    for pair in PAIRS:
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


def test_ignore_walls_is_a_real_canonical_shortcut():
    assert set(GEN.CANONICAL_SHORTCUTS) == {"ignore_walls"}
    shortcut = GEN.CANONICAL_SHORTCUTS["ignore_walls"]
    assert all(shortcut(pair["input"]) == pair["output"] for pair in PAIRS)


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", EXPECTED_PROFILES)
@pytest.mark.parametrize("grid_h,grid_w", [(7, 9), (16, 16)])
def test_exact_profile_and_dimension_overrides_are_observable(
    difficulty, profile, grid_h, grid_w
):
    grid = GEN.generate(
        4200 + grid_h,
        170 + grid_w,
        difficulty=difficulty,
        grid_h=grid_h,
        grid_w=grid_w,
        profile=profile,
    )
    expected = {"grid_h": grid_h, "grid_w": grid_w, "profile": profile}
    assert GEN.self_check(grid) == []
    assert GEN.strict_canonical_like(grid) == []
    assert GEN.observe_overrides(grid) == expected
    assert GEN.rule_mirror(grid) != grid


@pytest.mark.parametrize(
    "overrides",
    [
        {"unknown_axis": 1},
        {"grid_h": 6},
        {"grid_h": 17},
        {"grid_w": 8},
        {"grid_w": 17},
        {"grid_h": True},
        {"grid_w": 10.5},
        {"profile": "random_scatter"},
    ],
)
def test_invalid_and_unknown_overrides_fail_loudly(overrides):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **overrides)


def test_unknown_difficulty_fails_loudly():
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(0, 0, difficulty="extreme")


def test_default_schedule_covers_each_profile_once_per_five_draws():
    for difficulty in (None, "easy", "medium", "hard"):
        for start in range(10):
            seen = [
                GEN.observe_overrides(
                    GEN.generate(731, start + offset, difficulty=difficulty)
                )["profile"]
                for offset in range(5)
            ]
            assert set(seen) == set(EXPECTED_PROFILES)
        for sample_index, profile in enumerate(EXPECTED_PROFILES):
            assert GEN.schedule_profile(731, sample_index, difficulty=difficulty) == profile


def test_every_cyclic_lesson_and_every_query_rotation_refutes_declared_rivals():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(10):
            demos, query = _lesson(8100 + start, start, difficulty)
            assert GEN.lesson_identifiable(demos, query) == []
            all_pairs = demos + [query]
            for query_index, held_out in enumerate(all_pairs):
                rotated = [
                    pair for index, pair in enumerate(all_pairs) if index != query_index
                ]
                assert GEN.lesson_identifiable(rotated, held_out) == []
                for name, rival in GEN.LESSON_COMPETITORS.items():
                    assert any(
                        rival(pair["input"]) != pair["output"] for pair in rotated
                    ), (difficulty, start, query_index, name)


def test_each_semantic_witness_fires_and_is_a_real_counterexample():
    hits = {name: 0 for name in GEN.SEMANTIC_WITNESSES}
    for difficulty in ("easy", "medium", "hard"):
        for index in range(20):
            grid = GEN.generate(19_000 + index, index, difficulty=difficulty)
            truth = GEN.rule_mirror(grid)
            for witness_name, witness in GEN.SEMANTIC_WITNESSES.items():
                if witness(grid):
                    hits[witness_name] += 1
                    assert any(
                        GEN.SEMANTIC_RIVALS[rival](grid) != truth
                        for rival in GEN.WITNESS_RIVALS[witness_name]
                    )
    assert all(count > 0 for count in hits.values()), hits


def test_default_distribution_hits_canonical_profiles_in_every_band():
    for difficulty in ("easy", "medium", "hard"):
        profiles = {
            (len(grid), len(grid[0]), _palette_size(grid))
            for index in range(20)
            for grid in [GEN.generate(28_000 + index, index, difficulty=difficulty)]
        }
        assert profiles & CANONICAL_PROFILES, (difficulty, profiles)


def test_default_distribution_includes_corner_straight_and_reflected_cases():
    for difficulty in ("easy", "medium", "hard"):
        observed = [
            GEN._analysis(GEN.generate(37_000 + index, index, difficulty=difficulty))
            for index in range(25)
        ]
        assert any(item["corner_source"] for item in observed)
        assert any(len(item["hit_mirrors"]) == 0 for item in observed)
        assert any(len(item["hit_mirrors"]) == 2 for item in observed)
        assert {item["termination"] for item in observed} == {"wall", "boundary"}
        assert all(not item["errors"] for item in observed)


def test_corner_priority_is_top_or_bottom_before_left_or_right():
    grid = [[0] * 7 for _ in range(7)]
    grid[0][6] = 2
    grid[2][1] = 4  # lawful off-route mirror keeps the declared domain nondegenerate
    expected = copy.deepcopy(grid)
    for row in range(1, 7):
        expected[row][6] = 7
    assert GEN.rule_mirror(grid) == expected
    assert GEN.SEMANTIC_RIVALS["horizontal_corner_priority"](grid) != expected


def test_active_wall_stops_before_cells_that_ignore_walls_would_paint():
    grid = GEN.generate(
        404,
        5,
        profile="straight_wall_decoys",
        grid_h=9,
        grid_w=11,
    )
    truth = GEN.rule_mirror(grid)
    rival = GEN.SEMANTIC_RIVALS["ignore_walls"](grid)
    assert truth != rival
    assert GEN.SEMANTIC_WITNESSES["active_wall"](grid)


def test_self_check_rejects_structural_palette_and_answer_leak_mutations():
    base = GEN.generate(91, 2, profile="corner_single_wall", grid_h=8, grid_w=10)
    assert GEN.self_check(base) == []

    ragged = copy.deepcopy(base)
    ragged[0].pop()

    no_source = [[0 if value == 2 else value for value in row] for row in base]

    duplicate_source = copy.deepcopy(base)
    duplicate_source[-1][-1] = 2

    interior_source = copy.deepcopy(base)
    for r, row in enumerate(interior_source):
        for c, value in enumerate(row):
            if value == 2:
                interior_source[r][c] = 0
    interior_source[3][3] = 2

    answer_leak = copy.deepcopy(base)
    leak_cell = next(
        (r, c)
        for r, row in enumerate(answer_leak)
        for c, value in enumerate(row)
        if value == 0
    )
    answer_leak[leak_cell[0]][leak_cell[1]] = 7

    boolean_cell = copy.deepcopy(base)
    boolean_cell[0][0] = True

    for mutation in (
        ragged,
        no_source,
        duplicate_source,
        interior_source,
        answer_leak,
        boolean_cell,
    ):
        assert GEN.self_check(mutation), mutation


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(20261008)
    before = random.getstate()
    first = GEN.generate(777, 888, difficulty="hard")
    middle = random.getstate()
    second = GEN.generate(777, 888, difficulty="hard")
    after = random.getstate()
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second, strict=True))
    assert before == middle == after
    first[0][0] = 9
    assert GEN.generate(777, 888, difficulty="hard") == second


def test_retained_counterexamples_are_replayable_and_hash_bound():
    retained = (
        GENERATOR_PATH.parent
        / "counterexamples"
        / "review-9a3cfcbadd2ba12e-v0001"
        / "counterexamples.json"
    )
    payload = json.loads(retained.read_text(encoding="utf-8"))
    assert payload["task_id"] == TASK_ID
    assert payload["rule_hash"] == GEN.RULE_HASH
    assert payload["generator_sha256"] == hashlib.sha256(
        GENERATOR_PATH.read_bytes()
    ).hexdigest()

    for case in payload["canonical_support"]:
        assert GEN.self_check(case["input"]) == []
        assert GEN.rule_mirror(case["input"]) == case["output"]

    witness = payload["active_wall_witness"]
    grid = GEN.generate(
        witness["seed"],
        witness["sample_index"],
        difficulty=witness["difficulty"],
        **witness["overrides"],
    )
    assert grid == witness["input"]
    assert GEN.rule_mirror(grid) == witness["canonical_output"]
    assert GEN.SEMANTIC_RIVALS["ignore_walls"](grid) == witness["ignore_walls_output"]
    assert witness["canonical_output"] != witness["ignore_walls_output"]
