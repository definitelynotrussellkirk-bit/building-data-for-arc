"""Independent behavioral contract for the native parametric ring family."""
from __future__ import annotations

import copy
from functools import lru_cache
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_path, find_root


TASK_ID = "630d6cc550e4"
PROTOTYPE = Path(__file__).resolve().parents[1] / "workspace" / "parametric" / "prototype.py"
MODES = ("canonical", "inverse", "odd_canonical", "even_canonical")

# Hand-derived examples, independent of the implementation's permutation data.
EVEN_RING = [[0, 1, 2], [3, 7, 4], [5, 6, 8]]
EVEN_CANONICAL = [[2, 3, 8], [6, 7, 1], [0, 4, 5]]
EVEN_INVERSE = [[5, 4, 0], [1, 7, 6], [8, 3, 2]]
ODD_RING = [[0, 1, 2], [2, 7, 1], [1, 0, 2]]
ODD_CANONICAL = [[2, 2, 2], [0, 7, 1], [0, 1, 1]]
ODD_INVERSE = [[1, 1, 0], [1, 7, 0], [2, 2, 2]]


def _scene(size, *placements):
    grid = [[7] * size for _ in range(size)]
    for top, left, ring in placements:
        for dr, row in enumerate(ring):
            grid[top + dr][left:left + 3] = row[:]
    return grid


def _pair_payloads(pairs):
    return [{"input": pair["input"], "output": pair["output"]} for pair in pairs]


def _assert_generated_scene(grid):
    """Recognize full separated rings without using production detectors."""
    height, width = len(grid), len(grid[0])
    assert 7 <= height <= 30 and 7 <= width <= 30
    assert all(len(row) == width for row in grid)
    assert all(type(value) is int and 0 <= value <= 9 for row in grid for value in row)
    border = [(r, c) for r in range(3) for c in range(3) if (r, c) != (1, 1)]
    boxes = [(r, c) for r in range(height - 2) for c in range(width - 2)
             if grid[r + 1][c + 1] == 7
             and all(grid[r + dr][c + dc] != 7 for dr, dc in border)]
    assert boxes, "generated scene has no complete ring"
    occupied = {(r + dr, c + dc) for r, c in boxes for dr, dc in border}
    actual = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 7}
    assert occupied == actual, "foreground must belong to complete rings"
    assert len(occupied) == 8 * len(boxes), "rings must not overlap"
    for index, (r, c) in enumerate(boxes):
        for other_r, other_c in boxes[index + 1:]:
            assert r + 3 < other_r or other_r + 3 < r or c + 3 < other_c or other_c + 3 < c


@lru_cache(maxsize=1)
def _prototype():
    assert PROTOTYPE.is_file(), "parametric ring prototype has not been implemented"
    spec = importlib.util.spec_from_file_location("independent_parametric_rings", PROTOTYPE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=1)
def _canonical():
    path = canonical_path(find_root(__file__))
    rows = [json.loads(line) for line in path.open(encoding="utf-8") if line.strip()]
    matches = [row for row in rows if row.get("task_id") == TASK_ID
               and row.get("source") == "training" and row.get("parent_hash") is None]
    assert len(matches) == 1
    return matches[0]


def test_default_program_preserves_exact_canonical_bytes():
    prototype = _prototype()
    original = _canonical()["program_solution"]
    assert prototype.program({}) == original
    assert prototype.program({"ring_motion": "canonical"}) == original


def test_default_rule_matches_all_official_labelled_pairs():
    prototype = _prototype()
    original = _canonical()
    pairs = original["train"] + original["test"]
    assert pairs
    for pair in pairs:
        assert prototype.apply_rule(pair["input"], {}) == pair["output"]


@pytest.mark.parametrize("mode,want", [
    ("canonical", EVEN_CANONICAL),
    ("inverse", EVEN_INVERSE),
    ("odd_canonical", EVEN_INVERSE),
    ("even_canonical", EVEN_CANONICAL),
])
def test_exact_eight_color_ring_permutation_includes_zero_in_parity(mode, want):
    assert _prototype().apply_rule(EVEN_RING, {"ring_motion": mode}) == want


