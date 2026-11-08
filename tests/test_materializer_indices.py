"""Actual accepted sample positions must survive rejection and pair dedup."""
import json
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import pytest


@pytest.mark.parametrize('mode', ['runner', 'public_worker'])
def test_materializer_keeps_actual_indices_after_generator_identity_and_duplicate_rejections(tmp_path, mode):
    source = Path(__file__).resolve().parents[1] / 'shared/runtime'
    code = '''
import json
from types import SimpleNamespace
from puzzle_generators import runner
def generate(*, seed, sample_index, **kwargs):
    if sample_index == 10:
        raise ValueError('deliberate fixture rejection')
    return [[{11: 0, 12: 1, 13: 1, 14: 3}[sample_index]]]
runner._apply_rule = lambda bridge, name, grid: [[0]] if grid == [[0]] else [[grid[0][0]+1]]
bundle = SimpleNamespace(kind='per_puzzle', generator_module=SimpleNamespace(generate=generate, VERSION='fixture'),
    rule_task_id='fixture', rule_file='fixture.rkt', rule_source='fixture', rule_callable_text='unused', allow_identity_output=False)
if MODE == 'runner':
    instance = runner.run_one('fixture', 42, 10, n_train=1, n_test=1,
        bundle=bundle, bridge=object(), fn_name='fixture')
else:
    from arcpuzzles import worker
    kept = []
    worker._generate_episodes({'task_id':'fixture','kind':'per_puzzle','count':1,'seed':42,
        'sample_index':10,'n_train':1,'n_test':1,'difficulty':'medium'},
        bundle.generator_module, runner, runner.is_well_formed, kept.append, {'bundle':bundle},
        lambda: (object(), 'fixture'), lambda: None)
    instance = kept[0]
print(json.dumps(instance))
'''
    result = subprocess.run([sys.executable, '-B', '-c', 'MODE = '+repr(mode)+'\n'+code], cwd=tmp_path,
                            env={**os.environ, 'PYTHONPATH': os.pathsep.join((str(source), str(source.parents[1]/'src')))},
                            check=True, capture_output=True, text=True, timeout=15)
    instance = json.loads(result.stdout)
    assert instance['train'] == [{'input': [[1]], 'output': [[2]]}]
    assert instance['test'] == [{'input': [[3]], 'output': [[4]]}]
    sampling = instance['sampling']
    assert sampling['requested_start'] == 10
    assert sampling['next_sample_index'] == 15
    assert sampling['attempted_pairs'] == 5
    assert [(p['split'], p['pair_index'], p['sample_index']) for p in sampling['accepted_pairs']] == [
        ('train', 0, 12), ('test', 0, 14)]
    assert [r['sample_index'] for r in sampling['rejections']] == [10, 11, 13]
    assert sampling['rejections'][1]['reason'] == 'validate.output_equals_input'
    assert sampling['accepted_pairs'][0]['input_sha256'] == hashlib.sha256(b'[[1]]').hexdigest()
