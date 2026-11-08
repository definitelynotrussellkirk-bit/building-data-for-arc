"""Findings-only bounded audit; imports selected source with public helper."""
from collections import Counter
import hashlib,json
from pathlib import Path
from reviewer_support import canonical_pairs,canonical_path,find_root,load_selected_generator

OUT=Path(__file__).resolve().parent
ROOT=find_root(__file__)
TASK='b6fb46980e63'
module,source,source_hash=load_selected_generator(TASK,root=ROOT)
canonical=[]
for line in canonical_path(ROOT).read_text().splitlines():
    row=json.loads(line)
    if row.get('task_id')==TASK:
        canonical.append(row)
assert len(canonical)==1
row=canonical[0]
program=row['program_solution']
if isinstance(program,dict):
    raise TypeError('expected string program_solution')
rulehash=hashlib.sha256(program.encode()).hexdigest()


def components(grid):
    seen,result=set(),[]
    for r in range(1,len(grid)):
        for c in range(len(grid[0])):
            if grid[r][c]==0 or (r,c) in seen: continue
            seen.add((r,c));stack=[(r,c)];cells=[]
            while stack:
                rr,cc=stack.pop();cells.append((rr,cc))
                for dr,dc in ((-1,0),(1,0),(0,-1),(0,1)):
                    nr,nc=rr+dr,cc+dc
                    if 1<=nr<len(grid) and 0<=nc<len(grid[0]) and grid[nr][nc]!=0 and (nr,nc) not in seen:
                        seen.add((nr,nc));stack.append((nr,nc))
            result.append(cells)
    return result


def holes(cells):
    top,bottom=min(r for r,c in cells),max(r for r,c in cells)
    left,right=min(c for r,c in cells),max(c for r,c in cells)
    occupied=set(cells);visited=set();count=0
    for r in range(top,bottom+1):
        for c in range(left,right+1):
            if (r,c) in occupied or (r,c) in visited: continue
            visited.add((r,c));stack=[(r,c)];edge=False
            while stack:
                rr,cc=stack.pop()
                edge |= rr in (top,bottom) or cc in (left,right)
                for dr,dc in ((-1,0),(1,0),(0,-1),(0,1)):
                    nr,nc=rr+dr,cc+dc
                    if top<=nr<=bottom and left<=nc<=right and (nr,nc) not in occupied and (nr,nc) not in visited:
                        visited.add((nr,nc));stack.append((nr,nc))
            count+=not edge
    return count


def write(name,value):
    (OUT/name).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')

rows=[];first=None
for band in ('easy','medium','hard'):
    for seed in range(20):
        grid=module.generate(seed,0,difficulty=band)
        counts=Counter(holes(cells) for cells in components(grid))
        missing=[k for k in (0,1,2) if not counts[k]]
        record={'seed':seed,'sample_index':0,'difficulty':band,'holes':dict(sorted(counts.items())),'component_count':sum(counts.values()),'missing_mandatory_classes':missing,'self_check':module.self_check(grid)}
        rows.append(record)
        if missing and first is None:
            first={**record,'input':grid}
assert first is not None,'no omission in bounded sample'
canon_pairs=canonical_pairs(TASK,root=ROOT)
canon_checks=[{'variant':pair['variant'],'split':pair['split'],'pair_index':pair['pair_index'],'self_check':module.self_check(pair['input'])} for pair in canon_pairs]
no_legend=module.generate(0,0,texture='no_legend')
write('input.json',first['input'])
write('no-legend-input.json',no_legend)
write('canonical-inputs.json',[pair['input'] for pair in canon_pairs])
write('canonical-expected.json',[pair['output'] for pair in canon_pairs])
summary={'schema':'arcpuzzles-bounded-findings-audit-v1','task_id':TASK,'version':module.VERSION,'generator_source':str(source.relative_to(ROOT)),'generator_sha256':source_hash,'ledger_program_sha256':rulehash,'canonical_ledger_sha256':hashlib.sha256(canonical_path(ROOT).read_bytes()).hexdigest(),'scope':{'bands':['easy','medium','hard'],'seeds':'0..19 inclusive per band','sample_index':0,'draw_count':len(rows),'unique_input_count':len({json.dumps(module.generate(seed,0,difficulty=band)) for band in ('easy','medium','hard') for seed in range(20)})},'counts':{'missing_mandatory_class':sum(bool(r['missing_mandatory_classes']) for r in rows),'validator_accepted':sum(not r['self_check'] for r in rows)},'by_band':{band:{'draw_count':20,'missing_mandatory_class':sum(bool(r['missing_mandatory_classes']) for r in rows if r['difficulty']==band)} for band in ('easy','medium','hard')},'first_omission':first,'canonical_pair_count':len(canon_pairs),'canonical_rejected':sum(bool(r['self_check']) for r in canon_checks),'canonical_checks':canon_checks,'declared_no_legend':{'seed':0,'sample_index':0,'overrides':{'texture':'no_legend'},'self_check':module.self_check(no_legend),'legend_nonzero_count':sum(bool(v) for v in no_legend[0])},'draws':rows,'focused_tests':'No tests directory or focused target tests are present in this packet.'}
write('probe.json',summary)
print(json.dumps({key:summary[key] for key in ('generator_sha256','ledger_program_sha256','scope','counts','by_band','canonical_pair_count','canonical_rejected','declared_no_legend')},sort_keys=True))
