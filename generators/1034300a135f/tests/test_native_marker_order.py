"""Bounded behavioral checks for the native marker-order parametric adapter.

These tests cover the opt-in family, not the unchanged production sampler.
The hand-built ordering witness is labelled through the protected Racket bridge.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_path, find_root


TASK = "1034300a135f"
ROOT = find_root(__file__)
ORDERS = ("near_to_far", "far_to_near")


def _source_path(filename):
    """Find this task's exact source in either the library or a copied runtime."""
    identity = f"generators/{TASK}/workspace/parametric/{filename}"
    manifest = ROOT / "RUNTIME_MANIFEST.json"
    if manifest.is_file():
        entries = [
            row for row in json.loads(manifest.read_text())["files"]
            if row.get("library_path") == identity
        ]
        entries.sort(key=lambda row: row.get("runtime_path") == identity)
        if entries:
            return ROOT / entries[0]["runtime_path"]
    return ROOT / identity


def _load(filename):
    source = _source_path(filename)
    assert source.is_file(), f"missing native family source: {source}"
    name = f"native_marker_order_1034300a135f_{source.stem}"
    spec = importlib.util.spec_from_file_location(name, source)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def proto():
    return _load("prototype.py")


@pytest.fixture(scope="module")
def adapter():
    return _load("adapter.py")


@pytest.fixture(scope="module")
def episode(proto):
    @lru_cache(maxsize=None)
    def make(order="near_to_far", seed=17, demos=3, queries=4):
        return proto.native_generate(
            seed, {"marker_order": order}, demos=demos, queries=queries,
        )
    return make


@pytest.fixture(scope="module")
def racket():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    bridge = RacketBridge()
    identity = bridge.runtime_identity
    assert identity["backend"] == "racket" and identity["protected"] is True

    def apply(program, grid):
        literal = "'(" + " ".join(
            "(" + " ".join(map(str, row)) + ")" for row in grid
        ) + ")"
        return bridge.eval_text(f"({wrap_rule(program)} {literal})")

    try:
        yield apply
    finally:
        bridge.close()


def _visible_inputs(ep):
    return {split: [pair["input"] for pair in ep[split]] for split in ("train", "test")}


def _rings(height, width, colors, background):
    """Independent expected grid: draw nested rectangular perimeters."""
    grid = [[background] * width for _ in range(height)]
    for rank, color in enumerate(colors):
        bottom, right = height - rank - 1, width - rank - 1
        if rank > bottom or rank > right:
            break
        for col in range(rank, right + 1):
            grid[rank][col] = color
            grid[bottom][col] = color
        for row in range(rank, bottom + 1):
            grid[row][rank] = color
            grid[row][right] = color
    return grid


def _markers(grid):
    counts = Counter(value for row in grid for value in row if value != 0)
    background = counts.most_common(1)[0][0]
    height, width = len(grid), len(grid[0])
    markers = [
        (min(row, col, height - 1 - row, width - 1 - col), row, col, value)
        for row, cells in enumerate(grid)
        for col, value in enumerate(cells)
        if value != background
    ]
    return background, markers


def test_native_default_preserves_exact_authority_bytes(proto, adapter):
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        programs = {
            row["program_solution"]
            for row in map(json.loads, handle)
            if row.get("task_id") == TASK
        }
    assert len(programs) == 1
    canonical = programs.pop()
    assert proto.native_program({"marker_order": "near_to_far"}) == canonical
    assert adapter.program({"marker_order": "near_to_far"}) == canonical
    alternate = adapter.program({"marker_order": "far_to_near"})
    assert alternate != canonical
    assert alternate == proto.native_program({"marker_order": "far_to_near"})


@pytest.mark.parametrize("order,first,second", [
    ("near_to_far", [2, 1, 8, 4, 6], [2, 6, 1, 8, 4]),
    ("far_to_near", [6, 4, 8, 2, 1], [4, 8, 2, 6, 1]),
])
def test_input_dependent_global_ranking_is_needed_before_ring_painting(
    proto, racket, order, first, second,
):
    original = [[7] * 11 for _ in range(11)]
    for row, col, color in ((0, 9, 2), (1, 3, 8), (2, 4, 4), (3, 5, 6), (8, 10, 1)):
        original[row][col] = color
    moved = deepcopy(original)
    moved[3][5], moved[3][10] = 7, 6
    assert [m[3] for m in _markers(original)[1]] == [2, 8, 4, 6, 1]
    assert [m[3] for m in _markers(moved)[1]] == [2, 8, 4, 6, 1]
    program = proto.native_program({"marker_order": order})
    output = racket(program, original)
    moved_output = racket(program, moved)
    assert output == _rings(11, 11, first, 7)
    assert moved_output == _rings(11, 11, second, 7)
    assert output != moved_output
    skip_sort = _rings(11, 11, [2, 8, 4, 6, 1], 7)
    assert skip_sort != output and skip_sort != moved_output


