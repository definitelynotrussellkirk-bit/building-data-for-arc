"""Tests-first contracts for native modal-anchor component packing."""
from __future__ import annotations

from collections import Counter
import copy
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
PARAMETRIC = ROOT / "generators/579f1e2dcb4a/workspace/parametric"
RUNTIME = ROOT / "shared/runtime"
sys.path.insert(0, str(ROOT / "src"))
POLICIES = ("spatial", "anchor_color_ascending", "anchor_color_descending")
CANONICAL_SHA = "29c3632de610b7ee7d934b7b3251e244cc47e7d1d119a233e359d0711def0733"


def setting(policy):
    return {"pack_order": policy}


@lru_cache(None)
def load_adjacent(filename):
    path = PARAMETRIC / filename
    name = "_native_test_579f1e2dcb4a_" + path.stem
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    assert Path(module.__file__).resolve() == path.resolve()
    return module


@pytest.fixture(scope="module")
def family():
    return load_adjacent("native_family.py")


@pytest.fixture(scope="module")
def adapter():
    return load_adjacent("adapter.py")


@pytest.fixture(scope="module")
def racket():
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator

    with _local_imports(RUNTIME, PARAMETRIC):
        apply_program, identity, bridge = _real_evaluator(RUNTIME)
        assert identity["backend"] == "racket" and identity["protected"] is True
        try:
            yield apply_program
        finally:
            bridge.close()


def canonical_row():
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open() as handle:
        selected = [row for line in handle if (row := json.loads(line)).get("task_id") == "579f1e2dcb4a"]
    assert len(selected) == 1
    return selected[0]


def put(grid, crop, top, left):
    for r, row in enumerate(crop):
        for c, value in enumerate(row):
            grid[top + r][left + c] = value


def literal_pack(crops):
    """Arrange already literal crops in an explicitly authored order."""
    height = max(len(crop) for crop in crops)
    output = [[] for _ in range(height)]
    for index, crop in enumerate(crops):
        width = len(crop[0])
        for r in range(height):
            if index:
                output[r].append(0)
            output[r].extend(crop[r] if r < len(crop) else [0] * width)
    return output


def modal_fixture():
    anchor = [[3, 1, 3], [3, 1, 3]]
    count_two = [[3, 3, 8]]
    count_one = [[3], [2]]
    grid = [[0] * 11 for _ in range(5)]
    put(grid, anchor, 1, 7)
    put(grid, count_two, 4, 1)
    put(grid, count_one, 1, 4)
    expected = {
        "spatial": [[3, 3, 8, 0, 3, 0, 3, 1, 3], [0, 0, 0, 0, 2, 0, 3, 1, 3]],
        "anchor_color_ascending": [[3, 0, 3, 3, 8, 0, 3, 1, 3], [2, 0, 0, 0, 0, 0, 3, 1, 3]],
        "anchor_color_descending": [[3, 1, 3, 0, 3, 3, 8, 0, 3], [3, 1, 3, 0, 0, 0, 0, 0, 2]],
    }
    return grid, expected


def foreign_crop_fixture():
    ring_raw_crop = [[5, 5, 5, 5, 5], [5, 0, 0, 0, 5], [5, 0, 6, 0, 5],
                     [5, 0, 0, 0, 5], [5, 5, 5, 5, 5]]
    singleton = [[6]]
    anchor = [[6, 1, 2, 3, 4, 5], [6, 1, 2, 3, 4, 5], [6, 6, 7, 7, 8, 9]]
    grid = [[0] * 15 for _ in range(7)]
    put(grid, ring_raw_crop, 1, 1)
    put(grid, anchor, 0, 8)
    return grid, {
        "spatial": literal_pack([ring_raw_crop, singleton, anchor]),
        "anchor_color_ascending": literal_pack([ring_raw_crop, singleton, anchor]),
        "anchor_color_descending": literal_pack([anchor, singleton, ring_raw_crop]),
    }


