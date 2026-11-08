"""Independent regressions for leaf-component semantics and exact controls."""
import importlib.util
import hashlib
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root

TASK_ID = "9f05dcdedf35"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name,path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def modules():
    root = find_root(__file__)
    homes = [root/"generators"/TASK_ID,root/"puzzle_generators"/"per_puzzle"/TASK_ID]
    home = next(p for p in homes if (p/"generator.py").is_file())
    return (load(home/"generator.py","leaf_generator_test"),
            load(home/"workspace"/"semantic_probe.py","independent_leaf_probe"),root)


def test_canonical_input8_and_component_shapes_are_accepted(modules):
    gen,probe,root = modules
    for pair in canonical_pairs(TASK_ID,root=root):
        assert gen.self_check(pair["input"]) == [],(pair["split"],pair["pair_index"])
        assert probe.intended(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band",["easy","medium","hard"])
def test_default_teaching_branches_expose_all_distinctions(modules,band):
    gen,probe,_ = modules
    for seed in (0,7,29):
        for index in (0,1,4,5):
            grid = gen.generate(seed,index,difficulty=band)
            objs,edges = probe.graph(grid)
            assert sorted(len(neighbors) for neighbors in edges if neighbors) == [1,1,1,2,3]
            assert sum(not neighbors for neighbors in edges) in (2,3)
            assert all(len(objs[i][1]) == 4 for i,neighbors in enumerate(edges) if neighbors)
            assert gen.self_check(grid) == []
            label = probe.intended(grid)
            assert all(probe.predict(grid,name) != label for name in probe.RIVAL_NAMES)
            assert grid == gen.generate(seed,index,difficulty=band)


@pytest.mark.parametrize("palette_size",[5,6])
@pytest.mark.parametrize("band",["easy","medium","hard"])
def test_both_teaching_palettes_distinguish_component_count_from_neighbor_colors(modules,palette_size,band):
    gen,probe,_ = modules
    for index in (0,1):
        grid = gen.generate(37,index,difficulty=band,palette_size=palette_size)
        label = probe.intended(grid)
        assert all(probe.predict(grid,name) != label for name in probe.RIVAL_NAMES)
        objs,edges = probe.graph(grid)
        assert any(len(neighbors) == 2 and objs[i][0] != 8
                   and len({objs[j][0] for j in neighbors}) == 1
                   for i,neighbors in enumerate(edges))


@pytest.mark.parametrize("band",[None,"easy","medium","hard"])
@pytest.mark.parametrize("controls",[
    dict(height=8,width=8,palette_size=5,chain_orientation="horizontal",graph_shape="chain",component_span=2),
    dict(height=8,width=8,palette_size=6,chain_orientation="vertical",graph_shape="branch",component_span=2),
    dict(height=14,width=16,palette_size=5,chain_orientation="vertical",graph_shape="chain",component_span=1),
    dict(height=9,width=11,palette_size=6,chain_orientation="horizontal",graph_shape="branch",component_span=1),
])
def test_controls_are_observable_independently(modules,band,controls):
    gen,probe,_ = modules
    for index in (0,1,2,3):
        grid = gen.generate(17,index,difficulty=band,**controls)
        assert gen.self_check(grid) == []
        assert probe.observe(grid) == controls


@pytest.mark.parametrize("controls",[
    {"height":True},{"height":8.0},{"width":"8"},{"component_span":False},
    {"palette_size":5.0},{"height":7},{"height":15},{"width":7},{"width":17},
    {"palette_size":4},{"palette_size":7},{"component_span":0},{"component_span":3},
    {"chain_orientation":"diagonal"},{"graph_shape":"ring"},
    {"texture":"all_isolated"},{"palette_kind":"warm"},{"unknown_axis":1},
])
def test_invalid_or_retired_controls_raise(modules,controls):
    gen,_,_ = modules
    with pytest.raises((ValueError,TypeError)):
        gen.generate(0,0,**controls)


@pytest.mark.parametrize("grid",[
    None,[],[[]],[None],[[0,1],[0]],[[True,0],[0,0]],
    [[0,10],[0,0]],[[0,"2"],[0,0]],[[0,1.0],[0,0]],
    [[0]*31],[[0,0],[0,0]],[[2,3,4]],
])
def test_bad_or_no_contrast_inputs_reject_without_crashing(modules,grid):
    gen,_,_ = modules
    try:
        errors = gen.self_check(grid,meta={"texture":"all_isolated"})
    except Exception as exc:
        pytest.fail(f"validator raised {type(exc).__name__}: {exc}")
    assert isinstance(errors,list) and errors


def test_repeated_leaf_and_isolate_color_preserves_object_identity(modules):
    gen,probe,_ = modules
    grid = [[0]*7 for _ in range(4)]
    grid[1][1:4] = [2,3,4]
    grid[3][6] = 2
    grid[3][0] = 8
    assert gen.self_check(grid) == []
    output = probe.intended(grid)
    assert output[1][1] == output[1][3] == 8
    assert output[1][2] == 3 and output[3][6] == 2 and output[3][0] == 8


@pytest.mark.parametrize("band",["easy","medium","hard"])
def test_default_lesson_rotations_have_no_declared_ambiguity(modules,band):
    gen,probe,_ = modules
    for start in range(4):
        grids = [gen.generate(53,start+i,difficulty=band) for i in range(4)]
        labels = list(map(probe.intended,grids))
        for query in range(4):
            for name in probe.RIVAL_NAMES:
                if all(probe.predict(grids[i],name)==labels[i] for i in range(4) if i!=query):
                    assert probe.predict(grids[query],name)==labels[query],(start,query,name)


@pytest.mark.parametrize("name",["canonical_input8","canonical_multicell_leaf","teaching_nonmax_degree","neighbor_colors_teaching"])
def test_retained_authority_examples_have_replayable_semantic_distinctions(modules,name):
    gen,probe,_ = modules
    home = Path(__file__).resolve().parents[1]
    fixture = json.loads((home/"counterexamples"/(name+".json")).read_text())
    grid,output = fixture["input"],fixture["output"]
    assert fixture["actual_racket"] is True
    assert fixture["rule_hash"] == gen.RULE_HASH
    assert hashlib.sha256(json.dumps(grid,separators=(",",":")).encode()).hexdigest() == fixture["input_sha256"]
    assert hashlib.sha256(json.dumps(output,separators=(",",":")).encode()).hexdigest() == fixture["output_sha256"]
    assert gen.self_check(grid) == fixture["current_validator"] == []
    assert probe.intended(grid) == output
    rival = probe.predict(grid,fixture["rival_name"])
    assert rival == fixture["rival_prediction"]
    differences = [[r,c] for r,row in enumerate(output) for c,value in enumerate(row) if value != rival[r][c]]
    assert differences == fixture["differing_coordinates"] and differences
    if name in ("teaching_nonmax_degree","neighbor_colors_teaching"):
        args = fixture["generation"]
        # Retain historical authority examples across VERSION/RNG changes.
        # Exact generation replay applies only to the pinned source bytes.
        source = home/"generator.py"
        if source.is_file() and hashlib.sha256(source.read_bytes()).hexdigest() == fixture["generator_sha256"]:
            assert gen.generate(args["seed"],args["sample_index"],difficulty=args["band"]) == grid
        assert probe.observe(grid) == fixture["observed_axes"]
    if name == "neighbor_colors_teaching":
        before = fixture["before"]
        assert before["actual_racket"] is True
        assert probe.intended(before["input"]) == before["output"]
        assert probe.predict(before["input"],"neighbor_colors") == before["output"]
        assert before["differing_coordinates"] == []
        assert before["generation"] == fixture["generation"]
        assert fixture["observed_axes"]["palette_size"] == 6
