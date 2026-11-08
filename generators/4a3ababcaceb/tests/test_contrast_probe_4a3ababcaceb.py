"""The census must distinguish an executable run from a refuted-rival lesson."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('contrast_probe', HOME / 'workspace/contrast_probe.py')
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def good_report():
    return {'failures': [], 'bands': {
        str(band): {'lesson_count': 3,
                    'three_demo_rival_survivals': {name: 0 for name in probe.NAMES}}
        for band in probe.BANDS}}


def test_refutation_gate_exists_and_accepts_complete_zero_survival_evidence():
    assert callable(getattr(probe, 'refutation_gate_errors', None))
    report = good_report()
    saved = copy.deepcopy(report)
    assert probe.refutation_gate_errors(report) == []
    assert report == saved


@pytest.mark.parametrize('defect', ('survivor', 'missing_rival', 'missing_band',
                                    'zero_lessons', 'invalid_count', 'racket_failure'))
def test_refutation_gate_fails_closed(defect):
    assert callable(getattr(probe, 'refutation_gate_errors', None))
    report = good_report()
    band = report['bands']['medium']
    if defect == 'survivor':
        band['three_demo_rival_survivals']['purest_red_tile'] = 1
    elif defect == 'missing_rival':
        del band['three_demo_rival_survivals']['purest_red_tile']
    elif defect == 'missing_band':
        del report['bands']['medium']
    elif defect == 'zero_lessons':
        band['lesson_count'] = 0
    elif defect == 'invalid_count':
        band['three_demo_rival_survivals']['purest_red_tile'] = -1
    else:
        report['failures'].append({'mirror_disagreement': 'example'})
    assert probe.refutation_gate_errors(report)
