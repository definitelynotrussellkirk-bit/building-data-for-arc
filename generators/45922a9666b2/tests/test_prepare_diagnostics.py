"""Synthetic-only regression for an optional shared preparation diagnostic proposal.

No live task source, canonical row, labels, rules, or generation are consulted.
Run PREPARE_DIAGNOSTICS_BASELINE=1 to demonstrate the unmodified reporter fails.
"""
import importlib.util
import json
import os
from pathlib import Path
import sys
import types

import pytest
from arcpuzzles import review_solve
from reviewer_support import find_root


def diagnostic_module():
    root = find_root(__file__)
    source = root / 'generators/45922a9666b2/workspace/diagnostics/prepare_diagnostics.py'
    spec = importlib.util.spec_from_file_location('task_prepare_diagnostics', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def isolated_solve():
    source = Path(review_solve.__file__).read_text()
    if not os.environ.get('PREPARE_DIAGNOSTICS_BASELINE'):
        source = diagnostic_module().instrument_source(source)
    module = types.ModuleType('arcpuzzles.synthetic_prepare_diagnostics')
    module.__file__ = review_solve.__file__
    exec(compile(source, module.__file__, 'exec'), module.__dict__)
    return module


def packet(tmp_path, declaration):
    task = tmp_path / 'repo/generators/synthetic'
    task.mkdir(parents=True)
    (task / 'generator.py').write_text(declaration + '\n')
    canonical = tmp_path / 'repo/shared/data/canonical'
    canonical.mkdir(parents=True)
    (canonical / 'puzzles.jsonl').write_text('')
    (tmp_path / 'BLIND_ASSIGNMENT.json').write_text(json.dumps({
        'schema': review_solve.BLIND_SCHEMA, 'assignment_id': 'synthetic',
        'packet_id': 'synthetic', 'task_id': 'synthetic',
        'generator': {'generator': 'generators/synthetic/generator.py'}}))
    return tmp_path


def test_declaration_failure_exposes_safe_stage_without_source(tmp_path):
    module = isolated_solve()
    root = packet(tmp_path, 'EXAMPLES_NEEDED = private_symbol()')
    result = module.prepare_solve(root, 'blind')
    assert result['status'] == 'blocked'
    assert result.get('preparation_stage') == 'demonstration_contract'
    assert result.get('failure_code') == 'invalid_demonstration_contract'
    public = module._public_cli_result(result)
    assert public.get('preparation_stage') == 'demonstration_contract'
    assert public.get('failure_code') == 'invalid_demonstration_contract'
    assert 'private_symbol' not in json.dumps(public)
    assert not (root / 'solve-blind/challenge.json').exists()


def test_materialization_error_never_exposes_rule_or_worker_output(tmp_path):
    module = isolated_solve()
    root = packet(tmp_path, 'EXAMPLES_NEEDED = 3')
    class FailingCatalog:
        def __init__(self, _):
            pass
        def generate(self, *args, **kwargs):
            raise RuntimeError('PRIVATE_RULE_SENTINEL and QUERY_LABEL_SENTINEL')
    module.Catalog = FailingCatalog
    result = module.prepare_solve(root, 'blind')
    public = module._public_cli_result(result)
    assert public.get('preparation_stage') == 'episode_materialization'
    assert public.get('failure_code') == 'episode_materialization_failed'
    assert 'PRIVATE_RULE_SENTINEL' not in json.dumps(public)
    assert 'QUERY_LABEL_SENTINEL' not in json.dumps(public)
    private = json.loads((root / '.review/solve-private-blind/generation-error-0001.json').read_text())
    assert 'PRIVATE_RULE_SENTINEL' in private['error']


@pytest.mark.parametrize('error,kind,expected', [
    ('malformed node or string on line 3: <ast.Call object at 0xdeadbeef>', 'ValueError', 'nonliteral_demonstration_declaration'),
    ('EXAMPLES_NEEDED must be a literal integer in 1..32', 'ValueError', 'invalid_demonstration_declaration'),
    ('Mapped runtime receipt reader conflicts with the installed reader', 'ValueError', 'runtime_receipt_reader_conflict'),
    ('PRIVATE_RULE_SENTINEL', 'RuntimeError', 'private_detail_suppressed'),
])
def test_private_error_classifier_never_returns_raw_detail(error, kind, expected):
    result = diagnostic_module().classify_private_error(error, kind)
    assert result['safe_code'] == expected
    assert result['raw_private_detail_emitted'] is False
    assert 'PRIVATE_RULE_SENTINEL' not in json.dumps(result)
    assert '0xdeadbeef' not in json.dumps(result)
