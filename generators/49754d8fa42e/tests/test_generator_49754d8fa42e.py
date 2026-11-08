"""Pixel-level regressions for the fixed nonzero-mode classifier.

Expected outputs live only in these tests; the executable Racket program
remains the task's label authority.
"""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys

import pytest


REPO = Path(__file__).resolve().parents[3]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))
TASK = "49754d8fa42e"
BANDS = (None, "easy", "medium", "hard")
AXIS_VALUES = {
    "grid_h": range(3, 11),
    "grid_w": range(3, 11),
    "mode_color": range(1, 4),
    "mode_count": range(5, 96),
    "palette_size": range(2, 7),
}
GLYPHS = {
    1: [[0, 5, 0], [5, 5, 5], [0, 5, 0]],
    2: [[5, 5, 5], [0, 5, 0], [0, 5, 0]],
    3: [[0, 0, 5], [0, 0, 5], [5, 5, 5]],
}


@pytest.fixture(scope="module")
def gen():
    path = REPO / "generators" / TASK / "generator.py"
    spec = importlib.util.spec_from_file_location("tested_generator_49754d8fa42e", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def canonical():
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("task_id") == TASK:
                return record
    pytest.fail("canonical task record missing")


def _pixels(grid):
    """Independent observer: never trust recorded generation metadata."""
    assert isinstance(grid, list) and 3 <= len(grid) <= 10
    assert all(isinstance(row, list) for row in grid)
    width = len(grid[0])
    assert 3 <= width <= 10 and all(len(row) == width for row in grid)
    values = [value for row in grid for value in row]
    assert all(type(value) is int and 0 <= value <= 9 for value in values)
    counts = Counter(values)
    assert counts[0] >= 5
    assert 2 <= len(counts) <= 6
    foreground = Counter({color: count for color, count in counts.items() if color})
    (mode, count), *rest = foreground.most_common()
    assert mode in (1, 2, 3)
    assert count >= 5
    assert all(count > other_count for _, other_count in rest)
    return {
        "grid_h": len(grid), "grid_w": width, "mode_color": mode,
        "mode_count": count, "palette_size": len(counts),
    }


def _assert_lawful(gen, grid, difficulty=None):
    observed = _pixels(grid)
    before = copy.deepcopy(grid)
    assert gen.self_check(grid, difficulty=difficulty) == []
    assert gen.strict_canonical_like(grid) == []
    assert gen.observe_overrides(grid) == observed
    assert grid == before, "inspection hooks mutated the input"
    return observed


def _endpoint_complement(grid):
    """Independent wrong-rule prediction using endpoints, never cell counts."""
    foreground = [value for row in grid for value in row if value]
    first, last = foreground[0], foreground[-1]
    if first == last:
        predicted_color = first
    else:
        missing = {1, 2, 3} - {first, last}
        predicted_color = min(missing) if missing else 0
    return GLYPHS.get(predicted_color, [[0] * 3 for _ in range(3)])


def _endpoint_limited_mode(grid):
    """Wrong rule that counts only colors exposed at foreground endpoints."""
    foreground = [value for row in grid for value in row if value]
    candidates = {foreground[0], foreground[-1]}
    counts = Counter(foreground)
    predicted_color = max(candidates, key=lambda color: (counts[color], -color))
    return GLYPHS.get(predicted_color, [[0] * 3 for _ in range(3)])


def test_axis_surface_and_canonical_authority(gen, canonical):
    assert set(gen.AXES) == set(AXIS_VALUES)
    assert gen.RULE_HASH == "a84bb758c578"
    source = " ".join(canonical["program_solution"].split())
    assert hashlib.sha256(source.encode()).hexdigest()[:12] == gen.RULE_HASH
    assert gen.EXAMPLES_NEEDED == 5


def test_all_nine_canonical_pairs_are_accepted(gen, canonical):
    pairs = [*canonical["train"], *canonical["test"]]
    assert len(pairs) == 9
    for pair in pairs:
        observed = _assert_lawful(gen, pair["input"])
        assert gen.strict_canonical_like(pair["input"]) == []
        assert GLYPHS[observed["mode_color"]] == pair["output"]


@pytest.mark.parametrize("difficulty", BANDS)
@pytest.mark.parametrize("axis", AXIS_VALUES)
def test_every_individually_valid_axis_works_in_every_band(gen, axis, difficulty):
    for value in AXIS_VALUES[axis]:
        # Both an anchor index and a contrast index must honor the pin.
        for index in (0, 1):
            grid = gen.generate(1703, index, difficulty=difficulty, **{axis: value})
            assert _assert_lawful(gen, grid, difficulty)[axis] == value


@pytest.mark.parametrize("difficulty", BANDS)
@pytest.mark.parametrize("pins", [
    {"grid_h": 3, "grid_w": 4, "mode_color": 1, "mode_count": 5, "palette_size": 2},
    {"grid_h": 3, "grid_w": 5, "mode_color": 2, "mode_count": 5, "palette_size": 6},
    {"grid_h": 3, "grid_w": 4, "mode_color": 3, "mode_count": 7, "palette_size": 2},
    {"grid_h": 3, "grid_w": 5, "mode_color": 2, "mode_count": 9, "palette_size": 3},
    {"grid_h": 10, "grid_w": 10, "mode_color": 3, "mode_count": 95, "palette_size": 2},
    {"grid_h": 3, "grid_w": 10, "mode_color": 1, "mode_count": 21, "palette_size": 6},
    {"grid_h": 10, "grid_w": 3, "mode_color": 2, "mode_count": 21, "palette_size": 6},
])
def test_feasible_boundary_combinations_are_exact(gen, pins, difficulty):
    for index in (0, 1, 2):
        grid = gen.generate(73, index, difficulty=difficulty, **pins)
        assert _assert_lawful(gen, grid, difficulty) == pins


@pytest.mark.parametrize("pins", [
    {"grid_h": 3, "grid_w": 3},
    {"grid_h": 3, "grid_w": 4, "mode_count": 5, "palette_size": 6},
    {"mode_count": 95, "palette_size": 3},
    {"grid_h": 3, "grid_w": 3, "mode_count": 5},
    {"grid_h": 3, "grid_w": 4, "mode_count": 8, "palette_size": 3},
    {"grid_h": 3, "mode_count": 30},
])
@pytest.mark.parametrize("difficulty", BANDS)
def test_infeasible_combinations_raise_declared_incompatibilities(gen, pins, difficulty):
    with pytest.raises(ValueError) as caught:
        gen.generate(11, 0, difficulty=difficulty, **pins)
    axes = getattr(caught.value, "incompatible_axes", None)
    assert axes, "infeasibility must identify incompatible_axes"
    assert set(axes).issubset(pins), "report caller pins rather than unpinned defaults"
    if "mode_count" in pins:
        assert "mode_count" in axes


@pytest.mark.parametrize("axis", AXIS_VALUES)
@pytest.mark.parametrize("value", [True, False, 3.0, "3", [], {}])
def test_axes_reject_wrong_types_without_coercion(gen, axis, value):
    with pytest.raises(ValueError):
        gen.generate(9, 1, **{axis: value})


@pytest.mark.parametrize("axis,values", [
    ("grid_h", (2, 11)), ("grid_w", (2, 11)),
    ("mode_color", (0, 4)), ("mode_count", (4, 96)),
    ("palette_size", (1, 7)),
])
def test_axes_reject_out_of_domain_values(gen, axis, values):
    for value in values:
        with pytest.raises(ValueError):
            gen.generate(9, 1, **{axis: value})


@pytest.mark.parametrize("key,value", [
    ("other_color", 3), ("decoy_density", 0.0),
    ("cell_layout", "scattered"), ("texture", "blob"),
    ("texture", "all_zero"), ("typo_axis", 3), ("other_count", 2),
    ("other_color", None), ("typo_axis", None),
])
def test_removed_and_unknown_keys_fail_closed(gen, key, value):
    with pytest.raises(ValueError):
        gen.generate(19, 1, **{key: value})


@pytest.mark.parametrize("difficulty", BANDS)
def test_none_axis_values_are_exactly_unpinned(gen, difficulty):
    for index in range(6):
        expected = gen.generate(88, index, difficulty=difficulty)
        for axis in AXIS_VALUES:
            assert gen.generate(88, index, difficulty=difficulty, **{axis: None}) == expected
        assert gen.generate(88, index, difficulty=difficulty,
                            **dict.fromkeys(AXIS_VALUES)) == expected


INVALID_GRIDS = [
    None, 7, [], [[]], ["123", "000", "000"],
    [[1, 0, 0], [0, 0], [0, 0, 0]],
    [[1, 0], [0, 0]], [[1] * 5 + [0] * 6] + [[0] * 11 for _ in range(2)],
    [[1, 1, 1], [1, 1, 0]] + [[0] * 3 for _ in range(9)],
    [[0] * 3 for _ in range(3)], [[1] * 3 for _ in range(3)],
    [[1, 1, 1, 1], [1, 2, 2, 2], [2, 2, 0, 0], [0, 0, 0, 0]],
    [[4, 4, 4, 0], [4, 4, 0, 0], [0, 0, 0, 0]],
    [[1, 1, 1, 1], [1, 2, 3, 4], [5, 6, 0, 0], [0, 0, 0, 0]],
    # These still have well-defined Racket answers but lie outside the
    # nontrivial counting curriculum (at least five mode and zero cells).
    [[0, 0, 0], [0, 2, 0], [0, 0, 0]],
    [[2, 2, 0], [2, 2, 0], [0, 0, 0]],
    [[2, 2, 2, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
    [[2, 2, 2], [2, 2, 2], [2, 2, 0]],
    [[2, 2, 2], [2, 2, 0], [0, 0, 0]],
]
for bad_cell in (True, 1.0, "1", -1, 10, None, []):
    # Apart from this cell, all count, size, palette and dominance bounds hold.
    INVALID_GRIDS.append([[1, 1, bad_cell, 0], [1, 1, 1, 0], [0, 0, 0, 0]])


@pytest.mark.parametrize("grid", INVALID_GRIDS)
def test_self_check_rejects_invalid_grid_types_ties_blank_and_backgroundless(gen, grid):
    before = copy.deepcopy(grid)
    errors = gen.self_check(grid)
    assert isinstance(errors, list) and errors
    assert grid == before


def test_self_check_excludes_zero_from_mode(gen):
    # The zero background may outnumber the foreground; it is never a candidate.
    grid = [[2, 2, 0, 0], [2, 0, 2, 0], [0, 2, 0, 0]]
    assert _assert_lawful(gen, grid)["mode_color"] == 2


def test_hardcoded_counterexample_rejects_color_and_scan_shortcuts(gen):
    grid = [[1, 0, 0, 0, 0], [0, 2, 2, 0, 0], [0, 2, 2, 2, 0],
            [0, 0, 0, 0, 0], [0, 0, 0, 0, 3]]
    observed = _assert_lawful(gen, grid)
    assert observed == {"grid_h": 5, "grid_w": 5, "mode_color": 2,
                        "mode_count": 5, "palette_size": 4}
    expected = [[5, 5, 5], [0, 5, 0], [0, 5, 0]]
    assert GLYPHS[2] == expected
    shortcuts = gen.CANONICAL_SHORTCUTS
    assert shortcuts and all(callable(fn) for fn in shortcuts.values())
    disagreements = {name for name, fn in shortcuts.items() if fn(copy.deepcopy(grid)) != expected}
    assert len(disagreements) >= 4, "first/last/min/max color cues all select a decoy"


def test_every_declared_canonical_shortcut_fits_all_nine_official_pairs(gen, canonical):
    assert gen.CANONICAL_SHORTCUTS
    assert gen.SEMANTIC_RIVALS
    for name, shortcut in gen.CANONICAL_SHORTCUTS.items():
        assert callable(shortcut) and name in gen.SEMANTIC_RIVALS
        for pair in [*canonical["train"], *canonical["test"]]:
            before = copy.deepcopy(pair["input"])
            assert shortcut(pair["input"]) == pair["output"], name
            assert pair["input"] == before, name


@pytest.mark.parametrize("difficulty", BANDS)
def test_default_schedule_has_one_anchor_two_contrasts_and_all_classes_per_block(gen, difficulty):
    schedules = set()
    profile_schedules = set()
    anchor_positions = set()
    anchor_colors = set()
    grids_seen = set()
    counts_seen = set()
    for seed in (0, 1, 23, 1703):
        for block in range(5):
            colors = []
            profiles = []
            contrast_mode_endpoint_counts = []
            for offset in range(3):
                index = 3 * block + offset
                grid = gen.generate(seed, index, difficulty=difficulty)
                observed = _assert_lawful(gen, grid, difficulty)
                colors.append(observed["mode_color"])
                profile = gen.schedule_profile(seed, index, difficulty)
                profiles.append(profile)
                if observed["palette_size"] == 2:
                    assert (observed["grid_h"], observed["grid_w"], observed["palette_size"]) == (5, 5, 2)
                    assert gen.strict_canonical_like(grid) == []
                    assert profile == "canonical_anchor"
                    anchor_positions.add(offset)
                    anchor_colors.add(observed["mode_color"])
                else:
                    assert {0, 1, 2, 3}.issubset({v for row in grid for v in row})
                    foreground = [v for row in grid for v in row if v]
                    mode = observed["mode_color"]
                    if profile == "early_decoy":
                        assert foreground[0] != mode
                    elif profile == "late_decoy":
                        assert foreground[-1] != mode
                    else:
                        pytest.fail("mixed inputs must have an early_decoy or late_decoy profile")
                    contrast_mode_endpoint_counts.append(
                        int(foreground[0] == mode) + int(foreground[-1] == mode))
                    grids_seen.add(tuple(tuple(row) for row in grid))
                    counts_seen.add(observed["mode_count"])
            assert set(colors) == {1, 2, 3}
            assert sorted(profiles) == ["canonical_anchor", "early_decoy", "late_decoy"]
            assert sorted(contrast_mode_endpoint_counts) == [0, 1], (
                "one contrast must hide the mode from both foreground endpoints; "
                "the other must expose it at exactly one endpoint")
            schedules.add(tuple(colors))
            profile_schedules.add(tuple(profiles))
    assert len(schedules) > 1, "the class permutation must depend on seed/block"
    assert len(profile_schedules) > 1 and len(anchor_positions) > 1
    assert anchor_colors == {1, 2, 3}, "profile and class shuffles must not bind anchors to one class"
    assert len(grids_seen) > 10 and len(counts_seen) > 1


@pytest.mark.parametrize("difficulty", BANDS)
def test_every_five_demo_window_refutes_independent_endpoint_complement(gen, canonical, difficulty):
    # This rival fits all nine official binary examples. It also fits a sampler
    # that always puts the two other core colors at the contrast endpoints.
    for pair in [*canonical["train"], *canonical["test"]]:
        assert _endpoint_complement(pair["input"]) == pair["output"]
    for seed in (0, 17, 211, 1703):
        for start in range(15):
            demos = [gen.generate(seed, index, difficulty=difficulty)
                     for index in range(start, start + 5)]
            assert any(_endpoint_complement(grid) != GLYPHS[_pixels(grid)["mode_color"]]
                       for grid in demos), (difficulty, seed, start)


@pytest.mark.parametrize("difficulty", BANDS)
def test_every_five_demo_window_refutes_independent_endpoint_limited_mode(gen, canonical, difficulty):
    # Merely varying which endpoint carries the mode leaves this counting
    # shortcut untouched: a mode absent from both endpoints is required.
    for pair in [*canonical["train"], *canonical["test"]]:
        assert _endpoint_limited_mode(pair["input"]) == pair["output"]
    for seed in (0, 17, 211, 1703):
        for start in range(15):
            demos = [gen.generate(seed, index, difficulty=difficulty)
                     for index in range(start, start + 5)]
            assert any(_endpoint_limited_mode(grid) != GLYPHS[_pixels(grid)["mode_color"]]
                       for grid in demos), (difficulty, seed, start)


@pytest.mark.parametrize("difficulty", BANDS)
def test_every_five_demo_window_refutes_all_callable_rivals(gen, difficulty):
    assert gen.EXAMPLES_NEEDED == 5
    assert gen.SEMANTIC_RIVALS
    for seed in (0, 17, 211):
        for start in (0, 1, 2, 4, 8, 13):
            demos = [gen.generate(seed, index, difficulty=difficulty)
                     for index in range(start, start + 5)]
            observations = [_pixels(grid) for grid in demos]
            assert {o["mode_color"] for o in observations} == {1, 2, 3}
            assert any((o["grid_h"], o["grid_w"], o["palette_size"]) == (5, 5, 2)
                       for o in observations)
            assert sum(o["palette_size"] > 2 for o in observations) >= 2
            for name, rival in gen.SEMANTIC_RIVALS.items():
                assert callable(rival), name
                assert any(rival(copy.deepcopy(grid)) != GLYPHS[observed["mode_color"]]
                           for grid, observed in zip(demos, observations)), (seed, start, name)


def test_replay_freshness_and_global_random_isolation(gen):
    state = random.getstate()
    try:
        for difficulty in BANDS:
            for index in range(6):
                grid = gen.generate(991, index, difficulty=difficulty)
                expected = copy.deepcopy(grid)
                assert random.getstate() == state
                gen.generate(3, 19, difficulty=difficulty, mode_count=95)
                assert gen.generate(991, index, difficulty=difficulty) == expected
                grid[0][0] = 9
                assert gen.generate(991, index, difficulty=difficulty) == expected
                assert random.getstate() == state
    finally:
        random.setstate(state)


def _component_sizes_independent(grid, diagonal=False):
    """Independent flood fill; the production helper is not imported here."""
    neighbors = ((-1, 0), (1, 0), (0, -1), (0, 1))
    if diagonal:
        neighbors += ((-1, -1), (-1, 1), (1, -1), (1, 1))
    remaining = {(r, c) for r, row in enumerate(grid)
                 for c, color in enumerate(row) if color != 0}
    sizes = []
    while remaining:
        root = min(remaining)
        color = grid[root[0]][root[1]]
        frontier = [root]
        remaining.remove(root)
        count = 0
        while frontier:
            r, c = frontier.pop()
            count += 1
            for dr, dc in neighbors:
                cell = (r + dr, c + dc)
                if cell in remaining and grid[cell[0]][cell[1]] == color:
                    remaining.remove(cell)
                    frontier.append(cell)
        sizes.append((count, color))
    return sizes


def _largest_component_independent(grid, diagonal=False):
    components = _component_sizes_independent(grid, diagonal)
    color = max(components, key=lambda item: (item[0], -item[1]))[1]
    return GLYPHS.get(color, [[0] * 3 for _ in range(3)])


def _largest_bbox_independent(grid):
    colors = {v for row in grid for v in row if v}
    areas = {}
    for color in colors:
        cells = [(r, c) for r, row in enumerate(grid)
                 for c, value in enumerate(row) if value == color]
        height = max(r for r, c in cells) - min(r for r, c in cells) + 1
        width = max(c for r, c in cells) - min(c for r, c in cells) + 1
        areas[color] = height * width
    return GLYPHS.get(max(areas, key=lambda c: (areas[c], -c)), [[0] * 3 for _ in range(3)])


SPATIAL_RIVALS_INDEPENDENT = {
    "largest_component_4": lambda g: _largest_component_independent(g),
    "largest_component_8": lambda g: _largest_component_independent(g, diagonal=True),
    "largest_color_bbox": _largest_bbox_independent,
}


@pytest.mark.parametrize("rival_name", SPATIAL_RIVALS_INDEPENDENT)
@pytest.mark.parametrize("difficulty", BANDS)
def test_five_demo_windows_refute_spatial_selection_shortcuts(gen, canonical, difficulty, rival_name):
    rival = SPATIAL_RIVALS_INDEPENDENT[rival_name]
    # Same-color canonical examples cannot distinguish color frequency from
    # connected-object size or bounding-box area.
    for pair in [*canonical["train"], *canonical["test"]]:
        assert rival(pair["input"]) == pair["output"]
    for seed in (0, 1, 17, 23, 1703):
        grids = [gen.generate(seed, i, difficulty=difficulty) for i in range(19)]
        for start in range(15):
            demos = grids[start:start + 5]
            assert any(rival(g) != GLYPHS[_pixels(g)["mode_color"]] for g in demos), (
                rival_name, difficulty, seed, start)


@pytest.mark.parametrize("difficulty", BANDS)
def test_spatial_witness_and_endpoint_condition_are_crossed_independently(gen, difficulty):
    crossed = set()
    witness_modes = set()
    free_modes = set()
    for seed in range(30):
        for block in range(3):
            witnesses = 0
            for i in range(3 * block, 3 * block + 3):
                g = gen.generate(seed, i, difficulty=difficulty)
                mode = _pixels(g)["mode_color"]
                if gen.schedule_profile(seed, i) == "canonical_anchor":
                    continue
                spatial = gen.schedule_spatial_witness(seed, i)
                values = [v for row in g for v in row if v]
                mode_at_endpoint = mode in (values[0], values[-1])
                crossed.add((spatial, mode_at_endpoint))
                (witness_modes if spatial else free_modes).add(mode)
                witnesses += int(spatial)
                if spatial:
                    modal8 = max(n for n, color in _component_sizes_independent(g, True) if color == mode)
                    other4 = max(n for n, color in _component_sizes_independent(g) if color != mode)
                    assert other4 > modal8, "witness must be strict, not a tie-break artifact"
                    assert _largest_bbox_independent(g) != GLYPHS[mode]
            assert witnesses == 1
    assert crossed == {(False, False), (False, True), (True, False), (True, True)}
    assert witness_modes == free_modes == {1, 2, 3}


def test_spatial_rivals_distinguish_diagonal_from_orthogonal_connectivity(gen):
    # A helper-level example, not a claim of curriculum validity (mode count 3).
    g = [[1, 0, 2, 2], [0, 1, 0, 0], [0, 0, 1, 0]]
    assert gen.SEMANTIC_RIVALS["largest_component_4"](g) == GLYPHS[2]
    assert gen.SEMANTIC_RIVALS["largest_component_8"](g) == GLYPHS[1]
    assert g == [[1, 0, 2, 2], [0, 1, 0, 0], [0, 0, 1, 0]]
