"""Focused regression tests for generator c5a69e7cd8c8."""
from __future__ import annotations

import hashlib
import importlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "c5a69e7cd8c8"
try:
    GENERATOR = importlib.import_module(
        f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
    )
except ModuleNotFoundError:
    generator_path = Path(__file__).resolve().parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location(
        f"task_generator_{TASK_ID}", generator_path
    )
    assert spec is not None and spec.loader is not None
    GENERATOR = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = GENERATOR
    spec.loader.exec_module(GENERATOR)

ROOT = find_root(__file__)


def _canonical_program() -> str:
    path = Path(ROOT) / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row["program_solution"]
    raise AssertionError(f"canonical task {TASK_ID} not found")


def _pair(grid):
    return {"input": grid, "output": GENERATOR.rule_mirror(grid)}


def test_rule_hash_canonical_acceptance_and_python_oracle():
    digest = hashlib.sha256(
        " ".join(_canonical_program().split()).encode("utf-8")
    ).hexdigest()[:12]
    assert GENERATOR.RULE_HASH == digest == "bf2554f59664"

    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 4
    for pair in pairs:
        source = pair["input"]
        snapshot = [row[:] for row in source]
        assert GENERATOR.self_check(source) == []
        assert GENERATOR.strict_canonical_like(source) == []
        assert GENERATOR.rule_mirror(source) == pair["output"]
        assert source == snapshot


def test_advertised_axes_are_exact_and_unknown_calls_fail_closed():
    assert tuple(GENERATOR.AXES) == (
        "canvas",
        "opening",
        "support_depth",
        "palette",
        "anchor",
        "lateral",
        "n_extras",
    )
    assert GENERATOR.INCOMPATIBLE_OVERRIDE_COMBINATIONS == ()

    cases = []
    canvases = tuple(GENERATOR.CANVAS_DIMS)
    palettes = tuple(GENERATOR.PALETTES)
    depth_lo, depth_hi = (
        int(part)
        for part in GENERATOR.AXES["support_depth"]["valid"].split("..")
    )
    for index, canvas in enumerate(canvases):
        cases.append(
            {
                "canvas": canvas,
                "opening": GENERATOR.OPENINGS[index % len(GENERATOR.OPENINGS)],
                "support_depth": depth_lo + index % (depth_hi - depth_lo + 1),
                "palette": palettes[index % len(palettes)],
                "anchor": GENERATOR.ANCHORS[index % len(GENERATOR.ANCHORS)],
                "lateral": GENERATOR.LATERALS[index % len(GENERATOR.LATERALS)],
                "n_extras": index % 6,
            }
        )
    # Boundary-heavy combinations exercise each opening at maximum depth and extras.
    for index, opening in enumerate(GENERATOR.OPENINGS):
        cases.append(
            {
                "canvas": canvases[index % len(canvases)],
                "opening": opening,
                "support_depth": depth_hi,
                "palette": palettes[-1 - index % len(palettes)],
                "anchor": GENERATOR.ANCHORS[-1 - index % len(GENERATOR.ANCHORS)],
                "lateral": GENERATOR.LATERALS[-1 - index % len(GENERATOR.LATERALS)],
                "n_extras": 5,
            }
        )

    for band in ("easy", "medium", "hard"):
        for index, overrides in enumerate(cases):
            grid = GENERATOR.generate(
                30_000 + index,
                700 + index,
                difficulty=band,
                **overrides,
            )
            assert GENERATOR.self_check(grid) == []
            assert GENERATOR.observe_overrides(grid) == overrides

    with pytest.raises((TypeError, ValueError), match="unknown override"):
        GENERATOR.generate(1, 2, unknown_axis=3)
    with pytest.raises(ValueError, match="difficulty"):
        GENERATOR.generate(1, 2, difficulty="nightmare")
    with pytest.raises((TypeError, ValueError), match="support_depth"):
        GENERATOR.generate(1, 2, support_depth=True)
    with pytest.raises((TypeError, ValueError), match="canvas"):
        GENERATOR.generate(1, 2, canvas="99x99")


def test_every_advertised_geometric_cross_product_is_pixel_decodable():
    lo, hi = (
        int(part)
        for part in GENERATOR.AXES["support_depth"]["valid"].split("..")
    )
    for canvas, (height, width) in GENERATOR.CANVAS_DIMS.items():
        for opening in GENERATOR.OPENINGS:
            lateral_length = width if opening in ("up", "down") else height
            for depth in range(lo, hi + 1):
                positions = GENERATOR._lateral_positions(lateral_length, depth)
                assert len(set(positions.values())) == len(GENERATOR.LATERALS), (
                    canvas,
                    opening,
                    depth,
                    positions,
                )
                for lateral in GENERATOR.LATERALS:
                    overrides = {
                        "canvas": canvas,
                        "opening": opening,
                        "support_depth": depth,
                        "lateral": lateral,
                    }
                    grid = GENERATOR.generate(44_000, 5, **overrides)
                    observed = GENERATOR.observe_overrides(grid)
                    assert {
                        name: observed[name] for name in overrides
                    } == overrides


