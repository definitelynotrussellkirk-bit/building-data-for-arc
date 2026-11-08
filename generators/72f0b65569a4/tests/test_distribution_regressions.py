"""Protect the actual support floor and public scalar contract."""
from __future__ import annotations

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


ROOT = find_root(__file__)
MODULE, _, _ = load_selected_generator("72f0b65569a4", root=ROOT)


@pytest.mark.parametrize("argument", ["seed", "sample_index"])
@pytest.mark.parametrize("invalid", [True, False, -1, 0.5, "1", None])
def test_call_scalars_reject_nonnegative_integer_impostors(argument, invalid):
    args = {"seed": 17, "sample_index": 0}
    args[argument] = invalid
    with pytest.raises((TypeError, ValueError)):
        MODULE.generate(**args)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_band_retains_canonical_scale_and_broader_sizes(band):
    canonical = {
        (len(pair["input"]), len(pair["input"][0]))
        for pair in canonical_pairs("72f0b65569a4", root=ROOT)
    }
    for seed in (0, 17, 20261019):
        grids = [MODULE.generate(seed, i, difficulty=band) for i in range(30)]
        exact = [g for g in grids if (len(g), len(g[0])) in canonical
                 and {v for row in g for v in row} == {0, 1, 4}]
        assert len(exact) >= 5, (band, seed, len(exact))
        assert any((len(g), len(g[0])) not in canonical for g in grids)
        assert all(MODULE.self_check(g) == [] for g in grids)


def test_explicit_large_canvas_survives_canonical_scale_schedule():
    for i in range(9):
        g = MODULE.generate(17, i, difficulty="hard", grid_h=18, grid_w=20,
                            frame_h=12, frame_w=14, n_marks=7)
        assert len(g) == 18 and len(g[0]) == 20
        assert MODULE.observe_overrides(g) == {
            "grid_h": 18, "grid_w": 20, "frame_h": 12,
            "frame_w": 14, "n_marks": 7,
        }
