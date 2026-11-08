"""Diagnostics discover existing contracts while retaining collapsed-output findings."""
import importlib.util
from pathlib import Path
import sys
import types

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_tool(monkeypatch, name):
    package = types.ModuleType('scripts'); package.__path__ = [str(ROOT / 'shared/tools')]
    monkeypatch.setitem(sys.modules, 'scripts', package)
    spec = importlib.util.spec_from_file_location('contract_' + name, ROOT / f'shared/tools/{name}.py')
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('distinct', [1, 10])
def test_lint_output_warning_names_contract_and_requires_full_alphabet(monkeypatch, tmp_path, distinct):
    lint = load_tool(monkeypatch, 'lint_generator')
    source = tmp_path / 'fixture/generator.py'; source.parent.mkdir()
    source.write_text('''GENERATOR_ID = TASK_ID = 'fixture'
VERSION = '1.0.0'
RULE_HASH = '123456789abc'
SUMMARY = 'fixture'
INVARIANTS = ['fixture']
AXES = {}
def generate(seed, sample_index, *, difficulty=None, **overrides): return [[0]]
def self_check(grid): return []
''')
    # Validation and Racket probing are external to message generation; retain
    # the real linter branch using a measured collapsed-output fixture.
    runner = types.ModuleType('puzzle_generators.runner')
    runner.run_batch = lambda *a, **k: [None] * 20
    runner._load_generator_module = lambda tid: types.SimpleNamespace()
    probe = types.ModuleType('scripts.gen_diversity_probe')
    probe.probe_task = lambda *a, **k: {'pairs': 100, 'uniq_out': distinct / 100,
        'n_distinct_out': distinct, 'frac_identity': 0, 'out_shapes': [], 'n_colors': 2}
    monkeypatch.setitem(sys.modules, 'puzzle_generators.runner', runner)
    monkeypatch.setitem(sys.modules, 'scripts.gen_diversity_probe', probe)
    report = lint.lint_generator(source, validate=True)
    messages = report.errors + report.warnings
    finding = next(text for text in messages if 'output' in text and ('POISON' in text or 'diversity' in text))
    assert 'EXPECTED_OUTPUT_CODOMAIN' in finding
    assert 'canonical rule' in finding and 'cover' in finding
    assert bool(report.errors) is (distinct == 1)


def test_defect_solid_message_names_existing_self_check_contract(monkeypatch):
    tool = load_tool(monkeypatch, 'generator_defect_lint')
    context = {'output': [[0] * 3 for _ in range(3)], 'train': [], 'has_self_check': True}
    finding = tool.d_all_background_output(context)[0]
    assert 'SOLID_OUTPUT_JUSTIFICATION' in finding
    assert 'self_check' in finding and 'canonical rule' in finding
    assert tool.d_all_background_output({**context, 'solid_output_justification': 'short'})
    assert tool.d_all_background_output({**context,
        'solid_output_justification': 'A concrete canonical rule explanation of this lawful endpoint.'}) == []
    assert tool.d_all_background_output({**context, 'has_self_check': False,
        'solid_output_justification': 'A concrete canonical rule explanation of this lawful endpoint.'})


def test_defect_diversity_message_requires_codomain_coverage(monkeypatch):
    tool = load_tool(monkeypatch, 'generator_defect_lint')
    context = {'all_outputs': [[[0] * 4 for _ in range(4)]] * 12, 'train': [], 'expected_codomain': 2}
    finding = tool.d_low_output_diversity(context)[0]
    assert 'EXPECTED_OUTPUT_CODOMAIN' in finding
    assert 'canonical rule' in finding and 'cover' in finding
    assert tool.d_low_output_diversity({**context,
        'all_outputs': context['all_outputs'][:6] + [[[1] * 4 for _ in range(4)]] * 6}) == []
