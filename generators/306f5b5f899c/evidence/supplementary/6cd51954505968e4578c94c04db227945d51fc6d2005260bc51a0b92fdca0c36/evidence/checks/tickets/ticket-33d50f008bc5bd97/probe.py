"""One bounded shortcut witness probe for pinned peer 306f5b5f899c."""
from pathlib import Path
import hashlib
import json
import signal
import time

from reviewer_support import canonical_path, find_root, load_selected_generator
from arc_repl.racket_bridge import RacketBridge

TASK = '306f5b5f899c'
TICKET = 'ticket-33d50f008bc5bd97'
PIN = '2b94c076ff1edc8e26643b27c31302522d3e849e4a13326dced5c9c9dcce076b'
RULE_PIN = '2cde2dccfbeb'
SEED_HEX = 'f24a219f5f6d709205517912c08df70bda9114c9c427d153cc1fb81290e58107'
OUT = Path(__file__).resolve().parent
START = time.monotonic()

def timed_out(signum, frame):
    raise TimeoutError('One targeted probe reached its 110-second internal deadline')
signal.signal(signal.SIGALRM, timed_out)
signal.alarm(110)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def components(grid):
    seen, result = set(), []
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if not color or (r,c) in seen:
                continue
            todo, cells = [(r,c)], []
            seen.add((r,c))
            while todo:
                rr,cc=todo.pop(); cells.append((rr,cc))
                for nr,nc in ((rr-1,cc),(rr+1,cc),(rr,cc-1),(rr,cc+1)):
                    if (0<=nr<len(grid) and 0<=nc<len(row) and (nr,nc) not in seen
                            and grid[nr][nc]==color):
                        seen.add((nr,nc)); todo.append((nr,nc))
            r0=min(p[0] for p in cells); c0=min(p[1] for p in cells)
            h=max(p[0] for p in cells)-r0+1; w=max(p[1] for p in cells)-c0+1
            result.append({'color':color,'size':len(cells),'bbox_area':h*w,'top_left':[r0,c0],
                           'shape':[(rr-r0,cc-c0) for rr,cc in cells],'height':h,'width':w})
    return result

def union(objs, key):
    chosen=sorted(objs,key=lambda o:(-o[key],*o['top_left']))[:2]
    g=[[0]*max(o['width'] for o in chosen) for _ in range(max(o['height'] for o in chosen))]
    for o in chosen:
        for r,c in o['shape']: g[r][c]=8
    return g, [o['color'] for o in chosen]

result={'schema':'arcpuzzles-bounded-adversarial-witness-v1','ticket_id':TICKET,
        'task_id':TASK,'consumer':'target_current_audit','status':'unknown',
        'shortcut':'Select the two motifs with largest bounding-box area instead of largest occupied-cell count; retain the same top-left tie-break and normalized union.'}
