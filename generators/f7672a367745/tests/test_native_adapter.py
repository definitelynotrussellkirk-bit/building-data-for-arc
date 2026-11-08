"""Independent literal tests for rectangle reconstruction, ranking, and paint."""
from __future__ import annotations

import copy
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys

import pytest

from arcpuzzles.parametric_worker import _local_imports, _real_evaluator

ROOT = Path(__file__).resolve().parents[3]
PARAMETRIC = ROOT / "generators/f7672a367745/workspace/parametric"
RUNTIME = ROOT / "shared/runtime"
POLICIES = ("outline", "largest", "smallest")
CANONICAL_SHA = "f641b0a1fe4253332c7b90eac0a58f983725f056bb473c0ce53bd89af6d4934c"


def setting(policy):
    return {"fill_policy": policy}


@lru_cache(None)
def load_adjacent(filename):
    path = PARAMETRIC / filename
    name = "_native_test_f7672a367745_" + path.stem
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
def canonical():
    path = ROOT / "shared/data/canonical/puzzles.jsonl"
    rows = [row for line in path.read_text().splitlines()
            if (row := json.loads(line))["task_id"] == "f7672a367745"]
    assert len(rows) == 1
    return rows[0]


@pytest.fixture(scope="module")
def racket():
    with _local_imports(RUNTIME, PARAMETRIC):
        apply_program, identity, bridge = _real_evaluator(RUNTIME)
        assert identity["backend"] == "racket" and identity["protected"] is True
        try:
            yield apply_program
        finally:
            bridge.close()


def literal_pair_fixture():
    grid = [[2, 0, 0, 0, 0, 0, 0, 4],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 2, 0, 4, 0, 0, 0]]
    top = [2, 2, 2, 0, 4, 4, 4, 4]
    expected = {
        "outline": [top[:], [2, 0, 2, 0, 4, 0, 0, 4], top[:]],
        "largest": [top[:], [2, 0, 2, 0, 4, 4, 4, 4], top[:]],
        "smallest": [top[:], [2, 2, 2, 0, 4, 0, 0, 4], top[:]],
    }
    return grid, expected


def test_outline_is_byte_exact_canonical_and_preserves_five_official_pairs(family, canonical, racket):
    source = family.program(setting("outline"))
    assert source == canonical["program_solution"]
    assert hashlib.sha256(source.encode()).hexdigest() == CANONICAL_SHA
    official = canonical["train"] + canonical["test"]
    assert len(official) == 5
    for pair in official:
        assert family.apply_claim(pair["input"], setting("outline")) == pair["output"]
        assert racket(source, pair["input"]) == pair["output"]


@pytest.mark.parametrize("policy", POLICIES)
def test_literal_pair_uses_same_color_and_both_diagonal_orientations(family, racket, policy):
    grid, expected = literal_pair_fixture()
    before = copy.deepcopy(grid)
    assert family.apply_claim(grid, setting(policy)) == expected[policy]
    assert racket(family.program(setting(policy)), grid) == expected[policy]
    assert grid == before


def marker_input(height, width, pairs):
    grid = [[0] * width for _ in range(height)]
    for color, coordinates in pairs:
        for row, col in coordinates:
            grid[row][col] = color
    return grid


def literal_patches(height, width, patches):
    """Place already literal expected patches; no bbox, ranking, or drawing logic."""
    grid = [[0] * width for _ in range(height)]
    for top, left, patch in patches:
        for row, values in enumerate(patch):
            for col, value in enumerate(values):
                grid[top + row][left + col] = value
    return grid


