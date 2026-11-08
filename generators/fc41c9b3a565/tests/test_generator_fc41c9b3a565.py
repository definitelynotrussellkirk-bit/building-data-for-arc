from __future__ import annotations

import copy
import importlib.util
import os
from pathlib import Path
import random

import pytest
from reviewer_support import canonical_pairs, find_root

TASK_ID = "fc41c9b3a565"
PROFILES = (
    "pair_1sym_1asym",
    "trio_2sym_1asym",
    "trio_1sym_2asym",
    "quartet_1sym_3asym",
)
TASK_HOME = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("GENERATOR_UNDER_TEST", TASK_HOME / "generator.py"))


def _load_generator():
    spec = importlib.util.spec_from_file_location(f"review_{TASK_ID}", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _canonical_pairs():
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def _objects(grid):
    errors, analysis = gen._analyze_grid(grid)
    assert errors == []
    assert analysis is not None
    return analysis["objects"]


def _replace_component(grid, obj, new_shape):
    out = copy.deepcopy(grid)
    for r, c in obj["cells"]:
        out[r][c] = 0
    height, width = len(out), len(out[0])
    shape_h = max(r for r, _ in new_shape) + 1
    shape_w = max(c for _, c in new_shape) + 1
    preferred = (min(r for r, _ in obj["cells"]), min(c for _, c in obj["cells"]))
    candidates = [preferred] + [
        (top, left)
        for top in range(height - shape_h + 1)
        for left in range(width - shape_w + 1)
        if (top, left) != preferred
    ]
    for top, left in candidates:
        cells = [(top + dr, left + dc) for dr, dc in new_shape]
        if all(out[r][c] == 0 for r, c in cells):
            for r, c in cells:
                out[r][c] = obj["color"]
            return out
    raise AssertionError("replacement shape does not fit without overlap")


def test_rule_hash_and_exact_axis_contract_are_pinned():
    assert gen.RULE_HASH == "735d17bb2ca5"
    assert tuple(gen._PROFILE_OPTIONS) == PROFILES
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert set(gen.AXES) == {"grid_h", "grid_w", "scene_profile"}


def test_all_canonical_inputs_and_outputs_are_owned():
    pairs = _canonical_pairs()
    assert len(pairs) == 4
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("height", [6, 10])
@pytest.mark.parametrize("width", [6, 10])
@pytest.mark.parametrize("profile", PROFILES)
def test_declared_override_boundaries_are_exact_and_observable(
    band, height, width, profile
):
    grid = gen.generate(
        431,
        7,
        difficulty=band,
        grid_h=height,
        grid_w=width,
        scene_profile=profile,
    )
    assert gen.observe_overrides(grid) == {
        "grid_h": height,
        "grid_w": width,
        "scene_profile": profile,
    }
    assert gen.self_check(grid) == []


def test_unknown_overrides_fail_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 1, bogus_axis=3)


def test_default_schedule_has_exact_anchors_and_shortcut_rebuttals():
    anchors = [gen.generate(0, index, difficulty="hard") for index in (0, 5, 10)]
    assert all(gen.strict_canonical_like(grid) == [] for grid in anchors)
    assert {
        gen.observe_overrides(grid)["scene_profile"] for grid in anchors
    } == {
        "quartet_1sym_3asym",
        "trio_2sym_1asym",
        "trio_1sym_2asym",
    }

    for band in ("easy", "medium", "hard"):
        for sample_index in (1, 2, 3, 4):
            grid = gen.generate(19, sample_index, difficulty=band)
            for name in (
                "point_only_object_kept",
                "axis_reflection_shortcuts_rebutted",
                "canonical_prototype_memorization_rebutted",
                "largest_object_shortcut_rebutted",
                "left_half_position_shortcut_rebutted",
                "aspect_ratio_shortcut_rebutted",
            ):
                assert gen.SEMANTIC_WITNESSES[name](grid), (band, sample_index, name)


