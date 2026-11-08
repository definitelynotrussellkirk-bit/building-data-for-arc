from __future__ import annotations

import copy
import hashlib
import importlib
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest


_HERE = Path(__file__).resolve()
_PORTABLE_ROOT = _HERE.parents[1]
if (_PORTABLE_ROOT / "data/canonical/puzzles.jsonl").is_file():
    ROOT = _PORTABLE_ROOT
    sys.path.insert(0, str(ROOT))
    GEN = importlib.import_module(
        "puzzle_generators.per_puzzle.306adf8e4c54.generator"
    )
else:
    REPO_ROOT = _HERE.parents[3]
    ROOT = REPO_ROOT / "shared"
    sys.path.insert(0, str(ROOT / "runtime"))
    sys.path.insert(0, str(ROOT / "tools"))
    spec = importlib.util.spec_from_file_location(
        "generator_306adf8e4c54_review",
        REPO_ROOT / "generators/306adf8e4c54/generator.py",
    )
    assert spec is not None and spec.loader is not None
    GEN = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(GEN)


def _canonical_row() -> dict:
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        rows = [
            json.loads(line)
            for line in handle
            if '"task_id": "306adf8e4c54"' in line
        ]
    assert len(rows) == 1
    return rows[0]


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _pair(grid: list[list[int]]) -> dict:
    return {"input": copy.deepcopy(grid), "output": GEN.rule_mirror(grid)}


def test_metadata_pins_authority_and_canonical_examples() -> None:
    canonical = _canonical_row()
    assert GEN.RULE_HASH == _normalized_hash(canonical["program_solution"])
    assert GEN.EXAMPLES_NEEDED == 4
    assert GEN.MIN_STRICT_FRAC >= 0.20

    pairs = [*canonical["train"], *canonical["test"]]
    assert len(pairs) == 3
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_scene_profile_overrides_are_exact_and_unknown_keys_reject() -> None:
    for difficulty in ("easy", "medium", "hard"):
        for profile in GEN.SCENE_PROFILES:
            grid = GEN.generate(
                314159,
                17,
                difficulty=difficulty,
                scene_profile=profile,
            )
            assert GEN.self_check(grid) == []
            assert GEN.observe_overrides(grid) == {"scene_profile": profile}

    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, typo_axis="canonical_anchor")
    with pytest.raises(ValueError):
        GEN.generate(1, 0, scene_profile="not_a_profile")


def test_every_sliding_four_example_window_refutes_all_named_competitors() -> None:
    for difficulty in ("easy", "medium", "hard"):
        for start in range(16):
            grids = [
                GEN.generate(8000 + start, start + offset, difficulty=difficulty)
                for offset in range(5)
            ]
            demos = [_pair(grid) for grid in grids[:4]]
            query = _pair(grids[4])
            assert GEN.lesson_identifiable(demos, query) == []
            for name, competitor in GEN.LESSON_COMPETITORS.items():
                assert any(
                    competitor(demo["input"]) != demo["output"]
                    for demo in demos
                ), name


def test_named_witnesses_are_causal_in_every_band() -> None:
    for difficulty in ("easy", "medium", "hard"):
        grids = [
            GEN.generate(12000 + index, index, difficulty=difficulty)
            for index in range(32)
        ]
        for witness_name, rival_names in GEN.WITNESS_RIVALS.items():
            witness = GEN.SEMANTIC_WITNESSES[witness_name]
            firing = [grid for grid in grids if witness(grid)]
            assert firing, (difficulty, witness_name)
            for grid in firing:
                official = GEN.rule_mirror(grid)
                assert any(
                    GEN.SEMANTIC_RIVALS[rival](grid) != official
                    for rival in rival_names
                ), (difficulty, witness_name)


def test_controls_profile_preserves_blockers_and_nonfour_sandwiches() -> None:
    grid = GEN.generate(2026, 2, scene_profile="controls_9x9")
    facts = GEN._analyze(grid)
    assert facts["errors"] == []
    assert facts["blocked_midpoints"]
    assert facts["nonfour_sandwiches"]
    assert facts["long_distance_controls"]

    output = GEN.rule_mirror(grid)
    for row, col in facts["blocked_midpoints"]:
        assert output[row][col] == grid[row][col] != 0
    for row, col in facts["nonfour_sandwiches"]:
        assert output[row][col] == 0


def test_noncascade_profile_exposes_single_pass_semantics() -> None:
    grid = GEN.generate(2027, 3, scene_profile="noncascade_8x9")
    official = GEN.rule_mirror(grid)
    iterative = GEN.SEMANTIC_RIVALS["iterative_closure"](grid)
    assert official != iterative
    assert GEN.SEMANTIC_WITNESSES["single_pass_not_iterative"](grid)

    first_delta = {
        (r, c)
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if grid[r][c] != official[r][c]
    }
    later_delta = {
        (r, c)
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if official[r][c] != iterative[r][c]
    }
    assert first_delta
    assert later_delta
    assert first_delta.isdisjoint(later_delta)


def test_generation_is_deterministic_fresh_and_global_rng_pure() -> None:
    random.seed(8675309)
    before = random.getstate()
    first = GEN.generate(77, 19, difficulty="hard")
    middle = GEN.generate(78, 20, difficulty="easy")
    second = GEN.generate(77, 19, difficulty="hard")
    after = random.getstate()

    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    assert middle != first
    assert before == after

    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second
    assert second == GEN.generate(77, 19, difficulty="hard")


def test_mutation_fixtures_are_rejected() -> None:
    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 5
    for name, grid in fixtures:
        assert GEN.self_check(grid), name


def test_controls_profile_never_confounds_the_nonfour_color_witness() -> None:
    """Regression: seed 115 once hid 5,0,5 inside a simultaneous 4,0,4 cross."""
    grid = GEN.generate(115, 2, difficulty="medium")
    official = GEN.rule_mirror(grid)
    any_equal_nonzero = GEN.SEMANTIC_RIVALS["any_equal_nonzero_color"](grid)
    assert any_equal_nonzero != official
    assert GEN.SEMANTIC_WITNESSES["yellow_is_color_specific"](grid)
