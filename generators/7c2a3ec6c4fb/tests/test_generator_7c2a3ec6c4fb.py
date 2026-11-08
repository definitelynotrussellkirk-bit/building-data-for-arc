from __future__ import annotations

import copy
import importlib.util
import json
import random
import sys
from collections import Counter
from pathlib import Path

import pytest


TASK_ID = "7c2a3ec6c4fb"
ROOT = Path(__file__).resolve().parents[3]
RUNTIME = ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

MODULE_PATH = ROOT / "generators" / TASK_ID / "generator.py"
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", MODULE_PATH)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def canonical_pairs():
    pairs = []
    with (ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            for split in ("train", "test"):
                value = row.get(split, [])
                if isinstance(value, dict):
                    value = [value]
                pairs.extend(value)
    return pairs


def frozen(grid):
    return tuple(tuple(row) for row in grid)


def test_rule_hash_canonical_acceptance_and_python_mirror_parity():
    assert GEN.RULE_HASH == "38ad2c645d79"
    pairs = canonical_pairs()
    assert len(pairs) == 4
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_default_distribution_teaches_multiple_repeated_classes(difficulty):
    exact_profiles = set()
    for index in range(180):
        grid = GEN.generate(10_000 + index, index, difficulty=difficulty)
        facts = GEN.semantic_observables(grid)
        assert facts["valid"], facts["errors"]
        assert facts["singleton_pattern_classes"] == 1
        assert facts["repeated_pattern_classes"] >= 2
        assert facts["component_count"] == 2 * facts["repeated_pattern_classes"] + 1
        assert facts["multiplicities"] == (1,) + (2,) * facts["repeated_pattern_classes"]
        assert not facts["bbox_overlap"]
        assert GEN.rule_mirror(grid) == facts["output"]
        exact_profiles.add((len(grid), len(grid[0]), len({v for row in grid for v in row})))
    # Every difficulty band must retain a literal canonical morphology anchor.
    assert exact_profiles & {(11, 11, 4), (12, 12, 5), (13, 13, 4), (13, 13, 5)}


def test_sparse_bbox_overlap_regression_is_gone():
    grid = GEN.generate("probe", 3113)
    facts = GEN.semantic_observables(grid)
    assert facts["valid"], facts["errors"]
    assert not facts["bbox_overlap"]
    assert facts["singleton_pattern_classes"] == 1
    assert facts["repeated_pattern_classes"] >= 2


def test_self_check_names_bbox_contamination_failure():
    # Four components are 8-separated, but the lower two have overlapping
    # bounding boxes. Cropping from the whole grid therefore contaminates one
    # object with a cell belonging to the other.
    contaminated = [
        [0, 0, 0, 0, 0, 4, 1, 4, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 4, 4, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 4, 0, 0, 0, 0, 0, 3, 3, 4, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 3, 3, 4, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 3, 3, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0] * 15,
        [0] * 15,
    ]
    errors = GEN.self_check(contaminated)
    assert any("bounding box" in error for error in errors), errors


def test_declared_shortcut_reproduces_all_canonical_pairs_but_generated_witnesses_refute_it():
    palette_shortcut = GEN.CANONICAL_SHORTCUTS["unique_color_signature"]
    for pair in canonical_pairs():
        assert palette_shortcut(pair["input"]) == pair["output"]

    for difficulty in ("easy", "medium", "hard"):
        hits = 0
        for index in range(180):
            grid = GEN.generate(20_000 + index, index, difficulty=difficulty)
            if GEN.SEMANTIC_WITNESSES["shared_color_signature_counterexample"](grid):
                hits += 1
                assert palette_shortcut(grid) != GEN.rule_mirror(grid)
        assert hits >= 90


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_geometry_only_shortcut_gets_many_direct_counterexamples(difficulty):
    rival = GEN.SEMANTIC_RIVALS["unique_geometry_signature"]
    hits = 0
    for index in range(180):
        grid = GEN.generate(30_000 + index, index, difficulty=difficulty)
        if GEN.SEMANTIC_WITNESSES["same_geometry_different_colors"](grid):
            hits += 1
            assert rival(grid) != GEN.rule_mirror(grid)
    assert hits >= 45


@pytest.mark.parametrize("scene_profile", [
    "square11_c3", "square12_c4", "square13_c3", "square13_c4",
])
@pytest.mark.parametrize("n_pairs", [2, 4])
@pytest.mark.parametrize("pattern_profile", ["color_swap", "shape_shift", "mixed_signature"])
def test_every_override_boundary_and_branch_is_lawful(
    scene_profile, n_pairs, pattern_profile,
):
    grid = GEN.generate(
        40_000,
        n_pairs,
        difficulty="hard",
        scene_profile=scene_profile,
        n_pairs=n_pairs,
        pattern_profile=pattern_profile,
    )
    assert GEN.self_check(grid) == []
    facts = GEN.semantic_observables(grid)
    assert facts["repeated_pattern_classes"] == n_pairs
    assert facts["scene_profile"] == scene_profile
    assert facts["pattern_profile"] == pattern_profile
    assert GEN.observe_overrides(grid) == {
        "scene_profile": scene_profile,
        "n_pairs": n_pairs,
        "pattern_profile": pattern_profile,
    }


@pytest.mark.parametrize("kwargs", [
    {"difficulty": "extreme"},
    {"scene_profile": "unknown"},
    {"n_pairs": 1},
    {"n_pairs": 5},
    {"pattern_profile": "unknown"},
    {"__override_contract_unknown_axis__": 1},
])
def test_invalid_controls_fail_closed(kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 0, **kwargs)


def test_axis_contract_is_literal_minimal_and_live():
    assert set(GEN.AXES) == {
        "scene_profile", "n_pairs", "pattern_profile"
    }
    assert GEN.HELPFUL_TEXTURES == GEN.DEGENERATE_TEXTURES == ()

    controls = {
        "scene_profile": ("square11_c3", "square13_c4"),
        "n_pairs": (2, 4),
        "pattern_profile": ("color_swap", "shape_shift"),
    }
    for axis, (left, right) in controls.items():
        assert any(
            GEN.generate(50_000 + seed, seed, **{axis: left})
            != GEN.generate(50_000 + seed, seed, **{axis: right})
            for seed in range(12)
        ), axis


def test_deterministic_fresh_and_global_rng_independent():
    random.seed(918273)
    state = random.getstate()
    first = GEN.generate(61, 7, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(61, 7, difficulty="hard")
    assert first == second
    assert first is not second and first[0] is not second[0]
    frozen_second = frozen(second)
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert frozen(GEN.generate(61, 7, difficulty="hard")) == frozen_second


def test_generated_pool_is_diverse_without_reintroducing_palette_shortcut():
    grids = [GEN.generate(70_000 + i, i) for i in range(240)]
    outputs = [GEN.rule_mirror(grid) for grid in grids]
    assert len({frozen(grid) for grid in grids}) >= 220
    assert len({frozen(output) for output in outputs}) >= 120
    assert {len(GEN.semantic_observables(grid)["components"]) for grid in grids} == {5, 7, 9}
    assert all(
        not GEN.semantic_observables(grid)["singleton_has_exclusive_color"]
        for grid in grids
    )


def _old_lattice_origins(size: int, height: int, width: int):
    starts = (0, (size - 3) // 2, size - 3)
    return {
        (zone_row + row_jitter, zone_col + col_jitter)
        for zone_row in starts
        for zone_col in starts
        for row_jitter in range(max(0, 4 - height))
        for col_jitter in range(max(0, 4 - width))
    }


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_answer_color_cardinality_covers_monochrome_and_multicolor(difficulty):
    observed = set()
    for index in range(360):
        grid = GEN.generate(
            f"answer-color-cardinality:{difficulty}",
            index,
            difficulty=difficulty,
        )
        facts = GEN.semantic_observables(grid)
        observed.add(len(facts["singleton"]["colors"]))
    assert observed == {1, 2}


def test_sparse_scenes_cover_canonical_long_answer_crops():
    dimensions = set()
    for index in range(720):
        grid = GEN.generate(
            "long-answer-crops",
            index,
            n_pairs=2,
        )
        singleton = GEN.semantic_observables(grid)["singleton"]
        dimensions.add((len(singleton["crop"]), len(singleton["crop"][0])))
    assert any(max(height, width) >= 4 for height, width in dimensions), dimensions


def test_sparse_layouts_escape_the_old_three_by_three_lattice():
    eligible = 0
    escaped = 0
    for index in range(360):
        grid = GEN.generate(
            "free-layout",
            index,
            n_pairs=2,
        )
        singleton = GEN.semantic_observables(grid)["singleton"]
        height = len(singleton["crop"])
        width = len(singleton["crop"][0])
        if height > 3 or width > 3:
            continue
        eligible += 1
        origin = singleton["bbox"][:2]
        if origin not in _old_lattice_origins(len(grid), height, width):
            escaped += 1
    assert eligible >= 200
    assert escaped >= eligible // 4


@pytest.mark.parametrize(
    ("rival_name", "witness_name"),
    [
        ("unique_color_histogram", "shared_color_histogram_counterexample"),
        (
            "unique_geometry_and_colors",
            "shared_geometry_color_counterexample",
        ),
        (
            "unique_bbox_and_histogram",
            "shared_bbox_histogram_counterexample",
        ),
    ],
)
def test_additional_canonical_perfect_shortcuts_are_declared_and_refuted(
    rival_name, witness_name,
):
    assert rival_name in GEN.CANONICAL_SHORTCUTS
    rival = GEN.CANONICAL_SHORTCUTS[rival_name]
    for pair in canonical_pairs():
        assert rival(pair["input"]) == pair["output"]

    assert witness_name in GEN.SEMANTIC_WITNESSES
    witness = GEN.SEMANTIC_WITNESSES[witness_name]
    hits = 0
    for index in range(360):
        grid = GEN.generate(f"shortcut:{rival_name}", index)
        if witness(grid):
            hits += 1
            assert rival(grid) != GEN.rule_mirror(grid)
    assert hits >= 120


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
@pytest.mark.parametrize("pattern_profile", GEN.PATTERN_PROFILES)
def test_pattern_profile_override_is_observable_across_gate_seed_range(
    difficulty, pattern_profile,
):
    for seed in range(30):
        sample_index = seed * 17 + 3
        grid = GEN.generate(
            seed,
            sample_index,
            difficulty=difficulty,
            pattern_profile=pattern_profile,
        )
        assert GEN.observe_overrides(grid)["pattern_profile"] == pattern_profile
