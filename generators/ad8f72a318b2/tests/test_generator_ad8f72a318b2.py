from __future__ import annotations

import copy
import importlib
import random

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "ad8f72a318b2"
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.ad8f72a318b2.generator"
)


def _pair(seed: int, sample_index: int, band: str) -> dict[str, list[list[int]]]:
    grid = GEN.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_rule_hash_and_canonical_python_mirror() -> None:
    assert GEN.RULE_HASH == "5d4b4a902077"
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)
    assert len(pairs) == 5
    for pair in pairs:
        grid = copy.deepcopy(pair["input"])
        assert GEN.self_check(grid) == []
        assert GEN.rule_mirror(grid) == pair["output"]


def test_unknown_override_rejected_and_exact_controls_observable() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(7, 0, difficulty="easy", typo_axis=1)

    for band in ("easy", "medium", "hard"):
        for index in range(1, 5):
            for transform in range(1, 6):
                for target_relation in GEN.TARGET_RELATIONS:
                    grid = GEN.generate(
                        1000 + index * 100 + transform * 10,
                        transform,
                        difficulty=band,
                        index=index,
                        transform=transform,
                        target_relation=target_relation,
                    )
                    expected = {
                        "index": index,
                        "transform": transform,
                        "target_relation": target_relation,
                    }
                    assert GEN.observe_overrides(grid) == expected
                    assert GEN.self_check(grid, meta={"overrides": expected}) == []


def test_every_five_demo_window_teaches_all_controls() -> None:
    assert GEN.EXAMPLES_NEEDED == 5
    assert GEN.LESSON_SCHEDULE_PERIOD == 60
    for start in range(GEN.LESSON_SCHEDULE_PERIOD):
        profiles = [
            GEN.schedule_profile(0, start + offset, difficulty="medium")
            for offset in range(GEN.EXAMPLES_NEEDED + 1)
        ]
        controls = [GEN._PROFILE_BY_NAME[profile] for profile in profiles]
        demos, query = controls[:-1], controls[-1]
        assert {index for index, _, _ in demos} == {1, 2, 3, 4}
        assert {transform for _, transform, _ in demos} == {1, 2, 3, 4, 5}
        assert {relation for _, _, relation in demos} == set(GEN.TARGET_RELATIONS)
        assert query[1] in {transform for _, transform, _ in demos}


def test_generated_panels_are_distinct_and_transform_sensitive() -> None:
    for band in ("easy", "medium", "hard"):
        for sample_index in range(20):
            grid = GEN.generate(4000 + sample_index, sample_index, difficulty=band)
            assert GEN.strict_canonical_like(grid) == []
            analysis = GEN._analysis(grid)
            supports = [panel["cells"] for panel in analysis["panels"]]
            assert len({GEN._dihedral_key(cells) for cells in supports}) == 4
            for cells in supports:
                variants = {
                    GEN._transform_support(cells, code)
                    for code in range(1, 6)
                }
                assert len(variants) == 5


def test_production_lessons_refute_every_declared_competitor() -> None:
    for band in ("easy", "medium", "hard"):
        for start in range(0, GEN.LESSON_SCHEDULE_PERIOD, 7):
            pairs = [
                _pair(7000 + start, start + offset, band)
                for offset in range(GEN.EXAMPLES_NEEDED + 1)
            ]
            demos, query = pairs[:-1], pairs[-1]
            assert GEN.lesson_identifiable(demos, query) == []
            for name, competitor in GEN.LESSON_COMPETITORS.items():
                survives = all(
                    competitor(pair["input"]) == pair["output"]
                    for pair in demos
                )
                assert not (
                    survives
                    and competitor(query["input"]) != query["output"]
                ), name


def test_self_check_rejects_structural_impostors() -> None:
    base = GEN.generate(9001, 5, difficulty="medium")

    non_unary_selector = copy.deepcopy(base)
    non_unary_selector[0][:4] = [1, 0, 1, 0]
    assert GEN.self_check(non_unary_selector)

    stray_separator = copy.deepcopy(base)
    stray_separator[6][4] = 9
    assert GEN.self_check(stray_separator)

    disconnected_panel = copy.deepcopy(base)
    for row in range(2, 6):
        for col in range(0, 4):
            disconnected_panel[row][col] = 0
    disconnected_panel[2][0] = 2
    disconnected_panel[5][3] = 2
    assert GEN.self_check(disconnected_panel)

    duplicate_panel_color = copy.deepcopy(base)
    first_color = next(
        duplicate_panel_color[row][col]
        for row in range(2, 6)
        for col in range(0, 4)
        if duplicate_panel_color[row][col]
    )
    for row in range(2, 6):
        for col in range(5, 9):
            if duplicate_panel_color[row][col]:
                duplicate_panel_color[row][col] = first_color
    assert GEN.self_check(duplicate_panel_color)


def test_replay_fresh_returns_and_global_rng_preservation() -> None:
    random.seed(123456)
    before = random.getstate()
    first = GEN.generate(77, 8, difficulty="hard")
    after = random.getstate()
    assert before == after

    second = GEN.generate(77, 8, difficulty="hard")
    assert first == second
    assert first is not second
    first[0][0] = 9
    assert second[0][0] != 9


def test_every_semantic_witness_names_a_disagreeing_rival() -> None:
    assert set(GEN.SEMANTIC_WITNESSES) <= set(GEN.WITNESS_RIVALS)


def test_all_query_rotations_refute_declared_competitors() -> None:
    for band in ("easy", "medium", "hard"):
        for start in range(GEN.LESSON_SCHEDULE_PERIOD):
            pairs = [
                _pair(12000 + start, start + offset, band)
                for offset in range(GEN.EXAMPLES_NEEDED + 1)
            ]
            for query_index, query in enumerate(pairs):
                demos = [
                    pair for position, pair in enumerate(pairs)
                    if position != query_index
                ]
                assert GEN.lesson_identifiable(demos, query) == []
                for name, competitor in GEN.LESSON_COMPETITORS.items():
                    survives = all(
                        competitor(pair["input"]) == pair["output"]
                        for pair in demos
                    )
                    assert not (
                        survives
                        and competitor(query["input"]) != query["output"]
                    ), (band, start, query_index, name)
