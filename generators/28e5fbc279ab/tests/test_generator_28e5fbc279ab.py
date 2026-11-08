"""Task-local tests: run explicitly; the repository test root is narrower."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import sys
import pytest

HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
sys.path.insert(0, str(REPO / "shared/runtime"))
spec = importlib.util.spec_from_file_location("stamp_generator_under_test", HOME / "generator.py")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def geometry(g):
    ref = {(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v == 3}
    r0,c0 = min(r for r,c in ref),min(c for r,c in ref)
    shape = {(r-r0,c-c0) for r,c in ref}
    markers = [(r,c,v) for r,row in enumerate(g) for c,v in enumerate(row) if v not in (0,3)]
    footprints = [ref] + [{(r+dr,c+dc) for dr,dc in shape} | {(r,c)} for r,c,v in markers]
    return ref, shape, markers, footprints


def test_reject_output_footprint_collision_not_only_input_components():
    g = [[0]*9 for _ in range(7)]
    for c in (0,1,2): g[0][c] = 3
    g[4][3],g[4][5] = 1,2
    assert gen.self_check(g), "two singleton markers create overlapping stamp footprints"


def test_reject_clipped_stamp():
    g = [[0]*9 for _ in range(7)]
    g[0][0:3] = [3,3,3]
    g[6][8] = 1
    assert gen.self_check(g), "the template cannot fit at the bottom-right marker"


def test_no_unknown_overrides_are_silently_accepted():
    with pytest.raises(TypeError): gen.generate(7,0, typo_axis=1)


@pytest.mark.parametrize("band", ["easy","medium","hard"])
def test_declared_dimension_and_count_overrides_work_in_each_band(band):
    for h,w,n in ((6,8,1),(6,8,5),(18,20,5),(9,12,2)):
        g = gen.generate(13,0,difficulty=band,grid_h=h,grid_w=w,n_markers=n)
        assert (len(g),len(g[0])) == (h,w)
        assert len(geometry(g)[2]) == n
        assert gen.self_check(g) == []


def test_layout_is_not_fixed_to_reference_top_left_markers_bottom_right():
    above = left = reference_elsewhere = 0
    for i in range(80):
        g=gen.generate(101,i)
        ref, shape, markers, footprints=geometry(g)
        r0,c0=min(r for r,c in ref),min(c for r,c in ref)
        above += any(r<r0 for r,c,v in markers)
        left += any(c<c0 for r,c,v in markers)
        reference_elsewhere += r0>=len(g)//2 or c0>=len(g[0])//2
    assert min(above,left,reference_elsewhere) > 5, (above,left,reference_elsewhere)


@pytest.mark.parametrize("band", ["easy","medium","hard"])
def test_default_outputs_are_complete_disjoint_and_deterministic(band):
    for i in range(100):
        g=gen.generate(101,i,difficulty=band)
        assert g == gen.generate(101,i,difficulty=band)
        assert gen.self_check(g) == []
        ref,shape,markers,footprints=geometry(g)
        assert all(not a&b for j,a in enumerate(footprints) for b in footprints[j+1:]), i
        assert all(0<=r<len(g) and 0<=c<len(g[0]) for f in footprints for r,c in f), i


def test_canonical_inputs_remain_in_domain():
    for line in (REPO/"shared/data/canonical/puzzles.jsonl").open():
        row=json.loads(line)
        if row.get("task_id")==gen.TASK_ID:
            for pair in row["train"]+[row["test"]]:
                g=[[int(v) for v in r] for r in pair["input"]]
                assert gen.self_check(g)==[]
            return
    pytest.fail("missing canonical task")


def test_motif_bank_has_every_translation_normalized_shape():
    assert [len(gen._motifs(k)) for k in (3,4,5)] == [6,19,63]
    for k in (3,4,5):
        assert len(set(gen._motifs(k))) == len(gen._motifs(k))
        for shape in gen._motifs(k):
            assert len(shape) == k
            assert min(r for r,c in shape) == min(c for r,c in shape) == 0


@pytest.mark.parametrize("band", ["easy","medium","hard"])
def test_crossed_override_boundaries_are_exact(band):
    for h in (6,7,8,9,18):
        for w in (8,9,10,13,20):
            for n in (1,3,5):
                for size in (3,4,5):
                    for anchor in ("occupied","empty"):
                        ov=dict(grid_h=h,grid_w=w,n_markers=n,motif_size=size,anchor_kind=anchor)
                        # The inherited override matrix uses index=17*seed+3,
                        # which aliases (seed+index)%3 to zero. Cover all three
                        # schedule residues explicitly rather than trusting it.
                        for index in range(3):
                            g=gen.generate(29,index,difficulty=band,**ov)
                            assert gen.self_check(g)==[], (ov,index)
                            assert gen.observe_overrides(g)==ov


def test_scheduled_three_demo_windows_refute_all_named_rivals():
    for band in ("easy","medium","hard"):
        for seed in range(8):
            for start in range(6):
                grids=[gen.generate(seed,start+j,difficulty=band) for j in range(4)]
                pairs=[dict(input=g,output=gen.rule_mirror(g)) for g in grids]
                for name,rival in gen.LESSON_COMPETITORS.items():
                    assert any(rival(p["input"])!=p["output"] for p in pairs[:3]), (name,seed,start,band)
                assert gen.lesson_identifiable(pairs[:3],pairs[3])==[]


def test_lesson_gate_catches_query_relevant_missing_corner_ambiguity():
    demos=[]
    for i in range(3):
        g=gen.generate(5,i,anchor_kind="occupied")
        demos.append(dict(input=g,output=gen.rule_mirror(g)))
    q=gen.generate(5,3,anchor_kind="empty")
    reasons=gen.lesson_identifiable(demos,dict(input=q))
    assert any("first_cell_anchor" in r for r in reasons), reasons


def test_canonical_mirror_matches_stored_outputs_and_rule_pin():
    import hashlib
    for line in (REPO/"shared/data/canonical/puzzles.jsonl").open():
        row=json.loads(line)
        if row.get("task_id")==gen.TASK_ID:
            rule=" ".join(row["program_solution"].split())
            assert hashlib.sha256(rule.encode()).hexdigest()[:12]==gen.RULE_HASH
            for pair in row["train"]+[row["test"]]:
                expected=[[int(v) for v in r] for r in pair["output"]]
                assert gen.rule_mirror(pair["input"])==expected
                assert gen.strict_canonical_like(pair["input"])==[]
            return
    pytest.fail("missing canonical task")


def test_negative_fixtures_rejected():
    fixtures=gen.mutation_fixtures()
    assert len(fixtures)>=7
    assert len({name for name,g in fixtures})==len(fixtures)
    for name,g in fixtures:
        assert gen.self_check(g), name


@pytest.mark.parametrize("g", [None,[],[[]],[[0],[0,1]],[[False]],[[10]],[[1.5]],["x"],[[0]*31]])
def test_malformed_inputs_return_reasons_instead_of_crashing(g):
    assert gen.self_check(g)


@pytest.mark.parametrize("ov", [{"grid_h":5},{"grid_w":21},{"n_markers":0},{"motif_size":6},
                               {"anchor_kind":"bogus"},{"n_markers":True},{"grid_h":9.5}])
def test_invalid_overrides_fail_loudly(ov):
    with pytest.raises(ValueError): gen.generate(0,0,**ov)


def test_difficulty_mixture_does_not_duplicate_cross_band_inputs():
    grids=[gen.generate(101,i,difficulty=band)
           for band in ("easy","medium","hard") for i in range(60)]
    assert len({json.dumps(g) for g in grids}) == len(grids)
