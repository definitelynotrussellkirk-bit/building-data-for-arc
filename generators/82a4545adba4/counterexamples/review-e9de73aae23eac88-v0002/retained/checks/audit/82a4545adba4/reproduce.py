"""Read-only bounded audit; independent ray model and exact-control probes."""
import argparse,hashlib,importlib.util,json,sys
from pathlib import Path

def digest(x):
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def predict(grid):
    h,w=len(grid),len(grid[0]);out=[[0]*w for _ in range(h)]
    for c,color in enumerate(grid[0]):
        if color:
            for r in range(min(h,w-c)):
                out[r][c+r]=color
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True,type=Path);ap.add_argument('--out',required=True,type=Path);args=ap.parse_args()
    repo=args.repo.resolve();sys.path.insert(0,str(repo/'shared/runtime'))
    path=repo/'generators/82a4545adba4/generator.py'
    spec=importlib.util.spec_from_file_location('audited',path);gen=importlib.util.module_from_spec(spec);spec.loader.exec_module(gen)
    ledger=repo/'shared/data/canonical/puzzles.jsonl'
    row=next(json.loads(line) for line in ledger.read_text().splitlines() if json.loads(line).get('task_id')=='82a4545adba4')
    pairs=list(row['train'])+[row['test']]
    checks=[]
    for values in ({'grid_h':4.9},{'grid_w':7.9},{'n_markers':2.9},{'grid_h':'6'}):
        grid=gen.generate(0,0,difficulty='medium',**values)
        observed={'grid_h':len(grid),'grid_w':len(grid[0]),'n_markers':sum(v!=0 for v in grid[0])}
        checks.append({'call':{'seed':0,'sample_index':0,'difficulty':'medium','overrides':values},'observed':{k:observed[k] for k in values},'self_check':gen.self_check(grid),'input':grid,'input_sha256':digest(grid)})
    bad=[];mirror_mismatch=[];signatures=set()
    for band in ('easy','medium','hard'):
        for seed in range(100):
            index=seed*13+5;grid=gen.generate(seed,index,difficulty=band);errors=gen.self_check(grid)
            if errors:bad.append({'seed':seed,'index':index,'band':band,'errors':errors,'input':grid})
            if predict(grid)!=gen.rule_mirror(grid):mirror_mismatch.append({'seed':seed,'index':index,'band':band})
            signatures.add(digest(grid))
    out={'schema':'read-only-random-audit/1','task_id':'82a4545adba4','source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'version':gen.VERSION,'rule_hash':gen.RULE_HASH,'canonical_ledger_sha256':hashlib.sha256(ledger.read_bytes()).hexdigest(),'canonical_independent_model_pass':sum(predict(p['input'])==p['output'] for p in pairs),'canonical_pairs':len(pairs),'default_draws':300,'unique_inputs':len(signatures),'default_self_check_failures':bad,'python_mirror_mismatches':mirror_mismatch,'coerced_override_cases':checks,'label_scope':'Canonical saved labels and independent Python diagnostics; no new Racket labels in this probe.','prior_audit_lead':'review-ca62fa1453076264:v0001; lower-row distractor is explicitly off-domain, not reclassified as a generated defect.'}
    args.out.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in('source_sha256','canonical_independent_model_pass','canonical_pairs','default_draws','unique_inputs','default_self_check_failures','python_mirror_mismatches')}));print('coerced_override_cases',len(checks))
if __name__=='__main__':main()