@pytest.mark.parametrize("order", ORDERS)
def test_native_episode_labels_execute_in_protected_racket(proto, episode, racket, order):
    ep = episode(order)
    assert ep["program_solution"] == proto.native_program({"marker_order": order})
    for pair in ep["train"] + ep["test"]:
        assert racket(ep["program_solution"], pair["input"]) == pair["output"]


@pytest.mark.parametrize("demos", range(2, 7))
@pytest.mark.parametrize("queries", (1, 4))
def test_independent_requested_counts_and_distinct_typed_grids(episode, demos, queries):
    ep = episode(demos=demos, queries=queries)
    assert (len(ep["train"]), len(ep["test"])) == (demos, queries)
    pairs = ep["train"] + ep["test"]
    fingerprints = {tuple(map(tuple, pair["input"])) for pair in pairs}
    assert len(fingerprints) == len(pairs)
    for pair in pairs:
        for grid in (pair["input"], pair["output"]):
            assert type(grid) is list and 5 <= len(grid) <= 30
            assert type(grid[0]) is list and 5 <= len(grid[0]) <= 30
            assert all(type(row) is list and len(row) == len(grid[0]) for row in grid)
            assert all(type(value) is int and 0 <= value <= 9 for row in grid for value in row)


@pytest.mark.parametrize("name,bad", [
    ("seed", True), ("seed", False), ("seed", 1.0), ("seed", "17"),
    ("seed", None), ("seed", -1), ("seed", 2**63),
    ("demos", True), ("demos", 3.0), ("demos", "3"), ("demos", None),
    ("demos", 1), ("demos", 7),
    ("queries", True), ("queries", 1.0), ("queries", "4"), ("queries", None),
    ("queries", 0), ("queries", 5),
])
def test_bad_scalar_requests_fail_closed(proto, name, bad):
    request = {"seed": 17, "settings": {"marker_order": "near_to_far"}, "demos": 3, "queries": 4}
    request[name] = bad
    with pytest.raises((TypeError, ValueError)):
        proto.native_generate(**request)


@pytest.mark.parametrize("settings", [
    None, {}, [], "near_to_far", {"marker_order": True},
    {"marker_order": "unknown"}, {"marker_order": "near_to_far", "extra": 1},
])
def test_settings_are_an_exact_bounded_contract(proto, settings):
    with pytest.raises((TypeError, ValueError)):
        proto.native_program(settings)
    with pytest.raises((TypeError, ValueError)):
        proto.native_generate(17, settings, demos=2, queries=1)


def test_seed_endpoints_and_replay_are_supported(proto):
    settings = {"marker_order": "near_to_far"}
    for seed in (0, 2**63 - 1):
        ep = proto.native_generate(seed, settings, demos=2, queries=1)
        assert ep == proto.native_generate(seed, settings, demos=2, queries=1)


def test_setting_and_count_changes_preserve_input_streams(episode):
    near, far = episode("near_to_far"), episode("far_to_near")
    assert _visible_inputs(near) == _visible_inputs(far)
    assert any(a["output"] != b["output"] for a, b in zip(near["train"], far["train"]))
    short, long = episode(demos=2), episode(demos=6)
    assert _visible_inputs(short)["test"] == _visible_inputs(long)["test"]
    assert short["train"] == long["train"][:2]
    one = episode(queries=1)
    assert one["train"] == near["train"]
    assert one["test"] == near["test"][:1]


