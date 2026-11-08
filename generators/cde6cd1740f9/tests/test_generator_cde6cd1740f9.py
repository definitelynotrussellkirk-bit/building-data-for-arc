from __future__ import annotations

import hashlib
import json
import random
from collections import Counter
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs as read_canonical_pairs
from reviewer_support import find_root, load_selected_generator


RUNTIME_ROOT = find_root(__file__)
generator, GENERATOR_SOURCE, GENERATOR_SHA256 = load_selected_generator(
    "cde6cd1740f9", root=RUNTIME_ROOT
)


def canonical_pairs():
    seen = set()
    pairs = []
    for pair in read_canonical_pairs(
        generator.TASK_ID, root=RUNTIME_ROOT, labeled_only=True
    ):
        key = (
            tuple(map(tuple, pair["input"])),
            tuple(map(tuple, pair["output"])),
        )
        if key not in seen:
            seen.add(key)
            pairs.append({"input": pair["input"], "output": pair["output"]})
    return pairs


def test_rule_hash_and_all_canonical_pairs_are_exact():
    assert generator.RULE_HASH == "027335bb451f"
    pairs = canonical_pairs()
    assert len(pairs) == 4
    signatures = set()
    for pair in pairs:
        before = [row[:] for row in pair["input"]]
        assert generator.self_check(pair["input"]) == []
        assert generator.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before
        signatures.add(generator.canonical_profile_signature(pair["input"]))
    assert signatures == {
        (16, 11, 2),
        (16, 13, 2),
        (21, 9, 4),
        (30, 10, 4),
    }


def test_every_nine_sample_window_is_identifiable_in_every_band():
    expected_schedule = {
        (profile, structure)
        for profile in generator.PROFILES
        for structure in generator.STRUCTURES
    }
    assert generator.EXAMPLES_NEEDED == 9
    assert generator.LESSON_SCHEDULE_PERIOD == 20

    for band in ("easy", "medium", "hard"):
        assert {
            generator.schedule_profile(0, sample_index, difficulty=band)
            for sample_index in range(generator.LESSON_SCHEDULE_PERIOD)
        } == expected_schedule
        for sample_index in range(generator.LESSON_SCHEDULE_PERIOD):
            assert generator.schedule_profile(
                0, sample_index, difficulty=band
            ) == generator.schedule_profile(
                999,
                sample_index + generator.LESSON_SCHEDULE_PERIOD,
                difficulty=band,
            )

        for seed in (0, 7, 101):
            for start in range(generator.LESSON_SCHEDULE_PERIOD):
                demos = []
                for sample_index in range(start, start + generator.EXAMPLES_NEEDED):
                    grid = generator.generate(seed, sample_index, difficulty=band)
                    demos.append({"input": grid, "output": generator.rule_mirror(grid)})
                query_grid = generator.generate(
                    seed, start + generator.EXAMPLES_NEEDED, difficulty=band
                )
                query = {"input": query_grid, "output": generator.rule_mirror(query_grid)}
                assert generator.lesson_identifiable(demos, query) == []
                signatures = [generator.semantic_signature(pair["input"]) for pair in demos]
                assert {signature["profile"] for signature in signatures} == set(
                    generator.PROFILES
                )
                assert {signature["structure"] for signature in signatures} == set(
                    generator.STRUCTURES
                )
                assert all(
                    any(predicate(pair["input"]) for pair in demos)
                    for predicate in generator.SEMANTIC_WITNESSES.values()
                )
                assert all(
                    any(competitor(pair["input"]) != pair["output"] for pair in demos)
                    for competitor in generator.LESSON_COMPETITORS.values()
                )


def test_every_query_rotation_of_ten_pair_window_is_identifiable():
    for band in ("easy", "medium", "hard"):
        for seed in (0, 7, 101):
            for start in range(generator.LESSON_SCHEDULE_PERIOD):
                pairs = []
                for sample_index in range(start, start + generator.EXAMPLES_NEEDED + 1):
                    grid = generator.generate(seed, sample_index, difficulty=band)
                    pairs.append({"input": grid, "output": generator.rule_mirror(grid)})
                for query_index, query in enumerate(pairs):
                    demos = [
                        pair for index, pair in enumerate(pairs) if index != query_index
                    ]
                    assert generator.lesson_identifiable(demos, query) == []
                    assert all(
                        any(
                            competitor(pair["input"]) != pair["output"]
                            for pair in demos
                        )
                        for competitor in generator.LESSON_COMPETITORS.values()
                    )


