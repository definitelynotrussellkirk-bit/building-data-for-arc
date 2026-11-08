"""Review regressions; expected behavior comes from the teaching contract and Racket fixtures."""
import importlib.util
from pathlib import Path
import pytest
from reviewer_support import canonical_pairs, find_root

ROOT = find_root(__file__)
TASK = "866b956f2402"
SOURCE = ROOT / "generators" / TASK / "generator.py"
if not SOURCE.is_file():
    SOURCE = ROOT / "puzzle_generators/per_puzzle" / TASK / "generator.py"
spec = importlib.util.spec_from_file_location("reviewed_gravity_generator", SOURCE)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

@pytest.mark.parametrize("grid", [
    [[0]*7 for _ in range(8)],
    [[4]*7 for _ in range(8)],
    [[0]*7 for _ in range(7)]+[[0,0,0,8,0,0,0]],
    [[0]*7 for _ in range(7)]+[[0,0,0,True,0,0,0]],
    [[0]*7 for _ in range(7)]+[[0,0,0,10,0,0,0]],
    [[0]*7 for _ in range(7)]+[[0,0,0,1.0,0,0,0]],
])
def test_rejects_non_teaching_impostors(grid):
    assert gen.self_check(grid)

@pytest.mark.parametrize("name", ["n_active", "palette_kind", "palette_size", "n_distinct_colors", "position_bias", "density", "typo_axis"])
def test_removed_ignored_controls_fail_explicitly(name):
    with pytest.raises((ValueError, TypeError)):
        gen.generate(7, 0, **{name: 3})

@pytest.mark.parametrize("value", [True, 9.0, "9"])
def test_integer_controls_do_not_coerce(value):
    with pytest.raises((ValueError, TypeError)):
        gen.generate(7, 0, grid_h=value)

@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_dimension_override_is_exact_in_every_band(band):
    grid = gen.generate(7, 0, difficulty=band, grid_h=8, grid_w=7)
    assert (len(grid),len(grid[0])) == (8,7)
    assert gen.self_check(grid) == []


def test_all_canonical_inputs_remain_accepted():
    pairs = canonical_pairs(TASK, root=ROOT)
    assert len(pairs) == 5
    assert all(gen.self_check(pair["input"]) == [] for pair in pairs)


def test_contrast_exposes_wall_free_tail_and_color_one():
    grid = gen.generate(7, 1, texture="contrast")
    cols = list(zip(*grid))
    assert any(8 not in col and any(v not in (0,8) for v in col[:-1]) for col in cols)
    assert any(8 in col and any(v not in (0,8) for v in col[max(i for i,v in enumerate(col) if v==8)+1:-1]) for col in cols)
    assert any(1 in row for row in grid)


def test_settled_pebbles_are_outside_teaching_domain():
    grid = [[0]*7 for _ in range(8)]
    grid[5][1]=8; grid[4][1]=3
    grid[7][4]=8; grid[6][4]=2
    assert gen.self_check(grid)


# These exact lesson seeds failed the first repaired source's full census.
@pytest.mark.parametrize("band,seed,start", [('medium', 2886644973, 9), ('medium', 1890446777, 97), ('hard', 1783697477, 29), ('hard', 1082562389, 66), ('hard', 2217127249, 69), ('hard', 3897934245, 72)])
def test_border_behavior_has_repeated_lesson_evidence(band,seed,start):
    pairs = [gen.generate(seed,start+i,difficulty=band) for i in range(6)]
    wrong = gen.SEMANTIC_RIVALS["interior_columns_only"]
    failures = sum(wrong(grid) != gen._gravity(grid) for grid in pairs)
    assert failures != 1

@pytest.mark.parametrize("band,seed", [("easy",0),("easy",31),("medium",0),("medium",7),("hard",1),("hard",7),("hard",31)])
def test_rigid_object_shortcut_has_repeated_lesson_evidence(band,seed):
    assert "rigid_horizontal_runs" in gen.SEMANTIC_RIVALS
    wrong = gen.SEMANTIC_RIVALS["rigid_horizontal_runs"]
    pairs = [gen.generate(seed,i,difficulty=band) for i in range(6)]
    assert sum(wrong(grid) != gen._gravity(grid) for grid in pairs) >= 2


