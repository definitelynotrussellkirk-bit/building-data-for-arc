"""Task-local regression tests for the common-shape-across-panels generator."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from importlib.util import module_from_spec, spec_from_file_location
import hashlib
import json
import os
from pathlib import Path
import random
import sys

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "1cbcf1ed9a32"
HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = spec_from_file_location(f"review_{TASK_ID}", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
GEN = module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)
ROOT = find_root(__file__)


def _normalize(cells):
    cells = tuple(cells)
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return tuple(sorted((r - top, c - left) for r, c in cells))


def _rot90(cells):
    cells = _normalize(cells)
    max_r = max(r for r, _ in cells)
    return _normalize((c, max_r - r) for r, c in cells)


def _mirror(cells):
    cells = _normalize(cells)
    max_c = max(c for _, c in cells)
    return _normalize((r, max_c - c) for r, c in cells)


def _orbit(cells):
    base = _normalize(cells)
    result = set()
    for reflected in (False, True):
        cur = _mirror(base) if reflected else base
        for _ in range(4):
            result.add(_normalize(cur))
            cur = _rot90(cur)
    return tuple(sorted(result))


def _canonical(cells):
    return _orbit(cells)[0]


def _components(panel):
    height, width = len(panel), len(panel[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            color = panel[row][col]
            if color == 0 or (row, col) in seen:
                continue
            cells = []
            stack = [(row, col)]
            seen.add((row, col))
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    point = r + dr, c + dc
                    rr, cc = point
                    if (
                        0 <= rr < height
                        and 0 <= cc < width
                        and point not in seen
                        and panel[rr][cc] == color
                    ):
                        seen.add(point)
                        stack.append(point)
            result.append((color, tuple(cells)))
    return result


def _panel_records(grid):
    height, width = len(grid), len(grid[0])
    dividers = [
        col for col in range(width) if all(grid[row][col] == 5 for row in range(height))
    ]
    assert len(dividers) == 2
    bounds = ((0, dividers[0]), (dividers[0] + 1, dividers[1]), (dividers[1] + 1, width))
    records = []
    for start, stop in bounds:
        panel = [row[start:stop] for row in grid]
        comps = _components(panel)
        largest_size = max(len(cells) for _, cells in comps)
        largest = [(color, cells) for color, cells in comps if len(cells) == largest_size]
        assert len(largest) == 1
        color, cells = largest[0]
        records.append(
            {
                "color": color,
                "cells": _normalize(cells),
                "canonical": _canonical(cells),
                "size": len(cells),
                "component_sizes": sorted(len(part) for _, part in comps),
            }
        )
    return records


def _render(cells):
    cells = _normalize(cells)
    height = max(r for r, _ in cells) + 1
    width = max(c for _, c in cells) + 1
    out = [[0] * width for _ in range(height)]
    for row, col in cells:
        out[row][col] = 8
    return out


def _oracle(grid):
    records = _panel_records(grid)
    signatures = [record["canonical"] for record in records]
    counts = Counter(signatures)
    common = max(counts, key=lambda signature: counts[signature])
    return _render(common)


def _canonical_pairs():
    return canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def _pair_from_records(records):
    signatures = [record["canonical"] for record in records]
    counts = Counter(signatures)
    common = max(counts, key=lambda signature: counts[signature])
    return ",".join(str(index) for index, signature in enumerate(signatures) if signature == common)


def test_rule_pin_and_all_canonical_pairs_match_an_independent_oracle():
    assert GEN.RULE_HASH == "dc0d41aa47ba"
    pairs = _canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        original = deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert _oracle(pair["input"]) == pair["output"]
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "requested",
    [
        {
            "grid_h": 5,
            "panel_w": 4,
            "common_cells": 3,
            "common_pair": "1,2",
            "palette_kind": "default",
            "secondary_objects": "none",
        },
        {
            "grid_h": 6,
            "panel_w": 5,
            "common_cells": 5,
            "common_pair": "0,2",
            "palette_kind": "warm",
            "secondary_objects": "singletons",
        },
        {
            "grid_h": 8,
            "panel_w": 7,
            "common_cells": 7,
            "common_pair": "0,1",
            "palette_kind": "cool",
            "secondary_objects": "singletons",
        },
    ],
)
def test_exact_overrides_round_trip_in_every_band(band, requested):
    grid = GEN.generate(91, 17, difficulty=band, **requested)
    assert GEN.self_check(grid) == []
    assert GEN.strict_canonical_like(grid) == []
    assert GEN.observe_overrides(grid) == requested
    records = _panel_records(grid)
    assert {record["size"] for record in records} == {requested["common_cells"]}
    assert _pair_from_records(records) == requested["common_pair"]
    expected_components = [requested["common_cells"]]
    if requested["secondary_objects"] == "singletons":
        expected_components = [1, requested["common_cells"]]
    assert all(record["component_sizes"] == expected_components for record in records)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo_axis": 1},
        {"shape": 2},
        {"d4_variant_idx": 1},
        {"texture": "all_match"},
        {"grid_h": True},
        {"grid_h": 4},
        {"panel_w": 8},
        {"common_cells": 2},
        {"common_cells": 4.0},
        {"common_pair": 12},
        {"common_pair": "2,1"},
        {"palette_kind": "unknown"},
        {"secondary_objects": "two_objects_per_panel"},
    ],
)
def test_invalid_and_retired_overrides_fail_loudly(kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **kwargs)


@pytest.mark.parametrize("seed,sample_index", [(True, 0), (1.5, 0), ("1", 0), (1, True), (1, -1), (1, 2.5)])
def test_seed_and_sample_index_are_strict(seed, sample_index):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(seed, sample_index)


def test_unsupported_difficulty_is_rejected():
    with pytest.raises(ValueError):
        GEN.generate(1, 0, difficulty="extreme")


def test_default_schedule_does_not_lock_size_to_panel_width():
    observed = [
        GEN.observe_overrides(GEN.generate(19, index, difficulty="medium"))
        for index in range(GEN.LESSON_SCHEDULE_PERIOD)
    ]
    pairs = {(row["common_cells"], row["panel_w"]) for row in observed}
    assert len(pairs) > len({row["common_cells"] for row in observed})


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_schedule_has_canonical_profile_support_and_refutes_declared_rivals(band):
    assert GEN.EXAMPLES_NEEDED == 4
    assert GEN.LESSON_SCHEDULE_PERIOD == 4
    expected_profiles = set(GEN.SCHEDULE_PROFILES)
    for start in range(GEN.LESSON_SCHEDULE_PERIOD):
        indices = range(start, start + GEN.EXAMPLES_NEEDED)
        assert {GEN.schedule_profile(0, index, band) for index in indices} == expected_profiles
        demos = []
        for index in indices:
            grid = GEN.generate(2026, index, difficulty=band)
            demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
        assert any((len(pair["input"]), len(pair["input"][0])) == (5, 14) for pair in demos)
        assert all(
            any(rival(pair["input"]) != pair["output"] for pair in demos)
            for rival in GEN.LESSON_COMPETITORS.values()
        )
        query_grid = GEN.generate(2026, start + GEN.EXAMPLES_NEEDED, difficulty=band)
        query = {"input": query_grid, "output": GEN.rule_mirror(query_grid)}
        assert GEN.lesson_identifiable(demos, query) == []


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_query_rotation_of_a_five_pair_window_is_identifiable(band):
    for seed in (0, 7):
        for start in range(GEN.LESSON_SCHEDULE_PERIOD):
            pairs = []
            for index in range(start, start + GEN.EXAMPLES_NEEDED + 1):
                grid = GEN.generate(seed, index, difficulty=band)
                pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
            for query_index, query in enumerate(pairs):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                assert GEN.lesson_identifiable(demos, query) == []


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_generated_objects_have_equal_size_but_only_two_share_d4_class(band):
    seen_outputs = set()
    seen_pairs = set()
    for index in range(80):
        grid = GEN.generate(700 + index, index, difficulty=band)
        assert GEN.self_check(grid) == []
        records = _panel_records(grid)
        assert len({record["size"] for record in records}) == 1
        counts = Counter(record["canonical"] for record in records)
        assert sorted(counts.values()) == [1, 2]
        pair = _pair_from_records(records)
        seen_pairs.add(pair)
        matching = [record["cells"] for record in records if counts[record["canonical"]] == 2]
        assert len(set(matching)) == 2  # translation-only equality is deliberately insufficient
        seen_outputs.add(tuple(map(tuple, GEN.rule_mirror(grid))))
    assert seen_pairs == {"0,1", "0,2", "1,2"}
    assert len(seen_outputs) >= 35


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_first_twenty_draws_hit_the_exact_canonical_input_profile(band):
    profiles = {
        (len(grid), len(grid[0]), len({value for row in grid for value in row}))
        for index in range(20)
        for grid in [GEN.generate(1200 + index, index, difficulty=band)]
    }
    assert (5, 14, 5) in profiles


def test_canonical_shortcuts_fit_canonical_labels_but_generated_witnesses_refute_them():
    pairs = _canonical_pairs()
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name
    for index in range(16):
        grid = GEN.generate(17, index, common_pair="1,2")
        assert GEN.SEMANTIC_WITNESSES["panel_zero_distractor"](grid)
        truth = GEN.rule_mirror(grid)
        assert all(rival(grid) != truth for rival in GEN.SEMANTIC_RIVALS.values())


def test_retained_counterexample_is_exact_and_source_bound():
    path = HOME / "counterexamples" / "repeated_cell_count_else_first_panel.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["generator_sha256"] == hashlib.sha256(Path(GEN.__file__).read_bytes()).hexdigest()
    grid = GEN.generate(
        record["seed"],
        record["sample_index"],
        difficulty=record["difficulty"],
        **record["overrides"],
    )
    assert grid == record["input"]
    assert GEN.observe_overrides(grid) == record["observed_axes"]
    assert GEN.rule_mirror(grid) == record["intended_output"]
    rival = GEN.CANONICAL_SHORTCUTS[record["rival_name"]]
    assert rival(grid) == record["rival_output"]
    assert record["rival_output"] != record["intended_output"]


def test_self_check_rejects_malformed_and_semantic_impostors():
    good = GEN.generate(44, 3, common_pair="1,2", secondary_objects="singletons")
    cases = [None, [], [[]], [[0], [0, 1]], [[True] * 14 for _ in range(5)]]
    ragged = deepcopy(good)
    ragged[0].pop()
    cases.append(ragged)
    no_divider = deepcopy(good)
    divider = next(
        col for col in range(len(good[0])) if all(row[col] == 5 for row in good)
    )
    for row in no_divider:
        row[divider] = 0
    cases.append(no_divider)
    tied_largest = deepcopy(good)
    # Grow one reserved singleton into a domino, preserving disconnection.
    last_row = len(tied_largest) - 1
    first_start = 0
    panel_width = GEN.observe_overrides(good)["panel_w"]
    first_panel_color = next(
        value
        for value in tied_largest[last_row][first_start:first_start + panel_width]
        if value not in (0, 5)
    )
    singleton_col = next(
        col
        for col in range(panel_width)
        if tied_largest[last_row][first_start + col] == first_panel_color
    )
    other_col = singleton_col + 1 if singleton_col < panel_width - 1 else singleton_col - 1
    tied_largest[last_row][first_start + other_col] = first_panel_color
    cases.append(tied_largest)
    for case in cases:
        assert GEN.self_check(case)


def test_generation_is_deterministic_fresh_and_does_not_touch_global_random():
    random.seed(90210)
    state = random.getstate()
    first = GEN.generate(31, 8, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(31, 8, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert GEN.generate(31, 8, difficulty="hard") == second
