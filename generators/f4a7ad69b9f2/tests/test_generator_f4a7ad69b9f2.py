from __future__ import annotations

import importlib
import random
from copy import deepcopy

import pytest

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash


TASK_ID = "f4a7ad69b9f2"
gen = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)


def test_rule_pin_and_python_mirror_match_every_canonical_pair():
    assert gen.RULE_HASH == canonical_rule_hash(TASK_ID) == "16e822df83e5"
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]

    # The official test input intentionally has the 1-cell color-3 object
    # touching the color-5 frame.  Monochrome components remain distinct.
    assert gen.self_check(pairs[-1]["input"]) == []


def test_canonical_color_tiebreak_shortcut_survives_official_but_generated_kills_it():
    pairs = canonical_pairs(TASK_ID)
    assert all(
        gen._rival_width_height_color(pair["input"]) == pair["output"]
        for pair in pairs
    )

    killers = [
        gen.generate(
            8800 + i,
            i,
            difficulty="medium",
            lesson_profile="lex_shape",
        )
        for i in range(12)
    ]
    assert all(gen.observe_overrides(grid)["lesson_profile"] == "lex_shape" for grid in killers)
    assert all(gen._lex_shape_witness(grid) for grid in killers)
    assert all(gen._rival_width_height_color(grid) != gen.rule_mirror(grid) for grid in killers)


def test_every_production_window_contains_all_decisive_profiles():
    period = len(gen._SCHEDULE)
    grids = [
        gen.generate(1701, index, difficulty="medium")
        for index in range(period * 4)
    ]
    observed = [gen.observe_overrides(grid)["lesson_profile"] for grid in grids]
    assert observed[: period * 2] == list(gen._SCHEDULE) * 2

    required_witnesses = (
        gen._width_primary_witness,
        gen._height_tie_witness,
        gen._lex_shape_witness,
        gen._lex_color_witness,
    )
    for start in range(period * 2):
        window = grids[start : start + gen.EXAMPLES_NEEDED]
        assert all(any(witness(grid) for grid in window) for witness in required_witnesses)
        demos = [{"input": grid, "output": gen.rule_mirror(grid)} for grid in window]
        query_grid = grids[start + gen.EXAMPLES_NEEDED]
        query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
        assert gen.lesson_identifiable(demos, query) == []


def test_curriculum_fits_serializable_lesson_contract():
    assert 2 <= gen.EXAMPLES_NEEDED <= 5


def test_width_profiles_each_refute_width_and_height_shortcuts():
    for profile in ("width_primary", "height_tie"):
        for index in range(24):
            grid = gen.generate(
                2801 + index,
                index,
                difficulty=("easy", "medium", "hard")[index % 3],
                lesson_profile=profile,
            )
            assert gen._width_primary_witness(grid)
            assert gen._height_tie_witness(grid)


def test_every_query_rotation_retains_all_decisive_profiles():
    period = len(gen._SCHEDULE)
    for start in range(period):
        grids = [
            gen.generate(2701, start + offset, difficulty="medium")
            for offset in range(gen.EXAMPLES_NEEDED + 1)
        ]
        pairs = [
            {"input": grid, "output": gen.rule_mirror(grid)}
            for grid in grids
        ]
        for query_index, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert gen.lesson_identifiable(demos, query) == [], (
                start,
                query_index,
                [gen.observe_overrides(pair["input"])["lesson_profile"] for pair in pairs],
                gen.lesson_identifiable(demos, query),
            )


def test_each_semantic_branch_has_positive_witness_and_named_rival_disagreement():
    grids = {
        profile: gen.generate(
            314159,
            index,
            difficulty="hard",
            lesson_profile=profile,
        )
        for index, profile in enumerate(gen.LESSON_PROFILES)
    }
    assert gen._width_primary_witness(grids["width_primary"])
    assert gen._height_tie_witness(grids["height_tie"])
    assert gen._lex_shape_witness(grids["lex_shape"])
    assert gen._lex_color_witness(grids["lex_color"])
    for grid in grids.values():
        assert gen._left_to_right_witness(grid)
        assert gen._top_alignment_witness(grid)
        assert gen._gap_witness(grid)


def test_exact_overrides_are_observable_in_every_band_and_unknown_keys_reject():
    for difficulty in ("easy", "medium", "hard"):
        for canvas in gen.CANVAS_PROFILES:
            for profile in gen.LESSON_PROFILES:
                grid = gen.generate(
                    9917,
                    23,
                    difficulty=difficulty,
                    canvas=canvas,
                    lesson_profile=profile,
                )
                assert gen.self_check(grid) == []
                assert gen.observe_overrides(grid) == {
                    "canvas": canvas,
                    "lesson_profile": profile,
                }
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 2, unknown_axis="typo")
    with pytest.raises(ValueError):
        gen.generate(1, 2, canvas="30x30")
    with pytest.raises(ValueError):
        gen.generate(1, 2, lesson_profile="width_only")


