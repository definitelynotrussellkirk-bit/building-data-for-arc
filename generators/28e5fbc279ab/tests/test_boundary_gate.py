"""Tests for the reusable integer-predicate boundary coverage gate."""
import importlib.util
from pathlib import Path
import pytest

path = Path(__file__).resolve().parents[1] / 'workspace/predicate_boundary_gate.py'
spec = importlib.util.spec_from_file_location('predicate_boundary_gate', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_empty_histogram_fails_closed():
    result = module.check_boundaries({}, [8, 24])
    assert result['status'] == 'FAIL'
    assert result['missing_values'] == [7, 8, 9, 23, 24, 25]
    assert result['observations'] == 0


def test_real_missing_equalities_not_rescued_by_large_sample():
    result = module.check_boundaries({'6': 1000, '12': 1000, '25': 1000}, [8, 24])
    assert result['missing_values'] == [7, 8, 9, 23, 24]
    assert result['status'] == 'FAIL'


def test_neighbors_are_required_not_just_equalities():
    result = module.check_boundaries({'8': 1, '24': 1}, [8, 24])
    assert result['missing_values'] == [7, 9, 23, 25]


def test_complete_coverage_is_only_coverage_not_accuracy():
    result = module.check_boundaries({str(x): 1 for x in [7,8,9,23,24,25]}, [8,24])
    assert result['status'] == 'PASS'
    assert result['missing_values'] == []
    assert result['semantics_verified'] is False


def test_shared_neighbors_deduplicated_and_zero_count_missing():
    result = module.check_boundaries({'7': 1, '8': 1, '9': 0, '10': 1}, [8,9,8])
    assert result['required_values'] == [7,8,9,10]
    assert result['missing_values'] == [9]


@pytest.mark.parametrize('counts,thresholds', [
    ({'8': -1}, [8]), ({'8': 0.5}, [8]), ({'8': True}, [8]),
    ({'8.0': 1}, [8]), ({'08': 1}, [8]), ({True: 1}, [8]),
    ({'8': 1}, []), ({'8': 1}, [8.0]), ({'8': 1}, [True]),
])
def test_malformed_contract_is_rejected(counts, thresholds):
    with pytest.raises((TypeError, ValueError)):
        module.check_boundaries(counts, thresholds)
