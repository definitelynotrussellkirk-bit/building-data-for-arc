from __future__ import annotations

import copy
import importlib
import random

import pytest
from reviewer_support import canonical_pairs, find_root

TASK_ID = "a86a630485ac"
gen = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def _canonical_pairs():
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def _objects(grid):
    errors, analysis = gen._analyze_grid(grid)
    assert errors == []
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
        if not all(0 <= r < height and 0 <= c < width for r, c in cells):
            continue
        if all(out[r][c] == 0 for r, c in cells):
            for r, c in cells:
                out[r][c] = obj["color"]
            return out
    raise AssertionError("replacement shape does not fit without overlap")


def test_rule_hash_is_pinned_to_current_normalized_authority():
    assert gen.RULE_HASH == "3cb323ae99fd"


def test_all_canonical_inputs_and_outputs_are_owned():
    pairs = _canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("height", [6, 10])
@pytest.mark.parametrize("width", [8, 12])
@pytest.mark.parametrize("profile", gen._PROFILE_OPTIONS)
def test_declared_override_boundaries_are_exact_and_observable(band, height, width, profile):
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
        "pair_1sym_1asym",
        "trio_2sym_1asym",
        "trio_1sym_2asym",
    }

    for band in ("easy", "medium", "hard"):
        grid = gen.generate(19, 1, difficulty=band)
        assert gen.SEMANTIC_WITNESSES["lr_only_object_kept"](grid)
        assert gen.SEMANTIC_WITNESSES["horizontal_only_object_erased"](grid)
        assert gen.SEMANTIC_WITNESSES["canonical_prototype_memorization_rebutted"](grid)
        assert gen.SEMANTIC_WITNESSES["largest_object_shortcut_rebutted"](grid)


def test_self_check_rejects_targeted_structural_impostors():
    pair = gen.generate(97, 1, difficulty="easy")
    objects = _objects(pair)
    symmetric = next(obj for obj in objects if obj["lr_symmetric"])
    asymmetric = next(obj for obj in objects if not obj["lr_symmetric"])

    no_asymmetric = _replace_component(pair, asymmetric, gen._SQUARE)
    assert any("asymmetric" in message for message in gen.self_check(no_asymmetric))

    no_symmetric = _replace_component(pair, symmetric, gen._HORIZONTAL_ONLY_T4)
    assert any("LR-symmetric" in message for message in gen.self_check(no_symmetric))

    split_color = copy.deepcopy(pair)
    source_r, source_c = symmetric["cells"][0]
    split_color[source_r][source_c] = 0
    isolated = next(
        (r, c)
        for r in range(len(pair))
        for c in range(len(pair[0]))
        if split_color[r][c] == 0
        and all(
            not (0 <= r + dr < len(pair) and 0 <= c + dc < len(pair[0]))
            or split_color[r + dr][c + dc] != symmetric["color"]
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
        )
    )
    split_color[isolated[0]][isolated[1]] = symmetric["color"]
    assert any("disconnected" in message for message in gen.self_check(split_color))

    singleton = copy.deepcopy(pair)
    for r, c in asymmetric["cells"]:
        singleton[r][c] = 0
    r, c = asymmetric["cells"][0]
    singleton[r][c] = asymmetric["color"]
    assert any("singleton" in message for message in gen.self_check(singleton))

    bad_dimensions = [row[:7] for row in pair]
    assert any("width" in message for message in gen.self_check(bad_dimensions))


def test_negative_recombination_is_rejected_but_oracle_remains_executable():
    grid = gen.generate(211, 1, difficulty="easy")
    objects = _objects(grid)
    asymmetric = next(obj for obj in objects if not obj["lr_symmetric"])
    impostor = _replace_component(grid, asymmetric, gen._SQUARE)
    assert gen.self_check(impostor)

    # The Racket rule's mathematical domain is broader than the teaching
    # distribution: Python mirror likewise executes deterministically even
    # though the lesson checker rejects the all-symmetric recombination.
    first = gen.rule_mirror(impostor)
    second = gen.rule_mirror(copy.deepcopy(impostor))
    assert first == second


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
    for sample_index in range(3):
        grid = gen.generate(323, sample_index, difficulty="medium")
        demos.append({"input": grid, "output": gen.rule_mirror(grid)})
    query_grid = gen.generate(323, 3, difficulty="medium")
    query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
    assert gen.lesson_identifiable(demos, query) == []


def test_general_scenes_always_rebut_left_half_position_shortcut():
    for band in ("easy", "medium", "hard"):
        for seed in range(12):
            for sample_index in (1, 2, 3, 4, 6, 7, 8, 9):
                grid = gen.generate(7000 + seed, sample_index, difficulty=band)
                assert gen.SEMANTIC_WITNESSES["left_half_position_shortcut_rebutted"](grid)


@pytest.mark.parametrize(
    "seed,start,band",
    [(3000087, 20348, "easy"), (3000177, 20708, "easy")],
)
def test_previously_ambiguous_position_lessons_are_identifiable(seed, start, band):
    demos = []
    for sample_index in range(start, start + 3):
        grid = gen.generate(seed, sample_index, difficulty=band)
        demos.append({"input": grid, "output": gen.rule_mirror(grid)})
    query_grid = gen.generate(seed, start + 3, difficulty=band)
    query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
    assert gen.lesson_identifiable(demos, query) == []


def _role_geometry_keys(grid):
    objects = _objects(grid)
    symmetric = {
        (obj["cell_count"], obj["bbox_h"], obj["bbox_w"])
        for obj in objects
        if obj["lr_symmetric"]
    }
    asymmetric = {
        (obj["cell_count"], obj["bbox_h"], obj["bbox_w"])
        for obj in objects
        if not obj["lr_symmetric"]
    }
    return symmetric, asymmetric


def test_general_scenes_rebut_aspect_ratio_with_matched_role_geometry():
    assert "keep_wide_or_square_objects" in gen.SEMANTIC_RIVALS
    assert "aspect_ratio_shortcut_rebutted" in gen.SEMANTIC_WITNESSES

    for band in ("easy", "medium", "hard"):
        for seed in range(8):
            for sample_index in (1, 2, 3, 4, 6, 7, 8, 9):
                grid = gen.generate(8100 + seed, sample_index, difficulty=band)
                symmetric, asymmetric = _role_geometry_keys(grid)
                assert symmetric & asymmetric
                assert gen.SEMANTIC_WITNESSES["aspect_ratio_shortcut_rebutted"](grid)


def test_general_curriculum_includes_connected_width_four_objects():
    for band in ("easy", "medium", "hard"):
        widths = set()
        for seed in range(12):
            for sample_index in (1, 2, 3, 4, 6, 7, 8, 9):
                grid = gen.generate(8200 + seed, sample_index, difficulty=band)
                widths.update(obj["bbox_w"] for obj in _objects(grid))
        assert 4 in widths
