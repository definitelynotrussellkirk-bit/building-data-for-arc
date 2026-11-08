"""Focused semantic and regression coverage for task d9d4f0ebb48b."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

from puzzle_generators import base as generator_base
from reviewer_support import canonical_pairs, canonical_path, find_root

TASK_ID = "d9d4f0ebb48b"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
ROOT = find_root(__file__)


def _canonical_rule() -> str:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row["program_solution"]
    raise AssertionError("canonical task missing")


def _normalized_hash(text: str) -> str:
    return hashlib.sha256(" ".join(text.split()).encode()).hexdigest()[:12]


def _lesson(start: int, band: str):
    pairs = []
    for offset in range(GEN.EXAMPLES_NEEDED + 1):
        grid = GEN.generate(10_000 + start, start + offset, difficulty=band)
        pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
    return pairs[:-1], pairs[-1]


def test_rule_hash_and_contract_are_pinned():
    assert GEN.RULE_HASH == _normalized_hash(_canonical_rule()) == "e629f64db51d"
    assert GEN.EXAMPLES_NEEDED == 4
    assert set(GEN.SEMANTIC_WITNESSES) == set(GEN.WITNESS_RIVALS)
    assert set(GEN.SEMANTIC_RIVALS) == set(GEN.LESSON_COMPETITORS)


def test_all_canonical_pairs_are_accepted_and_mirrored_exactly():
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 4
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_sliding_lesson_window_is_identifiable(band):
    for start in range(12):
        demos, query = _lesson(start, band)
        assert {
            GEN.observe_overrides(pair["input"])["scene_profile"]
            for pair in demos
        } == set(GEN.SCENE_PROFILES)
        assert GEN.lesson_identifiable(demos, query) == []
        for name, rival in GEN.LESSON_COMPETITORS.items():
            assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("profile", GEN.SCENE_PROFILES)
@pytest.mark.parametrize("height,width", [(7, 8), (14, 14)])
@pytest.mark.parametrize("plus_count", [1, 2])
def test_full_override_boundaries_are_observable(
    band, profile, height, width, plus_count
):
    requested = {
        "grid_h": height,
        "grid_w": width,
        "plus_count": plus_count,
        "scene_profile": profile,
    }
    grid = GEN.generate(2718, 31, difficulty=band, **requested)
    assert GEN.self_check(grid, meta={"overrides": requested}) == []
    assert GEN.observe_overrides(grid) == requested


def test_unknown_and_invalid_overrides_fail_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, typo_axis=3)
    with pytest.raises(ValueError):
        GEN.generate(1, 0, grid_h=6)
    with pytest.raises(ValueError):
        GEN.generate(1, 0, grid_w=15)
    with pytest.raises(ValueError):
        GEN.generate(1, 0, plus_count=3)
    with pytest.raises(ValueError):
        GEN.generate(1, 0, scene_profile="unknown")


def test_default_keyed_axes_match_the_returned_grid():
    for band in ("easy", "medium", "hard"):
        for index in range(24):
            captured = []
            generator_base.set_ctx_observer(captured.append)
            try:
                grid = GEN.generate(50_000 + index, index, difficulty=band)
            finally:
                generator_base.set_ctx_observer(None)
            assert len(captured) == 1
            assert captured[0].recorded_draws() == GEN.observe_overrides(grid)
            assert set(captured[0].recorded_draws()) == set(GEN.AXES)


def test_determinism_fresh_returns_input_purity_and_global_rng():
    random.seed(123456)
    before = random.getstate()
    first = GEN.generate(55, 7, difficulty="hard")
    middle = random.getstate()
    second = GEN.generate(55, 7, difficulty="hard")
    after = random.getstate()
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == middle == after
    original = copy.deepcopy(second)
    result = GEN.rule_mirror(second)
    assert second == original
    assert result != second
    first[0][0] = 9
    assert second == original


def test_self_check_rejects_targeted_mutations():
    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 6
    for name, grid in fixtures:
        before = copy.deepcopy(grid)
        assert GEN.self_check(grid), name
        assert grid == before


def test_each_witness_fires_and_its_named_rival_disagrees():
    grids = [GEN.generate(77, index, difficulty="medium") for index in range(8)]
    for witness_name, witness in GEN.SEMANTIC_WITNESSES.items():
        firing = [grid for grid in grids if witness(grid)]
        assert firing, witness_name
        for rival_name in GEN.WITNESS_RIVALS[witness_name]:
            rival = GEN.SEMANTIC_RIVALS[rival_name]
            assert all(rival(grid) != GEN.rule_mirror(grid) for grid in firing)


def test_negative_recombination_is_rejected_but_oracle_mirror_executes():
    grid = GEN.generate(91, 2, difficulty="medium")  # multicolor cross
    mutated = copy.deepcopy(grid)
    analysis = GEN._analysis(mutated)
    remainder = sorted(analysis["remainder"])
    # Replace one arm by a color absent from every remaining scene part.
    used = {value for row in mutated for value in row}
    replacement = next(color for color in range(1, 10) if color not in used)
    row, col = remainder[0]
    mutated[row][col] = replacement
    assert GEN.self_check(mutated)
    assert GEN.rule_mirror(mutated)
