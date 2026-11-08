"""Passing semantic claims retain bounded, replayable evidence, not just counts."""
import hashlib
import importlib.util
import json
import shutil
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def gate(monkeypatch):
    # Load the real normalizer and seed reader without their staged scripts alias.
    package = ModuleType('scripts'); package.__path__ = []
    monkeypatch.setitem(sys.modules, 'scripts', package)
    for name, file in [('coder_synth_verify', 'coder_synth_verify.py'),
                       ('canonical_profile_gate', 'canonical_profile_gate.py'),
                       ('generator_semantic_gate', 'generator_semantic_gate.py')]:
        spec = importlib.util.spec_from_file_location(
            'scripts.' + name, ROOT / 'shared/tools' / file)
        module = importlib.util.module_from_spec(spec)
        monkeypatch.setitem(sys.modules, 'scripts.' + name, module)
        spec.loader.exec_module(module)
    return sys.modules['scripts.generator_semantic_gate']


class Oracle:
    """Only the external Racket operation is substituted in these CPU tests."""
    ready = True
    error = None

    def __init__(self, apply_fn=None):
        self.bundle = SimpleNamespace(rule_task_id='abc', rule_source='(lambda (g) g)',
                                      rule_callable_text='(lambda (g) g)')
        self.apply_fn = apply_fn or (lambda grid: (grid, None))
        self.calls = 0

    def apply(self, grid):
        self.calls += 1
        return self.apply_fn(grid)


def source(tmp_path):
    path = tmp_path / 'generator.py'
    path.write_bytes(b'# pinned synthetic generator\n')
    return SimpleNamespace(__file__=str(path), self_check=lambda grid: [])


def run(gate, gen, oracle, rivals, queue=None):
    return gate._verify_rival_claims(
        {'always': queue or [('easy', 17, 5, [[1]]), ('hard', 18, 6, [[2]])]},
        rivals=rivals, witness_rivals={'always': list(rivals)},
        oracle_factory=lambda: oracle, task_id='abc', generator=gen)['always']


def test_first_disagreement_per_pair_is_retained_without_extra_oracle_calls(gate, tmp_path):
    gen = source(tmp_path); oracle = Oracle()
    result = run(gate, gen, oracle, {'erase': lambda grid: [[0]],
                                   'erase_two': lambda grid: [[0 if grid[0][0] == 2 else 1]]})
    examples = result['witness_examples']
    assert set(examples) == {'erase', 'erase_two'}
    first = examples['erase']
    assert first['task_id'] == 'abc' and first['witness'] == 'always' and first['rival'] == 'erase'
    assert first['recipe'] == {'seed': 17, 'sample_index': 5, 'difficulty': 'easy', 'overrides': {}}
    assert first['input'] == [[1]] and first['authoritative_output'] == [[1]]
    assert first['rival_output'] == [[0]]
    assert examples['erase_two']['recipe']['seed'] == 18
    assert first['source_binding']['generator_sha256'] == hashlib.sha256(
        b'# pinned synthetic generator\n').hexdigest()
    assert first['source_binding']['rule_source_sha256'] == hashlib.sha256(
        b'(lambda (g) g)').hexdigest()
    assert first['validation']['self_check']['status'] == 'passed'
    assert result['claim_holds'] == result['checked'] == 2 and oracle.calls == 2
    assert result['per_rival_disagreements'] == {'erase': 2, 'erase_two': 1}
    assert result['witness_selection'] == 'first_checked_disagreement_per_pair'
    assert json.loads(json.dumps(result))['witness_examples'] == examples


def test_agreeing_and_errored_rivals_do_not_gain_a_positive_witness(gate, tmp_path):
    def broken(grid):
        raise ValueError('broken rival')
    result = run(gate, source(tmp_path), Oracle(), {'same': lambda grid: grid, 'broken': broken})
    assert result['witness_examples'] == {}
    assert result['claim_holds'] == 0 and result['claim_violated'] == 2
    assert result['rival_errors'] == 2


def test_oracle_failure_never_uses_a_guessed_output(gate, tmp_path):
    result = run(gate, source(tmp_path), Oracle(lambda grid: (None, 'rule failed')),
                 {'erase': lambda grid: [[0]]})
    assert result['witness_examples'] == {} and result['oracle_errors'] == 2