@pytest.mark.parametrize("mode,want", [
    ("odd_canonical", ODD_CANONICAL),
    ("even_canonical", ODD_INVERSE),
])
def test_repetitions_count_as_distinct_colors_not_eight_cells(mode, want):
    assert _prototype().apply_rule(ODD_RING, {"ring_motion": mode}) == want


def test_inverse_undoes_canonical_in_both_orders():
    prototype = _prototype()
    for grid in (EVEN_RING, ODD_RING):
        forward = prototype.apply_rule(grid, {"ring_motion": "canonical"})
        backward = prototype.apply_rule(grid, {"ring_motion": "inverse"})
        assert prototype.apply_rule(forward, {"ring_motion": "inverse"}) == grid
        assert prototype.apply_rule(backward, {"ring_motion": "canonical"}) == grid


@pytest.mark.parametrize("mode,first,second", [
    ("odd_canonical", EVEN_INVERSE, ODD_CANONICAL),
    ("even_canonical", EVEN_CANONICAL, ODD_INVERSE),
])
def test_contextual_choice_is_per_ring_and_preserves_background(mode, first, second):
    grid = _scene(7, (0, 0, EVEN_RING), (4, 4, ODD_RING))
    untouched = copy.deepcopy(grid)
    want = _scene(7, (0, 0, first), (4, 4, second))
    actual = _prototype().apply_rule(grid, {"ring_motion": mode})
    assert actual == want
    assert grid == untouched, "applying the rule must not mutate the input"
    actual[0][0] = 9
    assert grid == untouched, "returned rows must not alias input rows"


def test_thirty_by_thirty_boundary_rings_have_exact_outputs():
    grid = _scene(30, (0, 0, EVEN_RING), (27, 27, ODD_RING))
    want = _scene(30, (0, 0, EVEN_INVERSE), (27, 27, ODD_CANONICAL))
    assert _prototype().apply_rule(grid, {"ring_motion": "odd_canonical"}) == want


@pytest.mark.parametrize("settings", [
    None, [], "canonical", {"ring_motion": "clockwise"},
    {"ring_motion": True}, {"ring_motion": None},
    {"unknown": "canonical"}, {"ring_motion": "canonical", "unknown": 1},
])
def test_invalid_settings_are_rejected_at_public_boundaries(settings):
    prototype = _prototype()
    with pytest.raises((TypeError, ValueError)):
        prototype.validate_settings(settings)
    with pytest.raises((TypeError, ValueError)):
        prototype.program(settings)
    with pytest.raises((TypeError, ValueError)):
        prototype.generate(0, settings)


@pytest.mark.parametrize("seed", [True, False, 0.0, "0", None, -1, 2**63])
def test_invalid_seed_scalars_do_not_alias_valid_calls(seed):
    with pytest.raises((TypeError, ValueError)):
        _prototype().generate(seed, {"ring_motion": "canonical"})


@pytest.mark.parametrize("name,value", [
    ("demos", True), ("demos", 2.0), ("demos", "3"),
    ("demos", None), ("demos", 1), ("demos", 7),
    ("queries", True), ("queries", 1.0), ("queries", "2"),
    ("queries", None), ("queries", 0), ("queries", 5),
])
def test_counts_are_strict_independent_bounded_integers(name, value):
    with pytest.raises((TypeError, ValueError)):
        _prototype().generate(0, {"ring_motion": "canonical"}, **{name: value})