def tie_fixture():
    grid = marker_input(8, 8, [
        (2, [(0, 0), (2, 3)]), (7, [(0, 7), (3, 5)]),
        (4, [(5, 0), (7, 2)]), (9, [(5, 7), (7, 5)]),
    ])
    a = [[2, 2, 2, 2], [2, 0, 0, 2], [2, 2, 2, 2]]
    af = [[2, 2, 2, 2], [2, 2, 2, 2], [2, 2, 2, 2]]
    b = [[7, 7, 7], [7, 0, 7], [7, 0, 7], [7, 7, 7]]
    bf = [[7, 7, 7], [7, 7, 7], [7, 7, 7], [7, 7, 7]]
    c = [[4, 4, 4], [4, 0, 4], [4, 4, 4]]
    cf = [[4, 4, 4], [4, 4, 4], [4, 4, 4]]
    d = [[9, 9, 9], [9, 0, 9], [9, 9, 9]]
    df = [[9, 9, 9], [9, 9, 9], [9, 9, 9]]
    expected = {
        "outline": literal_patches(8, 8, [(0, 0, a), (0, 5, b), (5, 0, c), (5, 5, d)]),
        "largest": literal_patches(8, 8, [(0, 0, af), (0, 5, bf), (5, 0, c), (5, 5, d)]),
        "smallest": literal_patches(8, 8, [(0, 0, a), (0, 5, b), (5, 0, cf), (5, 5, df)]),
    }
    return grid, expected


def metric_fixture(kind):
    if kind == "perimeter":
        # 3x9 has smaller area27 but larger perimeter24 than 5x6 (30,22).
        grid = marker_input(5, 16, [(8, [(0, 0), (2, 8)]), (3, [(0, 15), (4, 10)])])
        a = [[8] * 9, [8, 0, 0, 0, 0, 0, 0, 0, 8], [8] * 9]
        af = [[8] * 9 for _ in range(3)]
        b = [[3] * 6, [3, 0, 0, 0, 0, 3], [3, 0, 0, 0, 0, 3],
             [3, 0, 0, 0, 0, 3], [3] * 6]
        bf = [[3] * 6 for _ in range(5)]
        return grid, {
            "outline": literal_patches(5, 16, [(0, 0, a), (0, 10, b)]),
            "largest": literal_patches(5, 16, [(0, 0, a), (0, 10, bf)]),
            "smallest": literal_patches(5, 16, [(0, 0, af), (0, 10, b)]),
        }
    # Inclusive areas39>36, whereas endpoint-difference products24<25.
    grid = marker_input(6, 20, [(1, [(0, 12), (2, 0)]), (8, [(0, 14), (5, 19)])])
    a = [[1] * 13, [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1], [1] * 13]
    af = [[1] * 13 for _ in range(3)]
    b = [[8] * 6, [8, 0, 0, 0, 0, 8], [8, 0, 0, 0, 0, 8],
         [8, 0, 0, 0, 0, 8], [8, 0, 0, 0, 0, 8], [8] * 6]
    bf = [[8] * 6 for _ in range(6)]
    return grid, {
        "outline": literal_patches(6, 20, [(0, 0, a), (0, 14, b)]),
        "largest": literal_patches(6, 20, [(0, 0, af), (0, 14, b)]),
        "smallest": literal_patches(6, 20, [(0, 0, a), (0, 14, bf)]),
    }


def input_boxes(grid):
    """Independent input metrics, used only for generated teaching assertions."""
    result = []
    for color in range(1, 10):
        cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
        if len(cells) != 2:
            continue
        top, bottom = sorted([cells[0][0], cells[1][0]])
        left, right = sorted([cells[0][1], cells[1][1]])
        height, width = bottom - top + 1, right - left + 1
        result.append({"color": color, "bbox": [top, left, bottom, right],
                       "height": height, "width": width, "area": height * width,
                       "perimeter": 2 * (height + width)})
    return result


def episode_inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def assert_grid(grid):
    assert type(grid) is list and 1 <= len(grid) <= 30
    assert type(grid[0]) is list and 1 <= len(grid[0]) <= 30
    width = len(grid[0])
    assert all(type(row) is list and len(row) == width
               and all(type(cell) is int and 0 <= cell <= 9 for cell in row) for row in grid)


