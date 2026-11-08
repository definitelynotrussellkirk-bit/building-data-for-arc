from __future__ import annotations

import importlib.util
from pathlib import Path

HOME = Path(__file__).resolve().parents[1]
PROBE_PATH = HOME / "workspace" / "lesson_probe.py"
SPEC = importlib.util.spec_from_file_location("lesson_probe_0f423424b1dc", PROBE_PATH)
assert SPEC and SPEC.loader
PROBE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROBE)


def test_probe_is_source_bound_and_checks_every_cyclic_start():
    report = PROBE.run_probe(per_band=4)

    assert report["task_id"] == "0f423424b1dc"
    assert report["source"]["declared_rule_hash"] == "1e2581a2f271"
    assert report["source"]["canonical_rule_hash"] == "1e2581a2f271"
    assert len(report["source"]["generator_sha256"]) == 64
    assert report["canonical_shortcuts"]["all_fit_every_canonical_pair"] is True

    for band in ("easy", "medium", "hard"):
        row = report["bands"][band]
        assert row["lessons"] == 4
        assert row["pairs"] == 20
        assert row["identifiable_lessons"] == 4
        assert row["self_check_failures"] == 0
        assert row["start_residues_mod_4"] == {"0": 1, "1": 1, "2": 1, "3": 1}
        assert row["unique_inputs"] == 20
        assert all(count == 4 for count in row["rival_refuted_lessons"].values())
