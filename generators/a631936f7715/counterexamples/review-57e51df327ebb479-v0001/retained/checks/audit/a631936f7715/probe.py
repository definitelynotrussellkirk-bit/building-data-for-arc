from pathlib import Path
import hashlib, importlib.util, json, sys

WORK = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(WORK / 'repo/shared/runtime'))
from reviewer_support import canonical_pairs
SOURCE = WORK / 'repo/generators/a631936f7715/generator.py'
spec = importlib.util.spec_from_file_location('audited_generator', SOURCE)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def connected_rival(grid, diagonal=False):
    h, w = len(grid), len(grid[0])
    result = [[7]*w for _ in range(h)]
    seen = set()
    moves = [(-1,0),(1,0),(0,-1),(0,1)]
    if diagonal:
        moves += [(-1,-1),(-1,1),(1,-1),(1,1)]
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 6 or (r,c) in seen:
                continue
            todo, comp = [(r,c)], []
            seen.add((r,c))
            while todo:
                cr, cc = todo.pop()
                comp.append((cr,cc))
                for dr,dc in moves:
                    nr,nc=cr+dr,cc+dc
                    if 0<=nr<h and 0<=nc<w and grid[nr][nc]==6 and (nr,nc) not in seen:
                        seen.add((nr,nc));todo.append((nr,nc))
            labels={grid[nr][nc] for cr,cc in comp for dr,dc in [(-1,0),(1,0),(0,-1),(0,1)]
                    for nr,nc in [(cr+dr,cc+dc)] if 0<=nr<h and 0<=nc<w and grid[nr][nc] not in (6,7)}
            color=min(labels) if labels else 6
            for cr,cc in comp:result[cr][cc]=color
    return result

rows=[]
for band in ['easy','medium','hard']:
    for seed in range(5):
        for key in ['palette_kind','texture']:
            invalid={key:'typo'}
            control={key:'broad'}
            item={'seed':seed,'sample_index':0,'difficulty':band,'overrides':invalid,'control_overrides':control}
            try:
                bad=gen.generate(seed,0,difficulty=band,**invalid)
                good=gen.generate(seed,0,difficulty=band,**control)
                item.update(status='accepted',self_check=gen.self_check(bad),same_as_broad=bad==good,input=bad)
            except Exception as e:
                item.update(status='raised',exception_type=type(e).__name__,error=str(e))
            rows.append(item)
pairs=canonical_pairs('a631936f7715',root=WORK/'repo',labeled_only=True)
canonical=[]
for p in pairs:
    canonical.append({**p,'self_check':gen.self_check(p['input']),
                      'four_connected_explanation_matches':connected_rival(p['input'])==p['output'],
                      'eight_connected_rival_matches':connected_rival(p['input'],True)==p['output']})
generated=gen.generate(9,0,difficulty='easy',palette_kind='typo')
crafted=[[7,1,7,7,7],[7,6,6,7,7],[7,7,7,6,2],[7,7,7,6,7],[7,7,7,7,7]]
inputs=[generated,crafted]
for name,value in [('input.json',inputs),('rival.json',[connected_rival(g,True) for g in inputs]),('four_connected_explanation.json',[connected_rival(g) for g in inputs])]:
    (OUT/name).write_text(json.dumps(value,indent=2)+'\n')
rule_rows=[]
for line in (WORK/'repo/shared/data/canonical/puzzles.jsonl').open():
    row=json.loads(line)
    if row.get('task_id')=='a631936f7715':
        source=row['program_solution']
        rule_rows.append({'source':row['source'],'content_hash':row['content_hash'],'written_solution':row['written_solution'],
                          'program_solution':source,'rule_text_sha256':hashlib.sha256(source.encode()).hexdigest()})
report={'task_id':'a631936f7715','phase':'final unchanged audited source',
        'generator_sha256':digest(SOURCE),'declared_rule_hash':gen.RULE_HASH,
        'canonical_ledger_sha256':digest(WORK/'repo/shared/data/canonical/puzzles.jsonl'),
        'generator_axes':gen.AXES,'command':'PYTHONPATH=repo/shared/runtime python3 checks/audit/a631936f7715/probe.py',
        'cwd':str(WORK),'finite_scope':{'seed_range':'0..4 inclusive','sample_index':0,'bands':['easy','medium','hard'],
          'invalid_override_cases':30,'valid_broad_controls':30,'canonical_pairs':len(pairs),
          'canonical_unique_inputs':len({json.dumps(p['input']) for p in pairs}),'counterexamples':2},
        'invalid_override_results':rows,'canonical_checks':canonical,'canonical_rule_rows':rule_rows,
        'inputs':[
          {'input_index':0,'origin':'generated','seed':9,'sample_index':0,'difficulty':'easy','overrides':{'palette_kind':'typo'},
           'self_check':gen.self_check(generated),'documented_domain':'grid is lawful; requested categorical value lies outside AXES.valid'},
          {'input_index':1,'origin':'crafted','seed':None,'sample_index':None,'overrides':None,'self_check':gen.self_check(crafted),
           'documented_domain':'two distinct labeled 4-connected dominoes on orange background; components touch diagonally only'}]}
report['totals']={'accepted_invalid':sum(r['status']=='accepted' for r in rows),
                  'self_check_clean_invalid':sum(r.get('self_check')==[] for r in rows),
                  'identical_to_broad_control':sum(r.get('same_as_broad') is True for r in rows),
                  'canonical_four_fit':sum(p['four_connected_explanation_matches'] for p in canonical),
                  'canonical_eight_fit':sum(p['eight_connected_rival_matches'] for p in canonical)}
(OUT/'probe.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report['totals']))
print('generator_sha256',report['generator_sha256'])
print('canonical rule text hashes',[r['rule_text_sha256'] for r in rule_rows])
