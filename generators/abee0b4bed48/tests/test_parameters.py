"""Behavioral tests for decoding followed by frequency ordering."""
from __future__ import annotations

import copy
import importlib.util
from collections import Counter
from itertools import groupby
from pathlib import Path

import pytest

HOME=Path(__file__).resolve().parents[1]


def load():
    path=HOME/"workspace/parametric/adapter.py"
    assert path.is_file(), "Native parametric adapter has not been built"
    spec=importlib.util.spec_from_file_location("test_frequency_adapter",path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def tile(cells):
    return [[5 if (r,c) in cells else 0 for c in range(3)] for r in range(3)]


def combine(tiles):
    return [[v for t in tiles for v in t[r]] for r in range(3)]


def labels_grid(labels):
    return [[v for label in labels for v in [label]*3] for _ in range(3)]


def test_native_adapter_surface():
    m=load()
    assert callable(m.generate) and callable(m.program)


def test_default_preserves_exact_canonical_bytes():
    from arcpuzzles import Catalog
    m=load()
    canonical={v["program_solution"] for v in Catalog(HOME.parents[1]).get(HOME.name)["variants"]}
    assert canonical=={m.program({"order":"input"})}


def test_programs_are_single_complete_rule_expressions():
    from arc_repl.parser import parse_all,Symbol
    for mode in ("input","frequency"):
        forms=parse_all(load().program({"order":mode}))
        assert len(forms)==1 and forms[0][0]==Symbol("rule!")


@pytest.mark.parametrize("seed", [0,17])
def test_sorted_demos_distinguish_every_fixed_decoder_label_permutation(seed):
    m=load();ep=m.generate(seed,{"order":"frequency"},3,4)
    counts=[Counter(m.decode(p["input"])) for p in ep["train"]]
    classes=(0,1,3,4,6,9)
    signatures={label:tuple(c[label] for c in counts) for label in classes}
    assert all(any(signature) for signature in signatures.values())
    assert len(set(signatures.values()))==len(classes), signatures


@pytest.mark.parametrize("seed", [2,6])
def test_demos_refute_contiguous_run_count(seed):
    m=load();ep=m.generate(seed,{"order":"frequency"},3,4)
    def wrong(grid):
        labels=m.decode(grid)
        runs=Counter(label for label,_ in groupby(labels))
        ordered=sorted(labels,key=lambda label:(-runs[label],label))
        return labels_grid(ordered)
    assert any(wrong(p["input"])!=p["output"] for p in ep["test"]), "lost original query witness"
    assert not all(wrong(p["input"])==p["output"] for p in ep["train"])


@pytest.mark.parametrize("cells,label", [
    ({(0,0)},4),({(2,2)},4),
    ({(r,c) for r in range(3) for c in range(3)}-{(1,1)},3),
    ({(r,c) for r in range(3) for c in range(3)}-{(0,0)},3),
    ({(0,c) for c in range(3)},6),({(2,c) for c in range(3)},1),
    ({(1,c) for c in range(3)},9),({(r,r) for r in range(3)},9),
    ({(0,0),(0,1),(1,0)},9),(set(),0),({(0,0),(0,1)},0),
    ({(r,c) for r in range(3) for c in range(3)},0)])
def test_tile_classification_includes_all_fallback_counts(cells,label):
    m=load();g=tile(cells)
    assert m.decode(g)==[label]
    for mode in ("input","frequency"):
        assert m.mirror(g,{"order":mode})==labels_grid([label])


def example():
    return combine([tile({(0,c) for c in range(3)}),tile({(1,1)}),
        tile({(2,c) for c in range(3)}),tile({(r,r) for r in range(3)}),
        tile({(r,c) for r in range(3) for c in range(3)}-{(1,1)}),
        tile({(1,c) for c in range(3)})])


def test_frequency_uses_decoded_classes_and_numeric_label_ties():
    m=load();g=example();original=copy.deepcopy(g)
    assert m.first_stage(g,{"order":"frequency"})==[6,4,1,9,3,9]
    a=m.analyze(g,{"order":"frequency"})
    assert a["frequencies"]==[1,1,1,2,1,2]
    assert a["permutation"]==[3,5,2,4,1,0]
    assert a["ordered_labels"]==[9,9,1,3,4,6]
    assert a["output"]==labels_grid([9,9,1,3,4,6])
    assert m.mirror(g,{"order":"input"})==labels_grid([6,4,1,9,3,9])
    assert g==original


def test_zero_is_a_real_decoded_class_in_frequency_and_tie_counts():
    m=load()
    tiles=[tile({(0,c) for c in range(3)}),tile({(r,r) for r in range(3)}),tile(set()),
      tile({(2,c) for c in range(3)}),tile({(1,c) for c in range(3)}),tile({(0,0),(0,1)}),
      tile({(1,1)}),tile({(r,c) for r in range(3) for c in range(3)}-{(0,0)})]
    assert m.mirror(combine(tiles),{"order":"frequency"})==labels_grid([0,0,9,9,1,3,4,6])


@pytest.mark.parametrize("g", [[],[[0]*3],[[0]*3]*2,[[0]*3]*4,[[0]*30]*30,
    [[0]*2]*3,[[0]*4]*3,[[0]*33]*3,[[0,0,0],[0,0],[0,0,0]],
    [[0,0,0],[0,True,0],[0,0,0]],[[0,0,0],[0,5.0,0],[0,0,0]],
    [[0,0,0],[0,7,0],[0,0,0]],((0,0,0),)*3])
def test_invalid_grid_geometry_and_types_rejected(g):
    with pytest.raises((ValueError,TypeError)):
        load().mirror(g,{"order":"input"})


@pytest.mark.parametrize("settings", [{},{"order":True},{"order":"bad"},{"order":"input","x":0},None,[]])
def test_invalid_settings_rejected(settings):
    with pytest.raises((ValueError,TypeError)):
        load().program(settings)


@pytest.mark.parametrize("change", [{"seed":True},{"seed":-1},{"seed":2**63},
    {"demos":2},{"demos":7},{"demos":3.0},{"queries":0},{"queries":5},{"queries":True}])
def test_invalid_request_rejected(change):
    args=dict(seed=0,settings={"order":"input"},demos=3,queries=4);args.update(change)
    with pytest.raises((ValueError,TypeError)):
        load().generate(**args)


def test_settings_share_inputs_and_counts_have_stable_novel_prefixes():
    m=load()
    for seed in (0,17,2**63-1):
        a=m.generate(seed,{"order":"input"},6,4)
        b=m.generate(seed,{"order":"frequency"},6,4)
        pristine=copy.deepcopy(a)
        for split in ("train","test"):
            assert [p["input"] for p in a[split]]==[p["input"] for p in b[split]]
        assert any(x["output"]!=y["output"] for x,y in zip(a["train"][:3],b["train"][:3]))
        for demos in range(3,7):
            for queries in range(1,5):
                got=m.generate(seed,{"order":"input"},demos,queries)
                assert got["train"]==a["train"][:demos] and got["test"]==a["test"][:queries]
        inputs=[p["input"] for split in ("train","test") for p in a[split]]
        assert len({str(g) for g in inputs})==10
        a["train"][0]["input"][0][0]=9
        assert m.generate(seed,{"order":"input"},6,4)==pristine
        assert b["train"][0]["input"][0][0]!=9


def test_maximum_width_has_ten_substantial_zones_and_full_output():
    m=load()
    for seed in range(4):
        ep=m.generate(seed,{"order":"frequency"},3,4)
        largest=[p for p in ep["test"] if len(p["input"][0])==30]
        assert len(largest)==1
        p=largest[0]
        assert len(p["input"])==len(p["output"])==3 and len(p["output"][0])==30
        assert sum(v==5 for row in p["input"] for v in row)>=40
        assert len(m.decode(p["input"]))==10
