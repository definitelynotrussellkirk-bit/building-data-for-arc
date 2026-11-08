"""Regression coverage for non-vacuous task-local audit evidence."""
from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_probe():
    path = Path(__file__).resolve().parents[1] / "workspace" / "passthrough_probe.py"
    if not path.is_file():
        # The isolated legacy runtime may collect the mirrored test source.
        from reviewer_support import find_root

        root = find_root(__file__)
        candidates = (
            root / "generators" / "69cab6228fdc" / "workspace" / "passthrough_probe.py",
            root / "workspace" / "passthrough_probe.py",
        )
        path = next(candidate for candidate in candidates if candidate.is_file())
    spec = importlib.util.spec_from_file_location("passthrough_probe_evidence", path)
    assert spec is not None and spec.loader is not None
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    return probe


def test_empty_canonical_evidence_cannot_report_a_successful_shortcut_audit():
    # Removing the nonempty-evidence guard must make this regression fail.
    report = _load_probe().run_probe(canonical_pairs=[], per_band=4)

    assert report["status"] == "fail"
    assert any("canonical evidence is empty" in failure for failure in report["failures"])
    assert report["canonical_evidence"] == {"status": "empty", "pairs": 0}
    assert report["canonical_shortcuts"]
    for result in report["canonical_shortcuts"].values():
        assert result == {"fits": 0, "pairs": 0, "status": "unverified"}


def test_omitted_canonical_evidence_is_explicitly_reported_as_unrun():
    # A generated-scene-only run is allowed, but must expose its skipped check.
    report = _load_probe().run_probe(per_band=4)

    assert report["status"] == "pass"
    assert report["failures"] == []
    assert report["canonical_shortcuts"] == {}
    assert report["canonical_evidence"] == {"status": "not_provided", "pairs": 0}


def test_nonempty_evidence_retains_real_shortcut_refutations():
    probe = _load_probe()
    gen = probe.load_generator()
    grid = probe.EXACT_WITNESS
    report = probe.run_probe(
        generator=gen,
        canonical_pairs=[{
            "input": grid,
            "output": [
                [3, 5, 6, 0, 0, 0],
                [4, 6, 5, 0, 0, 0],
                [3, 4, 5, 6, 0, 0],
                [4, 3, 6, 5, 0, 0],
            ],
        }],
        per_band=4,
    )

    assert report["status"] == "fail"
    assert report["canonical_evidence"] == {"status": "checked", "pairs": 1}
    assert len(report["failures"]) == 2
    for result in report["canonical_shortcuts"].values():
        assert result == {"fits": 0, "pairs": 1, "status": "refuted"}
