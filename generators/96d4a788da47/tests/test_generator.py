"""Regression and contract tests for the repaired left-slide sampler."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    bbox_fill_left_rival,
    color_components,
    has_nonrectangular_object,
    labeled_canonical_pairs,
    load_generator,
    observed_axes,
    slide_left_reference,
)

gen = load_generator()


@pytest.mark.parametrize(
    "pair",
    labeled_canonical_pairs(),
    ids=lambda pair: f"v{pair['variant']}-{pair['split']}{pair['pair_index']}",
)
def test_canonical_inputs_are_owned_and_reference_rule_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert slide_left_reference(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {"grid_h": 7, "grid_w": 8, "n_blobs": 2},
        {"grid_h": 7, "grid_w": 14, "n_blobs": 3},
        {"grid_h": 14, "grid_w": 8, "n_blobs": 3},
        {"grid_h": 14, "grid_w": 14, "n_blobs": 2},
    ],
)
def test_every_public_override_combination_is_exact_in_every_band(band, options):
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed_axes(grid) == options
    assert gen.observe_overrides(grid) == options
    assert slide_left_reference(grid) != grid


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo": 1},
        {"grid_h": 6},
        {"grid_h": 15},
        {"grid_w": 7},
        {"grid_w": 15},
        {"n_blobs": 1},
        {"n_blobs": 4},
        {"grid_h": True},
        {"grid_w": 8.0},
        {"n_blobs": "2"},
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **kwargs)


@pytest.mark.parametrize(
    "seed,index,difficulty",
    [
        (True, 0, None),
        (1.0, 0, None),
        ("1", 0, None),
        (1, True, None),
        (1, -1, None),
        (1, 0, "unknown"),
        (1, 0, 1),
    ],
)
def test_invalid_public_call_scalars_are_rejected(seed, index, difficulty):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(seed, index, difficulty=difficulty)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_distribution_is_exact_deterministic_and_shape_preserving(band):
    seen_shapes = set()
    seen_counts = set()
    for index in range(96):
        grid = gen.generate(1000 + index, index * 7, difficulty=band)
        assert grid == gen.generate(1000 + index, index * 7, difficulty=band)
        assert gen.self_check(grid) == []
        observed = observed_axes(grid)
        assert gen.observe_overrides(grid) == observed
        assert observed["n_blobs"] in (2, 3)
        assert has_nonrectangular_object(grid)
        output = slide_left_reference(grid)
        assert output != grid
        # The rule translates each component without changing its cell count.
        assert sorted(len(cells) for _, cells in color_components(output)) == sorted(
            len(cells) for _, cells in color_components(grid)
        )
        seen_shapes.add((observed["grid_h"], observed["grid_w"]))
        seen_counts.add(observed["n_blobs"])
    assert len(seen_shapes) >= 12
    assert seen_counts == {2, 3}


def test_declared_canonical_shortcut_is_real_and_generated_witness_refutes_it():
    assert all(
        bbox_fill_left_rival(pair["input"]) == pair["output"]
        for pair in labeled_canonical_pairs()
    )
    for index in range(32):
        grid = gen.generate(700 + index, index)
        assert gen.SEMANTIC_WITNESSES["shape_preservation"](grid)
        rival = gen.SEMANTIC_RIVALS["bbox_fill_left"](deepcopy(grid))
        assert rival == bbox_fill_left_rival(grid)
        assert rival != slide_left_reference(grid)


def test_validator_rejects_representative_destructive_mutations():
    grid = gen.generate(41, 3, grid_h=10, grid_w=12, n_blobs=3)
    assert gen.self_check(grid) == []

    blank = [[0 for _ in row] for row in grid]
    assert gen.self_check(blank)

    touches_left = deepcopy(grid)
    color, cells = color_components(touches_left)[0]
    for r, c in cells:
        touches_left[r][c] = 0
        touches_left[r][c - min(col for _, col in cells)] = color
    assert gen.self_check(touches_left)

    split_color = deepcopy(grid)
    color, cells = color_components(split_color)[0]
    r, c = cells[0]
    split_color[r][c] = 0
    split_color[-1][-1] = color
    assert gen.self_check(split_color)

    overlapping_rows = deepcopy(grid)
    components = color_components(overlapping_rows)
    color, cells = components[-1]
    for r, c in cells:
        overlapping_rows[r][c] = 0
    target_row = min(r for r, _ in components[0][1])
    left = min(c for _, c in cells)
    for r, c in cells:
        nr = target_row + (r - min(rr for rr, _ in cells))
        if overlapping_rows[nr][c] == 0:
            overlapping_rows[nr][c] = color
    assert gen.self_check(overlapping_rows)


@pytest.mark.parametrize("bad", [None, [], [[]], [[0], [0, 1]], [[True] * 8 for _ in range(7)]])
def test_malformed_grids_are_diagnostic_not_exceptions(bad):
    assert gen.self_check(bad)


def test_rule_hash_and_contract_inventory_are_pinned():
    assert gen.RULE_HASH == "da14dfe7467e"
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert set(gen.SEMANTIC_WITNESSES) == {"shape_preservation"}
    assert set(gen.SEMANTIC_RIVALS) == {"bbox_fill_left"}
    assert gen.WITNESS_RIVALS == {"shape_preservation": ["bbox_fill_left"]}
    assert gen.CANONICAL_SHORTCUTS["bbox_fill_left"] is gen.SEMANTIC_RIVALS["bbox_fill_left"]
    assert gen.LESSON_COMPETITORS["bbox_fill_left"] is gen.SEMANTIC_RIVALS["bbox_fill_left"]


def test_retained_bbox_fill_counterexample_is_lawful_and_distinguishing():
    import json

    path = HOME / "counterexamples" / "bbox-fill-left.json"
    case = json.loads(path.read_text(encoding="utf-8"))
    import hashlib

    assert case["generator_sha256"] == hashlib.sha256((HOME / "generator.py").read_bytes()).hexdigest()
    assert case["rule_hash"] == gen.RULE_HASH
    assert gen.self_check(case["input"]) == []
    assert slide_left_reference(case["input"]) == case["correct_output"]
    assert bbox_fill_left_rival(case["input"]) == case["rival_output"]
    assert case["correct_output"] != case["rival_output"]
