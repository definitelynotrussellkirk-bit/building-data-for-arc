import hashlib, importlib.util, json
from collections import Counter
from pathlib import Path
p=Path('generators/38200022d1b7/generator.py')
s=importlib.util.spec_from_file_location('peer382',p); g=importlib.util.module_from_spec(s); s.loader.exec_module(g)
out=Path('../checks/38200022d1b7')
def rival(x):
    counts=Counter(v for row in x for v in row if v not in (0,5))
    pr,pc=next((r,c) for r,row in enumerate(x) for c,v in enumerate(row) if v==5)
    y=[row[:] for row in x]
    for r,row in enumerate(x):
        for c,v in enumerate(row):
            if v not in (0,5) and counts[v]>1: y[2*pr-r][2*pc-c]=v
    return y
examined=0
for seed in range(3820,3860):
    xs=[g.generate(seed,i,difficulty='medium') for i in range(5)]
    pairs=[dict(input=x,output=g.rule_mirror(x)) for x in xs]
    for qi in range(5):
        examined+=1
        demos=[p for i,p in enumerate(pairs) if i!=qi]
        if all(rival(p['input'])==p['output'] for p in demos) and rival(xs[qi])!=pairs[qi]['output']:
            report={'schema':'arc-bounded-peer-ambiguity-v1','task_id':g.TASK_ID,'generator_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'rule_hash':g.RULE_HASH,'seed':seed,'difficulty':'medium','sample_indices':list(range(5)),'query_index':qi,'rival':'copy only source colors whose total input frequency is greater than one; retain all original cells','candidate_rotations_examined':examined,'self_checks':[g.self_check(x) for x in xs],'lesson_identifiable':g.lesson_identifiable(demos,pairs[qi]),'pairs':pairs,'rival_predictions':[rival(x) for x in xs]}
            (out/'candidate.json').write_text(json.dumps(report,indent=2)+'\n')
            (out/'inputs.json').write_text(json.dumps({'inputs':xs})+'\n')
            print(json.dumps({k:v for k,v in report.items() if k not in ('pairs','rival_predictions')}))
            raise SystemExit(0)
raise SystemExit('no counterexample in bounded search')
