"""Findings-only audit, pinned to the assigned source; labels execute Racket."""
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

WORK = Path(__file__).resolve().parents[3]
ROOT = WORK / 'repo'
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'shared/runtime'))
from reviewer_support import canonical_pairs, canonical_path, load_selected_generator
from arc_repl.racket_bridge import RacketBridge

TASK = '56bcb1d01e53'
EXPECTED = '7c7978cf0cd1f1f3842837e34539120bfb5c65a880b21053c1da05485437612d'


def sha(value):
    if not isinstance(value, bytes):
        value = json.dumps(value, sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(value).hexdigest()


def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def execute(bridge, program, grid):
    p = program.strip()
    assert p.startswith('(rule! (lambda (g)') and p.endswith(')')
    body = p[len('(rule!'):-1].strip()
    literal = "'(" + ' '.join('(' + ' '.join(map(str, row)) + ')' for row in grid) + ')'
    return bridge.eval_text(f'({body} {literal})')


def differences(first, second):
    return [[r, c, first[r][c], second[r][c]] for r in range(len(first))
            for c in range(len(first[0])) if first[r][c] != second[r][c]]


def main():
    mod, path, source_sha = load_selected_generator(TASK, root=ROOT)
    assert source_sha == EXPECTED
    programs = set()
    for line in canonical_path(ROOT).open():
        row = json.loads(line)
        if row.get('task_id') == TASK:
            programs.add(row['program_solution'])
    assert len(programs) == 1
    program = programs.pop()
    assert hashlib.sha256(' '.join(program.split()).encode()).hexdigest()[:12] == mod.RULE_HASH
    # This rival keeps the cardinal-center branch and omits only the >=7 diagonal branch.
    def cardinal_only(grid):
        output = mod._apply_rule(grid, center_fill=False)
        bg = mod._background(grid)
        for cluster in mod._clusters(grid, bg):
            rs, cs = [r for r, _ in cluster], [c for _, c in cluster]
            bh, bw = max(rs) - min(rs) + 1, max(cs) - min(cs) + 1
            if bh != bw or bh % 2 == 0:
                continue
            cr, cc = (min(rs) + max(rs)) // 2, (min(cs) + max(cs)) // 2
            color = grid[cluster[0][0]][cluster[0][1]]
            if output[cr][cc] == bg and all(
                min(rs) <= cr + dr <= max(rs) and min(cs) <= cc + dc <= max(cs)
                and output[cr + dr][cc + dc] == color for dr, dc in mod._DIR4
            ):
                output[cr][cc] = color
        return output

    production = []
    for band in (None, 'easy', 'medium', 'hard'):
        for index in range(10):
            grid = mod.generate(9200 + index, index, difficulty=band)
            facts = mod._grid_facts(grid)
            production.append({'seed': 9200 + index, 'sample_index': index, 'difficulty': band,
                               'input_sha256': sha(grid), 'self_check': facts['errors'],
                               'shapes': [[f['height'], f['width']] for f in facts['cluster_facts']],
                               'cardinal_only_matches_mirror': cardinal_only(grid) == mod.rule_mirror(grid)})
    canonical = []
    with RacketBridge() as bridge:
        for pair in canonical_pairs(TASK, root=ROOT, labeled_only=True):
            grid = pair['input']
            output = execute(bridge, program, grid)
            rival_output = cardinal_only(grid)
            canonical.append({'variant': pair['variant'], 'split': pair['split'], 'pair_index': pair['pair_index'],
                              'input': grid, 'output': output, 'provided_label_matches_racket': output == pair['output'],
                              'self_check': mod.self_check(grid), 'rival_output': rival_output,
                              'rival_differences': differences(output, rival_output),
                              'shapes': [[f['height'], f['width']] for f in mod._grid_facts(grid)['cluster_facts']]})
        # Existing retained zero-background authority counterexample, independently rerun.
        previous = json.loads((ROOT / 'generators' / TASK / 'counterexamples/background-zero-authority-sentinel.json').read_text())
        write('existing-zero-counterexample-structure.json', {'keys': list(previous), 'source_file_sha256': sha((ROOT / 'generators' / TASK / 'counterexamples/background-zero-authority-sentinel.json').read_bytes())})
        # Swap color roles in a current production input, preserving component geometry and strict majority.
        current = mod.generate(17, 1, background=4)
        zero = [[0 if v == 4 else 4 if v == 0 else v for v in row] for row in current]
        zero_output = execute(bridge, program, zero)
        zero_mirror = mod.rule_mirror(zero)
        zero_evidence = {'input': zero, 'output': zero_output, 'mirror_output': zero_mirror,
                         'source_generation': {'seed': 17, 'sample_index': 1, 'background': 4},
                         'mutation': 'Swap colors 0 and 4 in a lawful emitted input.',
                         'self_check': mod.self_check(zero), 'observe_overrides': mod.observe_overrides(zero),
                         'differences': differences(zero_output, zero_mirror)}
        # One retained, entirely real-reference four-pair lesson for production shortcut survival.
        pairs = []
        for index in range(4):
            grid = mod.generate(11, index)
            output = execute(bridge, program, grid)
            pairs.append({'seed': 11, 'sample_index': index, 'input': grid, 'output': output,
                          'mirror_matches_racket': mod.rule_mirror(grid) == output,
                          'cardinal_only_output': cardinal_only(grid)})
        rotations = []
        for query_index in range(4):
            demos = [p for i, p in enumerate(pairs) if i != query_index]
            rotations.append({'query_position': query_index,
                              'cardinal_only_fits_demos': all(p['cardinal_only_output'] == p['output'] for p in demos),
                              'cardinal_only_fits_query': pairs[query_index]['cardinal_only_output'] == pairs[query_index]['output'],
                              'declared_lesson_hook': mod.lesson_identifiable(demos, pairs[query_index])})
        runtime = bridge.runtime_identity
    report = {'schema': 'arc-findings-only-audit-v1', 'task_id': TASK, 'generator_sha256': source_sha,
              'rule_hash': mod.RULE_HASH, 'program_sha256': sha(program.encode()), 'canonical_program': program,
              'probe_sha256': sha(Path(__file__).read_bytes()), 'python': sys.executable, 'argv': sys.argv,
              'cwd': str(Path.cwd()), 'racket_runtime': runtime, 'reference_applications': 10,
              'canonical': canonical, 'production_census': production, 'retained_production_pairs': pairs,
              'rotations': rotations, 'zero_background_witness': zero_evidence,
              'source_unchanged': sha(path.read_bytes()) == source_sha}
    write('audit-evidence.json', report)
    write('production-challenge.json', {'train': [{'input': p['input'], 'output': p['output']} for p in pairs[:3]],
                                         'test': [{'input': pairs[3]['input']}]})
    print(json.dumps({'generator_sha256': source_sha, 'source_unchanged': report['source_unchanged'],
                      'canonical_labels_match_racket': all(c['provided_label_matches_racket'] for c in canonical),
                      'canonical_cardinal_only_differences': [[c['split'], c['pair_index'], c['rival_differences']] for c in canonical],
                      'production_cardinal_only_matches': sum(p['cardinal_only_matches_mirror'] for p in production),
                      'production_cases': len(production), 'rotations': rotations,
                      'zero_self_check': zero_evidence['self_check'], 'zero_differences': zero_evidence['differences'],
                      'reference_applications': 10}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
