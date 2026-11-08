"""Self-contained fault adapters; temporary artifacts must live outside checks."""
import json
import hashlib
from pathlib import Path
import subprocess
import sys

import pytest


PROBE = Path(__file__).with_name("probe_sampler.py")
ADAPTER = '''
FAULT = {fault!r}
CALLS = 0
def program(settings):
    return "(rule! " + str(settings['mode']) + ")"
def generate(seed, settings, demos, queries):
    global CALLS
    CALLS += 1
    if FAULT == 'mutating_helper':
        from pathlib import Path
        Path(__file__).with_name('native_family.py').write_text('changed during generation')
    def pair(split, index):
        value = (seed % 100000) * 1000 + split * 100 + index
        if FAULT == 'setting_rng':
            value += settings['mode'] * 10
        if FAULT == 'prefix':
            value += demos * 10 + queries
        if FAULT == 'nondeterminism':
            value += CALLS * 10
        grid = [[0] * 30 for _ in range(30)]
        digits = str(value).zfill(15)
        grid[0][:15] = [int(x) for x in digits]
        grid[15] = [3] * 30
        if FAULT == 'bool':
            grid[0][0] = True
        output = settings['mode']
        if FAULT == 'output_prefix':
            output = demos
        return {{'input': grid, 'output': [[output]]}}
    train = [pair(0, i) for i in range(demos)]
    test = [pair(1, i) for i in range(queries)]
    if FAULT == 'count':
        test = test[:-1]
    if FAULT == 'duplicate':
        test[0]['input'] = train[0]['input']
    if FAULT == 'program':
        return {{'train': train, 'test': test, 'program_solution': 'wrong'}}
    return {{'train': train, 'test': test, 'program_solution': program(settings)}}
'''


def run_probe(tmp_path, fault='', contract_changes=None, extra=()):
    assert PROBE.exists(), 'the reusable sampler probe has not been implemented'
    adapter = tmp_path / 'adapter.py'
    adapter.write_text(ADAPTER.format(fault=fault))
    contract = {'schema': 'arcpuzzles-parametric-adapter-v1',
                'parameters': {'mode': [1, 2]}, 'default': {'mode': 1},
                'limits': {'demos': [2, 6], 'queries': [1, 4]}}
    contract.update(contract_changes or {})
    contract_path = tmp_path / 'promotion.json'
    contract_path.write_text(json.dumps(contract))
    out = tmp_path / 'report.json'
    result = subprocess.run([sys.executable, str(PROBE), '--adapter', str(adapter),
                             '--contract', str(contract_path), '--out', str(out),
                             *extra], capture_output=True, text=True, timeout=30)
    assert out.exists(), result.stderr
    return result, json.loads(out.read_text())


def test_valid_settings_may_have_different_outputs_and_report_coverage(tmp_path):
    result, report = run_probe(tmp_path)
    assert result.returncode == 0, report['failures']
    assert report['status'] == 'passed'
    assert report['request_count'] == report['success_count'] == 16 * 2 * 3
    assert report['replay_count'] == 2
    assert report['failures'] == []
    assert report['requested']['seeds'][-1] == 2**63 - 1
    assert report['requested']['counts'] == [[2, 1], [3, 4], [6, 4]]
    assert len(report['adapter_sha256']) == len(report['contract_sha256']) == 64
    assert report['execution']['python_only'] is True
    assert report['execution']['racket_executed'] is False
    assert report['input_statistics']['max_height'] == 30
    assert report['input_statistics']['grids_30x30'] > 0
    assert report['input_statistics']['distinct_query_inputs'] == 16 * 4
    assert report['input_statistics']['distinct_inputs'] == 16 * 10
    assert len(result.stdout) < 1000