def diagonal_tie_fixture():
    upper = [[2, 0], [7, 7]]
    lower = [[0, 0, 2], [8, 8, 8]]
    anchor = [[2, 2, 3], [2, 2, 3]]
    grid = [[0] * 10 for _ in range(8)]
    put(grid, upper, 0, 1)
    put(grid, lower, 2, 1)
    put(grid, anchor, 5, 6)
    spatial = [[2, 0, 0, 0, 0, 2, 0, 2, 2, 3], [7, 7, 0, 8, 8, 8, 0, 2, 2, 3]]
    descending = [[2, 2, 3, 0, 2, 0, 0, 0, 0, 2], [2, 2, 3, 0, 7, 7, 0, 8, 8, 8]]
    return grid, {"spatial": spatial, "anchor_color_ascending": spatial,
                  "anchor_color_descending": descending}


def test_canonical_default_is_byte_exact_and_adapter_delegates(family, adapter):
    canonical = canonical_row()["program_solution"]
    assert hashlib.sha256(canonical.encode()).hexdigest() == CANONICAL_SHA
    assert family.program(setting("spatial")) == canonical
    for policy in POLICIES:
        assert adapter.program(setting(policy)) == family.program(setting(policy))


@pytest.mark.parametrize("fixture", [modal_fixture, foreign_crop_fixture, diagonal_tie_fixture])
def test_independent_literal_packing_semantics(family, racket, fixture):
    grid, expected = fixture()
    unchanged = copy.deepcopy(grid)
    for policy in POLICIES:
        assert family.apply_claim(grid, setting(policy)) == expected[policy]
        assert racket(family.program(setting(policy)), grid) == expected[policy]
    assert grid == unchanged


def components(grid, diagonal=False):
    remaining = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
    directions = ((-1, 0), (1, 0), (0, -1), (0, 1))
    if diagonal:
        directions += ((-1, -1), (-1, 1), (1, -1), (1, 1))
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        found, stack = {start}, [start]
        while stack:
            r, c = stack.pop()
            for dr, dc in directions:
                point = (r + dr, c + dc)
                if point in remaining:
                    remaining.remove(point)
                    found.add(point)
                    stack.append(point)
        result.append(found)
    return result


def bbox(cells):
    return (min(r for r, c in cells), min(c for r, c in cells),
            max(r for r, c in cells), max(c for r, c in cells))


def check_shared_grammar(grid):
    assert type(grid) is list and 1 <= len(grid) <= 30
    assert type(grid[0]) is list and 1 <= len(grid[0]) <= 30
    width = len(grid[0])
    assert all(type(row) is list and len(row) == width
               and all(type(value) is int and 0 <= value <= 9 for value in row) for row in grid)
    groups = components(grid)
    assert 2 <= len(groups) <= 6
    ordered = sorted(groups, key=len)
    assert len(ordered[-1]) > len(ordered[-2])
    counts = Counter(grid[r][c] for r, c in ordered[-1])
    assert list(counts.values()).count(max(counts.values())) == 1
    boxes = [bbox(group) for group in groups]
    out_shape = [max(r1 - r0 + 1 for r0, c0, r1, c1 in boxes),
                 sum(c1 - c0 + 1 for r0, c0, r1, c1 in boxes) + len(groups) - 1]
    assert out_shape[1] <= 30
    return groups, out_shape


def test_authored_foreign_crop_and_connectivity_facts():
    grid, expected = foreign_crop_fixture()
    groups, out_shape = check_shared_grammar(grid)
    assert sorted(map(len, groups)) == [1, 16, 18]
    anchor = max(groups, key=len)
    assert Counter(grid[r][c] for r, c in anchor).most_common(1) == [(6, 4)]
    assert Counter(value for row in grid for value in row if value).most_common(1) == [(5, 18)]
    assert sorted(sum(grid[r][c] == 6 for r, c in group) for group in groups) == [0, 1, 4]
    assert sum(value != 0 for row in grid for value in row) == 35
    for output in expected.values():
        assert [len(output), len(output[0])] == out_shape == [5, 14]
        assert sum(value != 0 for row in output for value in row) == 36
    diagonal, _ = diagonal_tie_fixture()
    assert len(components(diagonal)) == 3
    assert len(components(diagonal, diagonal=True)) == 2
    boxes = [bbox(group) for group in components(diagonal)]
    assert boxes[0][:2] == (0, 1) and boxes[1][:2] == (2, 1)


