"""Focused regression tests for the Sprout Plus Seeds generator."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import random
import subprocess
import sys
from itertools import product

import pytest

from puzzle_generators.per_puzzle.cc74d7392ecd import generator as gen
from reviewer_support import canonical_pairs, canonical_path, find_root

ROOT = find_root(__file__)


def _canonical_program() -> str:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row["program_solution"]
    raise AssertionError("canonical row missing")


def _pair(seed: int, sample_index: int, difficulty: str) -> dict:
    grid = gen.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def _is_corner(r: int, c: int, height: int, width: int) -> bool:
    return r in (0, height - 1) and c in (0, width - 1)


def _boundary_seed_kinds(grid) -> tuple[int, int, int]:
    height, width = len(grid), len(grid[0])
    corner = noncorner = interior = 0
    for r, c, _ in gen._seed_cells(grid):
        if _is_corner(r, c, height, width):
            corner += 1
        elif gen._is_edge(r, c, height, width):
            noncorner += 1
        else:
            interior += 1
    return corner, noncorner, interior


def _ignore_corner_seeds(grid):
    height, width = len(grid), len(grid[0])
    seeds = [
        seed
        for seed in gen._seed_cells(grid)
        if not _is_corner(seed[0], seed[1], height, width)
    ]
    return gen._apply_seed_rule(
        grid,
        lambda sr, sc, r, c: abs(sr - r) + abs(sc - c) <= 1,
        seeds=seeds,
    )


def _ignore_noncorner_boundary_seeds(grid):
    height, width = len(grid), len(grid[0])
    seeds = [
        seed
        for seed in gen._seed_cells(grid)
        if not (
            gen._is_edge(seed[0], seed[1], height, width)
            and not _is_corner(seed[0], seed[1], height, width)
        )
    ]
    return gen._apply_seed_rule(
        grid,
        lambda sr, sc, r, c: abs(sr - r) + abs(sc - c) <= 1,
        seeds=seeds,
    )


def test_rule_hash_and_all_canonical_pairs() -> None:
    expected_hash = hashlib.sha256(
        " ".join(_canonical_program().split()).encode()
    ).hexdigest()[:12]
    assert gen.RULE_HASH == expected_hash

    pairs = canonical_pairs(gen.TASK_ID, root=ROOT)
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_all_exact_axis_boundaries_are_realized() -> None:
    index = 0
    for difficulty, values in product(
        ("easy", "medium", "hard"),
        product((6, 10), (6, 10), (2, 3), (0, 1, 2)),
    ):
        grid_h, grid_w, n_seeds, edge_seed_count = values
        grid = gen.generate(
            1000 + index,
            2000 + index,
            difficulty=difficulty,
            grid_h=grid_h,
            grid_w=grid_w,
            n_seeds=n_seeds,
            edge_seed_count=edge_seed_count,
        )
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == {
            "grid_h": grid_h,
            "grid_w": grid_w,
            "n_seeds": n_seeds,
            "edge_seed_count": edge_seed_count,
        }
        index += 1


def test_two_boundary_override_realizes_corner_and_noncorner_clipping() -> None:
    grid = gen.generate(
        1717,
        3,
        difficulty="hard",
        grid_h=6,
        grid_w=6,
        n_seeds=3,
        edge_seed_count=2,
    )
    assert _boundary_seed_kinds(grid) == (1, 1, 1)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
@pytest.mark.parametrize("sample_index", [1, 3])
def test_scheduled_clipped_profiles_cover_both_boundary_classes(
    difficulty, sample_index
) -> None:
    grid = gen.generate(8181, sample_index, difficulty=difficulty)
    assert _boundary_seed_kinds(grid) == (1, 1, 1)


def test_unknown_axes_and_invalid_values_reject_loudly() -> None:
    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(1, 1, typo_axis=3)
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 1, difficulty="extreme")
    with pytest.raises(ValueError, match="outside"):
        gen.generate(1, 1, grid_h=5)
    with pytest.raises(ValueError, match="outside"):
        gen.generate(1, 1, n_seeds=4)


@pytest.mark.parametrize(
    ("axis", "value"),
    [
        ("grid_h", 7.75),
        ("grid_w", "7"),
        ("n_seeds", 2.75),
        ("edge_seed_count", True),
        ("edge_seed_count", 1.75),
    ],
)
def test_integer_axes_reject_coercible_non_integer_overrides(axis, value) -> None:
    with pytest.raises(TypeError, match="override must be an integer"):
        gen.generate(17, 3, difficulty="hard", **{axis: value})


@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1"])
def test_seed_requires_a_literal_integer(seed) -> None:
    with pytest.raises(TypeError, match="seed must be an integer"):
        gen.generate(seed, 0, difficulty="easy")


@pytest.mark.parametrize("sample_index", [True, False, 1.0, 1.75, "1"])
def test_sample_index_requires_a_literal_integer(sample_index) -> None:
    with pytest.raises(TypeError, match="sample_index must be an integer"):
        gen.generate(991, sample_index, difficulty="easy")


def test_sample_index_must_be_nonnegative() -> None:
    with pytest.raises(ValueError, match="sample_index must be nonnegative"):
        gen.generate(991, -1, difficulty="easy")


def test_determinism_fresh_returns_and_global_rng_state() -> None:
    random.seed(740739)
    state_before = random.getstate()
    first = gen.generate(17, 9, difficulty="medium")
    state_after = random.getstate()
    second = gen.generate(17, 9, difficulty="medium")

    assert state_before == state_after
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    first[0][0] = 9
    assert first != second
    assert second != gen.generate(18, 9, difficulty="medium")
    assert second != gen.generate(17, 10, difficulty="medium")


def test_generation_is_stable_across_python_hash_seeds() -> None:
    code = (
        "import json; "
        "from puzzle_generators.per_puzzle.cc74d7392ecd import generator as g; "
        "print(json.dumps(g.generate(17, 1, difficulty='medium')))"
    )
    outputs = []
    for hash_seed in ("1", "2", "101"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed)
        completed = subprocess.run(
            [sys.executable, "-c", code],
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )
        outputs.append(completed.stdout)
    assert len(set(outputs)) == 1


def test_every_three_demo_schedule_window_is_identifiable() -> None:
    for difficulty in ("easy", "medium", "hard"):
        for start in range(len(gen.SCHEDULE_PROFILES)):
            demos = [
                _pair(5000 + start, start + offset, difficulty)
                for offset in range(gen.EXAMPLES_NEEDED)
            ]
            query = _pair(
                5000 + start,
                start + gen.EXAMPLES_NEEDED,
                difficulty,
            )
            assert gen.lesson_identifiable(demos, query) == []


def test_boundary_shortcuts_fit_canonical_but_die_in_every_lesson_window() -> None:
    pairs = canonical_pairs(gen.TASK_ID, root=ROOT)
    independent_rivals = {
        "ignore_corner_seeds": _ignore_corner_seeds,
        "ignore_noncorner_boundary_seeds": _ignore_noncorner_boundary_seeds,
    }
    assert set(independent_rivals) <= set(gen.CANONICAL_SHORTCUTS)
    for name, rival in independent_rivals.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name
        for difficulty in ("easy", "medium", "hard"):
            for start in range(len(gen.SCHEDULE_PROFILES)):
                demos = [
                    gen.generate(9300 + start, start + offset, difficulty=difficulty)
                    for offset in range(gen.EXAMPLES_NEEDED)
                ]
                assert any(rival(grid) != gen.rule_mirror(grid) for grid in demos), (
                    name,
                    difficulty,
                    start,
                )


def test_saved_boundary_shortcut_counterexample_is_reproducible() -> None:
    path = (
        ROOT
        / "generators"
        / gen.TASK_ID
        / "counterexamples"
        / "boundary_shortcut_counterexample.json"
    )
    record = json.loads(path.read_text(encoding="utf-8"))
    generation = record["generation"]
    grid = gen.generate(
        generation["seed"],
        generation["sample_index"],
        difficulty=generation["difficulty"],
        **generation["overrides"],
    )
    assert grid == record["input"]
    assert gen.self_check(grid) == []
    assert gen.rule_mirror(grid) == record["intended_racket_output"]
    rival = gen.CANONICAL_SHORTCUTS[record["rival_name"]]
    assert rival(grid) == record["rival_output"]
    assert record["rival_output"] != record["intended_racket_output"]


def test_missing_edge_witness_leaves_boundary_shortcut_alive() -> None:
    # Sample indices 0, 2, and 4 are all interior schedule profiles.
    demos = [_pair(7001, sample_index, "medium") for sample_index in (0, 2, 4)]
    query = _pair(7001, 1, "medium")
    findings = gen.lesson_identifiable(demos, query)
    assert any("ignore_boundary_seeds" in finding for finding in findings)


def test_named_rivals_are_killed_by_their_witnesses() -> None:
    interior = gen.generate(8100, 0, difficulty="easy")
    clipped = gen.generate(8100, 1, difficulty="easy")
    assert gen.SEMANTIC_WITNESSES[
        "cardinal_plus_not_square_x_or_line"
    ](interior)
    assert gen.SEMANTIC_WITNESSES["every_seed_expands"](interior)
    assert gen.SEMANTIC_WITNESSES[
        "each_plus_keeps_its_seed_color"
    ](interior)
    assert gen.SEMANTIC_WITNESSES[
        "boundary_seed_is_clipped_not_ignored"
    ](clipped)
    assert gen.SEMANTIC_WITNESSES[
        "corner_seed_is_clipped_not_ignored"
    ](clipped)
    assert gen.SEMANTIC_WITNESSES[
        "noncorner_edge_seed_is_clipped_not_ignored"
    ](clipped)


def test_targeted_mutation_fixtures_are_rejected() -> None:
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert gen.self_check(grid), name


def test_absent_color_negative_recombination_is_distribution_invalid() -> None:
    grid = gen.generate(9901, 0, difficulty="easy")
    used = {value for row in grid for value in row}
    replacement = next(color for color in range(1, 10) if color not in used)
    recombined = copy.deepcopy(grid)
    seed_r, seed_c, _ = gen._seed_cells(recombined)[0]
    candidate_neighbors = [
        (seed_r - 1, seed_c),
        (seed_r + 1, seed_c),
        (seed_r, seed_c - 1),
        (seed_r, seed_c + 1),
    ]
    r, c = next(
        (r, c)
        for r, c in candidate_neighbors
        if 0 <= r < len(recombined)
        and 0 <= c < len(recombined[0])
        and recombined[r][c] == 0
    )
    recombined[r][c] = replacement

    assert gen.self_check(recombined)
    # Oracle executability is separate from lesson-distribution validity.
    output = gen.rule_mirror(recombined)
    assert len(output) == len(recombined)
    assert len(output[0]) == len(recombined[0])


def test_rule_changes_every_ordinary_input() -> None:
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(20):
            grid = gen.generate(12000 + sample_index, sample_index, difficulty=difficulty)
            assert gen.rule_mirror(grid) != grid
