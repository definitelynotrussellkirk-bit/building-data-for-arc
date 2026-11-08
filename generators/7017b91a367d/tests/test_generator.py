"""Task-local regressions for the three-panel overlap-count generator."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import itertools
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

HOME = Path(__file__).resolve().parents[1]


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location("selected_generator", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()
PAIRS = canonical_pairs("7017b91a367d", root=find_root(__file__))
PROFILE_HISTOGRAMS = {
    "s4_d3_t2": (4, 3, 2),
    "s2_d5_t2": (2, 5, 2),
    "s2_d5_t1": (2, 5, 1),
    "s1_d6_t1": (1, 6, 1),
    "s2_d4_t2": (2, 4, 2),
}
PALETTES = ("default", "warm", "cool", "varied")


def intended_output(grid):
    """Independent count-map oracle used only by tests/workspace tooling."""
    return [
        [
            {0: 0, 1: 2, 2: 4, 3: 8}[
                sum(grid[r][c + 6 * panel] != 0 for panel in range(3))
            ]
            for c in range(5)
        ]
        for r in range(5)
    ]


def occupancy_histogram(grid):
    counts = [0, 0, 0, 0]
    for r in range(5):
        for c in range(5):
            n = sum(grid[r][c + 6 * panel] != 0 for panel in range(3))
            counts[n] += 1
    return tuple(counts[1:])


def panel_cells(grid, panel):
    left = 6 * panel
    return {
        (r, c)
        for r in range(5)
        for c in range(5)
        if grid[r][left + c] != 0
    }


def connected(cells):
    if not cells:
        return False
    seen = {next(iter(cells))}
    pending = list(seen)
    while pending:
        r, c = pending.pop()
        for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if point in cells and point not in seen:
                seen.add(point)
                pending.append(point)
    return seen == cells


def labeled_pair(grid):
    return {"input": deepcopy(grid), "output": intended_output(grid)}


def test_declares_only_real_exact_controls_and_semantic_contract():
    assert gen.RULE_HASH == "aa994ed25e88"
    assert set(gen.AXES) == {"profile", "palette_kind"}
    assert gen.EXAMPLES_NEEDED == 3
    assert tuple(gen.SCHEDULE_PROFILES) == ("center", "top_left", "bottom_right")
    assert set(gen.SEMANTIC_WITNESSES) >= {"border_occupancy", "all_count_levels"}
    assert gen.WITNESS_RIVALS == {"border_occupancy": ["central_3x3_only"]}
    assert set(gen.CANONICAL_SHORTCUTS) == {"central_3x3_only"}
    assert set(gen.LESSON_COMPETITORS) == {"central_3x3_only"}


@pytest.mark.parametrize("pair", PAIRS, ids=lambda p: f"{p['split']}{p['pair_index']}")
def test_accepts_canonical_inputs_and_matches_count_rule(pair):
    assert gen.self_check(pair["input"]) == []
    assert intended_output(pair["input"]) == pair["output"]
    assert gen.CANONICAL_SHORTCUTS["central_3x3_only"](pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_exact_override_combination_is_honored_in_every_band(band):
    for index, (profile, palette) in enumerate(itertools.product(PROFILE_HISTOGRAMS, PALETTES)):
        grid = gen.generate(
            7017 + index,
            index,
            difficulty=band,
            profile=profile,
            palette_kind=palette,
        )
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == {"profile": profile, "palette_kind": palette}
        assert occupancy_histogram(grid) == PROFILE_HISTOGRAMS[profile]
        assert grid == gen.generate(
            7017 + index,
            index,
            difficulty=band,
            profile=profile,
            palette_kind=palette,
        )


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo": "default"},
        {"profile": "not-a-profile"},
        {"profile": 1},
        {"palette_kind": "infrared"},
        {"palette_kind": 3},
    ],
)
def test_rejects_unknown_or_invalid_overrides(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **overrides)


def test_generated_panels_are_three_connected_objects_and_teach_all_counts():
    seen_inputs = set()
    for band in (None, "easy", "medium", "hard"):
        for i in range(180):
            grid = gen.generate(9000 + i, i * 11, difficulty=band)
            assert gen.self_check(grid) == []
            assert intended_output(grid) == intended_output(deepcopy(grid))
            colors = []
            for panel in range(3):
                cells = panel_cells(grid, panel)
                assert connected(cells)
                left = 6 * panel
                panel_colors = {grid[r][left + c] for r, c in cells}
                assert len(panel_colors) == 1
                colors.extend(panel_colors)
            assert len(set(colors)) == 3
            assert {2, 4, 8} <= {value for row in intended_output(grid) for value in row}
            seen_inputs.add(tuple(tuple(row) for row in grid))
    assert len(seen_inputs) > 500


def test_three_position_schedule_and_border_counterexample_are_real():
    for index, expected in enumerate(("center", "top_left", "bottom_right") * 4):
        grid = gen.generate(81, index, profile="s4_d3_t2", palette_kind="default")
        assert gen.schedule_profile(81, index) == expected
        has_border = gen.SEMANTIC_WITNESSES["border_occupancy"](grid)
        assert has_border is (expected != "center")
        rival = gen.SEMANTIC_RIVALS["central_3x3_only"](grid)
        if has_border:
            assert rival != intended_output(grid)
        else:
            assert rival == intended_output(grid)
        assert gen.SEMANTIC_WITNESSES["all_count_levels"](grid)


def test_every_cyclic_four_pair_lesson_and_query_rotation_refutes_shortcut():
    for band in (None, "easy", "medium", "hard"):
        for start in range(12):
            pairs = [labeled_pair(gen.generate(500 + start, start + offset, difficulty=band)) for offset in range(4)]
            for query_index in range(4):
                query = pairs[query_index]
                demos = [pair for i, pair in enumerate(pairs) if i != query_index]
                assert gen.lesson_identifiable(demos, query) == []
                assert any(
                    gen.LESSON_COMPETITORS["central_3x3_only"](demo["input"]) != demo["output"]
                    for demo in demos
                )


@pytest.mark.parametrize(
    "bad",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 17 for _ in range(5)],
        [[0] * 17 for _ in range(5)],
    ],
)
def test_self_check_rejects_malformed_or_non_teaching_grids(bad):
    assert gen.self_check(bad)


@pytest.mark.parametrize(
    "mutation",
    ["separator", "color10", "empty_panel", "disconnected", "missing_triple"],
)
def test_self_check_rejects_destructive_mutations(mutation):
    grid = gen.generate(33, 0, profile="s4_d3_t2", palette_kind="default")
    if mutation == "separator":
        grid[0][5] = 1
    elif mutation == "color10":
        grid[0][0] = 10
    elif mutation == "empty_panel":
        for r in range(5):
            for c in range(12, 17):
                grid[r][c] = 0
    elif mutation == "disconnected":
        cells = sorted(panel_cells(grid, 0))
        r, c = cells[0]
        grid[r][c] = 0
        grid[4][4] = 4
    elif mutation == "missing_triple":
        for r in range(5):
            for c in range(5):
                if all(grid[r][c + 6 * panel] != 0 for panel in range(3)):
                    grid[r][c] = 0
                    break
            else:
                continue
            break
    assert gen.self_check(grid)


def test_semantic_helpers_do_not_mutate_inputs():
    grid = gen.generate(11, 1)
    original = deepcopy(grid)
    _ = gen.observe_overrides(grid)
    _ = gen.strict_canonical_like(grid)
    _ = gen.SEMANTIC_RIVALS["central_3x3_only"](grid)
    _ = gen.SEMANTIC_WITNESSES["border_occupancy"](grid)
    _ = gen.SEMANTIC_WITNESSES["all_count_levels"](grid)
    assert grid == original


def test_workspace_qualifier_replays_contract_and_cyclic_lessons():
    import sys

    workspace = HOME / "workspace"
    sys.path.insert(0, str(workspace))
    try:
        from qualify import build_report

        report = build_report(generator_path=HOME / "generator.py", starts=range(6))
    finally:
        sys.path.remove(str(workspace))
    assert report["status"] == "PASS"
    assert report["canonical"]["count_rule_matches"] == len(PAIRS)
    assert report["canonical"]["central_shortcut_matches"] == len(PAIRS)
    assert report["overrides"]["cases"] == 4 * len(PROFILE_HISTOGRAMS) * len(PALETTES)
    assert report["lessons"]["ambiguous_rotations"] == 0
    assert report["witness"]["intended_output_sha256"] != report["witness"]["rival_output_sha256"]