@pytest.mark.parametrize("rival_name", ["masked_crops", "solid_crops"])
def test_crop_rivals_use_bbox_dimensions(family, racket, rival_name):
    grid, expected = foreign_crop_fixture()
    rival = family.rivals(setting("spatial"))[rival_name]
    actual = racket(rival, grid)
    assert [len(actual), len(actual[0])] == [5, 14]
    if rival_name == "masked_crops":
        masked = copy.deepcopy(expected["spatial"])
        assert masked[2][2] == 6
        masked[2][2] = 0
        assert actual == masked
        assert sum(value != 0 for row in actual for value in row) == 35
    else:
        # Three solid rectangles: 5x5, 1x1, 3x6; gaps/padding remain zero.
        assert sum(value != 0 for row in actual for value in row) == 44


@pytest.mark.parametrize("rival_name", ["color_raw_crop", "raw_crop_counts"])
def test_raw_crop_rivals_respect_inclusive_input_boundaries(family, racket, rival_name):
    original, expected = foreign_crop_fixture()
    grid = [row[:-1] for row in original[:-1]]
    assert any(grid[-1]) and any(row[-1] for row in grid)
    check_shared_grammar(grid)
    anchor = [row[8:14] for row in original[:3]]
    ring = [row[1:6] for row in original[1:6]]
    wanted = (expected["anchor_color_descending"] if rival_name == "color_raw_crop"
              else literal_pack([anchor, ring, [[6]]]))
    actual = racket(family.rivals(setting("anchor_color_descending"))[rival_name], grid)
    assert actual == wanted
    assert [len(actual), len(actual[0])] == [5, 14]


@pytest.mark.parametrize("rival_name", ["anchor_bbox", "anchor_height", "anchor_width"])
def test_bbox_anchor_rivals_select_geometry_not_absolute_endpoints(family, racket, rival_name):
    original, _ = foreign_crop_fixture()
    ring = [row[1:6] for row in original[1:6]]
    anchor = [row[8:14] for row in original[:3]]
    if rival_name == "anchor_bbox":
        grid = original
        # Ring bbox25 exceeds the occupied-largest object's bbox18.
        wanted = literal_pack([[[6]], anchor, ring])
    elif rival_name == "anchor_height":
        grid = [[0] * 15 for _ in range(11)]
        put(grid, ring, 1, 1)
        put(grid, anchor, 7, 8)
        # Ring height5 beats anchor height3, although its bottom row is smaller.
        wanted = literal_pack([[[6]], anchor, ring])
    else:
        grid = [[0] * 14 for _ in range(7)]
        put(grid, anchor, 0, 0)
        put(grid, ring, 1, 8)
        # Anchor width6 beats ring width5, although its right column is smaller.
        wanted = literal_pack([ring, [[6]], anchor])
    check_shared_grammar(grid)
    actual = racket(family.rivals(setting("anchor_color_ascending"))[rival_name], grid)
    assert actual == wanted


def test_default_replays_all_five_official_pairs(family, racket):
    row = canonical_row()
    pairs = row["train"] + row["test"]
    assert len(pairs) == 5
    for pair in pairs:
        result = racket(family.program(setting("spatial")), pair["input"])
        assert result == pair["output"]
        assert family.apply_claim(pair["input"], setting("spatial")) == result


def test_six_components_allow_singletons_and_nonanchor_area_ties(family, racket):
    grid = [[0] * 10 for _ in range(7)]
    anchor = [[2, 2, 3], [2, 2, 3]]
    put(grid, anchor, 0, 6)
    for r, c, color in ((0, 0, 9), (2, 0, 2), (4, 2, 2), (2, 4, 8), (5, 9, 2)):
        grid[r][c] = color
    assert sorted(map(len, components(grid))) == [1, 1, 1, 1, 1, 6]
    expected = {
        "spatial": literal_pack([[[9]], [[2]], [[2]], [[8]], anchor, [[2]]]),
        "anchor_color_ascending": literal_pack([[[9]], [[8]], [[2]], [[2]], [[2]], anchor]),
        "anchor_color_descending": literal_pack([anchor, [[2]], [[2]], [[2]], [[9]], [[8]]]),
    }
    for policy in POLICIES:
        assert family.apply_claim(grid, setting(policy)) == expected[policy]
        assert racket(family.program(setting(policy)), grid) == expected[policy]


@pytest.mark.parametrize("bad", [None, {}, {"pack_order": True}, {"pack_order": "ascending"},
                                 {"pack_order": "spatial", "extra": 1}])
