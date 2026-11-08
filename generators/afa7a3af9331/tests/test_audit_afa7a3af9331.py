from pathlib import Path
import importlib.util
import pytest
from reviewer_support import canonical_pairs, find_root
ROOT = find_root(__file__)
SPEC = importlib.util.spec_from_file_location("audited_" + Path(__file__).parents[1].name, Path(__file__).parents[1] / "generator.py")
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)

def test_canonical_rule_pin_and_pairs():
    assert GEN.RULE_HASH == "a235c2b1bb6c"
    for p in canonical_pairs(GEN.TASK_ID,root=ROOT):
        assert GEN.self_check(p["input"]) == []
        assert GEN.rule_mirror(p["input"]) == p["output"]

def test_ordinary_draws_are_two_objects_with_color_preserving_overlap():
    for band in ("easy","medium","hard"):
        for i in range(60):
            grid=GEN.generate(0,i,difficulty=band)
            assert GEN.self_check(grid) == []
            objs=GEN._objects(grid)
            assert len(objs)==2
            out=GEN.rule_mirror(grid)
            assert 8 in {v for row in out for v in row}
            assert any(v not in (0,8) for row in out for v in row)


def test_difficulty_changes_default_support():
    assert any(GEN.generate(seed,0,difficulty="easy") != GEN.generate(seed,0,difficulty="hard") for seed in range(5))
