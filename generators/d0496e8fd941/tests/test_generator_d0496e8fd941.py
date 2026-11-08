from __future__ import annotations

import copy
import json
import random
from pathlib import Path

from puzzle_generators.per_puzzle.d0496e8fd941 import generator as gen


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/base/solutions/banks/cc07013acae1/M67__d0496e8fd941.json"


def _canonical_pairs():
    row = json.loads(BASE.read_text())
    pairs = list(row["visible_context"]["train"])
    for index, item in enumerate(row["visible_context"]["test_inputs"]):
        pairs.append(
            {
                "input": item["input"],
                "output": row["verification"]["expected_test_outputs"][index],
            }
        )
    return pairs


def _noncorner_border_cell(record):
    row0, col0, row1, col1 = record["bbox"]
    if col1 - col0 >= 2:
        return row0, col0 + 1
    return row0 + 1, col0


def test_canonical_inputs_are_accepted_and_python_mirror_matches_outputs():
    pairs = _canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_all_scene_profile_overrides_are_exactly_observable():
    for band in ("easy", "medium", "hard"):
        for index, profile in enumerate(gen.SCENE_PROFILES):
            grid = gen.generate(500 + index, 11, difficulty=band, scene_profile=profile)
            assert gen.self_check(grid, difficulty=band, meta={"scene_profile": profile}) == []
            assert gen.observe_overrides(grid) == {"scene_profile": profile}


def test_default_three_demo_schedule_witnesses_positive_and_counterexample_branches():
    for seed in range(10):
        grids = [gen.generate(seed, sample_index, difficulty="medium") for sample_index in range(3)]
        facts = [gen._analysis(grid)["facts"] for grid in grids]
        assert all(fact["changed_count"] > 0 for fact in facts)
        assert facts[0]["selected_valid"]
        assert (
            facts[1]["selected_invalid"]
            or len(facts[1]["marker"]["cells"]) > 1
        )
        assert facts[2]["selected_valid"]


def test_touching_selected_components_are_preserved_even_when_color_matches_selector():
    grid = gen.generate(71, 3, difficulty="hard", scene_profile="touching_selected_identity")
    analysis = gen._analysis(grid)
    assert analysis["errors"] == []
    assert analysis["facts"]["selected_valid"] == ()
    assert analysis["facts"]["selected_invalid"]
    assert gen.rule_mirror(grid) == grid


def test_valid_selected_frame_fills_while_touching_selected_component_stays_unchanged():
    grid = gen.generate(72, 3, difficulty="hard", scene_profile="valid_plus_touching_selected")
    facts = gen._analysis(grid)["facts"]
    output = gen.rule_mirror(grid)
    assert facts["selected_valid"] and facts["selected_invalid"]
    for record in facts["selected_valid"]:
        assert all(output[row][col] == facts["target"] for row, col in record["interior"])
    for record in facts["selected_invalid"]:
        assert all(output[row][col] == grid[row][col] for row, col in record["cells"])


def test_self_check_rejects_targeted_structural_impostors():
    base = gen.generate(90, 0, difficulty="medium", scene_profile="selected_single")
    facts = gen._analysis(base)["facts"]

    missing_selector = copy.deepcopy(base)
    missing_selector[0][0] = 0
    assert gen.self_check(missing_selector)

    broken_selected = copy.deepcopy(base)
    row, col = _noncorner_border_cell(facts["selected_valid"][0])
    broken_selected[row][col] = 0
    assert gen.self_check(broken_selected)

    selector_joined = copy.deepcopy(base)
    row0, col0, _, _ = facts["selected_valid"][0]["bbox"]
    for col in range(col0 + 1):
        selector_joined[0][col] = facts["target"]
    for row in range(row0 + 1):
        selector_joined[row][col0] = facts["target"]
    assert gen.self_check(selector_joined)

    broken_decoy = copy.deepcopy(base)
    row, col = _noncorner_border_cell(facts["decoy_frames"][0])
    broken_decoy[row][col] = 0
    assert gen.self_check(broken_decoy)

    occupied_interior = copy.deepcopy(base)
    row, col = facts["selected_valid"][0]["interior"][0]
    occupied_interior[row][col] = facts["decoy_frames"][0]["color"]
    assert gen.self_check(occupied_interior)


def test_replay_is_deterministic_fresh_and_does_not_touch_global_rng():
    random.seed(123456)
    before = random.getstate()
    first = gen.generate(31415, 2, difficulty="hard")
    after = random.getstate()
    second = gen.generate(31415, 2, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 0
    assert second[0][0] != 0
