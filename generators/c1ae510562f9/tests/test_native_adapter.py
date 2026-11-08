"""Native promotion regressions for the retained spiral-direction prototype."""
from __future__ import annotations

from collections import Counter
import copy
import importlib.util
import json
from pathlib import Path
import random

import pytest

TASK = Path(__file__).resolve().parents[1]
ROOT = TASK.parents[1]
HOME = TASK / "workspace/parametric"


def load(name):
    spec = importlib.util.spec_from_file_location("spiral_native_test_" + name, HOME / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def family():
    return load("native_family")


@pytest.fixture(scope="module")
def adapter():
    return load("adapter")


@pytest.fixture(scope="module")
def racket():
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator
    with _local_imports(ROOT / "shared/runtime", HOME):
        apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
        assert identity["backend"] == "racket" and identity["protected"] is True
        try:
            yield apply
        finally:
            bridge.close()


def test_reuses_retained_programs_and_exact_default_seven_official_pairs(adapter, family, racket):
    row = next(json.loads(line) for line in (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
               if json.loads(line).get("task_id") == "c1ae510562f9")
    old = load("spiral_direction")
    for direction in old.ALLOWED_DIRECTIONS:
        assert adapter.program({"spiral_direction": direction}) == old.materialize_rule(direction)
    assert adapter.program({"spiral_direction": "clockwise"}) == row["program_solution"]
    assert len(row["train"] + row["test"]) == 7
    for pair in row["train"] + row["test"]:
        assert family.apply_claim(pair["input"], {"spiral_direction": "clockwise"}) == pair["output"]
        assert racket(row["program_solution"], pair["input"]) == pair["output"]


@pytest.mark.parametrize("direction", ["clockwise", "counterclockwise"])
def test_count_depends_on_row_occupancy_not_color_histogram(family, adapter, racket, direction):
    interior = [[8, 8], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [8, 0]]
    first = family.make_input(interior, top=1, left=1)
    moved = copy.deepcopy(interior)
    moved[0][1], moved[1][1] = 0, 8
    second = family.make_input(moved, top=1, left=1)
    assert Counter(v for row in first for v in row) == Counter(v for row in second for v in row)
    settings = {"spiral_direction": direction}
    assert family.describe(first, settings)["empty_row_count"] == 5
    assert family.describe(second, settings)["empty_row_count"] == 4
    a, b = [racket(adapter.program(settings), grid) for grid in (first, second)]
    assert sum(v == 8 for row in a for v in row) == 5
    assert sum(v == 8 for row in b for v in row) == 4
    assert sum(x != y for ra, rb in zip(a, b) for x, y in zip(ra, rb)) == 1
    area_rule = family.rivals(settings)["zero_area_div_width"]
    assert racket(area_rule, first) == racket(area_rule, second)
    assert racket(area_rule, second) != b


@pytest.mark.parametrize("direction", ["clockwise", "counterclockwise"])
def test_minimum_lesson_rejects_early_saturation_and_forced_nonzero(family, adapter, racket, direction):
    episode = adapter.generate(0, {"spiral_direction": direction}, 3, 4)
    for expression in (f"(min 6 {family._EMPTY})", f"(max 1 {family._EMPTY})"):
        rival = family._rival_rule(direction, expression)
        assert any(racket(rival, pair["input"]) != pair["output"] for pair in episode["train"])


@pytest.mark.parametrize("count", [0, 1, 8, 9, 28])
def test_lawful_endpoints_and_saturation(family, adapter, racket, count):
    grid = family.make_input([[0, 0]] * count + [[8, 0]], pad_bottom=0)
    for direction in family.SETTINGS:
        settings = {"spiral_direction": direction}
        actual = racket(adapter.program(settings), grid)
        assert actual == family.apply_claim(grid, settings)
        assert len(actual) == len(actual[0]) == 3
        assert sum(v == 8 for row in actual for v in row) == min(count, 9)


@pytest.mark.parametrize("seed", [0, 17, 2**63 - 1])
def test_three_demo_boundary_witnesses_and_full_canvas_geometry(family, adapter, seed):
    episode = adapter.generate(seed, {"spiral_direction": "clockwise"}, 3, 4)
    details = [family.describe(pair["input"], {"spiral_direction": "clockwise"}) for pair in episode["train"]]
    assert [d["empty_row_count"] for d in details[:2]] == [0, 5]
    assert details[2]["empty_row_count"] >= 9
    assert details[0]["row_occupied_counts"][0] > 0 and details[0]["row_occupied_counts"][-1] > 0
    assert details[1]["row_occupied_counts"][0] == details[1]["row_occupied_counts"][-1] == 0
    assert len(details[0]["partial_row_indices"]) == 6 and len(details[1]["partial_row_indices"]) == 2
    last = family.describe(episode["test"][-1]["input"], {"spiral_direction": "clockwise"})
    assert last["input_shape"] == [30, 30]
    assert last["interior_shape"] == [29, 28]
    assert last["bounds"] == [0, 29, 0, 29]
    assert 2 <= last["empty_row_count"] <= 7
    assert last["cyan_cells"] > 200
    assert last["output_shape"] == [3, 3]
    assert family.apply_claim(episode["test"][-1]["input"], {"spiral_direction": "counterclockwise"}) != episode["test"][-1]["output"]


def test_shared_inputs_counts_prefixes_fresh_outputs_and_global_rng(family, adapter):
    random.seed(22713)
    before = random.getstate()
    settings = {"spiral_direction": "counterclockwise"}
    small = adapter.generate(17, settings, 3, 1)
    ordinary = adapter.generate(17, settings, 3, 4)
    large = adapter.generate(17, settings, 6, 4)
    assert random.getstate() == before
    assert small["train"] == large["train"][:3]
    assert small["test"] == large["test"][:1]
    assert family.public_turn(small, 0) == family.public_turn(ordinary, 0)
    expected = [p["input"] for s in ("train", "test") for p in large[s]]
    assert len({json.dumps(g) for g in expected}) == 10
    for demos in range(3, 7):
        for queries in range(1, 5):
            current = adapter.generate(17, settings, demos, queries)
            assert current["train"] == large["train"][:demos]
            assert current["test"] == large["test"][:queries]
    for direction in family.SETTINGS:
        current = adapter.generate(17, {"spiral_direction": direction}, 6, 4)
        assert [p["input"] for s in ("train", "test") for p in current[s]] == expected
    small["train"][0]["input"][0][0] = 9
    assert adapter.generate(17, settings, 3, 1)["train"] == ordinary["train"]


def test_public_projection_masks_all_private_and_future_data(family, adapter):
    episode = adapter.generate(0, {"spiral_direction": "clockwise"}, 3, 4)
    visible = family.public_turn(episode, 0)
    assert set(visible) == {"train", "test"}
    assert len(visible["test"]) == 1 and set(visible["test"][0]) == {"input"}
    assert all(set(pair) == {"input", "output"} for pair in visible["train"])
    visible["test"][0]["input"][0][0] = 9
    assert episode["test"][0]["input"][0][0] != 9
    for bad in (True, -1, 4):
        with pytest.raises(ValueError):
            family.public_turn(episode, bad)


@pytest.mark.parametrize("settings", [{}, None, {"spiral_direction": True}, {"spiral_direction": "other"},
                                     {"spiral_direction": "clockwise", "extra": 1}])
def test_settings_are_exact_declared_strings(adapter, settings):
    with pytest.raises(ValueError):
        adapter.program(settings)


@pytest.mark.parametrize("seed,demos,queries", [(True,3,4),(-1,3,4),(2**63,3,4),(0,1,4),(0,2,4),
                                               (0,7,4),(0,3.0,4),(0,3,True),(0,3,0),(0,3,5)])
def test_invalid_count_and_seed_rejected(adapter, seed, demos, queries):
    with pytest.raises(ValueError):
        adapter.generate(seed, {"spiral_direction": "clockwise"}, demos, queries)


@pytest.mark.parametrize("grid", [[[True]], [[1.0]], [[0],[0,0]], [[5]*31], [[0]], [[5,5,5],[5,8,5]]])
def test_invalid_grid_or_container_rejected(family, grid):
    with pytest.raises(ValueError):
        family.apply_claim(grid, {"spiral_direction": "clockwise"})