import json
from itertools import product

FIXTURE_FILE = SOURCE.parent / "counterexamples/racket_witnesses.json"
FIXTURES = json.loads(FIXTURE_FILE.read_text())["fixtures"]

@pytest.mark.parametrize("case", FIXTURES, ids=[case["name"] for case in FIXTURES])
def test_model_matches_frozen_racket_witnesses(case):
    assert gen._gravity(case["input"]) == case["output"] == case["expected"]
    assert (not gen.self_check(case["input"])) == case["teaching_expected"]

@pytest.mark.parametrize("band,h,w,texture", list(product(("easy","medium","hard"),(8,24),(7,24),("canonical","contrast"))))
def test_joint_dimension_and_texture_boundaries(band,h,w,texture):
    grid = gen.generate(19,4,difficulty=band,grid_h=h,grid_w=w,texture=texture)
    assert len(grid)==h and all(len(row)==w for row in grid)
    assert gen.self_check(grid)==[]
    assert grid==gen.generate(19,4,difficulty=band,grid_h=h,grid_w=w,texture=texture)

@pytest.mark.parametrize("axis,value",[("grid_h",7),("grid_h",25),("grid_w",6),("grid_w",25),("grid_w",True),("grid_w",7.0),("grid_w","7")])
def test_invalid_axis_values_fail(axis,value):
    with pytest.raises((ValueError,TypeError)):
        gen.generate(19,0,**{axis:value})

@pytest.mark.parametrize("texture",gen.DEGENERATE_TEXTURES)
def test_negative_fixtures_are_explicitly_outside_teaching_domain(texture):
    grid=gen.generate(19,0,texture=texture,grid_h=8,grid_w=7)
    assert len(grid)==8 and len(grid[0])==7
    assert gen.self_check(grid)
    assert texture not in gen.AXES["texture"]["valid"].split("|")

@pytest.mark.parametrize("band",["easy","medium","hard"])
def test_canonical_anchor_support_in_every_band(band):
    for seed in (0,1,7,31):
        assert gen.strict_canonical_like(gen.generate(seed,0,difficulty=band))==[]


def test_all_declared_rivals_are_deterministic_and_leave_inputs_unchanged():
    grid=gen.generate(19,1,texture="contrast")
    saved=[row[:] for row in grid]
    for rival in gen.SEMANTIC_RIVALS.values():
        assert rival(grid)==rival(grid)
        assert grid==saved


def independently_adaptive_sort(grid):
    result=[row[:] for row in grid]
    for col in range(len(grid[0])):
        start=0
        for stop in range(len(grid)+1):
            if stop==len(grid) or grid[stop][col]==8:
                values=[grid[r][col] for r in range(start,stop) if grid[r][col]!=0]
                if len(values)>1:
                    values=sorted(values,reverse=values[0]>values[1])
                for r in range(start,stop):
                    result[r][col]=0
                for r,value in zip(range(stop-len(values),stop),values):
                    result[r][col]=value
                start=stop+1
    return result


@pytest.mark.parametrize("band,seed,start", [('easy', 3228884894, 29), ('easy', 3510205454, 5), ('medium', 1587572304, 5), ('medium', 42745292, 6), ('hard', 2203943415, 9), ('hard', 3119307146, 1)])
def test_adaptive_sort_has_repeated_lesson_evidence(band,seed,start):
    grids=[gen.generate(seed,start+i,difficulty=band) for i in range(6)]
    assert sum(independently_adaptive_sort(grid)!=gen._gravity(grid) for grid in grids)>=2


def test_adaptive_sort_is_a_declared_canonical_fitting_rival():
    assert "adaptive_direction_sort" in gen.CANONICAL_SHORTCUTS
    wrong=gen.CANONICAL_SHORTCUTS["adaptive_direction_sort"]
    for pair in canonical_pairs(TASK,root=ROOT):
        assert wrong(pair["input"])==pair["output"]
    for case in FIXTURES:
        assert wrong(case["input"])==independently_adaptive_sort(case["input"])
