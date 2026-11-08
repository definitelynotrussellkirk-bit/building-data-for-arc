from pathlib import Path
import importlib.util
import pytest
from reviewer_support import canonical_pairs, find_root
ROOT = find_root(__file__)
SPEC = importlib.util.spec_from_file_location("audited_" + Path(__file__).parents[1].name, Path(__file__).parents[1] / "generator.py")
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)

def test_axes_are_lawful_and_observable_in_every_band():
    assert set(GEN.AXES) == {"shape_h", "shape_w"}
    for band in ("easy", "medium", "hard"):
        for h in range(2,7):
            for w in range(2,7):
                grid = GEN.generate(37,11,difficulty=band,shape_h=h,shape_w=w)
                assert GEN.self_check(grid) == []
                assert GEN.observe_overrides(grid) == {"shape_h":h,"shape_w":w}
    for key in ("palette_kind", "palette_size", "n_distinct_colors", "texture", "unknown"):
        with pytest.raises(ValueError): GEN.generate(37,11,**{key: "warm"})


def test_difficulty_changes_default_support():
    assert any(GEN.generate(seed,0,difficulty="easy") != GEN.generate(seed,0,difficulty="hard") for seed in range(5))
