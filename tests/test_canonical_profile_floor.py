#!/usr/bin/env python3
"""Controlled unit regression: no canonical files, generators, or Racket used."""
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

DEFAULT_SOURCE = Path(__file__).resolve().parents[1] / 'shared/tools/canonical_profile_gate.py'

def load_gate(path):
    # Only the import-time encoding helpers are stubbed. These unit fixtures
    # replace canonical_inputs entirely and do not exercise normalization.
    scripts = types.ModuleType('scripts')
    normalizers = types.ModuleType('scripts.coder_synth_verify')
    normalizers._as_pairs = lambda value: value
    normalizers._norm_grid = lambda value: value
    spec = importlib.util.spec_from_file_location('profile_floor_unit_subject', path)
    module = importlib.util.module_from_spec(spec)
    original_path = sys.path[:]
    try:
        with patch.dict(sys.modules, {'scripts': scripts, 'scripts.coder_synth_verify': normalizers}):
            spec.loader.exec_module(module)
    finally:
        sys.path[:] = original_path
    return module

def grid(h, w, colors):
    return [[(r * w + c) % colors for c in range(w)] for r in range(h)]

EXACT = grid(2, 2, 2)
ENVELOPE_ONLY = grid(3, 3, 3)
OUTSIDE = grid(5, 5, 5)
CANONICAL = [EXACT, grid(4, 4, 4)]

def audit_case(gate, name):
    calls = {band: 0 for band in gate.BANDS}
    def generate(seed, sample_index, *, difficulty):
        index = calls[difficulty]
        calls[difficulty] += 1
        if name == 'envelope_only':
            return ENVELOPE_ONLY
        if name == 'mixed_bands':
            return EXACT if difficulty == 'easy' else ENVELOPE_ONLY
        return EXACT if index == 0 else OUTSIDE
    generator = types.SimpleNamespace(generate=generate, self_check=lambda value: [])
    floor = 2 if name == 'double_count' else 1
    with patch.object(gate, 'canonical_inputs', return_value=CANONICAL), patch.object(
        gate.importlib, 'import_module', return_value=generator
    ):
        result = gate.audit_task('controlled_fixture', per_band=20, strict=True, min_band_support=floor)
    return result

class ProfileFloorRegression(unittest.TestCase):
    gate = load_gate(DEFAULT_SOURCE)
    def test_envelope_only_cannot_satisfy_exact_floor(self):
        result = audit_case(self.gate, 'envelope_only')
        self.assertEqual(result['exact_hits'], 0)
        self.assertEqual(result['envelope_hits'], 60)
        self.assertEqual(result['status'], 'FAIL')
        self.assertEqual(result['bands_below_floor'], ['easy', 'hard', 'medium'])
    def test_each_band_requires_its_own_exact_hit(self):
        result = audit_case(self.gate, 'mixed_bands')
        self.assertEqual(result['exact_hits'], 20)
        self.assertEqual(result['envelope_hits'], 60)
        self.assertEqual(result['status'], 'FAIL')
        self.assertEqual(result['bands_below_floor'], ['hard', 'medium'])
    def test_one_exact_hit_does_not_count_as_two_hits(self):
        result = audit_case(self.gate, 'double_count')
        self.assertEqual(result['exact_hits'], 3)
        self.assertEqual(result['envelope_hits'], 3)
        self.assertEqual(result['status'], 'FAIL')
        self.assertEqual(result['envelope_only_hits'], 0)
        self.assertEqual(result['bands_below_floor'], ['easy', 'hard', 'medium'])
    def test_positive_one_exact_hit_per_band(self):
        result = audit_case(self.gate, 'positive')
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(result['exact_hits'], 3)
        self.assertEqual(result['envelope_hits'], 3)
        self.assertEqual(result['envelope_only_hits'], 0)
        self.assertEqual(result['bands_with_zero_support'], [])
        self.assertEqual(result['band_support_basis'], 'exact')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--module', type=Path, default=DEFAULT_SOURCE)
    args = parser.parse_args()
    ProfileFloorRegression.gate = load_gate(args.module)
    unittest.main(argv=[sys.argv[0]], verbosity=2)
