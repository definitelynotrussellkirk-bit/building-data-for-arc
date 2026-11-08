"""Focused findings-only reproduction; no generator edits."""
from collections import deque
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2] / 'repo'
sys.path.insert(0, str(ROOT / 'shared/runtime'))
SOURCE = ROOT / 'generators/ad9405621c3d/generator.py'
spec = importlib.util.spec_from_file_location('audited_gen', SOURCE)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))

def solve(grid, *, rival=False):
    h, w = len(grid), len(grid[0])
    color = next(v for row in grid for v in row if v not in (0, 5))
    start, goal = [(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v == color]
    interior = all(min(r, h-1-r, c, w-1-c) >= 2 for r,c in (start, goal))
    distance = lambda p: abs(p[0]-goal[0]) + abs(p[1]-goal[1])
    parent = {start: None}
    queue = deque([start])
    while queue:
        cur = queue.popleft()
        if cur == goal:
            break
        for dr,dc in DIRS:
            nxt = cur[0]+dr,cur[1]+dc
            r,c = nxt
            if not (0 <= r < h and 0 <= c < w) or nxt in parent:
                continue
            if nxt != goal and grid[r][c] != 0:
                continue
            if rival and interior and distance(nxt) >= distance(cur):
                continue
            parent[nxt] = cur
            queue.append(nxt)
    out = deepcopy(grid)
    if goal not in parent:
        return out
    cur = goal
    while cur is not None:
        out[cur[0]][cur[1]] = color
        cur = parent[cur]
    return out

def dump(name, obj):
    (HERE / name).write_text(json.dumps(obj, indent=2) + '\n')

canonical = next(json.loads(line) for line in (ROOT/'shared/data/canonical/puzzles.jsonl').read_text().splitlines() if json.loads(line)['task_id'] == 'ad9405621c3d')
pairs = canonical['train'] + canonical['test']
dump('canonical-fit.json', {'count': len(pairs), 'rival_passed': sum(solve(p['input'], rival=True) == p['output'] for p in pairs), 'independent_passed': sum(solve(p['input']) == p['output'] for p in pairs)})

records = []
lessons = []
for band in ('easy','medium','hard'):
    for h in range(6,10):
        for w in range(7,10):
            seed = 100000 + h * 100 + w
            overrides = {'grid_h': h, 'grid_w': w, 'endpoint_color': 2}
            demos = []
            for index in range(4):
                grid = gen.generate(seed,index,difficulty=band,**overrides)
                expected = solve(grid)
                rival = solve(grid,rival=True)
                records.append({'seed':seed,'sample_index':index,'difficulty':band,'overrides':overrides,'profile':gen.schedule_profile(seed,index,band),'input':grid,'independent_output':expected,'generator_output':gen.expected_output(grid),'rival_output':rival,'self_check':gen.self_check(grid),'strict_canonical_like':gen.strict_canonical_like(grid),'rival_agrees':rival == expected})
                demos.append({'input':grid,'output':expected})
            query_input = gen.generate(seed,4,difficulty=band,**overrides)
            lessons.append({'seed':seed,'difficulty':band,'overrides':overrides,'indices':[0,1,2,3],'declared_lesson_identifiable_reasons':gen.lesson_identifiable(demos, {'input':query_input,'output':solve(query_input)}),'undeclared_rival_survives':all(solve(d['input'],rival=True)==d['output'] for d in demos)})
dump('generated-cases.json',records)
dump('lessons.json',lessons)

# An interior U route requires an initial move away from the same-row goal.
grid = [[5]*9 for _ in range(9)]
for r in range(2,5):
    grid[r][2] = grid[r][6] = 0
for c in range(2,7):
    grid[4][c] = 0
grid[2][2] = grid[2][6] = 2
dump('input.json',grid)
dump('rival.json',solve(grid,rival=True))
dump('independent.json',solve(grid))
dump('summary.json', {'task_id':gen.TASK_ID,'generator_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'rule_hash':gen.RULE_HASH,'canonical_rule_sha256':hashlib.sha256(canonical['program_solution'].encode()).hexdigest(),'canonical_row_sha256':hashlib.sha256(json.dumps(canonical,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'probe_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'generated_count':len(records),'rival_generated_agreements':sum(r['rival_agrees'] for r in records),'independent_generator_agreements':sum(r['independent_output']==r['generator_output'] for r in records),'generated_valid':sum(r['self_check']==[] and r['strict_canonical_like']==[] for r in records),'lesson_count':len(lessons),'rival_surviving_lessons':sum(l['undeclared_rival_survives'] for l in lessons),'declared_identifiable_lessons':sum(l['declared_lesson_identifiable_reasons']==[] for l in lessons),'witness_provenance':{'kind':'hand_constructed','seed':None,'sample_index':None,'overrides':None},'witness_self_check':gen.self_check(grid),'witness_strict_canonical_like':gen.strict_canonical_like(grid),'witness_domain_claim':'9x9, one endpoint color 2 appearing twice at depth 2, background 0, walls 5, endpoints connected; accepted by both current validators. Outside sampler support: interior route exceeds Manhattan distance.','witness_rival_disagrees':solve(grid)!=solve(grid,rival=True)})
print(json.dumps(json.loads((HERE/'summary.json').read_text()),indent=2))
