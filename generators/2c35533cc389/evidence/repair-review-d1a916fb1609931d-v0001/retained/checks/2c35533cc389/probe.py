"""One bounded source-before-write teaching audit; no generator edits."""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / 'shared/runtime'))
from reviewer_support import load_selected_generator
from arcpuzzles import Catalog
from arcpuzzles.parametric_worker import _real_evaluator

TASK = '2c35533cc389'
EXPECTED = 'e075e2031af5f502ee73f2bdfe45bc044e23ef3f48c1802e9bb1131fd38dd547'
module, source, digest = load_selected_generator(TASK, root=ROOT)
assert digest == EXPECTED
canonical = next(v['program_solution'] for v in Catalog(ROOT).get(TASK)['variants'] if v.get('program_solution'))
rival = '''(rule!
 (let* ((sources (find-color g 2))
        (heads (filter (lambda (p)
                 (not (member (list (first p) (- (second p) 1)) sources))) sources)))
   (paint-cells g
     (filter (lambda (p) (< (second p) w))
       (map (lambda (p) (list (first p) (+ (second p) 1))) heads)) 1)))'''
selected = None
for seed in range(16):
    demo = module.generate(seed, 2)
    query = module.generate(seed, 5)
    if (module.observe_overrides(demo)['right_edge_mode'] == 'present'
            and module.observe_overrides(query)['right_edge_mode'] == 'absent'):
        selected = seed
        break
assert selected is not None, 'No witness in bounded 16-seed search'
out = Path(__file__).resolve().parent
report = {
    'schema': '2c35533cc389-bounded-peer-audit-v1', 'task_id': TASK,
    'generator_source': str(source.relative_to(ROOT)), 'generator_sha256': digest,
    'probe_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'seed': selected, 'bounded_search_seeds_examined': selected + 1,
    'program': canonical, 'rival_program': rival,
    'rival_name': 'only_leftmost_red_in_horizontal_run',
    'scope': 'Three fixed-order production demos, their default anchor query, and one additional lawful overwrite query. No arbitrary rotation or production query-policy change claimed.',
    'racket_evaluations': 0, 'cases': [], 'errors': []}
bridge = None
try:
    execute, identity, bridge = _real_evaluator(ROOT / 'shared/runtime')
    report['racket'] = identity
    for index in (0, 1, 2, 3, 5):
        grid = module.generate(selected, index)
        assert not module.self_check(grid)
        gold = execute(canonical, grid)
        report['racket_evaluations'] += 1
        wrong = execute(rival, grid)
        report['racket_evaluations'] += 1
        assert gold == module.rule_mirror(grid)
        report['cases'].append({'sample_index': index, 'input': grid,
            'output': gold, 'rival_output': wrong,
            'controls': module.observe_overrides(grid), 'outputs_equal': gold == wrong})
    assert all(c['outputs_equal'] for c in report['cases'][:4])
    assert not report['cases'][4]['outputs_equal']
    demos = [{'input': c['input'], 'output': c['output']} for c in report['cases'][:3]]
    report['declared_rival_check_on_additional_query'] = module.lesson_identifiable(demos, {'input': report['cases'][4]['input']})
    assert not report['declared_rival_check_on_additional_query']
    report['status'] = 'finding'
    report['finding'] = 'An edge-anchored overwrite pair fails to teach that the overwritten red remains a source: the leftmost-only rival fits all three demos and the default anchor query, but differs on the additional lawful interior-overwrite query. Existing lesson_identifiable accepts that additional query because this rival is unlisted.'
    report['default_fixed_order_query_failure'] = False
    report['recommendation'] = 'If extending query assembly to interior overwrite queries, require an interior adjacent-red demonstration, or include this rival in a query-relevant teaching check. Preserve source-before-write semantics.'
    report['limits'] = 'One seed and one rival; no fixed-order production label bug demonstrated, no generator repair, no broad census, no acceptance or training admission.'
except Exception as exc:
    report['status'] = 'failed'
    report['errors'].append(type(exc).__name__ + ': ' + str(exc))
finally:
    if bridge is not None:
        bridge.close()
    (out / 'audit.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
print(json.dumps({key: report.get(key) for key in ('status','seed','racket_evaluations','finding','errors')}))
raise SystemExit(0 if report['status'] == 'finding' else 1)
