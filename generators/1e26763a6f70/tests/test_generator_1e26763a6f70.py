"""Portable semantic and contract regressions for 1e26763a6f70."""
from __future__ import annotations

from collections import Counter
import copy
import random
from statistics import median

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "1e26763a6f70"
ROOT = find_root(__file__)
GEN, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
CANONICAL = canonical_pairs(TASK_ID, root=ROOT)
CANONICAL_SHAPES = {(5, 7), (7, 6), (7, 7)}


def _pairs(grid):
    positions: dict[int, list[tuple[int, int]]] = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                positions.setdefault(value, []).append((r, c))
    records = []
    for color, cells in positions.items():
        if len(cells) != 2:
            continue
        (r1, c1), (r2, c2) = cells
        if r1 == r2:
            orientation = "horizontal"
            span = abs(c2 - c1)
        elif c1 == c2:
            orientation = "vertical"
            span = abs(r2 - r1)
        else:
            orientation = "diagonal"
            span = -1
        records.append((color, orientation, span, cells))
    return records


def _label(grid):
    return {"input": copy.deepcopy(grid), "output": GEN.rule_mirror(grid)}


def test_rule_pin_and_canonical_semantics():
    assert GEN.RULE_HASH == "dffe1ada0168"
    assert len(CANONICAL) == 3
    for pair in CANONICAL:
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 5, "grid_w": 5, "pairs": 1},
        {"grid_h": 5, "grid_w": 5, "pairs": 4},
        {"grid_h": 7, "grid_w": 6, "pairs": 3},
        {"grid_h": 12, "grid_w": 12, "pairs": 4},
    ],
)
def test_exact_overrides_round_trip_in_every_band(band, overrides):
    grid = GEN.generate(17, 29, difficulty=band, **overrides)
    assert GEN.self_check(grid, difficulty=band) == []
    assert GEN.observe_overrides(grid) == overrides


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo_axis": 1},
        {"grid_h": 4},
        {"grid_h": 13},
        {"grid_w": True},
        {"pairs": 0},
        {"pairs": 5},
        {"pairs": 1.0},
    ],
)
def test_invalid_overrides_are_rejected(kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **kwargs)


@pytest.mark.parametrize("sample_index", [True, False, 1.0, "1", -1])
def test_invalid_sample_index_is_rejected(sample_index):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, sample_index)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_schedule_has_rich_teaching_support_and_canonical_anchors(band):
    canonical_hits = 0
    for start in range(18):
        profiles = [GEN.schedule_profile(0, i, band) for i in range(start, start + 4)]
        assert sum(name.startswith("rich_") for name in profiles) >= 2

    for index in range(36):
        grid = GEN.generate(1000 + index, index, difficulty=band)
        assert GEN.self_check(grid, difficulty=band) == []
        assert grid == GEN.generate(1000 + index, index, difficulty=band)
        records = _pairs(grid)
        profile = GEN.schedule_profile(0, index, band)
        if profile.startswith("rich_"):
            orientations = {record[1] for record in records}
            spans = {record[2] for record in records}
            assert orientations == {"horizontal", "vertical"}
            assert 2 in spans
            assert any(span >= 4 for span in spans)
            assert len(records) == 3
        if (len(grid), len(grid[0])) in CANONICAL_SHAPES and len(records) == 1:
            canonical_hits += 1
    assert canonical_hits >= 3


