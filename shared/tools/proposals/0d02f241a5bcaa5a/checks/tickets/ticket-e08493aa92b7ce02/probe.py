"""One source-pinned valid/invalid advertised offset_choice comparison."""
from pathlib import Path
import hashlib
import json
import time
from reviewer_support import load_selected_generator

start = time.monotonic()
task = '1e36fd36fdb1'
expected = '6816d4ef50571f77b91d050379f8b1ef02b2b1b6d5a8b41ba260ba945fe2626a'
module, source, source_sha = load_selected_generator(task)
if source_sha != expected:
    raise ValueError('Pinned ticket source differs')
seed_hex = '6459b5c066962d14653f2d27e21bd87fddcfefdb47984565277b0f9219ca99d6'
seed = int(seed_hex[:16], 16)
records = []
for choice in (0, 5):
    try:
        grid = module.generate(seed, 0, offset_choice=choice)
        positions = {color: [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color][0]
                     for color in (2, 3, 4, 8)}
        origin = positions[2]
        vx = tuple(b-a for a,b in zip(origin,positions[3]))
        vy = tuple(b-a for a,b in zip(origin,positions[4]))
        delta = tuple(b-a for a,b in zip(origin,positions[8]))
        observed = [sum(a*b for a,b in zip(delta,vx)),sum(a*b for a,b in zip(delta,vy))]
        records.append({'offset_choice': choice,'returned': True,'grid': grid,
                        'grid_sha256': hashlib.sha256(json.dumps(grid,separators=(',',':')).encode()).hexdigest(),
                        'observed_local_offset': observed,'self_check': module.self_check(grid)})
    except Exception as exc:
        records.append({'offset_choice': choice,'returned': False,'exception': type(exc).__name__,'message': str(exc)})
report = {'ticket_id':'ticket-e08493aa92b7ce02','type':'api_boundary','task_id': task,
          'source_sha256':source_sha,'rule_hash':'3c21b4618c96','probe_seed':seed_hex,
          'seed_derivation':'int(first 16 hexadecimal characters,16)','seed':seed,'sample_index':0,
          'advertised_axis':module.AXES['offset_choice'],'advertised_offsets':module.OFFSETS,
          'valid_invalid_calls':records,'probe_elapsed_seconds':time.monotonic()-start,
          'identical_returned_grids': all(r.get('returned') for r in records) and records[0]['grid']==records[1]['grid'],
          'interpretation':'offset_choice is advertised but ignored: out-of-range5 returns the same valid grid as0. This is an API/coverage contract defect; no wrong reference label or unsafe grid was established.',
          'proposed_action':'Honor and strictly validate offset_choice0..4, or withdraw that advertised axis. Keep this peer source unchanged in this return.',
          'scope_limit':'One advertised override boundary, two calls; no peer safety battery or Racket label claim.'}
p=Path('../checks/tickets/ticket-e08493aa92b7ce02/result.json')
p.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['ticket_id','source_sha256','identical_returned_grids','interpretation']}))
