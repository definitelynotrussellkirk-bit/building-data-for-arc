"""Regression tests for the retained source-bound qualification driver."""
from __future__ import annotations

from pathlib import Path
import importlib.util

HOME = Path(__file__).resolve().parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_small_qualification_balances_phases_and_refutes_every_declared_rival():
    qualify = _load("task_qualify", HOME / "workspace/qualify.py")
    probe = _load("task_probe_for_qualify", HOME / "workspace/reference_probe.py")
    generator = probe.load_generator()

    report, parity_grids = qualify.audit(generator, lessons_per_band=4, parity_per_band=2)

    assert report["passed_without_racket"] is True
    assert report["lesson_policy"]["pairs_per_lesson"] == 5
    assert report["lesson_policy"]["cyclic_starts"] == [0, 1, 2, 3]
    assert set(report["canonical_shortcuts"]) == set(generator.CANONICAL_SHORTCUTS)
    assert set(report["lesson_competitors"]) == set(generator.LESSON_COMPETITORS)
    assert len(parity_grids) == len(probe.canonical_pairs()) + 3 * 2

    for band in ("easy", "medium", "hard"):
        row = report["bands"][band]
        assert row["lessons"] == 4
        assert row["input_slots"] == 20
        assert row["cyclic_start_counts"] == {"0": 1, "1": 1, "2": 1, "3": 1}
        assert row["self_check_failures"] == 0
        assert row["nondeterministic_replays"] == 0
        assert row["profile_counts"] == {
            "canonical_core": 5,
            "shifted_prototype": 5,
            "padded_index": 5,
            "broad_tiles": 5,
        }
        assert all(value == 4 for value in row["lessons_refuting_competitor"].values())
        assert all(value > 0 for value in row["input_disagreements_by_competitor"].values())


def test_shortcut_witness_is_exact_and_disagrees():
    qualify = _load("task_qualify_witness", HOME / "workspace/qualify.py")
    probe = _load("task_probe_witness", HOME / "workspace/reference_probe.py")
    generator = probe.load_generator()

    witness = qualify.shortcut_witness(generator)

    assert witness["shortcut"] == "absolute_row_padding"
    assert witness["profile"] == "shifted_prototype"
    assert witness["self_check"] == []
    assert witness["intended_python"] != witness["rival_output"]
    assert witness["differing_cells"] > 0
