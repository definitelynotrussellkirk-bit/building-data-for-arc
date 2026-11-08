"""One hand input separates first matching line from nearest matching line."""
from pathlib import Path
import hashlib
import json
import types

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs

ROOT = Path.cwd()
TASK = '77e696585932'
OUT = Path(__file__).resolve().parent
SOURCE = ROOT / 'generators' / TASK / 'generator.py'
SHA = 'be2ae4aed1cf23cb1fa18aa1223202c215df7a8e865277e308ec16b4a6dbc1b9'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SHA
gen = types.ModuleType('audit_nearest_full_line_subject')
gen.__file__ = str(SOURCE)
exec(compile(SOURCE.read_bytes(), str(SOURCE), 'exec'), gen.__dict__)

def first_matching_line(grid):
    """Choose the first matching row/column; compare only those two distances."""
    h, w = len(grid), len(grid[0])
    rows = [(r, grid[r][0]) for r in range(h) if grid[r][0] != 0 and len(set(grid[r])) == 1]
    cols = [(c, grid[0][c]) for c in range(w)
            if grid[0][c] != 0 and len({grid[r][c] for r in range(h)}) == 1]
    row_ids, col_ids = {r for r, _ in rows}, {c for c, _ in cols}
    output = [[grid[r][c] if r in row_ids or c in col_ids else 0 for c in range(w)]
              for r in range(h)]
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if not color or r in row_ids or c in col_ids:
                continue
            matching_rows = [rr for rr, value in rows if value == color]
            matching_cols = [cc for cc, value in cols if value == color]
            if not matching_rows and not matching_cols:
                continue
            rr = matching_rows[0] if matching_rows else -1
            cc = matching_cols[0] if matching_cols else -1
            dr = abs(r - rr) if rr != -1 else 9999
            dc = abs(c - cc) if cc != -1 else 9999
            dest = (rr - 1 if r < rr else rr + 1, c) if dr <= dc else (
                r, cc - 1 if c < cc else cc + 1)
            output[dest[0]][dest[1]] = color
    return output

seed, band, indices = 4107, 'medium', [2, 3, 4, 5]
generated = [gen.generate(seed, i, difficulty=band) for i in indices]
canonical = canonical_pairs(TASK, root=ROOT)
hand = [[0] * 12 for _ in range(12)]
hand[2] = [2] * 12
hand[8] = [2] * 12
hand[0][3] = 2
hand[10][4] = 2
hand[0][10] = 3
assert gen.self_check(hand) == gen.strict_canonical_like(hand) == []
grids = generated + [pair['input'] for pair in canonical] + [hand]
reference = Catalog(ROOT).apply(TASK, grids, allow_unapproved=True)
assert reference['executed_rule_hash'] == gen.RULE_HASH == '315cb8671701'
assert reference['rule_hash_matches_catalog']
labels = [result['output'] for result in reference['results']]
assert all(label is not None for label in labels)
predictions = [first_matching_line(grid) for grid in grids]
assert all(prediction == label for prediction, label in zip(predictions[:-1], labels[:-1]))
assert all(pair['output'] == label for pair, label in zip(canonical, labels[4:-1]))
assert predictions[-1] != labels[-1]
assert gen._expected_output(hand) == labels[-1]
assert labels[-1][9][4] == 2 and labels[-1][3][4] == 0
assert predictions[-1][9][4] == 0 and predictions[-1][3][4] == 2
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SHA

evidence = {
    'task_id': TASK, 'source_sha256': SHA, 'rule_hash': gen.RULE_HASH,
    'classification': 'reproduced_distribution_shortcut',
    'finding': 'Choose first matching line rather than nearest matching line: this rival fits all four canonical pairs and all generated teaching profiles, but changes a validator-accepted two-parallel-same-color-row scene.',
    'rival_definition': 'Use the first matching full row and first matching full column in scan order, compare their distances with row winning a tie, and move one cell outside that chosen line.',
    'generated_parameters': {'seed': seed, 'difficulty': band, 'sample_indices': indices, 'overrides': {}},
    'generated_samples': [{'sample_index': i, 'input': grid, 'racket_output': label,
                           'rival_prediction': prediction, 'profile': gen.observe_overrides(grid)['scene_profile']}
                          for i, grid, label, prediction in zip(indices, generated, labels, predictions)],
    'canonical_pairs': [{**pair, 'racket_output': label, 'rival_prediction': prediction}
                        for pair, label, prediction in zip(canonical, labels[4:-1], predictions[4:-1])],
    'counterexample': {'input': hand, 'racket_output': labels[-1],
                       'rival_prediction': predictions[-1], 'self_check': [],
                       'strict_canonical_like': [], 'zero_based_full_rows': [[2, 2], [8, 2]],
                       'matching_sources': [[0, 3, 2], [10, 4, 2]],
                       'distractor_source': [0, 10, 3],
                       'decisive_move': {'source': [10, 4], 'nearest_matching_row': 8,
                                         'racket_destination': [9, 4], 'rival_destination': [3, 4]}},
    'structural_reason': 'Generated rows use two distinct line colors, columns use three distinct line colors, and a cross contains only one row and one column. Therefore each generated color has at most one matching line per orientation; first and nearest per orientation coincide for every generated scene, not merely these four seeds.',
    'reference_receipt': {k: v for k, v in reference.items() if k != 'results'},
    'bounded_scope': {'generated_draws': 4, 'canonical_pairs': 4, 'hand_inputs': 1, 'racket_inputs': 9},
    'limits': ['No wrong generated labels found.',
               'The hand scene passes both public validators but is outside the three narrow scene_profile layouts and cannot be requested through the current axes.',
               'This is a coverage shortcut in the claimed nearest-line semantics, not proof of failure in the original three-demo production orientation.'],
    'command_receipt': 'checks/audit/77e696585932/shortcut-command/receipt.json',
}
(OUT / 'shortcut-evidence.json').write_text(json.dumps(evidence, indent=2) + '\n')
print(json.dumps({k: evidence[k] for k in ('task_id', 'classification', 'source_sha256',
                                         'rule_hash', 'bounded_scope')}, indent=2))
print('Hand pixel (10,4): Racket nearest row8 -> (9,4); first-line rival row2 -> (3,4).')
