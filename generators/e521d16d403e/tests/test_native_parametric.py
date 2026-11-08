"""Focused native contract checks; fixture answers are hand-drawn, never mirrored."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import types

import pytest

from arcpuzzles.parametric_promotion import _public
from arcpuzzles.parametric_worker import _real_evaluator
from reviewer_support import canonical_path, find_root


ROOT = find_root(__file__)
HOME = ROOT / "generators/e521d16d403e/workspace/parametric"
RULES = ("occupied_cells", "bbox_area", "occupied_anchor_partner")


def _load(name):
    path = HOME / (name + ".py")
    assert path.is_file(), f"native parametric {name}.py adapter is required"
    spec = importlib.util.spec_from_file_location("_test_e521d16d403e_" + name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def native():
    return _load("native")


@pytest.fixture(scope="module")
def racket():
    apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
    assert identity["backend"] == "racket" and identity["protected"] is True
    try:
        yield apply
    finally:
        bridge.close()


# Solid 2x4 (8 occupied / area 8) beats the cross (5 occupied / area 9).
# Each has a unique same-color asymmetric partner. The cross partner comes
# first in scan order, so "first asymmetric object" is also distinguished.
WITNESS = [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,3,3,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,3,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,2,2,2,2,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,2,2,2,2,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,3,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,3,3,3,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,3,0,0,0,2,2,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,2,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
]
EXPECTED = {
    "occupied_cells": [[2,2,2,2], [2,2,2,2]],
    "bbox_area": [[0,3,0], [3,3,3], [0,3,0]],
    "occupied_anchor_partner": [[2,2,0], [0,2,2]],
}


def _key(grid):
    return json.dumps(grid, separators=(",", ":"))


def _components(grid):
    """Structural grammar checks only; does not produce reference labels."""
    height, width = len(grid), len(grid[0])
    seen, result = set(), []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if not color or (row, col) in seen:
                continue
            todo, cells = [(row, col)], set()
            seen.add((row, col))
            while todo:
                rr, cc = todo.pop()
                cells.add((rr, cc))
                for nr, nc in ((rr-1,cc), (rr+1,cc), (rr,cc-1), (rr,cc+1)):
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr,nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr,nc)); todo.append((nr,nc))
            r0, r1 = min(r for r,c in cells), max(r for r,c in cells)
            c0, c1 = min(c for r,c in cells), max(c for r,c in cells)
            crop = [line[c0:c1+1] for line in grid[r0:r1+1]]
            result.append({"color": color, "size": len(cells), "bbox": (r0,c0,r1,c1),
                           "area": (r1-r0+1)*(c1-c0+1),
                           "eligible": c1 > c0 and all(line == line[::-1] for line in crop)})
    return result


def test_adapter_exists_and_exports_native_functionality():
    adapter = _load("adapter")
    for name in ("program", "generate"):
        assert callable(getattr(adapter, name, None)), f"adapter must expose {name}"


def test_settings_and_canonical_program_bytes(native):
    assert type(native.SETTINGS) is tuple
    assert native.SETTINGS == tuple({"selection_rule": rule} for rule in RULES)
    prototype = _load("prototype")
    canonical = {row["program_solution"]
                 for line in canonical_path(ROOT).read_text().splitlines() if line.strip()
                 if (row := json.loads(line)).get("task_id") == "e521d16d403e"}
    assert len(canonical) == 1
    source = canonical.pop()
    assert native.program(native.SETTINGS[0]) == source
    assert hashlib.sha256(source.encode()).hexdigest() == prototype.CANONICAL_SOURCE_SHA256
    assert native.program(native.SETTINGS[1]) == prototype.materialize_rule("bbox_area", root=ROOT)
    assert len({native.program(setting) for setting in native.SETTINGS}) == 3


def test_three_rules_have_literal_distinguishing_answers(native, racket):
    for rule, expected in EXPECTED.items():
        assert racket(native.program({"selection_rule": rule}), WITNESS) == expected


def test_partner_depends_on_selected_occupied_anchor_color(native, racket):
    source = native.program({"selection_rule": "occupied_anchor_partner"})
    # Exchange only partner colors. Anchors, rankings, shapes and positions stay
    # fixed; following the occupied anchor must now return the cross partner L.
    changed = deepcopy(WITNESS)
    for r, c in ((1,1), (1,2), (2,1)):
        changed[r][c] = 2
    for r, c in ((9,14), (9,15), (10,15), (10,16)):
        changed[r][c] = 3
    assert racket(source, changed) == [[2,2], [2,0]]
    assert racket(native.program(native.SETTINGS[0]), changed) == EXPECTED["occupied_cells"]
    assert racket(native.program(native.SETTINGS[1]), changed) == EXPECTED["bbox_area"]


def test_sampler_determinism_bounds_and_scene_grammar(native):
    baseline = native.sample_inputs(17, 3, 4)
    assert baseline == native.sample_inputs(17, 3, 4)
    assert baseline != native.sample_inputs(18, 3, 4)
    assert set(baseline) == {"train", "test"}
    for demos, queries, seed in ((2,1,0), (6,4,2**63-1), (4,2,23)):
        sampled = native.sample_inputs(seed, demos, queries)
        assert len(sampled["train"]) == demos and len(sampled["test"]) == queries
        grids = sampled["train"] + sampled["test"]
        assert len({_key(grid) for grid in grids}) == len(grids)
        for grid in grids:
            assert type(grid) is list and 1 <= len(grid) <= 30
            assert 1 <= len(grid[0]) <= 30
            assert all(type(row) is list and len(row) == len(grid[0]) for row in grid)
            assert all(type(cell) is int and 0 <= cell <= 9 for row in grid for cell in row)
            components = _components(grid)
            anchors = [obj for obj in components if obj["eligible"]]
            assert len(anchors) >= 2
            occupied = max(anchors, key=lambda obj: obj["size"])
            area = max(anchors, key=lambda obj: obj["area"])
            assert occupied != area
            assert sum(obj["size"] == occupied["size"] for obj in anchors) == 1
            assert sum(obj["area"] == area["area"] for obj in anchors) == 1
            for anchor in (occupied, area):
                partners = [obj for obj in components if obj is not anchor and obj["color"] == anchor["color"]]
                assert len(partners) == 1 and not partners[0]["eligible"]


@pytest.mark.parametrize("seed,demos,queries", [
    (True,3,4), (-1,3,4), (2**63,3,4), (1.0,3,4),
    (0,True,4), (0,1,4), (0,7,4), (0,3,True), (0,3,0), (0,3,5),
])
def test_invalid_seed_or_counts_rejected(native, seed, demos, queries):
    with pytest.raises((ValueError, TypeError)):
        native.sample_inputs(seed, demos, queries)
    with pytest.raises((ValueError, TypeError)):
        native.generate(seed, native.SETTINGS[0], demos, queries)


@pytest.mark.parametrize("setting", [None, {}, {"selection_rule": True},
    {"selection_rule": "occupied_cells", "extra": 1}, {"selection_rule": "largest"}])
def test_invalid_settings_rejected(native, setting):
    with pytest.raises((ValueError, TypeError)):
        native.program(setting)
    with pytest.raises((ValueError, TypeError)):
        native.generate(0, setting, 2, 1)


def test_four_queries_are_novel_and_include_substantive_30_by_30(native):
    sampled = native.sample_inputs(29, 3, 4)
    train = {_key(grid) for grid in sampled["train"]}
    queries = sampled["test"]
    assert len({_key(grid) for grid in queries}) == 4
    assert all(_key(grid) not in train for grid in queries)
    assert len({(len(grid),len(grid[0])) for grid in queries}) >= 3
    large = [grid for grid in queries if len(grid) == len(grid[0]) == 30]
    assert large, "four-query schedule must include an exact 30x30 scene"
    for grid in large:
        occupied = [(r,c) for r,row in enumerate(grid) for c,value in enumerate(row) if value]
        assert len(occupied) >= 60
        assert {(r//15,c//15) for r,c in occupied} == {(0,0),(0,1),(1,0),(1,1)}
        rows, cols = {r for r,c in occupied}, {c for r,c in occupied}
        assert max(rows)-min(rows)+1 >= 25 and max(cols)-min(cols)+1 >= 25
        assert sum((0 in rows,29 in rows,0 in cols,29 in cols)) >= 2


@pytest.mark.parametrize("seed", [0, 17])
def test_teaching_reverses_anchor_aspect_in_demos_and_queries(native, seed):
    """Occupied count must not be confounded with choosing the wider object."""
    sampled = native.sample_inputs(seed, 2, 4)
    orientations = {"train": [], "test": []}
    for split in ("train", "test"):
        for grid in sampled[split]:
            eligible = [obj for obj in _components(grid) if obj["eligible"]]
            occupied = max(eligible, key=lambda obj: obj["size"])
            r0, c0, r1, c1 = occupied["bbox"]
            height, width = r1-r0+1, c1-c0+1
            orientations[split].append((height > width) - (height < width))
    assert set(orientations["train"]) == {-1, 1}, (
        "the mandatory first two demos must teach both tall and wide count winners")
    assert 1 in orientations["test"], (
        "four-query support must include a tall count winner")


def test_generate_matches_inputs_across_settings_and_real_racket_labels(native, racket):
    sampled = native.sample_inputs(31, 2, 4)
    episodes = [native.generate(31, setting, 2, 4) for setting in native.SETTINGS]
    for setting, episode in zip(native.SETTINGS, episodes):
        assert episode["program_solution"] == native.program(setting)
        for split in ("train", "test"):
            assert [pair["input"] for pair in episode[split]] == sampled[split]
            for pair in episode[split]:
                assert pair["output"] == racket(episode["program_solution"], pair["input"])
    # Every scene teaches all three settings by its labels.
    for split in ("train", "test"):
        for index in range(len(sampled[split])):
            assert len({_key(ep[split][index]["output"]) for ep in episodes}) == 3
    assert native.generate(31, native.SETTINGS[0], 2, 4) == episodes[0]


def test_single_query_preserves_first_turn_and_public_projection(native):
    setting = native.SETTINGS[2]
    one = native.generate(37, setting, 3, 1)
    four = native.generate(37, setting, 3, 4)
    assert one["train"] == four["train"]
    assert one["test"] == four["test"][:1]
    assert native.public_turn(one) == native.public_turn(four)
    assert native.public_turn(four) == {"train": _public(four)["train"],
                                         "test": _public(four)["test"][:1]}
    assert native.public_turn(four, query_index=2) == {
        "train": _public(four)["train"], "test": _public(four)["test"][2:3]}
    assert native.sample_inputs(37,3,1) == {
        "train": native.sample_inputs(37,3,4)["train"],
        "test": native.sample_inputs(37,3,4)["test"][:1],
    }
    public = _public(four)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input","output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    changed = deepcopy(four)
    changed.update(seed=999, settings={"selection_rule": "hidden"}, program_solution="hidden")
    for pair in changed["test"]:
        pair["output"] = [[9]]
    assert _public(changed) == public
    assert native.public_turn(changed) == native.public_turn(four)
    assert not any(word in _key(public) for word in ("selection_rule", "program", "seed", "settings"))


def test_adapter_ignores_unrelated_bare_prototype_module(native, monkeypatch):
    poisoned = types.ModuleType("prototype")
    def fail(*args, **kwargs):
        raise AssertionError("bare prototype import was used")
    poisoned.materialize_rule = poisoned.canonical_source = fail
    monkeypatch.setitem(sys.modules, "prototype", poisoned)
    isolated_native = _load("native")
    assert isolated_native.program(native.SETTINGS[0]) == native.program(native.SETTINGS[0])
    adapter = _load("adapter")
    assert adapter.program(native.SETTINGS[0]) == native.program(native.SETTINGS[0])
