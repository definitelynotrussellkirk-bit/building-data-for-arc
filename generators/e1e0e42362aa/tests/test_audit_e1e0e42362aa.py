from pathlib import Path
import importlib.util
import pytest
from reviewer_support import canonical_pairs, find_root
ROOT = find_root(__file__)
SPEC = importlib.util.spec_from_file_location("audited_" + Path(__file__).parents[1].name, Path(__file__).parents[1] / "generator.py")
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)

def test_exact_endpoints_and_removed_inert_controls():
    assert GEN.RULE_HASH == "e51db089d1da"
    assert set(GEN.AXES) == {"grid_h", "grid_w", "n_cells"}
    for band in ("easy","medium","hard"):
        for axis, values in (("grid_h",(5,15)),("grid_w",(5,15)),("n_cells",(1,30))):
            for value in values:
                grid=GEN.generate(731,2,difficulty=band,**{axis:value})
                assert GEN.self_check(grid) == []
                assert GEN.observe_overrides(grid)[axis] == value
    for axis in ("palette_size","n_distinct_colors","palette_kind","position_bias","density","texture","unknown"):
        with pytest.raises(ValueError): GEN.generate(731,2,**{axis:1})

def test_malformed_and_identity_inputs_rejected():
    for grid in ([],[[True]],[[10]],[[0,1],[0]],[[0]*5 for _ in range(5)]):
        assert GEN.self_check(grid)


def test_count_endpoint_never_fails_due_to_unpinned_dimensions():
    for seed in range(500):
        grid=GEN.generate(seed,0,difficulty="medium",n_cells=30)
        assert GEN.observe_overrides(grid)["n_cells"]==30
    for h,w,n in ((5,5,25),(5,5,29),(5,6,30),(6,5,30)):
        with pytest.raises(ValueError) as caught:
            GEN.generate(0,0,grid_h=h,grid_w=w,n_cells=n)
        assert set(caught.value.incompatible_axes)=={"grid_h","grid_w","n_cells"}


def test_difficulty_changes_default_support():
    assert any(GEN.generate(seed,0,difficulty="easy") != GEN.generate(seed,0,difficulty="hard") for seed in range(5))
