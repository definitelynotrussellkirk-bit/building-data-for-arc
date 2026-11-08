from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
from pathlib import Path

import pytest


TASK_ID = "ce0b0e843251"
REPO = Path(__file__).resolve().parents[3]
GENERATOR_PATH = REPO / "generators" / TASK_ID / "generator.py"
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", GENERATOR_PATH)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _canonical_row():
    with (REPO / "shared/data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError("canonical task missing")


def _canonical_pairs():
    row = _canonical_row()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return row["train"] + test


def _rooms(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    rooms = []
    for sr in range(h):
        for sc in range(w):
            if (sr, sc) in seen or grid[sr][sc] in (5, 7):
                continue
            seen.add((sr, sc))
            stack = [(sr, sc)]
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] not in (5, 7)
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rooms.append(cells)
    return rooms


def test_rule_hash_and_python_mirror_match_every_canonical_pair():
    row = _canonical_row()
    expected_hash = hashlib.sha256(
        " ".join(row["program_solution"].split()).encode()
    ).hexdigest()[:12]
    assert GEN.RULE_HASH == expected_hash
    for pair in _canonical_pairs():
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize(
    "profile,rooms",
    [
        ("three_room", 3),
        ("four_room", 4),
        ("five_room", 5),
        ("six_room", 6),
    ],
)
@pytest.mark.parametrize("orientation", ["vertical", "horizontal"])
@pytest.mark.parametrize("coverage,seedless", [("all_seeded", 0), ("one_seedless", 1)])
def test_each_exact_override_combination_is_observable_and_lawful(
    profile, rooms, orientation, coverage, seedless
):
    grid = GEN.generate(
        1701,
        23,
        difficulty="easy",
        layout_profile=profile,
        orientation=orientation,
        seed_coverage=coverage,
    )
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == {
        "layout_profile": profile,
        "orientation": orientation,
        "seed_coverage": coverage,
    }
    analysis = GEN.semantic_signature(grid)
    assert analysis["rooms"] == rooms
    assert analysis["seedless_rooms"] == seedless
    assert GEN.rule_mirror(grid) != grid


def test_default_census_covers_canonical_profiles_and_all_declared_branches():
    observed = set()
    exact_profiles = set()
    strict_hits = 0
    canonical_profiles = {
        (9, 11, 6),
        (9, 12, 7),
        (10, 12, 8),
    }
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for index in range(80):
            grid = GEN.generate(20000 + 1000 * band_index + index, index, difficulty=band)
            assert GEN.self_check(grid) == []
            factors = GEN.observe_overrides(grid)
            observed.add(tuple(sorted(factors.items())))
            profile = (
                len(grid),
                len(grid[0]),
                len({value for row in grid for value in row}),
            )
            if profile in canonical_profiles:
                exact_profiles.add(profile)
            if GEN.strict_canonical_like(grid) == []:
                strict_hits += 1
    assert exact_profiles == canonical_profiles
    assert strict_hits >= 12
    assert {dict(items)["layout_profile"] for items in observed} == {
        "three_room",
        "four_room",
        "five_room",
        "six_room",
    }
    assert {dict(items)["orientation"] for items in observed} == {
        "vertical",
        "horizontal",
    }
    assert {dict(items)["seed_coverage"] for items in observed} == {
        "all_seeded",
        "one_seedless",
    }


def test_self_check_rejects_structural_and_semantic_impostors():
    minimal = [
        [7, 7, 7, 7, 7],
        [7, 0, 0, 0, 7],
        [7, 0, 2, 0, 7],
        [7, 0, 0, 0, 7],
        [7, 7, 7, 7, 7],
    ]
    assert GEN.self_check(minimal)

    valid = GEN.generate(
        55,
        8,
        layout_profile="five_room",
        orientation="vertical",
        seed_coverage="one_seedless",
    )
    assert GEN.self_check(valid) == []

    broken_border = copy.deepcopy(valid)
    broken_border[0][2] = 0
    assert GEN.self_check(broken_border)

    no_dividers = copy.deepcopy(valid)
    for r in range(1, len(no_dividers) - 1):
        for c in range(1, len(no_dividers[0]) - 1):
            if no_dividers[r][c] == 5:
                no_dividers[r][c] = 0
    assert GEN.self_check(no_dividers)

    ambiguous = copy.deepcopy(valid)
    seeded_room = next(
        room
        for room in _rooms(ambiguous)
        if any(ambiguous[r][c] not in (0, 5, 7) for r, c in room)
        and sum(ambiguous[r][c] == 0 for r, c in room) >= 1
    )
    existing = next(
        ambiguous[r][c]
        for r, c in seeded_room
        if ambiguous[r][c] not in (0, 5, 7)
    )
    r, c = next((r, c) for r, c in seeded_room if ambiguous[r][c] == 0)
    ambiguous[r][c] = next(color for color in (1, 2, 3, 4, 6, 8, 9) if color != existing)
    assert GEN.self_check(ambiguous)


def _modal_nonbackground_components(grid):
    counts = {}
    for row in grid:
        for value in row:
            counts[value] = counts.get(value, 0) + 1
    background = max(counts, key=counts.get)
    h, w = len(grid), len(grid[0])
    seen = set()
    components = 0
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] == background or (sr, sc) in seen:
                continue
            components += 1
            seen.add((sr, sc))
            stack = [(sr, sc)]
            while stack:
                r, c = stack.pop()
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] != background
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
    return components


def test_battery_census_keeps_multiple_nonbackground_components():
    # Mirrors generator_distribution_gate.py's exact census. The former
    # edge-heavy sampler collapsed the aggregate median to one wall-connected
    # blob, while the canonical training median is four components.
    values = [
        _modal_nonbackground_components(GEN.generate(seed, seed, difficulty=band))
        for band in ("easy", "medium", "hard")
        for seed in range(1, 41)
    ]
    values.sort()
    aggregate_median = (values[59] + values[60]) / 2
    assert aggregate_median >= 2


def test_unknown_override_is_rejected():
    with pytest.raises((TypeError, ValueError), match="unknown override"):
        GEN.generate(1, 0, typo_axis="three_room")


def test_generation_is_deterministic_fresh_and_does_not_touch_global_rng():
    state = random.getstate()
    kwargs = dict(
        difficulty="hard",
        layout_profile="six_room",
        orientation="horizontal",
        seed_coverage="one_seedless",
    )
    first = GEN.generate(9988, 77, **kwargs)
    second = GEN.generate(9988, 77, **kwargs)
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    saved = copy.deepcopy(second)
    first[0][0] = 0
    assert GEN.generate(9988, 77, **kwargs) == saved
