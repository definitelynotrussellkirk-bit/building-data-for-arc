"""Behavioral checks for native hole-ordering lessons and their public turns."""
from __future__ import annotations

import copy
from fractions import Fraction
import importlib.util
import json

import pytest
from reviewer_support import canonical_path, find_root, public_challenge_bytes


ROOT = find_root(__file__)
HOME = ROOT / "generators/73d82a9cacf6/workspace/parametric"
ORDERS = ("larger_first", "smaller_first")


@pytest.fixture(scope="module")
def adapter():
    path = HOME / "adapter.py"
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location("tested_hole_order_adapter", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_is_exact_selected_reference(adapter):
    assert adapter is not None, "native hole-order adapter is not implemented"
    with canonical_path(ROOT).open() as handle:
        canonical = {r["program_solution"] for r in map(json.loads, handle)
                     if r.get("task_id") == "73d82a9cacf6"}
    assert canonical == {adapter.program({"area_order": "larger_first"})}
    assert adapter.program({"area_order": "smaller_first"}) not in canonical


@pytest.mark.parametrize("order", ORDERS)
def test_literal_packing_in_protected_racket(adapter, order):
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    grid = [[0] * 13 for _ in range(7)]
    for r in range(2):
        for c in range(2):
            grid[r][c] = 4
    for size, color, top, left in ((4, 7, 0, 8), (3, 2, 4, 3)):
        for r in range(size):
            for c in range(size):
                if r in (0, size - 1) or c in (0, size - 1):
                    grid[top + r][left + c] = color
    expected = {
        "larger_first": [[4, 4, 0, 7, 7, 7, 7, 0, 2, 2, 2],
                         [4, 4, 0, 7, 0, 0, 7, 0, 2, 0, 2],
                         [0, 0, 0, 7, 0, 0, 7, 0, 2, 2, 2],
                         [0, 0, 0, 7, 7, 7, 7, 0, 0, 0, 0]],
        "smaller_first": [[4, 4, 0, 2, 2, 2, 0, 7, 7, 7, 7],
                          [4, 4, 0, 2, 0, 2, 0, 7, 0, 0, 7],
                          [0, 0, 0, 2, 2, 2, 0, 7, 0, 0, 7],
                          [0, 0, 0, 0, 0, 0, 0, 7, 7, 7, 7]],
    }[order]
    settings = {"area_order": order}
    assert adapter.predict(grid, settings) == expected
    bridge = RacketBridge()
    try:
        assert bridge.runtime_identity["backend"] == "racket"
        assert bridge.runtime_identity["protected"] is True
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        assert bridge.eval_text(f"({wrap_rule(adapter.program(settings))} {literal})") == expected
    finally:
        bridge.close()


@pytest.mark.parametrize("seed", [0, 17, 2**63 - 1])
@pytest.mark.parametrize("demos,queries", [(2, 1), (2, 4), (6, 1), (6, 4)])
def test_counts_matched_inputs_and_novel_queries(adapter, seed, demos, queries):
    larger = adapter.generate(seed, {"area_order": "larger_first"}, demos, queries)
    smaller = adapter.generate(seed, {"area_order": "smaller_first"}, demos, queries)
    assert (len(larger["train"]), len(larger["test"])) == (demos, queries)
    inputs = [p["input"] for split in ("train", "test") for p in larger[split]]
    assert len({json.dumps(g) for g in inputs}) == demos + queries
    assert all(1 <= len(g) <= 30 and 1 <= len(g[0]) <= 30 for g in inputs)
    for split in ("train", "test"):
        assert [p["input"] for p in larger[split]] == [p["input"] for p in smaller[split]]
        assert all(a["output"] != b["output"] for a, b in zip(larger[split], smaller[split]))


def test_counts_preserve_both_input_prefixes(adapter):
    settings = {"area_order": "smaller_first"}
    full = adapter.generate(17, settings, 6, 4)
    for demos, queries in ((2, 1), (3, 2), (5, 3)):
        small = adapter.generate(17, settings, demos, queries)
        assert small["train"] == full["train"][:demos]
        assert small["test"] == full["test"][:queries]


def test_every_demo_combines_hole_groups_and_area_ties(adapter):
    for seed in (0, 1, 17, 2**63 - 1):
        episode = adapter.generate(seed, {"area_order": "larger_first"}, 6, 4)
        for pair in episode["train"]:
            objects = adapter._source()._objects(pair["input"])
            assert len(objects) == 5
            assert sorted(o["holes"] for o in objects) == [0, 1, 1, 2, 2]
            for holes in (1, 2):
                tied = [o for o in objects if o["holes"] == holes]
                assert len({o["area"] for o in tied}) == 2
            rings = [o for o in objects if o["holes"] == 1]
            area_order = sorted(rings, key=lambda o: o["area"])
            assert area_order[0]["height"] * area_order[0]["width"] > \
                area_order[1]["height"] * area_order[1]["width"]
            scan = [o["color"] for o in objects]
            colors = sorted(scan)
            for sign in (-1, 1):
                correct = [o["color"] for o in sorted(objects,
                           key=lambda o: (o["holes"], sign * o["area"], o["color"]))]
                assert scan != correct
                assert colors != correct


def test_largest_query_has_six_substantial_objects_and_full_width_output(adapter):
    episode = adapter.generate(17, {"area_order": "larger_first"}, 2, 4)
    pair = episode["test"][-1]
    assert (len(pair["input"]), len(pair["input"][0])) == (30, 30)
    assert (len(pair["output"]), len(pair["output"][0])) == (13, 30)
    objects = adapter._source()._objects(pair["input"])
    assert len(objects) == 6
    assert sorted(o["holes"] for o in objects) == [0, 1, 1, 2, 2, 3]
    assert sum(o["area"] for o in objects) == 242
    assert max(o["bottom"] for o in objects) - min(o["top"] for o in objects) >= 27
    assert max(o["right"] for o in objects) - min(o["left"] for o in objects) >= 27


@pytest.mark.parametrize("seed", [0, 17])
@pytest.mark.parametrize("order", ORDERS)
def test_every_rich_pair_rejects_scan_and_color_tiebreaks(adapter, seed, order):
    # Retained v001 audit found arbitrary two-demo rotations could preserve
    # hole-then-scan sorting. Each rich pair must now reject it by construction.
    episode = adapter.generate(seed, {"area_order": order}, 6, 4)
    source = adapter._source()
    for pair in episode["train"] + episode["test"][1:]:
        objects = source._objects(pair["input"])
        for secondary in ("reading_rank", "color"):
            rival = source._pack_objects(sorted(objects, key=lambda o: (o["holes"], o[secondary])))
            assert rival != pair["output"], f"{secondary} shortcut survives one rich pair"


@pytest.mark.parametrize("order", ORDERS)
def test_rich_pairs_distinguish_area_from_density(adapter, order):
    # Independent native review found density fits all original A/B demos yet
    # reverses the two ordinary rings in query 0. Keep that shortcut refuted.
    episode = adapter.generate(0, {"area_order": order}, 6, 4)
    sign = -1 if order == "larger_first" else 1
    source = adapter._source()
    for pair in episode["train"] + episode["test"][1:]:
        objects = source._objects(pair["input"])
        rival = source._pack_objects(sorted(objects, key=lambda o:
            (o["holes"], sign * Fraction(o["area"], o["height"] * o["width"]), o["color"])))
        assert rival != pair["output"], "painted density still explains a rich pair"


@pytest.mark.parametrize("order", ORDERS)
def test_exact_remaining_ties_follow_canonical_color_fallback(adapter, order):
    assert adapter.predict([[5, 0, 2, 0, 7]], {"area_order": order}) == [[2, 0, 5, 0, 7]]


def test_one_query_projection_hides_answers_settings_and_future_count(adapter):
    settings = {"area_order": "smaller_first"}
    many = adapter.generate(17, settings, 3, 4)
    one = adapter.generate(17, settings, 3, 1)
    assert adapter.public_turn(many, 0) == adapter.public_turn(one, 0)
    assert adapter.public_turn(many, 0) == public_challenge_bytes(one)
    visible = json.loads(adapter.public_turn(many, 2))
    assert visible == {"train": many["train"], "test": [{"input": many["test"][2]["input"]}]}
    changed = copy.deepcopy(many)
    changed["settings"] = {"secret": True}
    changed["program_solution"] = "controller only"
    changed["test"][0]["output"] = [[9]]
    changed["test"][1]["input"] = [[8]]
    assert adapter.public_turn(changed, 0) == adapter.public_turn(many, 0)


@pytest.mark.parametrize("kwargs", [
    {"seed": True}, {"seed": -1}, {"seed": 2**63}, {"seed": 0.0},
    {"demos": 1}, {"demos": 7}, {"demos": 2.0}, {"demos": True},
    {"queries": 0}, {"queries": 5}, {"queries": 4.0}, {"queries": False},
    {"settings": None}, {"settings": {}}, {"settings": {"area_order": "random"}},
    {"settings": {"area_order": True}},
    {"settings": {"area_order": "larger_first", "hidden": 1}},
])
def test_invalid_requests_fail_closed(adapter, kwargs):
    request = dict(seed=0, settings={"area_order": "larger_first"}, demos=3, queries=4)
    request.update(kwargs)
    with pytest.raises(ValueError):
        adapter.generate(**request)


@pytest.mark.parametrize("grid", [
    None, [], [[]], [[0]], [[1, 0], [2]], [[True, 0, 2, 0, 3]],
    [[1.0, 0, 2, 0, 3]], [[10, 0, 2, 0, 3]], [[1, 2, 3]],
    [[1, 0, 1, 0, 3]], [[1, 0, 2]], [[0] * 31], [[0]] * 31,
    [[1, 0, 0], [0, 2, 0], [0, 0, 3]],
])
def test_malformed_or_out_of_grammar_grid_is_rejected(adapter, grid):
    with pytest.raises(ValueError):
        adapter.predict(grid, {"area_order": "larger_first"})


def test_nested_bounding_boxes_and_oversized_packing_are_rejected(adapter):
    nested = [[1 if r in (0, 6) or c in (0, 6) else 0 for c in range(9)]
              for r in range(7)]
    # Isolated center object would contaminate the source crop of the ring.
    nested[3][3] = 2
    nested[3][8] = 3
    too_wide = [[color] * 11 if color else [0] * 11 for color in (1, 0, 0, 2, 0, 0, 3)]
    for grid in (nested, too_wide):
        with pytest.raises(ValueError):
            adapter.predict(grid, {"area_order": "larger_first"})


@pytest.mark.parametrize("index", [-1, True, 1.0, 4])
def test_public_turn_rejects_invalid_index(adapter, index):
    episode = adapter.generate(0, {"area_order": "larger_first"}, 3, 4)
    with pytest.raises(ValueError):
        adapter.public_turn(episode, index)


def test_generation_returns_independent_mutable_grids(adapter):
    first = adapter.generate(17, {"area_order": "larger_first"}, 3, 4)
    expected = copy.deepcopy(first)
    first["train"][0]["input"][0][0] = 9
    first["test"][0]["output"][0][0] = 9
    assert adapter.generate(17, {"area_order": "larger_first"}, 3, 4) == expected
