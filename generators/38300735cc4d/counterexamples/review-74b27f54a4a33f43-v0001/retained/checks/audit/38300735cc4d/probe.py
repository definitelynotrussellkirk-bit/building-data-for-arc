from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
from reviewer_support import canonical_pairs, canonical_path, find_root

TASK = '38300735cc4d'
HERE = Path(__file__).resolve().parent
ROOT = find_root(Path.cwd())
SOURCE = ROOT / 'generators' / TASK / 'generator.py'
spec = importlib.util.spec_from_file_location('audit_target', SOURCE)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
sha = lambda data: hashlib.sha256(data).hexdigest()

def prepare():
    canonical = canonical_pairs(TASK, root=ROOT)
    row = next(json.loads(line) for line in canonical_path(ROOT).read_text().splitlines() if json.loads(line).get('task_id') == TASK)
    inputs = [p['input'] for p in canonical]
    records = [{'kind': 'canonical', 'split': p['split'], 'pair_index': p['pair_index'], 'variant': p['variant']} for p in canonical]
    shortcuts = []
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        matches = [rival(p['input']) == p['output'] for p in canonical]
        shortcuts.append({'name': name, 'matches': matches})
    assert all(all(r['matches']) for r in shortcuts)
    for bi, band in enumerate(('easy', 'medium', 'hard')):
        for index in range(11):
            seed = 881600 + bi
            grid = gen.generate(seed, index, difficulty=band)
            assert gen.self_check(grid) == []
            inputs.append(grid)
            records.append({'kind': 'generated', 'seed': seed, 'sample_index': index, 'difficulty': band, 'overrides': {}, 'observed_axes': gen.observe_overrides(grid), 'self_check': [], 'documented_generated_domain': True})
    witness = [[0]*6 for _ in range(6)]
    witness[0][0] = witness[0][1] = 2
    witness[2][3] = witness[3][3] = 3
    assert gen.self_check(witness) == []
    inputs.append(witness)
    records.append({'kind': 'inherited_witness_reconstructed', 'seed': None, 'sample_index': None, 'overrides': None, 'self_check': [], 'documented_generated_domain': False, 'reason': 'Span-one pairs cannot be generated; generate requires span >=2 and nonidentity.'})
    report = {'task_id': TASK, 'generator_sha256': sha(SOURCE.read_bytes()), 'canonical_raw_rule_sha256': sha(row['program_solution'].encode()), 'normalized_rule_id': gen.RULE_HASH, 'canonical_pair_count': len(canonical), 'canonical_shortcuts': shortcuts, 'inputs': records, 'mirror_outputs': [gen.rule_mirror(g) for g in inputs]}
    (HERE/'input.json').write_text(json.dumps(inputs)+'\n')
    (HERE/'prepared.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'inputs': len(inputs), 'generated': 33, 'canonical': len(canonical), 'witness': 1}))

def verify():
    report = json.loads((HERE/'prepared.json').read_text())
    applied = json.loads((HERE/'racket.json').read_text())
    assert sha(SOURCE.read_bytes()) == report['generator_sha256'] == applied['generator_sha256']
    assert applied['executed_rule_hash'] == gen.RULE_HASH
    results = applied['results']
    assert len(results) == 37
    assert all(r['valid_output'] and not r['error'] for r in results)
    assert [r['output'] for r in results] == report['mirror_outputs']
    by_band_index = {(rec['difficulty'], rec['sample_index']): result for rec, result in zip(report['inputs'], results) if rec['kind'] == 'generated'}
    lessons = []
    for bi, band in enumerate(('easy', 'medium', 'hard')):
        for start in range(6):
            pairs = [{'input': by_band_index[(band, i)]['input'], 'output': by_band_index[(band, i)]['output']} for i in range(start, start+6)]
            holds = []
            for qi in range(6):
                demos = pairs[:qi] + pairs[qi+1:]
                reasons = gen.lesson_identifiable(demos, pairs[qi])
                assert not reasons, (band, start, qi, reasons)
                rivals = {name: [i for i, pair in enumerate(pairs) if i != qi and rival(pair['input']) != pair['output']] for name, rival in gen.LESSON_COMPETITORS.items()}
                assert all(rivals.values())
                holds.append({'query_position': qi, 'reasons': reasons, 'refuting_pair_indices': rivals})
            lessons.append({'difficulty': band, 'seed': 881600+bi, 'start': start, 'production_query_position': 5, 'demo_count': 5, 'holds': holds})
    axes = []
    for bi, band in enumerate(('easy', 'medium', 'hard')):
        for h in (6, 12):
            for w in (6, 12):
                for profile in gen.SCENE_PROFILES:
                    overrides = {'grid_h': h, 'grid_w': w, 'scene_profile': profile}
                    index = len(axes)
                    grid = gen.generate(882000+index, index, difficulty=band, **overrides)
                    observed = gen.observe_overrides(grid)
                    assert observed == overrides and gen.self_check(grid) == []
                    axes.append({'seed': 882000+index, 'sample_index': index, 'difficulty': band, 'overrides': overrides, 'observed': observed, 'self_check': []})
    witness = results[-1]
    rival_output = gen.LESSON_COMPETITORS['copy_input'](witness['input'])
    differing_cells = [[r, c] for r, row in enumerate(witness['output']) for c, value in enumerate(row) if rival_output[r][c] != value]
    assert not differing_cells and witness['output'] == witness['input']
    evidence = {'task_id': TASK, 'generator_sha256': applied['generator_sha256'], 'canonical_raw_rule_sha256': report['canonical_raw_rule_sha256'], 'executable_callable_sha256': applied['rule_text_sha256'], 'normalized_rule_id': gen.RULE_HASH, 'seed': None, 'sample_index': None, 'overrides': None, 'input_index': 36, 'input': witness['input'], 'actual_racket_output': witness['output'], 'rival_name': 'copy_input', 'rival_output': rival_output, 'differing_cells': differing_cells, 'self_check': gen.self_check(witness['input']), 'documented_generated_domain': False, 'semantic_witness': gen.SEMANTIC_WITNESSES['clear_bridge_changes_grid'](witness['input']), 'cwd': 'packet_root', 'argv': ['python3', 'run_with_racket.py', 'python3', '-m', 'arcpuzzles', 'apply', TASK, '--input', '../checks/audit/'+TASK+'/input.json', '--out', '../checks/audit/'+TASK+'/racket.json']}
    (HERE/'counterexample.json').write_text(json.dumps(evidence, indent=2)+'\n')
    final = {'task_id': TASK, 'generator_sha256': applied['generator_sha256'], 'canonical_raw_rule_sha256': report['canonical_raw_rule_sha256'], 'executable_callable_sha256': applied['rule_text_sha256'], 'canonical_pairs': 3, 'canonical_shortcuts_fitted': 5, 'racket_valid_outputs': 37, 'racket_mirror_matches': 37, 'generated_unique_inputs': len({r['input_sha256'] for r in results[3:36]}), 'production_lessons_passed': 18, 'production_lessons_total': 18, 'rotation_lessons_passed': 108, 'rotation_lessons_total': 108, 'authority': 'fresh selected Racket labels for all 33 generated grids; Python competitors and lesson_identifiable', 'lesson_policy': 'five demonstrations then one query; cyclic starts 0..5 at fixed seed per band; all six query positions', 'lessons': lessons, 'axis_checks': axes, 'axis_checks_authority': 'input realization/self_check only; these 72 extra grids were not independently Racket-labelled', 'inherited_domain_witness_reproduced': True, 'source_unchanged': True}
    (HERE/'verification.json').write_text(json.dumps(final, indent=2)+'\n')
    print(json.dumps({key: final[key] for key in ('racket_valid_outputs', 'racket_mirror_matches', 'generated_unique_inputs', 'production_lessons_passed', 'rotation_lessons_passed')}))

if __name__ == '__main__':
    import sys
    {'prepare': prepare, 'verify': verify}[sys.argv[1]]()
