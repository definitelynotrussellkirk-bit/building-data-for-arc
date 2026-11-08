"""Task-local regression contract for the repaired cross-reflection generator."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TASK_ID = "09d287bbfa0b"
HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
RUNTIME = REPO / "shared" / "runtime"
# Repository tests need the source-tree runtime on sys.path. Portable task-test
# snapshots already expose their selected runtime and carry RUNTIME_MANIFEST.json;
# inserting the mirrored source path there would mix two puzzle_generators trees.
if not (REPO / "RUNTIME_MANIFEST.json").is_file() and RUNTIME.is_dir():
    if str(RUNTIME) not in sys.path:
        sys.path.insert(0, str(RUNTIME))

from reviewer_support import (  # noqa: E402
    canonical_pairs,
    find_root,
    load_selected_generator,
)


ROOT = find_root(__file__)
GEN, _GENERATOR_SOURCE, _GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
PAIRS = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
CANONICAL_PROFILES = {(8, 8, 7), (10, 15, 7), (11, 11, 7), (11, 17, 9)}


def rule_output(grid):
    """Independent Python transcription of the selected Racket semantics."""
    height, width = len(grid), len(grid[0])
    cross_row = next((r for r in range(height) if all(v != 7 for v in grid[r])), None)
    cross_col = next(
        (c for c in range(width) if all(grid[r][c] != 7 for r in range(height))),
        None,
    )
    out = [list(row) for row in grid]
    if cross_row is None or cross_col is None:
        return out
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if value == 7 or row == cross_row or col == cross_col:
                continue
            reflected = (
                (row, 2 * cross_col - col),
                (2 * cross_row - row, col),
                (2 * cross_row - row, 2 * cross_col - col),
            )
            for target_row, target_col in reflected:
                if (
                    0 <= target_row < height
                    and 0 <= target_col < width
                    and target_row != cross_row
                    and target_col != cross_col
                ):
                    out[target_row][target_col] = value
    return out


def analyse(grid):
    height, width = len(grid), len(grid[0])
    cross_row = next(r for r in range(height) if all(v != 7 for v in grid[r]))
    cross_col = next(c for c in range(width) if all(grid[r][c] != 7 for r in range(height)))
    separator = grid[cross_row][cross_col]
    sources = []
    axis_dots = []
    orbit_counts = {}
    partial_clip = False
    quadrants = set()
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if value == 7:
                continue
            if row == cross_row or col == cross_col:
                if value != separator:
                    axis_dots.append((row, col, value))
                continue
            sources.append((row, col, value))
            key = (abs(row - cross_row), abs(col - cross_col))
            orbit_counts[key] = orbit_counts.get(key, 0) + 1
            quadrants.add((row < cross_row, col < cross_col))
            reflected = (
                (row, 2 * cross_col - col),
                (2 * cross_row - row, col),
                (2 * cross_row - row, 2 * cross_col - col),
            )
            valid = sum(
                0 <= rr < height
                and 0 <= cc < width
                and rr != cross_row
                and cc != cross_col
                for rr, cc in reflected
            )
            partial_clip |= 0 < valid < 3
    return {
        "cross_row": cross_row,
        "cross_col": cross_col,
        "separator": separator,
        "sources": sources,
        "axis_dots": axis_dots,
        "collision": any(count > 1 for count in orbit_counts.values()),
        "partial_clip": partial_clip,
        "quadrants": quadrants,
    }


@pytest.mark.parametrize("pair", PAIRS, ids=lambda p: f"v{p['variant']}-{p['split']}{p['pair_index']}")
def test_canonical_pairs_are_owned_and_independent_oracle_matches(pair):
    assert GEN.self_check(pair["input"]) == []
    assert GEN.strict_canonical_like(pair["input"]) == []
    assert rule_output(pair["input"]) == pair["output"]


def test_contract_metadata_and_hooks_are_complete():
    assert GEN.RULE_HASH == "36baa035a1e3"
    assert GEN.EXAMPLES_NEEDED == 3
    assert tuple(GEN.SCHEDULE_PROFILES) == ("canonical_core", "teaching_mix")
    assert set(GEN.AXES) == {"grid_h", "grid_w", "sep_color", "n_pixels", "texture"}
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    for name in ("observe_overrides", "schedule_profile", "lesson_identifiable"):
        assert callable(getattr(GEN, name))


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {"grid_h": 7, "grid_w": 7, "sep_color": 1, "n_pixels": 2, "texture": "plain"},
        {"grid_h": 7, "grid_w": 7, "sep_color": 2, "n_pixels": 2, "texture": "multi_quadrant"},
        {"grid_h": 7, "grid_w": 7, "sep_color": 3, "n_pixels": 2, "texture": "clip"},
        {"grid_h": 18, "grid_w": 18, "sep_color": 4, "n_pixels": 8, "texture": "axis_dot"},
        {"grid_h": 18, "grid_w": 18, "sep_color": 6, "n_pixels": 8, "texture": "mixed"},
    ],
)
def test_every_exact_override_is_observable_in_every_band(difficulty, options):
    grid = GEN.generate(173, 19, difficulty=difficulty, **options)
    assert GEN.self_check(grid, difficulty=difficulty) == []
    assert GEN.observe_overrides(grid) == options
    assert grid == GEN.generate(173, 19, difficulty=difficulty, **options)
    assert rule_output(grid) != grid


@pytest.mark.parametrize(
    "bad",
    [
        {"typo": 1},
        {"grid_h": 6}, {"grid_h": 19}, {"grid_h": True}, {"grid_h": 7.0},
        {"grid_w": 6}, {"grid_w": 19}, {"grid_w": "7"},
        {"sep_color": 0}, {"sep_color": 7}, {"sep_color": False},
        {"n_pixels": 1}, {"n_pixels": 9}, {"n_pixels": 2.0},
        {"texture": "dense"}, {"texture": 1},
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(bad):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **bad)


@pytest.mark.parametrize(
    "texture,expected",
    [
        ("plain", {"axis": False, "collision": False, "clip": False, "multi": False}),
        ("multi_quadrant", {"axis": False, "collision": True, "clip": False, "multi": True}),
        ("clip", {"axis": False, "collision": False, "clip": True, "multi": False}),
        ("axis_dot", {"axis": True, "collision": False, "clip": False, "multi": False}),
        ("mixed", {"axis": True, "collision": True, "clip": True, "multi": True}),
    ],
)
def test_each_texture_has_its_advertised_observable_signal(texture, expected):
    grid = GEN.generate(900, 7, grid_h=9, grid_w=10, n_pixels=6, texture=texture)
    facts = analyse(grid)
    assert bool(facts["axis_dots"]) is expected["axis"]
    assert facts["collision"] is expected["collision"]
    assert facts["partial_clip"] is expected["clip"]
    assert (len(facts["quadrants"]) > 1) is expected["multi"]


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_default_curriculum_never_barely_demonstrates_the_transformation(difficulty):
    for index in range(20):
        grid = GEN.generate(6100 + index, index, difficulty=difficulty)
        output = rule_output(grid)
        changed = sum(
            before != after
            for input_row, output_row in zip(grid, output)
            for before, after in zip(input_row, output_row)
        )
        assert changed / (len(grid) * len(grid[0])) >= 0.03, (
            difficulty,
            index,
            changed,
            len(grid),
            len(grid[0]),
        )


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_default_twenty_draws_hit_exact_canonical_profiles_and_both_schedule_branches(difficulty):
    profiles = set()
    schedule = set()
    inputs = set()
    for index in range(20):
        grid = GEN.generate(4000 + index, index, difficulty=difficulty)
        assert GEN.self_check(grid, difficulty=difficulty) == []
        profiles.add((len(grid), len(grid[0]), len({v for row in grid for v in row})))
        schedule.add(GEN.schedule_profile(4000 + index, index, difficulty))
        inputs.add(tuple(tuple(row) for row in grid))
    assert CANONICAL_PROFILES <= profiles
    assert schedule == set(GEN.SCHEDULE_PROFILES)
    assert len(inputs) == 20


def test_canonical_shortcuts_really_fit_every_canonical_pair():
    expected = {"single_quadrant_only", "reflect_axis_cells", "preserve_original_sources"}
    assert set(GEN.CANONICAL_SHORTCUTS) == expected
    for pair in PAIRS:
        for name, rival in GEN.CANONICAL_SHORTCUTS.items():
            assert rival(deepcopy(pair["input"])) == pair["output"], name


def test_one_mixed_input_refutes_every_declared_semantic_rival_and_fires_witnesses():
    grid = GEN.generate(719, 1, texture="mixed", n_pixels=8)
    expected = rule_output(grid)
    assert set(GEN.LESSON_COMPETITORS) == set(GEN.SEMANTIC_RIVALS)
    for name, rival in GEN.SEMANTIC_RIVALS.items():
        assert rival(deepcopy(grid)) != expected, name
    for name, predicate in GEN.SEMANTIC_WITNESSES.items():
        assert predicate(grid), name


@pytest.mark.parametrize("start", range(8))
def test_every_production_window_and_every_query_rotation_refutes_all_competitors(start):
    pairs = []
    for offset in range(4):
        grid = GEN.generate(8123, start + offset, difficulty="medium")
        pairs.append({"input": grid, "output": rule_output(grid)})
    assert "teaching_mix" in {
        GEN.schedule_profile(8123, start + offset, "medium") for offset in range(3)
    }
    for query_index in range(4):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        query = pairs[query_index]
        assert GEN.lesson_identifiable(demos, query) == []
        for name, rival in GEN.LESSON_COMPETITORS.items():
            assert any(rival(deepcopy(pair["input"])) != pair["output"] for pair in demos), name


@pytest.mark.parametrize(
    "bad",
    [None, [], [[]], [[7], [7, 7]], [[True] * 7 for _ in range(7)], [[10] * 7 for _ in range(7)]],
)
def test_malformed_grids_are_diagnostic_not_exceptions(bad):
    assert GEN.self_check(bad)


@pytest.mark.parametrize(
    "difficulty",
    ["__invalid_difficulty__", "EASY", True, False, 0, 1, 1.5, [], {}],
)
def test_generate_rejects_invalid_difficulty_scalars(difficulty):
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(101, 0, difficulty=difficulty)


@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1"])
def test_generate_rejects_non_integer_seed_scalars(seed):
    with pytest.raises((TypeError, ValueError), match="seed"):
        GEN.generate(seed, 0, difficulty="medium")


@pytest.mark.parametrize("sample_index", [True, False, 1.0, 1.75, "1", -1])
def test_generate_rejects_invalid_sample_index_scalars(sample_index):
    with pytest.raises((TypeError, ValueError), match="sample_index"):
        GEN.generate(991, sample_index, difficulty="medium")
