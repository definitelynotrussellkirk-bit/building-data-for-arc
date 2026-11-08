"""Run from WORK/repo through review.py run; authoring evidence only."""
from pathlib import Path
import argparse, hashlib, importlib.util, json
from arcpuzzles import Catalog
from reviewer_support import canonical_pairs

root = Path.cwd()
task = '2d2b102b7740'
parser = argparse.ArgumentParser(description='Check actual declared canonical rivals on an exact generated Racket witness.')
parser.add_argument('--out', type=Path, help='New report path; existing files are never overwritten.')
args = parser.parse_args()
source = root / 'generators' / task / 'generator.py'
raw = source.read_bytes()
spec = importlib.util.spec_from_file_location('shortcut_witness_generator', source)
gen = importlib.util.module_from_spec(spec)
exec(compile(raw, str(source), 'exec'), gen.__dict__)
canonical = canonical_pairs(task, root=root)
fits = {name: [rival(p['input']) == p['output'] for p in canonical]
        for name, rival in gen.CANONICAL_SHORTCUTS.items()}
assert all(all(values) for values in fits.values())
grid = gen.generate(0, 1, difficulty='medium')
receipt = Catalog(root).apply(task, [grid], reference='canonical', allow_unapproved=True)
actual = receipt['results'][0]['output']
rival_outputs = {name: rival(grid) for name, rival in gen.CANONICAL_SHORTCUTS.items()}
assert actual != rival_outputs['absolute_column_step']
report = {'task_id':task, 'generator_sha256':hashlib.sha256(raw).hexdigest(),
          'rule_hash':gen.RULE_HASH, 'seed':0, 'sample_index':1, 'difficulty':'medium',
          'overrides':{}, 'self_check':gen.self_check(grid), 'input':grid,
          'actual_racket_output':actual, 'rival_outputs':rival_outputs,
          'canonical_fit':fits, 'canonical_pair_count':len(canonical),
          'reference_receipt':receipt,
          'scope':'All declared canonical shortcuts fit every usable canonical pair; exact generated witness supplied.'}
out = args.out or root / 'generators' / task / 'counterexamples' / 'shortcut-witness.json'
with out.open('x') as f: json.dump(report,f,indent=2);f.write('\n')
if args.out is None:
    with (root.parent/'checks/repair/shortcut-witness.json').open('x') as f:
        json.dump(report,f,indent=2);f.write('\n')
print(json.dumps({'source':report['generator_sha256'],'canonical_shortcuts':len(fits),
                  'canonical_pairs':len(canonical),'shape':[len(grid),len(grid[0])],
                  'blue_cells':[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==1],
                  'red_cells':[(r,c) for r,row in enumerate(actual) for c,v in enumerate(row) if v==2]}))