@pytest.mark.parametrize("policy", POLICIES)
def test_all_extreme_ties_are_filled_and_nonextreme_boxes_stay_outlined(family, racket, policy):
    grid, expected = tie_fixture()
    assert family.apply_claim(grid, setting(policy)) == expected[policy]
    assert racket(family.program(setting(policy)), grid) == expected[policy]
    description = family.describe(grid, setting(policy))
    assert {box["color"]: box["area"] for box in description["boxes"]} == {2: 12, 7: 12, 4: 9, 9: 9}
    assert description["selected_colors"] == {"outline": [], "largest": [2, 7], "smallest": [4, 9]}[policy]


@pytest.mark.parametrize("kind", ["perimeter", "exclusive_spans"])
@pytest.mark.parametrize("policy", POLICIES)
def test_ranking_uses_inclusive_area_instead_of_perimeter_or_endpoint_spans(family, racket, kind, policy):
    grid, expected = metric_fixture(kind)
    assert family.apply_claim(grid, setting(policy)) == expected[policy]
    assert racket(family.program(setting(policy)), grid) == expected[policy]


@pytest.mark.parametrize("policy", POLICIES)
def test_nested_paint_uses_input_boxes_and_later_outline_does_not_clear_interior(family, racket, policy):
    grid = [[2, 0, 0, 0, 0], [0, 7, 0, 0, 0], [0, 0, 0, 0, 0],
            [0, 0, 0, 7, 0], [0, 0, 0, 0, 2]]
    expected = [[2, 2, 2, 2, 2], [2, 7, 7, 7, 2], [2, 7, 0, 7, 2],
                [2, 7, 7, 7, 2], [2, 2, 2, 2, 2]]
    expected[2][2] = {"outline": 0, "largest": 2, "smallest": 7}[policy]
    assert family.apply_claim(grid, setting(policy)) == expected
    assert racket(family.program(setting(policy)), grid) == expected
    assert {box["color"]: box["area"] for box in family.describe(grid, setting(policy))["boxes"]} == {2: 25, 7: 9}


@pytest.mark.parametrize("policy", POLICIES)
def test_higher_color_wins_coincident_boxes_even_when_scanned_first(family, racket, policy):
    grid = [[7, 0, 2], [0, 0, 0], [2, 0, 7]]
    expected = [[7, 7, 7], [7, 0 if policy == "outline" else 7, 7], [7, 7, 7]]
    assert family.apply_claim(grid, setting(policy)) == expected
    assert racket(family.program(setting(policy)), grid) == expected


@pytest.mark.parametrize("policy", POLICIES)
def test_colors_without_exactly_two_occurrences_are_erased_and_excluded_from_ranking(family, racket, policy):
    grid, expected = literal_pair_fixture()
    grid[1] = [0, 9, 0, 3, 3, 3, 0, 0]
    assert family.apply_claim(grid, setting(policy)) == expected[policy]
    assert racket(family.program(setting(policy)), grid) == expected[policy]
    assert {box["color"] for box in family.describe(grid, setting(policy))["boxes"]} == {2, 4}


@pytest.mark.parametrize("policy", POLICIES)
def test_blank_ignored_only_lines_and_two_by_two_are_supported(family, racket, policy):
    cases = [([[0]], [[0]]), ([[7]], [[0]]), ([[5, 5, 5]], [[0, 0, 0]]),
             ([[2, 2], [2, 2]], [[0, 0], [0, 0]]),
             ([[5, 0, 5]], [[5, 5, 5]]), ([[4], [0], [4]], [[4], [4], [4]]),
             ([[2, 0], [0, 2]], [[2, 2], [2, 2]])]
    for grid, expected in cases:
        assert family.apply_claim(grid, setting(policy)) == expected
        assert racket(family.program(setting(policy)), grid) == expected


