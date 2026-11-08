"""Bounded findings-only probe; labels come only from public Racket apply."""
import copy,hashlib,importlib.util,json,sys
from pathlib import Path

ROOT=Path.cwd(); TASK='923465deb4e4'; OUT=ROOT.parent/'checks/audit'/TASK
path=ROOT/'generators'/TASK/'generator.py'
spec=importlib.util.spec_from_file_location('audit_corner_key',path)
gen=importlib.util.module_from_spec(spec);spec.loader.exec_module(gen)

def digest(g):return hashlib.sha256(json.dumps(g,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def counts(g):
    key=g[0][0]; colors={v for row in g for v in row}-{0,key}
    return {'key':key,'distractor_colors':sorted(colors),'n_distractor_colors':len(colors)}

cases=[]
for band in ('easy','medium','hard'):
    for seed in (0,17,101):
        for n in (0,1,3):
            g=gen.generate(seed,0,difficulty=band,n_distractors=n)
            snap=copy.deepcopy(g); errors=gen.self_check(g,difficulty=band)
            cases.append({'seed':seed,'sample_index':0,'difficulty':band,'overrides':{'n_distractors':n},'input':g,'input_sha256':digest(g),'observed':counts(g),'validation':errors,'self_check_mutated':g!=snap})
first=cases[0]
rule=next(json.loads(line)['program_solution'] for line in (ROOT/'shared/data/canonical/puzzles.jsonl').read_text().splitlines() if json.loads(line).get('task_id')==TASK)
receipt={'schema':'findings-only-audit-probe-v1','task_id':TASK,'generator_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'canonical_rule_exact_sha256':hashlib.sha256(rule.encode()).hexdigest(),'probe_argv':sys.argv,'payload_cwd':str(ROOT),'cases':cases,'same_inputs_across_n_distractors':all(cases[i]['input']==cases[i+1]['input']==cases[i+2]['input'] for i in range(0,len(cases),3)),'scope':'27 generation/control draws; this probe does not infer Racket labels.'}
(OUT/'probe_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
(OUT/'input.json').write_text(json.dumps({'input':first['input']},indent=2)+'\n')
print(json.dumps({'generator_sha256':receipt['generator_sha256'],'case_count':len(cases),'same_inputs_across_overrides':receipt['same_inputs_across_n_distractors'],'actual_distractor_counts':sorted({c['observed']['n_distractor_colors'] for c in cases}),'all_selfchecks_valid':all(not c['validation'] for c in cases),'first':{k:first[k] for k in ('seed','sample_index','difficulty','overrides','observed','input_sha256')}}))
