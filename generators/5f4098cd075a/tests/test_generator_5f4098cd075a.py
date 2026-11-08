"""Focused semantic and regression tests for generator 5f4098cd075a."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest


TASK_ID = "5f4098cd075a"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
ROOT = Path(__file__).resolve().parents[1]


def _canonical_row():
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def _canonical_pairs():
    row = _canonical_row()
    test = row["test"]
    return row["train"] + (test if isinstance(test, list) else [test])


def _pair(seed: int, sample_index: int, band: str = "medium"):
    grid = MODULE.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": MODULE.rule_mirror(grid)}


def test_canonical_inputs_outputs_and_repeated_test_key_are_supported():
    pairs = _canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        assert MODULE.self_check(pair["input"]) == []
        assert MODULE.strict_canonical_like(pair["input"]) == []
        assert MODULE.rule_mirror(pair["input"]) == pair["output"]
    assert MODULE.semantic_observables(pairs[-1]["input"])["target_keys"] == [1, 3, 1]
    assert MODULE.observe_overrides(pairs[-1]["input"])["target_repeats"] is True


def test_default_four_step_schedule_covers_all_semantic_branches_per_band():
    for band in ("easy", "medium", "hard"):
        facts = [MODULE.semantic_observables(MODULE.generate(71, i, difficulty=band)) for i in range(4)]
        assert facts[0]["n_src"] == 3 and facts[0]["n_tgt"] == 2
        assert MODULE.strict_canonical_like(MODULE.generate(71, 0, difficulty=band)) == []
        assert facts[1]["full_target_row"] and not facts[1]["target_repeats"]
        assert facts[2]["full_target_row"] and facts[2]["target_repeats"]
        assert facts[3]["has_trailing_blank"] and not facts[3]["target_repeats"]
        assert all(item["position_mismatch"] for item in facts)
        assert all(len(set(item["prototype_shapes"])) == item["n_src"] for item in facts)
        assert all(len(set(item["prototype_colors"])) == item["n_src"] for item in facts)


def test_every_valid_exact_override_boundary_is_observable_in_every_band():
    for band in ("easy", "medium", "hard"):
        for n_src in range(3, 6):
            for n_tgt in range(2, n_src + 1):
                repeat_options = (False, True) if n_tgt >= 3 else (False,)
                for repeats in repeat_options:
                    grid = MODULE.generate(
                        131,
                        19 + n_src * 11 + n_tgt,
                        difficulty=band,
                        n_src=n_src,
                        n_tgt=n_tgt,
                        target_repeats=repeats,
                    )
                    assert MODULE.observe_overrides(grid) == {
                        "n_src": n_src,
                        "n_tgt": n_tgt,
                        "target_repeats": repeats,
                    }
                    assert MODULE.self_check(
                        grid,
                        meta={"overrides": {
                            "n_src": n_src,
                            "n_tgt": n_tgt,
                            "target_repeats": repeats,
                        }},
                    ) == []


def test_incompatible_and_unknown_overrides_reject_loudly():
    invalid = (
        {"n_src": 2},
        {"n_src": 6},
        {"n_tgt": 1},
        {"n_tgt": 6},
        {"target_repeats": "yes"},
        {"n_src": 3, "n_tgt": 4},
        {"n_tgt": 2, "target_repeats": True},
        {"texture": "warm"},
    )
    for overrides in invalid:
        with pytest.raises((TypeError, ValueError)):
            MODULE.generate(3, 5, **overrides)


def test_structural_self_check_rejects_targeted_impostors():
    base = MODULE.generate(211, 0, difficulty="medium")
    facts = MODULE.semantic_observables(base)
    impostors = []

    broken_divider = copy.deepcopy(base)
    broken_divider[MODULE.DIVIDER_ROW][0] = 0
    impostors.append(broken_divider)

    broken_source_frame = copy.deepcopy(base)
    broken_source_frame[1][0] = 0
    impostors.append(broken_source_frame)

    prefilled_target = copy.deepcopy(base)
    prefilled_target[MODULE.TARGET_FRAME_TOP + 1][1] = 4
    impostors.append(prefilled_target)

    duplicate_source_key = copy.deepcopy(base)
    duplicate_source_key[0][MODULE.PITCH + MODULE.FRAME // 2] = duplicate_source_key[0][MODULE.FRAME // 2]
    impostors.append(duplicate_source_key)

    absent_target_key = copy.deepcopy(base)
    absent_target_key[MODULE.TARGET_KEY_ROW][MODULE.FRAME // 2] = 6
    impostors.append(absent_target_key)

    fixed_position = copy.deepcopy(base)
    for index, key in enumerate(facts["source_keys"][: facts["n_tgt"]]):
        fixed_position[MODULE.TARGET_KEY_ROW][index * MODULE.PITCH + MODULE.FRAME // 2] = key
    impostors.append(fixed_position)

    for grid in impostors:
        assert MODULE.self_check(grid), grid


def test_generated_lessons_identify_key_lookup_not_shortcuts():
    for band in ("easy", "medium", "hard"):
        rows = [_pair(307, index, band) for index in range(4)]
        assert MODULE.lesson_identifiable(rows[:3], rows[3]) == []
        for mode in (
            "fixed_position",
            "reverse_position",
            "first_prototype",
            "key_as_answer",
            "modal_color_echo",
        ):
            # A shortcut may be answer-equivalent on one query by coincidence,
            # but it must be contradicted somewhere in the scheduled lesson.
            assert any(
                MODULE._competitor_output(row["input"], mode) != row["output"]
                for row in rows
            )


def test_rule_pin_matches_canonical_and_selected_task_local_authority():
    row = _canonical_row()
    source = row["program_solution"]
    base = json.loads(
        (ROOT / "data/base/solutions/banks/b9cb6b5db49d/H74__5f4098cd075a.json").read_text()
    )
    expected = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
    assert expected == MODULE.RULE_HASH == "27d29e43e3ba"
    assert base["racket_target"]["target_code"] == source


def test_determinism_freshness_and_process_global_rng_purity():
    random.seed(20260724)
    state = random.getstate()
    first = MODULE.generate(401, 503, difficulty="hard", n_src=5, n_tgt=5, target_repeats=True)
    assert random.getstate() == state
    second = MODULE.generate(401, 503, difficulty="hard", n_src=5, n_tgt=5, target_repeats=True)
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    second[0][0] = 9 if second[0][0] != 9 else 0
    assert first != second
