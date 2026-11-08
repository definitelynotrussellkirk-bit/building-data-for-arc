"""Focused tests; run explicitly through `arcpuzzles check --stage task_tests`."""
import hashlib
import importlib.util
from pathlib import Path
import pytest

# Source tree: ../workspace; copied runtime: puzzle_generators/per_puzzle/TASK/workspace.
HERE = Path(__file__).resolve()
p = HERE.parents[1] / 'workspace' / 'review_probe.py'
if not p.exists():
    import importlib
    gm = importlib.import_module('puzzle_generators.per_puzzle.312fb4bdff00.generator')
    p = Path(gm.__file__).parent / 'workspace' / 'review_probe.py'
spec = importlib.util.spec_from_file_location('review_probe',p)
probe = importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
gen = probe.load_generator()


def test_rule_pin():
    assert getattr(gen,'RULE_HASH',None) == 'cc8c5c7301a4'


def test_unknown_axis_rejected():
    with pytest.raises(ValueError):
        gen.generate(3,4,unknown_axis=1)


@pytest.mark.parametrize('band',['easy','medium','hard'])
def test_exact_override_across_bands(band):
    g = gen.generate(17,2,difficulty=band,panel_s=3,n_cands=4,shape_k=8,
                     match_count=0,target_color=8)
    assert len(g)==4 and len(g[0])==19
    assert len(probe.support(probe.panels(g)[0]))==8
    assert len(probe.matches(g))==0
    assert next(x for x in g[0] if x)==8


def test_oversized_joint_override_rejected_not_clipped():
    with pytest.raises(ValueError):
        gen.generate(1,0,difficulty='hard',panel_s=6,n_cands=4)


def test_no_match_emitted_in_ordinary_distribution():
    assert any(not probe.matches(gen.generate(9,i)) for i in range(16))


def test_multiple_matches_emitted_in_ordinary_distribution():
    assert any(len(probe.matches(gen.generate(9,i)))>=2 for i in range(16))


@pytest.mark.parametrize('band',['easy','medium','hard'])
def test_six_pair_default_lessons_keep_two_no_match_examples(band):
    """Holding out one absence must leave another sentinel demonstration."""
    for seed in range(16):
        for start in range(3):
            grids = [gen.generate(seed,start+offset,difficulty=band) for offset in range(6)]
            match_counts = [len(probe.matches(grid)) for grid in grids]
            assert match_counts.count(0) >= 2, {
                'band':band,'seed':seed,'start':start,'match_counts':match_counts,
            }


def test_translation_witness_emitted():
    assert any(probe.oracle(g) != probe.copy_query(g) and probe.matches(g)
               for g in (gen.generate(1,i) for i in range(16)))


def test_canonical_inputs_accepted_and_independent_oracle_correct():
    for pair in probe.canonical_pairs():
        assert gen.self_check(pair['input']) == []
        assert probe.oracle(pair['input']) == pair['output']
        assert probe.copy_query(pair['input']) == pair['output']


@pytest.mark.parametrize('bad',[
    [],[[]],[[1,0],[0]],[[1,0],[8,8]],[[1]+[0]*8]+[[2]*9 for _ in range(4)],
    [[1]+[0]*8]+[[0]*4+[8]+[0]*4 for _ in range(4)],
])
def test_validator_rejects_malformed_panels(bad):
    assert gen.self_check(bad)


@pytest.mark.parametrize('band',['easy','medium','hard'])
def test_entire_legal_joint_integer_domain(band):
    sample = 0
    for side in range(3,7):
        for n in range(1,5):
            if (n+1)*(side+1)-1 > 30:
                continue
            for k in range(2,9):
                for count in range(n+1):
                    requested = dict(panel_s=side,n_cands=n,shape_k=k,
                                     match_count=count,target_color=1+sample%9)
                    g = gen.generate(971,sample,difficulty=band,**requested)
                    assert not gen.self_check(g),requested
                    assert gen.observe_overrides(g)==requested
                    assert len(probe.matches(g))==count
                    assert len(probe.support(probe.panels(g)[0]))==k
                    sample += 1
    assert sample == 357


@pytest.mark.parametrize('axis,value',[
    ('panel_s',True),('panel_s',3.5),('panel_s','4'),('panel_s',7),
    ('match_count',-1),('target_color',0),('n_cands',5),('shape_k',9),
])
def test_invalid_exact_controls_rejected(axis,value):
    with pytest.raises(ValueError):
        gen.generate(1,2,**{axis:value})


@pytest.mark.parametrize('band',['easy','medium','hard'])
def test_five_example_default_lessons_refute_every_declared_rival_at_all_rotations(band):
    instances = []
    for seed in range(12):
        for start in range(3):
            pairs = []
            for offset in range(6):
                g = gen.generate(seed,start+offset,difficulty=band)
                assert not gen.self_check(g)
                pairs.append({'input':g,'output':probe.oracle(g)})
            instances.append({'train':pairs[:5],'test':pairs[5:]})
    report = probe.cyclic_rivals(gen,instances)
    assert not report['ambiguities'],report['ambiguities'][:1]
    assert all(row['windows']==216 for row in report['counts'].values())
    assert all(row['ambiguous']==0 for row in report['counts'].values())


def test_canonical_shortcut_declarations_are_truthful():
    for name,rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(p['input'])==p['output'] for p in probe.canonical_pairs()),name


@pytest.mark.parametrize('band',['easy','medium','hard'])
def test_pinned_profile_has_support(band):
    canonical = {(len(p['input']),len(p['input'][0]),len({x for row in p['input'] for x in row}))
                 for p in probe.canonical_pairs()}
    hits = 0
    for i in range(20):
        seed = int(hashlib.sha256(f'profile-floor:v1:312fb4bdff00:{band}:{i}'.encode()).hexdigest()[:12],16)
        g = gen.generate(seed,seed%7919+i,difficulty=band)
        hits += (len(g),len(g[0]),len({x for row in g for x in row})) in canonical
    assert hits >= 1


def test_default_curriculum_keeps_translated_unique_and_varied_multiple_placements():
    seen=set()
    for seed in range(12):
        for index in range(12):
            g=gen.generate(seed,index)
            count=len(probe.matches(g))
            if count:
                seen.add((count,probe.oracle(g)==probe.copy_query(g)))
    assert {(1,False),(2,False),(2,True)} <= seen


def test_exact_override_can_request_aligned_single_match():
    g=gen.generate(0,1,panel_s=4,n_cands=3,shape_k=4,
                   match_count=1,target_color=7)
    assert gen.observe_overrides(g)['match_count'] == 1
    assert probe.oracle(g) == probe.copy_query(g)