def test_settings_are_exact_and_strict(family, bad):
    grid, _ = modal_fixture()
    for action in (lambda: family.program(bad), lambda: family.generate(0, bad, 3, 1),
                   lambda: family.apply_claim(grid, bad), lambda: family.describe(grid, bad),
                   lambda: family.rivals(bad)):
        with pytest.raises((ValueError, TypeError)):
            action()


@pytest.mark.parametrize("seed", [True, False, -1, 2**63, 1.5, "1", None])
def test_seed_is_a_literal_bounded_integer(family, seed):
    with pytest.raises((ValueError, TypeError)):
        family.generate(seed, setting("spatial"), 3, 1)


@pytest.mark.parametrize("demos,queries", [(2, 1), (7, 1), (True, 1), (3.0, 1),
                                          (3, 0), (3, 5), (3, True), (3, 1.0)])
def test_demo_and_query_bounds_are_strict(family, demos, queries):
    with pytest.raises((ValueError, TypeError)):
        family.generate(0, setting("spatial"), demos, queries)


def test_grid_grammar_rejects_bad_values_anchor_ties_and_packed_overflow(family):
    valid, _ = modal_fixture()
    malformed = [[], [[]], tuple(valid), [tuple(row) for row in valid],
                 valid[:-1] + [[0]], "not-a-grid", valid + [[0] * 11 for _ in range(26)],
                 [row + [0] * 20 for row in valid]]
    for value in (True, -1, 10, 3.0, "3"):
        grid = copy.deepcopy(valid)
        grid[1][7] = value
        malformed.append(grid)
    malformed.append([[1, 0, 2]])  # Two equally largest singleton components.
    malformed.append([[1, 2, 0, 3]])  # Largest component has tied color modes.
    malformed.append([[1, 1]])  # Only one component.
    seven = [[0] * 15 for _ in range(3)]
    seven[0][0] = seven[0][1] = 4
    for c in (3, 5, 7, 9, 11, 13):
        seven[2][c] = 6
    malformed.append(seven)
    too_wide_when_packed = [[1] * 30, [0] * 30, [2] * 29 + [0]]
    malformed.append(too_wide_when_packed)
    for grid in malformed:
        for policy in POLICIES:
            with pytest.raises((ValueError, TypeError)):
                family.apply_claim(grid, setting(policy))
            with pytest.raises((ValueError, TypeError)):
                family.describe(grid, setting(policy))


def test_claims_are_fresh_and_describe_exposes_both_shapes(family):
    grid, expected = foreign_crop_fixture()
    unchanged = copy.deepcopy(grid)
    for policy in POLICIES:
        selected = setting(policy)
        result = family.apply_claim(grid, selected)
        result[0][0] = 9 - result[0][0]
        assert family.apply_claim(grid, selected) == expected[policy]
        description = family.describe(grid, selected)
        assert description["input_shape"] == [7, 15]
        assert description["output_shape"] == [5, 14]
        assert grid == unchanged


def test_full_banks_have_independent_prefixes_matched_inputs_and_no_global_rng_effect(family, adapter):
    before_rng = random.getstate()
    reference_inputs = None
    for policy in POLICIES:
        selected = setting(policy)
        full = family.generate(7, selected, 6, 4)
        assert len(full["train"]) == 6 and len(full["test"]) == 4
        assert full == family.generate(7, selected, 6, 4)
        for demos, queries in ((3, 1), (3, 4), (6, 1), (4, 2), (5, 3)):
            smaller = family.generate(7, selected, demos, queries)
            assert smaller["train"] == full["train"][:demos]
            assert smaller["test"] == full["test"][:queries]
        inputs = [pair["input"] for pair in full["train"] + full["test"]]
        assert len({json.dumps(grid) for grid in inputs}) == 10
        if reference_inputs is None:
            reference_inputs = copy.deepcopy(inputs)
        else:
            assert inputs == reference_inputs
        for grid in inputs:
            check_shared_grammar(grid)
        assert adapter.generate(7, selected, 3, 1) == family.generate(7, selected, 3, 1)
        untouched = copy.deepcopy(full)
        full["train"][0]["input"][0][0] = 9 - full["train"][0]["input"][0][0]
        full["test"][0]["output"][0][0] = 9 - full["test"][0]["output"][0][0]
        assert family.generate(7, selected, 6, 4) == untouched
    assert random.getstate() == before_rng
    assert len(family.generate(2**63 - 1, setting("spatial"), 3, 1)["train"]) == 3


