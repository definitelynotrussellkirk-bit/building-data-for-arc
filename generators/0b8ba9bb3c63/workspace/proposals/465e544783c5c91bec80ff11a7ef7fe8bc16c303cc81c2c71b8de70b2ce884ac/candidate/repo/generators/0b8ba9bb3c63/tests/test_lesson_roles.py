"""Behavioral regressions for role-teaching across ordinary lesson windows."""
import copy
import json
from pathlib import Path
import pytest
from reviewer_support import find_root, load_selected_generator

ROOT = find_root(__file__)
G, SOURCE, SOURCE_SHA = load_selected_generator("0b8ba9bb3c63", root=ROOT)


def blue_only(grid):
    objects = G._components(grid)
    cyan = next(o for o in objects if o["color"] == 8)
    blockers = [o for o in objects if o["color"] not in (2,8)]
    output = G._paint_cross(grid, cyan, [o for o in blockers if o["color"] == 1])
    for o in blockers:
        for r,c in o["cells"]:
            output[r][c] = o["color"]
    return output


def test_seed8_demonstrations_refute_blue_only_before_generalized_query():
    grids = [G.generate(8, i) for i in range(4)]
    assert any(blue_only(g) != G.rule_mirror(g) for g in grids[:3]), "the reported seed-8 three-demo lesson still teaches only blue blockers"


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_schedule_start_and_query_holdout_retains_role_evidence(band):
    grids = [G.generate(17,i,difficulty=band) for i in range(8)]
    for start in range(5):
        window = grids[start:start+4]
        for holdout in range(4):
            demos = [g for i,g in enumerate(window) if i != holdout]
            assert any(blue_only(g) != G.rule_mirror(g) for g in demos), (band,start,holdout)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_generalized_draw_is_an_actual_color_role_witness(band):
    for i in range(20):
        grid = G.generate(29,i,difficulty=band,scene_family="generalized")
        assert G.self_check(grid) == []
        assert blue_only(grid) != G.rule_mirror(grid)


def test_exact_scene_override_takes_precedence_and_is_recorded():
    from puzzle_generators.base import set_ctx_observer
    for family in ("public", "generalized"):
        contexts=[]
        set_ctx_observer(contexts.append)
        try:
            grid=G.generate(8,0,scene_family=family)
        finally:
            set_ctx_observer(None)
        assert G.observe_overrides(grid)["scene_family"] == family
        assert contexts[0].overrides_used() == {"scene_family":family}
        assert contexts[0].axis_value("scene_family") == family


def test_blue_only_contract_is_pure_and_does_not_claim_universal_identity():
    assert G.LESSON_SCHEDULE_PERIOD == 5
    assert "blue_only_blocks" in G.LESSON_COMPETITORS
    assert "blue_only_blocks" in G.CANONICAL_SHORTCUTS
    grid=G.generate(11,1)
    original=copy.deepcopy(grid)
    assert G.LESSON_COMPETITORS["blue_only_blocks"](grid) == blue_only(grid)
    assert grid == original


@pytest.mark.parametrize("name,value", [("seed",True),("seed",False),("seed",1.0),("seed",1.75),("seed","1"),("sample_index",True),("sample_index",False),("sample_index",1.0),("sample_index",1.75),("sample_index","1"),("sample_index",-1)])
def test_reject_invalid_seed_and_index_scalars(name,value):
    args={"seed":991,"sample_index":0}
    args[name]=value
    with pytest.raises((TypeError,ValueError)):
        G.generate(**args)


def test_selected_authority_text_matches_canonical_but_archival_raw_is_retained():
    from reviewer_support import canonical_path
    canonical=next(json.loads(line)["program_solution"] for line in canonical_path(ROOT).read_text().splitlines() if json.loads(line).get("task_id")=="0b8ba9bb3c63")
    data=ROOT/"shared/data" if (ROOT/"shared/data").is_dir() else ROOT/"data"
    for family,identifier in (("training","0b8ba9bb3c63"),("augmented","7a159f50b0e0")):
        row=json.loads((data/f"base/solutions/{family}/6ffe8f07__{identifier}.json").read_text())
        assert row["racket_target"]["target_code"] == canonical
        import hashlib
        assert hashlib.sha256(row["racket_target"]["raw_code"].encode()).hexdigest() == "e50f7da3fcaf4ab3b5de00698811e0e103c8e3f982755c9d8f5e2ff05165779d"
