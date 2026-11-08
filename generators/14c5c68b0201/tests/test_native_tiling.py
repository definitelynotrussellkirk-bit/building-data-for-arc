"""Native tiling contract: count independence, teaching, size and privacy."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import find_root, public_challenge_bytes

HOME = Path(__file__).resolve().parents[1]
AXES = ("both", "horizontal", "vertical")


@pytest.fixture(scope="module")
def adapter():
    path = HOME / "workspace/parametric/adapter.py"
    if not path.is_file():
        pytest.fail("Native root tiling adapter is not implemented")
    spec = importlib.util.spec_from_file_location("native_tiling_contract", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_is_exact_canonical_and_all_settings_change_labels(adapter):
    from arcpuzzles import Catalog
    canonical = {v["program_solution"] for v in Catalog(find_root(__file__))._variants()["14c5c68b0201"]}
    assert canonical == {adapter.program({"tiling_axes": "both"})}
    episodes = [adapter.generate(0, {"tiling_axes": axis}, 2, 4) for axis in AXES]
    assert len({episode["program_solution"] for episode in episodes}) == 3
    for i in range(6):
        assert len({json.dumps((ep["train"] + ep["test"])[i]["output"]) for ep in episodes}) == 3


@pytest.mark.parametrize("demos,queries", [(2, 1), (3, 4), (6, 4)])
def test_supported_counts_have_distinct_setting_independent_inputs(adapter, demos, queries):
    episodes = [adapter.generate(17, {"tiling_axes": axis}, demos, queries) for axis in AXES]
    inputs = []
    for episode in episodes:
        assert len(episode["train"]) == demos and len(episode["test"]) == queries
        grids = [pair["input"] for pair in episode["train"] + episode["test"]]
        assert len({json.dumps(g) for g in grids}) == demos + queries
        inputs.append(grids)
    assert inputs[0] == inputs[1] == inputs[2]


def test_count_changes_keep_both_prefixes_and_actor_first_turn(adapter):
    settings = {"tiling_axes": "horizontal"}
    small = adapter.generate(5, settings, 2, 1)
    large = adapter.generate(5, settings, 6, 4)
    assert small["train"] == large["train"][:2]
    assert small["test"] == large["test"][:1]
    single = adapter.generate(5, settings, 6, 1)
    assert public_challenge_bytes(adapter.visible_turn(large, 0)) == public_challenge_bytes(single)


@pytest.mark.parametrize("axis", AXES)
def test_first_two_demos_refute_the_declared_finite_rivals(adapter, axis):
    settings = {"tiling_axes": axis}
    ep = adapter.generate(0, settings, 2, 4)
    report = adapter.teaching_report(ep["train"], settings)
    assert report["rival_count"] >= 8 and report["all_refuted"], report
    scenes = [adapter.observables(p["input"]) for p in ep["train"]]
    assert {scene["background"] for scene in scenes} == {8, 9}
    assert any(len(scene["holes"]) > 1 for scene in scenes)
    assert all(hole["period"] != [2, 2] for scene in scenes for hole in scene["holes"])


def test_thirty_square_is_a_real_multi_hole_tiling_scene(adapter):
    ep = adapter.generate(17, {"tiling_axes": "both"}, 6, 4)
    query = ep["test"][-1]
    scene = adapter.observables(query["input"])
    assert (scene["height"], scene["width"]) == (30, 30)
    assert len(scene["holes"]) == 2
    area = sum((h["bbox"][2]-h["bbox"][0]+1)*(h["bbox"][3]-h["bbox"][1]+1) for h in scene["holes"])
    assert area >= 288
    assert min(h["bbox"][0] for h in scene["holes"]) == 1
    assert max(h["bbox"][2] for h in scene["holes"]) == 28
    assert sum(a != b for ra, rb in zip(query["input"], query["output"]) for a, b in zip(ra, rb)) > 100


@pytest.mark.parametrize("axis", ["both", "vertical"])
def test_fixed_three_row_period_is_refuted_before_queries(adapter, axis):
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule
    settings={"tiling_axes":axis}
    ep=adapter.generate(0,settings,2,4)
    source=adapter.program(settings)
    site="(sh (+ 1 (- sr2 sr1)))"
    assert source.count(site)==1
    wrong=source.replace(site,"(sh 3)",1)
    with RacketBridge(timeout=10.0,startup_timeout=30.0) as bridge:
        def apply(grid):
            literal="'("+' '.join('('+' '.join(map(str,row))+')' for row in grid)+')'
            return bridge.eval_text(f'({wrap_rule(wrong)} {literal})')
        query=ep['test'][0]
        query_prediction=apply(query['input'])
        assert query_prediction != query['output']
        assert query_prediction == adapter.rival_output('fixed_height_3',query['input'],settings)
        predictions=[apply(pair['input']) for pair in ep['train']]
        assert all(prediction == adapter.rival_output('fixed_height_3',pair['input'],settings)
                   for prediction,pair in zip(predictions,ep['train']))
        assert any(prediction != pair['output'] for prediction,pair in zip(predictions,ep['train'])), 'fixed height 3 survives every demonstration'
    periods={h['period'][0] for p in ep['train'] for h in adapter.observables(p['input'])['holes']}
    assert periods=={2,3}


@pytest.mark.parametrize("demos,queries", [(1,4),(7,4),(3,0),(3,5),(True,4),(3,4.0)])
def test_invalid_counts_are_rejected(adapter, demos, queries):
    with pytest.raises((TypeError,ValueError)):
        adapter.generate(0,{"tiling_axes":"both"},demos,queries)


@pytest.mark.parametrize("seed", [True,-1,1.5,"1",2**63])
def test_invalid_seed_is_rejected(adapter, seed):
    with pytest.raises((TypeError,ValueError)):
        adapter.generate(seed,{"tiling_axes":"both"},2,1)


@pytest.mark.parametrize("settings", [{},{"tiling_axes":True},{"tiling_axes":"other"},{"tiling_axes":"both","other":1}])
def test_invalid_settings_are_rejected(adapter, settings):
    with pytest.raises((TypeError,ValueError)):
        adapter.generate(0,settings,2,1)


def test_private_changes_do_not_change_visible_bytes_or_actor_copy(adapter):
    ep = adapter.generate(0,{"tiling_axes":"vertical"},2,4)
    before = public_challenge_bytes(ep)
    changed = deepcopy(ep)
    changed.update(seed=999,settings={"hidden":True},program_solution="private")
    for pair in changed["test"]:
        pair["output"]=[[0]]
    assert public_challenge_bytes(changed) == before
    turn = adapter.visible_turn(ep,0)
    assert set(turn)=={"train","test"} and len(turn["test"])==1 and set(turn["test"][0])=={"input"}
    turn["train"][0]["input"][0][0]=0
    assert public_challenge_bytes(ep)==before


def test_writer_hashes_exact_public_bytes_and_rejects_visible_duplicates(adapter,tmp_path):
    eps=[adapter.generate(0,{"tiling_axes":axis},2,4) for axis in AXES]
    result=adapter.write_batch(eps,tmp_path/'batch')
    assert len(result["public_ids"])==3 and result["public_ids"]==sorted(result["public_ids"])
    assert result["turn_count"]==12
    for folder in ('public','turns'):
        for path in (tmp_path/'batch'/folder).glob('*.json'):
            assert hashlib.sha256(path.read_bytes()).hexdigest()==path.stem
            public=json.loads(path.read_bytes())
            assert set(public)=={"train","test"}
            assert all(set(pair)=={"input"} for pair in public["test"])
    clone=deepcopy(eps[0]);clone['settings']={'private':'changed'}
    with pytest.raises(ValueError,match='duplicate'):
        adapter.write_batch([eps[0],clone],tmp_path/'duplicate')
    assert not (tmp_path/'duplicate').exists()
