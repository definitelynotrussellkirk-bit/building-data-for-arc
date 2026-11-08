from __future__ import annotations

import copy
import json
import random
from pathlib import Path

from puzzle_generators.per_puzzle.e58953aee67a import generator as gen


ROOT = Path(__file__).resolve().parents[1]


def _canonical_inputs():
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == gen.TASK_ID:
            return [pair["input"] for pair in row["train"] + row["test"]]
    raise AssertionError("canonical task missing")


def test_canonical_inputs_are_exactly_owned():
    grids = _canonical_inputs()
    assert len(grids) == 3
    for grid in grids:
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []


def test_exact_axes_replay_freshness_and_global_rng():
    state = random.getstate()
    first = gen.generate(11, 7, difficulty="easy", grid_h=4, n_singletons=12)
    second = gen.generate(11, 7, difficulty="easy", grid_h=4, n_singletons=12)
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert random.getstate() == state
    observed = gen.observe_overrides(first)
    assert observed["grid_h"] == 4
    assert observed["n_singletons"] == 12
    assert gen.self_check(
        first,
        meta={"overrides": {"grid_h": 4, "n_singletons": 12}},
    ) == []


def test_incompatible_boundary_tuple_rejects_loudly():
    try:
        gen.generate(3, 1, grid_h=4, grid_w=4, n_singletons=12)
    except ValueError as exc:
        assert "capacity" in str(exc)
    else:
        raise AssertionError("incompatible exact tuple should reject")


def test_five_sample_schedule_covers_semantic_witnesses():
    grids = [gen.generate(19, index, difficulty="medium") for index in range(5)]
    assert gen.strict_canonical_like(grids[0]) == []
    assert gen.SEMANTIC_WITNESSES[
        "nonred_distractor_rebuts_move_all_colours"
    ](grids[1])
    assert gen.SEMANTIC_WITNESSES["red_blob_rebuts_move_all_red"](grids[1])
    assert gen.SEMANTIC_WITNESSES["red_blob_rebuts_move_all_red"](grids[2])
    assert gen.SEMANTIC_WITNESSES[
        "nonred_distractor_rebuts_move_all_colours"
    ](grids[3])
    assert gen.SEMANTIC_WITNESSES["red_blob_rebuts_move_all_red"](grids[3])


def test_self_check_rejects_four_structural_impostors():
    lawful = gen.generate(23, 4, difficulty="easy")

    blank = [[0 for _ in row] for row in lawful]
    assert gen.self_check(blank)

    one = [[0 for _ in row] for row in lawful]
    one[0][0] = 2
    assert gen.self_check(one)

    edge = [[0] * 5 for _ in range(5)]
    edge[0][0] = 2
    edge[2][0] = 2
    edge[4][4] = 2
    assert any("right edge" in reason for reason in gen.self_check(edge))

    blocked = [[0] * 5 for _ in range(5)]
    blocked[0][0] = 2
    blocked[2][0] = 2
    blocked[4][1] = 2
    blocked[4][2] = 4
    assert any("blocked right" in reason for reason in gen.self_check(blocked))


def test_lesson_schedule_refutes_query_changing_rivals():
    for start in range(5):
        inputs = [gen.generate(31, start + offset) for offset in range(4)]
        pairs = [{"input": grid, "output": gen.rule_mirror(grid)} for grid in inputs]
        assert gen.lesson_identifiable(pairs[:3], pairs[3]) == []