def test_describe_reports_input_geometry_and_apply_returns_fresh_rows(family):
    grid, expected = literal_pair_fixture()
    description = family.describe(grid, setting("largest"))
    assert description["input_shape"] == description["output_shape"] == [3, 8]
    by_color = {box["color"]: box for box in description["boxes"]}
    assert [by_color[2][key] for key in ("bbox", "height", "width", "area", "perimeter")] == [[0, 0, 2, 2], 3, 3, 9, 12]
    assert [by_color[4][key] for key in ("bbox", "height", "width", "area", "perimeter")] == [[0, 4, 2, 7], 3, 4, 12, 14]
    original = copy.deepcopy(grid)
    result = family.apply_claim(grid, setting("largest"))
    result[0][0] = 9
    assert grid == original
    assert family.apply_claim(grid, setting("largest")) == expected["largest"]


def test_settings_grid_seed_and_count_validation_is_strict(family):
    for bad in (None, "outline", {}, {"fill_policy": True}, {"fill_policy": "unknown"},
                {"fill_policy": ["outline"]}, {"fill_policy": "outline", "extra": 0}):
        with pytest.raises((TypeError, ValueError)):
            family.program(bad)
        with pytest.raises((TypeError, ValueError)):
            family.apply_claim([[0]], bad)
        with pytest.raises((TypeError, ValueError)):
            family.generate(0, bad, 3, 1)
    for bad in (None, [], [[]], ((0,),), [(0, 1)], [[0], [0, 1]], [[True]],
                [[1.0]], [["1"]], [[-1]], [[10]], [[0] * 31], [[0] for _ in range(31)]):
        with pytest.raises((TypeError, ValueError)):
            family.apply_claim(bad, setting("outline"))
        with pytest.raises((TypeError, ValueError)):
            family.describe(bad, setting("outline"))
    for bad in (-1, 2**63, True, 0.0, "0"):
        with pytest.raises((TypeError, ValueError)):
            family.generate(bad, setting("outline"), 3, 1)
    for demos, queries in ((2, 1), (7, 1), (3, 0), (3, 5), (True, 1), (3, True), (3.0, 1), (3, 1.0)):
        with pytest.raises((TypeError, ValueError)):
            family.generate(0, setting("outline"), demos, queries)


def test_full_banks_are_matched_independent_prefixes_and_do_not_touch_global_rng(family):
    before = random.getstate()
    banks = {policy: family.generate(17, setting(policy), 6, 4) for policy in POLICIES}
    for policy, bank in banks.items():
        assert len(bank["train"]) == 6 and len(bank["test"]) == 4
        assert episode_inputs(bank) == episode_inputs(banks["outline"])
        for demos, queries in ((3, 1), (3, 4), (6, 1), (4, 2), (5, 3)):
            short = family.generate(17, setting(policy), demos, queries)
            assert short["train"] == bank["train"][:demos]
            assert short["test"] == bank["test"][:queries]
        for pair in bank["train"] + bank["test"]:
            assert_grid(pair["input"])
            assert_grid(pair["output"])
    assert random.getstate() == before
    again = family.generate(17, setting("outline"), 6, 4)
    assert again == banks["outline"]
    again["train"][0]["input"][0][0] = (again["train"][0]["input"][0][0] + 1) % 10
    again["test"][0]["output"][0][0] = (again["test"][0]["output"][0][0] + 1) % 10
    assert family.generate(17, setting("outline"), 6, 4) == banks["outline"]
    edge = family.generate(2**63 - 1, setting("largest"), 3, 1)
    assert len(edge["train"]) == 3 and len(edge["test"]) == 1


