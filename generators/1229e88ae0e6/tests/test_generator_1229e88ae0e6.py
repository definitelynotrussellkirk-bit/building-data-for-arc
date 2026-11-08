"""Focused regression tests for generator 1229e88ae0e6."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

from scripts.canonical_profile_gate import canonical_pairs


TASK_ID = "1229e88ae0e6"
ROOT = Path(__file__).resolve().parents[1]
gen = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)


def _canonical_program() -> str:
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row["program_solution"]
    raise AssertionError("canonical task row not found")


def _pair(grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def _sort_output_colors(grid, *, reverse=False):
    """Wrong rival: center correctly, then sort colors over occupied cells."""
    output = gen.rule_mirror(grid)
    cells = [
        (row, col)
        for row, values in enumerate(output)
        for col, value in enumerate(values)
        if value != 0
    ]
    colors = sorted(
        (output[row][col] for row, col in cells), reverse=reverse
    )
    rival = copy.deepcopy(output)
    for (row, col), color in zip(cells, colors):
        rival[row][col] = color
    return rival


def _pack_output_support(grid):
    """Wrong rival: preserve cell count/colors but pack holes row-major."""
    analysis = gen._basic_analysis(grid)
    target_row, target_col = analysis["target_origin"]
    colors = [grid[row][col] for row, col in analysis["cells"]]
    positions = [
        (row, col)
        for row in range(analysis["bbox_h"])
        for col in range(analysis["bbox_w"])
    ][: len(colors)]
    output = [
        [0 for _ in range(analysis["width"])]
        for _ in range(analysis["height"])
    ]
    for (row, col), color in zip(positions, colors):
        output[target_row + row][target_col + col] = color
    return output


def test_rule_hash_and_all_canonical_pairs():
    normalized = " ".join(_canonical_program().split())
    expected = hashlib.sha256(normalized.encode()).hexdigest()[:12]
    assert gen.RULE_HASH == expected == "5e5cb5402934"

    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("source_zone", tuple(gen._ZONES))
@pytest.mark.parametrize("color_mode", tuple(gen._COLOR_MODES))
def test_every_exact_override_is_observable_in_every_band(
    band, source_zone, color_mode
):
    requested = {"source_zone": source_zone, "color_mode": color_mode}
    grid = gen.generate(20260728, 17, difficulty=band, **requested)
    assert gen.self_check(grid, difficulty=band, meta=requested) == []
    assert gen.observe_overrides(grid) == requested
    assert gen.rule_mirror(grid) != grid


def test_ordinary_schedule_records_exact_observable_controls():
    for band in ("easy", "medium", "hard"):
        for seed in range(6):
            for sample_index in range(12):
                grid = gen.generate(seed, sample_index, difficulty=band)
                assert gen.observe_overrides(grid) == {
                    "source_zone": gen._scheduled_zone(sample_index, seed),
                    "color_mode": gen._scheduled_color_mode(seed, sample_index),
                }


def test_unknown_and_invalid_overrides_fail_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, texture="corner")
    with pytest.raises(ValueError, match="unknown source_zone"):
        gen.generate(1, 0, source_zone="center")
    with pytest.raises(ValueError, match="unknown color_mode"):
        gen.generate(1, 0, color_mode="rainbow")
    with pytest.raises(ValueError, match="unknown difficulty"):
        gen.generate(1, 0, difficulty="extreme")


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(91027)
    before = random.getstate()
    first = gen.generate(41, 8, difficulty="hard")
    middle = random.getstate()
    second = gen.generate(41, 8, difficulty="hard")
    after = random.getstate()
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    assert before == middle == after
    first[0][0] = 9 if first[0][0] != 9 else 1
    assert second == gen.generate(41, 8, difficulty="hard")


def test_self_check_rejects_four_targeted_impostors():
    short_line = [
        [4, 4, 4, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
    ]
    assert any("height and width" in error for error in gen.self_check(short_line))

    solid_2x2 = [
        [5, 5, 0, 0, 0, 0],
        [5, 5, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
    ]
    assert any("background hole" in error for error in gen.self_check(solid_2x2))

    disconnected = copy.deepcopy(short_line)
    disconnected[0] = [4, 4, 0, 0, 0, 0]
    disconnected[2][2] = 7
    assert any("not 4-connected" in error for error in gen.self_check(disconnected))

    already_centered = [
        [0, 0, 0, 0, 0, 0],
        [0, 0, 2, 2, 0, 0],
        [0, 0, 2, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
    ]
    assert any("already centered" in error for error in gen.self_check(already_centered))


def test_every_four_demo_sliding_window_is_identifiable():
    for band in ("easy", "medium", "hard"):
        for seed in range(8):
            pairs = [
                _pair(gen.generate(seed, index, difficulty=band))
                for index in range(20)
            ]
            for start in range(16):
                demos = pairs[start : start + gen.EXAMPLES_NEEDED]
                query = pairs[start + gen.EXAMPLES_NEEDED]
                assert gen.lesson_identifiable(demos, query) == []


def test_schedule_supplies_each_named_rival_killer():
    demos = [
        gen.generate(12, index, difficulty="medium")
        for index in range(gen.EXAMPLES_NEEDED)
    ]
    assert {gen.observe_overrides(grid)["source_zone"] for grid in demos} == set(
        gen._scheduled_zone(i, 12) for i in range(gen.EXAMPLES_NEEDED)
    )
    for witness_name, witness in gen.SEMANTIC_WITNESSES.items():
        assert any(witness(grid) for grid in demos), witness_name


def test_interior_source_is_a_border_shortcut_regression_witness():
    grid = gen.generate(
        77,
        (2 - (77 // 8)) % 4,  # Effective slot 2 is the seeded interior witness.
        difficulty="medium",
        source_zone="southeast",
        color_mode="multi",
    )
    analysis = gen._basic_analysis(grid)
    assert analysis["touches_border"] is False
    assert gen._rival_border_only(grid) == grid
    assert gen.rule_mirror(grid) != grid


def test_negative_recombination_is_rejected_by_the_teaching_grammar():
    grid = gen.generate(
        19,
        0,
        difficulty="medium",
        source_zone="northwest",
        color_mode="mono",
    )
    impostor = copy.deepcopy(grid)
    occupied = [
        (r, c)
        for r, row in enumerate(impostor)
        for c, value in enumerate(row)
        if value
    ]
    # Add a new, isolated color/component absent from the retained connected motif.
    target = (len(impostor) - 1, len(impostor[0]) - 1)
    assert all(abs(target[0] - r) + abs(target[1] - c) > 1 for r, c in occupied)
    impostor[target[0]][target[1]] = 9
    assert any("not 4-connected" in error for error in gen.self_check(impostor))


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_distribution_covers_canonical_axis_moves_and_canvas_sizes(band):
    """Catches the v2 all-diagonal / one-canvas-per-band support collapse."""
    cases = [gen.generate(20260927, i, difficulty=band) for i in range(256)]
    facts = [gen._basic_analysis(grid) for grid in cases]
    assert any(a["row_delta"] == 0 and a["col_delta"] != 0 for a in facts)
    assert any(a["col_delta"] == 0 and a["row_delta"] != 0 for a in facts)
    assert {(a["height"], a["width"]) for a in facts} == gen._CANONICAL_SHAPES
    assert any((a["height"] - a["bbox_h"]) % 2 == 0 and
               (a["width"] - a["bbox_w"]) % 2 == 0 for a in facts)
    assert all(gen.strict_canonical_like(grid) == [] for grid in cases)


@pytest.mark.parametrize("zone", ["north", "east", "south", "west"])
def test_axis_aligned_overrides_are_observable(zone):
    for band in ("easy", "medium", "hard"):
        grid = gen.generate(99, 13, difficulty=band, source_zone=zone)
        assert gen.observe_overrides(grid)["source_zone"] == zone
        a = gen._basic_analysis(grid)
        assert (a["row_delta"] == 0) != (a["col_delta"] == 0)


def test_hard_morphology_is_not_eight_transformed_templates():
    supports = set()
    counts = set()
    for index in range(512):
        grid = gen.generate(20260927, index, difficulty="hard")
        a = gen._basic_analysis(grid)
        r0, c0, _, _ = a["bbox"]
        supports.add(tuple((r-r0, c-c0) for r, c in a["cells"]))
        counts.add(len(a["cells"]))
    assert len(supports) >= 50
    assert {3, 4, 5, 6, 7, 8} <= counts


def test_axis_only_blind_rival_is_exposed_by_ordinary_lessons():
    def diagonal_only(grid):
        a = gen._basic_analysis(grid)
        return gen.rule_mirror(grid) if a["row_delta"] and a["col_delta"] else grid
    for band in ("easy", "medium", "hard"):
        cases = [gen.generate(7, i, difficulty=band) for i in range(20)]
        for start in range(16):
            assert any(diagonal_only(g) != gen.rule_mirror(g)
                       for g in cases[start:start+gen.EXAMPLES_NEEDED])


def test_real_episode_query_index_covers_all_eight_source_directions():
    # Episode generation starts at zero: train indices 0..3, query at 4.
    # Sliding-window coverage alone missed a permanent query-direction bias.
    for band in ("easy", "medium", "hard"):
        seen = {gen.observe_overrides(gen.generate(seed, 4, difficulty=band))["source_zone"]
                for seed in range(32)}
        assert seen == set(gen._ZONES)


def test_query_direction_and_color_mode_are_not_coupled():
    seen = {tuple(gen.observe_overrides(gen.generate(seed, 4)).values())
            for seed in range(64)}
    assert seen == {(zone, mode) for zone in gen._ZONES for mode in gen._COLOR_MODES}


def test_all_override_layouts_exist_at_every_curriculum_slot():
    for band in ("easy", "medium", "hard"):
        for zone in gen._ZONES:
            for slot in range(4):
                layouts = gen._layouts(band, zone, slot)
                assert layouts, (band, zone, slot)
                for h, w, bh, bw, counts, origins in layouts:
                    assert counts and origins
                    assert all(gen._motifs(bh, bw, count) for count in counts)
                    for r, c in origins:
                        assert (gen._sign(r-(h-bh)//2), gen._sign(c-(w-bw)//2)) == gen._ZONE_SIGNS[zone]
                        if slot == 0:
                            assert (h-bh)%2 or (w-bw)%2
                            assert max(abs(r-(h-bh)//2), abs(c-(w-bw)//2)) >= 2
                        if slot == 2:
                            assert 0 < r < h-bh and 0 < c < w-bw


def test_missing_single_axis_demonstrations_are_rejected():
    # Contains multicolor, holes, interior, odd-slack and long-move evidence,
    # but all four demonstrations move diagonally. Do not accept this lesson.
    demos = [_pair(gen.generate(0, i)) for i in (0, 2, 4, 6)]
    query = _pair(gen.generate(0, 1))
    reasons = gen.lesson_identifiable(demos, query)
    assert any("single_axis" in reason or "diagonal_sources" in reason for reason in reasons)


def test_color_frequencies_are_not_forced_to_be_equal():
    from collections import Counter
    differences = []
    for i in range(256):
        grid = gen.generate(41, i, difficulty="hard", color_mode="multi")
        counts = Counter(v for row in grid for v in row if v)
        differences.append(max(counts.values())-min(counts.values()))
    assert max(differences) >= 2


def test_horizontal_flip_can_leave_the_nonidentity_teaching_domain():
    grid = [[0]*5 for _ in range(5)]
    grid[1][2] = grid[1][3] = grid[2][2] = 2
    assert gen.self_check(grid) == []
    flipped = [row[::-1] for row in grid]
    assert any("already centered" in error for error in gen.self_check(flipped))


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_northwest_queries_are_not_always_border_sources(band):
    # The first repair phased directions and witness roles together, retaining
    # a source-direction -> border-status shortcut. Phase them independently.
    northwest = []
    for seed in range(128):
        grid = gen.generate(seed, 4, difficulty=band)
        a = gen._basic_analysis(grid)
        if a["source_zone"] == "northwest":
            northwest.append(a)
    assert northwest
    assert any(not a["touches_border"] for a in northwest)
    assert any(a["touches_border"] for a in northwest)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_color_binding_witness_slot_refutes_palette_order_shortcuts(band):
    """Multicolor evidence must bind each color to its original motif cell."""
    for seed in [*range(32), -1, 2**63 + 3]:
        phase = (seed // 8 + seed // 32) % 4
        sample_index = (1 - phase) % 4
        grid = gen.generate(seed, sample_index, difficulty=band)
        assert gen.observe_overrides(grid)["color_mode"] == "multi"
        expected = gen.rule_mirror(grid)
        assert _sort_output_colors(grid) != expected
        assert _sort_output_colors(grid, reverse=True) != expected


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_geometry_witness_slot_refutes_row_major_hole_packing(band):
    """At least one slot per quartet must identify the exact hole positions."""
    for seed in [*range(32), 239, 331, -1, 2**63 + 3]:
        sample_index = (1 - seed // 8) % 4
        grid = gen.generate(seed, sample_index, difficulty=band)
        assert _pack_output_support(grid) != gen.rule_mirror(grid)


def test_cell_binding_and_hole_position_rivals_are_declared():
    expected = {
        "sort_colors_ascending",
        "sort_colors_descending",
        "pack_nonzeros_in_centered_bbox",
    }
    assert expected <= set(gen.SEMANTIC_RIVALS)
    assert expected <= {
        rival
        for rivals in gen.WITNESS_RIVALS.values()
        for rival in rivals
    }
