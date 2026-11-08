from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path
from reviewer_support import canonical_pairs

TASK='32169a05c213'
ROOT=Path(__file__).resolve().parents[3]
GEN_PATH=ROOT/'repo'/'generators'/TASK/'generator.py'
spec=importlib.util.spec_from_file_location('audit_gen_'+TASK, GEN_PATH)
gen=importlib.util.module_from_spec(spec); spec.loader.exec_module(gen)
pairs=canonical_pairs(TASK, root=ROOT/'repo')

def eq(a,b): return a==b
canonical={name:sum(eq(fn(p['input']),p['output']) for p in pairs) for name,fn in gen.CANONICAL_SHORTCUTS.items()}
counts={name:{'refuted_by_demos':0,'ambiguous':0,'survived_all':0} for name in gen.LESSON_COMPETITORS}
lessons=0
for bi,band in enumerate(('easy','medium','hard')):
  for off in range(100):
    seed=880000+bi*10000+off
    for start in range(4):
      grids=[gen.generate(seed,start+i,difficulty=band) for i in range(gen.EXAMPLES_NEEDED+1)]
      outs=[gen.rule_mirror(g) for g in grids]
      assert all(gen.self_check(g)==[] for g in grids)
      lessons += 1
      for name,fn in gen.LESSON_COMPETITORS.items():
        ro=[fn(g) for g in grids]
        fit=all(eq(ro[i],outs[i]) for i in range(gen.EXAMPLES_NEEDED))
        same=eq(ro[-1],outs[-1])
        key='refuted_by_demos' if not fit else ('survived_all' if same else 'ambiguous')
        counts[name][key]+=1
report={
 'schema':'arcpuzzles-audit-cyclic-probe-v1','task_id':TASK,
 'generator_sha256':hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
 'rule_hash':gen.RULE_HASH,'canonical_pairs':len(pairs),'canonical_fit_counts':canonical,
 'policy':'3 bands x 100 seeds x 4 cyclic starts; four consecutive demonstrations and the following query',
 'lessons':lessons,'competitors':counts,
 'ambiguities':sum(v['ambiguous'] for v in counts.values()),
 'all_declared_rivals_refuted_in_every_lesson':all(v['refuted_by_demos']==lessons for v in counts.values()),
 'limits':'Finite check of the eight declared competitors; no claim against undeclared rivals.'
}
Path(__file__).with_name('cyclic_report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'lessons':lessons,'ambiguities':report['ambiguities'],'all_refuted':report['all_declared_rivals_refuted_in_every_lesson']},indent=2))
