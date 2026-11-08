from __future__ import annotations

import copy
import hashlib
import importlib.util
import random
from pathlib import Path

import pytest

from scripts.canonical_profile_gate import canonical_pairs

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "puzzle_generators/per_puzzle/69e5340ad7b0/generator.py"
)
SPEC = importlib.util.spec_from_file_location("generator_69e5340ad7b0", MODULE_PATH)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)
ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "data/canonical/puzzles.jsonl"


def _canonical_rule() -> str:
    import json

    for line in CANONICAL.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == GEN.TASK_ID:
            return row["program_solution"]
    raise AssertionError("canonical rule missing")


def test_rule_hash_and_all_canonical_pairs_are_pinned():
    normalized = " ".join(_canonical_rule().split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == GEN.RULE_HASH
    pairs = canonical_pairs(GEN.TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(945101)
    global_state = random.getstate()
    first = GEN.generate(731, 11, difficulty="hard")
    assert random.getstate() == global_state
    second = GEN.generate(731, 11, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9
    assert second == GEN.generate(731, 11, difficulty="hard")


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_ordinary_draws_are_lawful_and_observable(difficulty):
    for sample_index in range(40):
        grid = GEN.generate(20_000 + sample_index, sample_index, difficulty=difficulty)
        assert GEN.self_check(grid) == []
        assert GEN.strict_canonical_like(grid) == []
        observed = GEN.observe_overrides(grid)
        assert observed["scene_profile"] == GEN.schedule_profile(
            20_000 + sample_index, sample_index, difficulty
        )
        assert GEN.rule_mirror(grid) != grid


def test_exact_override_boundaries_and_unknown_key_rejection():
    cases = (
        {
            "scene_profile": "cmd1_connected_cmdcolor",
            "grid_h": 8,
            "grid_w": 9,
            "motif_cells": 6,
            "motif_colors": 2,
        },
        {
            "scene_profile": "cmd2_split_no_cmdcolor",
            "grid_h": 14,
            "grid_w": 16,
            "motif_cells": 12,
            "motif_colors": 4,
        },
        {
            "scene_profile": "cmd1_split_no_cmdcolor",
            "grid_h": 10,
            "grid_w": 12,
            "motif_cells": 9,
            "motif_colors": 3,
        },
        {
            "scene_profile": "cmd2_connected_no_cmdcolor",
            "grid_h": 9,
            "grid_w": 11,
            "motif_cells": 7,
            "motif_colors": 2,
        },
    )
    for index, overrides in enumerate(cases):
        grid = GEN.generate(31 + index, index, difficulty="easy", **overrides)
        assert GEN.observe_overrides(grid) == overrides
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(3, 1, texture="warm")
    with pytest.raises(ValueError, match="outside"):
        GEN.generate(3, 1, motif_cells=5)


def test_declared_mutation_impostors_are_rejected():
    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert GEN.self_check(copy.deepcopy(grid)), name


def test_every_sliding_four_example_window_identifies_the_rule():
    for start in range(12):
        pairs = []
        for sample_index in range(start, start + GEN.EXAMPLES_NEEDED + 1):
            grid = GEN.generate(4242, sample_index, difficulty="medium")
            pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
        demos = pairs[: GEN.EXAMPLES_NEEDED]
        query = pairs[-1]
        assert GEN.lesson_identifiable(demos, query) == []
        profiles = {GEN.observe_overrides(pair["input"])["scene_profile"] for pair in demos}
        assert profiles == set(GEN.SCENE_PROFILES)


def test_semantic_witnesses_refute_their_named_rivals():
    grids = [GEN.generate(777, index, difficulty="medium") for index in range(8)]
    for witness_name, witness in GEN.SEMANTIC_WITNESSES.items():
        firing = [grid for grid in grids if witness(grid)]
        assert firing, witness_name
        rival_names = GEN.WITNESS_RIVALS[witness_name]
        assert any(
            GEN.SEMANTIC_RIVALS[rival_name](grid) != GEN.rule_mirror(grid)
            for grid in firing
            for rival_name in rival_names
        ), witness_name
