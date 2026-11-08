"""Independent tests for section-count selection followed by cyclic overlay."""
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
PARAMETRIC = ROOT / "generators/9000d0ea6484/workspace/parametric"
RUNTIME = ROOT / "shared/runtime"
STARTS = (0, 1, 2, 3, "densest", "sparsest")
DIRECTIONS = ("forward", "reverse")
CANONICAL_SHA = "3bec9ede53940dce7bdf0aa83666b99ea3fb754cb6c4d356406e7eab30dade8c"


def setting(start=2, direction="forward"):
    return {"start_section": start, "scan_direction": direction}


@lru_cache(None)
def load_adjacent(filename):
    path = PARAMETRIC / filename
    assert path.is_file(), f"Native feature is missing: {path}"
    name = "_native_test_9000d0ea6484_" + path.stem
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
            if (row := json.loads(line))["task_id"] == "9000d0ea6484"]
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


def test_default_is_byte_exact_canonical_and_preserves_seven_official_pairs(family, canonical, racket):
    source = family.program(setting())
    assert source == canonical["program_solution"]
    assert hashlib.sha256(source.encode()).hexdigest() == CANONICAL_SHA
    official = canonical["train"] + canonical["test"]
    assert len(official) == 7
    for pair in official:
        assert family.apply_claim(pair["input"], setting()) == pair["output"]
        assert racket(source, pair["input"]) == pair["output"]


def panel_input(*panels):
    """Join authored panels; this helper performs no selection or overlay."""
    assert len(panels) == 4 and len({len(panel) for panel in panels}) == 1
    return [panels[0][r][:] + [3] + panels[1][r][:] + [3]
            + panels[2][r][:] + [3] + panels[3][r][:]
            for r in range(len(panels[0]))]


def balanced_fixture():
    # Empty, four solos, six pairs, all four: each panel has exactly five cells.
    grid = panel_input(
        [[0, 1, 0, 0], [0, 1, 1, 1], [0, 0, 0, 1]],
        [[0, 0, 6, 0], [0, 6, 0, 0], [6, 6, 0, 6]],
        [[0, 0, 0, 2], [0, 0, 2, 0], [2, 0, 2, 2]],
        [[0, 0, 0, 0], [8, 0, 0, 8], [0, 8, 8, 8]],
    )
    expected = {
        (0, "forward"): [[0, 1, 6, 2], [8, 1, 1, 1], [6, 6, 2, 1]],
        (0, "reverse"): [[0, 1, 6, 2], [8, 1, 1, 1], [2, 8, 8, 1]],
        (1, "forward"): [[0, 1, 6, 2], [8, 6, 2, 8], [6, 6, 2, 6]],
        (1, "reverse"): [[0, 1, 6, 2], [8, 6, 1, 1], [6, 6, 8, 6]],
        (2, "forward"): [[0, 1, 6, 2], [8, 1, 2, 8], [2, 8, 2, 2]],
        (2, "reverse"): [[0, 1, 6, 2], [8, 6, 2, 1], [2, 6, 2, 2]],
        (3, "forward"): [[0, 1, 6, 2], [8, 1, 1, 8], [6, 8, 8, 8]],
        (3, "reverse"): [[0, 1, 6, 2], [8, 6, 2, 8], [2, 8, 8, 8]],
    }
    return grid, expected


def unequal_fixture():
    # Four, two, three, one occupied cells; weighted color sums rank differently.
    return panel_input(
        [[1, 0, 0, 0], [1, 1, 1, 0]],
        [[6, 6, 0, 0], [0, 0, 0, 0]],
        [[2, 2, 2, 0], [0, 0, 0, 0]],
        [[8, 0, 0, 0], [0, 0, 0, 0]],
    ), {
        ("densest", "forward"): [[1, 6, 2, 0], [1, 1, 1, 0]],
        ("densest", "reverse"): [[1, 2, 2, 0], [1, 1, 1, 0]],
        ("sparsest", "forward"): [[8, 6, 2, 0], [1, 1, 1, 0]],
        ("sparsest", "reverse"): [[8, 2, 2, 0], [1, 1, 1, 0]],
    }


