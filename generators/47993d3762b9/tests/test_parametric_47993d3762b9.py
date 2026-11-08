"""Focused prototype API checks; protected Racket qualification is separate."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest


HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
MODES = ("all_corners", "largest_bbox_frame", "smallest_bbox_frame")


def _load(name):
    path = HOME / "workspace" / "parametric" / (name + ".py")
    assert path.is_file(), f"Required parametric implementation is missing: {path}"
    module_name = "_bbox_parametric_test_" + name
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def adapter():
    return _load("adapter")


@pytest.fixture(scope="module")
def prototype():
    return _load("prototype")


def _boxes(grid):
    colors = {cell for row in grid for cell in row} - {0}
    result = {}
    for color in colors:
        cells = [(r, c) for r, row in enumerate(grid) for c, cell in enumerate(row) if cell == color]
        result[color] = (min(r for r, c in cells), min(c for r, c in cells),
                         max(r for r, c in cells), max(c for r, c in cells))
    return result


def _oracle(grid, mode):
    boxes = _boxes(grid)
    output = [[0 for _ in row] for row in grid]
    if mode == "all_corners":
        chosen = boxes
    else:
        areas = {color: (b - t + 1) * (r - l + 1) for color, (t, l, b, r) in boxes.items()}
        assert len(set(areas.values())) == len(areas), "Sampled selection must avoid tied bbox areas"
        target = (max if mode == "largest_bbox_frame" else min)(areas, key=areas.get)
        chosen = {target: boxes[target]}
    for color, (top, left, bottom, right) in chosen.items():
        cells = {(top, left), (top, right), (bottom, left), (bottom, right)}
        if mode != "all_corners":
            cells |= {(r, c) for r in range(top, bottom + 1) for c in range(left, right + 1)
                      if r in (top, bottom) or c in (left, right)}
        for r, c in cells:
            output[r][c] = color
    return output


def _inputs(episode, split):
    return [pair["input"] for pair in episode[split]]


def test_default_is_exact_same_tree_canonical_program(adapter):
    ledger = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    programs = {row["program_solution"] for line in ledger.read_text().splitlines()
                if (row := json.loads(line)).get("task_id") == "47993d3762b9"}
    assert len(programs) == 1
    assert adapter.program({"mode": "all_corners"}) == next(iter(programs))
    assert len({adapter.program({"mode": mode}) for mode in MODES}) == 3


def test_independent_counts_novel_inputs_and_literal_grid_labels(adapter):
    for mode in MODES:
        settings = {"mode": mode}
        for demos in range(2, 7):
            for queries in range(1, 5):
                episode = adapter.generate(17, settings, demos, queries)
                assert len(episode["train"]) == demos
                assert len(episode["test"]) == queries
                assert episode["program_solution"] == adapter.program(settings)
                pairs = episode["train"] + episode["test"]
                assert len({json.dumps(pair["input"]) for pair in pairs}) == demos + queries
                for pair in pairs:
                    for grid in (pair["input"], pair["output"]):
                        assert type(grid) is list and 1 <= len(grid) <= 30
                        assert type(grid[0]) is list and 1 <= len(grid[0]) <= 30
                        assert all(type(row) is list and len(row) == len(grid[0]) for row in grid)
                        assert all(type(cell) is int and 0 <= cell <= 9 for row in grid for cell in row)
                    assert pair["output"] == _oracle(pair["input"], mode)
        assert settings == {"mode": mode}


def test_matched_inputs_determinism_prefixes_and_fresh_returns(adapter):
    episodes = [adapter.generate(0, {"mode": mode}, 3, 4) for mode in MODES]
    for split in ("train", "test"):
        assert all(_inputs(episode, split) == _inputs(episodes[0], split) for episode in episodes)
    for mode, episode in zip(MODES, episodes):
        settings = {"mode": mode}
        saved = copy.deepcopy(episode)
        assert adapter.generate(0, settings, 3, 4) == saved
        assert _inputs(adapter.generate(0, settings, 2, 4), "test") == _inputs(saved, "test")
        assert _inputs(adapter.generate(0, settings, 6, 4), "test") == _inputs(saved, "test")
        assert adapter.generate(0, settings, 3, 1)["test"] == saved["test"][:1]
        episode["train"][0]["input"][0][0] = 99
        assert adapter.generate(0, settings, 3, 4) == saved


def test_two_demos_teach_all_modes_and_one_query_is_substantive_30x30(adapter):
    for mode in MODES:
        episode = adapter.generate(17, {"mode": mode}, 2, 4)
        for rival in set(MODES) - {mode}:
            assert any(_oracle(pair["input"], rival) != pair["output"] for pair in episode["train"])
        stress = [pair["input"] for pair in episode["test"]
                  if len(pair["input"]) == len(pair["input"][0]) == 30]
        assert len(stress) == 1
        grid = stress[0]
        assert len(grid) == 30 and all(len(row) == 30 for row in grid)
        cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
        assert len(cells) / 900 > 0.10
        assert min(r for r, c in cells) == min(c for r, c in cells) == 0
        assert max(r for r, c in cells) == max(c for r, c in cells) == 29
        assert len(_boxes(grid)) >= 2, "Selection needs distractor colors"


def test_query_size_does_not_always_identify_the_final_turn(adapter):
    positions = set()
    for seed in range(8):
        episode = adapter.generate(seed, {"mode": "all_corners"}, 3, 4)
        shapes = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
        assert set(shapes) == {(9, 11), (17, 24), (24, 26), (30, 30)}
        positions.add(shapes.index((30, 30)))
    assert len(positions) >= 3, "A fixed stress size must not label the final query turn"


def test_malformed_settings_and_request_boundaries_reject(adapter):
    for settings in (None, {}, {"mode": "typo"}, {"mode": True}, {"mode": "all_corners", "extra": 1}):
        with pytest.raises((ValueError, TypeError)):
            adapter.program(settings)
        with pytest.raises((ValueError, TypeError)):
            adapter.generate(0, settings, 3, 4)
    settings = {"mode": "all_corners"}
    for seed in (-1, 2**63, True, 0.0, "0"):
        with pytest.raises((ValueError, TypeError)):
            adapter.generate(seed, settings, 3, 4)
    for demos, queries in ((1, 4), (7, 4), (True, 4), (3.0, 4), (3, 0), (3, 5), (3, True), (3, 4.0)):
        with pytest.raises((ValueError, TypeError)):
            adapter.generate(0, settings, demos, queries)
    assert len(adapter.generate(2**63 - 1, settings, 2, 1)["test"]) == 1


def test_first_public_projection_ignores_private_and_future_data(adapter, prototype):
    episode = adapter.generate(17, {"mode": "largest_bbox_frame"}, 3, 4)
    visible = prototype.public_challenge(episode, query_index=0)
    identity = prototype.public_id(episode, query_index=0)
    assert set(visible) == {"train", "test"}
    assert visible["train"] == episode["train"]
    assert visible["test"] == [{"input": episode["test"][0]["input"]}]
    assert len(identity) == 64 and all(ch in "0123456789abcdef" for ch in identity)
    changed = copy.deepcopy(episode)
    changed.update(settings={"mode": "smallest_bbox_frame"}, seed=999, program_solution="private-only", private_note="hidden")
    for pair in changed["test"]:
        pair["output"] = [[9]]
    for pair in changed["test"][1:]:
        pair["input"] = [[8]]
    assert prototype.public_challenge(changed, query_index=0) == visible
    assert prototype.public_id(changed, query_index=0) == identity
    changed["train"][0]["output"][0][0] = (changed["train"][0]["output"][0][0] + 1) % 10
    assert prototype.public_challenge(changed, query_index=0) != visible
    assert prototype.public_id(changed, query_index=0) != identity
    assert episode == adapter.generate(17, {"mode": "largest_bbox_frame"}, 3, 4)