@pytest.mark.parametrize("seed", [0, 17])
def test_first_three_demonstrations_identify_policies_and_show_both_extreme_ties(family, seed):
    episodes = [family.generate(seed, setting(policy), 3, 1) for policy in POLICIES]
    assert all(episode_inputs(ep) == episode_inputs(episodes[0]) for ep in episodes)
    assert len({json.dumps([pair["output"] for pair in ep["train"]]) for ep in episodes}) == 3
    boxes_by_demo = [input_boxes(pair["input"]) for pair in episodes[0]["train"]]
    assert any(len(boxes) == 1 for boxes in boxes_by_demo)
    for extremum in (min, max):
        assert any(len({box["area"] for box in boxes}) > 1
                   and sum(box["area"] == extremum(b["area"] for b in boxes) for box in boxes) >= 2
                   for boxes in boxes_by_demo)
        assert any({box["color"] for box in boxes if box["area"] == extremum(b["area"] for b in boxes)}
                   != {box["color"] for box in boxes if box["perimeter"] == extremum(b["perimeter"] for b in boxes)}
                   for boxes in boxes_by_demo)


@pytest.mark.parametrize("seed", [0, 17])
@pytest.mark.parametrize("policy", ["largest", "smallest"])
def test_first_three_demos_refute_a_single_monotone_absolute_area_threshold(family, seed, policy):
    episode = family.generate(seed, setting(policy), 3, 1)
    selected, unselected = [], []
    for pair in episode["train"]:
        for box in input_boxes(pair["input"]):
            top, left, bottom, right = box["bbox"]
            assert box["height"] >= 3 and box["width"] >= 3
            filled = all(pair["output"][r][c] == box["color"]
                         for r in range(top + 1, bottom) for c in range(left + 1, right))
            (selected if filled else unselected).append(box["area"])
    assert selected and unselected
    if policy == "largest":
        assert min(selected) <= max(unselected), "a fixed area lower bound still fits all three demonstrations"
    else:
        assert max(selected) >= min(unselected), "a fixed area upper bound still fits all three demonstrations"


@pytest.mark.parametrize("policy", POLICIES)
def test_generated_labels_and_boundary_stress_are_protected_and_substantive(family, racket, policy):
    episode = family.generate(0, setting(policy), 3, 4)
    for pair in episode["train"] + [episode["test"][0], episode["test"][3]]:
        assert racket(family.program(setting(policy)), pair["input"]) == pair["output"]
    stress = episode["test"][3]
    grid, output = stress["input"], stress["output"]
    assert len(grid) == len(grid[0]) == len(output) == len(output[0]) == 30
    occupied = sum(cell != 0 for row in grid for cell in row)
    assert 2 <= occupied <= 18 and occupied == 2 * len(input_boxes(grid))
    assert any(grid[0]) and any(grid[-1]) and any(row[0] for row in grid) and any(row[-1] for row in grid)
    assert sum(cell != 0 for row in output for cell in row) >= 100
    assert family.describe(grid, setting(policy))["output_shape"] == [30, 30]


@pytest.mark.parametrize("policy", POLICIES)
def test_extra_rivals_are_complete_executable_programs(family, racket, policy):
    rivals = family.rivals(setting(policy))
    assert type(rivals) is dict and rivals
    grid = family.generate(0, setting(policy), 3, 1)["train"][0]["input"]
    for name, program in rivals.items():
        assert type(name) is str and name and type(program) is str and program
        assert_grid(racket(program, grid))


