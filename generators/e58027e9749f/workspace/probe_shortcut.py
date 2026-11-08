"""Reproduce a source-bound canonical shortcut counterexample using native apply.

From WORK:
  python3 run_with_racket.py python3 generators/e58027e9749f/workspace/probe_shortcut.py prepare
  python3 run_with_racket.py python3 -m arcpuzzles apply e58027e9749f --input ../checks/shortcut/input.json --check-generator-domain --out ../checks/shortcut/racket.json
  python3 run_with_racket.py python3 generators/e58027e9749f/workspace/probe_shortcut.py assess
"""
import hashlib
import json
from pathlib import Path
import sys
from reviewer_support import find_root, load_selected_generator, canonical_pairs

ID='e58027e9749f'
PIN='9ed6edce720cc2eb2adeb44ced6ce129345a1176f1fb43a3fcaa81ebfc9020c6'
ROOT=find_root(__file__)
GEN,SOURCE,HASH=load_selected_generator(ID,root=ROOT)
assert HASH==PIN,(HASH,PIN)
OUT=ROOT.parent/'checks/shortcut'


def write(name,data):
    (OUT/name).write_text(json.dumps(data,indent=1)+'\n')


def prepare():
    OUT.mkdir(parents=True,exist_ok=True)
    overrides=dict(size=5,cell_count=1,n_distinct_colors=1,position_bias='below_diagonal')
    inp=GEN.generate(0,0,**overrides)
    errors=GEN.self_check(inp)
    assert not errors,errors
    observed=GEN.observe_overrides(inp)
    assert all(observed[k]==v for k,v in overrides.items()),observed
    pairs=canonical_pairs(ID,root=ROOT,labeled_only=True)
    fits={name:sum(rival(p['input'])==p['output'] for p in pairs)
          for name,rival in GEN.CANONICAL_SHORTCUTS.items()}
    assert all(n==len(pairs) for n in fits.values()),fits
    write('input.json',{'input':inp})
    write('provenance.json',dict(generator_id=ID,generator_sha256=HASH,seed=0,sample_index=0,difficulty=None,overrides=overrides,observed=observed,
        self_check=errors,canonical_labeled_pairs=len(pairs),canonical_shortcut_matches=fits,
        actual_lesson_competitors=list(GEN.LESSON_COMPETITORS),source=str(SOURCE)))
    write('rival-output.json',dict(name='upper_only',output=GEN.CANONICAL_SHORTCUTS['upper_only'](inp)))
    print(json.dumps({'canonical_pairs':len(pairs),'shortcut_matches':fits,'source_hash':HASH,'observed':observed}))


def assess():
    native=json.loads((OUT/'racket.json').read_text())
    assert native['generator_sha256']==HASH
    assert native['rule_hash_matches_catalog']
    result=native['results'][0]
    assert len(native['results'])==1 and result['error'] is None
    assert result['generator_domain']=={'status':'valid','errors':[]}
    rival=json.loads((OUT/'rival-output.json').read_text())
    assert rival['output']==GEN.CANONICAL_SHORTCUTS['upper_only'](result['input'])
    differences=[dict(row=r,column=c,racket=a,rival=b)
                 for r,(native_row,rival_row) in enumerate(zip(result['output'],rival['output'],strict=True))
                 for c,(a,b) in enumerate(zip(native_row,rival_row,strict=True)) if a!=b]
    assert differences,differences
    write('assessment.json',dict(generator_sha256=HASH,rule_hash=native['executed_rule_hash'],rule_text_sha256=native['rule_text_sha256'],
        input=result['input'],racket_output=result['output'],rival_output=rival['output'],differences=differences,
        finding='upper_only fits all canonical labeled pairs but misses reflection of this valid below-diagonal source; repaired generator supplies the witness.'))
    print(json.dumps({'counterexample':True,'differences':differences,'generator_sha256':HASH}))


if __name__=='__main__':
    {'prepare':prepare,'assess':assess}[sys.argv[1]]()
