"""One protected-Racket count-boundary check following independent review."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

from reviewer_support import find_root

root = find_root(__file__)
path = root / 'generators/17ea562973ac/workspace/parametric/verify.py'
spec = importlib.util.spec_from_file_location('missing_box_boundary_verifier', path)
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)
adapter = verify._load_adapter()
grid = [[0] * 30 for _ in range(30)]
outer = [(0, 0), (29, 29)]
# Span the full inner 28x28 box as well as exercising maximum admitted count.
inner = [(1, 1), (28, 28), (1, 28), (28, 1)]
pool = [(r, c) for r in range(1, 29) for c in range(1, 29) if (r, c) not in inner]
for r, c in outer + inner + pool[:154]:
    grid[r][c] = 7
assert len(adapter.analyze(grid)['cells']) == 160
assert adapter.validate_input(grid) == []
over = deepcopy(grid)
over[pool[154][0]][pool[154][1]] = 7
assert len(adapter.analyze(over)['cells']) == 161
assert adapter.validate_input(over) == ['prototype needs 4..160 markers']
evaluator = verify.RacketEvaluator()
try:
    labels = []
    for depth in (0, 1):
        settings = {'peel_depth': depth}
        program = adapter.program(settings)
        output = evaluator.apply(program, grid)
        assert output == adapter.mirror(grid, settings)
        labels.append({'settings': settings, 'program': program, 'output': output})
    record = {'status': 'passed', 'source_hashes': verify._source_snapshot()[0],
              'scope': 'Literal 160-marker upper boundary, both settings; 161-marker rejection.',
              'input': grid, 'labels': labels, 'racket': evaluator.identity,
              'racket_evaluations': evaluator.evaluations,
              'over_limit_errors': adapter.validate_input(over)}
finally:
    evaluator.close()
destination = Path(__file__).with_name('count-boundary.json')
with destination.open('x') as stream:
    json.dump(record, stream, sort_keys=True)
    stream.write('\n')
print(json.dumps({'status': 'passed', 'racket_evaluations': record['racket_evaluations'],
                  'markers': 160, 'over_limit_rejected': 161}))
