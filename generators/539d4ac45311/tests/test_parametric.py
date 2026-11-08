"""Behavioral contract for the native endpoint-connection family."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from arcpuzzles import Catalog


ROOT = Path(__file__).resolve().parents[3]
HOME = ROOT / "generators/539d4ac45311/workspace/parametric"
ADAPTER = HOME / "adapter.py"
SETTINGS = [
    {"connection_mode": "horizontal"},
    {"connection_mode": "vertical"},
    {"connection_mode": "cascade"},
]


def _load(name: str):
    path = HOME / f"{name}.py"
    assert path.is_file(), f"build {path.relative_to(ROOT)}"
    spec = importlib.util.spec_from_file_location(f"test_539_{name}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def adapter():
    return _load("adapter")


def test_adapter_exists():
    assert ADAPTER.is_file(), "Implement the native endpoint adapter"


def test_default_program_is_exact_canonical_and_alternatives_are_distinct(adapter):
    record = Catalog(ROOT).get("539d4ac45311")
    programs = {row["program_solution"] for row in record["variants"]}
    assert len(programs) == 1
    canonical = next(iter(programs))
    assert adapter.program(SETTINGS[0]) == canonical
    assert len({adapter.program(setting) for setting in SETTINGS}) == 3


def test_literal_crossing_and_cascade_semantics(adapter):
    grid = [[0] * 11 for _ in range(9)]
    # A horizontal span crosses a vertical span of a different color.  The
    # first pass blocks the second; reversing the order changes the answer.
    grid[4][1] = grid[4][9] = 2
    grid[1][5] = grid[7][5] = 6
    # Two equal horizontal endpoint rows create a rectangle only in cascade.
    for r in (0, 3):
        grid[r][0] = grid[r][3] = 4

    horizontal = adapter.solve(grid, "horizontal")
    vertical = adapter.solve(grid, "vertical")
    cascade = adapter.solve(grid, "cascade")
    reverse = adapter.solve(adapter.solve(grid, "vertical"), "horizontal")

    assert horizontal[4][1:10] == [2] * 9
    assert vertical[1][5] == vertical[7][5] == 6
    assert all(vertical[r][5] == 6 for r in range(1, 8))
    assert all(cascade[r][c] == 4 for r in range(4) for c in range(4))
    assert cascade != horizontal and cascade != vertical and cascade != reverse
    assert cascade[4][5] == 2 and reverse[4][5] == 6


@pytest.mark.parametrize("demos", range(2, 7))
@pytest.mark.parametrize("queries", range(1, 5))
def test_counts_matched_inputs_reproducibility_and_prefixes(adapter, demos, queries):
    full = adapter.generate(17, SETTINGS[2], 6, 4)
    episode = adapter.generate(17, SETTINGS[2], demos, queries)
    assert episode["train"] == full["train"][:demos]
    assert episode["test"] == full["test"][:queries]
    assert episode == adapter.generate(17, SETTINGS[2], demos, queries)
    assert len(episode["train"]) == demos and len(episode["test"]) == queries
    identities = [json.dumps(pair["input"]) for split in ("train", "test") for pair in episode[split]]
    assert len(identities) == len(set(identities))

    baseline_inputs = [pair["input"] for split in ("train", "test") for pair in episode[split]]
    for setting in SETTINGS[:2]:
        other = adapter.generate(17, setting, demos, queries)
        assert [pair["input"] for split in ("train", "test") for pair in other[split]] == baseline_inputs
        assert other["program_solution"] == adapter.program(setting)

    changed = copy.deepcopy(episode)
    changed["train"][0]["input"][0][0] = 9
    assert adapter.generate(17, SETTINGS[2], demos, queries) == episode


def test_minimum_demos_identify_all_three_settings(adapter):
    episodes = [adapter.generate(29, setting, 2, 4) for setting in SETTINGS]
    for chosen, episode in enumerate(episodes):
        survivors = []
        for rival, setting in enumerate(SETTINGS):
            labels = [adapter.solve(pair["input"], setting["connection_mode"]) for pair in episode["train"]]
            if labels == [pair["output"] for pair in episode["train"]]:
                survivors.append(rival)
        assert survivors == [chosen]


def test_large_query_is_real_30x30_stress(adapter):
    episode = adapter.generate(0, SETTINGS[2], 2, 4)
    pair = next(pair for pair in episode["test"] if len(pair["input"]) == len(pair["input"][0]) == 30)
    source, output = pair["input"], pair["output"]
    occupied = [(r, c) for r, row in enumerate(source) for c, value in enumerate(row) if value]
    assert len(occupied) >= 28
    assert any(r == 0 for r, _ in occupied) and any(r == 29 for r, _ in occupied)
    assert any(c == 0 for _, c in occupied) and any(c == 29 for _, c in occupied)
    assert sum(a != b for ar, br in zip(source, output) for a, b in zip(ar, br)) >= 180
    assert all(any(source[r][c] for r in range(r0, r0 + 15) for c in range(c0, c0 + 15))
               for r0 in (0, 15) for c0 in (0, 15))


def test_public_turn_contains_one_masked_query_and_is_metadata_invariant(adapter):
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
    with pytest.raises(ValueError):
        adapter.public_turn(episode, True)


@pytest.mark.parametrize("settings", [None, {}, {"connection_mode": "diagonal"},
    {"connection_mode": True}, {"connection_mode": "horizontal", "extra": 1}])
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


def test_bad_grids_rejected(adapter):
    bad = [[], [[]], [[0] * 4 for _ in range(5)], [[0] * 31 for _ in range(5)],
           [[0] * 5 for _ in range(4)] + [[0] * 4], [[False] * 5 for _ in range(5)],
           [[10] * 5 for _ in range(5)]]
    for grid in bad:
        with pytest.raises(ValueError):
            adapter.solve(grid, "horizontal")


def test_bounded_audit_replays_identifiability_and_cascade_causality(tmp_path):
    audit = _load("audit")
    destination = tmp_path / "audit.json"
    report = audit.run_audit(destination, seeds=(0, 17, 29, 63))
    assert report["status"] == "pass"
    assert report["seeds"] == [0, 17, 29, 63]
    assert report["settings_checked"] == 12
    assert report["minimum_demo_survivors"] == 12
    assert report["cascade_pairs_checked"] == 24
    assert report["cascade_differs_from_skip_a"] == 24
    assert report["cascade_differs_from_skip_b"] == 24
    assert report["cascade_differs_from_reversed_order"] == 24
    assert json.loads(destination.read_text()) == report
