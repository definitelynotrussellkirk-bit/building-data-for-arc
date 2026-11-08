"""Contract tests for the task-local native parametric main prototype.

These tests deliberately need no Racket executable. Native qualification must
separately establish that the returned programs execute the intended labels.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
from fractions import Fraction

import pytest


TASK_HOME = Path(__file__).resolve().parents[1]
REPO = TASK_HOME.parents[1]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))
from reviewer_support import canonical_path, public_challenge_bytes


@pytest.fixture(scope="module")
def proto():
    path = TASK_HOME / "workspace" / "parametric" / "prototype.py"
    assert path.is_file(), f"Native parametric prototype has not been implemented: {path}"
    spec = importlib.util.spec_from_file_location("parametric_38200022d1b7_contract", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def episode(proto, seed=73, mode="all_sources", demos=2, queries=1):
    return proto.generate(seed, {"mode": mode}, demos=demos, queries=queries)


def inputs(result, split):
    return [pair["input"] for pair in result[split]]


def geometry(grid):
    pivots = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 5]
    assert len(pivots) == 1
    pr, pc = pivots[0]
    cells = [(r, c, v, abs(r - pr) + abs(c - pc))
             for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 5)]
    assert cells
    return (pr, pc), cells


def independent_label(grid, mode):
    """Small geometric oracle, independent of prototype selector/label helpers."""
    (pr, pc), cells = geometry(grid)
    chosen = None
    if mode != "all_sources":
        distance = (min if mode == "nearest_color" else max)(cell[3] for cell in cells)
        winners = {v for _, _, v, d in cells if d == distance}
        assert len(winners) == 1, "Generated extremum has an ambiguous color"
        chosen = winners.pop()
    out = copy.deepcopy(grid)
    for r, c, value, _ in cells:
        if chosen is None or value == chosen:
            rr, cc = 2 * pr - r, 2 * pc - c
            if 0 <= rr < len(grid) and 0 <= cc < len(grid[0]):
                out[rr][cc] = value
    return chosen, out


def test_default_program_is_exact_canonical_ledger_source(proto):
    sources = set()
    with canonical_path(REPO).open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("task_id") == "38200022d1b7":
                sources.add(row["program_solution"])
    assert len(sources) == 1
    assert proto.MODES == ("all_sources", "nearest_color", "farthest_color")
    assert proto.DEFAULT_SETTINGS == {"mode": "all_sources"}
    assert proto.program(proto.DEFAULT_SETTINGS) == sources.pop()
    assert len({proto.program({"mode": mode}) for mode in proto.MODES}) == 3


def test_labels_and_selector_follow_point_reflection_and_color_extrema(proto):
    for mode in proto.MODES:
        result = episode(proto, mode=mode, demos=3, queries=2)
        assert result["program_solution"] == proto.program({"mode": mode})
        for pair in result["train"] + result["test"]:
            original = copy.deepcopy(pair["input"])
            chosen, expected = independent_label(pair["input"], mode)
            assert proto.selected_color(pair["input"], mode) == chosen
            assert pair["output"] == expected
            assert pair["output"] != original
            assert pair["input"] == original


def test_same_inputs_across_settings_and_two_demo_teaching_distinction(proto):
    for seed in (0, 73, 2**63 - 1):
        results = {mode: episode(proto, seed=seed, mode=mode) for mode in proto.MODES}
        baseline = results["all_sources"]
        for result in results.values():
            assert inputs(result, "train") == inputs(baseline, "train")
            assert inputs(result, "test") == inputs(baseline, "test")
        for left, right in (("all_sources", "nearest_color"),
                            ("all_sources", "farthest_color"),
                            ("nearest_color", "farthest_color")):
            assert any(a["output"] != b["output"] for a, b in
                       zip(results[left]["train"][:2], results[right]["train"][:2]))


def test_demo_query_streams_are_independent_and_deterministic(proto):
    before = random.getstate()
    small = episode(proto, demos=2, queries=1)
    more_demos = episode(proto, demos=6, queries=1)
    more_queries = episode(proto, demos=2, queries=4)
    both = episode(proto, demos=6, queries=4)
    assert random.getstate() == before
    assert small == episode(proto, demos=2, queries=1)
    assert len(both["train"]) == 6 and len(both["test"]) == 4
    assert more_demos["train"] == both["train"]
    assert small["train"] == more_demos["train"][:2] == more_queries["train"]
    assert small["test"] == more_demos["test"] == more_queries["test"][:1]
    assert more_queries["test"] == both["test"]


def test_distinct_pair_inputs_and_fresh_unaliased_returned_grids(proto):
    result = episode(proto, demos=6, queries=4)
    pairs = result["train"] + result["test"]
    assert len({json.dumps(pair["input"]) for pair in pairs}) == len(pairs)
    grids = [pair[key] for pair in pairs for key in ("input", "output")]
    assert len({id(grid) for grid in grids}) == len(grids)
    rows = [row for grid in grids for row in grid]
    assert len({id(row) for row in rows}) == len(rows)
    pristine = copy.deepcopy(result)
    result["train"][0]["input"][0][0] = 99
    assert episode(proto, demos=6, queries=4) == pristine
    assert result["train"][0]["output"] == pristine["train"][0]["output"]


def test_seed_and_split_counts_require_exact_integers_within_bounds(proto):
    for field, values in {
        "seed": (True, 1.0, "1", -1, 2**63),
        "demos": (True, 2.0, 1, 7),
        "queries": (True, 1.0, 0, 5),
    }.items():
        for value in values:
            args = {"seed": 0, "settings": {"mode": "all_sources"}, "demos": 2, "queries": 1}
            args[field] = value
            with pytest.raises((TypeError, ValueError)):
                proto.generate(**args)


def test_settings_are_exact_mode_only_and_not_mutated(proto):
    for settings in (None, [], {}, {"mode": "other"}, {"mode": True},
                     {"mode": "all_sources", "hint": 1}):
        with pytest.raises((TypeError, ValueError)):
            proto.generate(0, settings, demos=2, queries=1)
        with pytest.raises((TypeError, ValueError)):
            proto.program(settings)
    settings = {"mode": "nearest_color"}
    proto.generate(0, settings, demos=2, queries=1)
    proto.program(settings)
    assert settings == {"mode": "nearest_color"}


def test_public_turn_exact_helper_bytes_contain_only_selected_query(proto):
    result = episode(proto, queries=4)
    before = copy.deepcopy(result)
    raw = proto.public_turn_bytes(result, query_index=2)
    expected = {"train": result["train"], "test": [{"input": result["test"][2]["input"]}]}
    assert type(raw) is bytes
    assert raw == public_challenge_bytes(expected)
    public = json.loads(raw)
    assert set(public) == {"train", "test"}
    assert len(public["test"]) == 1 and set(public["test"][0]) == {"input"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert result == before


def test_public_hash_ignores_private_fields_but_changes_with_visible_pixels(proto, tmp_path):
    result = episode(proto, queries=4)
    raw = proto.public_turn_bytes(result)
    first = Path(proto.write_public(result, tmp_path))
    assert first == tmp_path / (hashlib.sha256(raw).hexdigest() + ".json")
    assert first.read_bytes() == raw
    private_changed = copy.deepcopy(result)
    private_changed["settings"] = {"mode": "private sentinel"}
    private_changed["program_solution"] = "PRIVATE PROGRAM SENTINEL"
    private_changed["test"][0]["output"][0][0] = 9
    private_changed["test"][1]["input"][0][0] = 9
    private_changed["train"][0]["metadata"] = "PRIVATE DEMO SENTINEL"
    assert proto.public_turn_bytes(private_changed) == raw
    assert Path(proto.write_public(private_changed, tmp_path)) == first
    for split, key in (("train", "output"), ("test", "input")):
        visible_changed = copy.deepcopy(result)
        grid = visible_changed[split][0][key]
        grid[0][0] = (grid[0][0] + 1) % 10
        changed_raw = proto.public_turn_bytes(visible_changed)
        changed_path = Path(proto.write_public(visible_changed, tmp_path))
        assert changed_raw != raw
        assert changed_path != first
        assert changed_path.name == hashlib.sha256(changed_raw).hexdigest() + ".json"
        assert changed_path.read_bytes() == changed_raw


def test_four_queries_include_meaningful_thirty_by_thirty_content(proto):
    result = episode(proto, queries=4)
    large = [pair for pair in result["test"]
             if len(pair["input"]) == 30 and all(len(row) == 30 for row in pair["input"])]
    assert large, "Four-query sampling must exercise the real 30x30 boundary"
    for pair in large:
        (pr, pc), cells = geometry(pair["input"])
        assert len({v for _, _, v, _ in cells}) >= 3
        assert max(r for r, _, _, _ in cells) - min(r for r, _, _, _ in cells) >= 15
        assert max(c for _, c, _, _ in cells) - min(c for _, c, _, _ in cells) >= 15
        additions = [(r, c) for r, row in enumerate(pair["output"]) for c, v in enumerate(row)
                     if v != pair["input"][r][c]]
        assert len(additions) >= 3
        assert max(abs(r - pr) + abs(c - pc) for r, c in additions) >= 15


def test_two_demos_refute_exact_and_integer_mean_distance_shortcuts(proto):
    """Regression: DSL integer division made 22/4 and 26/5 both equal five."""
    for seed in (0, 17):
        for mode in ("nearest_color", "farthest_color"):
            result = episode(proto, seed=seed, mode=mode, demos=2)
            for integer_mean in (False, True):
                rejected = False
                for pair in result["train"]:
                    _, cells = geometry(pair["input"])
                    scores = {}
                    for color in sorted({v for _, _, v, _ in cells}):
                        distances = [d for _, _, v, d in cells if v == color]
                        scores[color] = (sum(distances) // len(distances) if integer_mean
                                         else Fraction(sum(distances), len(distances)))
                    # Racket's strict comparison retains the lower color on ties.
                    winner = min(scores, key=lambda c: (scores[c] if mode == "nearest_color"
                                                        else -scores[c], c))
                    actual, _ = independent_label(pair["input"], mode)
                    rejected |= winner != actual
                assert rejected, (seed, mode, "integer mean" if integer_mean else "exact mean")


def test_extremal_ties_accept_one_color_and_reject_conflicting_colors(proto):
    original = episode(proto)["train"][0]["input"]
    (pr, pc), cells = geometry(original)
    lo, hi = min(cell[3] for cell in cells), max(cell[3] for cell in cells)

    def add_tie(distance, color):
        # Relocate an interior cell: retain every palette count, the pivot,
        # the original extrema, and blank antipodal destinations.
        source = next((r, c) for r, c, v, d in cells if v == color and lo < d < hi)
        target = next((r, c) for r, row in enumerate(original) for c, value in enumerate(row)
                      if value == 0 and abs(r - pr) + abs(c - pc) == distance
                      and 0 <= 2 * pr - r < len(original)
                      and 0 <= 2 * pc - c < len(original[0])
                      and original[2 * pr - r][2 * pc - c] == 0)
        changed = copy.deepcopy(original)
        changed[source[0]][source[1]] = 0
        changed[target[0]][target[1]] = color
        return changed

    for mode, distance in (("nearest_color", lo), ("farthest_color", hi)):
        chosen, _ = independent_label(original, mode)
        same_color = add_tie(distance, chosen)
        assert proto.selected_color(same_color, mode) == chosen
        assert proto.selected_color(same_color, "all_sources") is None
        other_color = next(v for _, _, v, d in cells if v != chosen and lo < d < hi)
        conflicting = add_tie(distance, other_color)
        for selection in proto.MODES:
            with pytest.raises(ValueError):
                proto.selected_color(conflicting, selection)


def test_malformed_geometry_typed_grids_and_invalid_public_query_indices(proto, tmp_path):
    result = episode(proto, queries=4)
    valid = result["train"][0]["input"]
    (pr, pc), cells = geometry(valid)
    typed = copy.deepcopy(valid)
    typed[0][0] = True
    duplicate = copy.deepcopy(valid)
    r, c = next((r, c) for r, row in enumerate(valid) for c, v in enumerate(row) if v == 0)
    duplicate[r][c] = 5
    occupied = copy.deepcopy(valid)
    r, c, color, _ = cells[0]
    occupied[2 * pr - r][2 * pc - c] = color
    for malformed in (typed, duplicate, occupied):
        for mode in proto.MODES:
            with pytest.raises(ValueError):
                proto.selected_color(malformed, mode)
    typed_public = copy.deepcopy(result)
    typed_public["train"][0]["input"] = typed
    with pytest.raises(ValueError):
        proto.public_turn_bytes(typed_public)
    for invalid in (True, 0.0, "0", -1, 4):
        with pytest.raises((TypeError, ValueError)):
            proto.public_turn_bytes(result, invalid)
        with pytest.raises((TypeError, ValueError)):
            proto.write_public(result, tmp_path, invalid)
    assert list(tmp_path.iterdir()) == []