@pytest.mark.parametrize("seed,demos,queries", [(0, 2, 1), (2**63 - 1, 6, 4)])
def test_valid_scalar_endpoints_produce_requested_novel_pairs(seed, demos, queries):
    episode = _prototype().generate(seed, {"ring_motion": "odd_canonical"}, demos=demos, queries=queries)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == queries
    pairs = episode["train"] + episode["test"]
    keys = [json.dumps(pair["input"], separators=(",", ":")) for pair in pairs]
    assert len(keys) == len(set(keys)), "every query must be novel and distinct from all demos"
    for pair in pairs:
        _assert_generated_scene(pair["input"])
        assert (len(pair["output"]), len(pair["output"][0])) == (len(pair["input"]), len(pair["input"][0]))


def test_common_inputs_across_settings_and_demos_identify_each_setting():
    prototype = _prototype()
    baseline = None
    for mode in MODES:
        settings = {"ring_motion": mode}
        episode = prototype.generate(17, settings, demos=2, queries=4)
        inputs = {split: [pair["input"] for pair in episode[split]] for split in ("train", "test")}
        if baseline is None:
            baseline = inputs
        assert inputs == baseline, "private setting must not change the common input stream"
        for rival in MODES:
            if rival != mode:
                assert any(prototype.apply_rule(pair["input"], {"ring_motion": rival}) != pair["output"]
                           for pair in episode["train"]), f"visible demos leave {rival} viable for {mode}"


def test_changing_counts_preserves_demo_and_query_prefixes():
    prototype = _prototype()
    settings = {"ring_motion": "even_canonical"}
    complete = prototype.generate(17, settings, demos=6, queries=4)
    for demos, queries in ((2, 1), (3, 4), (6, 2)):
        shorter = prototype.generate(17, settings, demos=demos, queries=queries)
        assert _pair_payloads(shorter["train"]) == _pair_payloads(complete["train"][:demos])
        assert _pair_payloads(shorter["test"]) == _pair_payloads(complete["test"][:queries])


def test_generation_is_deterministic_and_returns_fresh_pair_storage():
    prototype = _prototype()
    first = prototype.generate(0, {}, demos=2, queries=1)
    second = prototype.generate(0, {}, demos=2, queries=1)
    assert _pair_payloads(first["train"]) == _pair_payloads(second["train"])
    assert _pair_payloads(first["test"]) == _pair_payloads(second["test"])
    saved = copy.deepcopy(second["train"][0]["input"])
    first["train"][0]["input"][0][0] = (first["train"][0]["input"][0][0] + 1) % 10
    assert second["train"][0]["input"] == saved


def test_public_projection_has_one_query_and_ignores_private_and_future_data():
    prototype = _prototype()
    episode = prototype.generate(0, {"ring_motion": "odd_canonical"}, demos=3, queries=4)
    raw = prototype.public_challenge_bytes(episode)
    assert isinstance(raw, bytes)
    visible = json.loads(raw)
    assert set(visible) == {"train", "test"}
    assert visible["train"] == _pair_payloads(episode["train"])
    assert visible["test"] == [{"input": episode["test"][0]["input"]}]
    altered = copy.deepcopy(episode)
    altered.update({"settings": {"ring_motion": "inverse"}, "seed": 123456,
                    "program": "PRIVATE_SENTINEL", "query_answers": [[[9]]]})
    for pair in altered["test"]:
        pair["output"] = [[9]]
    altered["test"][1]["input"] = [[9]]
    assert prototype.public_challenge_bytes(altered) == raw
    single = prototype.generate(0, {"ring_motion": "odd_canonical"}, demos=3, queries=1)
    assert prototype.public_challenge_bytes(single) == raw, "first turn must match single-query use"
    changed_demo = copy.deepcopy(episode)
    changed_demo["train"][0]["output"] = [[9]]
    assert prototype.public_challenge_bytes(changed_demo) != raw


def test_public_bytes_match_native_content_identity_convention():
    from reviewer_support import public_challenge_bytes as native_bytes
    prototype = _prototype()
    episode = prototype.generate(0, {}, demos=2, queries=1)
    visible = {"train": _pair_payloads(episode["train"]),
               "test": [{"input": episode["test"][0]["input"]}]}
    assert prototype.public_challenge_bytes(episode) == native_bytes(visible)
