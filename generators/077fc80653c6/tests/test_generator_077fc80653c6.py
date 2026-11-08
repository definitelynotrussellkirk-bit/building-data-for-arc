from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

from src.core.canonical_pairs import load_task_pairs

TASK_ID = "077fc80653c6"
ROOT = Path(__file__).resolve().parents[1]
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.077fc80653c6.generator"
)
AUTHORITY = ROOT / (
    "data/base/solutions/banks/545aa94c7c6c/"
    "S13_H3__077fc80653c6.json"
)


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _episode(seed: int, difficulty: str = "medium"):
    grids = [
        GEN.generate(seed, index, difficulty=difficulty)
        for index in range(GEN.EXAMPLES_NEEDED + 1)
    ]
    pairs = [{"input": grid, "output": GEN.rule_mirror(grid)} for grid in grids]
    return pairs[:-1], pairs[-1]


def test_metadata_and_task_local_authority_are_pinned():
    assert GEN.GENERATOR_ID == TASK_ID
    assert GEN.TASK_ID == TASK_ID
    assert GEN.VERSION == "4.0.0"
    assert GEN.RULE_HASH == "5e186b36b85c"
    record = json.loads(AUTHORITY.read_text())
    assert _normalized_hash(record["racket_target"]["target_code"]) == GEN.RULE_HASH


def test_all_canonical_pairs_are_owned_and_python_mirror_is_exact():
    pairs = load_task_pairs(TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize("profile", tuple(GEN.SCENE_PROFILES))
@pytest.mark.parametrize("family", tuple(GEN.TARGET_TRIPLES))
@pytest.mark.parametrize("divider", (6, 7, 8))
def test_declared_override_product_is_exact(profile, family, divider):
    requested = {
        "scene_profile": profile,
        "target_family": family,
        "divider_col": divider,
    }
    grid = GEN.generate(9137, 41, difficulty="hard", **requested)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == requested
    assert GEN.rule_mirror(grid)


def test_unknown_override_and_invalid_difficulty_fail_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, texture="plain")
    with pytest.raises(ValueError, match="unsupported difficulty"):
        GEN.generate(1, 0, difficulty="impossible")


def test_semantic_witnesses_fire_in_every_band():
    for band in ("easy", "medium", "hard"):
        counts = {name: 0 for name in GEN.SEMANTIC_WITNESSES}
        for index in range(120):
            grid = GEN.generate(100_000 + index, 17 + index, difficulty=band)
            assert GEN.strict_canonical_like(grid) == []
            for name, witness in GEN.SEMANTIC_WITNESSES.items():
                counts[name] += bool(witness(grid))
        assert all(count > 0 for count in counts.values()), (band, counts)


def test_lesson_schedule_refutes_documented_shortcuts():
    for band in ("easy", "medium", "hard"):
        for seed in range(20):
            demos, query = _episode(seed, band)
            assert GEN.lesson_identifiable(demos, query) == []
        scheduled = [
            GEN.observe_overrides(GEN.generate(7, index, difficulty=band))["target_family"]
            for index in range(GEN.EXAMPLES_NEEDED)
        ]
        assert scheduled == ["plain_asym", "hole_asym", "canonical_hole"]


def test_self_check_rejects_targeted_semantic_impostors():
    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 5
    for name, grid in fixtures:
        assert GEN.self_check(grid), name


def test_determinism_fresh_returns_and_global_rng_isolation():
    state = random.getstate()
    first = GEN.generate(444, 19, difficulty="medium")
    assert random.getstate() == state
    second = GEN.generate(444, 19, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert GEN.generate(444, 19, difficulty="medium") == second
