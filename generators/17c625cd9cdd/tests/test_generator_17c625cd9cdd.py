from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

TASK = "17c625cd9cdd"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = Path(__file__).resolve().parents[1]


def canonical_row():
    return next(
        json.loads(line)
        for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines()
        if json.loads(line).get("task_id") == TASK
    )


def test_canonical_pairs_match_rule_and_self_check():
    row = canonical_row()
    pairs = row["train"] + row["test"]
    assert len(pairs) == 5
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN._mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_four_sample_schedule_covers_semantic_branches():
    observed = [GEN.observe_overrides(GEN.generate(91, i, difficulty="medium")) for i in range(4)]
    assert [item["orientation"] for item in observed] == [
        "horizontal", "vertical", "mixed", "mixed"
    ]
    assert [item["span_class"] for item in observed] == [
        "short", "long", "mixed", "long"
    ]
    assert [item["edge_anchor"] for item in observed] == [False, True, False, True]
    assert all(item["n_pairs"] >= 2 for item in observed)
    assert sum(item["n_distractors"] > 0 for item in observed) >= 3


@pytest.mark.parametrize(
    "overrides",
    [
        {
            "grid_h": 6,
            "grid_w": 14,
            "n_pairs": 4,
            "n_distractors": 3,
            "orientation": "horizontal",
            "span_class": "short",
            "palette_kind": "spread",
            "edge_anchor": False,
        },
        {
            "grid_h": 14,
            "grid_w": 6,
            "n_pairs": 4,
            "n_distractors": 2,
            "orientation": "vertical",
            "span_class": "long",
            "palette_kind": "upper",
            "edge_anchor": True,
        },
        {
            "grid_h": 14,
            "grid_w": 14,
            "n_pairs": 4,
            "n_distractors": 3,
            "orientation": "mixed",
            "span_class": "mixed",
            "palette_kind": "lower",
            "edge_anchor": True,
        },
    ],
)
def test_exact_overrides_are_observable(overrides):
    grid = GEN.generate(17, 23, difficulty="hard", **overrides)
    observed = GEN.observe_overrides(grid)
    assert len(grid) == overrides["grid_h"]
    assert len(grid[0]) == overrides["grid_w"]
    for axis in (
        "n_pairs", "n_distractors", "orientation", "span_class",
        "palette_kind", "edge_anchor",
    ):
        assert observed[axis] == overrides[axis]
    assert GEN.self_check(grid) == []


def test_incompatible_exact_combinations_reject_loudly():
    with pytest.raises(ValueError, match="orientation=mixed requires"):
        GEN.generate(1, 1, n_pairs=1, orientation="mixed")
    with pytest.raises(ValueError, match="span_class=mixed requires"):
        GEN.generate(1, 1, n_pairs=1, span_class="mixed")
    with pytest.raises(ValueError, match="spread requires"):
        GEN.generate(1, 1, n_pairs=1, n_distractors=0, palette_kind="spread")
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 1, texture="no_pairs")


def test_self_check_rejects_targeted_impostors():
    cases = []
    cases.append([[0] * 6 for _ in range(6)])

    adjacent = [[0] * 6 for _ in range(6)]
    adjacent[2][2] = adjacent[2][3] = 4
    cases.append(adjacent)

    diagonal = [[0] * 6 for _ in range(6)]
    diagonal[1][1] = diagonal[3][3] = 4
    cases.append(diagonal)

    triple = [[0] * 6 for _ in range(6)]
    triple[2][1] = triple[2][4] = triple[4][4] = 4
    cases.append(triple)

    blocked_span = [[0] * 6 for _ in range(6)]
    blocked_span[2][1] = blocked_span[2][4] = 4
    blocked_span[2][2] = 7
    cases.append(blocked_span)

    assert all(GEN.self_check(case) for case in cases)


def test_distractors_remain_unchanged_while_targets_fire():
    grid = GEN.generate(
        444,
        2,
        difficulty="hard",
        n_pairs=4,
        n_distractors=3,
        orientation="mixed",
        span_class="mixed",
        palette_kind="spread",
        edge_anchor=False,
    )
    observed = GEN.observe_overrides(grid)
    positions = GEN._positions_by_color(grid)
    targets = {item[0] for item in GEN._target_info(grid)}
    distractors = set(positions) - targets
    output = GEN._mirror(grid)
    assert output != grid
    for color in distractors:
        assert [(r, c) for r, row in enumerate(output) for c, value in enumerate(row) if value == color] == positions[color]
    assert observed["n_distractors"] == 3


def test_determinism_fresh_returns_and_global_rng_preservation():
    random.seed(20260724)
    state = random.getstate()
    first = GEN.generate(77, 19, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(77, 19, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 99
    assert second[0][0] != 99


def test_rule_hash_matches_normalized_canonical_source():
    source = canonical_row()["program_solution"]
    normalized = " ".join(source.split())
    assert GEN.RULE_HASH == hashlib.sha256(normalized.encode()).hexdigest()[:12]
