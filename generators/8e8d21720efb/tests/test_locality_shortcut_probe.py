from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_probe():
    path = Path(__file__).resolve().parents[1] / "workspace" / "locality_shortcut_probe.py"
    spec = importlib.util.spec_from_file_location("locality_shortcut_probe", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_authority_and_global_frequency_rival_separate_locality():
    probe = _load_probe()
    grid = [
        [2, 2, 0, 0],
        [0, 0, 0, 2],
        [0, 0, 3, 0],
        [0, 3, 0, 0],
    ]
    authority = probe.authority_output(grid)
    rival = probe.global_frequency_output(grid)
    assert authority == [
        [2, 2, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]
    assert rival == [
        [2, 2, 0, 0],
        [0, 0, 0, 2],
        [0, 0, 3, 0],
        [0, 3, 0, 0],
    ]


def test_analyze_module_counts_examples_and_rotation_ambiguity():
    probe = _load_probe()

    canonical = [
        [1, 1, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 2, 2],
        [0, 0, 0, 0],
    ]
    witness = [
        [1, 1, 0, 1],
        [0, 0, 0, 0],
        [0, 0, 2, 2],
        [0, 0, 0, 0],
    ]

    class FakeModule:
        @staticmethod
        def generate(seed, sample_index, *, difficulty=None):
            del seed, difficulty
            return canonical if sample_index % 2 == 0 else witness

        @staticmethod
        def self_check(grid):
            return []

    report = probe.analyze_module(FakeModule, seed=7, per_band=6, bands=("easy",))
    band = report["bands"]["easy"]
    assert band["generated"] == 6
    assert band["rival_matches"] == 3
    assert band["rival_disagreements"] == 3
    # Every four-pair alternating window retains a witness in any three demos,
    # so the rival never fits all demos while differing on the held-out query.
    assert band["ambiguous_rotations"] == 0
    assert band["rotations_checked"] == 12
