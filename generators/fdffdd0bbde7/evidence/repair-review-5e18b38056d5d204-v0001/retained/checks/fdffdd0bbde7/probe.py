"""Bounded overlap-order learnability probe; labels replay in protected Racket."""
from pathlib import Path
import hashlib
import json

from reviewer_support import find_root, load_selected_generator, canonical_path
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

TASK = 'fdffdd0bbde7'
ROOT = find_root(__file__)
OUT = Path(__file__).resolve().parent
module, source_path, source_sha = load_selected_generator(TASK, root=ROOT)
programs = {r['program_solution'] for line in canonical_path(ROOT).read_text().splitlines()
            if (r := json.loads(line)).get('task_id') == TASK}
assert len(programs) == 1
canonical = programs.pop()
needle = '(in-list body-cells)'
assert canonical.count(needle) == 1
rival = canonical.replace(needle, '(in-list (reverse body-cells))')


def mirror(grid, reverse=False):
    """Candidate search only; independent Racket decides every retained label."""
    parsed = module._parse_grid(grid)
    offsets = {e['color']: e['offsets'] for e in parsed['entries']}
    out = [[0] * len(grid[0]) for _ in grid]
    cells = list(parsed['body'])
    if reverse:
        cells.reverse()
    for row, col, color in cells:
        for dr, dc in offsets[color]:
            rr, cc = row + dr, col + dc
            if 0 <= rr < len(grid) and 0 <= cc < len(grid[0]):
                out[rr][cc] = color
    return out


def execute(program, grid, bridge):
    literal = "'(" + ' '.join('(' + ' '.join(map(str, row)) + ')' for row in grid) + ')'
    return bridge.eval_text(f'({wrap_rule(program)} {literal})')


finding = None
checked = 0
for lesson in range(96):
    grids = [module.generate(271828, 4 * lesson + i) for i in range(4)]
    outputs = [mirror(grid) for grid in grids]
    alternatives = [mirror(grid, True) for grid in grids]
    checked += 1
    if all(a == b for a, b in zip(outputs[:3], alternatives[:3])) and outputs[3] != alternatives[3]:
        finding = (lesson, grids, outputs, alternatives)
        break

result = {'task_id': TASK, 'generator_sha256': source_sha, 'rule_hash': module.RULE_HASH,
          'canonical_program_sha256': hashlib.sha256(canonical.encode()).hexdigest(),
          'rival_program_sha256': hashlib.sha256(rival.encode()).hexdigest(),
          'probe': 'First body-seed stamp wins cross-color overlap, rather than last row-major seed.',
          'search_seed': 271828, 'max_lessons': 96, 'lessons_checked': checked,
          'rivals_tested': 1, 'demonstrations': 3, 'queries': 1,
          'limits': 'Bounded default sampler windows, one plausible overlap-priority rival. Not universal ambiguity, not an approval or training-admission decision.'}
if finding:
    lesson, grids, outputs, alternatives = finding
    with RacketBridge() as bridge:
        result['racket'] = bridge.runtime_identity
        assert result['racket']['backend'] == 'racket' and result['racket']['protected'] is True
        actual = [execute(canonical, grid, bridge) for grid in grids]
        counterfactual = [execute(rival, grid, bridge) for grid in grids]
    assert actual == outputs and counterfactual == alternatives
    assert actual[:3] == counterfactual[:3] and actual[3] != counterfactual[3]
    result.update(status='finding', lesson_index=lesson, sample_indices=list(range(4*lesson, 4*lesson+4)),
                  racket_evaluations=8, validator_errors=[module.self_check(g) for g in grids])
    result['query_differences'] = [
        {'row': row, 'col': col, 'canonical': actual[3][row][col],
         'rival': counterfactual[3][row][col]}
        for row in range(len(grids[3])) for col in range(len(grids[3][0]))
        if actual[3][row][col] != counterfactual[3][row][col]
    ]
    witness = {'generator_sha256': source_sha, 'rule_hash': module.RULE_HASH,
               'racket': result['racket'], 'seed': 271828,
               'sample_indices': result['sample_indices'],
               'program': canonical, 'counterfactual_program': rival,
               'train': [{'input': g, 'output': o, 'rival_output': r}
                         for g, o, r in zip(grids[:3], actual[:3], counterfactual[:3])],
               'test': [{'input': grids[3], 'output': actual[3], 'rival_output': counterfactual[3]}]}
    (OUT / 'witness.json').write_text(json.dumps(witness, sort_keys=True) + '\n')
    result['witness_path'] = 'checks/fdffdd0bbde7/witness.json'
else:
    result.update(status='no_finding', racket_evaluations=0,
                  note='No surviving demonstration-fit/query-disagreement candidate in bounded Python prefilter; no Racket-backed ambiguity claimed.')
assert hashlib.sha256(source_path.read_bytes()).hexdigest() == source_sha
(OUT / 'result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
print(json.dumps(result, sort_keys=True))