try:
    root=find_root(__file__)
    source_path=root/'generators'/TASK/'generator.py'
    if sha(source_path.read_bytes()) != PIN:
        raise ValueError('Pinned peer source differs before import')
    module, loaded_path, source_hash=load_selected_generator(TASK,root=root)
    if source_hash!=PIN or loaded_path.resolve()!=source_path.resolve():
        raise ValueError('Pinned peer source differs after exact-source loader')
    programs={r['program_solution'] for line in canonical_path(root).read_text().splitlines()
              if (r:=json.loads(line)).get('task_id')==TASK}
    if len(programs)!=1: raise ValueError('Expected one canonical program')
    program=programs.pop()
    rule_hash=sha(' '.join(program.split()).encode())[:12]
    if rule_hash!=RULE_PIN: raise ValueError('Canonical rule differs from pinned ticket')
    result['bindings']={'generator_sha256':source_hash,'rule_task_id':TASK,'rule_hash':rule_hash,
                        'canonical_program_sha256':sha(program.encode()),'probe_sha256':sha(Path(__file__).read_bytes())}
    seed=int(SEED_HEX,16)
    inspected=[]; grid=None; origin=None
    # One small fixed schedule, stopping immediately at the first separating draw.
    for index in range(12):
        candidate=module.generate(seed,index,difficulty='medium')
        errors=module.self_check(candidate)
        if errors: raise ValueError(f'Generated witness failed self_check: {errors}')
        objs=components(candidate)
        actual, chosen=union(objs,'size'); rival, wrong=union(objs,'bbox_area')
        inspected.append({'sample_index':index,'separates':actual!=rival})
        if actual!=rival:
            grid=candidate; origin={'kind':'generated','seed':seed,'ticket_seed':SEED_HEX,
                                     'sample_index':index,'difficulty':'medium','overrides':{}}
            break
    if grid is None:
        # Lawful source-supported shapes: 3 distinct connected motifs of 3..7 cells,
        # each bbox is separated, on a default-sized 9x11 board.
        grid=[[0]*11 for _ in range(9)]
        for color,r0,c0,cells in (
            (2,0,0,[(0,0),(0,1),(0,2),(1,0),(1,1),(1,2),(2,0)]),
            (3,0,7,[(0,0),(0,1),(0,2),(1,0),(1,1),(1,2)]),
            (4,6,0,[(0,0),(1,0),(2,0),(2,1),(2,2)])):
            for rr,cc in cells: grid[r0+rr][c0+cc]=color
        origin={'kind':'authored_lawful','support':'Default 9x11, three separated connected motifs, distinct permitted colors, sizes 7/6/5; every shape is reachable by the connected growth procedure.'}
    errors=module.self_check(grid)
    if errors: raise ValueError(f'Witness self_check failure: {errors}')
    objs=components(grid)
    predicted, chosen=union(objs,'size'); shortcut, wrong=union(objs,'bbox_area')
    if predicted==shortcut: raise ValueError('Witness does not separate selected shortcut')
    rival_program=program
    for symbol,bb in (('a','ba'),('b','bb')):
        old=f'(obj-size {symbol})'
        if rival_program.count(old)!=1: raise ValueError('Unexpected canonical comparison shape')
        replacement=f'(* (+ 1 (- (third {bb}) (first {bb}))) (+ 1 (- (fourth {bb}) (second {bb}))))'
        rival_program=rival_program.replace(old,replacement,1)
    if not program.startswith('(rule! ') or not program.endswith(')'):
        raise ValueError('Unexpected canonical wrapper')
    literal='('+' '.join('('+' '.join(map(str,row))+')' for row in grid)+')'
    with RacketBridge(timeout=15) as bridge:
        # Apply the exact body inside the canonical rule! wrapper with its g bound.
        answer=bridge.eval_text(f"(let ((g '{literal})) {program[7:-1]})")
        rival_answer=bridge.eval_text(f"(let ((g '{literal})) {rival_program[7:-1]})")
        runtime=bridge.runtime_identity
    if answer!=predicted or rival_answer!=shortcut or answer==rival_answer:
        raise ValueError('Racket did not confirm the independently calculated separating outputs')
    result.update(status='completed',safety_finding=False,origin=origin,
                  inspected_samples=inspected,inspected_sample_limit=12,
                  self_check_errors=errors,canonical_selected_colors=chosen,
                  shortcut_selected_colors=wrong,objects=objs,
                  canonical_program=program,rival_program=rival_program,
                  rival_program_sha256=sha(rival_program.encode()),input=grid,
                  output=answer,shortcut_output=rival_answer,
                  differing_cells=[[r,c] for r in range(max(len(answer),len(rival_answer)))
                                   for c in range(max(len(answer[0]),len(rival_answer[0])))
                                   if (answer[r][c] if r<len(answer) and c<len(answer[0]) else None)
                                   !=(rival_answer[r][c] if r<len(rival_answer) and c<len(rival_answer[0]) else None)],
                  racket={k:runtime[k] for k in ('schema','backend','protected','binary_sha256','prelude_sha256','bridge_sha256','boot_script_sha256','candidate_symbol_policy_sha256') if k in runtime},
                  summary='Retained one lawful witness separating occupied-cell count from bounding-box area. The pinned generator exposes the shortcut; no peer safety defect established.',
                  limits=['One shortcut and at most 12 fixed sample indices; no generator-wide safety, frequency or coverage conclusion.','No peer source edits, full battery, qualification, acceptance or training admission.'])
except Exception as error:
    result.update(status='blocked',safety_finding=False,error=f'{type(error).__name__}: {error}',summary='Bounded probe could not establish the requested witness.')
finally:
    signal.alarm(0)
    result['elapsed_probe_seconds']=round(time.monotonic()-START,3)
    (OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:result.get(key) for key in ('status','summary','error','elapsed_probe_seconds','origin','canonical_selected_colors','shortcut_selected_colors')}))
