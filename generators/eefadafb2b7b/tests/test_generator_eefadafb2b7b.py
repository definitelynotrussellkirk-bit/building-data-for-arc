from __future__ import annotations

import ast
import hashlib
import importlib
import json
import random
from copy import deepcopy
from pathlib import Path

import pytest

TASK_ID = "eefadafb2b7b"
gen = importlib.import_module(
    f"generators.{TASK_ID}.generator"
)
REPO = Path(__file__).resolve().parents[3]
AUTHORITY = (
    REPO
    / "shared"
    / "data"
    / "base"
    / "solutions"
    / "training"
    / "239be575__eefadafb2b7b.json"
)
CANONICAL_DIMS = {(5, 5), (5, 7), (6, 6), (6, 7), (8, 6)}
CANONICAL = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"


def _canonical_row():
    with CANONICAL.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def canonical_pairs():
    row = _canonical_row()
    return list(row["train"]) + list(row["test"])


def canonical_rule_source():
    return _canonical_row()["program_solution"]


def canonical_rule_hash():
    source = canonical_rule_source()
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def test_solve_harness_can_read_literal_teaching_minimum():
    source = Path(gen.__file__).read_text(encoding="utf-8")
    assignments = [
        statement
        for statement in ast.parse(source).body
        if isinstance(statement, (ast.Assign, ast.AnnAssign))
        and any(
            isinstance(target, ast.Name) and target.id == "EXAMPLES_NEEDED"
            for target in (
                statement.targets
                if isinstance(statement, ast.Assign)
                else [statement.target]
            )
        )
    ]
    assert len(assignments) == 1
    assert ast.literal_eval(assignments[0].value) == 4


def test_binary_classifier_declares_its_complete_output_codomain():
    assert gen.EXPECTED_OUTPUT_CODOMAIN == 2


def test_rule_pin_python_mirror_and_strict_contract_match_canonical_pairs():
    assert gen.RULE_HASH == canonical_rule_hash() == "1d44fc0f4360"
    pairs = canonical_pairs()
    assert len(pairs) == 8
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_declared_canonical_shortcuts_really_fit_every_official_pair():
    pairs = canonical_pairs()
    assert set(gen.CANONICAL_SHORTCUTS) == {
        "four_connected_bridge",
        "bounding_box_bridge",
    }
    for name, shortcut in gen.CANONICAL_SHORTCUTS.items():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in pairs), name


def test_every_four_demo_window_contains_all_decisive_profiles_and_kills_rivals():
    grids = [gen.generate(1701, index, difficulty="medium") for index in range(12)]
    observed = [gen.observe_overrides(grid)["lesson_profile"] for grid in grids]
    assert observed[:8] == list(gen.LESSON_PROFILES) * 2

    expected = set(gen.LESSON_PROFILES)
    for start in range(8):
        window = grids[start : start + gen.EXAMPLES_NEEDED]
        assert {gen.observe_overrides(grid)["lesson_profile"] for grid in window} == expected
        demos = [{"input": grid, "output": gen.rule_mirror(grid)} for grid in window]
        query_grid = grids[start + gen.EXAMPLES_NEEDED]
        query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
        assert gen.lesson_identifiable(demos, query) == []
        for name, rival in gen.LESSON_COMPETITORS.items():
            assert any(rival(demo["input"]) != demo["output"] for demo in demos), name


def test_each_profile_is_a_direct_counterexample_to_its_named_rival():
    for index, profile in enumerate(gen.LESSON_PROFILES):
        grid = gen.generate(
            314159,
            index,
            difficulty="hard",
            lesson_profile=profile,
        )
        assert gen.observe_overrides(grid)["lesson_profile"] == profile
        assert gen.SEMANTIC_WITNESSES[profile](grid)
        expected = gen.rule_mirror(grid)
        for rival_name in gen.WITNESS_RIVALS[profile]:
            assert gen.SEMANTIC_RIVALS[rival_name](grid) != expected


def test_exact_overrides_are_observable_in_every_band_and_unknown_keys_reject():
    for difficulty in ("easy", "medium", "hard"):
        for h in range(5, 9):
            for w in range(5, 8):
                for profile in gen.LESSON_PROFILES:
                    grid = gen.generate(
                        9917,
                        23,
                        difficulty=difficulty,
                        grid_h=h,
                        grid_w=w,
                        lesson_profile=profile,
                    )
                    assert gen.self_check(grid) == []
                    assert gen.observe_overrides(grid) == {
                        "grid_h": h,
                        "grid_w": w,
                        "lesson_profile": profile,
                    }
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 2, unknown_axis="typo")
    with pytest.raises(ValueError):
        gen.generate(1, 2, grid_h=4)
    with pytest.raises(ValueError):
        gen.generate(1, 2, grid_w=8)
    with pytest.raises(ValueError):
        gen.generate(1, 2, lesson_profile="ordinary")


def test_default_draws_anchor_canonical_profiles_and_cover_both_labels():
    labels = set()
    profiles = set()
    for difficulty in ("easy", "medium", "hard"):
        for index in range(80):
            grid = gen.generate(40000 + index, index, difficulty=difficulty)
            assert gen.self_check(grid) == []
            assert gen.strict_canonical_like(grid) == []
            assert (len(grid), len(grid[0])) in CANONICAL_DIMS
            assert {value for row in grid for value in row} == {0, 2, 8}
            labels.add(gen.rule_mirror(grid)[0][0])
            profiles.add(gen.observe_overrides(grid)["lesson_profile"])
    assert labels == {0, 8}
    assert profiles == set(gen.LESSON_PROFILES)


def test_replay_is_deterministic_fresh_and_global_rng_pure():
    random.seed(20261002)
    state = random.getstate()
    first = gen.generate(123, 456, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(123, 456, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second


def test_self_check_rejects_structural_mutations():
    valid = gen.generate(777, 2, difficulty="medium")

    ragged = deepcopy(valid)
    ragged[0] = ragged[0][:-1]

    invalid_color = deepcopy(valid)
    invalid_color[0][0] = 10

    missing_red = deepcopy(valid)
    red = next((r, c) for r, row in enumerate(missing_red) for c, value in enumerate(row) if value == 2)
    missing_red[red[0]][red[1]] = 0

    no_cyan = [[0 if value == 8 else value for value in row] for row in valid]

    for name, grid in {
        "ragged": ragged,
        "invalid_color": invalid_color,
        "missing_red": missing_red,
        "no_cyan": no_cyan,
    }.items():
        assert gen.self_check(grid), name


def test_bound_authority_source_is_exactly_synchronized_to_canonical():
    payload = json.loads(AUTHORITY.read_text(encoding="utf-8"))
    assert payload["racket_target"]["target_code"] == canonical_rule_source()
