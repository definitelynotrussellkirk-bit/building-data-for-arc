from __future__ import annotations

import importlib.util
from pathlib import Path

from reviewer_support import find_root


TASK_ID = "88ce0ac7322b"


def _load_probe():
    root = Path(find_root(__file__))
    path = root / "generators" / TASK_ID / "workspace" / "rival_probe.py"
    spec = importlib.util.spec_from_file_location(f"{TASK_ID}_rival_probe", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_retained_rival_probe_is_source_bound_dynamic_and_clean():
    probe = _load_probe()
    report = probe.run_probe(starts_per_band=15)

    assert report["task_id"] == TASK_ID
    assert report["generator_sha256"] == probe.generator_sha256()
    assert report["declared_competitors"] == sorted(
        probe.load_generator().LESSON_COMPETITORS
    )
    assert report["canonical"]["pair_count"] == 3
    assert all(row["fits_all"] for row in report["canonical"]["shortcuts"].values())
    assert report["override_matrix"]["cases"] == 36
    assert report["override_matrix"]["failures"] == 0
    assert report["lessons"]["production_windows"] == 45
    assert report["lessons"]["rotated_queries"] == 180
    assert report["lessons"]["unidentifiable"] == 0
    assert report["failures"] == []
