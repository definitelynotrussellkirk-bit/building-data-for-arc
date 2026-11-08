"""Authoring-only input/rival probe; no Python authority outputs."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path.cwd() / 'repo'
sys.path.insert(0, str(ROOT / 'shared/runtime'))
from reviewer_support import canonical_pairs
TASK = '2d4e8c8fa10e'
OUT = Path.cwd() / 'checks/audit' / TASK
source = ROOT / 'generators' / TASK / 'generator.py'
spec = importlib.util.spec_from_file_location('audit_generator', source)
gen = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = gen
spec.loader.exec_module(gen)

def rival(grid):
    h, w = len(grid), len(grid[0])
    unseen = {(r,c) for r in range(h) for c in range(w) if grid[r][c] == 6}
    out = [[0]*w for _ in range(h)]
    while unseen:
        first = min(unseen)
        unseen.remove(first)
        cells = [first]
        for r,c in cells:
            for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)):
                pt = r+dr,c+dc
                if pt in unseen:
                    unseen.remove(pt)
                    cells.append(pt)
        if len(cells)==4 and max(r for r,c in cells)-min(r for r,c in cells)==1:
            for r,c in cells:
                out[r][c]=6
    return out

records=[]
for index in range(3):
    grid=gen.generate(123,index,difficulty='easy')
    records.append({'kind':'generated_demo', 'seed':123,'sample_index':index,
                    'difficulty':'easy','overrides':{}, 'input':grid})
base=records[1]['input']
query=[list(row) for row in zip(*base)]
records.append({'kind':'validator_domain_query','construction':'transpose generated demo index1',
                'seed':123,'sample_index':1,'difficulty':'easy','overrides':{},'input':query,
                'production_support':'Absent: generator non-square tetromino templates all have height3; transpose has height2.'})
for pair in canonical_pairs(TASK,root=ROOT):
    records.append({'kind':'canonical','variant':pair['variant'],'split':pair['split'],
                    'pair_index':pair['pair_index'],'input':pair['input'],
                    'canonical_saved_output':pair['output']})
for record in records:
    record['self_check_errors']=gen.self_check(record['input'])
    record['rival_output']=rival(record['input'])
ledger=ROOT/'shared/data/canonical/puzzles.jsonl'
row=next(json.loads(line) for line in ledger.open() if json.loads(line).get('task_id')==TASK)
report={'task_id':TASK,'generator_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'normalized_rule_sha256':hashlib.sha256(' '.join(row['program_solution'].split()).encode()).hexdigest(),
        'rival':'Keep every cardinal magenta component iff size is4 and bounding-box height is2.',
        'command':[sys.executable,*sys.argv],'cwd':str(Path.cwd()),'records':records,
        'label_authority':'Racket outputs obtained separately; no Python mirror authority.'}
(OUT/'input.json').write_text(json.dumps([r['input'] for r in records],indent=2)+'\n')
(OUT/'probe.json').write_text(json.dumps(report,indent=2)+'\n')
print('records',len(records),'self_check errors',[r['self_check_errors'] for r in records])
