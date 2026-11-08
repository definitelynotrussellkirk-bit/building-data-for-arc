"""Task-local regression tests for the c2fb0e01a539 topology curriculum."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
from reviewer_support import canonical_pairs, find_root

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from topology_probe import holes, load_generator, profile_signature, racket_outputs, true_output

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
ROOT = find_root(__file__)
PAIRS = canonical_pairs("c2fb0e01a539", root=ROOT)
EXPECTED_SIGNATURES = {
    "unit_plus_tall2": (1, 2),
    "wide2_plus_bent3": (2, 3),
    "unit_plus_bent4": (1, 4),
    "bent4_plus_tall2": (2, 4),
}


def test_metadata_pins_authority_and_declares_real_axes():
    assert gen.RULE_HASH == "8efc6e86f888"
    assert gen.EXAMPLES_NEEDED == 4
    assert tuple(gen.SCHEDULE_PROFILES) == tuple(EXPECTED_SIGNATURES)
    assert set(gen.AXES) == {"grid_h", "grid_w", "scene_profile", "palette_kind"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert callable(gen.observe_overrides)
    assert callable(gen.strict_canonical_like)
    assert callable(gen.rule_mirror)
    assert callable(gen.lesson_identifiable)


@pytest.mark.parametrize("pair", PAIRS, ids=lambda p: f"{p['split']}{p['pair_index']}")
def test_accepts_every_canonical_input_and_matches_labels(pair):
    grid = pair["input"]
    assert gen.self_check(grid) == []
    assert gen.strict_canonical_like(grid) == []
    assert true_output(grid) == pair["output"]
    assert gen.rule_mirror(grid) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", tuple(EXPECTED_SIGNATURES))
@pytest.mark.parametrize("palette", ["canonical", "broad"])
@pytest.mark.parametrize("height,width", [(9, 9), (14, 14)])
def test_exact_overrides_are_constructive_and_observable(
    band, profile, palette, height, width
):
    requested = {
        "grid_h": height,
        "grid_w": width,
        "scene_profile": profile,
        "palette_kind": palette,
    }
    grid = gen.generate(17, 9, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert (len(grid), len(grid[0])) == (height, width)
    assert gen.observe_overrides(grid) == requested
    assert profile_signature(grid) == EXPECTED_SIGNATURES[profile]
    assert gen.rule_mirror(grid) == true_output(grid)


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 8),
        ("grid_h", 15),
        ("grid_w", 8),
        ("grid_w", 15),
        ("grid_h", True),
        ("grid_w", 9.0),
        ("scene_profile", "missing"),
        ("scene_profile", 3),
        ("palette_kind", "warm"),
        ("palette_kind", 1),
    ],
)
def test_rejects_unknown_or_invalid_overrides(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_schedule_has_all_profiles_in_every_four_draw_window(band):
    for start in range(12):
        grids = [gen.generate(101, start + offset, difficulty=band) for offset in range(4)]
        observed = [gen.observe_overrides(grid)["scene_profile"] for grid in grids]
        expected = [gen.schedule_profile(101, start + offset, band) for offset in range(4)]
        assert observed == expected
        assert set(observed) == set(EXPECTED_SIGNATURES)


@pytest.mark.parametrize("profile", tuple(EXPECTED_SIGNATURES))
def test_profiles_teach_topology_not_just_rectangles(profile):
    grid = gen.generate(
        11,
        3,
        grid_h=9,
        grid_w=11,
        scene_profile=profile,
        palette_kind="canonical",
    )
    intended = true_output(grid)
    assert len(holes(grid)) == 2
    assert any(len(region) > 1 for region in holes(grid))
    assert gen.SEMANTIC_WITNESSES["cooperative_multi_component_enclosure"](grid)
    assert gen.SEMANTIC_WITNESSES["open_bbox_decoy"](grid)
    assert gen.SEMANTIC_WITNESSES["diagonal_is_not_an_escape"](grid)
    assert gen.SEMANTIC_RIVALS["fill_all_zeros"](grid) != intended
    assert gen.SEMANTIC_RIVALS["fill_with_boundary_color"](grid) != intended
    assert gen.SEMANTIC_RIVALS["largest_hole_only"](grid) != intended
    assert gen.SEMANTIC_RIVALS["one_cell_per_hole"](grid) != intended
    assert gen.SEMANTIC_RIVALS["component_bbox_interiors"](grid) != intended
    assert gen.SEMANTIC_RIVALS["eight_neighbor_holes"](grid) != intended


@pytest.mark.parametrize("profile", ["wide2_plus_bent3", "unit_plus_bent4", "bent4_plus_tall2"])
def test_nonrectangular_profiles_refute_shape_shortcuts(profile):
    grid = gen.generate(31, 7, scene_profile=profile, palette_kind="broad")
    assert gen.SEMANTIC_WITNESSES["nonrectangular_hole"](grid)
    intended = true_output(grid)
    assert gen.SEMANTIC_RIVALS["rectangular_holes_only"](grid) != intended
    assert gen.SEMANTIC_RIVALS["hole_bounding_boxes"](grid) != intended


def test_every_cyclic_lesson_start_and_query_rotation_is_identifiable():
    for band in (None, "easy", "medium", "hard"):
        for start in range(12):
            materialized = []
            for offset in range(gen.EXAMPLES_NEEDED + 1):
                grid = gen.generate(700 + start, start + offset, difficulty=band)
                materialized.append({"input": grid, "output": true_output(grid)})
            for query_index in range(len(materialized)):
                query = materialized[query_index]
                demos = materialized[:query_index] + materialized[query_index + 1 :]
                assert gen.lesson_identifiable(demos, query) == []
                for name, rival in gen.LESSON_COMPETITORS.items():
                    if all(rival(p["input"]) == p["output"] for p in demos):
                        assert rival(query["input"]) == query["output"], name


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 9 for _ in range(9)],
        [[0] * 9 for _ in range(9)],
        [[2] * 9 for _ in range(9)],
        [[0, 0, 0], [0, 2, 0], [0, 0, 0]],
        [[0, 0, 0], [2, 0, 2], [2, 2, 2]],
    ],
)
def test_self_check_rejects_malformed_or_no_enclosure_impostors(grid):
    assert gen.self_check(grid)


def test_rule_mirror_and_rivals_do_not_mutate_input():
    grid = gen.generate(44, 13, difficulty="hard")
    before = deepcopy(grid)
    assert gen.rule_mirror(grid) == true_output(grid)
    for rival in gen.SEMANTIC_RIVALS.values():
        rival(grid)
        assert grid == before
    assert grid == before


def test_generation_is_deterministic_and_diverse():
    grids = [gen.generate(900 + i, i, difficulty="hard") for i in range(64)]
    assert grids == [gen.generate(900 + i, i, difficulty="hard") for i in range(64)]
    encoded = {json.dumps(grid, separators=(",", ":")) for grid in grids}
    assert len(encoded) >= 56


def test_keyed_rng_is_independent_of_python_hash_seed():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from topology_probe import load_generator;"
        "print(json.dumps(load_generator().generate(31,8,difficulty='hard')))"
    )
    results = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        results.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
                env=env,
                text=True,
            )
        )
    assert results[0] == results[1]


def test_real_racket_authority_on_canonical_and_generated_inputs():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in PAIRS]
    grids += [gen.generate(1701 + index, index) for index in range(16)]
    assert racket_outputs(grids) == [true_output(grid) for grid in grids]

@pytest.mark.parametrize("profile", tuple(EXPECTED_SIGNATURES))
def test_generated_morphology_stays_near_canonical_component_scale(profile):
    grid = gen.generate(
        503,
        5,
        grid_h=9,
        grid_w=11,
        scene_profile=profile,
        palette_kind="canonical",
    )
    components = gen._same_color_components(grid)
    assert len(components) <= 4
    assert max(len(component["cells"]) for component in components) >= 14
