from __future__ import annotations

import copy
import json
import random
from pathlib import Path

import importlib
import pytest

gen = importlib.import_module("puzzle_generators.per_puzzle.56f043832ecb.generator")


ROOT = Path(__file__).resolve().parents[1]


def _canonical_inputs():
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == gen.TASK_ID:
            return [pair["input"] for split in ("train", "test") for pair in row[split]]
    raise AssertionError("canonical task row not found")


def _solid_block():
    grid = [[0] * 7 for _ in range(7)]
    for r in range(1, 5):
        for c in range(1, 5):
            grid[r][c] = 4
    return grid


def _closed_frame():
    grid = [[0] * 8 for _ in range(7)]
    for c in range(1, 6):
        grid[1][c] = 3
        grid[5][c] = 3
    for r in range(1, 6):
        grid[r][1] = 3
        grid[r][5] = 3
    return grid


def _spurred_frame():
    """A closed 5x5 perimeter with one outward, connected spur."""
    grid = _closed_frame()
    grid[3][6] = 3
    return grid


def _open_frame():
    grid = _closed_frame()
    grid[3][1] = 0
    return grid


def _pair(grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_canonical_inputs_are_accepted():
    assert len(_canonical_inputs()) == 4
    for grid in _canonical_inputs():
        assert gen.self_check(grid) == []


def test_exact_axes_are_observable_and_overridable():
    grid = gen.generate(
        19,
        23,
        difficulty="hard",
        grid_h=10,
        grid_w=12,
        n_frames=2,
        n_open_decoys=1,
        palette_kind="broad",
    )
    assert (len(grid), len(grid[0])) == (10, 12)
    assert gen.observe_overrides(grid) == {
        "n_frames": 2,
        "n_open_decoys": 1,
        "palette_kind": "broad",
    }
    assert gen.self_check(grid) == []


def test_unknown_override_keys_fail_loudly():
    with pytest.raises(ValueError, match="unknown override axis"):
        gen.generate(19, 23, difficulty="hard", n_framez=2)


def test_three_profile_schedule_is_explicit_and_cyclic():
    expected = {"canonical_pair", "open_decoy", "irregular_broad"}
    assert set(gen.SCHEDULE_PROFILES) == expected
    for start in range(9):
        assert {
            gen.schedule_profile(17, index, difficulty="hard")
            for index in range(start, start + gen.EXAMPLES_NEEDED)
        } == expected


def test_hard_band_schedule_retains_strict_canonical_support():
    for sample_index in range(0, 30, gen.EXAMPLES_NEEDED):
        grid = gen.generate(881, sample_index, difficulty="hard")
        assert gen.schedule_profile(881, sample_index, "hard") == "canonical_pair"
        assert gen.strict_canonical_like(grid) == []


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(918273)
    before = random.getstate()
    first = gen.generate(31, 7, difficulty="medium")
    middle = random.getstate()
    second = gen.generate(31, 7, difficulty="medium")
    after = random.getstate()
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == middle == after
    first[0][0] = 9
    assert second[0][0] != 9


def test_self_check_rejects_targeted_impostors():
    # 1. No hollow target: a solid rectangle is not a frame.
    assert gen.self_check(_solid_block())

    # 2. Only an open frame: there is no positive fill witness.
    open_only = _open_frame()
    assert gen.self_check(open_only)

    # 3. Interior contamination: the target is not a hollow perimeter.
    contaminated = _closed_frame()
    contaminated[3][3] = 3
    assert gen.self_check(contaminated)

    # 4. Two-cell protrusion is outside the exact one-spur grammar.
    spur = _closed_frame()
    spur[3][6] = 3
    spur[3][7] = 3
    assert gen.self_check(spur)

    # 5. Two otherwise valid frames violate the one-cell moat.
    touching = [[0] * 9 for _ in range(7)]
    for color, c0 in ((2, 0), (6, 4)):
        for c in range(c0, c0 + 4):
            touching[1][c] = color
            touching[4][c] = color
        for r in range(1, 5):
            touching[r][c0] = color
            touching[r][c0 + 3] = color
    assert gen.self_check(touching)


def test_exact_spurred_frame_family_is_accepted_and_filled_topologically():
    grid = _spurred_frame()
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == {
        "n_frames": 1,
        "n_open_decoys": 0,
        "palette_kind": "canonical",
    }

    output = gen.rule_mirror(grid)
    for row in range(2, 5):
        for col in range(2, 5):
            assert output[row][col] == 3
    # The spur expands the component bbox; bbox filling would wrongly paint
    # these exterior cells.  The topological rule leaves them alone.
    assert output[2][6] == 0
    assert output[4][6] == 0


def test_open_frame_has_no_fill_target():
    grid = _open_frame()
    # It is invalid alone because every lesson needs a positive target, but
    # the local rule mirror must still preserve the leaking interior.
    assert gen.rule_mirror(grid) == grid


def test_irregular_profile_materializes_a_spurred_positive():
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(2, 24, gen.EXAMPLES_NEEDED):
            grid = gen.generate(31337, sample_index, difficulty=difficulty)
            scene = gen._lawful_scene(grid)
            assert scene is not None
            assert any(kind == "closed_irregular" for kind, _, _ in scene)
            assert gen.observe_overrides(grid)["palette_kind"] == "broad"


def test_default_draws_cover_both_semantic_branches():
    seen = set()
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(80):
            grid = gen.generate(seed, seed * 13 + 5, difficulty=difficulty)
            observed = gen.observe_overrides(grid)
            seen.add((observed["n_frames"], observed["n_open_decoys"]))
            assert gen.self_check(copy.deepcopy(grid)) == []
    assert (1, 0) in seen
    assert (2, 0) in seen
    assert any(open_count == 1 for _, open_count in seen)


def test_declared_witnesses_really_refute_their_named_rivals():
    witnessed = set()
    for sample_index in range(90):
        grid = gen.generate(20261002, sample_index, difficulty="hard")
        truth = gen.rule_mirror(grid)
        for witness_name, witness in gen.SEMANTIC_WITNESSES.items():
            if not witness(grid):
                continue
            witnessed.add(witness_name)
            for rival_name in gen.WITNESS_RIVALS[witness_name]:
                assert gen.SEMANTIC_RIVALS[rival_name](grid) != truth
    assert witnessed == set(gen.SEMANTIC_WITNESSES)


def test_declared_canonical_shortcuts_fit_every_canonical_pair():
    canonical_pairs = []
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == gen.TASK_ID:
            canonical_pairs = [
                pair for split in ("train", "test") for pair in row[split]
            ]
            break
    assert canonical_pairs
    for name, shortcut in gen.CANONICAL_SHORTCUTS.items():
        for pair in canonical_pairs:
            assert shortcut(pair["input"]) == pair["output"], name


def test_every_three_demo_window_eliminates_all_lesson_competitors():
    for start in range(9):
        demos = [
            _pair(gen.generate(6001, index, difficulty="hard"))
            for index in range(start, start + gen.EXAMPLES_NEEDED)
        ]
        query = _pair(
            gen.generate(6001, start + gen.EXAMPLES_NEEDED, difficulty="hard")
        )
        for name, competitor in gen.LESSON_COMPETITORS.items():
            assert any(
                competitor(demo["input"]) != demo["output"] for demo in demos
            ), name
        assert gen.lesson_identifiable(demos, query) == []
