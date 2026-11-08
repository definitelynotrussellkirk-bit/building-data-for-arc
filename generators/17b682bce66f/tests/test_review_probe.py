"""Regression tests for translation-normalized concentration measurement."""
from pathlib import Path
import importlib.util


def probe():
    path = Path(__file__).resolve().parents[1] / 'workspace/review_probe.py'
    assert path.is_file(), 'Retain the runnable concentration probe, not just its numbers'
    spec = importlib.util.spec_from_file_location('review_concentration_probe', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_translation_signature_removes_position_not_palette_or_canvas():
    p = probe()
    a = [[0, 9, 8, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    b = [[0, 0, 0, 0], [9, 8, 0, 0], [0, 0, 0, 0]]
    c = [[0, 0, 0, 0], [9, 2, 0, 0], [0, 0, 0, 0]]
    assert p.translation_signature(a) == p.translation_signature(b)
    assert p.translation_signature(a) != p.translation_signature(c)
    assert p.translation_signature(a) != p.translation_signature(a + [[0]*4])


def test_empty_and_nonrectangular_inputs_are_explicit():
    p = probe()
    import pytest
    assert p.translation_signature([[0, 0], [0, 0]]) == (2, 2, ())
    for grid in ([], [[]], [[1, 2], [3]]):
        with pytest.raises(ValueError):
            p.translation_signature(grid)


def test_counter_reports_denominators_and_split_recurrence():
    p = probe()
    rows = [dict(raw_hash=str(i), signature_hash=s, profile='x', cloud_orbit_hash=s)
            for i, s in enumerate(('a', 'b', 'a', 'c'))]
    s = p.summarize(rows)
    assert s['draws'] == 4
    assert s['distinct_raw_inputs'] == 4
    assert s['distinct_translation_normalized_inputs'] == 3
    assert s['lookup_train_rows'] == 2
    assert s['lookup_test_rows'] == 2
    assert s['lookup_test_signature_hits'] == 1
    assert s['lookup_test_signature_hit_fraction'] == .5
