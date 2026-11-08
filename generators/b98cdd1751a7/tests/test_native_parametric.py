"""Focused contract tests for the native b98cdd1751a7 rule family."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import types

import pytest

from arcpuzzles.parametric_promotion import _public
from arcpuzzles.parametric_worker import _real_evaluator
from reviewer_support import canonical_path, find_root


TASK_ID = "b98cdd1751a7"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
RULES = ("left_right", "match_top_left_color")


def _load(name):
    path = HOME / f"{name}.py"
    assert path.is_file(), f"native parametric {name}.py is required"
    spec = importlib.util.spec_from_file_location(f"_test_{TASK_ID}_{name}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def native():
    return _load("native")


def _selected_runtime_root():
    roots = {
        Path(importlib.import_module(name).__file__).resolve().parents[1]
        for name in ("arc_repl.racket_bridge", "puzzle_generators.rule_wrap")
    }
    assert len(roots) == 1
    runtime = roots.pop()
    assert runtime.is_relative_to(ROOT.resolve())
    return runtime


@pytest.fixture(scope="module")
def racket():
    apply, identity, bridge = _real_evaluator(_selected_runtime_root())
    assert identity["backend"] == "racket" and identity["protected"] is True
    try:
        yield apply
    finally:
        bridge.close()


def _canonical_source():
    rows = []
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            rows.append(row)
    assert len(rows) == 1
    return rows[0]["program_solution"]


def _key(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            todo = [(row, col)]
            seen.add((row, col))
            cells = []
            while todo:
                rr, cc = todo.pop()
                cells.append((rr, cc))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        nr, nc = rr + dr, cc + dc
                        if (dr or dc) and 0 <= nr < height and 0 <= nc < width \
                                and (nr, nc) not in seen and grid[nr][nc] == color:
                            seen.add((nr, nc))
                            todo.append((nr, nc))
            r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
            c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
            result.append({"color": color, "cells": tuple(sorted(cells)),
                           "bbox": (r0, c0, r1, c1), "row0": r0, "col0": c0})
    return result


def _groups(grid):
    components = sorted(_components(grid), key=lambda obj: (obj["row0"], obj["col0"]))
    midpoint = (components[0]["row0"] + components[-1]["row0"]) / 2.0
    top = sorted((obj for obj in components if obj["row0"] < midpoint), key=lambda obj: obj["col0"])
    bottom = sorted((obj for obj in components if obj["row0"] >= midpoint), key=lambda obj: obj["col0"])
    return top, bottom


WITNESS = [[0] * 16 for _ in range(12)]
for r, c, color in (
    (1, 1, 8), (1, 2, 8), (2, 1, 8),
    (1, 10, 2), (2, 10, 2), (2, 11, 2), (2, 12, 2),
    (8, 1, 2), (9, 1, 2), (10, 1, 2), (10, 2, 2),
    (8, 11, 8), (8, 12, 8), (9, 12, 8),
):
    WITNESS[r][c] = color

CANONICAL_EXPECTED = [
    [8, 8, 0, 0, 2, 0, 0],
    [8, 0, 0, 0, 2, 2, 2],
    [0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0],
    [2, 0, 0, 0, 8, 8, 0],
    [2, 0, 0, 0, 0, 8, 0],
    [2, 2, 0, 0, 0, 0, 0],
]
MATCH_EXPECTED = [
    [8, 8, 0, 0, 2, 0, 0],
    [8, 0, 0, 0, 2, 2, 2],
    [0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0],
    [8, 8, 0, 0, 2, 0, 0],
    [0, 8, 0, 0, 2, 0, 0],
    [0, 0, 0, 0, 2, 2, 0],
]


def test_adapter_exists_and_exports_native_contract():
    adapter = _load("adapter")
    assert callable(adapter.program)
    assert callable(adapter.generate)


def test_settings_and_default_program_are_exact(native):
    assert native.SETTINGS == tuple({"bottom_order": value} for value in RULES)
    assert native.program(native.SETTINGS[0]) == _canonical_source()
    assert native.program(native.SETTINGS[1]) != _canonical_source()
    assert len({native.program(setting) for setting in native.SETTINGS}) == 2


def test_literal_witness_distinguishes_bottom_order_rules(native, racket):
    assert racket(native.program(native.SETTINGS[0]), WITNESS) == CANONICAL_EXPECTED
    assert racket(native.program(native.SETTINGS[1]), WITNESS) == MATCH_EXPECTED


@pytest.mark.parametrize("setting", [
    None,
    {},
    {"bottom_order": True},
    {"bottom_order": "left_right", "extra": 1},
    {"bottom_order": "color"},
])
def test_invalid_settings_fail_closed(native, setting):
    with pytest.raises((TypeError, ValueError)):
        native.program(setting)
    with pytest.raises((TypeError, ValueError)):
        native.generate(0, setting, 2, 1)


@pytest.mark.parametrize("seed,demos,queries", [
    (True, 3, 4), (-1, 3, 4), (2**63, 3, 4), (1.0, 3, 4),
    (0, True, 4), (0, 1, 4), (0, 7, 4),
    (0, 3, True), (0, 3, 0), (0, 3, 5),
])
def test_invalid_seed_or_counts_fail_closed(native, seed, demos, queries):
    with pytest.raises((TypeError, ValueError)):
        native.sample_inputs(seed, demos, queries)
    with pytest.raises((TypeError, ValueError)):
        native.generate(seed, native.SETTINGS[0], demos, queries)


def test_sampler_is_deterministic_prefix_stable_and_structurally_valid(native):
    baseline = native.sample_inputs(17, 3, 4)
    assert baseline == native.sample_inputs(17, 3, 4)
    assert baseline != native.sample_inputs(18, 3, 4)
    assert native.sample_inputs(17, 2, 1) == {
        "train": baseline["train"][:2],
        "test": baseline["test"][:1],
    }
    assert native.sample_inputs(17, 6, 4)["train"][:3] == baseline["train"]
    grids = baseline["train"] + baseline["test"]
    assert len({_key(grid) for grid in grids}) == len(grids)
    for grid in grids:
        assert type(grid) is list and 1 <= len(grid) <= 30
        assert type(grid[0]) is list and 1 <= len(grid[0]) <= 30
        assert all(type(row) is list and len(row) == len(grid[0]) for row in grid)
        assert all(type(cell) is int and 0 <= cell <= 9 for row in grid for cell in row)
        components = _components(grid)
        assert len(components) == 4
        assert all((obj["bbox"][2] - obj["bbox"][0] + 1) <= 3 for obj in components)
        assert all((obj["bbox"][3] - obj["bbox"][1] + 1) <= 3 for obj in components)
        top, bottom = _groups(grid)
        assert len(top) == len(bottom) == 2
        assert top[0]["color"] != top[1]["color"]
        assert sorted(obj["color"] for obj in top) == sorted(obj["color"] for obj in bottom)


@pytest.mark.parametrize("seed", [0, 17, 91])
def test_first_two_demos_defeat_spatial_swap_and_numeric_color_shortcuts(native, seed):
    first, second = native.sample_inputs(seed, 2, 1)["train"]
    top0, bottom0 = _groups(first)
    top1, bottom1 = _groups(second)
    assert bottom0[0]["color"] == top0[0]["color"]
    assert bottom1[1]["color"] == top1[0]["color"]
    assert top0[0]["color"] > top0[1]["color"]
    assert top1[0]["color"] < top1[1]["color"]


@pytest.mark.parametrize("seed", [0, 17])
def test_mandatory_demos_identify_each_declared_setting(native, racket, seed):
    inputs = native.sample_inputs(seed, 2, 1)["train"]
    outputs = {
        rule: [racket(native.program({"bottom_order": rule}), grid) for grid in inputs]
        for rule in RULES
    }
    assert outputs["left_right"][0] == outputs["match_top_left_color"][0]
    assert outputs["left_right"][1] != outputs["match_top_left_color"][1]
    assert len({_key(outputs[rule]) for rule in RULES}) == 2


def test_generate_uses_shared_inputs_and_real_racket_labels(native, racket):
    sampled = native.sample_inputs(31, 2, 4)
    episodes = [native.generate(31, setting, 2, 4) for setting in native.SETTINGS]
    for setting, episode in zip(native.SETTINGS, episodes):
        assert episode["program_solution"] == native.program(setting)
        for split in ("train", "test"):
            assert [pair["input"] for pair in episode[split]] == sampled[split]
            for pair in episode[split]:
                assert pair["output"] == racket(episode["program_solution"], pair["input"])
    assert native.generate(31, native.SETTINGS[0], 2, 4) == episodes[0]


def test_four_queries_include_both_partner_sides_and_substantive_30x30(native):
    queries = native.sample_inputs(29, 3, 4)["test"]
    sides = []
    for grid in queries:
        top, bottom = _groups(grid)
        sides.append(0 if bottom[0]["color"] == top[0]["color"] else 1)
    assert set(sides) == {0, 1}
    assert len({(len(grid), len(grid[0])) for grid in queries}) == 4
    large = [grid for grid in queries if len(grid) == len(grid[0]) == 30]
    assert len(large) == 1
    occupied = [(r, c) for r, row in enumerate(large[0]) for c, value in enumerate(row) if value]
    assert len(occupied) >= 20
    assert {(r // 15, c // 15) for r, c in occupied} == {(0, 0), (0, 1), (1, 0), (1, 1)}
    rows, cols = {r for r, _ in occupied}, {c for _, c in occupied}
    assert {0, 29} <= rows and {0, 29} <= cols


def test_public_projection_masks_private_fields_and_future_queries(native):
    one = native.generate(37, native.SETTINGS[1], 3, 1)
    four = native.generate(37, native.SETTINGS[1], 3, 4)
    assert one["train"] == four["train"]
    assert one["test"] == four["test"][:1]
    assert native.public_turn(one) == native.public_turn(four)
    assert native.public_turn(four, 2) == {
        "train": _public(four)["train"],
        "test": _public(four)["test"][2:3],
    }
    visible = _public(four)
    assert set(visible) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in visible["train"])
    assert all(set(pair) == {"input"} for pair in visible["test"])
    changed = deepcopy(four)
    changed.update(seed=999, settings={"bottom_order": "hidden"}, program_solution="hidden")
    for pair in changed["test"]:
        pair["output"] = [[9]]
    assert _public(changed) == visible
    assert native.public_turn(changed) == native.public_turn(four)
    assert not any(word in _key(visible) for word in ("bottom_order", "program", "seed", "settings"))


def test_adapter_loads_exact_adjacent_native_module(native, monkeypatch):
    poisoned = types.ModuleType("native")
    poisoned.program = poisoned.generate = lambda *args, **kwargs: (_ for _ in ()).throw(
        AssertionError("bare native import was used"))
    monkeypatch.setitem(sys.modules, "native", poisoned)
    adapter = _load("adapter")
    assert adapter.program(native.SETTINGS[0]) == native.program(native.SETTINGS[0])


def test_self_audit_rejects_demo_fit_query_disagreement(native, racket):
    audit = _load("self_audit")
    sampled = native.sample_inputs(5, 2, 1)
    ambiguous = {"train": sampled["train"][:1], "test": sampled["train"][1:2]}
    selected = native.program({"bottom_order": "match_top_left_color"})
    findings = audit.audit_episode(
        ambiguous,
        selected,
        {"left_right": native.program({"bottom_order": "left_right"})},
        racket,
    )
    assert len(findings) == 1
    assert findings[0]["rival"] == "left_right"
    assert findings[0]["query_index"] == 0


def test_self_audit_accepts_mandatory_teaching_set(native, racket):
    audit = _load("self_audit")
    sampled = native.sample_inputs(5, 2, 4)
    for setting in native.SETTINGS:
        selected = native.program(setting)
        rivals = audit.rival_programs()
        rivals.update({
            name: native.program(other)
            for name, other in (("left_right", native.SETTINGS[0]),
                                ("match_top_left_color", native.SETTINGS[1]))
            if native.program(other) != selected
        })
        assert audit.audit_episode(sampled, selected, rivals, racket) == []
