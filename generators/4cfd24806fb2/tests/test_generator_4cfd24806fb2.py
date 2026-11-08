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


TASK_ID = "4cfd24806fb2"
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


def _divider(grid) -> int:
    h, w = len(grid), len(grid[0])
    cols = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    assert len(cols) == 1
    return cols[0]


def _sources(grid):
    div = _divider(grid)
    return [
        (r, c, grid[r][c])
        for r in range(len(grid))
        for c in range(div)
        if grid[r][c] not in (0, 5)
    ]


def _right_cells(grid):
    div = _divider(grid)
    return [
        (r, c, grid[r][c])
        for r in range(len(grid))
        for c in range(div + 1, len(grid[0]))
        if grid[r][c] not in (0, 5)
    ]


def test_rule_pin_and_python_audit_match_every_canonical_pair():
    assert gen.RULE_HASH == "b5a5db408e2f"
    pairs = _canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.expected_output(pair["input"]) == pair["output"]


def test_four_profile_schedule_is_observable_and_semantically_broad():
    seed = 314159
    grids = [
        gen.generate(seed, index, difficulty="medium")
        for index in range(len(gen.PROFILE_SCHEDULE))
    ]
    observed_profiles = [
        gen.observe_overrides(grid)["scene_profile"] for grid in grids
    ]
    expected_profiles = [
        gen.schedule_profile(seed, index, difficulty="medium")
        for index in range(len(gen.PROFILE_SCHEDULE))
    ]
    assert observed_profiles == expected_profiles
    assert set(observed_profiles) == set(gen.SCENE_PROFILES)
    assert all(gen.self_check(grid) == [] for grid in grids)

    by_profile = dict(zip(observed_profiles, grids))

    canonical = by_profile["canonical_sparse"]
    assert gen.strict_canonical_like(canonical) == []
    assert _right_cells(canonical) == []

    off_center = by_profile["off_center_cluster"]
    off_div = _divider(off_center)
    assert off_div != (len(off_center[0]) - 1) // 2
    assert gen.semantic_observables(off_center)["connected_source_cells"]
    assert any(value == 9 for _r, _c, value in _sources(off_center))

    edge_rows = by_profile["edge_row_motif"]
    edge_sources = _sources(edge_rows)
    assert len(edge_sources) > 6
    assert {r for r, _c, _v in edge_sources} >= {0, len(edge_rows) - 1}
    row_counts = {}
    for r, _c, _v in edge_sources:
        row_counts[r] = row_counts.get(r, 0) + 1
    assert max(row_counts.values()) >= 2

    right_noise = by_profile["preserved_right_noise"]
    right_cells = _right_cells(right_noise)
    assert len(right_cells) >= 2
    output = gen.expected_output(right_noise)
    assert all(output[r][c] == value for r, c, value in right_cells)


def test_every_profile_override_round_trips_and_bad_calls_reject():
    for profile in gen.SCENE_PROFILES:
        grid = gen.generate(2718, 11, difficulty="easy", scene_profile=profile)
        assert gen.observe_overrides(grid) == {"scene_profile": profile}
        assert gen.self_check(grid) == []

    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 0, not_an_axis=3)
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 0, scene_profile="not-a-profile")
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 0, difficulty="extreme")


def test_declared_canonical_shortcuts_really_fit_canonical_but_one_lesson_refutes_them():
    canonical_pairs = _canonical_pairs()
    for name, shortcut in gen.CANONICAL_SHORTCUTS.items():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in canonical_pairs), name

    lesson = []
    for index in range(gen.EXAMPLES_NEEDED + 1):
        grid = gen.generate(777, index, difficulty="medium")
        lesson.append({"input": grid, "output": gen.expected_output(grid)})

    assert gen.lesson_identifiable(
        lesson[: gen.EXAMPLES_NEEDED], lesson[gen.EXAMPLES_NEEDED]
    ) == []
    for name, shortcut in gen.CANONICAL_SHORTCUTS.items():
        assert any(
            shortcut(pair["input"]) != pair["output"]
            for pair in lesson[: gen.EXAMPLES_NEEDED]
        ), name


def test_every_declared_witness_is_live_and_refutes_a_named_rival():
    grids = [
        gen.generate(4242, index, difficulty="medium")
        for index in range(len(gen.PROFILE_SCHEDULE))
    ]
    for witness_name, predicate in gen.SEMANTIC_WITNESSES.items():
        firing = [grid for grid in grids if predicate(grid)]
        assert firing, witness_name
        for grid in firing:
            authoritative = gen.expected_output(grid)
            assert any(
                gen.SEMANTIC_RIVALS[rival](grid) != authoritative
                for rival in gen.WITNESS_RIVALS[witness_name]
            ), witness_name


def test_pinned_profile_floor_has_exact_anchor_in_every_band():
    canonical_profiles = {
        (8, 9, 5),
        (9, 11, 6),
        (10, 12, 6),
        (10, 13, 7),
        (11, 15, 7),
    }
    per_band = {}
    for band in ("easy", "medium", "hard"):
        exact = 0
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
        per_band[band] = exact
    assert all(count >= 4 for count in per_band.values()), per_band


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


def test_self_check_rejects_ambiguous_or_uninformative_impostors():
    no_divider = [[0] * 11 for _ in range(9)]
    no_divider[2][2] = 4

    no_sources = [[0] * 11 for _ in range(9)]
    for row in range(9):
        no_sources[row][5] = 5

    one_distance = copy.deepcopy(no_sources)
    one_distance[1][3] = 2
    one_distance[3][3] = 3
    one_distance[5][3] = 4

    occupied_destination = copy.deepcopy(no_sources)
    occupied_destination[1][2] = 2
    occupied_destination[2][3] = 3
    occupied_destination[3][1] = 4
    occupied_destination[1][8] = 7  # mirror destination of (1,2)

    duplicate_divider = copy.deepcopy(no_sources)
    for row in range(9):
        duplicate_divider[row][6] = 5
    duplicate_divider[1][2] = 2
    duplicate_divider[2][3] = 3
    duplicate_divider[3][1] = 4

    stray_gray = copy.deepcopy(no_sources)
    stray_gray[1][2] = 2
    stray_gray[2][3] = 3
    stray_gray[3][1] = 4
    stray_gray[7][1] = 5

    for impostor in (
        no_divider,
        no_sources,
        one_distance,
        occupied_destination,
        duplicate_divider,
        stray_gray,
    ):
        assert gen.self_check(impostor), "ambiguous/uninformative input accepted"
