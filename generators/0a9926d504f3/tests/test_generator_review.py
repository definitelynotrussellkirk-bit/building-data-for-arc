"""Regression tests written before the 0a9926d504f3 repair."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    analyze,
    canonical_pairs,
    canonical_program,
    center_always_visible,
    exactly_four_markers,
    has_ignored_extra_marker,
    has_shared_corner,
    intended_output,
    load_generator,
    observed,
    preserve_nonrole_markers,
    shared_corner_is_exact,
    texture_from_grid,
    unique_extrema_roles,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))

TEXTURES = ("plain", "shared_corner", "center_edge", "extra_marker", "same_color")
BANDS = (None, "easy", "medium", "hard")


def test_authority_pin_and_honest_axis_surface():
    assert gen.RULE_HASH == "b54594bcf310"
    assert gen.AXES == {
        "grid_h": {
            "type": "int",
            "default": "canonical-weighted 10..22",
            "valid": "10..22",
        },
        "grid_w": {
            "type": "int",
            "default": "canonical-weighted 10..22",
            "valid": "10..22",
        },
        "texture": {
            "type": "str",
            "default": "scheduled helpful",
            "valid": "plain|shared_corner|center_edge|extra_marker|same_color",
            "doc": (
                "shared_corner: one marker is min-row AND min-col; "
                "center_edge: the 2 sits on an edge and vanishes; "
                "extra_marker: interior non-extreme dot erased."
            ),
        },
    }
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert gen.EXAMPLES_NEEDED == 4


@pytest.mark.parametrize(
    "pair", canonical_pairs(), ids=["train0", "train1", "train2", "test0"]
)
def test_canonical_inputs_are_accepted_and_independent_oracle_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert intended_output(pair["input"]) == pair["output"]


def test_all_active_base_authorities_match_the_exact_canonical_program():
    expected = canonical_program()
    paths = (
        ROOT / "shared/data/base/solutions/training/e4075551__0a9926d504f3.json",
        ROOT / "shared/data/base/solutions/augmented/e4075551__036bcbfa15d9.json",
    )
    for path in paths:
        row = json.loads(path.read_text(encoding="utf-8"))
        assert row["racket_target"]["raw_code"] == expected
        assert row["racket_target"]["target_code"] == expected


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("shape", [(10, 10), (14, 15), (22, 22)])
@pytest.mark.parametrize("texture", TEXTURES)
def test_all_declared_overrides_work_in_every_band(band, shape, texture):
    h, w = shape
    requested = {"grid_h": h, "grid_w": w, "texture": texture}
    grid = gen.generate(17, 9, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert observed(grid) == requested
    assert gen.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo": 1},
        {"grid_h": 9},
        {"grid_h": 23},
        {"grid_w": 9},
        {"grid_w": 23},
        {"grid_h": True},
        {"grid_h": "10"},
        {"grid_w": 10.0},
        {"texture": "unknown"},
        {"texture": 1},
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(kwargs):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **kwargs)


def test_pinned_canonical_profile_density_meets_the_intake_floor():
    canonical_profiles = {
        (len(pair["input"]), len(pair["input"][0]),
         len({value for row in pair["input"] for value in row}))
        for pair in canonical_pairs()
    }
    hits = 0
    for band in ("easy", "medium", "hard"):
        for index in range(20):
            digest = hashlib.sha256(
                f"profile-floor:v1:0a9926d504f3:{band}:{index}".encode()
            ).hexdigest()
            seed = int(digest[:12], 16)
            grid = gen.generate(seed, seed % 7919 + index, difficulty=band)
            profile = (
                len(grid), len(grid[0]),
                len({value for row in grid for value in row}),
            )
            hits += int(profile in canonical_profiles)
    assert hits >= 15, f"canonical-profile density {hits}/60 is below 25%"


@pytest.mark.parametrize("band", BANDS)
def test_generated_inputs_are_deterministic_valid_and_diverse(band):
    shapes: set[tuple[int, int]] = set()
    textures: set[str] = set()
    hashes: set[str] = set()
    for index in range(160):
        grid = gen.generate(600 + index, index, difficulty=band)
        assert grid == gen.generate(600 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert intended_output(grid) != grid
        actual = observed(grid)
        assert gen.observe_overrides(grid) == actual
        assert actual["texture"] == gen.schedule_profile(600 + index, index, difficulty=band)
        shapes.add((actual["grid_h"], actual["grid_w"]))
        textures.add(str(actual["texture"]))
        hashes.add(json.dumps(grid, separators=(",", ":")))
    assert textures == set(TEXTURES)
    assert {(15, 14), (14, 15), (15, 15), (16, 15)} <= shapes
    assert len(shapes) >= 12
    assert len(hashes) >= 155


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("start", range(24))
def test_every_consecutive_four_demo_window_refutes_all_declared_rivals(band, start):
    grids = [gen.generate(991, start + offset, difficulty=band) for offset in range(4)]
    textures = {texture_from_grid(grid) for grid in grids}
    assert {"shared_corner", "center_edge", "extra_marker"} <= textures
    assert any(exactly_four_markers(grid) != intended_output(grid) for grid in grids)
    assert any(center_always_visible(grid) != intended_output(grid) for grid in grids)
    assert any(preserve_nonrole_markers(grid) != intended_output(grid) for grid in grids)


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
@pytest.mark.parametrize("start", range(16))
def test_lesson_hook_accepts_scheduled_lessons_and_rejects_no_competitor(band, start):
    grids = [gen.generate(812, start + offset, difficulty=band) for offset in range(5)]
    demos = [{"input": grid, "output": intended_output(grid)} for grid in grids[:4]]
    query = {"input": grids[4], "output": intended_output(grids[4])}
    assert gen.lesson_identifiable(demos, query) == []
    for name, rival in gen.LESSON_COMPETITORS.items():
        assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_canonical_shortcuts_fit_all_canonical_pairs_but_declared_witnesses_refute_them():
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in canonical_pairs()), name
    grids = [gen.generate(73, index) for index in range(4)]
    for witness_name, rival_names in gen.WITNESS_RIVALS.items():
        witness = gen.SEMANTIC_WITNESSES[witness_name]
        witness_grid = next(grid for grid in grids if witness(grid))
        for rival_name in rival_names:
            assert gen.SEMANTIC_RIVALS[rival_name](witness_grid) != intended_output(witness_grid)


def test_known_plain_role_tie_regression_is_eliminated():
    grid = gen.generate(1, 0, texture="plain")
    assert unique_extrema_roles(grid)


def test_known_shared_corner_overwrite_regression_is_eliminated():
    grid = gen.generate(13, 0, texture="shared_corner")
    assert shared_corner_is_exact(grid)
    assert len(analyze(grid)["others"]) == 3


def test_texture_witnesses_match_their_generated_structures():
    for index, texture in enumerate(TEXTURES):
        grid = gen.generate(31, index, texture=texture)
        assert texture_from_grid(grid) == texture
        if texture == "shared_corner":
            assert has_shared_corner(grid)
        elif texture == "center_edge":
            info = analyze(grid)
            assert info["center"][0] in (info["top_row"], info["bottom_row"])
            assert intended_output(grid)[info["center"][0]][info["center"][1]] != 2
        elif texture == "extra_marker":
            assert has_ignored_extra_marker(grid)


@pytest.mark.parametrize(
    "mutation",
    [
        "ragged",
        "bad_color",
        "two_centers",
        "ambiguous_top",
        "center_outside",
        "shared_wrong_dual",
        "extra_on_cross",
    ],
)
def test_validator_rejects_structural_mutations(mutation):
    grid = gen.generate(19, 2, grid_h=15, grid_w=15, texture="plain")
    info = analyze(grid)
    if mutation == "ragged":
        grid[0].pop()
    elif mutation == "bad_color":
        grid[0][0] = 10
    elif mutation == "two_centers":
        grid[0][0] = 2
    elif mutation == "ambiguous_top":
        top = info["top"]
        candidate_col = top[1] + 1 if top[1] + 1 < info["right_col"] else top[1] - 1
        grid[top[0]][candidate_col] = 9
    elif mutation == "center_outside":
        cr, cc = info["center"]
        grid[cr][cc] = 0
        grid[0][0] = 2
    elif mutation == "shared_wrong_dual":
        grid = gen.generate(19, 2, grid_h=15, grid_w=15, texture="shared_corner")
        info = analyze(grid)
        tr, lc = info["top_row"], info["left_col"]
        color = grid[tr][lc]
        grid[tr][lc] = 0
        grid[tr][lc + 1] = color
        grid[tr + 1][lc] = color
    elif mutation == "extra_on_cross":
        grid = gen.generate(19, 2, grid_h=15, grid_w=15, texture="extra_marker")
        info = analyze(grid)
        selected = set(info["role_positions"]) | {info["center"]}
        extra = next(p for p in info["others"] if p not in selected)
        grid[extra[0]][extra[1]] = 0
        cr, _cc = info["center"]
        grid[cr][info["left_col"] + 1] = 9
    assert gen.self_check(grid)


@pytest.mark.parametrize("bad", [None, [], [[]], [[0], [0, 1]], [[True] * 10 for _ in range(10)]])
def test_malformed_grid_returns_diagnostics_not_exceptions(bad):
    assert gen.self_check(bad)


def test_keyed_rng_is_independent_of_python_hash_seed():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
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


def test_oracles_and_rivals_do_not_mutate_input():
    grid = gen.generate(22, 0)
    original = deepcopy(grid)
    intended_output(grid)
    exactly_four_markers(grid)
    center_always_visible(grid)
    preserve_nonrole_markers(grid)
    assert grid == original
