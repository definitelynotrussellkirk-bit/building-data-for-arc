"""Task-local regression tests for e4cb0224ca42."""
from __future__ import annotations

import importlib.util
import itertools
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
sys.path.insert(0, str(ROOT / "shared/runtime"))
from reviewer_support import canonical_pairs, find_root  # noqa: E402

GEN_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))


def _load(path: Path = GEN_PATH):
    spec = importlib.util.spec_from_file_location("generator_under_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _component_count(grid: list[list[int]]) -> int:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    total = 0
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            total += 1
            seen.add((row, col))
            stack = [(row, col)]
            while stack:
                rr, cc = stack.pop()
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
    return total


def test_known_easy_seed_realizes_requested_rectangle_count():
    """Production change that breaks this: retry-and-drop placement."""
    gen = _load()
    grid = gen.generate(3, 0, difficulty="easy", n_rects=2)
    assert _component_count(grid) == 2


def test_self_check_accepts_every_canonical_input():
    """Production change that breaks this: requiring diagonal clearance."""
    gen = _load()
    pairs = canonical_pairs("e4cb0224ca42", root=find_root(__file__), labeled_only=True)
    for index, pair in enumerate(pairs):
        assert gen.self_check(pair["input"]) == [], index


@pytest.mark.parametrize("band", (None, "easy", "medium", "hard"))
def test_axis_corner_overrides_are_exact_in_every_band(band):
    """Production change that breaks this: band-specific override clipping."""
    gen = _load()
    for height, width, requested in itertools.product((7, 14), (9, 16), (1, 3)):
        grid = gen.generate(
            17,
            5,
            difficulty=band,
            grid_h=height,
            grid_w=width,
            n_rects=requested,
        )
        assert (len(grid), len(grid[0])) == (height, width)
        assert _component_count(grid) == requested
        assert gen.self_check(grid) == []

@pytest.mark.parametrize(
    ("kwargs", "error"),
    [
        ({"seed": True, "sample_index": 0}, TypeError),
        ({"seed": 1.0, "sample_index": 0}, TypeError),
        ({"seed": "1", "sample_index": 0}, TypeError),
        ({"seed": -1, "sample_index": 0}, ValueError),
        ({"seed": 1, "sample_index": True}, TypeError),
        ({"seed": 1, "sample_index": 0.0}, TypeError),
        ({"seed": 1, "sample_index": "0"}, TypeError),
        ({"seed": 1, "sample_index": -1}, ValueError),
        ({"seed": 1, "sample_index": 0, "difficulty": "expert"}, ValueError),
        ({"seed": 1, "sample_index": 0, "bogus_axis": 3}, ValueError),
        ({"seed": 1, "sample_index": 0, "grid_h": True}, TypeError),
        ({"seed": 1, "sample_index": 0, "grid_w": 9.0}, TypeError),
        ({"seed": 1, "sample_index": 0, "n_rects": "2"}, TypeError),
    ],
)
def test_generate_rejects_noncanonical_call_arguments(kwargs, error):
    """Production change that breaks this: coercive or swallowed inputs."""
    gen = _load()
    with pytest.raises(error):
        gen.generate(**kwargs)

def test_contract_is_small_pinned_and_observable():
    """Production change that breaks this: advertising dead or unpinned axes."""
    gen = _load()
    assert gen.RULE_HASH == "7798fb9f1ac0"
    assert gen.VERSION == "4.0.0"
    assert gen.MIN_STRICT_FRAC == 1.0
    assert gen.EXAMPLES_NEEDED == 3
    assert set(gen.AXES) == {"grid_h", "grid_w", "n_rects"}
    assert gen.HELPFUL_TEXTURES == ()
    assert gen.DEGENERATE_TEXTURES == ()
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == ()

    grid = gen.generate(19, 2, grid_h=14, grid_w=16, n_rects=3)
    assert gen.observe_overrides(grid) == {
        "grid_h": 14,
        "grid_w": 16,
        "n_rects": 3,
    }


def test_rule_mirror_matches_all_canonical_pairs():
    """Production change that breaks this: Python mirror diverging from authority."""
    gen = _load()
    pairs = canonical_pairs("e4cb0224ca42", root=find_root(__file__), labeled_only=True)
    assert len(pairs) == 4
    for index, pair in enumerate(pairs):
        assert gen.rule_mirror(pair["input"]) == pair["output"], index

@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
def test_declared_four_pair_schedule_survives_every_query_rotation(band):
    """Production change that breaks this: lucky rather than scheduled witnesses."""
    gen = _load()
    assert not hasattr(gen, "LESSON_SCHEDULE_PERIOD")
    assert tuple(gen.SCHEDULE_PROFILES) == (
        "canonical_7x9",
        "canonical_9x11",
        "canonical_8x10",
        "canonical_test_9x11",
    )
    pairs = []
    for sample_index in range(4):
        grid = gen.generate(4242, sample_index, difficulty=band)
        assert gen.schedule_profile(4242, sample_index, band) == gen.SCHEDULE_PROFILES[sample_index]
        assert gen.strict_canonical_like(grid) == []
        assert gen.observe_overrides(grid)["n_rects"] == 2
        pairs.append({"input": grid, "output": gen.rule_mirror(grid)})

    for query_index, query in enumerate(pairs):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        assert gen.lesson_identifiable(demos, query) == []
        for name, rival in gen.LESSON_COMPETITORS.items():
            assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                band,
                query_index,
                name,
            )