def blank_grid(height=1):
    return panel_input(*([([0] * 4) for _ in range(height)] for _ in range(4)))


def episode_inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def assert_input_grid(grid, *, generated=False):
    assert type(grid) is list and (3 if generated else 1) <= len(grid) <= 30
    assert all(type(row) is list and len(row) == 19 for row in grid)
    for row in grid:
        assert all(type(cell) is int and 0 <= cell <= 9 for cell in row)
        assert [row[c] for c in (4, 9, 14)] == [3, 3, 3]
        assert all(value != 3 for c, value in enumerate(row) if c not in (4, 9, 14))


def assert_output_grid(grid, height):
    assert type(grid) is list and len(grid) == height
    assert all(type(row) is list and len(row) == 4
               and all(type(value) is int and 0 <= value <= 9 for value in row)
               for row in grid)


def test_settings_domain_and_all_eight_fixed_sources_preserve_the_prototype(family):
    assert type(family.SETTINGS) is tuple and len(family.SETTINGS) == 12
    assert family.DEFAULT == setting()
    assert all(type(item) is dict and set(item) == {"start_section", "scan_direction"}
               for item in family.SETTINGS)
    actual = {(item["start_section"], item["scan_direction"]) for item in family.SETTINGS}
    assert actual == {(start, direction) for start in STARTS for direction in DIRECTIONS}
    prototype = load_adjacent("prototype.py")
    for start in range(4):
        for direction in DIRECTIONS:
            assert family.program(setting(start, direction)) == prototype.materialize_rule(
                start, direction, root=ROOT)
    assert len({family.program(item) for item in family.SETTINGS}) == 12


@pytest.mark.parametrize("start", STARTS)
@pytest.mark.parametrize("direction", DIRECTIONS)
def test_literal_pairwise_priorities_and_balanced_tie_to_section_two(family, racket, start, direction):
    grid, outputs = balanced_fixture()
    chosen = start if type(start) is int else 2
    expected = outputs[(chosen, direction)]
    before = copy.deepcopy(grid)
    selected = setting(start, direction)
    assert family.apply_claim(grid, selected) == expected
    assert racket(family.program(selected), grid) == expected
    details = family.describe(grid, selected)
    assert list(details["counts"]) == [5, 5, 5, 5]
    assert details["selected_start"] == chosen
    assert grid == before


@pytest.mark.parametrize("start", ["densest", "sparsest"])
@pytest.mark.parametrize("direction", DIRECTIONS)
def test_unique_extreme_counts_then_partial_priority_fallback(family, racket, start, direction):
    grid, expected = unequal_fixture()
    selected = setting(start, direction)
    assert family.apply_claim(grid, selected) == expected[(start, direction)]
    assert racket(family.program(selected), grid) == expected[(start, direction)]
    details = family.describe(grid, selected)
    assert list(details["counts"]) == [4, 2, 3, 1]
    assert details["input_shape"] == [2, 19] and details["output_shape"] == [2, 4]
    chosen = 0 if start == "densest" else 3
    orders = {(0, "forward"): [0, 1, 2, 3], (0, "reverse"): [0, 3, 2, 1],
              (3, "forward"): [3, 0, 1, 2], (3, "reverse"): [3, 2, 1, 0]}
    assert details["selected_start"] == chosen
    assert list(details["priority_order"]) == orders[(chosen, direction)]


@pytest.mark.parametrize("start,counts,chosen,forward,reverse", [
    ("densest", [3, 1, 2, 3], 3, [8, 8, 8, 0], [8, 8, 8, 0]),
    ("sparsest", [1, 3, 2, 1], 3, [8, 6, 6, 0], [8, 2, 6, 0]),
    ("densest", [3, 3, 1, 2], 0, [1, 1, 1, 0], [1, 1, 1, 0]),
    ("sparsest", [1, 1, 3, 2], 0, [1, 2, 2, 0], [1, 8, 2, 0]),
])
def test_tie_order_keeps_three_before_zero_before_one_in_both_directions(
        family, racket, start, counts, chosen, forward, reverse):
    grid = panel_input(*([[color] * count + [0] * (4 - count)]
                         for color, count in zip((1, 6, 2, 8), counts)))
    for direction, expected in (("forward", forward), ("reverse", reverse)):
        selected = setting(start, direction)
        assert family.apply_claim(grid, selected) == [expected]
        assert racket(family.program(selected), grid) == [expected]
        details = family.describe(grid, selected)
        assert list(details["counts"]) == counts
        assert details["selected_start"] == chosen