def test_default_stream_stays_inside_canonical_object_count_band():
    # The official distribution gate compares median component count against
    # the canonical one-pair inputs.  Since each lawful pair contributes two
    # disconnected endpoints, keeping the median pair count <=3 keeps the
    # generated object median within the gate's 3x tolerance.
    pair_counts = [
        len(_pairs(GEN.generate(seed, seed, difficulty=band)))
        for band in ("easy", "medium", "hard")
        for seed in range(1, 21)
    ]
    assert median(pair_counts) <= 3
    assert sorted(pair_counts)[len(pair_counts) // 2] <= 3


def test_every_rotated_four_pair_lesson_refutes_declared_competitors():
    for band in ("easy", "medium", "hard"):
        for start in range(18):
            pairs = [_label(GEN.generate(77, start + offset, difficulty=band)) for offset in range(4)]
            for query_index in range(4):
                query = pairs[query_index]
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                assert GEN.lesson_identifiable(demos, query) == []


def test_declared_canonical_shortcuts_really_fit_all_canonical_pairs():
    assert set(GEN.CANONICAL_SHORTCUTS) == {"first_pair_only", "span_four_only"}
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        for pair in CANONICAL:
            assert rival(pair["input"]) == pair["output"], name


def test_each_rich_scene_is_a_counterexample_to_every_lesson_competitor():
    for index in range(18):
        if not GEN.schedule_profile(0, index, "medium").startswith("rich_"):
            continue
        grid = GEN.generate(909, index, difficulty="medium")
        expected = GEN.rule_mirror(grid)
        for name, rival in GEN.LESSON_COMPETITORS.items():
            assert rival(grid) != expected, name


def test_self_check_rejects_structural_impostors():
    diagonal = [[0] * 7 for _ in range(7)]
    diagonal[1][1] = diagonal[3][3] = 2

    odd_span = [[0] * 7 for _ in range(7)]
    odd_span[2][1] = odd_span[2][4] = 3

    blocked = [[0] * 7 for _ in range(7)]
    blocked[3][1] = blocked[3][5] = 4
    blocked[3][3] = 8

    duplicate_midpoint = [[0] * 7 for _ in range(7)]
    duplicate_midpoint[3][1] = duplicate_midpoint[3][5] = 2
    duplicate_midpoint[1][3] = duplicate_midpoint[5][3] = 6

    singleton = [[0] * 7 for _ in range(7)]
    singleton[2][2] = 5

    for grid in (diagonal, odd_span, blocked, duplicate_midpoint, singleton):
        assert GEN.self_check(grid)


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True] * 5 for _ in range(5)]],
)
def test_malformed_grids_return_diagnostics(grid):
    assert GEN.self_check(grid)


def test_generated_colors_are_distinct_pairs_and_midpoints_are_empty():
    for index in range(128):
        grid = GEN.generate(31337, index, difficulty="hard")
        counts = Counter(value for row in grid for value in row if value)
        assert set(counts.values()) == {2}
        midpoints = []
        for _, orientation, span, cells in _pairs(grid):
            assert orientation in {"horizontal", "vertical"}
            assert span >= 2 and span % 2 == 0
            (r1, c1), (r2, c2) = cells
            mid = ((r1 + r2) // 2, (c1 + c2) // 2)
            assert grid[mid[0]][mid[1]] == 0
            midpoints.append(mid)
        assert len(midpoints) == len(set(midpoints))


def test_generation_does_not_touch_global_random_state():
    before = random.getstate()
    first = GEN.generate(123, 456, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(123, 456, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))


def test_retained_counterexample_refutes_every_canonical_shortcut():
    import json

    # Reconstruct the source-bound witness so this regression remains portable
    # when the task-test snapshot intentionally omits authoring-only evidence.
    grid = GEN.generate(20261012, 1, difficulty="medium")
    expected = GEN.rule_mirror(grid)
    rival_outputs = {
        name: rival(grid) for name, rival in GEN.CANONICAL_SHORTCUTS.items()
    }
    assert GEN.schedule_profile(20261012, 1, "medium") == "rich_8x9_horizontal_long"
    assert GEN.self_check(grid) == []
    for name, output in rival_outputs.items():
        assert output != expected, name

    # In the authoring repository, additionally bind the retained JSON bytes to
    # the exact generator and reconstructed witness. Portable runtimes still
    # test the same deterministic counterexample above.
    path = SOURCE_PATH.parent / "counterexamples" / "canonical-shortcuts.json"
    if path.exists():
        payload = json.loads(path.read_text())
        assert payload["generator_sha256"] == SOURCE_SHA256
        assert payload["rule_hash"] == GEN.RULE_HASH
        assert payload["input"] == grid
        assert payload["intended_output"] == expected
        assert payload["rival_outputs"] == rival_outputs
