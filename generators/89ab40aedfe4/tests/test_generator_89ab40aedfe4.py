from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root

TASK_ID = "89ab40aedfe4"
ROOT = find_root(__file__)
GENERATOR_SOURCE = ROOT / "generators" / TASK_ID / "generator.py"
if not GENERATOR_SOURCE.is_file():
    GENERATOR_SOURCE = ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
SPEC = importlib.util.spec_from_file_location(
    "retained_tests_89ab40aedfe4", GENERATOR_SOURCE
)
GEN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)
AUTHORITY = canonical_path(ROOT).parent.parent / "base/solutions/training/85b81ff1__89ab40aedfe4.json"


def load_task_pairs(task_id):
    return canonical_pairs(task_id, root=ROOT, labeled_only=True)


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _pair(seed: int, sample_index: int, difficulty: str) -> dict:
    grid = GEN.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_metadata_and_selected_authority_are_pinned() -> None:
    assert GEN.GENERATOR_ID == TASK_ID
    assert GEN.TASK_ID == TASK_ID
    assert GEN.VERSION == "2.0.0"
    assert GEN.RULE_HASH == "4bc48cdc5789"
    record = json.loads(AUTHORITY.read_text())
    racket = record["racket_target"]
    assert _normalized_hash(racket["target_code"]) == GEN.RULE_HASH
    assert racket["target_code_role"] == "selected_task_rule"
    assert racket["raw_code_role"] == "archival_executable_source"


def test_all_canonical_pairs_are_owned_and_python_mirror_is_exact() -> None:
    pairs = load_task_pairs(TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_four_profile_schedule_is_identifiable_from_every_window() -> None:
    for band in ("easy", "medium", "hard"):
        for start in range(16):
            demos = [_pair(7001, start + offset, band) for offset in range(4)]
            query = _pair(7001, start + 4, band)
            assert GEN.lesson_identifiable(demos, query) == []
            assert {
                GEN.schedule_profile(7001, start + offset, band)
                for offset in range(4)
            } == set(GEN.SCHEDULE_PROFILES)


def test_each_semantic_branch_constructively_refutes_its_rival() -> None:
    for band in ("easy", "medium", "hard"):
        canonical = GEN.generate(8000, 0, difficulty=band)
        topmost = GEN.generate(8000, 1, difficulty=band)
        tie = GEN.generate(8000, 2, difficulty=band)
        marker = GEN.generate(8000, 3, difficulty=band)
        assert GEN.strict_canonical_like(canonical) == []
        assert GEN.SEMANTIC_WITNESSES["population_not_first_active_row"](topmost)
        assert GEN.SEMANTIC_WITNESSES["equal_counts_keep_source_order"](tie)
        assert GEN.SEMANTIC_WITNESSES["marker_only_column_participates"](marker)


def test_public_examples_leave_two_shortcuts_open_but_schedule_kills_them() -> None:
    canonical = load_task_pairs(TASK_ID)
    for name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in canonical), name
    tie = GEN.generate(8100, 2, difficulty="medium")
    marker = GEN.generate(8100, 3, difficulty="medium")
    assert (
        GEN.CANONICAL_SHORTCUTS["reverse_equal_population_ties"](tie)
        != GEN.rule_mirror(tie)
    )
    assert (
        GEN.CANONICAL_SHORTCUTS["keep_marker_only_columns_fixed"](marker)
        != GEN.rule_mirror(marker)
    )


@pytest.mark.parametrize(
    "override",
    (
        {"grid_h": 8},
        {"grid_h": 16},
        {"slot_count": 3},
        {"slot_count": 6},
        {"slot_spacing": 3},
        {"slot_spacing": 5},
        {"fg_color": 1},
        {"fg_color": 9},
    ),
)
def test_declared_override_boundaries_are_exact(override: dict[str, int]) -> None:
    grid = GEN.generate(8200, 1, difficulty="medium", **override)
    key, value = next(iter(override.items()))
    assert GEN.observe_overrides(grid)[key] == value
    assert GEN.self_check(grid) == []


def test_unknown_invalid_overrides_and_difficulty_fail_loudly() -> None:
    with pytest.raises(TypeError, match="unknown override"):
        GEN.generate(1, 0, typo_axis=3)
    with pytest.raises(ValueError):
        GEN.generate(1, 0, grid_h=7)
    with pytest.raises(ValueError):
        GEN.generate(1, 0, fg_color=0)
    with pytest.raises(ValueError, match="unknown difficulty"):
        GEN.generate(1, 0, difficulty="impossible")


def test_self_check_rejects_all_targeted_mutations() -> None:
    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 7
    for name, grid in fixtures:
        assert GEN.self_check(grid), name


def test_generation_is_deterministic_fresh_and_global_rng_neutral() -> None:
    random.seed(123456)
    state = random.getstate()
    first = GEN.generate(8300, 3, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(8300, 3, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 1 if first[0][0] != 1 else 2
    assert second == GEN.generate(8300, 3, difficulty="hard")