def test_adapter_exposes_literal_semantics_and_public_current_query_without_secrets(adapter, family, canonical):
    grid, expected = literal_pair_fixture()
    assert adapter.program(setting("outline")) == canonical["program_solution"]
    for policy in POLICIES:
        assert adapter.apply_claim(grid, setting(policy)) == expected[policy]
    episode = adapter.generate(0, setting("largest"), 3, 4)
    assert episode == family.generate(0, setting("largest"), 3, 4)
    public = adapter.public_turn(episode, 0)
    wanted = {"train": episode["train"], "test": [{"input": episode["test"][0]["input"]}]}
    assert public == wanted
    altered = copy.deepcopy(episode)
    altered["seed"] = "SECRET-SEED"
    altered["_private"] = {"secret": "PRIVATE-METADATA"}
    altered["settings"] = {"secret": "PRIVATE-SETTINGS"}
    altered["test"][0]["output"] = [[9]]
    altered["test"][1:] = [{"input": [[8]], "output": [[7]]} for _ in range(3)]
    assert adapter.public_turn(altered, 0) == public
    assert adapter.public_turn(adapter.generate(0, setting("largest"), 3, 1), 0) == public
    snapshot = copy.deepcopy(episode)
    public["train"][0]["input"][0][0] = (public["train"][0]["input"][0][0] + 1) % 10
    public["test"][0]["input"][0][0] = (public["test"][0]["input"][0][0] + 1) % 10
    assert episode == snapshot
    for index in (1, 2, 3):
        assert adapter.public_turn(episode, index) == {
            "train": episode["train"], "test": [{"input": episode["test"][index]["input"]}]}
    for bad in (-1, 4, True, 0.0, "0"):
        with pytest.raises((TypeError, ValueError, IndexError)):
            adapter.public_turn(episode, bad)


@pytest.mark.parametrize("policy", POLICIES)
def test_all_eight_d4_transforms_commute_with_literal_area_selection(family, racket, policy):
    # The authored 3x8 fixture is nonsquare and has unequal-area rectangles.
    # Transform its literal answer, never an answer produced by the family.
    grid, expected = literal_pair_fixture()
    program = family.program(setting(policy))

    def clockwise(value):
        return [list(row) for row in zip(*value[::-1])]

    for reflected in (False, True):
        transformed_input = [row[::-1] if reflected else row[:] for row in grid]
        transformed_output = [row[::-1] if reflected else row[:] for row in expected[policy]]
        for quarter_turns in range(4):
            assert racket(program, transformed_input) == transformed_output, (policy, reflected, quarter_turns)
            transformed_input = clockwise(transformed_input)
            transformed_output = clockwise(transformed_output)


@pytest.mark.parametrize("seed", [0, 17])
@pytest.mark.parametrize("policy", ["largest", "smallest"])
def test_demo_only_intermediate_areas_refute_complement_mean_and_median_shortcuts(family, seed, policy):
    demonstrations = family.generate(seed, setting(policy), 3, 1)["train"]
    refuted = {"fill_all_except_opposite_extreme": False,
               "split_at_mean": False, "split_at_median": False}
    two_intermediate_levels = False
    for pair in demonstrations:
        boxes = input_boxes(pair["input"])
        ordered = sorted(box["area"] for box in boxes)
        low, high = ordered[0], ordered[-1]
        two_intermediate_levels |= len({area for area in ordered if low < area < high}) >= 2
        observed = set()
        for box in boxes:
            top, left, bottom, right = box["bbox"]
            assert box["height"] >= 3 and box["width"] >= 3
            if all(pair["output"][r][c] == box["color"]
                   for r in range(top + 1, bottom) for c in range(left + 1, right)):
                observed.add(box["color"])
        count, total = len(ordered), sum(ordered)
        twice_median = ordered[(count - 1) // 2] + ordered[count // 2]
        if policy == "largest":
            candidates = {
                "fill_all_except_opposite_extreme": {box["color"] for box in boxes if low == high or box["area"] > low},
                "split_at_mean": {box["color"] for box in boxes if box["area"] * count >= total},
                "split_at_median": {box["color"] for box in boxes if 2 * box["area"] >= twice_median},
            }
        else:
            candidates = {
                "fill_all_except_opposite_extreme": {box["color"] for box in boxes if low == high or box["area"] < high},
                "split_at_mean": {box["color"] for box in boxes if box["area"] * count <= total},
                "split_at_median": {box["color"] for box in boxes if 2 * box["area"] <= twice_median},
            }
        for name, colors in candidates.items():
            refuted[name] |= colors != observed
    assert two_intermediate_levels, "visible demonstrations need two distinct intermediate area levels"
    assert all(refuted.values()), refuted
