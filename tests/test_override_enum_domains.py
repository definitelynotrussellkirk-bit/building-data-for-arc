"""Bound finite enum probes without dropping axes or inventing full coverage."""
import importlib.util
import json
from pathlib import Path
import sys
import types

import pytest


ROOT = Path(__file__).resolve().parents[1]


def load_tools(monkeypatch):
    def load(name, relative):
        spec = importlib.util.spec_from_file_location(name, ROOT / relative)
        module = importlib.util.module_from_spec(spec)
        monkeypatch.setitem(sys.modules, name, module)
        spec.loader.exec_module(module)
        return module

    base = load('puzzle_generators.base', 'shared/runtime/puzzle_generators/base.py')
    checker = load('scripts.check_generator_override_contract',
                   'shared/tools/check_generator_override_contract.py')
    lint = load('enum_fixture_lint', 'shared/tools/lint_generator.py')
    return base, checker, lint


@pytest.mark.parametrize('encoding', ['list', 'tuple', 'pipe'])
def test_large_enum_keeps_bounded_deterministic_probes(monkeypatch, encoding):
    _, checker, _ = load_tools(monkeypatch)
    values = [f'mode-{i:02d}' for i in range(26)]
    raw = values if encoding == 'list' else tuple(values) if encoding == 'tuple' else '|'.join(values)
    spec = {'type': 'enum', 'valid': raw}
    domain = checker.classify_axis_domain('scene_profile', spec, {'scene_profile': spec})
    assert domain.status == 'finite_enum_too_large'
    assert len(domain.values) == 16
    assert domain.values[0] == values[0] and domain.values[-1] == values[-1]
    assert len(set(domain.values)) == 16 and set(domain.values) < set(values)
    assert checker._axis_values(spec) == domain.values
    cases = checker._build_cases({'scene_profile': spec})
    assert len(cases) == 17
    assert [case['scene_profile'] for case in cases[1:]] == domain.values
    assert '26' in domain.reason and '16' in domain.reason
    assert 'sample' in domain.reason.lower()


def test_small_enum_stays_exhaustive_and_malformed_stays_unparsable(monkeypatch):
    _, checker, _ = load_tools(monkeypatch)
    values = [f'mode-{i}' for i in range(16)]
    spec = {'type': 'str', 'valid': values}
    assert checker._axis_values(spec) == values
    assert checker.classify_axis_domain('profile', spec, {}).status == 'probeable'
    bad = {'type': 'enum', 'valid': values + [None]}
    assert checker._axis_values(bad) == []
    assert checker.classify_axis_domain('profile', bad, {}).status == 'unparsable'


@pytest.mark.parametrize('size', [3, 26])
def test_diagnostic_enum_does_not_enter_case_matrix_or_required_observer(monkeypatch, size):
    _, checker, _ = load_tools(monkeypatch)
    axes = {'profile': {'type': 'enum', 'valid': [str(i) for i in range(size)],
                        'probe': 'diagnostic'}}
    assert checker.classify_axis_domain('profile', axes['profile'], axes).status == 'diagnostic'
    assert checker._build_cases(axes) == [{}]
    assert checker._required_observer_axes(axes) == set()


def test_sampled_enum_requires_realized_value_and_detects_omission_or_clamping(monkeypatch):
    _, checker, _ = load_tools(monkeypatch)
    axes = {'profile': {'type': 'enum', 'valid': [str(i) for i in range(26)]}}
    required = checker._required_observer_axes(axes)
    assert required == {'profile'}
    generator = types.SimpleNamespace(AXES=axes, observe_overrides=lambda grid: {})
    assert 'omitted required exact axis' in checker._observed_override_errors(
        generator, [[0]], {'profile': '25'}, 'fixture', required)[0]
    generator.observe_overrides = lambda grid: {'profile': '0'}
    assert 'observed' in checker._observed_override_errors(
        generator, [[0]], {'profile': '25'}, 'fixture', required)[0]


def test_static_lint_separates_bounded_enum_sampling_from_bad_metadata(monkeypatch):
    _, _, lint = load_tools(monkeypatch)
    report = lint.LintReport()
    lint._check_axis_domains({'profile': {'type': 'enum', 'valid': [str(i) for i in range(19)]}}, report)
    assert not report.errors
    assert any('finite_enum_too_large' in message and '19' in message and '16' in message
               for message in report.warnings)
    bad = lint.LintReport()
    lint._check_axis_domains({'profile': {'type': 'enum', 'valid': ['ok', None]}}, bad)
    assert bad.errors


