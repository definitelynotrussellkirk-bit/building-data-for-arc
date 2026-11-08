"""Bounded protected-Racket teaching audit of one peer; no source mutations."""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / 'src'))
from arcpuzzles.catalog import Catalog
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator

TASK = '35c7e1c0d116'
OUT = ROOT.parent / 'checks' / TASK / 'audit.json'
COMMAND = 'WORK/.venv/bin/python review.py run python3 ../checks/35c7e1c0d116/audit_peer.py'
catalog = Catalog(ROOT)
row = catalog.describe(TASK)
records = catalog._variants()[row.get('rule_task_id', TASK)]
assert len({r['program_solution'] for r in records}) == 1
canonical = records[0]['program_solution']
predicate = '(member? (normalize-cells (panel-occ (list-ref panels c))) (dihedral-variants (panel-occ (list-ref panels r))))'
assert canonical.count(predicate) == 1
rotation_clause = '(list (normalize-cells rot) (normalize-cells (reflect-h-cells rot)))'
assert canonical.count(rotation_clause) == 1
rivals = {
    'diagonal_only': canonical.replace(predicate, '(= r c)'),
    'cell_count_only': canonical.replace(predicate, '(= (length (panel-occ (list-ref panels c))) (length (panel-occ (list-ref panels r))))'),
    'rotation_only': canonical.replace(rotation_clause, '(list (normalize-cells rot))'),
}

def normalize(grid):
    return [[int(c) for c in r] if isinstance(r, str) else r for r in grid]

def pairs(value):
    return value if isinstance(value, list) else [value]

lessons = []
for i, record in enumerate(records):
    lessons.append({'origin': 'canonical_saved', 'variant': i,
                    'train': [{'input': normalize(p['input']), 'output': normalize(p['output'])} for p in pairs(record['train'])],
                    'test': [{'input': normalize(p['input']), **({'output': normalize(p['output'])} if 'output' in p else {})} for p in pairs(record['test'])]})
# Explicit research generation retains unapproved provenance; no approval changes.
for episode in catalog.generate(TASK, count=3, seed=0, difficulty='easy', n_train=3, n_test=4, timeout=60, allow_unapproved=True):
    lessons.append({'origin': 'native_generated', 'episode': episode,
                    'train': [{'input': normalize(p['input']), 'output': normalize(p['output'])} for p in pairs(episode['train'])],
                    'test': [{'input': normalize(p['input']), 'output': normalize(p['output'])} for p in pairs(episode['test'])]})

checks, findings = [], []
with _local_imports(ROOT/'shared/runtime', ROOT/'shared/runtime'):
    apply, identity, bridge = _real_evaluator(ROOT/'shared/runtime')
    try:
        for lesson_index, lesson in enumerate(lessons):
            labels = {}
            for name, program in {'canonical': canonical, **rivals}.items():
                labels[name] = {split: [_grid(apply(program, pair['input'])) for pair in lesson[split]] for split in ('train', 'test')}
            for split in ('train', 'test'):
                for pair, output in zip(lesson[split], labels['canonical'][split]):
                    if 'output' in pair:
                        assert output == pair['output'], 'Native/saved canonical label disagrees'
                    pair['output'] = output
            for name in rivals:
                survives = labels[name]['train'] == labels['canonical']['train']
                query_differences = [i for i, (a,b) in enumerate(zip(labels[name]['test'], labels['canonical']['test'])) if a != b]
                check = {'lesson_index': lesson_index, 'rival': name, 'fits_all_demos': survives,
                         'query_disagreement_indices': query_differences, 'rival_outputs': labels[name]}
                checks.append(check)
                if survives and query_differences:
                    findings.append({'kind': 'demonstration_teaching_hole', **check})
    finally:
        bridge.close()

result = {'schema': 'arcpuzzles-bounded-peer-teaching-audit-v1', 'task_id': TASK,
          'status': 'finding' if findings else 'no_issue_in_bounded_check',
          'command': COMMAND, 'source_binding': {'generator_path': row['generator'],
              'generator_sha256': row['generator_sha256'], 'rule_hash': row['rule_hash'],
              'canonical_program_sha256': hashlib.sha256(canonical.encode()).hexdigest(),
              'ledger_sha256': hashlib.sha256((ROOT/'shared/data/canonical/puzzles.jsonl').read_bytes()).hexdigest()},
          'programs': {'canonical': canonical, **rivals}, 'racket': identity,
          'lessons': lessons, 'checks': checks, 'findings': findings,
          'prior_evidence': 'generators/35c7e1c0d116/evidence/review_index.json',
          'limits': 'Only canonical saved lesson and three ordinary easy native episodes at seeds 0..2, with three declared rivals. No exhaustive uniqueness, empty-panel census, semantic repair, batteries, approval or training claim.'}
assert catalog.describe(TASK)['generator_sha256'] == row['generator_sha256']
OUT.write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps({'status':result['status'], 'lessons':len(lessons), 'rival_checks':len(checks), 'findings':len(findings), 'output':str(OUT)}))
