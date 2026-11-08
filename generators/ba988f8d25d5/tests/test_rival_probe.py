"""Regressions for the reusable, source-bound rival probe."""
import copy
import importlib.util
from pathlib import Path


def probe():
    path = Path(__file__).parents[1] / 'workspace/rival_probe.py'
    assert path.exists(), 'reusable rival probe is not implemented'
    spec = importlib.util.spec_from_file_location('rival_probe', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_score_keeps_rival_errors_distinct_from_counterexamples():
    def broken(grid):
        raise ValueError('deliberate malformed rival')
    result = probe().score_rivals([[1, 2]], [[1, 2]], {
        'identity': lambda grid: grid,
        'reverse': lambda grid: [list(reversed(row)) for row in grid],
        'broken': broken,
    })
    assert result['identity']['status'] == 'agrees'
    assert result['reverse'] == {'status': 'disagrees', 'output': [[2, 1]]}
    assert result['broken']['status'] == 'error'
    assert 'ValueError' in result['broken']['error']


def test_score_isolates_mutating_rivals_and_retains_input():
    grid = [[1, 2]]
    before = copy.deepcopy(grid)
    def mutate(value):
        value[0][0] = 9
        return value
    result = probe().score_rivals(grid, grid, {'mutate': mutate, 'identity': lambda value: value})
    assert grid == before
    assert result['identity']['status'] == 'agrees'
    assert result['mutate']['status'] == 'disagrees'


def test_html_escapes_untrusted_names():
    report = {'schema': 'arcpuzzles-rival-probe-v1', 'task_id': '<script>x</script>',
              'source': {}, 'canonical': {}, 'bands': {}, 'first_counterexamples': {}, 'errors': []}
    text = probe().render_html(report)
    assert '<script>x</script>' not in text
    assert '&lt;script&gt;x&lt;/script&gt;' in text
