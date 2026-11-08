"""Adversarial contract tests: valid positives plus deliberately invalid witnesses."""
import importlib.util
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
sys.path.insert(0, str(ROOT / "shared/runtime"))
spec = importlib.util.spec_from_file_location("round2_contract_generator", HOME / "generator.py")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def scene(points, h=7, w=7):
    grid = [[0] * w for _ in range(h)]
    for r, c, color in points:
        grid[r][c] = color
    return grid


@pytest.mark.parametrize("points", [
    [(0, 0, 1), (6, 6, 2)],       # no orthogonal length-three span
    [(0, 0, 1), (0, 1, 2)],       # adjacent, not a one-cell gap
    [(0, 0, 1), (1, 1, 2)],       # diagonal
    [(0, 0, 1), (0, 2, 2), (1, 0, 3), (1, 2, 4)],  # spans touch
    [(0, 0, 1), (0, 2, 2), (4, 0, 3), (6, 6, 4)],  # only one intact pair
])
def test_mismatched_fixture_requires_complete_separated_motifs(points):
    assert gen.self_check(scene(points), meta={"texture": "mismatched_endpoints"})


def test_mismatched_valid_adjacent_candidates_need_global_pairing():
    # c=2 and c=4 form an extra candidate edge. Degree-one validation is wrong.
    grid = scene([(0, 0, 1), (0, 2, 2), (0, 4, 3), (0, 6, 4)])
    assert not gen.self_check(grid, meta={"texture": "mismatched_endpoints", "gap_count": 2})


@pytest.mark.parametrize("meta", [
    {"texture": "no_gaps", "grid_h": 14},
    {"texture": "no_gaps", "grid_w": 14},
    {"texture": "no_gaps", "gap_count": 2},
    {"texture": "no_gaps", "colors": [1]},
    {"texture": "no_gaps", "colors": []},
])
def test_blank_fixture_cannot_bypass_requested_constraints(meta):
    assert gen.self_check(scene([]), meta=meta)


def test_blank_fixture_accepts_matching_dimensions():
    assert not gen.self_check(scene([]), meta={"texture": "no_gaps", "grid_h": 7, "grid_w": 7})


@pytest.mark.parametrize("colors", [[8], [0], [True], [1, 1], "1"])
def test_selfcheck_enforces_explicit_palette(colors):
    assert gen.self_check(scene([(0, 0, 1), (0, 2, 1)]), meta={"colors": colors})


def test_selfcheck_accepts_correct_palette_without_imposing_order():
    grid = scene([(0, 0, 1), (0, 2, 1), (4, 0, 8), (6, 0, 8)])
    assert not gen.self_check(grid, meta={"colors": [8, 1]})


@pytest.mark.parametrize("meta", [
    {"overrides": {"texture": "no_gaps", "grid_h": 14}},
    {"overrides": {"colors": [8]}},
])
def test_nested_metadata_is_enforced(meta):
    grid = scene([]) if meta["overrides"].get("texture") == "no_gaps" else scene([(0, 0, 1), (0, 2, 1)])
    assert gen.self_check(grid, meta=meta)


def test_selfcheck_rejects_more_than_eight_ordinary_motifs():
    points = [(r, c+k, i+1) for i, (r, c) in enumerate(
        [(r, c) for r in (0, 2, 4) for c in (0, 4, 8)]) for k in (0, 2)]
    assert gen.self_check(scene(points, h=11, w=11))


def test_selfcheck_rejects_unknown_explicit_texture():
    assert gen.self_check(scene([(0, 0, 1), (0, 2, 1)]), meta={"texture": "not-a-mode"})


@pytest.mark.parametrize("texture", ["no_gaps", "gap_already_filled", "mismatched_endpoints"])
def test_stronger_negative_validation_does_not_reject_generated_positives(texture):
    for h, w in ((5, 5), (5, 14), (14, 5), (14, 14), (7, 9)):
        for seed in range(8):
            overrides = {"grid_h": h, "grid_w": w, "texture": texture}
            grid = gen.generate(seed, 7, **overrides)
            assert not gen.self_check(grid, meta=overrides), (overrides, seed)


@pytest.mark.parametrize("texture", ["", False, 0, []])
def test_falsey_invalid_texture_is_not_treated_as_omitted(texture):
    assert gen.self_check(scene([(0, 0, 1), (0, 2, 1)]), meta={"texture": texture})


@pytest.mark.parametrize("meta", ["", False, 0, []])
def test_falsey_nondictionary_metadata_is_not_silently_discarded(meta):
    assert gen.self_check(scene([(0, 0, 1), (0, 2, 1)]), meta=meta)