@pytest.mark.parametrize("start", ["densest", "sparsest"])
@pytest.mark.parametrize("direction", DIRECTIONS)
def test_empty_section_is_a_valid_minimum_and_payload_colors_are_not_section_ids(
        family, racket, start, direction):
    grid = panel_input([[1, 4, 5, 6]], [[8, 0, 0, 7]], [[0, 2, 9, 0]], [[0, 0, 0, 0]])
    expected = [[8, 2, 9, 7]] if (start, direction) == ("sparsest", "reverse") else [[1, 4, 5, 6]]
    selected = setting(start, direction)
    assert family.apply_claim(grid, selected) == expected
    assert racket(family.program(selected), grid) == expected
    details = family.describe(grid, selected)
    assert list(details["counts"]) == [4, 2, 2, 0]
    assert details["selected_start"] == (0 if start == "densest" else 3)


def test_blank_payload_and_height_boundaries_are_lawful_and_outputs_are_fresh(family, racket):
    grid = blank_grid()
    for start in STARTS:
        for direction in DIRECTIONS:
            selected = setting(start, direction)
            assert family.apply_claim(grid, selected) == [[0, 0, 0, 0]]
            assert racket(family.program(selected), grid) == [[0, 0, 0, 0]]
            details = family.describe(grid, selected)
            assert list(details["counts"]) == [0, 0, 0, 0]
            assert details["selected_start"] == (start if type(start) is int else 2)
    tall = blank_grid(30)
    tall[0][0] = 7
    tall[-1][18] = 9
    expected = [[7, 0, 0, 0]] + [[0, 0, 0, 0] for _ in range(28)] + [[0, 0, 0, 9]]
    for selected in (setting(), setting("sparsest", "reverse")):
        actual = family.apply_claim(tall, selected)
        assert actual == expected
        assert racket(family.program(selected), tall) == expected
        actual[0][0] = 1
        actual[-1][3] = 1
        assert family.apply_claim(tall, selected) == expected
        assert tall[0][0] == 7 and tall[-1][18] == 9


@pytest.mark.parametrize("start", ["densest", "sparsest"])
@pytest.mark.parametrize("direction", DIRECTIONS)
def test_remote_occupancy_changes_local_overlap_without_changing_its_candidates(
        family, racket, start, direction):
    grid, baseline = unequal_fixture()
    changed = copy.deepcopy(grid)
    if start == "densest":
        changed[1][12:14] = [9, 4]
        expected = [[2, 2, 2, 0], [1, 1, 9, 4]]
        chosen, counts = 2, [4, 2, 5, 1]
    else:
        changed[1][17:19] = [5, 7]
        expected = [[6, 6, 2, 0], [1, 1, 5, 7] if direction == "forward" else [1, 1, 1, 7]]
        chosen, counts = 1, [4, 2, 3, 3]
    selected = setting(start, direction)
    assert grid[0] == changed[0]
    assert family.apply_claim(grid, selected) == baseline[(start, direction)]
    assert family.apply_claim(changed, selected) == expected
    assert racket(family.program(selected), grid) == baseline[(start, direction)]
    assert racket(family.program(selected), changed) == expected
    assert baseline[(start, direction)][0][0] != expected[0][0]
    details = family.describe(changed, selected)
    assert details["selected_start"] == chosen and list(details["counts"]) == counts


@pytest.mark.parametrize("bad", [
    {}, {"start_section": 2}, {"scan_direction": "forward"},
    {"start_section": 2, "scan_direction": "forward", "extra": 0},
    setting(True), setting(2.0), setting(-1), setting(4), setting("2"), setting("largest"),
    setting(2, True), setting(2, "backward"), [], "default",
])
def test_settings_reject_missing_extra_or_coercible_values(family, bad):
    with pytest.raises((TypeError, ValueError)):
        family.program(bad)
    with pytest.raises((TypeError, ValueError)):
        family.apply_claim(blank_grid(), bad)
    with pytest.raises((TypeError, ValueError)):
        family.generate(0, settings=bad, demos=4, queries=1)