def test_witness_claims_are_executable_and_name_real_rivals():
    """Production change that breaks this: decorative witness metadata."""
    gen = _load()
    assert set(gen.SEMANTIC_WITNESSES) == set(gen.WITNESS_RIVALS)
    grids = [gen.generate(99, index, difficulty="medium") for index in range(4)]
    for witness_name, witness in gen.SEMANTIC_WITNESSES.items():
        hits = [grid for grid in grids if witness(grid)]
        assert hits, witness_name
        for rival_name in gen.WITNESS_RIVALS[witness_name]:
            rival = gen.SEMANTIC_RIVALS[rival_name]
            assert all(rival(grid) != gen.rule_mirror(grid) for grid in hits)

def test_difficulty_bands_are_observable_without_changing_lawfulness():
    """Production change that breaks this: a dead difficulty parameter."""
    gen = _load()
    for sample_index in range(4):
        grids = {
            band: gen.generate(8080, sample_index, difficulty=band)
            for band in ("easy", "medium", "hard")
        }
        assert len({tuple(map(tuple, grid)) for grid in grids.values()}) == 3
        assert all(gen.self_check(grid) == [] for grid in grids.values())

def test_requested_count_never_silently_underfills_seed_sweep():
    """Regression for the retained retry-and-drop counterexample."""
    gen = _load()
    for band in ("easy", "medium", "hard"):
        for requested in (1, 2, 3):
            for seed in range(256):
                grid = gen.generate(seed, 0, difficulty=band, n_rects=requested)
                assert _component_count(grid) == requested, (band, requested, seed)
                assert gen.self_check(grid) == [], (band, requested, seed)


def test_generation_is_deterministic_fresh_and_global_rng_neutral():
    """Production change that breaks this: ambient RNG or returned-grid reuse."""
    import copy
    import random

    gen = _load()
    state = random.getstate()
    first = gen.generate(9876, 3, difficulty="hard")
    pristine = copy.deepcopy(first)
    assert random.getstate() == state
    first[0][0] = 9 if first[0][0] != 9 else 8
    second = gen.generate(9876, 3, difficulty="hard")
    assert second == pristine
    assert second is not first
    assert all(left is not right for left, right in zip(first, second))
    assert random.getstate() == state


def test_self_check_rejects_targeted_shape_impostors():
    """Production change that breaks this: presence-only validation."""
    gen = _load()

    empty = [[0] * 9 for _ in range(7)]

    even = [[0] * 9 for _ in range(7)]
    for row in range(1, 5):
        for col in range(1, 4):
            even[row][col] = 2

    hollow = [[0] * 9 for _ in range(7)]
    for row in range(1, 4):
        for col in range(1, 6):
            if row in (1, 3) or col in (1, 5):
                hollow[row][col] = 2

    duplicate_colors = [[0] * 9 for _ in range(7)]
    for row0, col0 in ((0, 0), (4, 6)):
        for row in range(row0, row0 + 3):
            for col in range(col0, col0 + 3):
                duplicate_colors[row][col] = 2

    cardinal_touch = [[0] * 10 for _ in range(7)]
    for row in range(0, 3):
        for col in range(0, 3):
            cardinal_touch[row][col] = 2
    for row in range(3, 6):
        for col in range(0, 3):
            cardinal_touch[row][col] = 3

    cases = {
        "empty": empty,
        "even": even,
        "hollow": hollow,
        "duplicate_colors": duplicate_colors,
        "cardinal_touch": cardinal_touch,
    }
    assert all(gen.self_check(grid) for grid in cases.values()), {
        name: gen.self_check(grid) for name, grid in cases.items()
    }
