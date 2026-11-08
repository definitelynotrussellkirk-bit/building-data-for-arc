from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path

ROOT = Path.cwd()
GEN_PATH = ROOT / 'generators/e3a2ff6ea587/generator.py'
spec = importlib.util.spec_from_file_location('audit_e3', GEN_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(mod)

def groups(grid):
    order=[]; cells={}
    for r,row in enumerate(grid):
        for c,v in enumerate(row):
            if v == 0: continue
            if v not in cells:
                order.append(v); cells[v]=[]
            cells[v].append((r,c))
    return order,cells

def exact(ps):
    if len(ps) != 4: return False
    rs=[r for r,_ in ps]; cs=[c for _,c in ps]
    return set(ps)=={(min(rs),min(cs)),(min(rs),max(cs)),(max(rs),min(cs)),(max(rs),max(cs))} and min(rs)<max(rs) and min(cs)<max(cs)

def rival_bbox_every_color(grid):
    h,w=len(grid),len(grid[0]); out=[[0]*w for _ in range(h)]
    order,cells=groups(grid)
    for color in order:
        ps=cells[color]; rs=[r for r,_ in ps]; cs=[c for _,c in ps]
        for r in range(min(rs),max(rs)+1):
            for c in range(min(cs),max(cs)+1): out[r][c]=color
    return out

stats={}
all_hashes=[]
for band in ('easy','medium','hard'):
    total=300; malformed=0; grids=[]; rect_counts=[]
    for i in range(total):
        g=mod.generate(82000+i,i,difficulty=band)
        grids.append(g)
        _,cells=groups(g)
        rect_counts.append(len(cells))
        malformed += sum(not exact(ps) for ps in cells.values())
    hashes={hashlib.sha256(json.dumps(g,separators=(',',':')).encode()).hexdigest() for g in grids}
    stats[band]={
      'draws': total,
      'unique_inputs': len(hashes),
      'nonqualifying_nonbackground_colors': malformed,
      'rectangle_count_values': sorted(set(rect_counts)),
    }
    all_hashes.extend(hashes)

base=mod.generate(123,4,difficulty='medium')
override_results={}
for key,value in [
    ('palette_kind','warm'),('texture','warm'),('palette_size',1),
    ('position_bias','spread'),('n_distinct_colors',1),('rect_area','mixed'),
    ('unknown_axis','accepted?')]:
    try:
        got=mod.generate(123,4,difficulty='medium',**{key:value})
        override_results[key]={'accepted':True,'same_as_base':got==base}
    except Exception as exc:
        override_results[key]={'accepted':False,'error':type(exc).__name__+': '+str(exc)}

witness=json.loads((Path('..')/'checks/audit/e3a2ff6ea587/input.json').read_text())
# run_with_racket changes cwd to repo; evidence is one level up.
order,cells=groups(witness)
result={
  'task_id': mod.TASK_ID,
  'generator_version': mod.VERSION,
  'generator_sha256': hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
  'rule_hash_declared': mod.RULE_HASH,
  'sample_policy': {'seed':'82000+i','sample_index':'i','per_band':300},
  'ordinary_draws':stats,
  'override_results':override_results,
  'witness':{
    'self_check':mod.self_check(witness),
    'nonbackground_color_shapes':{str(k):{'cells':v,'qualifies_exact_four_corners':exact(v)} for k,v in cells.items()},
    'passes_validator':mod.self_check(witness)==[],
    'belongs_to_documented_ordinary_generator_domain':False,
    'domain_note':'Color 4 has only three bbox corners; ordinary generate() emits only positive exact-four-corner colors.',
    'rival':'fill every nonzero color bounding box on a fresh grid, ignoring exact-four-corner predicate',
    'rival_output':rival_bbox_every_color(witness),
  },
  'command': ['python3','run_with_racket.py','python3','../checks/audit/e3a2ff6ea587/probe.py'],
  'cwd':'packet_root',
}
(Path('..')/'checks/audit/e3a2ff6ea587/probe.json').write_text(json.dumps(result,indent=2)+'\n')
(Path('..')/'checks/audit/e3a2ff6ea587/rival.json').write_text(json.dumps(result['witness']['rival_output'],indent=2)+'\n')
print(json.dumps(result,indent=2))
