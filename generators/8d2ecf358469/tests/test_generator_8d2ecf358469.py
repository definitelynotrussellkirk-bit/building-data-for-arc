from __future__ import annotations

import hashlib
import json
import random

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator


ROOT = find_root(__file__)
TASK_ID = "8d2ecf358469"
gen, _, _ = load_selected_generator(TASK_ID, root=ROOT)
BASE_PATH = canonical_path(ROOT).parent.parent / "base/solutions/banks/16956638be77/hard_25_bar_chart_component_areas_by_color__8d2ecf358469.json"


def test_rule_pin_canonical_pairs_and_selected_source_are_exact():
    assert gen.VERSION == "2.1.0"
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 6
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]

    canonical_source = None
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and row.get("program_solution"):
                canonical_source = row["program_solution"]
                break
    assert canonical_source is not None
    assert gen.RULE_HASH == hashlib.sha256(" ".join(canonical_source.split()).encode()).hexdigest()[:12] == "e8095729a5e6"
    target = json.loads(BASE_PATH.read_text(encoding="utf-8"))["racket_target"]
    assert target["target_code"] == canonical_source
    assert target["raw_code"] != target["target_code"]  # archival source is preserved


def test_override_boundaries_are_exact_observable_and_band_safe():
    areas = ("2-3-4", "2-5-4")
    case_index = 0
    for difficulty in ("easy", "medium", "hard"):
        for grid_h in (9, 11):
            for grid_w in (12, 14):
                for area_profile in areas:
                    requested = {
                        "grid_h": grid_h,
                        "grid_w": grid_w,
                        "area_profile": area_profile,
                    }
                    grid = gen.generate(
                        8000 + case_index,
                        case_index % 17,
                        difficulty=difficulty,
                        **requested,
                    )
                    assert gen.self_check(grid) == []
                    assert gen.observe_overrides(grid) == requested
                    case_index += 1

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 2, __override_contract_unknown_axis__="typo")


def test_every_sliding_lesson_falsifies_named_rivals():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(10):
            pairs = []
            for index in range(start, start + gen.EXAMPLES_NEEDED + 1):
                grid = gen.generate(1701 + start, index, difficulty=difficulty)
                pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
            demos, query = pairs[:-1], pairs[-1]
            assert gen.lesson_identifiable(demos, query) == []

            profiles = {
                gen.observe_overrides(pair["input"])["area_profile"]
                for pair in demos
            }
            assert profiles == set(gen.SCHEDULE_PROFILES)
            for name, competitor in gen.LESSON_COMPETITORS.items():
                assert any(
                    competitor(pair["input"]) != pair["output"]
                    for pair in demos
                ), name


def test_semantic_witnesses_fire_and_refute_their_named_rivals():
    grids = [gen.generate(9001, index, difficulty="medium") for index in range(10)]
    for witness_name, witness in gen.SEMANTIC_WITNESSES.items():
        witnesses = [grid for grid in grids if witness(grid)]
        assert witnesses, witness_name
        for rival_name in gen.WITNESS_RIVALS[witness_name]:
            assert any(
                gen.SEMANTIC_RIVALS[rival_name](grid) != gen.rule_mirror(grid)
                for grid in witnesses
            ), (witness_name, rival_name)


def test_structural_impostors_are_rejected_but_equal_areas_are_lawful():
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert gen.self_check(grid), name

    # Equal areas are not ambiguous because output rows are ordered by color.
    equal = [[0] * 12 for _ in range(9)]
    equal[2][2] = equal[2][3] = 2
    equal[4][5] = equal[4][6] = 4
    equal[6][8] = equal[6][9] = 6
    assert gen.self_check(equal) == []
    assert gen.rule_mirror(equal) == [[2, 2], [4, 4], [6, 6]]


def test_replay_is_fresh_deterministic_and_global_rng_pure():
    random.seed(20260815)
    state = random.getstate()
    first = gen.generate(123, 456, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(123, 456, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert first != second
