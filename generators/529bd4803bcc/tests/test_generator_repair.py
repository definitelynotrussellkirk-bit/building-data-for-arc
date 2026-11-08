"""Focused regressions for the 529bd4803bcc generator repair."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, canonical_path, find_root

TASK = "529bd4803bcc"
ROOT = find_root(__file__)
SOURCE = next(
    path
    for path in (
        ROOT / "generators" / TASK / "generator.py",
        ROOT / "puzzle_generators" / "per_puzzle" / TASK / "generator.py",
    )
    if path.is_file()
)
SPEC = importlib.util.spec_from_file_location("reviewed_529bd4803bcc", SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(GEN)


def components(grid):
    """Independent 4-neighbor components of every non-wall cell."""
    height, width = len(grid), len(grid[0])
    pending = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 5
    }
    result = []
    while pending:
        start = min(pending)
        pending.remove(start)
        todo = [start]
        component = {start}
        while todo:
            row, col = todo.pop()
            for neighbor in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if neighbor in pending:
                    pending.remove(neighbor)
                    component.add(neighbor)
                    todo.append(neighbor)
        result.append(component)
    return result


def seed_counts(grid):
    return sorted(
        sum(grid[row][col] in (1, 2, 3) for row, col in component)
        for component in components(grid)
    )


def expected_output(grid, *, accept_count=lambda count: count == 1):
    """Independent executable statement of the canonical component rule."""
    out = [[5 if value == 5 else 0 for value in row] for row in grid]
    for component in components(grid):
        seeds = [
            grid[row][col]
            for row, col in component
            if grid[row][col] in (1, 2, 3)
        ]
        if accept_count(len(seeds)):
            for row, col in component:
                out[row][col] = seeds[0]
    return out


def test_accepts_every_canonical_input_and_pins_the_exact_rule():
    pairs = canonical_pairs(TASK, root=ROOT)
    assert len(pairs) == 5
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert expected_output(pair["input"]) == pair["output"]

    with canonical_path(ROOT).open() as stream:
        record = next(json.loads(line) for line in stream if TASK in line)
    normalized = " ".join(record["program_solution"].split())
    assert GEN.RULE_HASH == hashlib.sha256(normalized.encode()).hexdigest()[:12]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {
            "grid_h": 10,
            "grid_w": 10,
            "row_dividers": 2,
            "col_dividers": 2,
            "wall_thickness": 2,
            "layout_kind": "local_split",
            "n_single": 3,
            "multi_seed_count": 4,
        },
        {
            "grid_h": 18,
            "grid_w": 18,
            "row_dividers": 1,
            "col_dividers": 1,
            "wall_thickness": 1,
            "layout_kind": "regular",
            "n_single": 0,
            "multi_seed_count": 2,
        },
    ],
)
def test_joint_boundary_overrides_are_exact_in_every_band(band, options):
    grid = GEN.generate(17, 11, difficulty=band, **options)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == options
    counts = seed_counts(grid)
    assert counts.count(1) == options["n_single"]
    assert max(counts) == options["multi_seed_count"]
    assert expected_output(grid) != grid


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo": 1},
        {"texture": "default"},
        {"grid_h": 9},
        {"grid_w": 19},
        {"row_dividers": 0},
        {"row_dividers": 3},
        {"col_dividers": True},
        {"wall_thickness": 3},
        {"layout_kind": "cross"},
        {"n_single": 4},
        {"multi_seed_count": 1},
        {"multi_seed_count": 5},
    ],
)
def test_unknown_removed_and_invalid_overrides_fail(overrides):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **overrides)


def test_validator_is_branch_neutral_and_handles_malformed_grids():
    zero_single = GEN.generate(3, 1, n_single=0, multi_seed_count=4)
    assert GEN.self_check(zero_single) == []
    assert 1 not in seed_counts(zero_single)
    for bad in (None, [], [[]], [[0], [0, 0]], [[True, 5], [0, 0]], [[9, 5], [0, 0]]):
        assert GEN.self_check(bad)


def test_declared_rivals_are_real_counterexamples():
    odd_witness = GEN.generate(
        9,
        1,
        layout_kind="regular",
        n_single=1,
        multi_seed_count=3,
    )
    intended = expected_output(odd_witness)
    assert GEN.SEMANTIC_WITNESSES["triple_seed_compartment"](odd_witness)
    assert GEN.SEMANTIC_RIVALS["odd_seed_count"](odd_witness) != intended

    split_witness = GEN.generate(
        9,
        2,
        layout_kind="local_split",
        n_single=1,
        multi_seed_count=3,
    )
    intended = expected_output(split_witness)
    assert GEN.SEMANTIC_WITNESSES["local_separator"](split_witness)
    assert GEN.SEMANTIC_RIVALS["global_dividers_only"](split_witness) != intended


def test_odd_seed_shortcut_fits_all_canonical_pairs_but_generated_triples_refute_it():
    pairs = canonical_pairs(TASK, root=ROOT)
    rival = GEN.CANONICAL_SHORTCUTS["odd_seed_count"]
    assert all(rival(pair["input"]) == pair["output"] for pair in pairs)
    for index in range(12):
        grid = GEN.generate(81, index)
        assert GEN.observe_overrides(grid)["multi_seed_count"] == 3
        assert rival(grid) != expected_output(grid)


def test_every_four_pair_window_survives_any_single_query_rotation():
    assert GEN.LESSON_SCHEDULE_PERIOD == 2
    for start in range(8):
        pairs = []
        for index in range(start, start + 4):
            grid = GEN.generate(210, index, difficulty="hard")
            pairs.append({"input": grid, "output": expected_output(grid)})
        for query_index, query in enumerate(pairs):
            demos = [pair for i, pair in enumerate(pairs) if i != query_index]
            for name, rival in GEN.LESSON_COMPETITORS.items():
                ambiguous = (
                    all(rival(pair["input"]) == pair["output"] for pair in demos)
                    and rival(query["input"]) != query["output"]
                )
                assert not ambiguous, (start, query_index, name)


def test_generation_is_deterministic_and_input_is_not_mutated_by_rivals():
    grid = GEN.generate(61, 7, difficulty="medium")
    assert grid == GEN.generate(61, 7, difficulty="medium")
    frozen = [row[:] for row in grid]
    for rival in GEN.LESSON_COMPETITORS.values():
        rival(grid)
        assert grid == frozen


def test_pinned_profile_floor_has_an_exact_anchor_in_every_band():
    canonical_profiles = {
        (
            len(pair["input"]),
            len(pair["input"][0]),
            len({value for row in pair["input"] for value in row}),
        )
        for pair in canonical_pairs(TASK, root=ROOT)
    }
    for band in ("easy", "medium", "hard"):
        hits = 0
        for index in range(20):
            digest = hashlib.sha256(
                f"profile-floor:v1:{TASK}:{band}:{index}".encode()
            ).hexdigest()
            seed = int(digest[:12], 16)
            grid = GEN.generate(seed, seed % 7919 + index, difficulty=band)
            profile = (
                len(grid),
                len(grid[0]),
                len({value for row in grid for value in row}),
            )
            hits += profile in canonical_profiles
        assert hits >= 1, (band, canonical_profiles)
