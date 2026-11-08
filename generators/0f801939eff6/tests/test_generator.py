"""Task-local regression suite for the area-sorted component curriculum.

The oracles below are deliberately independent of production helpers: tests
extract same-color 4-connected components directly from pixels, then implement
both the canonical rule and the two strongest rival rules.
"""
from __future__ import annotations

from collections import Counter, deque
import hashlib
from copy import deepcopy

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "0f801939eff6"
ROOT = find_root(__file__)
GEN, _SOURCE, _DIGEST = load_selected_generator(TASK_ID, root=ROOT)
PROFILES = (
    "unique_distinct",
    "repeated_distinct",
    "unique_tie",
    "repeated_tie",
)


def _pairs() -> list[dict]:
    return canonical_pairs(TASK_ID, root=ROOT)


def _components(grid) -> list[dict]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append(
                {"color": color, "size": len(cells), "anchor": min(cells), "cells": cells}
            )
    return result


def _canonical_output(grid) -> list[list[int]]:
    ordered = sorted(_components(grid), key=lambda item: (-item["size"], item["color"]))
    row = [item["color"] for item in ordered for _ in range(item["size"])]
    return [row or [0]]


def _color_frequency_output(grid) -> list[list[int]]:
    counts = Counter(value for row in grid for value in row if value != 0)
    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    row = [color for color, count in ordered for _ in range(count)]
    return [row or [0]]


def _position_tiebreak_output(grid) -> list[list[int]]:
    ordered = sorted(_components(grid), key=lambda item: (-item["size"], item["anchor"]))
    row = [item["color"] for item in ordered for _ in range(item["size"])]
    return [row or [0]]


def _profile_from_pixels(grid) -> str:
    parts = _components(grid)
    repeated = len({part["color"] for part in parts}) < len(parts)
    tied = len({part["size"] for part in parts}) < len(parts)
    return ("repeated" if repeated else "unique") + "_" + ("tie" if tied else "distinct")


def _lesson(seed: int, start: int, band: str) -> tuple[list[dict], dict]:
    pairs = []
    for offset in range(4):
        grid = GEN.generate(seed, start + offset, difficulty=band)
        pairs.append({"input": grid, "output": _canonical_output(grid)})
    return pairs[:3], pairs[3]


def test_rule_pin_and_canonical_pairs_are_exact() -> None:
    assert GEN.RULE_HASH == "cbb04236ecda"
    pairs = _pairs()
    assert len(pairs) == 5
    for pair in pairs:
        original = deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert _canonical_output(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_strict_canonical_predicate_owns_every_canonical_input() -> None:
    for pair in _pairs():
        assert GEN.strict_canonical_like(pair["input"]) == []


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", PROFILES)
def test_exact_overrides_are_realized_in_every_band(band, profile) -> None:
    options = {"grid_h": 16, "grid_w": 18, "scene_profile": profile}
    grid = GEN.generate(17, 9, difficulty=band, **options)
    assert GEN.self_check(grid) == []
    assert (len(grid), len(grid[0])) == (16, 18)
    assert _profile_from_pixels(grid) == profile
    assert GEN.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo": 1},
        {"grid_h": 7},
        {"grid_h": 17},
        {"grid_w": 10},
        {"grid_w": 19},
        {"grid_h": True},
        {"grid_h": 8.0},
        {"grid_w": "12"},
        {"scene_profile": "unknown"},
        {"scene_profile": 3},
    ],
)
def test_invalid_overrides_are_rejected(kwargs) -> None:
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **kwargs)


@pytest.mark.parametrize(
    "seed,sample_index,difficulty",
    [
        (True, 0, None),
        (1.5, 0, None),
        (1, True, None),
        (1, -1, None),
        (1, 0, "extreme"),
    ],
)
def test_invalid_generation_coordinates_are_rejected(seed, sample_index, difficulty) -> None:
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(seed, sample_index, difficulty=difficulty)


def test_declared_schedule_covers_both_semantic_distinctions_in_every_demo_window() -> None:
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.LESSON_SCHEDULE_PERIOD == 4
    assert tuple(GEN.SCHEDULE_PROFILES) == PROFILES
    for band in (None, "easy", "medium", "hard"):
        assert [GEN.schedule_profile(999, i, band) for i in range(8)] == list(PROFILES) * 2
    for start in range(4):
        demos = [PROFILES[(start + offset) % 4] for offset in range(3)]
        assert any(name.startswith("repeated_") for name in demos)
        assert any(name.endswith("_tie") for name in demos)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", ["repeated_distinct", "repeated_tie"])
