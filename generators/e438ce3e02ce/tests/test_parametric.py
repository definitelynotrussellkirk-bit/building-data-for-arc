"""Behavioral contract for the native Manhattan/Chebyshev seed partition family."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from arcpuzzles import Catalog


ROOT = Path(__file__).resolve().parents[3]
HOME = ROOT / "generators/e438ce3e02ce/workspace/parametric"
ADAPTER = HOME / "adapter.py"
SETTINGS = [
    {"distance_metric": "manhattan"},
    {"distance_metric": "chebyshev"},
]


def _load(name: str):
    path = HOME / f"{name}.py"
    assert path.is_file(), f"build {path.relative_to(ROOT)}"
    spec = importlib.util.spec_from_file_location(f"test_e438_{name}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def adapter():
    return _load("adapter")


def test_adapter_exists():
    assert ADAPTER.is_file(), "Implement the native seed-partition adapter"


def test_default_program_is_exact_canonical_and_chebyshev_is_distinct(adapter):
    record = Catalog(ROOT).get("e438ce3e02ce")
    programs = {row["program_solution"] for row in record["variants"]}
    assert len(programs) == 1
    canonical = next(iter(programs))
    assert adapter.program(SETTINGS[0]) == canonical
    assert adapter.program(SETTINGS[1]) != canonical


def test_literal_metric_and_tie_semantics(adapter):
    grid = [[0] * 9 for _ in range(9)]
    grid[5][2] = 1
    grid[1][6] = 2
    grid[6][1] = 3

    manhattan = adapter.solve(grid, "manhattan")
    chebyshev = adapter.solve(grid, "chebyshev")

    assert manhattan[0][0] == 8
    assert chebyshev[0][0] == 1
    assert manhattan != chebyshev
    for row, column, color in ((5, 2, 1), (1, 6, 2), (6, 1, 3)):
        assert manhattan[row][column] == chebyshev[row][column] == color
    assert 0 not in {value for row in manhattan for value in row}
    assert 0 not in {value for row in chebyshev for value in row}


@pytest.mark.parametrize("demos", range(2, 7))
@pytest.mark.parametrize("queries", range(1, 5))
def test_counts_matched_inputs_reproducibility_and_prefixes(adapter, demos, queries):
    full = adapter.generate(17, SETTINGS[1], 6, 4)
    episode = adapter.generate(17, SETTINGS[1], demos, queries)
    assert episode["train"] == full["train"][:demos]
    assert episode["test"] == full["test"][:queries]
    assert episode == adapter.generate(17, SETTINGS[1], demos, queries)
    assert len(episode["train"]) == demos and len(episode["test"]) == queries

    identities = [json.dumps(pair["input"]) for split in ("train", "test") for pair in episode[split]]
    assert len(identities) == len(set(identities))
    baseline_inputs = [pair["input"] for split in ("train", "test") for pair in episode[split]]
    other = adapter.generate(17, SETTINGS[0], demos, queries)
    assert [pair["input"] for split in ("train", "test") for pair in other[split]] == baseline_inputs
    assert other["program_solution"] == adapter.program(SETTINGS[0])

    changed = copy.deepcopy(episode)
    changed["train"][0]["input"][0][0] = 9
    assert adapter.generate(17, SETTINGS[1], demos, queries) == episode


@pytest.mark.parametrize("seed", [0, 17, 29, 63])
def test_minimum_demos_identify_both_settings(adapter, seed):
    for chosen in SETTINGS:
        episode = adapter.generate(seed, chosen, 2, 4)
        expected = [pair["output"] for pair in episode["train"]]
        survivors = []
        for candidate in SETTINGS:
            labels = [adapter.solve(pair["input"], candidate["distance_metric"])
                      for pair in episode["train"]]
            if labels == expected:
                survivors.append(candidate)
        assert survivors == [chosen]


def test_every_generated_input_has_valid_sparse_seed_grammar_and_metric_signal(adapter):
    episode = adapter.generate(29, SETTINGS[0], 6, 4)
    for split in ("train", "test"):
        for pair in episode[split]:
            grid = pair["input"]
            seeds = [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
            assert 3 <= len(seeds) <= 5
            colors = [value for _, _, value in seeds]
            assert len(colors) == len(set(colors))
            assert all(color not in (0, 8) for color in colors)
            manhattan = adapter.solve(grid, "manhattan")
            chebyshev = adapter.solve(grid, "chebyshev")
            assert manhattan != chebyshev
            assert any(value == 8 for row in manhattan for value in row)
            assert any(value == 8 for row in chebyshev for value in row)
            for color in colors:
                assert sum(value == color for row in manhattan for value in row) > 1
                assert sum(value == color for row in chebyshev for value in row) > 1


def test_large_query_is_real_30x30_stress(adapter):
    manhattan_episode = adapter.generate(0, SETTINGS[0], 2, 4)
    chebyshev_episode = adapter.generate(0, SETTINGS[1], 2, 4)
    manhattan_pair = next(pair for pair in manhattan_episode["test"]
                          if len(pair["input"]) == len(pair["input"][0]) == 30)
    chebyshev_pair = next(pair for pair in chebyshev_episode["test"]
                          if len(pair["input"]) == len(pair["input"][0]) == 30)
    source = manhattan_pair["input"]
    assert source == chebyshev_pair["input"]
    seeds = [(r, c, value) for r, row in enumerate(source) for c, value in enumerate(row) if value]
    assert len(seeds) == 5
    assert any(r == 0 for r, _, _ in seeds) and any(r == 29 for r, _, _ in seeds)
    assert any(c == 0 for _, c, _ in seeds) and any(c == 29 for _, c, _ in seeds)
    assert all(any((r < 15) == top and (c < 15) == left for r, c, _ in seeds)
               for top in (False, True) for left in (False, True))
    assert sum(a != b for ar, br in zip(manhattan_pair["output"], chebyshev_pair["output"])
               for a, b in zip(ar, br)) >= 150
    for pair in (manhattan_pair, chebyshev_pair):
        assert sum(a != b for ar, br in zip(source, pair["output"])
                   for a, b in zip(ar, br)) == 895
        assert 0 not in {value for row in pair["output"] for value in row}


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


@pytest.mark.parametrize("settings", [None, {}, {"distance_metric": "euclidean"},
    {"distance_metric": True}, {"distance_metric": "manhattan", "extra": 1}])
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
           [[10] * 5 for _ in range(5)], [[0] * 5 for _ in range(5)]]
    duplicate = [[0] * 5 for _ in range(5)]
    duplicate[0][0] = duplicate[4][4] = 1
    duplicate[2][2] = 2
    bad.append(duplicate)
    tie_color = [[0] * 5 for _ in range(5)]
    tie_color[0][0], tie_color[2][2], tie_color[4][4] = 1, 8, 2
    bad.append(tie_color)
    for grid in bad:
        with pytest.raises(ValueError):
            adapter.solve(grid, "manhattan")


def test_bounded_audit_replays_identifiability_metric_signal_and_stress(tmp_path):
    audit = _load("audit")
    destination = tmp_path / "audit.json"
    report = audit.run_audit(destination, seeds=(0, 17, 29, 63))
    assert report["status"] == "pass"
    assert report["seeds"] == [0, 17, 29, 63]
    assert report["settings_checked"] == 8
    assert report["minimum_demo_survivors"] == 8
    assert report["metric_pairs_checked"] == 40
    assert report["metric_outputs_differ"] == 40
    assert report["region_checks"] == 80
    assert report["stress_cases_checked"] == 4
    assert json.loads(destination.read_text()) == report
