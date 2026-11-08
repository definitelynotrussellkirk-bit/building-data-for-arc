from __future__ import annotations
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from reviewer_support import canonical_pairs, canonical_path, find_root

TASK = '38300735cc4d'
HERE = Path(__file__).resolve().parent
ROOT = find_root(HERE.parents[2] / 'repo')
SOURCE = ROOT / 'generators' / TASK / 'generator.py'
spec = importlib.util.spec_from_file_location('audited_generator', SOURCE)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
sha = lambda data: hashlib.sha256(data).hexdigest()
canonical = canonical_pairs(TASK, root=ROOT)
canonical_rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines() if json.loads(line).get('task_id') == TASK]
assert len(canonical_rows) == 1
rule = canonical_rows[0]['program_solution']
canonical_results = []
for name, rival in gen.CANONICAL_SHORTCUTS.items():
    matches = [rival(pair['input']) == pair['output'] for pair in canonical]
    canonical_results.append({'name': name, 'matched_pairs': sum(matches), 'pair_count': len(matches), 'all_match': all(matches)})
assert all(row['all_match'] for row in canonical_results)

# A bounded clean scene whose only two paths consist of adjacent endpoints.
# self_check claims to reject rule-hiding scenes, but this has no missing cell.
witness = [[0]*6 for _ in range(6)]
witness[0][0] = witness[0][1] = 2
witness[2][3] = witness[3][3] = 3
assert gen.self_check(witness) == []
assert gen.observe_overrides(witness) == {'grid_h': 6, 'grid_w': 6, 'scene_profile': 'clean_varied'}
assert gen.rule_mirror(witness) == witness

inputs = [witness]
records = [{'kind': 'constructed', 'seed': None, 'sample_index': None, 'overrides': None, 'validator_errors': gen.self_check(witness), 'documented_generated_domain': False, 'reason': 'Both aligned pair spans are 1; _candidate_segments starts end at start+2 and generate rejects identity output.'}]
for bi, band in enumerate(('easy', 'medium', 'hard')):
    seed = 77000 + bi
    for index in range(6):
        grid = gen.generate(seed, index, difficulty=band)
        errors = gen.self_check(grid)
        assert not errors
        inputs.append(grid)
        records.append({'kind': 'generated', 'seed': seed, 'sample_index': index, 'difficulty': band, 'overrides': {}, 'validator_errors': errors, 'scene_profile': gen.observe_overrides(grid)['scene_profile']})

# Exhaust all cyclic starts of the public six-residue schedule for this seed
# in each band. These checks use the public Python mirror, not Racket labels.
lessons = []
for bi, band in enumerate(('easy', 'medium', 'hard')):
    seed = 77000 + bi
    for start in range(6):
        grids = [gen.generate(seed, start+offset, difficulty=band) for offset in range(6)]
        pairs = [{'input': grid, 'output': gen.rule_mirror(grid)} for grid in grids]
        production = gen.lesson_identifiable(pairs[:5], pairs[5])
        rotations = [gen.lesson_identifiable(pairs[:qi]+pairs[qi+1:], pairs[qi]) for qi in range(6)]
        lessons.append({'seed': seed, 'difficulty': band, 'start': start, 'demo_count': 5, 'production_reasons': production, 'rotation_reasons': rotations})
assert all(not lesson['production_reasons'] and all(not reasons for reasons in lesson['rotation_reasons']) for lesson in lessons)

(HERE/'input.json').write_text(json.dumps(inputs, indent=2)+'\n')
(HERE/'rival.json').write_text(json.dumps({'name': 'copy_input', 'input_index': 0, 'output': gen.LESSON_COMPETITORS['copy_input'](witness)}, indent=2)+'\n')
report = {'task_id': TASK, 'generator_sha256': sha(SOURCE.read_bytes()), 'canonical_rule_sha256': sha(rule.encode()), 'generator_rule_pin': gen.RULE_HASH, 'canonical_pair_count': len(canonical), 'canonical_validator_errors': [gen.self_check(p['input']) for p in canonical], 'canonical_mirror_matches': [gen.rule_mirror(p['input']) == p['output'] for p in canonical], 'canonical_shortcuts': canonical_results, 'input_records': records, 'mirror_outputs': [gen.rule_mirror(grid) for grid in inputs], 'lesson_check_authority': 'Python mirror only; separate Racket report labels retained 19 inputs', 'lesson_policy': '5 demos followed by 1 query; starts 0..5; each 6-pair lesson also holds out every query position', 'lesson_count': len(lessons), 'rotated_lesson_count': len(lessons)*6, 'lessons': lessons, 'witness_semantic_observables': {'scene_profile': gen.semantic_observables(witness)['scene_profile'], 'spans': [p['span'] for p in gen.semantic_observables(witness)['pairs']], 'clear_bridge_changes_grid': gen.SEMANTIC_WITNESSES['clear_bridge_changes_grid'](witness)}, 'source_unchanged': True}
(HERE/'probe.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps({'inputs': len(inputs), 'generated_inputs': len(inputs)-1, 'canonical_pairs': len(canonical), 'production_lessons': len(lessons), 'rotated_lessons': len(lessons)*6, 'witness_validator_errors': gen.self_check(witness), 'witness_is_identity': gen.rule_mirror(witness) == witness}))