def test_default_schedule_has_canonical_support_and_broad_observable_coverage():
    canonical_profiles = {(12, 12, 3), (10, 15, 3), (15, 12, 3), (16, 11, 3)}
    for band_index, band in enumerate(("easy", "medium", "hard")):
        grids = [
            GENERATOR.generate(100_000 + band_index, index, difficulty=band)
            for index in range(GENERATOR.LESSON_SCHEDULE_PERIOD * 3)
        ]
        observations = [GENERATOR.observe_overrides(grid) for grid in grids]
        assert {obs["opening"] for obs in observations} == set(GENERATOR.OPENINGS)
        assert {obs["support_depth"] for obs in observations} == {2, 3}
        assert {obs["anchor"] for obs in observations} == set(GENERATOR.ANCHORS)
        assert {obs["lateral"] for obs in observations} == set(GENERATOR.LATERALS)
        assert {obs["n_extras"] for obs in observations} >= {0, 1, 2, 3, 4, 5}
        profiles = {
            (len(grid), len(grid[0]), len({value for row in grid for value in row}))
            for grid in grids
        }
        assert profiles & canonical_profiles
        assert len({json.dumps(grid, separators=(",", ":")) for grid in grids}) >= 20


def test_canonical_shortcuts_fit_canonical_but_fail_generated_witnesses():
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert set(GENERATOR.CANONICAL_SHORTCUTS) == {
        "canonical_triangle_only",
        "palette_direction_lookup",
    }
    assert set(GENERATOR.LESSON_COMPETITORS) >= set(GENERATOR.CANONICAL_SHORTCUTS)
    for name, rival in GENERATOR.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name

    grids = [GENERATOR.generate(222_000, index, difficulty="medium") for index in range(8)]
    for name, rival in GENERATOR.CANONICAL_SHORTCUTS.items():
        assert any(rival(grid) != GENERATOR.rule_mirror(grid) for grid in grids), name
    for name, witness in GENERATOR.SEMANTIC_WITNESSES.items():
        assert any(witness(grid) for grid in grids), name


def test_every_semantic_witness_names_the_rivals_it_proves_wrong():
    expected = {
        "noncanonical_support_refutes_exact_triangle_only": [
            "canonical_triangle_only"
        ],
        "palette_is_decoupled_from_direction": ["palette_direction_lookup"],
        "ray_is_opposite_the_open_side": ["through_open_side"],
        "ray_skips_support_and_continues": ["stop_at_support", "overwrite_support"],
    }
    assert GENERATOR.WITNESS_RIVALS == expected

    grids = [
        GENERATOR.generate(333_000, index, difficulty=band)
        for band in ("easy", "medium", "hard")
        for index in range(GENERATOR.LESSON_SCHEDULE_PERIOD)
    ]
    for witness_name, rival_names in expected.items():
        witness = GENERATOR.SEMANTIC_WITNESSES[witness_name]
        firing = [grid for grid in grids if witness(grid)]
        assert firing, witness_name
        for rival_name in rival_names:
            rival = GENERATOR.SEMANTIC_RIVALS[rival_name]
            assert any(
                rival(grid) != GENERATOR.rule_mirror(grid) for grid in firing
            ), (witness_name, rival_name)


def test_every_four_example_window_is_identifiable_under_all_query_rotations():
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for start in range(GENERATOR.LESSON_SCHEDULE_PERIOD):
            seed = 500_000 + band_index * 10_000 + start
            pairs = [
                _pair(GENERATOR.generate(seed, start + offset, difficulty=band))
                for offset in range(4)
            ]
            for query_index in range(4):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                query = pairs[query_index]
                assert GENERATOR.lesson_identifiable(demos, query) == [], (
                    band,
                    start,
                    query_index,
                )
                for name, rival in GENERATOR.LESSON_COMPETITORS.items():
                    assert any(
                        rival(demo["input"]) != demo["output"] for demo in demos
                    ), (band, start, query_index, name)


def test_self_check_rejects_structural_impostors():
    valid = GENERATOR.generate(777, 3, difficulty="medium")
    assert GENERATOR.self_check(valid) == []

    ragged = [row[:] for row in valid]
    ragged[0] = ragged[0][:-1]
    assert GENERATOR.self_check(ragged)

    analysis = GENERATOR.analyze(valid)
    sr, sc = analysis["singleton_position"]
    odr, odc = GENERATOR.DIRECTIONS[analysis["opening"]]

    blocked_opening = [row[:] for row in valid]
    blocked_opening[sr + odr][sc + odc] = analysis["support_color"]
    assert GENERATOR.self_check(blocked_opening)

    second_opening = [row[:] for row in valid]
    # Remove one of the three support neighbours, creating two open sides.
    for name, (dr, dc) in GENERATOR.DIRECTIONS.items():
        if name != analysis["opening"]:
            second_opening[sr + dr][sc + dc] = 0
            break
    assert GENERATOR.self_check(second_opening)

    duplicate_singleton = [row[:] for row in valid]
    duplicate_singleton[0][0] = analysis["singleton_color"]
    assert GENERATOR.self_check(duplicate_singleton)


def test_rule_mirror_skips_support_without_overwriting_or_mutating():
    grid = GENERATOR.generate(
        999,
        0,
        difficulty="hard",
        canvas="12x18",
        opening="left",
        support_depth=3,
        palette="6_9",
        anchor="middle",
        lateral="middle",
        n_extras=5,
    )
    before = [row[:] for row in grid]
    output = GENERATOR.rule_mirror(grid)
    analysis = GENERATOR.analyze(grid)
    assert grid == before
    assert output != grid
    assert GENERATOR.SEMANTIC_RIVALS["stop_at_support"](grid) == grid
    assert GENERATOR.SEMANTIC_RIVALS["overwrite_support"](grid) != output
    assert all(
        output[r][c] == analysis["support_color"]
        for r, c in analysis["support_cells"]
    )
