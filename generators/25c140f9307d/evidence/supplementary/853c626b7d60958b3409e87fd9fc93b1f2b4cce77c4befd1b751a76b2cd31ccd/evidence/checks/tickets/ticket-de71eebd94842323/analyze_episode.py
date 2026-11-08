from __future__ import annotations
import hashlib, json
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EPISODE = Path(__file__).with_name('episode.jsonl')
CANONICAL = ROOT / 'WORK/repo/shared/data/canonical/puzzles.jsonl'
TASK = '25c140f9307d'

def frozen(grid):
    return json.dumps(grid, separators=(',', ':'))

def sha(grid):
    return hashlib.sha256(frozen(grid).encode()).hexdigest()

def largest_red_bbox_crop(grid):
    h, w = len(grid), len(grid[0])
    unseen = {(r,c) for r in range(h) for c in range(w) if grid[r][c] == 2}
    comps = []
    while unseen:
        start=min(unseen); unseen.remove(start); q=deque([start]); cells=[]
        while q:
            r,c=q.popleft(); cells.append((r,c))
            for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)):
                p=(r+dr,c+dc)
                if p in unseen:
                    unseen.remove(p); q.append(p)
        comps.append(cells)
    cells=max(comps, key=len)
    r1=min(r for r,_ in cells); r2=max(r for r,_ in cells)
    c1=min(c for _,c in cells); c2=max(c for _,c in cells)
    return [row[c1:c2+1] for row in grid[r1:r2+1]]

def diff_cells(a,b):
    if len(a)!=len(b) or len(a[0])!=len(b[0]):
        return None
    return sum(x!=y for ra,rb in zip(a,b) for x,y in zip(ra,rb))

episode=json.loads(EPISODE.read_text().splitlines()[0])
generated=[]
for split in ('train','test'):
    for index,pair in enumerate(episode[split]):
        rival=largest_red_bbox_crop(pair['input'])
        generated.append({
            'split': split,
            'index': index,
            'input_sha256': sha(pair['input']),
            'authority_output_sha256': sha(pair['output']),
            'shortcut_output_sha256': sha(rival),
            'shortcut_matches': rival == pair['output'],
            'diff_cells': diff_cells(rival, pair['output']),
            'output_shape': [len(pair['output']), len(pair['output'][0])],
        })
canonical_row=None
for line in CANONICAL.read_text().splitlines():
    row=json.loads(line)
    if row.get('task_id')==TASK:
        canonical_row=row; break
assert canonical_row
canonical=[]
for split in ('train','test'):
    for index,pair in enumerate(canonical_row[split]):
        rival=largest_red_bbox_crop(pair['input'])
        canonical.append({
            'split': split,
            'index': index,
            'shortcut_matches': rival == pair['output'],
            'diff_cells': diff_cells(rival, pair['output']),
            'authority_output_sha256': sha(pair['output']),
            'shortcut_output_sha256': sha(rival),
        })
report={
    'schema':'arcpuzzles-bounded-adversarial-witness-v1',
    'ticket_id':'ticket-de71eebd94842323',
    'task_id':TASK,
    'generator_sha256':'524e9f948170fd75c7c84e708165d6ebc2da759753f5b0f77f410d3e4ffbb19b',
    'rule_hash':'fafb0679bd1e',
    'probe_seed':'13396e1413bf4906f8ccea9683252dfc465b1a52620e07ddeb866aac11b56ac5',
    'shortcut':'crop the bounding box of the largest 4-connected red component; do not match or stamp detached keys',
    'generated':generated,
    'canonical':canonical,
    'generated_matches':sum(x['shortcut_matches'] for x in generated),
    'generated_total':len(generated),
    'canonical_matches':sum(x['shortcut_matches'] for x in canonical),
    'canonical_total':len(canonical),
    'finding':(
        'The generated three-pair lesson is exactly fit by a crop-only shortcut, '
        'while the shortcut fails every canonical pair. Detached key payloads are '
        'therefore non-causal in this source-bound lesson.'
    ),
}
out=Path(__file__).with_name('analysis.json')
out.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ('generated_matches','generated_total','canonical_matches','canonical_total','finding')},indent=2))