def test_replay_is_deterministic_fresh_global_rng_pure_and_arc_bounded():
    random.seed(20260815)
    state = random.getstate()
    first = gen.generate(123, 456, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(123, 456, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second

    for band in ("easy", "medium", "hard"):
        for index in range(80):
            grid = gen.generate(40000 + index, index, difficulty=band)
            output = gen.rule_mirror(grid)
            assert gen.self_check(grid) == []
            assert len(grid) <= 30 and len(grid[0]) <= 30
            assert len(output) <= 30 and len(output[0]) <= 30


def test_self_check_rejects_structural_mutations_and_output_overflow():
    valid = gen.generate(777, 2, difficulty="medium")
    components = gen._components(valid)
    assert len(components) == 3

    missing_object = deepcopy(valid)
    for r, c in components[0]["cells"]:
        missing_object[r][c] = 0

    duplicate_color = deepcopy(valid)
    replacement = int(components[0]["color"])
    for r, c in components[1]["cells"]:
        duplicate_color[r][c] = replacement

    invalid_color = deepcopy(valid)
    r, c = components[0]["cells"][0]
    invalid_color[r][c] = 10

    ragged = deepcopy(valid)
    ragged[0] = ragged[0][:-1]

    overflow = [[0 for _ in range(30)] for _ in range(8)]
    for color, row in ((1, 0), (2, 3), (3, 6)):
        for col in range(10):
            overflow[row][col] = color

    fixtures = {
        "missing_object": missing_object,
        "duplicate_color": duplicate_color,
        "invalid_color": invalid_color,
        "ragged": ragged,
        "packed_output_overflow": overflow,
    }
    for name, grid in fixtures.items():
        assert gen.self_check(grid), name


def test_lex_shape_profile_requires_scanning_past_the_first_crop_cell():
    """The geometry tie-break must not collapse to first-cell then color."""
    for difficulty in ("easy", "medium", "hard"):
        for index in range(12):
            grid = gen.generate(
                610_000 + index,
                index,
                difficulty=difficulty,
                lesson_profile="lex_shape",
            )
            components = gen._components(grid)
            groups = {}
            for component in components:
                dimensions = (
                    int(component["height"]),
                    int(component["width"]),
                )
                groups.setdefault(dimensions, []).append(component)
            tied = next(group for group in groups.values() if len(group) == 2)
            crops = [gen._crop_flat(component) for component in tied]
            assert crops[0][:2] == crops[1][:2] == (0, 0)
            first_difference = next(
                position
                for position, (left, right) in enumerate(zip(*crops))
                if left != right
            )
            assert first_difference >= 2

            official_colors = [
                int(component["color"])
                for component in sorted(tied, key=gen._official_sort_key)
            ]
            shortcut_colors = [
                int(component["color"])
                for component in sorted(
                    tied,
                    key=lambda component: (
                        int(component["width"]),
                        int(component["height"]),
                        gen._crop_flat(component)[0],
                        int(component["color"]),
                    ),
                )
            ]
            assert shortcut_colors != official_colors


def test_first_cell_then_color_shortcut_is_declared_and_refuted():
    rival_name = "width_height_first_cell_then_color"
    assert rival_name in gen.SEMANTIC_RIVALS
    assert rival_name in gen.CANONICAL_SHORTCUTS
    assert rival_name in gen.WITNESS_RIVALS["lex_shape_signal"]

    rival = gen.SEMANTIC_RIVALS[rival_name]
    pairs = canonical_pairs(TASK_ID)
    assert all(rival(pair["input"]) == pair["output"] for pair in pairs)

    killers = [
        gen.generate(
            620_000 + index,
            index,
            difficulty=("easy", "medium", "hard")[index % 3],
            lesson_profile="lex_shape",
        )
        for index in range(36)
    ]
    assert all(gen._lex_shape_witness(grid) for grid in killers)
    assert all(rival(grid) != gen.rule_mirror(grid) for grid in killers)


def test_first_two_cells_then_color_shortcut_is_declared_and_refuted():
    rival_name = "width_height_first_two_cells_then_color"
    assert rival_name in gen.SEMANTIC_RIVALS
    assert rival_name in gen.CANONICAL_SHORTCUTS
    assert rival_name in gen.WITNESS_RIVALS["lex_shape_signal"]

    rival = gen.SEMANTIC_RIVALS[rival_name]
    pairs = canonical_pairs(TASK_ID)
    assert all(rival(pair["input"]) == pair["output"] for pair in pairs)

    killers = [
        gen.generate(
            630_000 + index,
            index,
            difficulty=("easy", "medium", "hard")[index % 3],
            lesson_profile="lex_shape",
        )
        for index in range(36)
    ]
    assert all(gen._lex_shape_witness(grid) for grid in killers)
    assert all(rival(grid) != gen.rule_mirror(grid) for grid in killers)
