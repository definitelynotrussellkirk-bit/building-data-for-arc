"""Bounded recheck of the retained left-justification teaching shortcut."""
import hashlib
import importlib.util
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_path, normalize_grid

ROOT = Path.cwd()
TASK = '664a918eb273'
OUT = ROOT.parent / 'checks' / TASK
source_path = ROOT / 'generators' / TASK / 'generator.py'
spec = importlib.util.spec_from_file_location('audited_paths', source_path)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines()
        if line.strip()]
task = next(row for row in rows if row.get('task_id') == TASK)
canonical = task['program_solution']
site = '(define all-cells (process (cdr infos) first-exit first-with-color))'
assert canonical.count(site) == 1
rival = canonical.replace(site, '''(define raw-all-cells (process (cdr infos) first-exit first-with-color))
             (define anchor (min-of second raw-all-cells))
             (define all-cells (map (lambda (cell)
                (list (first cell) (- (second cell) anchor) (nth cell 2))) raw-all-cells))''')

def digest(value):
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()

def execute(bridge, program, grid):
    assert program.startswith('(rule! ') and program.endswith(')')
    literal = "'(" + ' '.join('(' + ' '.join(map(str,row)) + ')' for row in grid) + ')'
    return normalize_grid(bridge.eval_text('(' + program[7:-1] + ' ' + literal + ')'))

cases = []
with RacketBridge() as bridge:
    runtime = bridge.runtime_identity
    assert runtime['backend'] == 'racket' and runtime['protected'] is True
    for split in ('train', 'test'):
        for index, pair in enumerate(task.get(split, [])):
            grid = normalize_grid(pair['input'])
            output = execute(bridge, canonical, grid)
            wrong = execute(bridge, rival, grid)
            assert output == normalize_grid(pair['output'])
            cases.append({'role': 'canonical_' + split, 'index': index,
                          'input': grid, 'output': output, 'rival_output': wrong,
                          'rival_matches': output == wrong})
    grid = gen.generate(0, 1)
    assert gen.self_check(grid) == []
    observed = gen.observe_overrides(grid)
    assert observed['anchor_col'] > 0
    output = execute(bridge, canonical, grid)
    wrong = execute(bridge, rival, grid)
    assert output != wrong
    assert wrong == gen.SEMANTIC_RIVALS['left_justify_packed_chain'](grid)
    witness = {'role': 'generated_query', 'seed': 0, 'sample_index': 1,
               'overrides': {}, 'observed_axes': observed, 'input': grid,
               'output': output, 'rival_output': wrong, 'rival_matches': False}
    cases.append(witness)

assert all(case['rival_matches'] for case in cases if case['role'].startswith('canonical_'))
report = {
    'task_id': TASK, 'outcome': 'unchanged',
    'finding': 'Reproduced retained canonical-demo ambiguity: always left-justify fits all canonical labels, but differs on a lawful positive-anchor query.',
    'new_source_defect': False,
    'generator_sha256': digest(source_path.read_bytes()),
    'canonical_source_sha256': digest(canonical),
    'rival_source_sha256': digest(rival),
    'probe_sha256': digest(Path(__file__).read_bytes()),
    'canonical_program': canonical, 'rival_program': rival,
    'racket': runtime, 'cases': cases,
    'teaching_repair': 'Include one positive-anchor demonstration, e.g. generated seed=0 sample_index=1, before asking an unseen positive-anchor query. It refutes this rival without changing the rule.',
    'limitations': ['One retained rival; five canonical pairs and one generated input.',
                    'Canonical-only teaching context is audited; no claim that the ordinary production schedule emits this context.',
                    'Current sampler already includes positive-anchor expanded cases; no new generator change is justified.',
                    'No universal identifiability, broad census, or training eligibility conclusion.']}
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'learnability.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: report[k] for k in ('task_id','outcome','finding','generator_sha256','canonical_source_sha256','rival_source_sha256')}))
