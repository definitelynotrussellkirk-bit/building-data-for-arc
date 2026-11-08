"""Reproduce a count-threshold rival using only target generator and canonical data."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT / 'repo'
sys.path.insert(0, str(REPO / 'shared/runtime'))
OUT = Path(__file__).resolve().parent
TARGET = '638cc86f2c0a'
SOURCE = REPO / 'generators' / TARGET / 'generator.py'
spec = importlib.util.spec_from_file_location('selected_audit_generator', SOURCE)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

def boxes(grid):
    pending = {(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v == 5}
    result = []
    while pending:
        start = min(pending)
        pending.remove(start)
        cells = {start}
        todo = [start]
        while todo:
            r,c = todo.pop()
            for q in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if q in pending:
                    pending.remove(q)
                    cells.add(q)
                    todo.append(q)
        top, bottom = min(r for r,c in cells), max(r for r,c in cells)
        left, right = min(c for r,c in cells), max(c for r,c in cells)
        border = {(r,c) for r in range(top,bottom+1) for c in range(left,right+1)
                  if r in (top,bottom) or c in (left,right)}
        if bottom-top >=2 and right-left >=2 and border==cells:
            result.append((top,left,bottom,right))
    return sorted(result)

def groups(grid, box):
    top,left,bottom,right = box
    colors = {}
    for r in range(top+1,bottom):
        for c in range(left+1,right):
            v = grid[r][c]
            if v not in (0,5):
                colors.setdefault(v,[]).append((r,c))
    return colors

def rival(grid):
    """Connect first two row-major markers whenever a color has >=2 markers."""
    out = [row[:] for row in grid]
    for box in boxes(grid):
        for color,cells in groups(grid,box).items():
            if len(cells)>=2:
                (ar,ac),(br,bc) = cells[:2]
                for r in range(ar,br+1):
                    out[r][ac]=color
                for c in range(min(ac,bc),max(ac,bc)+1):
                    out[br][c]=color
    return out

canonical_line = next(line for line in (REPO/'shared/data/canonical/puzzles.jsonl').read_text().splitlines()
                      if json.loads(line).get('task_id')==TARGET)
canonical = json.loads(canonical_line)
canonical_results=[]
for split in ('train','test'):
    for i,pair in enumerate(canonical.get(split,[])):
        canonical_results.append({'split':split,'index':i,'rival_matches':rival(pair['input'])==pair['output'],
                                  'interior_color_counts':[list(map(len,groups(pair['input'],box).values())) for box in boxes(pair['input'])]})

seed='audit-638cc86f2c0a-exactly-two'
scan=[]
for difficulty in ('easy','medium','hard'):
    unique=set()
    chamber_count=0
    self_check_failures=[]
    count_violations=[]
    for index in range(100):
        grid=gen.generate(seed,index,difficulty=difficulty)
        unique.add(hashlib.sha256(json.dumps(grid,separators=(',',':')).encode()).hexdigest())
        errors=gen.self_check(grid,difficulty=difficulty)
        if errors: self_check_failures.append({'index':index,'errors':errors})
        chamber_boxes=boxes(grid)
        chamber_count+=len(chamber_boxes)
        if not chamber_boxes or any(len(groups(grid,box))!=1 or any(len(cells)!=2 for cells in groups(grid,box).values()) for box in chamber_boxes):
            count_violations.append(index)
    scan.append({'difficulty':difficulty,'indices':[0,99],'draws':100,'unique_inputs':len(unique),
                 'chambers':chamber_count,'exactly_two_violations':count_violations,
                 'self_check_failures':self_check_failures})

witness=[[0]*10 for _ in range(9)]
for r in range(1,6):
    for c in range(1,6):
        if r in (1,5) or c in (1,5): witness[r][c]=5
for r,c in ((2,2),(3,3),(4,4)): witness[r][c]=2
(OUT/'input.json').write_text(json.dumps(witness)+'\n')
(OUT/'rival.json').write_text(json.dumps(rival(witness))+'\n')
report={'task_id':TARGET,'generator_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'canonical_record_sha256':hashlib.sha256(canonical_line.encode()).hexdigest(),
        'canonical_rule_utf8_sha256':hashlib.sha256(canonical['program_solution'].encode()).hexdigest(),
        'rival':'For each chamber/color with at least two interior markers, connect the first two in row-major order by a vertical-first elbow; preserve other cells.',
        'canonical_results':canonical_results,'generated_scan':{'seed':seed,'overrides':{},'bands':scan},
        'witness':{'provenance':'manually constructed','seed':None,'sample_index':None,'overrides':{},
                   'input_path':'checks/audit/638cc86f2c0a/input.json',
                   'rival_path':'checks/audit/638cc86f2c0a/rival.json','self_check_errors':gen.self_check(witness),
                   'belongs_to_documented_generator_domain':False,
                   'domain_reason':'One interior color occurs three times; documented generator invariant requires exactly two.'}}
(OUT/'probe.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'generator_sha256':report['generator_sha256'],'canonical_rival_matches':sum(v['rival_matches'] for v in canonical_results),'canonical_pairs':len(canonical_results),'scan':scan,'witness_self_check':report['witness']['self_check_errors']}))
control_seed='audit-638cc86f2c0a-exact-control'
control_overrides={'grid_h':9,'grid_w':10}
control_grid=gen.generate(control_seed,0,difficulty='easy',**control_overrides)
(OUT/'override_input.json').write_text(json.dumps(control_grid)+'\n')
report['exact_control_witness']={'seed':control_seed,'sample_index':0,'difficulty':'easy',
 'overrides':control_overrides,'expected_shape':[9,10],'actual_shape':[len(control_grid),len(control_grid[0])],
 'self_check_errors':gen.self_check(control_grid,difficulty='easy'),
 'belongs_to_documented_generator_domain':True,'input_path':'checks/audit/638cc86f2c0a/override_input.json'}
(OUT/'probe.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report['exact_control_witness']))