@pytest.mark.parametrize('report_flag', [None, '--compact-results', '--full-results'])
def test_actual_checker_reports_sampled_enum_coverage_and_still_fails_bad_observations(
        monkeypatch, tmp_path, report_flag):
    base, checker, _ = load_tools(monkeypatch)
    values = [str(i) for i in range(26)]
    axes = {'profile': {'type': 'enum', 'valid': values}}

    def generate(seed, index, difficulty='easy', **overrides):
        if checker.UNKNOWN_OVERRIDE_PROBE_KEY in overrides:
            raise ValueError('unknown override')
        ctx = base.gen_ctx(seed=seed, sample_index=index, difficulty=difficulty, overrides=overrides)
        value = ctx.draw_choice('profile', values)
        # Color values remain in 0..9, with a distinct shape for each mode.
        return [[0] * (int(value) + 1)]

    generator = types.SimpleNamespace(AXES=axes, generate=generate, __file__=__file__,
        observe_overrides=lambda grid: {'profile': str(len(grid[0]) - 1)})
    monkeypatch.setattr(checker, '_load_module', lambda _: generator)
    destination = tmp_path / 'result.json'
    argv = ['checker', 'fixture', '--seeds', '1', '--bands', 'easy', '--write-results', str(destination)]
    if report_flag:
        argv.append(report_flag)
    monkeypatch.setattr(sys, 'argv', argv)
    assert checker.main() == 0
    result = json.loads(destination.read_text())
    domain = result['axis_domains'][0]
    assert domain['status'] == 'finite_enum_too_large'
    assert domain['enum_declared_cardinality'] == 26
    assert domain['enum_probe_cap'] == 16
    assert domain['planned_coverage'] == 'sampled'
    assert len(domain['probed_values']) == len(domain['attempted_override_values']) == 16
    assert result['plan']['sampled_enum_axes'] == {'profile': {'declared_cardinality': 26,
                                                             'planned_cardinality': 16}}
    assert result['status'] == 'PASS_WITH_WARNINGS'
    assert result['draws_total'] == 17

    generator.observe_overrides = lambda grid: {}
    assert checker.main() == 1
    failed = json.loads(destination.read_text())
    assert any('omitted required exact axis' in finding['message'] for finding in failed['findings'])


def test_no_observer_remains_a_failure_for_sampled_exact_enum(monkeypatch, tmp_path):
    _, checker, _ = load_tools(monkeypatch)
    axes = {'profile': {'type': 'enum', 'valid': [str(i) for i in range(26)]}}
    generator = types.SimpleNamespace(AXES=axes, generate=lambda *args, **kwargs: [[0]], __file__=__file__)
    monkeypatch.setattr(checker, '_load_module', lambda _: generator)
    destination = tmp_path / 'missing-observer.json'
    monkeypatch.setattr(sys, 'argv', ['checker', 'fixture', '--seeds', '1', '--bands', 'easy',
                                    '--write-results', str(destination)])
    assert checker.main() == 1
    result = json.loads(destination.read_text())
    assert any('missing observe_overrides' in row['message'] for row in result['findings'])


def test_fail_fast_distinguishes_planned_enum_sample_from_zero_attempted_values(monkeypatch, tmp_path):
    _, checker, _ = load_tools(monkeypatch)
    axes = {'profile': {'type': 'enum', 'valid': [str(i) for i in range(26)]},
            'broken': {'type': 'enum', 'valid': ['ok', None]}}
    generator = types.SimpleNamespace(AXES=axes, generate=lambda *args, **kwargs: [[0]], __file__=__file__,
                                     observe_overrides=lambda grid: {'profile': '0'})
    monkeypatch.setattr(checker, '_load_module', lambda _: generator)
    destination = tmp_path / 'fail-fast.json'
    monkeypatch.setattr(sys, 'argv', ['checker', 'fixture', '--seeds', '1', '--bands', 'easy',
                                    '--write-results', str(destination)])
    assert checker.main() == 1
    result = json.loads(destination.read_text())
    assert result['status'] == 'FAIL_FAST' and result['draws_total'] == 0
    domain = result['axis_domains'][0]
    assert len(domain['probed_values']) == 16
    assert domain['attempted_override_values'] == []
