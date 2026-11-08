"""Focused proposed-prototype regressions; no canonical source changes."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import public_challenge_bytes, public_challenge_id, canonical_pairs

SOURCE = Path(__file__).parents[1] / "workspace/parametric/prototype.py"
SPEC = importlib.util.spec_from_file_location("zero_parametric", SOURCE)
P = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P)


@pytest.fixture(scope="module")
def default_episode():
    return P.build_episode(17, mode="both", protected_color=2)


def test_counts_distinct_lawful_and_teaching(default_episode):
    e = default_episode
    assert [len(e[k]) for k in ("train", "test")] == [3, 4]
    pairs = e["train"] + e["test"]
    assert len({json.dumps(p["input"]) for p in pairs}) == 7
    for p in pairs:
        assert P.GEN.self_check(p["input"]) == []
        assert P.input_witnesses(p["input"])
    assert e["private"]["teaching"]["parameter_survivors"] == [["both", 2]]
    assert all(q["agreement"] for q in e["private"]["teaching"]["queries"])


@pytest.mark.parametrize("train,test", [(1,1),(2,4),(4,2)])
def test_separate_counts(train, test):
    e = P.build_episode(29, n_train=train, n_test=test, mode="rows", protected_color=7)
    assert len(e["train"]) == train and len(e["test"]) == test


@pytest.mark.parametrize("kwargs", [{"n_train":0},{"n_test":0},{"n_train":True},
    {"n_test":33},{"mode":"diagonal"},{"protected_color":0},{"protected_color":True},
    {"seed":-1},{"seed":2**32},{"max_attempts":0}])
def test_invalid_domains(kwargs):
    args={"seed":17, **kwargs}
    with pytest.raises(ValueError):
        P.build_episode(**args)


def test_determinism_and_alternative_effect(default_episode):
    e = P.build_episode(17, mode="both", protected_color=2)
    assert e == default_episode
    alt = P.build_episode(17, mode="columns", protected_color=7)
    assert [p["input"] for p in e["train"]+e["test"]] == [p["input"] for p in alt["train"]+alt["test"]]
    assert any(a["output"] != b["output"] for a,b in zip(e["test"],alt["test"]))
    assert P.build_episode(18, n_train=1, n_test=1) == P.build_episode(18, n_train=1, n_test=1)


def test_all_27_materialized_programs_match_countermodels_and_canonical():
    representatives = [P.sample_input(3, i)[0] for i in range(3)]
    canonical = canonical_pairs(P.TASK, root=P.ROOT, labeled_only=True)
    with P.RacketLabeler() as labeler:
        for mode, protected in P.SETTINGS:
            program = P.materialize_program(mode, protected)
            for g in representatives:
                assert labeler.label(program,g) == P.countermodel(g,mode,protected)
        default_program = P.materialize_program("both",2)
        for pair in canonical:
            assert labeler.label(default_program,pair["input"]) == pair["output"]
    assert len({P.materialize_program(*s) for s in P.SETTINGS}) == 27


def test_demo_only_survivors_ignore_query_answers(default_episode):
    e = copy.deepcopy(default_episode)
    expected = P.assess_teaching(e["train"], [p["input"] for p in e["test"]])
    for pair in e["test"]:
        pair["output"] = [[9]]
    e["private"] = {"seed":999,"settings":["rows",9]}
    assert P.assess_teaching(e["train"], [p["input"] for p in e["test"]]) == expected
    weak = [{"input":[[0]],"output":[[0]]}]
    report=P.assess_teaching(weak, [[[0,1],[2,3]]])
    assert len(report["parameter_survivors"]) == 27
    assert report["queries"][0]["agreement"] is False


def test_public_projection_mutations_and_exact_writer(default_episode,tmp_path):
    original=copy.deepcopy(default_episode)
    changed=copy.deepcopy(original)
    changed["private"]={"seed":987,"setting":"hidden"}
    for p in changed["test"]: p["output"]=[[9]]
    assert public_challenge_bytes(original)==public_challenge_bytes(changed)
    assert public_challenge_id(original)==public_challenge_id(changed)
    p1=P.write_batch([original],tmp_path/"one")
    p2=P.write_batch([changed],tmp_path/"two")
    assert p1["public_ids"]==p2["public_ids"]
    id=p1["public_ids"][0]
    b=(tmp_path/"one/public"/(id+".json")).read_bytes()
    assert hashlib.sha256(b).hexdigest()==id
    assert b==public_challenge_bytes(original)
    assert set(json.loads(b)["test"][0])=={"input"}
    changed=copy.deepcopy(original); changed["train"][0]["output"][0][0]=(changed["train"][0]["output"][0][0]+1)%10
    assert public_challenge_id(original)!=public_challenge_id(changed)
    changed=copy.deepcopy(original); changed["test"][0]["input"][0][0]=(changed["test"][0]["input"][0][0]+1)%10
    assert public_challenge_id(original)!=public_challenge_id(changed)


def test_fail_closed_directory_and_duplicate_visible(default_episode,tmp_path):
    target=tmp_path/"existing"; target.mkdir(); (target/"keep").write_text("keep")
    with pytest.raises(FileExistsError): P.write_batch([default_episode],target)
    assert (target/"keep").read_text()=="keep"
    target=tmp_path/"duplicates"
    clone=copy.deepcopy(default_episode); clone["private"]={}
    with pytest.raises(ValueError,match="duplicate"): P.write_batch([default_episode,clone],target)
    assert not target.exists()


def test_public_batch_order_independent_of_input_order(default_episode,tmp_path):
    second=P.build_episode(20,n_train=1,n_test=1,mode="rows",protected_color=4)
    a=P.write_batch([default_episode,second],tmp_path/"a")
    b=P.write_batch([second,default_episode],tmp_path/"b")
    assert a["public_ids"]==b["public_ids"]==sorted(a["public_ids"])
    assert (tmp_path/"a/public/index.json").read_bytes()==(tmp_path/"b/public/index.json").read_bytes()


def test_fresh_zero_rival_reaches_true_fixed_point_across_protected_barriers():
    grid=[[2]*12 for _ in range(12)]
    grid[0][0]=0
    for r,c in ((0,1),(1,0),(1,1),(6,6)): grid[r][c]=1
    assert P.GEN.self_check(grid)==[]
    assert P.countermodel(grid,"both",2,rival="fresh_zero")[6][6]==1
    assert P.countermodel(grid,"both",2,rival="global")[6][6]==0
    # Independent authority: literally repeat the one-round Racket operation.
    with P.RacketLabeler() as labeler:
        program=P.materialize_program("both",2)
        once=labeler.label(program,grid)
        twice=labeler.label(program,once)
        assert twice==labeler.label(program,twice)
        assert once!=twice
        assert P.countermodel(grid,"both",2,rival="fresh_zero")==twice
