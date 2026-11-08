from __future__ import annotations

import importlib.util
from pathlib import Path


TASK_ROOT = Path(__file__).resolve().parents[1]
PROBE_PATH = TASK_ROOT / "workspace" / "profile_probe.py"


def _load_probe():
    spec = importlib.util.spec_from_file_location(
        "profile_probe_4cfd24806fb2", PROBE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_probe_covers_all_profiles_and_refutes_every_canonical_shortcut():
    probe = _load_probe()
    report = probe.analyze(seed=20261002, draws_per_band=8)
    assert report["self_check_failures"] == []
    assert set(report["profile_counts"]) == {
        "canonical_sparse",
        "off_center_cluster",
        "edge_row_motif",
        "preserved_right_noise",
    }
    assert all(count > 0 for count in report["profile_counts"].values())
    assert all(
        count > 0 for count in report["canonical_shortcut_refutations"].values()
    )
    assert report["lesson_identifiable"] == []
    assert all(rate >= 0.20 for rate in report["strict_rate_by_band"].values())
