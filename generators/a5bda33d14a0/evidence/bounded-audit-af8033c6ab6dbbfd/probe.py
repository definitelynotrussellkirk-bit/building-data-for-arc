"""Focused source-bound independent audit. Run prepare, native apply, assess."""
import hashlib
import json
from pathlib import Path
import sys
from reviewer_support import find_root, load_selected_generator, canonical_pairs

ID='a5bda33d14a0'
PIN='8095c7fca8bafafd63c796287fe7bba7ca1a85ea39b51542b868d913630192f5'
HERE=Path(__file__).resolve().parent
ROOT=find_root(__file__)
GEN,SOURCE,HASH=load_selected_generator(ID,root=ROOT)
assert HASH==PIN,(HASH,PIN)


def save(name,value):
    (HERE/name).write_text(json.dumps(value,indent=1)+'\n')


def truth(grid):
    out=[row[:] for row in grid]
    points=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v]
    top=min(r for r,c in points); bottom=max(r for r,c in points)
    left=min(c for r,c in points); right=max(c for r,c in points)
    for r in range(top,bottom+1):
        for c in range(left,right+1):
            if (r in (top,bottom) or c in (left,right)) and out[r][c]==0:
                out[r][c]=8
    return out


def prepare():
    records=[]
    for band in ('easy','medium','hard'):
        for seed in range(4):
            for index in range(4):
                records.append(dict(kind='default',seed=seed,sample_index=index,difficulty=band,overrides={}))
    for h,w in ((4,4),(4,18),(18,4),(18,18)):
        for count in (3,12):
            for colors in (2,min(9,count+1)):
                k=len(records)-48
                records.append(dict(kind='exact-boundary',seed=100+k,sample_index=k%4,
                    difficulty=('easy','medium','hard')[k%3],overrides=dict(grid_h=h,grid_w=w,n_cells=count,n_distinct_colors=colors)))
    inputs=[]
    for record in records:
        grid=GEN.generate(record['seed'],record['sample_index'],difficulty=record['difficulty'],**record['overrides'])
        assert not GEN.self_check(grid),(record,GEN.self_check(grid))
        observed=GEN.observe_overrides(grid)
        assert all(observed[k]==v for k,v in record['overrides'].items()),(record,observed)
        assert GEN.generate(record['seed'],record['sample_index'],difficulty=record['difficulty'],**record['overrides'])==grid
        record['observed']=observed
        inputs.append(grid)
    rejects=[]
    for kwargs in ({'seed':True},{'sample_index':-1},{'sample_index':True},{'difficulty':0.25},
                   {'grid_h':True},{'grid_w':19},{'n_cells':3,'n_distinct_colors':9},{'unknown_axis':1}):
        args=dict(seed=0,sample_index=0);args.update(kwargs)
        try:GEN.generate(**args)
        except (TypeError,ValueError) as exc:rejects.append(dict(request=kwargs,exception=type(exc).__name__,message=str(exc),incompatible_axes=getattr(exc,'incompatible_axes',None)))
        else:raise AssertionError(('unexpected acceptance',kwargs))
    pairs=canonical_pairs(ID,root=ROOT,labeled_only=True)
    canonical={name:sum(rival(p['input'])==p['output'] for p in pairs) for name,rival in GEN.CANONICAL_SHORTCUTS.items()}
    assert all(v==len(pairs) for v in canonical.values()),canonical
    assert all(truth(p['input'])==p['output'] for p in pairs)
    save('inputs.json',{'inputs':inputs})
    save('cases.json',{'generator_sha256':HASH,'records':records,'invalid_requests':rejects,'canonical_pairs':len(pairs),'canonical_shortcut_matches':canonical})
    print(json.dumps({'prepared':len(inputs),'invalid_requests_rejected':len(rejects),'canonical_pairs':len(pairs),'generator_sha256':HASH}))


def assess():
    cases=json.loads((HERE/'cases.json').read_text())
    native=json.loads((HERE/'racket.json').read_text())
    assert native['generator_sha256']==HASH
    assert native['rule_hash_matches_catalog']
    results=native['results']; assert len(results)==64
    rivals=GEN.LESSON_COMPETITORS
    matches={name:0 for name in rivals}
    for result in results:
        assert result['error'] is None,result
        assert result['valid_output'] is True,result
        assert result['generator_domain']=={'status':'valid','errors':[]},result
        assert result['output']==truth(result['input'])
        assert not GEN.self_check(result['input'])
        for name,rival in rivals.items():matches[name]+=rival(result['input'])==result['output']
    production=[];rotations=[]
    for start in range(0,48,4):
        rows=results[start:start+4]
        for query in range(4):
            ambiguous=[]
            for name,rival in rivals.items():
                fits=all(rival(row['input'])==row['output'] for j,row in enumerate(rows) if j!=query)
                if fits and rival(rows[query]['input'])!=rows[query]['output']:ambiguous.append(name)
            record=dict(case_indices=list(range(start,start+4)),query_case_index=start+query,ambiguous_rivals=ambiguous)
            rotations.append(record)
            if query==3:production.append(record)
    assert not any(r['ambiguous_rivals'] for r in rotations),rotations
    save('assessment.json',dict(generator_sha256=HASH,rule_text_sha256=native['rule_text_sha256'],rule_hash=native['executed_rule_hash'],native_inputs=64,
        unique_inputs=len({json.dumps(r['input']) for r in results}),native_python_disagreements=0,
        default_draws=48,boundary_draws=16,exact_override_mismatches=0,self_check_failures=0,
        invalid_requests_rejected=len(cases['invalid_requests']),canonical_pairs=cases['canonical_pairs'],canonical_shortcut_matches=cases['canonical_shortcut_matches'],
        rival_matches_on_64=matches,demonstrations=3,query_policy='three ordered consecutive demonstrations; fourth consecutive pair query; all four one-query rotations also checked',
        production_lessons=12,production_ambiguous=0,query_rotations=48,rotations_ambiguous=0,rotation_evidence=rotations,
        conclusion='No issue found within these bounded checks.'))
    print(json.dumps({'native_inputs':64,'production_lessons':12,'query_rotations':48,'ambiguities':0,'rival_matches':matches}))


if __name__=='__main__':
    {'prepare':prepare,'assess':assess}[sys.argv[1]]()
