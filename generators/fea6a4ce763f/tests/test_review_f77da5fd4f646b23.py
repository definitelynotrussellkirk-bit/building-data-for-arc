"""Focused regression tests for review-f77da5fd4f646b23.

These tests cover the request-contract repair and the canonical-structure bridge
added by this review.  The inherited ``test_generator_fea6a4ce763f.py`` fixture
is intentionally left byte-for-byte unchanged.
"""
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = HOME / "generator.py"
SPEC = spec_from_file_location("review_f77da5fd4f646b23_generator", GENERATOR_PATH)
assert SPEC and SPEC.loader
GEN = module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)


def _components(grid: list[list[int]]) -> list[tuple[int, set[tuple[int, int]]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[tuple[int, set[tuple[int, int]]]] = []
    for sr in range(h):
        for sc in range(w):
            color = grid[sr][sc]
            if color == 0 or (sr, sc) in seen:
                continue
            cells = {(sr, sc)}
            stack = [(sr, sc)]
            seen.add((sr, sc))
            while stack:
                r, c = stack.pop()
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        cells.add((nr, nc))
                        stack.append((nr, nc))
            result.append((color, cells))
    return result


@pytest.mark.parametrize(
    ("sample_index", "difficulty"),
    [
        (-1, None),
        (0, True),
        (0, False),
        (0, 0),
        (0, 1.0),
        (0, "__invalid_difficulty__"),
    ],
)
def test_invalid_common_scalars_are_rejected(sample_index, difficulty):
    with pytest.raises(ValueError):
        GEN.generate(0, sample_index, difficulty=difficulty)


@pytest.mark.parametrize("helper_name", ["schedule_profile", "semantic_phase"])
def test_schedule_helpers_reject_negative_indices(helper_name):
    with pytest.raises(ValueError):
        getattr(GEN, helper_name)(0, -1, "medium")


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_tenth_split_distractor_is_a_canonical_structure_bridge(band):
    for index in (0, 10, 20):
        grid = GEN.generate(30_000 + index, index, difficulty=band)
        components = _components(grid)
        truth = GEN.rule_mirror(grid)

        assert GEN.semantic_phase(30_000 + index, index, band) == "split_distractor"
        assert len(components) == 3
        assert all(len(cells) > 1 for _, cells in components)
        assert len({value for row in grid for value in row}) == 4
        assert GEN.self_check(grid) == []

        fired = [
            name
            for name, witness in GEN.SEMANTIC_WITNESSES.items()
            if witness(grid)
        ]
        assert fired == ["split_distractor"]
        for rival_name in GEN.WITNESS_RIVALS["split_distractor"]:
            assert GEN.SEMANTIC_RIVALS[rival_name](grid) != truth


def test_bridge_supports_the_p5_profile_override_without_singletons():
    grid = GEN.generate(31_000, 0, difficulty="hard", scene_profile="canonical_9x9_p5")
    components = _components(grid)
    assert len(components) == 4
    assert all(len(cells) > 1 for _, cells in components)
    assert len({value for row in grid for value in row}) == 5
    assert GEN.observe_overrides(grid) == {"scene_profile": "canonical_9x9_p5"}
    assert GEN.self_check(grid) == []


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_split_target_phase_refutes_all_declared_color_ranking_shortcuts(band):
    grid = GEN.generate(32_001, 1, difficulty=band)
    truth = GEN.rule_mirror(grid)
    assert GEN.semantic_phase(32_001, 1, band) == "split_target"

    fired = [
        name
        for name, witness in GEN.SEMANTIC_WITNESSES.items()
        if witness(grid)
    ]
    assert fired == ["split_target"]
    expected = {
        "most_frequent_color",
        "largest_component_of_most_frequent_color",
        "second_color_when_top_disconnected",
        "largest_single_component_color",
    }
    assert expected <= set(GEN.WITNESS_RIVALS["split_target"])
    for rival_name in GEN.WITNESS_RIVALS["split_target"]:
        assert GEN.SEMANTIC_RIVALS[rival_name](grid) != truth
