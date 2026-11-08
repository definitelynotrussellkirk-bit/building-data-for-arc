"""Original pairs are private fixtures, never generator inputs."""
import json
from pathlib import Path


HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]


def originals():
    raw = ROOT / 'shared' / 'data' / 'raw'
    parent = json.loads((raw / 'arc-agi_evaluation_challenges.json').read_text())['c7f57c3e']
    gold = json.loads((raw / 'arc-agi_evaluation_solutions.json').read_text())['c7f57c3e']
    normalize = lambda grid: [[int(v) for v in row] for row in grid]
    return [(normalize(pair['input']), normalize(pair['output'])) for pair in parent['train']] + [
        (normalize(pair['input']), normalize(answer)) for pair, answer in zip(parent['test'], gold)]


def test_general_reference_executes_every_original():
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator, _grid
    program = (HOME / 'reference.rkt').read_text()
    with _local_imports(ROOT / 'shared/runtime', HOME):
        apply, identity, bridge = _real_evaluator(ROOT / 'shared/runtime')
        assert identity['backend'] == 'racket' and identity['protected'] is True
        try:
            for grid, expected in originals():
                assert _grid(apply(program, grid)) == expected
        finally:
            bridge.close()
