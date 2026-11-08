"""Regression suite for the partial-plus completion generator."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import itertools
from pathlib import Path
import random
import sys

import pytest

TASK_ID = "fc999420d3aa"
HOME = Path(__file__).resolve().parents[1]


def _find_repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "shared" / "runtime" / "reviewer_support.py").is_file():
            return parent
    raise RuntimeError("could not locate portable repository root")


REPO = _find_repo_root()
sys.path.insert(0, str(REPO / "shared" / "runtime"))

from reviewer_support import canonical_pairs, find_root  # noqa: E402


def _load_generator():
    path = HOME / "generator.py"
    spec = importlib.util.spec_from_file_location(f"reviewed_{TASK_ID}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()
ROOT = find_root(__file__)
CANONICAL_PROFILES = {(5, 7, 2), (6, 9, 2), (9, 9, 3)}
BANDS = (None, "easy", "medium", "hard")


def _pair(grid):
    return {"input": deepcopy(grid), "output": gen.rule_mirror(grid)}


def _profile_floor_seed(band: str, index: int) -> int:
    digest = hashlib.sha256(
        f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def _target_colors(grid):
    return [grid[r][c] for r, c, _missing in gen._firing_centers(grid)]


def test_contract_is_pinned_and_exposes_only_observable_exact_axes():
    assert gen.GENERATOR_ID == TASK_ID
    assert gen.TASK_ID == TASK_ID
    assert gen.RULE_HASH == "75975e426e4b"
    assert gen.EXAMPLES_NEEDED == 3
    assert set(gen.AXES) == {"grid_h", "grid_w", "n_motifs"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


def test_canonical_inputs_are_accepted_and_python_mirror_matches_authority():
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 3
    for pair in pairs:
        original = deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_audited_duplicate_color_seed_now_has_distinct_target_colors():
    grid = gen.generate(810_027, 27, difficulty="easy")
    colors = _target_colors(grid)
    assert len(colors) == 2
    assert len(set(colors)) == len(colors)


@pytest.mark.parametrize("difficulty", BANDS)
def test_all_exact_axis_boundary_combinations_round_trip(difficulty):
    for grid_h, grid_w, n_motifs in itertools.product((5, 18), (5, 20), (1, 2)):
        requested = {
            "grid_h": grid_h,
            "grid_w": grid_w,
            "n_motifs": n_motifs,
        }
        grid = gen.generate(221, 17, difficulty=difficulty, **requested)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert gen.observe_overrides(grid) == requested
        assert len(set(_target_colors(grid))) == n_motifs


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo_axis", 1),
        ("grid_h", 4),
        ("grid_h", 19),
        ("grid_w", 4),
        ("grid_w", 21),
        ("n_motifs", 0),
        ("n_motifs", 3),
        ("grid_h", True),
        ("grid_w", 8.0),
        ("n_motifs", "2"),
    ],
)
def test_invalid_overrides_reject_loudly(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
def test_pinned_profile_floor_has_exact_support_in_every_band(band):
    profiles = set()
    for index in range(20):
        seed = _profile_floor_seed(band, index)
        grid = gen.generate(seed, seed % 7919 + index, difficulty=band)
        profiles.add((len(grid), len(grid[0]), len({v for row in grid for v in row})))
    assert profiles & CANONICAL_PROFILES


@pytest.mark.parametrize("difficulty", BANDS)
def test_every_sliding_three_demo_window_and_rotation_is_identifiable(difficulty):
    for start in range(9):
        pairs = [
            _pair(gen.generate(51_000 + start, start + offset, difficulty=difficulty))
            for offset in range(4)
        ]
        assert gen.lesson_identifiable(pairs[:3], pairs[3]) == []
        for query_index in range(4):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert gen.lesson_identifiable(demos, pairs[query_index]) == []


def test_decisive_profiles_refute_each_declared_rival():
    for profile_index in (1, 2):
        grid = gen.generate(61_000 + profile_index, profile_index, difficulty="medium")
        truth = gen.rule_mirror(grid)
        assert gen.SEMANTIC_WITNESSES["non_down_missing_arm"](grid)
        assert gen.SEMANTIC_WITNESSES["multiple_targets"](grid)
        assert gen.SEMANTIC_WITNESSES["two_arm_decoy"](grid)
        for rival in gen.SEMANTIC_RIVALS.values():
            assert rival(grid) != truth


def test_generation_is_deterministic_fresh_and_global_rng_neutral():
    random.seed(8675309)
    before = random.getstate()
    first = gen.generate(777, 13, difficulty="hard")
    after = random.getstate()
    second = gen.generate(777, 13, difficulty="hard")

    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))

    first[0][0] = 9
    assert gen.generate(777, 13, difficulty="hard") == second
