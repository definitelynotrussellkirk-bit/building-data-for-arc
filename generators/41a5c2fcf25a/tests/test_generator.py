"""Portable regression tests for recoloring components by area rank."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

TASK_ID = "41a5c2fcf25a"
HOME = Path(__file__).resolve().parents[1]
LIBRARY = next(
    (path for path in Path(__file__).resolve().parents if (path / "shared/runtime").is_dir()),
    None,
)
if LIBRARY is not None:
    sys.path.insert(0, str(LIBRARY / "shared/runtime"))
sys.path.insert(0, str(HOME / "workspace"))

from reviewer_support import canonical_pairs, find_root  # noqa: E402
from reference_probe import (  # noqa: E402
    analyze,
    ascending_area,
    exclude_source_from_legend,
    identity,
    load_generator,
    position_only,
    reverse_equal_size_ties,
    rule_output,
    sorted_legend,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
PAIRS = canonical_pairs(TASK_ID, root=find_root(__file__))
CANONICAL_PROFILES = {
    (len(pair["input"]), len(pair["input"][0]),
     len({value for row in pair["input"] for value in row}))
    for pair in PAIRS
}


def profile(grid):
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def labeled(grid):
    return {"input": deepcopy(grid), "output": rule_output(grid)}


def test_metadata_pins_authority_and_exposes_only_observable_axes():
    assert gen.GENERATOR_ID == gen.TASK_ID == TASK_ID
    assert gen.RULE_HASH == "729bc9e3873e"
    assert gen.VERSION == "3.0.0"
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.LESSON_SCHEDULE_PERIOD == 4
    assert gen.MIN_STRICT_FRAC == 1.0
    assert set(gen.AXES) == {"grid_h", "grid_w", "n_blobs"}
    assert tuple(gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS) == ()


@pytest.mark.parametrize("pair", PAIRS, ids=lambda p: f"{p['split']}{p['pair_index']}")
def test_accepts_all_canonical_pairs_and_independent_oracle_matches(pair):
    before = deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert rule_output(pair["input"]) == pair["output"]
    assert pair["input"] == before


def test_counterexample_covers_tie_and_source_legend_branches():
    evidence = json.loads((HOME / "counterexamples" / "tie-and-source-legend.json").read_text())
    grid = evidence["input"]
    stats = analyze(grid)
    assert gen.self_check(grid) == []
    assert stats["component_sizes"] == [4, 6, 4]
    assert stats["has_size_tie"]
    assert stats["source_in_legend"]
    expected = rule_output(grid)
    assert reverse_equal_size_ties(grid) != expected
    assert exclude_source_from_legend(grid) != expected


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_overrides_are_constructive_observable_and_band_independent(band):
    requested = {"grid_h": 10, "grid_w": 11, "n_blobs": 4}
    grid = gen.generate(17, 9, difficulty=band, **requested)
    assert gen.self_check(grid, difficulty=band, meta={"overrides": requested}) == []
    assert gen.observe_overrides(grid) == requested
    assert {name: analyze(grid)[name] for name in requested} == requested
    assert rule_output(grid) != grid


@pytest.mark.parametrize(
    "overrides",
    [
        {"unknown_axis": 1},
        {"grid_h": 9}, {"grid_h": 15}, {"grid_h": True}, {"grid_h": 10.0},
        {"grid_w": 10}, {"grid_w": 17}, {"grid_w": "11"},
        {"n_blobs": 1}, {"n_blobs": 5}, {"n_blobs": False},
    ],
)
def test_invalid_and_unknown_overrides_fail_loudly(overrides):
    with pytest.raises((TypeError, ValueError, KeyError)):
        gen.generate(0, 0, **overrides)


def test_unknown_difficulty_fails_loudly():
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(0, 0, difficulty="extreme")


@pytest.mark.parametrize(
    "seed,sample_index",
    [(True, 0), (1.5, 0), (0, True), (0, False), (0, -1), (0, "2")],
)
def test_seed_and_sample_index_are_strict_scalars(seed, sample_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(seed, sample_index)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_cyclic_four_sample_window_retains_each_teaching_branch(band):
    for start in range(12):
        pairs = [labeled(gen.generate(700 + start, start + offset, difficulty=band))
                 for offset in range(4)]
        stats = [analyze(pair["input"]) for pair in pairs]
        assert any(profile(pair["input"]) in CANONICAL_PROFILES for pair in pairs)
        assert sum(bool(item["has_size_tie"]) for item in stats) >= 2
        assert sum(bool(item["source_in_legend"]) for item in stats) >= 2
        assert all(item["legend_not_sorted"] for item in stats)
        assert all(item["rank_conflicts_position"] for item in stats)
        for held_out in range(4):
            demos = [pair for index, pair in enumerate(pairs) if index != held_out]
            assert gen.lesson_identifiable(demos, pairs[held_out]) == []


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_distribution_is_valid_diverse_and_covers_axes(band):
    grids = [gen.generate(2100 + index, index, difficulty=band) for index in range(160)]
    signatures = set()
    counts = set()
    source_modes = set()
    tie_modes = set()
    for grid in grids:
        assert gen.self_check(grid) == []
        stats = analyze(grid)
        counts.add(stats["n_blobs"])
        source_modes.add(stats["source_in_legend"])
        tie_modes.add(stats["has_size_tie"])
        signatures.add(json.dumps(grid, separators=(",", ":")))
    assert counts == {2, 3, 4}
    assert source_modes == {False, True}
    assert tie_modes == {False, True}
    assert len(signatures) >= 150


@pytest.mark.parametrize(
    "mutation",
    ["remove_legend", "gap_in_legend", "duplicate_legend", "wrong_blob_color",
     "remove_component", "add_component", "bad_color", "ragged", "bool_cell"],
)
def test_self_check_rejects_destructive_mutations(mutation):
    grid = gen.generate(41, 4, grid_h=11, grid_w=13, n_blobs=3)
    if mutation == "remove_legend":
        grid[0] = [0] * len(grid[0])
    elif mutation == "gap_in_legend":
        grid[0][1] = 0
    elif mutation == "duplicate_legend":
        grid[0][1] = grid[0][0]
    elif mutation == "wrong_blob_color":
        for row in range(1, len(grid)):
            for col in range(len(grid[0])):
                if grid[row][col] == 8:
                    grid[row][col] = 7
                    break
            else:
                continue
            break
    elif mutation == "remove_component":
        comps = __import__("reference_probe").components(grid)
        for row, col in comps[-1]:
            grid[row][col] = 0
    elif mutation == "add_component":
        grid[1][len(grid[0]) // 2] = 8
    elif mutation == "bad_color":
        grid[0][0] = 10
    elif mutation == "ragged":
        grid[0].pop()
    elif mutation == "bool_cell":
        grid[0][0] = True
    assert gen.self_check(grid)


def test_declared_witnesses_and_rivals_are_executable_counterexamples():
    seen = {name: False for name in gen.SEMANTIC_WITNESSES}
    for index in range(8):
        grid = gen.generate(900, index)
        expected = rule_output(grid)
        for name, witness in gen.SEMANTIC_WITNESSES.items():
            seen[name] |= bool(witness(grid))
        for name, rival in gen.SEMANTIC_RIVALS.items():
            prediction = rival(grid)
            assert grid == gen.generate(900, index)
            if name in {"reverse_equal_size_ties", "exclude_source_from_legend"}:
                continue
            assert prediction != expected
    assert all(seen.values())
    tie = gen.generate(900, 3)
    source = gen.generate(900, 2)
    assert gen.SEMANTIC_RIVALS["reverse_equal_size_ties"](tie) != rule_output(tie)
    assert gen.SEMANTIC_RIVALS["exclude_source_from_legend"](source) != rule_output(source)


def test_generation_is_deterministic_and_hash_seed_independent():
    for band in (None, "easy", "medium", "hard"):
        first = gen.generate(8128, 23, difficulty=band)
        assert first == gen.generate(8128, 23, difficulty=band)
        frozen = deepcopy(first)
        _ = rule_output(first)
        for rival in gen.LESSON_COMPETITORS.values():
            _ = rival(first)
        assert first == frozen

    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(31,8,difficulty='hard')))"
    )
    outputs = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        outputs.append(subprocess.check_output(
            [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
            env=env, text=True,
        ))
    assert outputs[0] == outputs[1]


def test_reference_probe_wrong_rules_are_distinct_on_scheduled_support():
    grids = [gen.generate(121, index) for index in range(4)]
    functions = [identity, position_only, ascending_area, sorted_legend,
                 reverse_equal_size_ties, exclude_source_from_legend]
    for rival in functions:
        assert any(rival(grid) != rule_output(grid) for grid in grids)