def test_canvas_template_shortcut_fits_canonical_but_not_ordinary_lessons():
    rival = generator.CANONICAL_SHORTCUTS["canvas_template"]
    assert all(rival(pair["input"]) == pair["output"] for pair in canonical_pairs())
    for band in ("easy", "medium", "hard"):
        for start in range(generator.LESSON_SCHEDULE_PERIOD):
            demos = []
            for sample_index in range(start, start + generator.EXAMPLES_NEEDED):
                grid = generator.generate(73, sample_index, difficulty=band)
                demos.append({"input": grid, "output": generator.rule_mirror(grid)})
            assert any(rival(pair["input"]) != pair["output"] for pair in demos)


def test_retained_cross_canvas_counterexample_refutes_canvas_template():
    fixture_path = (
        Path(__file__).parents[1]
        / "counterexamples"
        / "canvas_template_cross_canvas.json"
    )
    record = json.loads(fixture_path.read_text(encoding="utf-8"))
    grid = record["input"]
    assert record["generator_sha256"] == hashlib.sha256(
        Path(generator.__file__).read_bytes()
    ).hexdigest()
    assert generator.generate(
        record["seed"],
        record["sample_index"],
        **record["generation_arguments"],
    ) == grid
    expected = generator.rule_mirror(grid)
    rival = generator.CANONICAL_SHORTCUTS["canvas_template"](grid)
    assert generator.self_check(grid) == []
    assert generator.observe_overrides(grid) == record["observed_axes"]
    assert expected == record["expected_output"]
    assert rival == record["rival_output"]
    assert rival != expected


def test_forced_axis_values_and_boundary_crosses_are_exact():
    for profile in generator.PROFILES:
        for structure in generator.STRUCTURES:
            for active_columns in (1, 2):
                for primary_color in generator.PRIMARY_COLORS:
                    for layout_shift in (0, 1, 2):
                        grid = generator.generate(
                            53,
                            17,
                            difficulty="hard",
                            profile=profile,
                            structure=structure,
                            active_columns=active_columns,
                            primary_color=primary_color,
                            layout_shift=layout_shift,
                        )
                        expected = {
                            "profile": profile,
                            "structure": structure,
                            "active_columns": active_columns,
                            "primary_color": primary_color,
                            "layout_shift": layout_shift,
                        }
                        assert generator.self_check(
                            grid,
                            meta={"overrides": expected},
                        ) == []
                        assert generator.observe_overrides(grid) == expected
    with pytest.raises(ValueError, match="unknown override"):
        generator.generate(1, 2, grid_h=16)
    with pytest.raises(ValueError):
        generator.generate(1, 2, profile="12x12")
    with pytest.raises(ValueError):
        generator.generate(1, 2, structure="not-a-structure")
    with pytest.raises(ValueError):
        generator.generate(1, 2, active_columns=3)
    with pytest.raises(ValueError):
        generator.generate(1, 2, primary_color=0)
    with pytest.raises(ValueError):
        generator.generate(1, 2, layout_shift=3)


