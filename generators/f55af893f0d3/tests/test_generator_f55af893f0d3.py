from __future__ import annotations

import copy
import json
from pathlib import Path

from puzzle_generators.per_puzzle.f55af893f0d3 import generator as gen


ROOT = Path(__file__).resolve().parents[1]
AUTHORITY = ROOT / "data/base/solutions/banks/e2825ca16ace/E68__f55af893f0d3.json"


def _canonical_pairs():
    payload = json.loads(AUTHORITY.read_text())
    samples = json.loads(payload["visible_context"]["samples_text"])
    expected_test = payload["verification"]["expected_test_outputs"]
    pairs = list(samples["train"])
    pairs.extend(
        {"input": row["input"], "output": output}
        for row, output in zip(samples["test"], expected_test)
    )
    return pairs


def test_canonical_inputs_and_outputs_are_accepted():
    for pair in _canonical_pairs():
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_exact_override_boundaries_are_observable():
    cases = [
        dict(grid_h=9, grid_w=13, divider_col=5, motif_cells=3, n_decor_cells=8, n_decor_colors=2),
        dict(grid_h=12, grid_w=18, divider_col=8, motif_cells=8, n_decor_cells=16, n_decor_colors=4),
    ]
    for index, overrides in enumerate(cases):
        grid = gen.generate(1700 + index, index, difficulty="hard", **overrides)
        assert gen.observe_overrides(grid) == overrides
        assert gen.self_check(grid, meta={"overrides": overrides}) == []


def test_self_check_rejects_targeted_impostors():
    grid = gen.generate(2442, 3, difficulty="medium")
    facts = gen._analysis(grid)

    divider_hole = copy.deepcopy(grid)
    divider_hole[0][facts["divider"]] = 0
    assert gen.self_check(divider_hole)

    remote_orange = copy.deepcopy(grid)
    for row in remote_orange:
        for col, value in enumerate(row):
            if value == 0 and col < facts["divider"]:
                row[col] = 7
                break
        else:
            continue
        break
    assert any("connected" in reason for reason in gen.self_check(remote_orange))

    occupied_target = copy.deepcopy(grid)
    target = min(facts["mirror_cells"])
    occupied_target[target[0]][target[1]] = 1
    assert any("not empty" in reason for reason in gen.self_check(occupied_target))

    right_orange = copy.deepcopy(grid)
    target = min(facts["mirror_cells"])
    right_orange[target[0]][target[1]] = 7
    assert any("left of the divider" in reason for reason in gen.self_check(right_orange))

    one_sided_decor = copy.deepcopy(grid)
    for row, col, _ in facts["right_decor"]:
        one_sided_decor[row][col] = 0
    assert any("both sides" in reason for reason in gen.self_check(one_sided_decor))


def test_semantic_witnesses_and_lesson_identifiability():
    pairs = []
    for sample_index in range(4):
        grid = gen.generate(991, sample_index, difficulty="medium")
        assert all(predicate(grid) for predicate in gen.SEMANTIC_WITNESSES.values())
        pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
    assert gen.lesson_identifiable(pairs[:3], pairs[3]) == []


def test_replay_is_deterministic_and_returns_fresh_objects():
    first = gen.generate(7, 11, difficulty="easy")
    second = gen.generate(7, 11, difficulty="easy")
    assert first == second
    assert first is not second
    first[0][0] = 9 if first[0][0] != 9 else 1
    assert first != second


def test_seed_three_decoration_growth_terminates():
    grid = gen.generate(3, 3, difficulty="medium")
    assert gen.self_check(grid) == []


def test_reserved_decoration_anchors_are_not_consumed():
    assert gen.self_check(gen.generate(3, 4)) == []
    assert gen.self_check(gen.generate(7, 7, difficulty="hard")) == []
