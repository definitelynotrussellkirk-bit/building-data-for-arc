#!/usr/bin/env python3
from __future__ import annotations
import hashlib, importlib.util, json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
REPO=ROOT/'repo'
sys.path.insert(0,str(REPO/'shared/runtime'))
from reviewer_support import canonical_pairs


def load(tid):
    path=REPO/'generators'/tid/'generator.py'
    spec=importlib.util.spec_from_file_location(f'audit_{tid}',path)
    mod=importlib.util.module_from_spec(spec); sys.modules[spec.name]=mod; spec.loader.exec_module(mod)
    return mod,path

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def pair(mod,g): return {'input':g,'output':mod.rule_mirror(g)}

out={'schema':'arc-review-audit-probe-v1','targets':{}}

# c2f4...: canonical parity, generated validity, and fixed-position lesson identifiability.
tid='c2f4b540f2fb'; mod,path=load(tid); cp=canonical_pairs(tid,root=REPO)
row={'generator_sha256':sha(path),'canonical_pairs':len(cp)}
row['canonical_failures']=[i for i,p in enumerate(cp) if mod.self_check(p['input']) or mod.rule_mirror(p['input'])!=p['output']]
invalid=[]; lesson_fail=[]; witness_counts={k:0 for k in mod.SEMANTIC_WITNESSES}
for bi,band in enumerate(('easy','medium','hard')):
    for i in range(40):
        g=mod.generate(310000+bi*10000+i,i,difficulty=band)
        errs=mod.self_check(g)
        if errs: invalid.append({'band':band,'index':i,'errors':errs})
        for name,pred in mod.SEMANTIC_WITNESSES.items(): witness_counts[name]+=int(bool(pred(g)))
    for start in range(20):
        seed=330000+bi*10000+start
        grids=[mod.generate(seed,start+j,difficulty=band) for j in range(mod.EXAMPLES_NEEDED+1)]
        reasons=mod.lesson_identifiable([pair(mod,g) for g in grids[:-1]],pair(mod,grids[-1]))
        if reasons: lesson_fail.append({'band':band,'start':start,'reasons':reasons})
row.update({'generated_samples':120,'invalid_generated':invalid,'lessons_checked':60,'lesson_failures':lesson_fail,'witness_counts':witness_counts})
out['targets'][tid]=row

# 33c...: canonical parity plus direct public-axis observability comparison.
tid='33c1de6c4310'; mod,path=load(tid); cp=canonical_pairs(tid,root=REPO)
row={'generator_sha256':sha(path),'canonical_pairs':len(cp)}
row['canonical_failures']=[i for i,p in enumerate(cp) if mod.self_check(p['input']) or mod.rule_mirror(p['input'])!=p['output']]
invalid=[]
for bi,band in enumerate(('easy','medium','hard')):
    for i in range(30):
        g=mod.generate(410000+bi*10000+i,i,difficulty=band)
        errs=mod.self_check(g)
        if errs: invalid.append({'band':band,'index':i,'errors':errs})
row['generated_samples']=90; row['invalid_generated']=invalid
probe=mod.generate(424242,7,difficulty='medium',grid_h=11,panel_w=9,mask_components=3,src_colors=5,texture='wide')
observed=mod.observe_overrides(probe)
row['advertised_axes']=list(mod.AXES)
row['observed_axes']=sorted(observed)
row['missing_observable_axes']=sorted(set(mod.AXES)-set(observed))
row['override_probe']={'requested':{'grid_h':11,'panel_w':9,'mask_components':3,'src_colors':5,'texture':'wide'},'observed':observed,'actual_grid_h':len(probe)}
out['targets'][tid]=row

out['passed_clean_target']=not out['targets']['c2f4b540f2fb']['canonical_failures'] and not out['targets']['c2f4b540f2fb']['invalid_generated'] and not out['targets']['c2f4b540f2fb']['lesson_failures']
Path(__file__).with_name('audit_probe.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))
