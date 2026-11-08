"""Focused contracts for the merged three-choice domino family."""
import hashlib
import importlib.util
import json
from pathlib import Path
from copy import deepcopy

HOME=Path(__file__).resolve().parents[1]/"workspace/parametric"
SPEC=importlib.util.spec_from_file_location("domino_union_test",HOME/"prototype.py")
P=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(P)
SETTINGS=[{"preprocess":v} for v in ("none","blue_to_gray","nearest_vertical")]
EXPECTED={"none":"bba257d19e2b9ed977892b09ef1fa837029e8c9a96a819e0d356d2c04f708f44","nearest_vertical":"4fe45e1b31173ea2411c73ffe9a7f11e306d2ef585d19b92cb0ef1efd9aa73a3"}


def test_exact_legacy_and_reviewer_programs():
    for name,wanted in EXPECTED.items():
        assert hashlib.sha256(P.program({"preprocess":name}).encode()).hexdigest()==wanted
    body=P.CANONICAL_PROGRAM[len("(rule! "):-1]
    assert P.program(SETTINGS[1])=="(rule! (let ((g (cellmap g (r c v) (if (= v 1) 5 v)))) "+body+"))"
    contract=json.loads((HOME/"promotion.json").read_text())
    assert contract["parameters"]=={"preprocess":["none","blue_to_gray","nearest_vertical"]}
    assert contract["default"]==SETTINGS[0]


def test_shared_grammar_teaches_three_distinct_rules_and_unique_anchor():
    for seed in (0,17,29,2**63-1):
        episodes=[P.generate(seed,s,2,4) for s in SETTINGS]
        for index,pair in enumerate(episodes[0]["train"]+episodes[0]["test"]):
            grid=pair["input"]
            assert all((e["train"]+e["test"])[index]["input"]==grid for e in episodes)
            assert len({json.dumps((e["train"]+e["test"])[index]["output"]) for e in episodes})==3
            anchor,targets,nearest=P.nearest_analysis(grid)
            assert len(anchor)==2 and len(targets)>=2
            distances=sorted(P.object_distance(anchor,cells) for cells in targets)
            assert distances[0]<distances[1]
            assert nearest in targets


def test_nearest_literal_distance_witness_and_no_mutation():
    grid=[[0]*12 for _ in range(9)]
    for r,c in ((1,7),(2,7),(1,3),(1,4),(6,0),(6,1)):
        grid[r][c]=5
    grid[8][:3]=[5,5,1]
    before=deepcopy(grid);out=P.transform(grid,SETTINGS[2])
    assert out[1][3:5]==[8,8]
    assert out[6][:2]==[5,5] and out[8][:3]==[5,5,1]
    assert grid==before


def test_one_turn_hides_query_count_future_data_and_private_fields():
    for settings in SETTINGS:
        one=P.generate(17,settings,3,1);four=P.generate(17,settings,3,4)
        projected=P.public_turn(four,0)
        assert projected==P.public_turn(one,0)
        assert set(projected)=={"train","test"} and len(projected["test"])==1
        assert set(projected["test"][0])=={"input"}
        changed=deepcopy(four);changed.update(seed=8,settings={"secret":9},program_solution="secret")
        for pair in changed["test"]:
            pair["output"]=[[9]]
        for pair in changed["test"][1:]:
            pair["input"]=[[9]]
        assert P.public_turn(changed,0)==projected


def test_first_demo_rejects_metric_and_position_shortcuts():
    for seed in (0,17,29,71,97,101):
        episode=P.generate(seed,SETTINGS[2],2,4)
        grid=episode["train"][0]["input"]
        _,_,nearest=P.nearest_analysis(grid)
        assert all(target!=nearest for target in P.nearest_shortcuts(grid).values())
