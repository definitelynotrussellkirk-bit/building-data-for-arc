"""Owner replay must reject fabricated causal labels before native acceptance."""
import copy
from pathlib import Path
import shutil
import pytest


@pytest.fixture
def runtime(library):
    if shutil.which('racket') is None:
        pytest.skip('Real Racket required')
    source = Path(__file__).resolve().parents[1]
    target = library / 'shared/runtime'
    target.mkdir(parents=True)
    shutil.copytree(source / 'shared/runtime/arc_repl', target / 'arc_repl',
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    (target / 'puzzle_generators').mkdir()
    for name in ('__init__.py', 'base.py', 'rule_wrap.py'):
        shutil.copy2(source / 'shared/runtime/puzzle_generators' / name, target / 'puzzle_generators' / name)
    (library / 'shared/tools').mkdir()
    shutil.copy2(source / 'shared/tools/comment_solutions.py', library / 'shared/tools/comment_solutions.py')
    return library


def case():
    return {'input': [[1, 2]], 'program': '(rule! (lambda (g) g))',
            'counterfactual_program': '(rule! (flip-lr g))', 'output': [[1, 2]],
            'counterfactual_output': [[2, 1]]}


@pytest.mark.parametrize('change', [
    {'input': [[1]], 'counterfactual_program': '(rule! (lambda (g) g))',
     'output': [[1]], 'counterfactual_output': [[2]]},
    {'input': [[1]], 'output': [[1]], 'counterfactual_output': [[2]]},
    {'input': [[1]], 'output': [[1]], 'counterfactual_output': [[1]]},
    {'counterfactual_output': [[True, 1]]},
    {'counterfactual_program': '(rule! (lambda (g) (/ 1 0)))'},
])
def test_false_labels_same_outputs_malformed_grids_and_execution_errors_rejected(runtime, change):
    from arcpuzzles.review_sequential_replay import replay_witness
    witness = {'cases': [dict(case(), **change)]}
    with pytest.raises(ValueError):
        replay_witness(runtime, witness)


def test_replays_both_programs_and_retains_actual_results(runtime):
    from arcpuzzles.review_sequential_replay import replay_witness
    result = replay_witness(runtime, {'cases': [case()]})
    assert result['status'] == 'owner_replayed'
    assert result['racket']['backend'] == 'racket' and result['racket']['protected'] is True
    assert result['evaluations'] == 2
    assert result['cases'][0]['output'] == [[1, 2]]
    assert result['cases'][0]['counterfactual_output'] == [[2, 1]]


def test_replay_timeout_fails_closed(runtime):
    from arcpuzzles.review_sequential_replay import replay_witness
    with pytest.raises(ValueError, match='timed_out.*true'):
        replay_witness(runtime, {'cases': [case()]}, timeout=0.001)


def test_common_replay_rejects_trailing_syntax_before_bridge(runtime, monkeypatch):
    from arcpuzzles.review_sequential_replay import _evaluate
    from arcpuzzles import parametric_worker
    def forbidden(*args):
        pytest.fail('Malformed complete expression must not start the Racket bridge')
    monkeypatch.setattr(parametric_worker, '_real_evaluator', forbidden)
    witness = {'cases': [case()]}
    witness['cases'][0]['counterfactual_program'] += ')'
    with pytest.raises(ValueError, match='one complete'):
        _evaluate(runtime, witness)
