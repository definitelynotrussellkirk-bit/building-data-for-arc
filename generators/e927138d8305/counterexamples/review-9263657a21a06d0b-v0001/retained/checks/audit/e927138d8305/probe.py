"""Small findings-only canonical support and exact dimension audit."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--repo', required=True)
parser.add_argument('--out', required=True)
args = parser.parse_args()
repo = Path(args.repo).resolve()
out = Path(args.out).resolve()
sys.path.insert(0, str(repo / 'shared/runtime'))
from reviewer_support import canonical_pairs, canonical_path, find_root

root = find_root(repo / 'generators/e927138d8305/generator.py')
source = root / 'generators/e927138d8305/generator.py'
spec = importlib.util.spec_from_file_location('audit_e927_target', source)
target = importlib.util.module_from_spec(spec)
spec.loader.exec_module(target)
pairs = canonical_pairs(target.TASK_ID, root=root, labeled_only=True)
rows = [json.loads(line) for line in canonical_path(root).open() if line.strip()]
row = next(row for row in rows if row.get('task_id') == target.TASK_ID)
rule = row['program_solution']
sha = lambda data: hashlib.sha256(data).hexdigest()
canonical = []
for pair in pairs:
    comps = target._components(pair['input'])
    canonical.append({**pair, 'validator_errors': target.self_check(pair['input']),
        'components': [{'cells': cells,
                        'solid_rect': target._is_solid_rect(cells),
                        'colors': sorted({pair['input'][r][c] for r, c in cells})}
                       for cells in comps]})
controls = []
for overrides in ({'grid_h':7}, {'grid_h':16}, {'grid_w':8}, {'grid_w':18}):
    record = {'seed':0, 'sample_index':0, 'difficulty':None, 'overrides':overrides}
    try:
        grid = target.generate(0, 0, **overrides)
        record.update(status='returned', input=grid, validator_errors=target.self_check(grid))
    except Exception as exc:
        record.update(status='raised', exception_type=type(exc).__name__, exception=str(exc))
    controls.append(record)
generated = target.generate(0, 0)
canonical_witness = next(p for p in canonical if p['split']=='train' and p['pair_index']==2)
report = {'task_id':target.TASK_ID, 'generator_version':target.VERSION,
    'generator_sha256':sha(source.read_bytes()),
    'rule_sha256':sha(rule.encode()), 'rule':rule,
    'review_index_status':'absent', 'associated_notes_bytes':0,
    'canonical_pairs':canonical, 'canonical_validator_rejections':sum(bool(p['validator_errors']) for p in canonical),
    'canonical_denominator':len(canonical), 'exact_dimension_controls':controls,
    'generated_witness':{'seed':0,'sample_index':0,'difficulty':None,'overrides':{},
        'input':generated,'validator_errors':target.self_check(generated)},
    'apply_input_order':['canonical variant 0 train pair 2','generated seed 0 index 0 default']}
out.mkdir(parents=True,exist_ok=True)
(out/'probe.json').write_text(json.dumps(report,indent=2)+'\n')
(out/'input.json').write_text(json.dumps([canonical_witness['input'],generated])+'\n')
print(json.dumps({'generator_sha256':report['generator_sha256'],
    'rule_sha256':report['rule_sha256'],
    'canonical_rejections':report['canonical_validator_rejections'],
    'canonical_denominator':len(canonical),
    'controls':[{'overrides':r['overrides'],'status':r['status'],'exception':r.get('exception')} for r in controls],
    'generated_validator_errors':target.self_check(generated)}))