def test_returned_mutable_rival_grid_cannot_rewrite_a_previous_witness(gate, tmp_path):
    reused = [[0]]
    def rival(grid):
        reused[0][0] = 0 if grid[0][0] == 1 else 3
        return reused
    result = run(gate, source(tmp_path), Oracle(), {'mutable': rival})
    assert result['witness_examples']['mutable']['rival_output'] == [[0]]


def test_missing_source_and_validator_are_explicit(gate):
    result = run(gate, SimpleNamespace(), Oracle(), {'erase': lambda grid: [[0]]})
    example = result['witness_examples']['erase']
    assert example['source_binding']['generator_sha256'] is None
    assert example['source_binding']['status'] == 'incomplete'
    assert example['validation']['self_check']['status'] == 'not_declared'


@pytest.mark.parametrize('bad', [None, [[True]], [[1, 2], [1]], [[0] * 31], ['0' * 31]])
def test_non_arc_rival_output_is_not_retained_as_grid_evidence(gate, tmp_path, bad):
    result = run(gate, source(tmp_path), Oracle(), {'bad': lambda grid: bad})
    assert result['witness_examples'] == {}
    assert result['witness_retention_errors']


def test_census_threads_task_source_and_default_recipe(gate, tmp_path):
    gen = source(tmp_path)
    gen.generate = lambda seed, index, difficulty=None: [[1]]
    scored = gate.run_census('abc', gen, per_band=1, strict_hook=None,
        witnesses={'always': lambda grid: True}, rivals={'erase': lambda grid: [[0]]},
        witness_rivals={'always': ['erase']}, oracle_factory=Oracle)
    example = scored['witnesses']['always']['rival_claim']['witness_examples']['erase']
    assert example['task_id'] == 'abc'
    assert example['source_binding']['status'] == 'bound'
    assert example['recipe']['difficulty'] == 'easy' and example['recipe']['overrides'] == {}


@pytest.mark.parametrize('check, status', [
    (lambda grid: ['outside grammar'], 'failed'),
    (lambda grid: 1 / 0, 'error'),
])
def test_validator_failure_remains_visible_in_a_disagreement(gate, tmp_path, check, status):
    gen = source(tmp_path); gen.self_check = check
    result = run(gate, gen, Oracle(), {'erase': lambda grid: [[0]]})
    assert result['witness_examples']['erase']['validation']['self_check']['status'] == status
    assert result['checked'] == result['claim_holds'] == 2


def test_complete_row_string_grids_are_normalized_without_clipping(gate, tmp_path):
    result = run(gate, source(tmp_path), Oracle(lambda grid: (['12'], None)),
                 {'erase': lambda grid: ['00']}, [('easy', 17, 5, ['12'])])
    example = result['witness_examples']['erase']
    assert example['input'] == example['authoritative_output'] == [[1, 2]]
    assert example['rival_output'] == [[0, 0]]


@pytest.mark.skipif(not shutil.which('racket'), reason='real reference runtime required')
def test_actual_racket_oracle_supplies_the_retained_output(gate, tmp_path, monkeypatch):
    from puzzle_generators import runner
    rule = '(lambda (g) (map (lambda (row) (map (lambda (cell) 2) row)) g))'
    gen = source(tmp_path)
    bundle = SimpleNamespace(rule_task_id='abc', rule_source=rule,
                             rule_callable_text=rule, generator_module=gen)
    monkeypatch.setattr(runner, '_load_bundle', lambda task_id: bundle)
    oracle = gate._RuleOracle('abc')
    try:
        assert oracle.ready, oracle.error
        result = run(gate, gen, oracle, {'identity': lambda grid: grid},
                     [('easy', 17, 5, [[1, 0]])])
        example = result['witness_examples']['identity']
        assert example['authoritative_output'] == [[2, 2]]
        assert example['rival_output'] == [[1, 0]]
        assert example['source_binding']['rule_callable_sha256'] == hashlib.sha256(
            rule.encode()).hexdigest()
    finally:
        oracle.close()