def invalid_grids():
    cases = [("none", None), ("empty", []), ("empty-row", [[]]),
             ("narrow", [[0] * 18]), ("wide", [[0] * 20]),
             ("outer-tuple", tuple(blank_grid())), ("row-tuple", [tuple(blank_grid()[0])]),
             ("too-tall", blank_grid(31)), ("ragged", blank_grid() + [[0] * 18])]
    for name, value in (("boolean", True), ("float", 1.0), ("string", "1"),
                        ("negative", -1), ("large-color", 10), ("payload-divider", 3)):
        grid = blank_grid()
        grid[0][0] = value
        cases.append((name, grid))
    grid = blank_grid(2)
    grid[1][9] = 0
    cases.append(("incomplete-divider", grid))
    return cases


def test_grid_validation_is_strict_and_preserves_the_input(family):
    for name, grid in invalid_grids():
        before = copy.deepcopy(grid)
        for operation in (family.apply_claim, family.describe):
            with pytest.raises((TypeError, ValueError), match="."):
                operation(grid, setting())
        assert grid == before, name


def test_seed_and_independent_request_counts_reject_coercion_and_bounds(family):
    for bad in (True, False, -1, 2**63, 0.0, "0", None):
        with pytest.raises((TypeError, ValueError)):
            family.generate(bad, setting(), 4, 1)
    for demos in (3, 7, True, 4.0, "4"):
        with pytest.raises((TypeError, ValueError)):
            family.generate(0, setting(), demos, 1)
    for queries in (0, 5, False, 1.0, "1"):
        with pytest.raises((TypeError, ValueError)):
            family.generate(0, setting(), 4, queries)


def test_matched_banks_independent_prefixes_determinism_maxseed_and_freshness(family):
    before = random.getstate()
    banks = {}
    for start in STARTS:
        for direction in DIRECTIONS:
            selected = setting(start, direction)
            bank = family.generate(17, selected, 6, 4)
            banks[(start, direction)] = bank
            assert len(bank["train"]) == 6 and len(bank["test"]) == 4
            assert bank["program_solution"] == family.program(selected)
            assert len({json.dumps(grid) for grid in episode_inputs(bank)}) == 10
            for pair in bank["train"] + bank["test"]:
                assert_input_grid(pair["input"], generated=True)
                assert_output_grid(pair["output"], len(pair["input"]))
            short = family.generate(17, selected, 4, 1)
            assert short["train"] == bank["train"][:4]
            assert short["test"] == bank["test"][:1]
    reference = episode_inputs(banks[(2, "forward")])
    assert all(episode_inputs(bank) == reference for bank in banks.values())
    # Exercise the two independent axes and interior values without a count battery.
    for demos, queries in ((4, 4), (6, 1), (5, 2), (5, 3)):
        short = family.generate(17, setting("densest", "reverse"), demos, queries)
        bank = banks[("densest", "reverse")]
        assert short["train"] == bank["train"][:demos]
        assert short["test"] == bank["test"][:queries]
    implicit = family.generate(17, None, 6, 4)
    assert implicit["program_solution"] in {family.program(item) for item in family.SETTINGS}
    assert episode_inputs(implicit) == reference
    assert family.generate(17, None, 6, 4) == implicit
    default_request = family.generate(17, setting())
    assert default_request["train"] == banks[(2, "forward")]["train"][:4]
    assert default_request["test"] == banks[(2, "forward")]["test"]
    again = family.generate(17, setting(), 6, 4)
    assert again == banks[(2, "forward")]
    again["train"][0]["input"][0][0] = (again["train"][0]["input"][0][0] + 1) % 10
    again["test"][0]["output"][0][0] = (again["test"][0]["output"][0][0] + 1) % 10
    assert family.generate(17, setting(), 6, 4) == banks[(2, "forward")]
    edge = family.generate(2**63 - 1, setting("sparsest", "reverse"), 4, 1)
    assert len(edge["train"]) == 4 and len(edge["test"]) == 1
    assert random.getstate() == before


