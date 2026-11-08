"""Task-local regression suite for generator 6347dcb736b5."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import itertools
import os
from pathlib import Path
import random
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
sys.path.insert(0, str(ROOT / "shared/runtime"))
sys.path.insert(0, str(HOME / "workspace"))

from reviewer_support import canonical_pairs, find_root  # noqa: E402
import reference_probe as oracle  # noqa: E402

GEN_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))


def _load_generator(path: Path = GEN_PATH):
    spec = importlib.util.spec_from_file_location("generator_under_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()
BANDS = (None, "easy", "medium", "hard")
PAIRS = canonical_pairs("6347dcb736b5", root=find_root(__file__))
CANONICAL_PROFILES = {(6, 9, 3), (8, 9, 3), (8, 10, 4)}


def _profile_floor_seed(band: str, index: int) -> int:
    digest = hashlib.sha256(
        f"profile-floor:v1:6347dcb736b5:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def test_rule_pin_and_all_canonical_pairs():
    assert gen.RULE_HASH == "6bba75bb466d"
    assert len(PAIRS) == 3
    for pair in PAIRS:
        input_grid = pair["input"]
        assert gen.self_check(input_grid) == []
        assert gen.strict_canonical_like(input_grid) == []
        assert gen.rule_mirror(input_grid) == pair["output"]
        assert oracle.oracle(input_grid) == pair["output"]


def test_canonical_pairs_refute_fill_and_overlay_but_fit_global_color_shortcut():
    assert any(oracle.fill_bbox(pair["input"]) != pair["output"] for pair in PAIRS)
    assert any(oracle.outline_over_input(pair["input"]) != pair["output"] for pair in PAIRS)
    assert all(oracle.global_color_bbox(pair["input"]) == pair["output"] for pair in PAIRS)
    assert set(gen.CANONICAL_SHORTCUTS) == {"global_color_bbox"}
    assert all(
        gen.CANONICAL_SHORTCUTS["global_color_bbox"](pair["input"]) == pair["output"]
        for pair in PAIRS
    )


@pytest.mark.parametrize("band", BANDS)
def test_exact_override_domain_corners_round_trip_in_every_band(band):
    for height, width, n_blobs in itertools.product((6, 14), (9, 16), (2, 5)):
        requested = {"grid_h": height, "grid_w": width, "n_blobs": n_blobs}
        for seed in range(4):
            grid = gen.generate(seed, 17, difficulty=band, **requested)
            assert gen.self_check(grid) == [], (band, requested, seed)
            assert gen.observe_overrides(grid) == requested
            assert oracle.facts(grid)["n_objects"] == n_blobs


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo_axis", 1),
        ("grid_h", 5),
        ("grid_h", 15),
        ("grid_w", 8),
        ("grid_w", 17),
        ("n_blobs", 1),
        ("n_blobs", 6),
        ("grid_h", True),
        ("grid_w", 10.0),
        ("n_blobs", "3"),
    ],
)
def test_invalid_overrides_reject_loudly(key, value):
    with pytest.raises(ValueError):
        gen.generate(1, 0, **{key: value})


@pytest.mark.parametrize("band", BANDS)
def test_every_generated_grid_contains_a_decisive_outline_witness(band):
    for index in range(180):
        grid = gen.generate(10_000 + index, index * 7 + 3, difficulty=band)
        assert gen.self_check(grid) == [], (band, index)
        assert grid == gen.generate(10_000 + index, index * 7 + 3, difficulty=band)
        facts = oracle.facts(grid)
        assert 2 <= facts["n_objects"] <= 5
        assert facts["hollow_bboxes"] >= 1
        assert facts["interior_blob_cells"] >= 1
        truth = oracle.oracle(grid)
        assert truth == gen.rule_mirror(grid)
        assert oracle.fill_bbox(grid) != truth
        assert oracle.outline_over_input(grid) != truth


@pytest.mark.parametrize("band", BANDS)
def test_distribution_retains_canonical_profiles_and_broad_support(band):
    grids = [gen.generate(20_000 + index, index, difficulty=band) for index in range(180)]
    profiles = {oracle.profile_signature(grid) for grid in grids}
    counts = {oracle.facts(grid)["n_objects"] for grid in grids}
    dimensions = {(len(grid), len(grid[0])) for grid in grids}
    assert profiles & CANONICAL_PROFILES
    assert counts == {2, 3, 4, 5}
    assert len(dimensions) >= 16


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
def test_pinned_profile_floor_has_exact_support_in_every_band(band):
    profiles = set()
    for index in range(20):
        seed = _profile_floor_seed(band, index)
        grid = gen.generate(seed, seed % 7919 + index, difficulty=band)
        profiles.add(oracle.profile_signature(grid))
    assert profiles & CANONICAL_PROFILES


def test_default_axes_are_observable_and_replay_exactly():
    for band in BANDS:
        for index in range(80):
            grid = gen.generate(30_000 + index, index * 13, difficulty=band)
            observed = gen.observe_overrides(grid)
            assert gen.generate(30_000 + index, index * 13, difficulty=band, **observed) == grid


def test_declared_rivals_fail_generated_witnesses_with_honest_canonical_claims():
    assert set(gen.SEMANTIC_RIVALS) >= {
        "fill_bbox",
        "outline_over_input",
        "global_color_bbox",
    }
    for index in range(24):
        grid = gen.generate(40_000, index)
        truth = oracle.oracle(grid)
        assert gen.SEMANTIC_WITNESSES["interior_erasure"](grid)
        for rival_name in gen.WITNESS_RIVALS["interior_erasure"]:
            assert gen.SEMANTIC_RIVALS[rival_name](grid) != truth


@pytest.mark.parametrize("band", BANDS)
def test_repeated_color_schedule_refutes_global_color_shortcut_in_every_lesson_rotation(band):
    for start in range(12):
        pairs = []
        for offset in range(4):
            grid = gen.generate(45_000 + start, start + offset, difficulty=band)
            pairs.append({"input": grid, "output": oracle.oracle(grid)})
        for query_index in range(4):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert any(
                oracle.facts(pair["input"])["has_repeated_component_color"]
                for pair in demos
            ), (band, start, query_index)
            assert gen.lesson_identifiable(demos, pairs[query_index]) == []


def test_every_three_demo_lesson_refutes_declared_rivals():
    for band in BANDS:
        for start in range(12):
            pairs = []
            for offset in range(4):
                grid = gen.generate(50_000 + start, start + offset, difficulty=band)
                pairs.append({"input": grid, "output": oracle.oracle(grid)})
            assert gen.lesson_identifiable(pairs[:3], pairs[3]) == []


def test_self_check_rejects_minimal_and_structural_impostors():
    impostors = {
        "all_background": [[0] * 9 for _ in range(6)],
        "full_one_color": [[4] * 9 for _ in range(6)],
        "singleton": [[4 if (r, c) == (2, 2) else 0 for c in range(9)] for r in range(6)],
        "short_line": [[4 if r == 2 and 2 <= c <= 5 else 0 for c in range(9)] for r in range(6)],
        "solid_2x2": [[4 if 1 <= r <= 2 and 1 <= c <= 2 else 0 for c in range(9)] for r in range(6)],
    }
    for name, grid in impostors.items():
        assert gen.self_check(grid), name

    duplicate_color = gen.generate(61, 2, n_blobs=2)
    components = oracle.objects(duplicate_color)
    old_color = components[1]["color"]
    new_color = components[0]["color"]
    for row, col in components[1]["cells"]:
        assert duplicate_color[row][col] == old_color
        duplicate_color[row][col] = new_color
    assert gen.self_check(duplicate_color) == []
    assert oracle.global_color_bbox(duplicate_color) != oracle.oracle(duplicate_color)

    triple_duplicate = gen.generate(62, 2, n_blobs=3)
    components = oracle.objects(triple_duplicate)
    new_color = components[0]["color"]
    for component in components[1:]:
        for row, col in component["cells"]:
            triple_duplicate[row][col] = new_color
    assert gen.self_check(triple_duplicate)


def test_generation_is_fresh_and_global_rng_neutral():
    random.seed(123456)
    state = random.getstate()
    first = gen.generate(77, 9, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(77, 9, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    changed = copy.deepcopy(first)
    changed[0][0] = (changed[0][0] + 1) % 10
    assert changed != second
