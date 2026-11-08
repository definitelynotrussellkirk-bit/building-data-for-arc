from __future__ import annotations

import importlib.util
from pathlib import Path


PROBE_PATH = Path(__file__).resolve().parents[1] / "workspace" / "room_graph_probe.py"


def _load_probe():
    spec = importlib.util.spec_from_file_location(
        "room_graph_probe_6b694a414d96_test", PROBE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_probe_exercises_canonical_pairs_and_complete_three_profile_windows():
    probe = _load_probe()
    result = probe.run_probe(seeds_per_band=3)

    assert result["passed"] is True
    assert result["canonical_pairs"] == {"accepted": 3, "total": 3}
    assert result["windows_checked"] == 9
    assert result["profile_counts"] == {
        "horizontal": 9,
        "vertical": 9,
        "second_hop": 9,
    }
    assert result["second_hop_witnesses"] == 9
    assert result["failures"] == []