def test_full_canvas_boundary_is_substantive_and_taught(episode):
    ep = episode(demos=2)
    assert sorted((len(ep["train"][0]["input"]), len(ep["train"][0]["input"][0]))) == [11, 13]
    assert sorted((len(ep["train"][1]["input"]), len(ep["train"][1]["input"][0]))) == [29, 30]
    assert [sorted((len(p["input"]), len(p["input"][0]))) for p in ep["test"]] == [
        [5, 5], [17, 25], [23, 29], [30, 30],
    ]
    for pair in (ep["train"][1], ep["test"][-1]):
        grid = pair["input"]
        background, markers = _markers(grid)
        assert len(markers) == 15
        assert max(m[0] for m in markers) == 14
        assert len({m[3] for m in markers}) < len(markers)
        assert 0 in {m[3] for m in markers}
        assert max(m[1] for m in markers) - min(m[1] for m in markers) >= 20
        assert max(m[2] for m in markers) - min(m[2] for m in markers) >= 20
        assert sum(a != b for old, new in zip(grid, pair["output"]) for a, b in zip(old, new)) > 600
        assert pair["output"][14][14] != background


def test_public_bytes_and_identifier_ignore_all_private_metadata(proto, episode):
    ep = episode()
    encoded = proto.native_challenge_bytes(ep)
    assert type(encoded) is bytes
    assert proto.native_challenge_id(ep) == hashlib.sha256(encoded).hexdigest()
    public = json.loads(encoded)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    changed = deepcopy(ep)
    changed.update(seed=12345, settings={"marker_order": "far_to_near"},
                   program_solution="PRIVATE PROGRAM SENTINEL", private_note="PRIVATE NOTE SENTINEL")
    for split in ("train", "test"):
        for pair in changed[split]:
            pair["private_setting"] = "PRIVATE PAIR SENTINEL"
    for pair in changed["test"]:
        pair["output"] = [[9]]
    assert proto.native_challenge_bytes(changed) == encoded
    assert proto.native_challenge_id(changed) == proto.native_challenge_id(ep)
    changed["train"][0]["output"][0][0] = (changed["train"][0]["output"][0][0] + 1) % 10
    assert proto.native_challenge_id(changed) != proto.native_challenge_id(ep)


def test_public_turn_has_only_current_query_and_no_future_count_cues(proto, episode):
    ep = episode()
    first = proto.native_public_turn(ep, query_index=0)
    assert first == proto.native_public_turn(episode(queries=1), query_index=0)
    expected_train = [
        {"input": pair["input"], "output": pair["output"]} for pair in ep["train"]
    ]
    for index in range(4):
        visible = proto.native_public_turn(ep, query_index=index)
        assert visible == {"train": expected_train, "test": [{"input": ep["test"][index]["input"]}]}
    for bad in (-1, 4, True, 1.0, "1", None):
        with pytest.raises((TypeError, ValueError)):
            proto.native_public_turn(ep, query_index=bad)


@pytest.mark.parametrize("order", ORDERS)
def test_two_demos_reject_rank_caps_and_simple_ordering_shortcuts(episode, order):
    ep = episode(order, demos=2)
    names = ("cap8", "cap14", "row_major", "reverse_ties", "numeric_ties_ascending",
             "numeric_ties_descending", "ignore_zero", "deduplicate", "numeric", "extend_last")
    rejected = {name: False for name in names}
    for pair in ep["train"]:
        grid = pair["input"]
        height, width = len(grid), len(grid[0])
        background, markers = _markers(grid)
        sign = 1 if order == "near_to_far" else -1
        ordered = sorted(markers, key=lambda m: sign * m[0])
        colors = [m[3] for m in ordered]
        reversed_ties = sorted(markers, key=lambda m: (sign * m[0], -m[1], -m[2]))
        rivals = {
            "cap8": colors[:8],
            "cap14": colors[:14],
            "row_major": [m[3] for m in markers],
            "reverse_ties": [m[3] for m in reversed_ties],
            "numeric_ties_ascending": [m[3] for m in sorted(markers, key=lambda m: (sign * m[0], m[3]))],
            "numeric_ties_descending": [m[3] for m in sorted(markers, key=lambda m: (sign * m[0], -m[3]))],
            "ignore_zero": [color for color in colors if color != 0],
            "deduplicate": list(dict.fromkeys(colors)),
            "numeric": sorted(colors),
            "extend_last": colors + [colors[-1]] * 15,
        }
        for name, sequence in rivals.items():
            rejected[name] |= _rings(height, width, sequence, background) != pair["output"]
    assert all(rejected.values()), rejected
