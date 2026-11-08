import hashlib
import importlib.util
import json
from fractions import Fraction
from pathlib import Path
import sys

ROOT = Path.cwd()
OUT = ROOT.parent / 'checks/audit/f86f870eb9f2'
GEN = ROOT / 'generators/f86f870eb9f2/generator.py'
AUTH = ROOT / 'shared/data/base/solutions/banks/445ef4275a64/S21_M3__f86f870eb9f2.json'
spec = importlib.util.spec_from_file_location('audit_target', GEN)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

def save(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2) + '\n')

def rival(grid):
    facts = gen.analyze_scene(grid)
    rooms = facts['rooms']
    largest = max(range(len(rooms)), key=lambda i: rooms[i]['area'])
    eligible = [i for i in range(len(rooms)) if i != largest]
    target = max(eligible, key=lambda i: Fraction(rooms[i]['marker_count'], rooms[i]['area']))
    output = [[v if v in (1,7,9) else 0 for v in row] for row in grid]
    for r,c in rooms[target]['cells']:
        output[r][c] = 8
    return output

if sys.argv[1] == 'prepare':
    canonical = json.loads(AUTH.read_text())
    query = canonical['visible_context']['train'][1]['input']
    params = [{'seed': 100, 'sample_index': i, 'difficulty': 'medium', 'overrides': {}} for i in range(3)]
    demos = [gen.generate(p['seed'], p['sample_index'], difficulty=p['difficulty'], **p['overrides']) for p in params]
    save('input.json', {'inputs': [query] + demos})
    save('generation.json', {'demo_parameters': params, 'query_origin': 'exact canonical visible_context.train[1].input', 'generator_sha256': hashlib.sha256(GEN.read_bytes()).hexdigest(), 'canonical_authority_sha256': hashlib.sha256(AUTH.read_bytes()).hexdigest(), 'declared_rule_hash': gen.RULE_HASH})
    save('rival.json', {'name': 'densest_except_largest_room', 'outputs': [rival(g) for g in [query] + demos]})
    save('validators.json', {'self_check': [gen.self_check(g) for g in [query] + demos], 'strict_canonical_like': [gen.strict_canonical_like(g) for g in [query] + demos], 'observed_demo_overrides': [gen.observe_overrides(g) for g in demos]})
    print('Prepared exact canonical query and three generated demo inputs.')
elif sys.argv[1] == 'finish':
    inputs = json.loads((OUT / 'input.json').read_text())['inputs']
    applied = json.loads((OUT / 'racket.json').read_text())
    outputs = [r['output'] for r in applied['results']]
    assert all(r['valid_output'] and r['error'] is None for r in applied['results'])
    rivals = json.loads((OUT / 'rival.json').read_text())['outputs']
    demos = [{'input': g, 'output': o} for g,o in zip(inputs[1:], outputs[1:])]
    reasons = gen.lesson_identifiable(demos, {'input': inputs[0], 'output': outputs[0]})
    assert reasons == [], reasons
    assert all(a == b for a,b in zip(outputs[1:], rivals[1:]))
    assert outputs[0] != rivals[0]
    facts = gen.analyze_scene(inputs[0])
    save('finding.json', {'status': 'issue_found', 'kind': 'teaching_distribution_shortcut', 'rival_matches_all_three_racket_labeled_demos': True, 'rival_disagrees_with_canonical_query': True, 'lesson_identifiable_reasons': reasons, 'query_rooms': [{'index': i, 'area': room['area'], 'marker_count': room['marker_count']} for i,room in enumerate(facts['rooms'])], 'query_true_target_index': facts['target_index'], 'query_rival_target_index': 1, 'different_output_cells': sum(a!=b for ra,rb in zip(outputs[0],rivals[0]) for a,b in zip(ra,rb)), 'measured_scope': 'Exactly three generated medium demos: seed 100, indices 0,1,2, no overrides; one exact canonical train[1] query; all four publicly Racket applied.', 'domain_claims': {'query_validator_acceptance': 'self_check and strict_canonical_like both return []', 'query_canonical_membership': 'exact canonical visible_context.train[1].input', 'query_generation_membership': 'not claimed; source excludes the unique largest room from target_candidates on every generated input', 'generated_semantics': 'No observed wrong Racket labels. Issue is systematic exclusion of a canonical winning geometry and omitted rival.'}, 'source_argument': 'generate sets largest_index to the maximum area room and target_candidates to all other indices before choosing target_index; the strict density/count reversal and validators preserve that nonlargest winner. All declared geometries have a unique largest room.'})
    print('Confirmed rival fits all three public Racket demos, fails canonical query, and lesson_identifiable accepts the lesson.')
else:
    raise ValueError('expected prepare or finish')