def test_repeated_color_profiles_refute_color_frequency_aggregation(band, profile) -> None:
    grid = GEN.generate(101, 7, difficulty=band, scene_profile=profile)
    assert GEN.self_check(grid) == []
    assert _canonical_output(grid) != _color_frequency_output(grid)
    assert GEN.SEMANTIC_WITNESSES["disconnected_same_color"](grid)
    assert GEN.SEMANTIC_RIVALS["color_frequency_aggregate"](grid) == _color_frequency_output(grid)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", ["unique_tie", "repeated_tie"])
def test_tie_profiles_refute_position_tiebreak(band, profile) -> None:
    grid = GEN.generate(203, 11, difficulty=band, scene_profile=profile)
    assert GEN.self_check(grid) == []
    assert _canonical_output(grid) != _position_tiebreak_output(grid)
    assert GEN.SEMANTIC_WITNESSES["equal_area_color_tiebreak"](grid)
    assert GEN.SEMANTIC_RIVALS["position_tiebreak"](grid) == _position_tiebreak_output(grid)


def test_declared_canonical_shortcut_really_fits_all_canonical_pairs() -> None:
    shortcut = GEN.CANONICAL_SHORTCUTS["color_frequency_aggregate"]
    assert all(shortcut(pair["input"]) == pair["output"] for pair in _pairs())
    # The canonical examples already refute the weaker position-based tie-break.
    assert any(_position_tiebreak_output(pair["input"]) != pair["output"] for pair in _pairs())


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("start", range(4))
def test_every_scheduled_three_demo_lesson_is_identifiable(band, start) -> None:
    demos, query = _lesson(412, start, band)
    assert GEN.lesson_identifiable(demos, query) == []
    for rival in GEN.LESSON_COMPETITORS.values():
        assert any(rival(pair["input"]) != pair["output"] for pair in demos)


@pytest.mark.parametrize("profile", PROFILES)
def test_generated_outputs_preserve_canonical_reshape_relation(profile) -> None:
    for width in range(11, 19):
        grid = GEN.generate(733 + width, width, grid_w=width, scene_profile=profile)
        assert len(_canonical_output(grid)[0]) > width


def test_pinned_profile_census_has_exact_canonical_support_in_every_band() -> None:
    canonical_profiles = {
        (8, 12, 5),
        (9, 11, 4),
        (8, 13, 4),
        (10, 12, 4),
        (9, 12, 5),
    }
    for band in ("easy", "medium", "hard"):
        hits = 0
        for index in range(20):
            digest = hashlib.sha256(
                f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
            ).hexdigest()
            seed = int(digest[:12], 16)
            grid = GEN.generate(seed, seed % 7919 + index, difficulty=band)
            profile = (len(grid), len(grid[0]), len({v for row in grid for v in row}))
            hits += profile in canonical_profiles
        assert hits >= 1, f"{band} had no exact canonical profile"


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_generated_distribution_is_deterministic_complete_and_valid(band) -> None:
    profiles: set[str] = set()
    shapes: set[tuple[int, int]] = set()
    component_sizes: set[tuple[int, ...]] = set()
    for index in range(96):
        grid = GEN.generate(9000 + index, index * 7, difficulty=band)
        assert grid == GEN.generate(9000 + index, index * 7, difficulty=band)
        assert GEN.self_check(grid) == []
        parts = _components(grid)
        assert len(parts) == 4  # constructive placement must never silently drop one
        assert 8 <= len(grid) <= 16
        assert 11 <= len(grid[0]) <= 18
        assert sum(part["size"] for part in parts) <= 28
        assert _canonical_output(grid) == GEN.rule_mirror(grid)
        profiles.add(_profile_from_pixels(grid))
        shapes.add((len(grid), len(grid[0])))
        component_sizes.add(tuple(sorted(part["size"] for part in parts)))
    assert profiles == set(PROFILES)
    assert len(shapes) >= 12
    assert len(component_sizes) >= 12


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True, 0]], [[10]], [[-1]]],
)
def test_malformed_grids_are_diagnostic_not_exceptions(grid) -> None:
    assert GEN.self_check(grid)
