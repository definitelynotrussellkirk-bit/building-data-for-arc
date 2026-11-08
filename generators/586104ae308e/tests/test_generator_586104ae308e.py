from __future__ import annotations

import copy
import importlib
import json
import random
from itertools import product
from pathlib import Path


MODULE = importlib.import_module(
    "puzzle_generators.per_puzzle.586104ae308e.generator"
)
ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "586104ae308e"


def _canonical_row():
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"canonical row missing for {TASK_ID}")


def test_canonical_inputs_are_accepted_and_mirror_outputs():
    row = _canonical_row()
    for pair in [*row["train"], *row["test"]]:
        before = copy.deepcopy(pair["input"])
        assert MODULE.self_check(pair["input"]) == []
        assert MODULE.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_exact_override_boundaries_are_observable_and_composable():
    values = {
        "grid_h": (10, 18),
        "grid_w": (10, 18),
        "n8": (1, 4),
        "sep_row": (5, 7),
        "data_gap": (1, 2),
    }
    names = tuple(values)
    for selected in product(*(values[name] for name in names)):
        overrides = dict(zip(names, selected))
        grid = MODULE.generate(41, 3, difficulty="hard", **overrides)
        assert MODULE.self_check(grid, meta={"overrides": overrides}) == []
        assert MODULE.observe_overrides(grid) == overrides


def test_unknown_override_is_rejected():
    try:
        MODULE.generate(1, 0, typo_axis=3)
    except ValueError as exc:
        assert "unknown override" in str(exc)
    else:
        raise AssertionError("unknown override was silently accepted")


def test_self_check_rejects_targeted_structural_impostors():
    base = MODULE.generate(17, 0, difficulty="medium")
    analysis = MODULE._analysis(base)
    sep = analysis["separator"]
    data_row = analysis["data_row"]

    bad_header = copy.deepcopy(base)
    bad_header[0][0], bad_header[0][-1] = 0, 8
    assert MODULE.self_check(bad_header)

    duplicate_separator = copy.deepcopy(base)
    duplicate_separator[sep + 1] = [5] * len(base[0])
    assert MODULE.self_check(duplicate_separator)

    dirty_stripe = copy.deepcopy(base)
    dirty_stripe[sep - 1][0] = 2
    assert MODULE.self_check(dirty_stripe)

    second_data_row = copy.deepcopy(base)
    spare = next(row for row in range(sep + 1, len(base)) if row != data_row)
    second_data_row[spare][0] = 3
    assert MODULE.self_check(second_data_row)

    no_distractor = copy.deepcopy(base)
    no_distractor[data_row] = [2] * len(base[0])
    assert MODULE.self_check(no_distractor)


def test_every_four_consecutive_demos_identify_the_rule():
    for start in range(12):
        demos = []
        for sample_index in range(start, start + MODULE.EXAMPLES_NEEDED):
            grid = MODULE.generate(900 + start, sample_index, difficulty="medium")
            demos.append({"input": grid, "output": MODULE.rule_mirror(grid)})
        query_grid = MODULE.generate(
            900 + start, start + MODULE.EXAMPLES_NEEDED, difficulty="medium"
        )
        query = {"input": query_grid, "output": MODULE.rule_mirror(query_grid)}
        assert MODULE.lesson_identifiable(demos, query) == []


def test_semantic_witnesses_fire_and_refute_declared_rivals():
    hits = {name: 0 for name in MODULE.SEMANTIC_WITNESSES}
    for band in ("easy", "medium", "hard"):
        for sample_index in range(16):
            grid = MODULE.generate(300 + sample_index, sample_index, difficulty=band)
            official = MODULE.rule_mirror(grid)
            for name, witness in MODULE.SEMANTIC_WITNESSES.items():
                if witness(grid):
                    hits[name] += 1
                    rivals = MODULE.WITNESS_RIVALS[name]
                    assert any(
                        MODULE.SEMANTIC_RIVALS[rival](grid) != official
                        for rival in rivals
                    )
    assert all(count > 0 for count in hits.values())


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(123456)
    state = random.getstate()
    first = MODULE.generate(77, 9, difficulty="hard")
    assert random.getstate() == state
    second = MODULE.generate(77, 9, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 0
    assert second[0][0] == 8
