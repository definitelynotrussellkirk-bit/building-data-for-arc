"""Behavioral contract for the midpoint/connection parametric family."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from arcpuzzles import Catalog


ROOT = Path(__file__).resolve().parents[3]
HOME = ROOT / "generators/2fc4ca4ea6c4/workspace/parametric"
SETTINGS = [
    {"completion_mode": "midpoints"},
    {"completion_mode": "connect_aligned"},
]


def _load(name: str):
    path = HOME / f"{name}.py"
    assert path.is_file(), f"build {path.relative_to(ROOT)}"
    spec = importlib.util.spec_from_file_location(f"test_2fc_{name}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def adapter():
    return _load("adapter")


def _runs(grid):
    result = []
    for r, row in enumerate(grid):
        c = 0
        while c < len(row):
            if row[c] == 0:
                c += 1
                continue
            color = row[c]
            start = c
            while c < len(row) and row[c] == color:
                c += 1
            result.append((r, start, c - start, color))
    return result


def test_default_program_is_exact_canonical_and_alternative_is_distinct(adapter):
    record = Catalog(ROOT).get("2fc4ca4ea6c4")
    programs = {row["program_solution"] for row in record["variants"]}
    assert len(programs) == 1
    canonical = next(iter(programs))
    assert adapter.program(SETTINGS[0]) == canonical
    assert adapter.program(SETTINGS[1]) != canonical


def test_literal_midpoint_then_connection_semantics(adapter):
    grid = [[0] * 11 for _ in range(9)]
    for c in range(3, 8):
        grid[1][c] = 2
    for c in range(4, 7):
        grid[6][c] = 2
    grid[3][2] = 7
    for c in range(7, 10):
        grid[4][c] = 4

    stage_a = adapter.stage_a(grid)
    connected = adapter.stage_b(stage_a)
    assert stage_a == adapter.solve(grid, "midpoints")
    assert connected == adapter.solve(grid, "connect_aligned")
    assert {(r, c, v) for r, row in enumerate(stage_a) for c, v in enumerate(row) if v} == {
        (1, 5, 2), (6, 5, 2), (3, 2, 7), (4, 8, 4)
    }
    assert all(connected[r][5] == 2 for r in range(1, 7))
    assert adapter.stage_b(grid) != connected  # skipping A changes B's result


@pytest.mark.parametrize("demos", range(2, 7))
@pytest.mark.parametrize("queries", range(1, 5))
def test_counts_prefixes_reproducibility_and_matched_inputs(adapter, demos, queries):
    full = adapter.generate(17, SETTINGS[1], 6, 4)
    episode = adapter.generate(17, SETTINGS[1], demos, queries)
    assert episode["train"] == full["train"][:demos]
    assert episode["test"] == full["test"][:queries]
    assert episode == adapter.generate(17, SETTINGS[1], demos, queries)
    inputs = [pair["input"] for split in ("train", "test") for pair in episode[split]]
    assert len({json.dumps(grid) for grid in inputs}) == len(inputs)
    baseline = adapter.generate(17, SETTINGS[0], demos, queries)
    assert [p["input"] for s in ("train", "test") for p in baseline[s]] == inputs

    changed = copy.deepcopy(episode)
    changed["train"][0]["input"][0][0] = 9
    assert adapter.generate(17, SETTINGS[1], demos, queries) == episode


def test_two_demos_identify_both_settings_and_cover_singletons(adapter):
    for chosen, setting in enumerate(SETTINGS):
        episode = adapter.generate(29, setting, 2, 4)
        survivors = []
        for rival, candidate in enumerate(SETTINGS):
            labels = [adapter.solve(pair["input"], candidate["completion_mode"])
                      for pair in episode["train"]]
            if labels == [pair["output"] for pair in episode["train"]]:
                survivors.append(rival)
        assert survivors == [chosen]
        for pair in episode["train"]:
            lengths = [length for _, _, length, _ in _runs(pair["input"])]
            assert 1 in lengths and any(length >= 3 for length in lengths)


def test_every_alternative_pair_has_real_a_to_b_dependency(adapter):
    episode = adapter.generate(63, SETTINGS[1], 6, 4)
    for split in ("train", "test"):
        for pair in episode[split]:
            expected = pair["output"]
            assert expected == adapter.stage_b(adapter.stage_a(pair["input"]))
            assert expected != adapter.stage_b(pair["input"])
            assert expected != adapter.stage_a(pair["input"])


def test_large_query_is_substantive_30x30_boundary_stress(adapter):
    episode = adapter.generate(0, SETTINGS[1], 2, 4)
    pair = next(pair for pair in episode["test"] if len(pair["input"]) == len(pair["input"][0]) == 30)
    source, output = pair["input"], pair["output"]
    occupied = [(r, c) for r, row in enumerate(source) for c, v in enumerate(row) if v]
    assert len(occupied) >= 60
    assert any(r == 0 for r, _ in occupied) and any(r == 29 for r, _ in occupied)
    assert any(c == 0 for _, c in occupied) and any(c == 29 for _, c in occupied)
    assert sum(a != b for ar, br in zip(source, output) for a, b in zip(ar, br)) >= 40
    assert all(any(source[r][c] for r in range(r0, r0 + 15) for c in range(c0, c0 + 15))
               for r0 in (0, 15) for c0 in (0, 15))


def test_public_turn_masks_private_fields_and_future_queries(adapter):
    episode = adapter.generate(2, SETTINGS[1], 3, 4)
    visible = adapter.public_turn(episode, 0)
    assert visible == {"train": episode["train"], "test": [{"input": episode["test"][0]["input"]}]}
    changed = copy.deepcopy(episode)
    changed["seed"] = -1
    changed["settings"] = {"private": True}
    changed["program_solution"] = "private"
    for pair in changed["test"]:
        pair["output"] = [[9]]
    assert adapter.public_turn(changed, 0) == visible


@pytest.mark.parametrize("settings", [None, {}, {"completion_mode": "bad"},
    {"completion_mode": True}, {"completion_mode": "midpoints", "extra": 1}])
def test_bad_settings_rejected(adapter, settings):
    with pytest.raises(ValueError):
        adapter.program(settings)
    with pytest.raises(ValueError):
        adapter.generate(0, settings, 2, 1)


@pytest.mark.parametrize("seed,demos,queries", [
    (True, 2, 1), (-1, 2, 1), (2**63, 2, 1), (1.0, 2, 1),
    (0, True, 1), (0, 1, 1), (0, 7, 1), (0, 2.0, 1),
    (0, 2, True), (0, 2, 0), (0, 2, 5), (0, 2, 1.0),
])
def test_bad_counts_and_seeds_rejected(adapter, seed, demos, queries):
    with pytest.raises(ValueError):
        adapter.generate(seed, SETTINGS[0], demos, queries)


def test_bounded_audit_replays_teaching_and_causality(tmp_path):
    audit = _load("audit")
    report = audit.run_audit(tmp_path / "audit.json", seeds=(0, 17, 29, 63))
    assert report["status"] == "pass"
    assert report["settings_checked"] == 8
    assert report["minimum_demo_survivors"] == 8
    assert report["alternative_pairs_checked"] == 40
    assert report["differs_from_skip_a"] == 40
    assert report["differs_from_skip_b"] == 40
    assert report["singleton_pairs"] == 40
    assert report["shortcut_rivals_checked"] == 8
    assert report["shortcut_rivals_refuted_by_minimum_demos"] == 8
    assert report["shortcut_rivals_disagree_on_queries"] == 8


def _connect_same_color_ignoring_blockers(midpoints):
    height, width = len(midpoints), len(midpoints[0])
    out = [row[:] for row in midpoints]
    for column in range(width):
        for color in {midpoints[row][column] for row in range(height)} - {0}:
            hits = [row for row in range(height) if midpoints[row][column] == color]
            if len(hits) == 2:
                for row in range(hits[0], hits[1] + 1):
                    out[row][column] = color
    return out


def _connect_same_color_with_two_or_more(midpoints):
    height, width = len(midpoints), len(midpoints[0])
    out = [row[:] for row in midpoints]
    for column in range(width):
        for color in {midpoints[row][column] for row in range(height)} - {0}:
            hits = [row for row in range(height) if midpoints[row][column] == color]
            if len(hits) >= 2:
                for row in range(min(hits), max(hits) + 1):
                    out[row][column] = color
    return out


def test_two_demos_teach_clear_path_and_exactly_two_guards(adapter):
    episode = adapter.generate(29, SETTINGS[1], 2, 4)
    expected = [pair["output"] for pair in episode["train"]]
    ignoring_blockers = [
        _connect_same_color_ignoring_blockers(adapter.stage_a(pair["input"]))
        for pair in episode["train"]
    ]
    accepting_triples = [
        _connect_same_color_with_two_or_more(adapter.stage_a(pair["input"]))
        for pair in episode["train"]
    ]
    assert ignoring_blockers != expected
    assert accepting_triples != expected