def test_default_distribution_crosses_canvas_and_structure_without_collapse():
    expected = {
        "k2_solid": ((2,), (1,), 2, 1),
        "k3_solid": ((3,), (1,), 2, 1),
        "k3_three_color": ((3,), (3,), 4, 1),
        "mixed_k3_k2": ((3, 2), (2, 1), 4, 2),
        "mixed_k3_k2_8_1": ((3, 2), (2, 1), 4, 2),
    }
    canonical_anchors = {
        "16x11": "k2_solid",
        "16x13": "k3_solid",
        "21x9": "k3_three_color",
        "30x10": "mixed_k3_k2",
    }
    all_pairs = {
        (profile, structure)
        for profile in generator.PROFILES
        for structure in generator.STRUCTURES
    }
    for band in ("easy", "medium", "hard"):
        observed_pairs = Counter()
        unique_pairs = set()
        for sample_index in range(160):
            grid = generator.generate(811, sample_index, difficulty=band)
            assert generator.self_check(grid) == []
            assert generator.strict_canonical_like(grid) == []
            signature = generator.semantic_signature(grid)
            expected_sizes, expected_color_counts, palette_size, active = expected[
                signature["structure"]
            ]
            assert signature["column_sizes"] == expected_sizes
            assert signature["layer_color_counts"] == expected_color_counts
            assert signature["palette_size"] == palette_size
            assert signature["active_columns"] == active
            observed_pairs[(signature["profile"], signature["structure"])] += 1
            unique_pairs.add(
                (
                    tuple(map(tuple, grid)),
                    tuple(map(tuple, generator.rule_mirror(grid))),
                )
            )
        assert set(observed_pairs) == all_pairs
        assert max(observed_pairs.values()) - min(observed_pairs.values()) == 0
        assert all(observed_pairs[(profile, structure)] == 160 // len(all_pairs)
                   for profile, structure in all_pairs)
        assert all(observed_pairs[(profile, structure)] for profile, structure in canonical_anchors.items())
        assert len(unique_pairs) >= 150


def test_color_counts_are_preserved_as_complete_layers():
    for band in ("easy", "medium", "hard"):
        for seed in range(40):
            grid = generator.generate(seed, seed * 19 + 3, difficulty=band)
            output = generator.rule_mirror(grid)
            info, errors = generator._analyze(grid)
            assert errors == []
            for column in info["columns"]:
                in_counts = Counter(value for _row, value in column["cells"])
                out_counts = Counter(
                    output[row][col]
                    for row in range(info["height"])
                    for col in range(info["width"])
                    if output[row][col] != 0
                    and column["span"][0] <= col <= column["span"][1]
                )
                assert out_counts == in_counts


def test_self_check_rejects_old_incoherent_and_minimal_impostors():
    incoherent = [[0] * 11 for _ in range(16)]
    for row, color in ((0, 1), (3, 1), (6, 2), (9, 2)):
        incoherent[row][5] = color
    assert any("do not partition complete" in error for error in generator.self_check(incoherent))

    all_background = [[0] * 11 for _ in range(16)]
    singleton = [[0] * 11 for _ in range(16)]
    singleton[2][5] = 3
    short_line = [[0] * 11 for _ in range(16)]
    short_line[2][5] = short_line[3][5] = 3
    solid_2x2 = [[0] * 11 for _ in range(16)]
    for row in (2, 3):
        for col in (5, 6):
            solid_2x2[row][col] = 3
    full_one_color = [[3] * 11 for _ in range(16)]
    for grid in (all_background, singleton, short_line, solid_2x2, full_one_color):
        assert generator.self_check(grid)


def test_overlapping_output_footprints_are_rejected():
    grid = [[0] * 11 for _ in range(16)]
    for col, color in ((3, 1), (6, 2)):
        for row in (0, 1, 3, 4, 6, 8, 10, 11, 12):
            grid[row][col] = color
    assert any("overlap" in error for error in generator.self_check(grid))


def test_determinism_freshness_and_global_random_state():
    random.seed(9321)
    state = random.getstate()
    first = generator.generate(73, 91, difficulty="medium")
    assert random.getstate() == state
    second = generator.generate(73, 91, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9
    assert first != second
    assert generator.generate(73, 91, difficulty="medium") == second


def test_different_seeds_change_scatter_without_changing_profile_semantics():
    for sample_index in range(4):
        left = generator.generate(101, sample_index, difficulty="easy")
        right = generator.generate(102, sample_index, difficulty="easy")
        assert left != right
        left_signature = generator.semantic_signature(left)
        right_signature = generator.semantic_signature(right)
        assert left_signature["profile"] == right_signature["profile"]
        assert left_signature["column_sizes"] == right_signature["column_sizes"]
        assert left_signature["layer_color_counts"] == right_signature["layer_color_counts"]
