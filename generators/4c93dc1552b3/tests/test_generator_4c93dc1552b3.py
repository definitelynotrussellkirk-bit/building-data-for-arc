"""Focused regressions for the 4c93dc1552b3 rectangle-corner generator."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random

import pytest

from puzzle_generators import base as generator_base
from reviewer_support import canonical_pairs, canonical_path, find_root


gen = importlib.import_module(
    "puzzle_generators.per_puzzle.4c93dc1552b3.generator"
)
ROOT = find_root(__file__)


def _episode(seed: int, start: int, band: str):
    demos = []
    for offset in range(gen.EXAMPLES_NEEDED):
        grid = gen.generate(seed, start + offset, difficulty=band)
        demos.append({"input": grid, "output": gen.rule_mirror(grid)})
    query_grid = gen.generate(seed, start + gen.EXAMPLES_NEEDED, difficulty=band)
    query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
    return demos, query


def test_rule_hash_and_every_canonical_pair():
    pairs = canonical_pairs(gen.TASK_ID, root=ROOT)
    assert len(pairs) == 5
    row = next(
        json.loads(line)
        for line in canonical_path(ROOT).open(encoding="utf-8")
        if json.loads(line).get("task_id") == gen.TASK_ID
    )
    actual = hashlib.sha256(
        " ".join(row["program_solution"].split()).encode()
    ).hexdigest()[:12]
    assert gen.RULE_HASH == actual == "3b0c50f6c708"
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert gen.self_check(source) == []
        assert gen.strict_canonical_like(source) == []
        assert gen.rule_mirror(source) == pair["output"]


def test_every_profile_is_exact_observable_and_overrideable():
    for band in ("easy", "medium", "hard"):
        for index, profile in enumerate(gen.SCENE_PROFILES):
            grid = gen.generate(
                10_000 + index,
                20_000 + index,
                difficulty=band,
                scene_profile=profile,
            )
            assert gen.self_check(grid) == []
            assert gen.teaching_check(grid) == []
            assert gen.strict_canonical_like(grid) == []
            assert gen.observe_overrides(grid) == {"scene_profile": profile}
    with pytest.raises(ValueError):
        gen.generate(1, 1, scene_profile="unknown")
    with pytest.raises(ValueError):
        gen.generate(1, 1, typo_profile="easy_pair_8x10")
    with pytest.raises(ValueError):
        gen.generate(1, 1, difficulty="extreme")


def test_default_keyed_profile_matches_returned_grid():
    captured = []
    generator_base.set_ctx_observer(captured.append)
    try:
        for band_index, band in enumerate(("easy", "medium", "hard")):
            for index in range(24):
                grid = gen.generate(
                    30_000 + band_index * 100 + index,
                    index * 17 + 3,
                    difficulty=band,
                )
                ctx = captured[-1]
                observed = gen.observe_overrides(grid)
                assert ctx.recorded_draws()["scene_profile"] == observed["scene_profile"]
                assert ctx.overrides_used() == {}
    finally:
        generator_base.set_ctx_observer(None)


def test_determinism_fresh_returns_and_global_rng_state():
    random.seed(493)
    state = random.getstate()
    first = gen.generate(17, 9, difficulty="medium")
    assert random.getstate() == state
    second = gen.generate(17, 9, difficulty="medium")
    assert first == second
    assert first is not second and first[0] is not second[0]
    first[0][0] = 9 if first[0][0] != 9 else 0
    assert first != second
    assert second != gen.generate(18, 9, difficulty="medium")
    assert second != gen.generate(17, 10, difficulty="medium")


def test_self_check_rejects_targeted_impostors():
    valid = gen.generate(44, 1, scene_profile="medium_negative_10x12")
    assert gen.self_check(valid) == []

    malformed = [row[:] for row in valid]
    malformed[-1].pop()

    red_in_input = copy.deepcopy(valid)
    red_in_input[0][0] = 2

    missing_singleton = copy.deepcopy(valid)
    analysis = gen._analysis(missing_singleton)
    singleton = analysis["singleton_color"]
    for row in range(len(missing_singleton)):
        for col in range(len(missing_singleton[0])):
            if missing_singleton[row][col] == singleton:
                missing_singleton[row][col] = 0

    no_target = [[0] * 8 for _ in range(8)]
    no_target[0][0] = 1
    no_target[2][2] = no_target[2][3] = no_target[3][2] = 3
    no_target[7][7] = 4

    out_of_range = copy.deepcopy(valid)
    out_of_range[0][0] = 10

    two_main_colors = copy.deepcopy(valid)
    main = analysis["main_color"]
    changed = False
    for row in range(len(two_main_colors)):
        for col in range(len(two_main_colors[0])):
            if two_main_colors[row][col] == main:
                two_main_colors[row][col] = analysis["singleton_color"]
                changed = True
                break
        if changed:
            break

    for impostor in (
        malformed,
        red_in_input,
        missing_singleton,
        no_target,
        out_of_range,
        two_main_colors,
    ):
        assert gen.self_check(impostor)


def test_negative_recombinations_are_unchanged_and_oracle_executable():
    blue_negative = gen.generate(
        501, 1, difficulty="easy", scene_profile="easy_negative_8x9"
    )
    analysis = gen._analysis(blue_negative)
    before_irregular = {
        cell: blue_negative[cell[0]][cell[1]]
        for component in analysis["irregular"]
        for cell in component["cells"]
    }
    blue_output = gen.rule_mirror(blue_negative)
    assert all(blue_output[row][col] == value for (row, col), value in before_irregular.items())
    assert gen._rival_bbox_corners_all_blue_components(blue_negative) != blue_output

    wrong_color_negative = gen.generate(
        502, 1, difficulty="medium", scene_profile="medium_negative_10x12"
    )
    analysis = gen._analysis(wrong_color_negative)
    main_cells = {
        cell: wrong_color_negative[cell[0]][cell[1]]
        for component in analysis["main_components"]
        for cell in component["cells"]
    }
    wrong_color_output = gen.rule_mirror(wrong_color_negative)
    assert all(
        wrong_color_output[row][col] == value
        for (row, col), value in main_cells.items()
    )
    assert gen._rival_all_solid_rectangles_any_color(wrong_color_negative) != wrong_color_output

    # A lawful rule input outside the nine linked teaching profiles proves the
    # authority/teaching boundary: execution remains defined, but it is not
    # admitted as an ordinary lesson.
    recombined = [row[:] for row in gen.generate(503, 0, scene_profile="easy_pair_8x10")]
    recombined.append([0] * len(recombined[0]))
    assert gen.self_check(recombined) == []
    assert gen.teaching_check(recombined)
    assert gen.strict_canonical_like(recombined)
    result = gen.rule_mirror(recombined)
    assert len(result) == len(recombined) and result != recombined


def test_every_sliding_lesson_refutes_every_named_competitor():
    for band in ("easy", "medium", "hard"):
        for start in range(18):
            demos, query = _episode(91_000 + start, start, band)
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(
                    rival(demo["input"]) != demo["output"] for demo in demos
                ), (band, start, name)


def test_semantic_witnesses_cover_each_band_schedule():
    for band in ("easy", "medium", "hard"):
        grids = [gen.generate(400 + index, index, difficulty=band) for index in range(18)]
        for name, witness in gen.SEMANTIC_WITNESSES.items():
            assert any(witness(grid) for grid in grids), (band, name)
        for witness_name, rival_names in gen.WITNESS_RIVALS.items():
            witness = gen.SEMANTIC_WITNESSES[witness_name]
            for grid in grids:
                if witness(grid):
                    authority = gen.rule_mirror(grid)
                    for rival_name in rival_names:
                        assert gen.SEMANTIC_RIVALS[rival_name](grid) != authority, (
                            band,
                            witness_name,
                            rival_name,
                        )


def _role_mask(grid):
    analysis = gen._analysis(grid)
    assert analysis["errors"] == []
    return tuple(
        (
            "blue" if value == 1 else "singleton" if analysis["counts"][value] == 1 else "distractor",
            row,
            col,
        )
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    )


def test_each_profile_randomizes_component_positions_beyond_reflection_orbit():
    for profile in gen.SCENE_PROFILES:
        band, _template = gen._PROFILE_BY_NAME[profile]
        layouts = {
            _role_mask(
                gen.generate(seed, 0, difficulty=band, scene_profile=profile)
            )
            for seed in range(96)
        }
        assert len(layouts) >= 8, (profile, len(layouts))


def test_every_cyclic_four_pair_window_is_identifiable_under_query_rotation():
    for band in ("easy", "medium", "hard"):
        for start in range(3):
            pairs = []
            for offset in range(4):
                grid = gen.generate(77, start + offset, difficulty=band)
                pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
            for query_index, query in enumerate(pairs):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                assert gen.lesson_identifiable(demos, {"input": query["input"]}) == [], (
                    band,
                    start,
                    query_index,
                    gen.lesson_identifiable(demos, {"input": query["input"]}),
                )
