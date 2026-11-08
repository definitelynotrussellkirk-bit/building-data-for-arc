"""Focused contracts for the separate hole-area parametric prototype."""
from __future__ import annotations

import importlib.util
import copy
from functools import lru_cache
import json
from pathlib import Path
import random
import sys

import pytest


TASK = "56f043832ecb"
HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
PROTOTYPE = HOME / "workspace" / "parametric"
DEFAULT = {"selection": "all"}
SETTINGS = tuple({"selection": value} for value in ("all", "largest", "smallest"))


@lru_cache(maxsize=None)
def _load(name):
    path = PROTOTYPE / f"{name}.py"
    assert path.is_file(), f"Required native prototype source is missing: {path}"
    spec = importlib.util.spec_from_file_location(f"_test_{TASK}_{name}", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def native():
    return _load("native_family")


@pytest.fixture(scope="module")
def adapter():
    return _load("adapter")


def _frame(grid, row, col, height, width, color):
    """Draw a literal test rectangle; expectations never inspect the implementation."""
    for r in range(row, row + height):
        for c in range(col, col + width):
            if r in (row, row + height - 1) or c in (col, col + width - 1):
                grid[r][c] = color


def _filled(grid, rectangles):
    result = copy.deepcopy(grid)
    for row, col, height, width, color in rectangles:
        for r in range(row + 1, row + height - 1):
            for c in range(col + 1, col + width - 1):
                result[r][c] = color
    return result


def test_adapter_preserves_exact_selected_canonical_program():
    adapter = _load("adapter")
    from arcpuzzles import Catalog

    record = Catalog(REPO).get(TASK)
    programs = {row["program_solution"] for row in record["variants"]}
    assert programs == {adapter.program(DEFAULT)}


@pytest.mark.parametrize("variant", ("all", "largest", "smallest", "composed_all"))
def test_programs_are_complete_single_rules_accepted_by_native_wrap_path(native, variant):
    from arc_repl.parser import Symbol, parse_all
    from puzzle_generators.rule_wrap import wrap_rule

    program = (native.build_program("all") if variant == "composed_all"
               else native.program({"selection": variant}))
    forms = parse_all(program)
    assert len(forms) == 1
    assert forms[0][0] == Symbol("rule!")
    wrapped = parse_all(wrap_rule(program))
    assert len(wrapped) == 1
    assert wrapped[0][0] == Symbol("lambda")


@pytest.mark.parametrize("selection", ("all", "largest", "smallest"))
def test_mirror_fills_every_tied_positive_component_and_ignores_solid_objects(native, selection):
    grid = [[0] * 22 for _ in range(10)]
    # These cavities have areas 4, 4 and 6, despite different wall/bbox sizes.
    frames = [(1, 1, 4, 4, 2), (1, 7, 3, 6, 7), (1, 15, 5, 4, 4)]
    for frame in frames:
        _frame(grid, *frame)
    for r in (7, 8):
        for c in (1, 2):
            grid[r][c] = 9
    selected = {"all": frames, "largest": frames[2:], "smallest": frames[:2]}
    assert native.mirror(grid, {"selection": selection}) == _filled(grid, selected[selection])


def test_largest_selection_keeps_all_ties(native):
    grid = [[0] * 25 for _ in range(8)]
    frames = [(1, 1, 4, 5, 2), (1, 9, 3, 8, 3), (1, 20, 3, 4, 4)]
    for frame in frames:
        _frame(grid, *frame)
    # Areas 6, 6, 2: both maximum-area objects must act, without a scan-order tie break.
    assert native.mirror(grid, {"selection": "largest"}) == _filled(grid, frames[:2])


@pytest.mark.parametrize("selection", ("largest", "smallest"))
def test_selection_uses_hole_area_instead_of_bbox_or_wall_size(native, selection):
    grid = [[0] * 22 for _ in range(12)]
    tiny = (1, 1, 3, 3, 2)  # One enclosed cell.
    larger = (6, 15, 4, 4, 7)  # Four enclosed cells.
    _frame(grid, *tiny)
    _frame(grid, *larger)
    # A long connected outward tail gives tiny the larger bbox AND wall count.
    for c in range(4, 14):
        grid[2][c] = 2
    chosen = larger if selection == "largest" else tiny
    assert native.mirror(grid, {"selection": selection}) == _filled(grid, [chosen])


@pytest.mark.parametrize("selection", ("all", "largest", "smallest"))
def test_selection_sums_multiple_holes_of_one_component(native, selection):
    grid = [[0] * 16 for _ in range(7)]
    _frame(grid, 1, 1, 3, 7, 2)
    grid[2][4] = 2  # Two cavities of area 2, sharing a wall: total area 4.
    single = (1, 10, 3, 5, 7)  # One cavity of area 3.
    _frame(grid, *single)
    expected = copy.deepcopy(grid)
    if selection in ("all", "largest"):
        for c in (2, 3, 5, 6):
            expected[2][c] = 2
    if selection in ("all", "smallest"):
        expected[2][11:14] = [7, 7, 7]
    assert native.mirror(grid, {"selection": selection}) == expected


def test_disconnected_components_of_the_same_color_are_ranked_separately(native):
    grid = [[0] * 12 for _ in range(7)]
    small, large = (1, 1, 3, 3, 2), (1, 7, 4, 4, 2)
    _frame(grid, *small)
    _frame(grid, *large)
    assert native.mirror(grid, {"selection": "largest"}) == _filled(grid, [large])
    assert native.mirror(grid, {"selection": "smallest"}) == _filled(grid, [small])


@pytest.mark.parametrize("selection", ("all", "largest", "smallest"))
def test_open_frame_is_not_a_zero_area_minimum(native, selection):
    grid = [[0] * 14 for _ in range(8)]
    _frame(grid, 1, 1, 5, 5, 2)
    grid[3][1] = 0  # A four-neighbor passage to the local exterior.
    positive = (2, 9, 3, 3, 8)
    _frame(grid, *positive)
    assert native.mirror(grid, {"selection": selection}) == _filled(grid, [positive])


def test_holes_use_four_neighbor_reachability(native):
    # The diagonal opening cannot connect the central cell to the exterior.
    grid = [[0, 2, 2], [2, 0, 2], [2, 2, 2]]
    assert native.mirror(grid, DEFAULT) == [[0, 2, 2], [2, 2, 2], [2, 2, 2]]


def test_canonical_component_only_fill_overwrites_interior_other_color(native):
    # Native mirror accepts structural grids beyond the sampler grammar. The
    # canonical program treats only the current object's cells as barriers.
    grid = [[2, 2, 2, 2, 2], [2, 0, 0, 0, 2], [2, 0, 7, 0, 2],
            [2, 0, 0, 0, 2], [2, 2, 2, 2, 2]]
    expected = [[2] * 5 for _ in range(5)]
    assert native.mirror(grid, DEFAULT) == expected


def test_mirror_preserves_input_and_returns_fresh_rows(native):
    grid = [[0, 0], [0, 0]]
    before = copy.deepcopy(grid)
    result = native.mirror(grid, DEFAULT)
    assert result == before and grid == before
    assert result is not grid and all(a is not b for a, b in zip(result, grid))


class _DictSubclass(dict):
    pass


@pytest.mark.parametrize("settings", [
    {}, {"selection": "all", "extra": 1}, {"unknown": "all"},
    {"selection": "ALL"}, {"selection": ""}, {"selection": True},
    {"selection": 1}, {"selection": 1.0}, {"selection": None},
    {"selection": []}, "all", ["all"], _DictSubclass(selection="all"),
])
def test_strict_settings_reject_wrong_keys_types_and_values(native, adapter, settings):
    with pytest.raises(ValueError):
        adapter.program(settings)
    with pytest.raises(ValueError):
        adapter.generate(0, settings, 3, 4)
    with pytest.raises(ValueError):
        native.mirror([[0]], settings)


@pytest.mark.parametrize("field,value", [
    ("seed", True), ("seed", False), ("seed", 1.0), ("seed", "0"),
    ("seed", -1), ("seed", 2**63), ("seed", None),
    ("demos", True), ("demos", 3.0), ("demos", "3"),
    ("demos", 2), ("demos", 7), ("demos", None),
    ("queries", True), ("queries", 4.0), ("queries", "4"),
    ("queries", 0), ("queries", 5), ("queries", None),
])
def test_request_scalars_are_exact_bounded_integers(adapter, field, value):
    request = dict(seed=0, settings=DEFAULT, demos=3, queries=4)
    request[field] = value
    with pytest.raises(ValueError):
        adapter.generate(**request)


@pytest.mark.parametrize("grid", [
    None, (), [], [[]], [()], [[True]], [[0.0]], [[-1]], [[10]],
    [[0], [0, 0]], [[0] * 31], [[0] for _ in range(31)], ((0,),),
])
def test_grid_contract_rejects_malformed_and_noninteger_cells(native, grid):
    with pytest.raises(ValueError):
        native.validate_grid(grid)
    with pytest.raises(ValueError):
        native.mirror(grid, DEFAULT)


@pytest.mark.parametrize("grid", [[[0]], [[9] * 30 for _ in range(30)]])
def test_grid_contract_allows_exact_dimension_boundaries(native, grid):
    before = copy.deepcopy(grid)
    native.validate_grid(grid)
    assert grid == before


@pytest.mark.parametrize("settings", SETTINGS)
def test_independent_counts_select_stable_prefixes_and_unique_inputs(adapter, settings):
    full = adapter.generate(17, settings, 6, 4)
    for demos, queries in ((3, 1), (3, 4), (6, 1), (6, 4)):
        episode = adapter.generate(17, settings, demos, queries)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == queries
        assert episode["train"] == full["train"][:demos]
        assert episode["test"] == full["test"][:queries]
        assert episode["program_solution"] == adapter.program(settings)
        inputs = [json.dumps(pair["input"]) for split in ("train", "test")
                  for pair in episode[split]]
        assert len(inputs) == len(set(inputs))


def test_input_bank_is_matched_across_all_settings(adapter):
    episodes = [adapter.generate(23, setting, 6, 4) for setting in SETTINGS]
    inputs = [{split: [p["input"] for p in episode[split]] for split in ("train", "test")}
              for episode in episodes]
    assert inputs[0] == inputs[1] == inputs[2]
    assert len({episode["program_solution"] for episode in episodes}) == 3


@pytest.mark.parametrize("seed", (0, 17))
def test_query_size_boundary_has_substantive_content_across_the_canvas(adapter, seed):
    episode = adapter.generate(seed, DEFAULT, 3, 4)
    queries = [pair["input"] for pair in episode["test"]]
    assert all(1 <= len(grid) <= 30 and 1 <= len(grid[0]) <= 30 for grid in queries)
    assert any(min(len(grid), len(grid[0])) <= 10 for grid in queries)
    large = [grid for grid in queries if len(grid) == len(grid[0]) == 30]
    assert len(large) == 1
    grid = large[0]
    assert sum(cell != 0 for row in grid for cell in row) >= 200
    assert any(grid[0]) and any(grid[-1])
    assert any(row[0] for row in grid) and any(row[-1] for row in grid)
    for row_start in (0, 15):
        for col_start in (0, 15):
            assert any(grid[r][c] for r in range(row_start, row_start + 15)
                       for c in range(col_start, col_start + 15))


@pytest.mark.parametrize("seed", (0, 17, 2**63 - 1))
def test_minimum_lesson_distinguishes_all_declared_settings_without_queries(native, adapter, seed):
    for setting in SETTINGS:
        episode = adapter.generate(seed, setting, 3, 4)
        survivors = [candidate for candidate in SETTINGS if all(
            native.mirror(pair["input"], candidate) == pair["output"]
            for pair in episode["train"])]
        assert survivors == [setting]


@pytest.mark.parametrize("seed", (0, 17))
@pytest.mark.parametrize("settings", SETTINGS)
def test_minimum_lesson_selects_border_and_strict_interior_objects(native, adapter, seed, settings):
    episode = adapter.generate(seed, settings, 3, 4)
    selected_positions = set()
    for pair in episode["train"]:
        grid = pair["input"]
        eligible = [record for record in native.analyze_grid(grid) if record["area"] > 0]
        if settings["selection"] != "all":
            scores = [record["area"] for record in eligible]
            extreme = max(scores) if settings["selection"] == "largest" else min(scores)
            eligible = [record for record in eligible if record["area"] == extreme]
        for record in eligible:
            assert any(grid[r][c] != record["color"] for r, c in record["holes"])
            assert all(pair["output"][r][c] == record["color"] for r, c in record["holes"])
            r0, c0, r1, c1 = record["bbox"]
            touches_border = r0 == 0 or c0 == 0 or r1 == len(grid) - 1 or c1 == len(grid[0]) - 1
            selected_positions.add("border" if touches_border else "strict_interior")
    assert selected_positions == {"border", "strict_interior"}


def test_generation_is_deterministic_and_does_not_mutate_global_rng_or_settings(adapter):
    state = random.getstate()
    settings = {"selection": "smallest"}
    before_settings = copy.deepcopy(settings)
    try:
        random.seed(918273)
        expected_state = random.getstate()
        first = adapter.generate(31, settings, 3, 4)
        second = adapter.generate(31, settings, 3, 4)
        assert random.getstate() == expected_state
        assert settings == before_settings
        assert first == second
        before = copy.deepcopy(second)
        first["train"][0]["input"][0][0] = (first["train"][0]["input"][0][0] + 1) % 10
        first["test"][0]["output"][0][0] = (first["test"][0]["output"][0][0] + 1) % 10
        assert second == before
        assert adapter.generate(31, settings, 3, 4) == before
    finally:
        random.setstate(state)


def test_omitted_settings_choose_one_reproducible_episode_program(native):
    first = native.generate(19)
    assert first == native.generate(19, None, 3, 4)
    assert first["program_solution"] in {native.program(s) for s in SETTINGS}


def test_public_projection_ignores_private_metadata_and_query_answers(adapter):
    from reviewer_support import public_challenge_bytes, public_challenge_id

    episode = adapter.generate(5, DEFAULT, 3, 4)
    visible = public_challenge_bytes(episode)
    identifier = public_challenge_id(episode)
    changed = copy.deepcopy(episode)
    changed.update(settings={"selection": "smallest"}, seed=999,
                   program_solution="private different program", private_notes="hidden")
    for query in changed["test"]:
        query["output"] = [[9]]
    assert public_challenge_bytes(changed) == visible
    assert public_challenge_id(changed) == identifier
    public = json.loads(visible)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    changed["train"][0]["output"][0][0] = (changed["train"][0]["output"][0][0] + 1) % 10
    assert public_challenge_id(changed) != identifier


def test_existing_one_query_projection_has_identical_first_turn(adapter):
    from reviewer_support import public_challenge_bytes

    episode = json.loads(public_challenge_bytes(adapter.generate(5, DEFAULT, 3, 4)))
    prompts = [{"train": episode["train"], "test": [query]} for query in episode["test"]]
    one_query = {"train": episode["train"], "test": episode["test"][:1]}
    assert public_challenge_bytes(prompts[0]) == public_challenge_bytes(one_query)
    assert len(prompts) == 4
    for index, prompt in enumerate(prompts):
        assert set(prompt) == {"train", "test"}
        assert len(prompt["test"]) == 1
        assert set(prompt["test"][0]) == {"input"}
        assert prompt["test"][0]["input"] == episode["test"][index]["input"]
