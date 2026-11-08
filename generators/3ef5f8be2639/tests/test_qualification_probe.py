"""The reusable task-local qualification probe must remain executable."""
from __future__ import annotations

import importlib.util
from pathlib import Path

HOME = Path(__file__).resolve().parents[1]


def _load_probe():
    path = HOME / "workspace" / "qualify.py"
    spec = importlib.util.spec_from_file_location("qualify_3ef5f8be2639", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load qualification probe from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_qualification_probe_exhausts_exact_controls_and_cyclic_lesson_rotations():
    probe = _load_probe()
    report = probe.run_audit(
        per_band=8,
        bands=("easy", "medium", "hard"),
        exact_shapes=((7, 7),),
    )
    assert report["status"] == "pass"
    assert report["canonical"]["accepted"] == 3
    assert report["canonical"]["mirror_matches"] == 3
    assert report["canonical"]["rival_fits"] == {
        "all_pairs": 3,
        "distance_two_only": 3,
    }
    assert report["exact_matrix"]["cases"] == 3 * 1 * 24 * 4
    assert report["exact_matrix"]["failures"] == []
    assert report["default_schedule"]["draws"] == 3 * 8
    assert report["lesson_rotations"]["rotations"] == 3 * 8 * 4
    assert report["lesson_rotations"]["failures"] == []
