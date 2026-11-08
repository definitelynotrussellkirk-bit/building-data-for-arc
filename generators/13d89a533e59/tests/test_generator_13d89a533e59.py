from __future__ import annotations

import importlib
import json
import random
from pathlib import Path

import pytest

from scripts.canonical_profile_gate import (
    canonical_pairs,
    canonical_rule_hash,
    canonical_rule_source,
)


gen = importlib.import_module("puzzle_generators.per_puzzle.13d89a533e59.generator")

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "13d89a533e59"
BASE_PATH = ROOT / "data/base/solutions/training/85fa5666__13d89a533e59.json"


def test_rule_pin_canonical_pairs_and_selected_source_are_exact():
    assert gen.VERSION == "3.0.0"
    assert gen.RULE_HASH == canonical_rule_hash(TASK_ID) == "26b1f77320c5"

    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]

    target = json.loads(BASE_PATH.read_text(encoding="utf-8"))["racket_target"]
    assert target["target_code"] == canonical_rule_source(TASK_ID)
    assert target["target_code_role"] == "selected_task_rule"
    assert target["raw_code_role"] == "archival_executable_source"
    assert target["raw_code"] != target["target_code"]


def test_four_slot_schedule_covers_all_semantic_branches_and_every_window_identifies():
    for start in range(8):
        grids = [
            gen.generate(1701, start + offset, difficulty="medium")
            for offset in range(5)
        ]
        demos = [
            {"input": grid, "output": gen.rule_mirror(grid)}
            for grid in grids[: gen.EXAMPLES_NEEDED]
        ]
        query = {
            "input": grids[gen.EXAMPLES_NEEDED],
            "output": gen.rule_mirror(grids[gen.EXAMPLES_NEEDED]),
        }
        assert gen.lesson_identifiable(demos, query) == []

        observed_modes = {
            gen.observe_overrides(pair["input"])["interaction_mode"]
            for pair in demos
        }
        assert observed_modes == set(gen.INTERACTION_MODES)
        for witness_name, witness in gen.SEMANTIC_WITNESSES.items():
            assert any(witness(pair["input"]) for pair in demos), witness_name


def test_blocked_skimmer_is_narrow_and_open_skimmer_is_negative_control():
    blocked = gen.generate(
        99,
        3,
        difficulty="medium",
        grid_h=9,
        grid_w=9,
        n_blocks=2,
        marker_palette="canonical",
        interaction_mode="blocked_skimmer",
    )
    open_case = gen.generate(
        100,
        2,
        difficulty="medium",
        grid_h=9,
        grid_w=9,
        n_blocks=2,
        marker_palette="canonical",
        interaction_mode="open_skimmer",
    )

    assert gen.observe_overrides(blocked)["interaction_mode"] == "blocked_skimmer"
    assert gen.observe_overrides(open_case)["interaction_mode"] == "open_skimmer"
    assert (
        gen.SEMANTIC_RIVALS["no_special_skimmer_stop"](blocked)
        != gen.rule_mirror(blocked)
    )
    assert (
        gen.SEMANTIC_RIVALS["no_special_skimmer_stop"](open_case)
        == gen.rule_mirror(open_case)
    )
    assert (
        gen.SEMANTIC_RIVALS["opposite_corner_swap"](open_case)
        != gen.rule_mirror(open_case)
    )


def test_override_boundaries_are_exact_observable_and_band_safe():
    case_index = 0
    for difficulty in ("easy", "medium", "hard"):
        for grid_h, grid_w in ((8, 8), (8, 15), (15, 8), (15, 15)):
            for n_blocks in (1, 2, 3):
                modes = ("edge",) if n_blocks == 1 else gen.INTERACTION_MODES
                for interaction_mode in modes:
                    for marker_palette in gen.MARKER_PALETTES:
                        requested = {
                            "grid_h": grid_h,
                            "grid_w": grid_w,
                            "n_blocks": n_blocks,
                            "marker_palette": marker_palette,
                            "interaction_mode": interaction_mode,
                        }
                        grid = gen.generate(
                            9000 + case_index,
                            case_index % 17,
                            difficulty=difficulty,
                            **requested,
                        )
                        assert gen.self_check(grid) == []
                        assert gen.observe_overrides(grid) == requested
                        case_index += 1

    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(1, 2, bogus_axis=3)
    with pytest.raises(ValueError, match="require at least two blocks") as error:
        gen.generate(1, 2, n_blocks=1, interaction_mode="red_stop")
    assert set(error.value.incompatible_axes) == {"n_blocks", "interaction_mode"}


def test_structural_mutations_are_rejected():
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert gen.self_check(grid), name


def test_replay_is_fresh_deterministic_and_global_rng_pure():
    random.seed(20260815)
    state = random.getstate()
    first = gen.generate(123, 456, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(123, 456, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second
