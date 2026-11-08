"""Source-bound authoring probe: intersection-corner support restriction."""
from __future__ import annotations
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

ID = '5998c17d89a0'
HERE = Path(__file__).resolve().parent

def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + '\n')

def components(grid):
    h, w = len(grid), len(grid[0])
    seen = {(0, 0)}
    groups = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] == 0:
                continue
            color = grid[r][c]
            todo = [(r, c)]
            seen.add((r, c))
            cells = set()
            while todo:
                rr, cc = todo.pop()
                cells.add((rr, cc))
                for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
                    p = (rr+dr, cc+dc)
                    if 0 <= p[0] < h and 0 <= p[1] < w and p not in seen and grid[p[0]][p[1]] == color:
                        todo.append(p)
                        seen.add(p)
            minr = min(x[0] for x in cells)
            minc = min(x[1] for x in cells)
            mask = {(rr-minr,cc-minc) for rr,cc in cells}
            groups.append({'color':color, 'origin':(minr,minc), 'cells':cells, 'mask':mask,
                           'bbox_hw':(max(rr for rr,cc in mask)+1,max(cc for rr,cc in mask)+1)})
    return sorted(groups, key=lambda x: (x['origin'][1],x['origin'][0]))

def crop(cells):
    if not cells:
        return [[0]]
    r0,r1 = min(r for r,c in cells),max(r for r,c in cells)
    c0,c1 = min(c for r,c in cells),max(c for r,c in cells)
    return [[8 if (r,c) in cells else 0 for c in range(c0,c1+1)] for r in range(r0,r1+1)]

def mirrors(grid):
    a,b = [x['mask'] for x in components(grid)]
    key = grid[0][0]
    expected = crop(a|b if key==1 else a&b if key==2 else a^b if key==3 else a-b)
    rival = [row[:] for row in expected]
    if key == 2:
        rival[0][0] = 8
    return expected, rival

def attributes(grid):
    comps = components(grid)
    return {'input_hw':[len(grid),len(grid[0])], 'key':grid[0][0],
            'component_areas':[len(x['mask']) for x in comps],
            'component_bbox_hw':[list(x['bbox_hw']) for x in comps],
            'component_normalized_corner_filled':[(0,0) in x['mask'] for x in comps]}

def prepare():
    root = find_root(__file__)
    generator, source, source_sha = load_selected_generator(ID,root=root)
    records = []
    for line in canonical_path(root).read_text().splitlines():
        row = json.loads(line)
        if row.get('task_id') == ID:
            records.append({'raw_line_sha256':hashlib.sha256(line.encode()).hexdigest(), 'record':row})
    assert len(records) == 1
    canonical = canonical_pairs(ID,root=root,labeled_only=True)
    cases = []
    for pair in canonical:
        cases.append({'kind':'canonical', **pair})
    for band in ('easy','medium','hard'):
        for index in range(16):
            grid = generator.generate(0,index,difficulty=band)
            cases.append({'kind':'generated','seed':0,'sample_index':index,'difficulty':band,
                          'overrides':{},'input':grid})
    grid = [[0]*11 for _ in range(8)]
    grid[0][0] = 2
    a = {(0,1),(1,0),(1,1),(1,2),(2,1)}
    b = {(0,1),(1,0),(1,1),(1,2),(2,2)}
    for color,mask,(r0,c0) in ((3,a,(1,1)),(6,b,(4,7))):
        for r,c in mask:
            grid[r0+r][c0+c] = color
    cases.append({'kind':'counterexample','origin':'hand-authored equal-area 3x3 masks',
                  'difficulty':'easy','seed':None,'sample_index':None,'overrides':None,'input':grid})
    for i,case in enumerate(cases):
        case['apply_index'] = i
        case['self_check'] = generator.self_check(case['input'],difficulty=case.get('difficulty'))
        case['attributes'] = attributes(case['input'])
        expected,rival = mirrors(case['input'])
        case['python_mirror_output'] = expected
        case['rival_output'] = rival
    write('input.json',[x['input'] for x in cases])
    write('prepared.json',{
        'task_id':ID,'generator_sha256':source_sha,'generator_version':generator.VERSION,
        'generator_path':str(source.relative_to(root)),
        'canonical_ledger_path':str(canonical_path(root).relative_to(root)),
        'canonical_program_sha256':hashlib.sha256(records[0]['record']['program_solution'].encode()).hexdigest(),
        'canonical_record':records[0],
        'rival':'Boolean set rule except force output[0][0]=8 when key=2 (intersection).',
        'review_index_present':(root/f'generators/{ID}/evidence/review_index.json').exists(),
        'associated_notes_bytes':(root/f'generators/{ID}/evidence/associated_notes.jsonl').stat().st_size,
        'cases':cases})
    counts = Counter(x['kind'] for x in cases)
    print(json.dumps({'task_id':ID,'generator_sha256':source_sha,'prepared':dict(counts),
                      'self_check_failures':sum(bool(x['self_check']) for x in cases),
                      'rival_vs_canonical_labels':sum(x['rival_output']==x['output'] for x in cases if x['kind']=='canonical'),
                      'canonical_denominator':len(canonical)}))

if __name__ == '__main__':
    prepare()