def test_three_demos_distinguish_policies_without_query_answers(family):
    for policy in POLICIES:
        episode = family.generate(0, setting(policy), 3, 4)
        for candidate in POLICIES:
            fits = all(family.apply_claim(pair["input"], setting(candidate)) == pair["output"]
                       for pair in episode["train"])
            assert fits == (candidate == policy)


@pytest.mark.parametrize("seed", [0, 17])
def test_first_two_demos_reverse_modal_color_numeric_order(family, seed):
    """Teach against fixed min/max color selection using observed own-cell histograms."""
    episode = family.generate(seed, setting("anchor_color_ascending"), 3, 1)
    keys = []
    for index, pair in enumerate(episode["train"]):
        grid = pair["input"]
        groups = components(grid)
        anchor = max(groups, key=len)
        counts = Counter(grid[r][c] for r, c in anchor)
        winners = [color for color, count in counts.items() if count == max(counts.values())]
        assert len(winners) == 1
        key = winners[0]
        keys.append(key)
        other_colors = set(counts) - {key}
        if index < 2:
            assert other_colors
            assert (key < min(other_colors)) if index == 0 else (key > max(other_colors))
    assert len(set(keys)) == 3


def test_generated_labels_and_substantive_30_by_30_stress_match_protected_racket(family, racket):
    for policy in POLICIES:
        selected = setting(policy)
        episode = family.generate(0, selected, 3, 4)
        stress = episode["test"][3]
        for grid in (stress["input"], stress["output"]):
            assert [len(grid), len(grid[0])] == [30, 30]
            assert sum(value != 0 for row in grid for value in row) >= 300
        grid = stress["input"]
        assert any(grid[0]) and any(grid[-1])
        assert any(row[0] for row in grid) and any(row[-1] for row in grid)
        for pair in episode["train"] + episode["test"]:
            _, output_shape = check_shared_grammar(pair["input"])
            actual = racket(family.program(selected), pair["input"])
            assert pair["output"] == actual
            assert family.apply_claim(pair["input"], selected) == actual
            assert [len(actual), len(actual[0])] == output_shape


def test_rivals_are_complete_executable_racket_sources(family, racket):
    grid, _ = modal_fixture()
    seen = set()
    for policy in POLICIES:
        rivals = family.rivals(setting(policy))
        assert isinstance(rivals, dict)
        assert all(type(name) is str and name for name in rivals)
        for source in rivals.values():
            assert type(source) is str and source.strip()
            if source in seen:
                continue
            seen.add(source)
            result = racket(source, grid)
            assert type(result) is list and 1 <= len(result) <= 30
            assert type(result[0]) is list and 1 <= len(result[0]) <= 30
            assert all(type(row) is list and len(row) == len(result[0])
                       and all(type(value) is int and 0 <= value <= 9 for value in row)
                       for row in result)


def test_public_turn_is_one_query_with_no_private_or_future_dependence(family):
    selected = setting("anchor_color_ascending")
    episode = family.generate(0, selected, 3, 4)
    unchanged = copy.deepcopy(episode)
    for index in range(4):
        public = family.public_turn(episode, index)
        assert set(public) == {"train", "test"}
        assert public["train"] == [{"input": pair["input"], "output": pair["output"]}
                                   for pair in episode["train"]]
        assert public["test"] == [{"input": episode["test"][index]["input"]}]
    first = family.public_turn(episode, 0)
    assert first == family.public_turn(family.generate(0, selected, 3, 1), 0)
    tainted = copy.deepcopy(episode)
    tainted.update(seed=999, settings=setting("anchor_color_descending"), program="private-program-marker")
    tainted["test"][0]["output"] = [[9]]
    tainted["test"][1]["input"] = [[8]]
    assert family.public_turn(tainted, 0) == first
    first["train"][0]["input"][0][0] = 9 - first["train"][0]["input"][0][0]
    first["train"][0]["output"][0][0] = 9 - first["train"][0]["output"][0][0]
    first["test"][0]["input"][0][0] = 9 - first["test"][0]["input"][0][0]
    assert episode == unchanged
    for index in (-1, 4, True, 0.0, None):
        with pytest.raises((ValueError, TypeError, IndexError)):
            family.public_turn(episode, index)