@pytest.mark.parametrize('fault,kind', [
    ('count', 'count_mismatch'), ('bool', 'invalid_grid'),
    ('duplicate', 'duplicate_inputs'), ('setting_rng', 'setting_input_mismatch'),
    ('prefix', 'count_prefix_drift'), ('nondeterminism', 'nondeterminism'),
    ('output_prefix', 'count_prefix_drift'),
    ('program', 'program_mismatch'),
])
def test_real_fault_adapter_is_rejected(tmp_path, fault, kind):
    result, report = run_probe(tmp_path, fault, extra=('--seed', '7'))
    assert result.returncode == 1
    assert report['status'] == 'failed'
    assert kind in {failure['kind'] for failure in report['failures']}
    assert report['success_count'] < report['request_count']


def test_repeatable_seed_flags_override_defaults(tmp_path):
    result, report = run_probe(tmp_path, extra=('--seed', '7', '--seed', str(2**62)))
    assert result.returncode == 0
    assert report['requested']['seeds'] == [7, 2**62]
    assert report['request_count'] == 12


def test_contract_cartesian_product_is_bounded_before_adapter_runs(tmp_path):
    result, report = run_probe(tmp_path, contract_changes={
        'parameters': {'mode': list(range(17))}})
    assert result.returncode == 1
    assert report['request_count'] == 0
    assert report['failures'][0]['kind'] == 'invalid_contract'


def test_exact_adapter_file_is_loaded_without_sibling_import_search(tmp_path):
    result, report = run_probe(tmp_path, extra=('--seed', '1'))
    assert result.returncode == 0
    (tmp_path / 'sibling_probe_private.py').write_text('sentinel = 1\n')
    adapter = tmp_path / 'adapter.py'
    adapter.write_text('import sibling_probe_private\n' + adapter.read_text())
    out = tmp_path / 'isolated-report.json'
    result = subprocess.run([sys.executable, str(PROBE), '--adapter', str(adapter),
                             '--contract', str(tmp_path / 'promotion.json'),
                             '--out', str(out), '--seed', '1'], capture_output=True,
                            text=True, timeout=30)
    report = json.loads(out.read_text())
    assert result.returncode == 1
    assert report['failures'][0]['kind'] == 'adapter_load_error'


def test_adjacent_sources_and_promotion_resources_are_inventoried(tmp_path):
    (tmp_path / 'native_family.py').write_text('VALUE = 1\n')
    (tmp_path / 'canonical.rkt').write_text('(rule! identity)\n')
    nested = tmp_path / 'nested'
    nested.mkdir()
    (nested / 'rules.json').write_text('{}\n')
    (tmp_path / 'palette.dat').write_bytes(b'palette-data')
    for excluded in ('evidence', 'public', 'examples', '__pycache__'):
        directory = tmp_path / excluded
        directory.mkdir()
        (directory / 'ignored.py').write_text('not inventoried')
    result, report = run_probe(tmp_path, contract_changes={'resources': ['palette.dat']},
                               extra=('--seed', '7'))
    assert result.returncode == 0
    inventory = report['adjacent_source_files']
    assert inventory['before'] == inventory['after']
    assert inventory['unchanged'] is True
    paths = {entry['path'] for entry in inventory['before']}
    assert paths == {'adapter.py', 'promotion.json', 'native_family.py',
                     'canonical.rkt', 'nested/rules.json', 'palette.dat'}
    helper = next(entry for entry in inventory['before'] if entry['path'] == 'native_family.py')
    assert helper['sha256'] == hashlib.sha256(b'VALUE = 1\n').hexdigest()
    assert 'not complete Python dependency authentication' in inventory['scope']


def test_helper_mutation_during_generation_is_detected(tmp_path):
    (tmp_path / 'native_family.py').write_text('original helper\n')
    result, report = run_probe(tmp_path, 'mutating_helper', extra=('--seed', '7'))
    assert result.returncode == 1
    assert report['status'] == 'failed'
    assert 'adjacent_source_changed' in {failure['kind'] for failure in report['failures']}
    inventory = report['adjacent_source_files']
    assert inventory['unchanged'] is False
    before = {entry['path']: entry['sha256'] for entry in inventory['before']}
    after = {entry['path']: entry['sha256'] for entry in inventory['after']}
    assert before['native_family.py'] != after['native_family.py']
