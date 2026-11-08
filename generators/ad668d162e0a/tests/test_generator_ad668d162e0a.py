from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from scripts.rule_smoke import rule_application
from puzzle_generators.per_puzzle.ad668d162e0a import generator as gen

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "ad668d162e0a"


def _canonical_row():
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError("canonical row missing")


def _rule_hash(rule: str) -> str:
    # Same normalized-content convention used by generator_defect_lint.
    normalized = " ".join(rule.split())
    return hashlib.sha256(normalized.encode()).hexdigest()[:12]


def test_rule_hash_and_all_canonical_pairs_are_accepted_and_exact():
    row = _canonical_row()
    assert _rule_hash(row["program_solution"]) == gen.RULE_HASH
    pairs = [*row["train"], *row["test"]]
    assert len(pairs) == 4
    bridge = RacketBridge()
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        actual = bridge.eval_text(rule_application(row["program_solution"], pair["input"]))
        assert actual == pair["output"]
        assert pair["input"] == original


def test_regression_override_boundaries_are_exact_or_loud():
    cases = [
        {"grid_h": 5},
        {"grid_h": 10},
        {"grid_w": 6},
        {"grid_w": 12},
        {"n_blocks": 1},
        {"n_blocks": 3},
        {"palette_kind": "warm"},
        {"palette_kind": "cool", "n_blocks": 3},
    ]
    for case in cases:
        grid = gen.generate(991, 17, difficulty="easy", **case)
        observed = gen.observe_overrides(grid)
        for key, value in case.items():
            if key in observed:
                assert observed[key] == value
        assert gen.self_check(grid) == []


def test_regression_self_check_rejects_four_targeted_impostors():
    impostors = {
        "all_background": [[0] * 6 for _ in range(5)],
        "singleton": [[4 if (r, c) == (2, 2) else 0 for c in range(6)] for r in range(5)],
        "solid_2x2": [[4 if 1 <= r <= 2 and 1 <= c <= 2 else 0 for c in range(6)] for r in range(5)],
        "mixed_ring": [
            [4, 4, 6, 0, 0, 0],
            [4, 0, 6, 0, 0, 0],
            [4, 6, 6, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
        ],
        "filled_center": [
            [4, 4, 4, 0, 0, 0],
            [4, 4, 4, 0, 0, 0],
            [4, 4, 4, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
        ],
    }
    for name, grid in impostors.items():
        assert gen.self_check(grid), name


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(8675309)
    state = random.getstate()
    first = gen.generate(1234, 9, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(1234, 9, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second


def test_all_bands_cover_counts_and_shortcut_distractor():
    for band in ("easy", "medium", "hard"):
        counts = set()
        border = interior = 0
        for sample_index in range(36):
            grid = gen.generate(7000 + sample_index, sample_index, difficulty=band)
            assert gen.self_check(grid) == []
            counts.add(gen.observe_overrides(grid)["n_blocks"])
            border += int(gen.SEMANTIC_WITNESSES["border_anchored_target"](grid))
            interior += int(gen.SEMANTIC_WITNESSES["interior_target"](grid))
            assert gen.SEMANTIC_WITNESSES["shortcut_rebutting_distractor"](grid)
            assert gen.rule_mirror(grid) != grid
            assert gen._fill_component_bboxes(grid) != gen.rule_mirror(grid)
        assert counts == {1, 2, 3}
        assert border > 0
        assert interior > 0


def test_lesson_identifiability_on_materialized_pairs():
    pairs = []
    for index in range(5):
        grid = gen.generate(4400 + index, index, difficulty=("easy", "medium", "hard")[index % 3])
        pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
    assert gen.lesson_identifiable(pairs[:4], pairs[4]) == []
