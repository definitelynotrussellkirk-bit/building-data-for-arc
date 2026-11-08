from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).with_name("generator.py")
SPEC = importlib.util.spec_from_file_location("generator_735ba14c7162", MODULE_PATH)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)
ROOT = Path(__file__).resolve().parents[3]
CANONICAL = ROOT / "data/canonical/puzzles.jsonl"


def _canonical_row():
    for line in CANONICAL.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == GEN.TASK_ID:
            return row
    raise AssertionError("canonical task row missing")


def test_rule_hash_and_all_canonical_pairs_are_pinned():
    row = _canonical_row()
    normalized = " ".join(row["program_solution"].split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == GEN.RULE_HASH
    for pair in [*row["train"], *row["test"]]:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_generation_is_deterministic_fresh_and_rng_pure():
    random.seed(99117)
    state = random.getstate()
    first = GEN.generate(117, 9, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(117, 9, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert second == GEN.generate(117, 9, difficulty="hard")


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_ordinary_draw_teaches_the_declared_rule(difficulty):
    for index in range(30):
        grid = GEN.generate(10_000 + index, index, difficulty=difficulty)
        assert GEN.self_check(grid) == []
        assert GEN.strict_canonical_like(grid) == []
        assert all(predicate(grid) for predicate in GEN.SEMANTIC_WITNESSES.values())
        expected = GEN.rule_mirror(grid)
        for rival in GEN.SEMANTIC_RIVALS.values():
            assert rival(grid) != expected


def test_exact_axes_and_unknown_override_rejection():
    for overrides in (
        {"grid_h": 4, "grid_w": 7, "active_rows": 3, "palette_size": 4},
        {"grid_h": 8, "grid_w": 11, "active_rows": 8, "palette_size": 9},
        {"grid_h": 5, "grid_w": 9, "active_rows": 4, "palette_size": 9},
    ):
        grid = GEN.generate(17, 2, difficulty="medium", **overrides)
        assert GEN.observe_overrides(grid) == overrides
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(17, 2, palette_kind="warm")
    assert GEN.observe_overrides(GEN.generate(17, 2, active_rows=8))["active_rows"] == 8
    with pytest.raises(ValueError, match="grid_h.*active_rows"):
        GEN.generate(17, 2, grid_h=4, active_rows=8)


def test_declared_mutation_impostors_are_rejected():
    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert GEN.self_check(copy.deepcopy(grid)), name


def test_lessons_refute_named_competitors():
    pairs = []
    for sample_index in range(4):
        grid = GEN.generate(42, sample_index, difficulty="medium")
        pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
    assert GEN.lesson_identifiable(pairs[:3], pairs[3]) == []
