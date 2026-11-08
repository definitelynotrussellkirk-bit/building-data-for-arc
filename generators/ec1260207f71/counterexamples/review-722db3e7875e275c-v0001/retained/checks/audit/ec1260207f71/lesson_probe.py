from __future__ import annotations
import hashlib, importlib.util, json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
GEN_PATH=ROOT/'repo/generators/ec1260207f71/generator.py'
spec=importlib.util.spec_from_file_location('audit_ec_probe',GEN_PATH); assert spec and spec.loader
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

def freeze(g): return tuple(tuple(r) for r in g)

def solve(g): return mod.rule_mirror(g)
def unchanged(g): return [r[:] for r in g]
def branch_rival(axis, value, g):
    return solve(g) if mod.observe_overrides(g)[axis] == value else unchanged(g)

rivals={
 'upper_only':lambda g:branch_rival('dot_band','upper',g),
 'lower_only':lambda g:branch_rival('dot_band','lower',g),
 'left_only':lambda g:branch_rival('dot_side','left',g),
 'right_only':lambda g:branch_rival('dot_side','right',g),
}
per_band=100
report={'schema':'arcpuzzles-audit-lesson-probe-v1','task_id':mod.TASK_ID,'generator_sha256':hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),'declared_rule_hash':mod.RULE_HASH,'lesson_policy':'seed=720000+band_offset+k, start=k*11, four consecutive demonstrations and one query','per_band':per_band,'bands':{}}
for bi,band in enumerate(('easy','medium','hard')):
    counts=Counter(); examples={}; unique=set(); valid=0
    for k in range(per_band):
        seed=720000+bi*10000+k; start=k*11
        grids=[mod.generate(seed,start+i,difficulty=band) for i in range(5)]
        assert all(mod.self_check(g)==[] for g in grids)
        unique.update(freeze(g) for g in grids); valid+=5
        outputs=[solve(g) for g in grids]
        for name,fn in rivals.items():
            fit=all(fn(g)==out for g,out in zip(grids[:4],outputs[:4]))
            fail=fn(grids[4])!=outputs[4]
            if fit:
                counts[name+'_fits_demos']+=1
            if fit and fail:
                counts[name+'_fits_demos_fails_query']+=1
                examples.setdefault(name,{'seed':seed,'sample_index':start,'observed':[mod.observe_overrides(g) for g in grids]})
    report['bands'][band]={'lessons':per_band,'materialized_pairs':valid,'unique_inputs':len(unique),'counts':dict(counts),'first_examples':examples}
(here:=Path(__file__).resolve().parent/'lesson_probe.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({b:v['counts'] for b,v in report['bands'].items()},indent=2))