def test_self_check_rejects_targeted_structural_impostors():
    grid = gen.generate(
        97, 1, difficulty="easy", scene_profile="pair_1sym_1asym"
    )
    objects = _objects(grid)
    symmetric = next(obj for obj in objects if obj["rot180_symmetric"])
    asymmetric = next(obj for obj in objects if not obj["rot180_symmetric"])

    no_asymmetric = _replace_component(grid, asymmetric, gen._SQUARE)
    assert any("asymmetric" in message for message in gen.self_check(no_asymmetric))

    no_symmetric = _replace_component(grid, symmetric, gen._LR_ONLY_T5)
    assert any("180-symmetric" in message for message in gen.self_check(no_symmetric))

    split_color = copy.deepcopy(grid)
    source_r, source_c = symmetric["cells"][0]
    split_color[source_r][source_c] = 0
    isolated = next(
        (r, c)
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if split_color[r][c] == 0
        and all(
            not (0 <= r + dr < len(grid) and 0 <= c + dc < len(grid[0]))
            or split_color[r + dr][c + dc] != symmetric["color"]
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
        )
    )
    split_color[isolated[0]][isolated[1]] = symmetric["color"]
    assert any("disconnected" in message for message in gen.self_check(split_color))

    singleton = copy.deepcopy(grid)
    for r, c in asymmetric["cells"]:
        singleton[r][c] = 0
    r, c = asymmetric["cells"][0]
    singleton[r][c] = asymmetric["color"]
    assert any("singleton" in message for message in gen.self_check(singleton))

    bad_dimensions = [row[:5] for row in grid]
    assert any("width" in message for message in gen.self_check(bad_dimensions))


def test_negative_recombination_is_rejected_but_oracle_remains_executable():
    grid = gen.generate(
        211, 1, difficulty="easy", scene_profile="pair_1sym_1asym"
    )
    objects = _objects(grid)
    asymmetric = next(obj for obj in objects if not obj["rot180_symmetric"])
    impostor = _replace_component(grid, asymmetric, gen._SQUARE)
    assert gen.self_check(impostor)
    assert gen.rule_mirror(impostor) == gen.rule_mirror(copy.deepcopy(impostor))


def test_deterministic_fresh_and_global_rng_pure():
    random.seed(811)
    state = random.getstate()
    first = gen.generate(8, 3, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(8, 3, difficulty="hard")
    assert first == second
    assert first is not second
    first[0][0] = 9 if first[0][0] != 9 else 0
    assert second == gen.generate(8, 3, difficulty="hard")


def test_four_consecutive_examples_identify_named_rivals():
    demos = []
    for sample_index in range(4):
        grid = gen.generate(323, sample_index, difficulty="medium")
        demos.append({"input": grid, "output": gen.rule_mirror(grid)})
    query_grid = gen.generate(323, 4, difficulty="medium")
    query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
    assert gen.lesson_identifiable(demos, query) == []


def test_general_scenes_rebut_position_and_geometry_shortcuts():
    for band in ("easy", "medium", "hard"):
        for seed in range(8):
            for sample_index in (1, 2, 3, 4, 6, 7, 8, 9):
                grid = gen.generate(7000 + seed, sample_index, difficulty=band)
                objects = _objects(grid)
                symmetric = {
                    (obj["cell_count"], obj["bbox_h"], obj["bbox_w"])
                    for obj in objects
                    if obj["rot180_symmetric"]
                }
                asymmetric = {
                    (obj["cell_count"], obj["bbox_h"], obj["bbox_w"])
                    for obj in objects
                    if not obj["rot180_symmetric"]
                }
                assert symmetric & asymmetric
                assert gen.SEMANTIC_WITNESSES[
                    "left_half_position_shortcut_rebutted"
                ](grid)
                assert gen.SEMANTIC_WITNESSES[
                    "aspect_ratio_shortcut_rebutted"
                ](grid)


def test_canonical_anchor_schedule_meets_strict_profile_floor():
    for band in ("easy", "medium", "hard"):
        grids = [gen.generate(83, index, difficulty=band) for index in range(60)]
        strict = sum(gen.strict_canonical_like(grid) == [] for grid in grids)
        assert strict >= 12


def _load_semantic_probe():
    source = TASK_HOME / "workspace" / "semantic_probe.py"
    spec = importlib.util.spec_from_file_location(f"probe_{TASK_ID}", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import semantic probe from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_workspace_semantic_probe_reports_profiles_witnesses_and_rotations():
    probe = _load_semantic_probe()
    report = probe.run_probe(
        gen,
        seeds=(1301,),
        per_band=5,
        lesson_starts=2,
    )
    assert report["task_id"] == TASK_ID
    assert report["parameters"] == {
        "seeds": [1301],
        "per_band": 5,
        "lesson_starts": 2,
        "demonstrations": 4,
    }
    for band in ("easy", "medium", "hard"):
        section = report["bands"][band]
        assert section["draws"] == 5
        assert section["self_check_failures"] == []
        assert section["strict_canonical_count"] >= 1
        assert set(section["profiles"]) == set(PROFILES)
        assert all(count > 0 for count in section["witness_counts"].values())
    assert report["lessons"]["production_failures"] == []
    assert report["lessons"]["rotation_failures"] == []
