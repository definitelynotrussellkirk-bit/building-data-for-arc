from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / 'workspace/probe_conservation.py'


def probe():
    assert SCRIPT.is_file(), 'the reusable conservation probe is missing'
    spec = importlib.util.spec_from_file_location('review_probe', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def scene():
    g = [[0] * 9 for _ in range(7)]
    g[0][0] = 1
    for r, c in [(5, 8), (6, 6), (6, 7), (6, 8)]:
        g[r][c] = 5
    return g


def test_catches_silent_loss_from_legacy_seed_67():
    out = [[0] * 9 for _ in range(7)]
    out[5][6] = out[6][6] = 5
    assert 'motif_color_counts_changed' in probe().conservation_issues(scene(), out)


def test_ignores_control_but_not_a_motif_repainting_its_old_location():
    out = [[0] * 9 for _ in range(7)]
    for r, c in [(0, 0), (2, 2), (2, 3), (3, 2)]:
        out[r][c] = 5
    assert probe().conservation_issues(scene(), out) == []


def test_color_substitution_is_caught_even_with_equal_mass():
    out = [[0] * 9 for _ in range(7)]
    for r, c in [(1, 1), (2, 1), (3, 1), (3, 2)]:
        out[r][c] = 8
    assert 'motif_color_counts_changed' in probe().conservation_issues(scene(), out)


def test_output_shape_change_is_caught():
    assert 'canvas_shape_changed' in probe().conservation_issues(scene(), [[0]])


@pytest.mark.parametrize('out', [None, [], [[]], [[0], [0, 1]], [[11]], [[True]]])
def test_malformed_output_is_a_failure(out):
    assert 'malformed_output' in probe().conservation_issues(scene(), out)