@pytest.mark.parametrize("seed", [0, 17])
def test_first_four_demonstrations_distinguish_all_twelve_settings(family, seed):
    episodes = [family.generate(seed, setting(start, direction), 4, 1)
                for start in STARTS for direction in DIRECTIONS]
    assert all(episode_inputs(episode) == episode_inputs(episodes[0]) for episode in episodes)
    labels = {json.dumps([pair["output"] for pair in episode["train"]]) for episode in episodes}
    assert len(labels) == 12


@pytest.mark.parametrize("seed", [0, 17])
@pytest.mark.parametrize("start", ["densest", "sparsest"])
def test_first_four_demonstrations_use_every_density_anchor(family, seed, start):
    # Count the visible input cells independently. Four observed anchor roles
    # prevent a density rule from silently omitting a never-selected section.
    for direction in DIRECTIONS:
        selected = setting(start, direction)
        demonstrations = family.generate(seed, selected, 4, 1)["train"]
        anchors = set()
        for pair in demonstrations:
            counts = [sum(value != 0 for row in pair["input"] for value in row[offset:offset + 4])
                      for offset in (0, 5, 10, 15)]
            target = (max if start == "densest" else min)(counts)
            anchor = next(index for index in (2, 3, 0, 1) if counts[index] == target)
            details = family.describe(pair["input"], selected)
            assert list(details["counts"]) == counts
            assert details["selected_start"] == anchor
            anchors.add(anchor)
        assert anchors == {0, 1, 2, 3}, (seed, selected, anchors)


@pytest.mark.parametrize("start,direction", [(2, "forward"), ("densest", "forward"),
                                           ("densest", "reverse"), ("sparsest", "forward"),
                                           ("sparsest", "reverse")])
def test_generated_labels_and_maximum_height_are_protected(family, racket, start, direction):
    selected = setting(start, direction)
    episode = family.generate(0, selected, 4, 4)
    for pair in episode["train"] + [episode["test"][0], episode["test"][3]]:
        assert racket(family.program(selected), pair["input"]) == pair["output"]
    stress = episode["test"][3]
    assert len(stress["input"]) == len(stress["output"]) == 30
    assert_input_grid(stress["input"], generated=True)
    assert_output_grid(stress["output"], 30)
    grid, output = stress["input"], stress["output"]
    assert sum(value not in (0, 3) for row in grid for value in row) >= 300
    assert all(any(value not in (0, 3) for value in row) for row in grid)
    assert any(value not in (0, 3) for value in grid[0])
    assert any(value not in (0, 3) for value in grid[-1])
    assert any(row[0] for row in grid) and any(row[-1] for row in grid)
    assert sum(value != 0 for row in output for value in row) >= 95
    assert all(any(row) for row in output)


def test_adapter_projection_hides_private_state_future_queries_and_answers(adapter, family, canonical):
    grid, expected = balanced_fixture()
    assert adapter.program(setting()) == canonical["program_solution"]
    assert adapter.apply_claim(grid, setting()) == expected[(2, "forward")]
    episode = adapter.generate(0, setting("sparsest", "reverse"), 4, 4)
    assert episode == family.generate(0, setting("sparsest", "reverse"), 4, 4)
    public = adapter.public_turn(episode)
    assert public == {"train": episode["train"], "test": [{"input": episode["test"][0]["input"]}]}
    altered = copy.deepcopy(episode)
    altered["seed"] = "SECRET-SEED"
    altered["settings"] = {"hidden": "PRIVATE-SETTING"}
    altered["program_solution"] = "PRIVATE-RULE"
    altered["_private"] = {"hidden": "PRIVATE-METADATA"}
    altered["private_metadata"] = {"hidden": "PRIVATE-METADATA"}
    altered["test"][0]["output"] = [[9]]
    altered["test"][1:] = [{"input": [[8]], "output": [[7]]} for _ in range(3)]
    assert adapter.public_turn(altered, 0) == public
    assert adapter.public_turn(adapter.generate(0, setting("sparsest", "reverse"), 4, 1), 0) == public
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
