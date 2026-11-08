"""Task-local regression tests for the repaired b38782448e7b sampler."""
from __future__ import annotations

import os
from pathlib import Path
from statistics import median
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    all_top_non_background,
    binary_toggle_only,
    canonical_pairs,
    changed_cells,
    decoy_witness,
    erase_unmarked_body,
    intended_output,
    load_generator,
    observed,
    solid_paint_columns,
    witness_flags,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
CANONICAL_PROFILES = {(20, 20, 3), (30, 30, 6), (30, 30, 7)}
RIVALS = {
    "all_top_non_background": all_top_non_background,
    "erase_unmarked_body": erase_unmarked_body,
    "binary_toggle_only": binary_toggle_only,
    "solid_paint_columns": solid_paint_columns,
}


def _labeled(grid):
    return {"input": grid, "output": intended_output(grid)}


def test_canonical_pairs_are_accepted_and_independent_oracle_matches_labels():
    pairs = canonical_pairs()
    assert len(pairs) >= 3
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert intended_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_all_exact_overrides_are_observable_in_every_band(band):
    options = {
        "grid_h": 20,
        "grid_w": 20,
        "bg_color": 8,
        "palette_size": 7,
        "n_markers": 6,
        "n_decoys": 3,
    }
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "override",
    [
        {"typo": 1},
        {"grid_h": 19},
        {"grid_w": 31},
        {"bg_color": -1},
        {"bg_color": 10},
        {"palette_size": 2},
        {"palette_size": 8},
        {"n_markers": 1},
        {"n_markers": 7},
        {"n_decoys": -1},
        {"n_decoys": 4},
        {"grid_h": True},
        {"n_markers": 2.0},
        {"palette_size": "3"},
        {"bg_color": False},
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(override):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **override)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_distribution_is_lawful_supports_canonical_profiles_and_refutes_rivals(band):
    grids = [gen.generate(900 + i, i, difficulty=band) for i in range(24)]
    assert all(gen.self_check(grid) == [] for grid in grids)
    assert all(grid == gen.generate(900 + i, i, difficulty=band) for i, grid in enumerate(grids))
    profiles = {
        (len(grid), len(grid[0]), len({value for row in grid for value in row}))
        for grid in grids
    }
    assert CANONICAL_PROFILES <= profiles
    for grid in grids:
        flags = witness_flags(grid)
        assert all(flags.values()), flags
        answer = intended_output(grid)
        for name, rival in RIVALS.items():
            assert rival(grid) != answer, name


def test_every_four_pair_window_remains_identifying_after_any_query_rotation():
    for start in range(16):
        grids = [gen.generate(1200 + start, start + offset) for offset in range(4)]
        pairs = [_labeled(grid) for grid in grids]
        for held_out in range(4):
            demos = [pair for index, pair in enumerate(pairs) if index != held_out]
            query = pairs[held_out]
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(demo["input"]) != demo["output"] for demo in demos), name


def test_strongest_canonical_shortcut_fits_all_labels_and_exact_decoy_refutes_it():
    pairs = canonical_pairs()
    assert all(all_top_non_background(pair["input"]) == pair["output"] for pair in pairs)

    witness = decoy_witness()
    assert gen.self_check(witness) == []
    intended = intended_output(witness)
    rival = all_top_non_background(witness)
    assert changed_cells(intended, rival) == [
        (1, 13, 2, 8),
        (2, 13, 8, 2),
        (3, 13, 4, 2),
        *[(r, 13, 8, 2) for r in range(4, 20)],
    ]


def test_historical_erasure_shortcut_is_reproduced_then_refuted_by_repair():
    for band in (None, "easy", "medium", "hard"):
        for index in range(12):
            grid = gen.generate(2300 + index, index, difficulty=band)
            assert erase_unmarked_body(grid) != intended_output(grid)


def test_semantic_declarations_bind_every_witness_to_an_executable_rival():
    assert set(gen.SEMANTIC_WITNESSES) == {
        "non_firing_top_decoy",
        "unmarked_body_preservation",
        "third_color_overwrite",
        "xor_off_marker_match",
    }
    assert set(gen.SEMANTIC_RIVALS) == set(RIVALS)
    assert set(gen.LESSON_COMPETITORS) == set(RIVALS)
    assert set(gen.CANONICAL_SHORTCUTS) == {"all_top_non_background"}
    assert gen.WITNESS_RIVALS == {
        "non_firing_top_decoy": ["all_top_non_background"],
        "unmarked_body_preservation": ["erase_unmarked_body"],
        "third_color_overwrite": ["binary_toggle_only"],
        "xor_off_marker_match": ["solid_paint_columns"],
    }


