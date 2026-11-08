"""Regression contract for the corner-independent token repair."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_path, find_root

TASK_ID = "b7fbb716d189"
REPO_ROOT = find_root(__file__)
HOME = REPO_ROOT / "generators" / TASK_ID
CANONICAL_LEDGER = canonical_path(REPO_ROOT)
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    CANONICAL_CORNER_CODE,
    CORNERS,
    canonical_pairs,
    corner_shortcut_output,
    intended_output,
    load_generator,
    observe,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


@pytest.mark.parametrize("pair", canonical_pairs())
def test_accepts_canonical_inputs_and_matches_independent_oracle(pair):
    assert CANONICAL_LEDGER.is_file()
    assert gen.self_check(pair["input"]) == []
    assert intended_output(pair["input"]) == pair["output"]
    assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_exact_override_is_honored_in_every_band(band):
    options = {
        "grid_h": 12,
        "grid_w": 13,
        "token": 4,
        "token_corner": "bottom_left",
        "motif_cells": 9,
        "motif_colors": 5,
    }
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observe(grid) == options
    assert gen.observe_overrides(grid) == options
    assert gen.rule_mirror(grid) == intended_output(grid)


@pytest.mark.parametrize("token", range(1, 5))
@pytest.mark.parametrize("corner", CORNERS)
def test_token_value_and_corner_vary_independently(token, corner):
    grid = gen.generate(
        73,
        token * 10 + CORNERS.index(corner),
        grid_h=9,
        grid_w=10,
        token=token,
        token_corner=corner,
        motif_cells=6,
        motif_colors=3,
    )
    assert gen.self_check(grid) == []
    assert observe(grid)["token"] == token
    assert observe(grid)["token_corner"] == corner
    assert gen.rule_mirror(grid) == intended_output(grid)
    if token != CANONICAL_CORNER_CODE[corner]:
        assert corner_shortcut_output(grid) != intended_output(grid)


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 7),
        ("grid_h", 13),
        ("grid_w", 7),
        ("grid_w", 14),
        ("token", 0),
        ("token", 5),
        ("token_corner", "center"),
        ("motif_cells", 4),
        ("motif_cells", 10),
        ("motif_colors", 1),
        ("motif_colors", 6),
        ("grid_h", True),
        ("motif_cells", 6.0),
    ],
)
def test_invalid_overrides_are_rejected(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("mutation", ["blank", "remove_token", "duplicate_token", "disconnect_motif", "border_motif"])
def test_self_check_rejects_destructive_mutations(mutation):
    grid = gen.generate(
        101,
        7,
        grid_h=9,
        grid_w=10,
        token=2,
        token_corner="top_right",
        motif_cells=7,
        motif_colors=3,
    )
    changed = deepcopy(grid)
    motif = [(r, c) for r, row in enumerate(changed) for c, value in enumerate(row) if value >= 5]
    token = [(r, c) for r, row in enumerate(changed) for c, value in enumerate(row) if value in (1, 2, 3, 4)][0]
    if mutation == "blank":
        changed = [[0 for _ in row] for row in changed]
    elif mutation == "remove_token":
        changed[token[0]][token[1]] = 0
    elif mutation == "duplicate_token":
        changed[0][0] = 1
    elif mutation == "disconnect_motif":
        for r, c in motif:
            changed[r][c] = 0
        changed[2][2] = 5
        changed[-3][-3] = 6
        changed[2][3] = 7
        changed[3][2] = 5
        changed[-3][-4] = 6
    elif mutation == "border_motif":
        r, c = motif[0]
        changed[r][c] = 0
        changed[0][1] = 5
    assert gen.self_check(changed)


def test_canonical_fit_corner_shortcut_has_generated_counterexamples():
    pairs = canonical_pairs()
    assert all(corner_shortcut_output(pair["input"]) == pair["output"] for pair in pairs)
    witnesses = []
    for token in range(1, 5):
        for corner in CORNERS:
            grid = gen.generate(
                211,
                token * 10 + CORNERS.index(corner),
                token=token,
                token_corner=corner,
                motif_cells=7,
                motif_colors=3,
            )
            if intended_output(grid) != corner_shortcut_output(grid):
                witnesses.append(grid)
                assert gen.SEMANTIC_WITNESSES["token_corner_independence"](grid)
                assert gen.SEMANTIC_RIVALS["corner_encodes_transform"](grid) == corner_shortcut_output(grid)
    assert len(witnesses) == 12


def test_lesson_hook_requires_a_demo_that_refutes_corner_shortcut():
    ambiguous = []
    informative = []
    for token, corner in ((2, "top_left"), (4, "top_right"), (3, "bottom_right")):
        grid = gen.generate(313, token, token=token, token_corner=corner, motif_cells=6, motif_colors=3)
        ambiguous.append({"input": grid, "output": intended_output(grid)})
    for token, corner in ((1, "top_left"), (2, "top_right"), (3, "bottom_left")):
        grid = gen.generate(317, token, token=token, token_corner=corner, motif_cells=6, motif_colors=3)
        informative.append({"input": grid, "output": intended_output(grid)})
    assert gen.lesson_identifiable(ambiguous, ambiguous[0])
    assert gen.lesson_identifiable(informative, informative[0]) == []


def test_default_distribution_covers_all_corners_and_most_cross_pairings():
    for band in ("easy", "medium", "hard"):
        corners = set()
        pairings = set()
        canonical_profiles = 0
        for index in range(192):
            grid = gen.generate(1000 + index, index * 11, difficulty=band)
            assert gen.self_check(grid) == []
            assert grid == gen.generate(1000 + index, index * 11, difficulty=band)
            stats = observe(grid)
            corners.add(stats["token_corner"])
            pairings.add((stats["token"], stats["token_corner"]))
            canonical_profiles += (
                stats["grid_h"] in (8, 9)
                and stats["grid_w"] in (8, 9, 10)
                and stats["motif_colors"] == 3
            )
        assert corners == set(CORNERS)
        assert len(pairings) >= 14
        assert canonical_profiles >= 20


def test_retained_counterexample_refutes_corner_shortcut():
    root = HOME / "counterexamples" / "review-73698e4c67667471-shortcut"
    grid = json.loads((root / "input.json").read_text())
    rival = json.loads((root / "rival.json").read_text())
    racket = json.loads((root / "racket.json").read_text())
    intended = racket["results"][0]["output"]

    assert gen.self_check(grid) == []
    assert gen.rule_mirror(grid) == intended
    assert intended_output(grid) == intended
    assert gen.SEMANTIC_RIVALS["corner_encodes_transform"](grid) == rival
    assert rival != intended
