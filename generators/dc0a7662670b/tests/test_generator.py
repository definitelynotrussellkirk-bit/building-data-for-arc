from __future__ import annotations

import copy
import importlib
import importlib.util
from pathlib import Path
from collections import Counter

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "dc0a7662670b"
mod = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
PAIRS = canonical_pairs(TASK_ID, root=find_root(__file__))


def _components(grid):
    """Independent same-color 4-connected component extractor."""
    height, width = len(grid), len(grid[0])
    seen = set()
    records = []
    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            if color == 0 or (start_row, start_col) in seen:
                continue
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            cells = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    next_row, next_col = row + drow, col + dcol
                    if (
                        0 <= next_row < height
                        and 0 <= next_col < width
                        and grid[next_row][next_col] == color
                        and (next_row, next_col) not in seen
                    ):
                        seen.add((next_row, next_col))
                        stack.append((next_row, next_col))
            records.append((color, tuple(sorted(cells))))
    return records


def _perimeter(cells):
    occupied = set(cells)
    return sum(
        (row + drow, col + dcol) not in occupied
        for row, col in occupied
        for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1))
    )


def _demo(seed, sample_index, band="medium"):
    grid = mod.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": mod.rule_mirror(grid)}


def test_rule_pin_and_public_contract_are_explicit():
    assert mod.RULE_HASH == "eff15ddf94a7"
    assert mod.VERSION == "2.0.0"
    assert mod.EXAMPLES_NEEDED == 4
    assert tuple(mod.SCHEDULE_PROFILES) == (
        "canonical_four",
        "bbox_tie",
        "area_inversion",
        "color_tie",
    )
    assert mod.HELPFUL_TEXTURES == ()
    assert mod.DEGENERATE_TEXTURES == ()
    assert set(mod.AXES) == {"grid_h", "grid_w", "shape_profile"}


def test_canonical_pairs_are_accepted_and_python_mirror_matches_authority_examples():
    assert len(PAIRS) == 5
    for pair in PAIRS:
        grid = copy.deepcopy(pair["input"])
        assert mod.self_check(grid) == []
        assert mod.strict_canonical_like(grid) == []
        assert mod.rule_mirror(grid) == pair["output"]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_cyclic_four_demo_window_covers_all_profiles_and_identifies_rule(band):
    for start in range(8):
        demos = [_demo(700 + start, start + offset, band) for offset in range(4)]
        query = _demo(900 + start, start + 4, band)
        observed = {
            mod.observe_overrides(pair["input"])["shape_profile"]
            for pair in demos
        }
        assert observed == set(mod.SCHEDULE_PROFILES)
        assert mod.lesson_identifiable(demos, query) == []


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("height,width", [(10, 11), (14, 16)])
@pytest.mark.parametrize(
    "profile",
    ["canonical_four", "bbox_tie", "area_inversion", "color_tie"],
)
def test_all_advertised_exact_overrides_are_observable(band, height, width, profile):
    grid = mod.generate(
        23,
        17,
        difficulty=band,
        grid_h=height,
        grid_w=width,
        shape_profile=profile,
    )
    assert mod.self_check(grid) == []
    observed = mod.observe_overrides(grid)
    assert observed["grid_h"] == height
    assert observed["grid_w"] == width
    assert observed["shape_profile"] == profile


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo_axis": 1},
        {"grid_h": 9},
        {"grid_h": 15},
        {"grid_w": 10},
        {"grid_w": 17},
        {"grid_h": True},
        {"grid_w": 12.5},
        {"shape_profile": "unknown"},
    ],
)
def test_invalid_or_unknown_overrides_raise(kwargs):
    with pytest.raises(ValueError):
        mod.generate(0, 0, **kwargs)


def test_unknown_difficulty_raises():
    with pytest.raises(ValueError):
        mod.generate(0, 0, difficulty="expert")


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_constructive_generator_is_deterministic_valid_and_profile_complete(band):
    profile_counts = Counter()
    outputs = set()
    for index in range(80):
        seed = 10000 + index
        grid = mod.generate(seed, index * 7 + 3, difficulty=band)
        assert grid == mod.generate(seed, index * 7 + 3, difficulty=band)
        assert mod.self_check(grid) == []
        assert mod.strict_canonical_like(grid) == []
        observed = mod.observe_overrides(grid)
        profile_counts[observed["shape_profile"]] += 1
        output = mod.rule_mirror(grid)
        outputs.add(tuple(tuple(row) for row in output))
        assert len(output) >= 7
        assert 2 <= len(output[0]) <= 4
    assert set(profile_counts) == set(mod.SCHEDULE_PROFILES)
    assert len(outputs) >= 70


