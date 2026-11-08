from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
import sys
from pathlib import Path

import numpy as np
import pytest


TASK_ID = "2fd7d58a066c"
TASK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TASK_ROOT.parents[1]
RUNTIME_ROOT = REPO_ROOT / "shared" / "runtime"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

_spec = importlib.util.spec_from_file_location(
    f"generator_{TASK_ID}", TASK_ROOT / "generator.py"
)
assert _spec is not None and _spec.loader is not None
gen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gen)


def _canonical_row() -> dict:
    path = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError("canonical row missing")


def _canonical_pairs() -> list[dict]:
    row = _canonical_row()
    test = row["test"]
    return list(row["train"]) + ([test] if isinstance(test, dict) else list(test))


def _occupied_columns(grid):
    h, w = len(grid), len(grid[0])
    return {
        c: [(r, grid[r][c]) for r in range(h) if grid[r][c] != 0]
        for c in range(w)
        if any(grid[r][c] != 0 for r in range(h))
    }


def test_all_canonical_inputs_are_accepted_and_python_mirror_matches_outputs():
    pairs = _canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.expected_output(pair["input"]) == pair["output"]


def test_profile_schedule_is_observable_and_semantically_broad():
    grids = [
        gen.generate(314159, index, difficulty="medium")
        for index in range(len(gen.PROFILE_SCHEDULE))
    ]
    assert [gen.observe_overrides(grid)["scene_profile"] for grid in grids] == list(
        gen.PROFILE_SCHEDULE
    )
    assert all(gen.self_check(grid) == [] for grid in grids)

    by_profile = {
        profile: grid for profile, grid in zip(gen.PROFILE_SCHEDULE, grids)
    }
    canonical = by_profile["canonical_pairs"]
    adjacent = by_profile["adjacent_shared"]
    mixed = by_profile["mixed_extremes"]
    singleton = by_profile["singleton_and_extra"]
    canonical_cols = _occupied_columns(canonical)
    assert (len(canonical), len(canonical[0])) in gen.CANONICAL_DIMS
    assert {value for row in canonical for value in row} <= {0, 2}
    assert all(len(cells) == 2 for cells in canonical_cols.values())

    adjacent_cols = _occupied_columns(adjacent)
    ordered = sorted(adjacent_cols)
    assert any(b == a + 1 for a, b in zip(ordered, ordered[1:]))
    mono_colors = [cells[0][1] for cells in adjacent_cols.values() if len({v for _, v in cells}) == 1]
    assert len(mono_colors) != len(set(mono_colors))

    mixed_cols = _occupied_columns(mixed)
    assert any(cells[0][1] != cells[-1][1] for cells in mixed_cols.values())

    singleton_cols = _occupied_columns(singleton)
    assert any(len(cells) == 1 for cells in singleton_cols.values())
    assert any(len(cells) >= 3 for cells in singleton_cols.values())


def test_every_exact_profile_override_round_trips_and_unknown_keys_reject():
    for profile in gen.SCENE_PROFILES:
        grid = gen.generate(2718, 11, difficulty="easy", scene_profile=profile)
        assert gen.observe_overrides(grid) == {"scene_profile": profile}
        assert gen.self_check(grid) == []

    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 0, not_an_axis=3)
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 0, scene_profile="not-a-profile")


def test_profile_schedule_refutes_named_shortcuts_in_one_lesson():
    pairs = []
    for index in range(gen.EXAMPLES_NEEDED + 1):
        grid = gen.generate(777, index, difficulty="medium")
        pairs.append({"input": grid, "output": gen.expected_output(grid)})
    assert gen.lesson_identifiable(
        pairs[: gen.EXAMPLES_NEEDED], pairs[gen.EXAMPLES_NEEDED]
    ) == []

    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert any(
            rival(pair["input"]) != pair["output"]
            for pair in pairs[: gen.EXAMPLES_NEEDED]
        ), name


def test_declared_witnesses_are_live_and_refute_their_named_rivals():
    for index in range(len(gen.PROFILE_SCHEDULE)):
        grid = gen.generate(4242, index, difficulty="medium")
        authoritative = gen.expected_output(grid)
        for witness_name, predicate in gen.SEMANTIC_WITNESSES.items():
            if not predicate(grid):
                continue
            rival_names = gen.WITNESS_RIVALS[witness_name]
            assert any(
                gen.SEMANTIC_RIVALS[name](grid) != authoritative
                for name in rival_names
            ), witness_name

    assert all(
        any(
            predicate(gen.generate(4242, index, difficulty="medium"))
            for index in range(len(gen.PROFILE_SCHEDULE))
        )
        for predicate in gen.SEMANTIC_WITNESSES.values()
    )



def test_pinned_profile_floor_has_at_least_twenty_five_percent_exact_anchors():
    canonical_profiles = {(9, 9, 2), (10, 8, 2), (10, 10, 2)}
    exact = 0
    total = 0
    for band in ("easy", "medium", "hard"):
        for index in range(20):
            digest = hashlib.sha256(
                f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
            ).hexdigest()
            seed = int(digest[:12], 16)
            sample_index = seed % 7919 + index
            grid = gen.generate(seed, sample_index, difficulty=band)
            signature = (
                len(grid),
                len(grid[0]),
                len({value for row in grid for value in row}),
            )
            exact += signature in canonical_profiles
            total += 1
    assert exact / total >= 0.25

def test_generation_is_deterministic_fresh_and_does_not_touch_global_rngs():
    random.seed(123456)
    np.random.seed(654321)
    python_rng_before = random.getstate()
    numpy_rng_before = np.random.get_state()

    first = gen.generate(99, 3, difficulty="hard")
    snapshot = copy.deepcopy(first)
    second = gen.generate(99, 3, difficulty="hard")

    assert random.getstate() == python_rng_before
    numpy_rng_after = np.random.get_state()
    assert numpy_rng_after[0] == numpy_rng_before[0]
    assert np.array_equal(numpy_rng_after[1], numpy_rng_before[1])
    assert numpy_rng_after[2:] == numpy_rng_before[2:]
    assert first == second
    assert first is not second
    first[0][0] = 9
    assert second == snapshot


def test_self_check_rejects_minimal_and_already_filled_impostors():
    blank = [[0] * 8 for _ in range(9)]
    singleton = copy.deepcopy(blank)
    singleton[4][3] = 2

    already_filled = copy.deepcopy(blank)
    for r in range(1, 6):
        already_filled[r][2] = 3
    for r in range(2, 8):
        already_filled[r][5] = 4

    short_spans = copy.deepcopy(blank)
    short_spans[1][2] = short_spans[2][2] = 3
    short_spans[5][5] = short_spans[6][5] = 4

    for impostor in (blank, singleton, already_filled, short_spans):
        assert gen.self_check(impostor), "malformed/minimally uninformative input accepted"