def test_self_check_rejects_semantically_damaged_inputs():
    base = gen.generate(
        4,
        2,
        grid_h=20,
        grid_w=20,
        bg_color=8,
        palette_size=4,
        n_markers=3,
        n_decoys=1,
    )
    assert gen.self_check(base) == []
    bg = observed(base)["bg_color"]

    ragged = [row[:] for row in base]
    ragged[-1].pop()

    illegal = [row[:] for row in base]
    illegal[-1][-1] = 12

    no_controls = [row[:] for row in base]
    no_controls[0] = [bg] * len(no_controls[0])

    no_unmarked_body = [row[:] for row in base]
    firing = {
        c for c, value in enumerate(no_unmarked_body[0])
        if value != bg and value != no_unmarked_body[1][c]
    }
    for r in range(1, len(no_unmarked_body)):
        for c in range(len(no_unmarked_body[0])):
            if c not in firing:
                no_unmarked_body[r][c] = bg

    no_marker_match = [row[:] for row in base]
    for c in firing:
        marker = no_marker_match[0][c]
        replacement = next(v for v in range(10) if v not in (bg, marker))
        for r in range(1, len(no_marker_match)):
            if no_marker_match[r][c] == marker:
                no_marker_match[r][c] = replacement

    for damaged in (ragged, illegal, no_controls, no_unmarked_body, no_marker_match):
        assert gen.self_check(damaged)


def test_independent_oracle_and_declared_rules_are_pure():
    grid = gen.generate(412, 11)
    before = [row[:] for row in grid]
    assert gen.rule_mirror(grid) == intended_output(grid)
    for rival in gen.SEMANTIC_RIVALS.values():
        rival(grid)
    assert grid == before


def _largest_same_color_component(grid):
    from collections import Counter

    bg = Counter(value for row in grid for value in row).most_common(1)[0][0]
    seen = set()
    biggest = 0
    for start_r, row in enumerate(grid):
        for start_c, color in enumerate(row):
            if color == bg or (start_r, start_c) in seen:
                continue
            stack = [(start_r, start_c)]
            seen.add((start_r, start_c))
            size = 0
            while stack:
                r, c = stack.pop()
                size += 1
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < len(grid)
                        and 0 <= nc < len(grid[0])
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            biggest = max(biggest, size)
    return biggest


def test_canonical_profile_schedule_reaches_canonical_component_scales():
    small = gen.generate(71, 0, difficulty="easy")
    medium = gen.generate(72, 1, difficulty="medium")
    large = gen.generate(73, 2, difficulty="hard")
    assert _largest_same_color_component(small) >= 54
    assert _largest_same_color_component(medium) >= 100
    assert _largest_same_color_component(large) >= 100


def _longest_non_background_run_in_column(grid, col):
    from collections import Counter

    bg = Counter(value for row in grid for value in row).most_common(1)[0][0]
    best = current = 0
    current_color = None
    for row in range(5, len(grid)):
        value = grid[row][col]
        if value != bg and value == current_color:
            current += 1
        elif value != bg:
            current_color = value
            current = 1
        else:
            current_color = None
            current = 0
        best = max(best, current)
    return best


def test_default_controls_span_full_width_and_cut_through_large_components():
    normalized_columns = []
    for sample_index in range(48):
        grid = gen.generate(9100 + sample_index, sample_index, difficulty="hard")
        analysis = gen._analysis(grid)
        assert not analysis["errors"]
        markers = analysis["markers"]
        normalized_columns.extend(col / (len(grid[0]) - 1) for col in markers)
        assert any(
            _longest_non_background_run_in_column(grid, col) >= 6
            for col in markers
        )

    assert min(normalized_columns) < 0.15
    assert max(normalized_columns) > 0.85


def _non_background_component_count(grid):
    from collections import Counter

    bg = Counter(value for row in grid for value in row).most_common(1)[0][0]
    seen = set()
    count = 0
    for start_r, row in enumerate(grid):
        for start_c, value in enumerate(row):
            if value == bg or (start_r, start_c) in seen:
                continue
            count += 1
            stack = [(start_r, start_c)]
            seen.add((start_r, start_c))
            while stack:
                r, c = stack.pop()
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < len(grid)
                        and 0 <= nc < len(grid[0])
                        and (nr, nc) not in seen
                        and grid[nr][nc] != bg
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
    return count


def test_default_morphology_does_not_fragment_beyond_canonical_object_counts():
    counts = []
    for band in ("easy", "medium", "hard"):
        for seed in range(1, 21):
            grid = gen.generate(seed, seed, difficulty=band)
            counts.append(_non_background_component_count(grid))

    # The five labeled canonical records have 3, 5, or 10 components under
    # the repository's modal-background / any-non-background connectivity
    # metric.  Generated lessons should stay inside that observed envelope.
    assert max(counts) <= 10
    assert median(counts) <= 10