def test_declared_witnesses_are_real_counterexamples_to_named_rivals():
    fired = set()
    for profile_index, profile in enumerate(mod.SCHEDULE_PROFILES):
        grid = mod.generate(
            400 + profile_index,
            profile_index,
            difficulty="hard",
            shape_profile=profile,
        )
        official = mod.rule_mirror(grid)
        for witness_name, witness in mod.SEMANTIC_WITNESSES.items():
            if not witness(grid):
                continue
            fired.add(witness_name)
            named = mod.WITNESS_RIVALS[witness_name]
            assert any(mod.SEMANTIC_RIVALS[name](grid) != official for name in named)
    assert fired == set(mod.SEMANTIC_WITNESSES)


def test_real_canonical_shortcuts_fit_all_canonical_pairs_but_generated_witnesses_break_them():
    assert set(mod.CANONICAL_SHORTCUTS) == {
        "sort_by_area",
        "tie_break_color_descending",
    }
    for rival in mod.CANONICAL_SHORTCUTS.values():
        assert all(rival(pair["input"]) == pair["output"] for pair in PAIRS)

    area_grid = mod.generate(31, 2, shape_profile="area_inversion")
    tie_grid = mod.generate(31, 3, shape_profile="color_tie")
    assert mod.SEMANTIC_RIVALS["sort_by_area"](area_grid) != mod.rule_mirror(area_grid)
    assert (
        mod.SEMANTIC_RIVALS["tie_break_color_descending"](tie_grid)
        != mod.rule_mirror(tie_grid)
    )


def test_color_tie_profile_uses_ascending_color_as_authoritative_tie_break():
    grid = mod.generate(77, 3, shape_profile="color_tie")
    records = [
        (color, _perimeter(cells), cells)
        for color, cells in _components(grid)
    ]
    tied_colors = sorted(color for color, perimeter, _cells in records if perimeter == 12)
    assert len(tied_colors) == 2

    output = mod.rule_mirror(grid)
    first_rows = {}
    for row_index, row in enumerate(output):
        for color in tied_colors:
            if color in row and color not in first_rows:
                first_rows[color] = row_index
    assert first_rows[tied_colors[0]] < first_rows[tied_colors[1]]


def test_self_check_rejects_malformed_and_targeted_impostors():
    malformed = [None, [], [[]], [[0], [0, 1]], [[True] * 11 for _ in range(10)]]
    for grid in malformed:
        assert mod.self_check(grid)

    base = mod.generate(91, 0, shape_profile="canonical_four")
    components = _components(base)

    duplicate_color = copy.deepcopy(base)
    source_color = components[0][0]
    target_color, target_cells = components[1]
    assert source_color != target_color
    for row, col in target_cells:
        duplicate_color[row][col] = source_color
    assert mod.self_check(duplicate_color)

    extra_component = copy.deepcopy(base)
    empty = next(
        (r, c)
        for r, row in enumerate(extra_component)
        for c, value in enumerate(row)
        if value == 0
        and all(
            not (0 <= r + dr < len(extra_component) and 0 <= c + dc < len(row))
            or extra_component[r + dr][c + dc] == 0
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
        )
    )
    extra_component[empty[0]][empty[1]] = 9
    assert mod.self_check(extra_component)

    erase_smallest = copy.deepcopy(base)
    smallest = min(components, key=lambda item: _perimeter(item[1]))
    for row, col in smallest[1]:
        erase_smallest[row][col] = 0
    assert mod.self_check(erase_smallest)


def test_workspace_semantic_probe_reports_cyclic_lesson_coverage():
    probe_path = (
        Path.cwd()
        / "generators"
        / TASK_ID
        / "workspace"
        / "semantic_probe.py"
    )
    spec = importlib.util.spec_from_file_location("dc0a7662670b_semantic_probe", probe_path)
    assert spec is not None and spec.loader is not None
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)

    report = probe.run_probe(per_band=2, cyclic_starts=4)
    assert report["errors"] == []
    assert report["canonical_shortcuts_checked"] == 2
    assert report["cyclic_windows_checked"] == 3 * 2 * 4
    assert report["profiles_seen"] == sorted(mod.SCHEDULE_PROFILES)
    assert report["surviving_rivals"] == {}
