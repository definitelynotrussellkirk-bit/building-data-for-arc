"""Focused tests of the reviewer probe, independent of the selected generator."""
from __future__ import annotations

import copy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import time
from types import SimpleNamespace


PROBE_PATH = Path(__file__).resolve().parent.parent / "workspace" / "contract_probe.py"
SPEC = importlib.util.spec_from_file_location("e82_probe_under_test", PROBE_PATH)
PROBE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROBE)


def four_pair_grid():
    grid = [[0] * 7 for _ in range(7)]
    for r, c in ((0, 0), (0, 3), (3, 0), (3, 3)):
        grid[r][c] = grid[r + 1][c + 1] = 2
    return grid


def test_silent_underfill_and_lying_observer_are_both_detected():
    grid = four_pair_grid()
    observed = PROBE.independently_observe(grid)
    assert observed["n_pairs"] == 4
    honest_errors = PROBE.observation_errors(grid, {"n_pairs": 5}, observed)
    assert any("requested n_pairs=5" in error for error in honest_errors)
    lying_errors = PROBE.observation_errors(grid, {"n_pairs": 5}, {**observed, "n_pairs": 5})
    assert any("requested n_pairs=5" in error for error in lying_errors)
    assert any("observer n_pairs=5" in error for error in lying_errors)


def test_observer_bool_is_not_an_integer_measurement():
    grid = four_pair_grid()
    observed = {**PROBE.independently_observe(grid), "grid_h": True}
    assert "observer grid_h must be an exact integer" in PROBE.observation_errors(grid, {}, observed)


def test_materialized_case_records_determinism_and_detects_baseline_underfill(tmp_path):
    module = SimpleNamespace(generate=lambda *_args, **_kwargs: four_pair_grid(),
                             observe_overrides=PROBE.independently_observe,
                             self_check=lambda _grid, **_kwargs: [],
                             strict_canonical_like=lambda _grid: [])
    evidence = PROBE.Evidence(tmp_path / "exact-case")
    try:
        case = PROBE.generate_case(module, evidence, scope="unit", seed=0, index=0, band=None,
                                   requested={"n_pairs": 4}, repeat=True)
        assert case["status"] == "materialized"
        assert case["deterministic_replay"] == "matched"
        assert evidence.failure_count == 0
        PROBE.generate_case(module, evidence, scope="underfill", seed=0, index=0, band=None,
                            requested={"n_pairs": 5}, repeat=True)
        assert evidence.error_counts["requested_axis_mismatch"] == 1
    finally:
        evidence.close()


def test_coordinate_oracle_handles_shared_missing_corner_simultaneously():
    grid = [[2, 0, 2], [0, 2, 0]]
    original = copy.deepcopy(grid)
    assert PROBE.eligible_windows(grid) == {(0, 0), (0, 1)}
    assert PROBE.independent_oracle(grid) == [[2, 3, 2], [3, 2, 3]]
    assert grid == original


def test_survived_all_is_a_teaching_gap_even_without_query_ambiguity():
    name = "CANONICAL_SHORTCUTS.baseline_like"
    cases = []
    for index, (r, c) in enumerate(((0, 0), (0, 1), (1, 0), (1, 1))):
        grid = [[0] * 4 for _ in range(4)]
        grid[r][c] = grid[r + 1][c + 1] = 2
        expected = PROBE.independent_oracle(grid)
        cases.append({"case_id": index + 1, "seed": 0, "sample_index": index,
                      "difficulty": None, "input": grid, "input_sha256": PROBE.digest(grid),
                      "independent_oracle_output": expected, "predictions": {name: expected}})
    report = PROBE.score_lesson_rotations(cases, names=[name], shortcuts=[name], n_train=3,
                                         require_teaching_support=False)
    assert report["ambiguities"] == []
    assert report["survived_all"][name] == 4
    assert report["teaching_support"][name]["minimum_distinct_refuting_demos"] == 0
    assert report["insufficient_teaching_support"] == []
    strict = PROBE.score_lesson_rotations(cases, names=[name], shortcuts=[name], n_train=3,
                                         require_teaching_support=True)
    assert len(strict["insufficient_teaching_support"]) == 4


def test_observer_exception_is_a_failure_with_full_input_retained(tmp_path):
    grid = four_pair_grid()

    def broken_observer(_grid):
        raise RuntimeError("deliberate broken observer")

    evidence = PROBE.Evidence(tmp_path / "new-evidence")
    try:
        ok, value = PROBE.checked_hook(evidence, broken_observer, grid, name="observe_overrides",
                                       case={"case_id": 1})
        assert not ok and value is None
        assert evidence.failure_count == 1
    finally:
        evidence.close()
    with gzip.open(tmp_path / "new-evidence" / "failures.jsonl.gz", "rt") as handle:
        failure = json.loads(next(handle))
    assert failure["code"] == "hook_exception"
    assert failure["input"] == grid
    assert failure["exception"] == "RuntimeError"


def test_source_snapshots_pin_exact_bytes_and_detect_changes(tmp_path):
    path = tmp_path / "source.py"
    original = b"VERSION = 'before'\n"
    path.write_bytes(original)
    before = PROBE.source_snapshot({"source": path})
    assert before["source"]["bytes"] == len(original)
    assert before["source"]["sha256"] == hashlib.sha256(original).hexdigest()
    assert before == PROBE.source_snapshot({"source": path})
    path.write_bytes(b"VERSION = 'after'\n")
    assert before != PROBE.source_snapshot({"source": path})


def test_compressed_evidence_hashes_and_restoration_metadata(tmp_path):
    path = tmp_path / "cases.jsonl.gz"
    original = b'{"case":1}\n{"case":2}\n'
    with gzip.open(path, "wb") as handle:
        handle.write(original)
    metadata = PROBE.compressed_artifact_metadata(path)
    assert metadata["compressed_bytes"] == path.stat().st_size
    assert metadata["compressed_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert metadata["uncompressed_bytes"] == len(original)
    assert metadata["uncompressed_sha256"] == hashlib.sha256(original).hexdigest()
    assert metadata["jsonl_records"] == 2
    assert metadata["restored_filename"] == "cases.jsonl"
    assert metadata["restore_command"] == "gzip -dc cases.jsonl.gz > cases.jsonl"


def test_final_report_retains_integrity_error_without_rewriting_closed_evidence(tmp_path, monkeypatch):
    source = tmp_path / "generator.py"
    source.write_text("VERSION = 'fixture'\n")
    source_paths = {"generator": source}
    before = PROBE.source_snapshot(source_paths)
    evidence = PROBE.Evidence(tmp_path / "integrity-failure")
    evidence.case({"input": four_pair_grid()})
    evidence.close()
    closed_bytes = {name: (evidence.output / name).read_bytes()
                    for name in ("cases.jsonl.gz", "failures.jsonl.gz")}
    real_metadata = PROBE.compressed_artifact_metadata

    def fail_integrity_check(path):
        if path.name == "failures.jsonl.gz":
            raise OSError("deliberate compressed integrity failure")
        return real_metadata(path)

    monkeypatch.setattr(PROBE, "compressed_artifact_metadata", fail_integrity_check)
    PROBE.finalize_evidence(evidence, source_paths=source_paths, snapshots_before=before,
                            started=time.monotonic())
    report = json.loads((evidence.output / "report.json").read_text())
    assert report["passed"] is False
    assert report["error_count"] == 1
    assert report["error_counts"] == {"compressed_artifact_verification_failed": 1}
    assert report["source_snapshot_matches"] is True
    assert report["finalization_failures"] == [{
        "failure_id": 1, "code": "compressed_artifact_verification_failed",
        "filename": "failures.jsonl.gz", "exception": "OSError",
        "message": "deliberate compressed integrity failure",
    }]
    for name, original in closed_bytes.items():
        assert (evidence.output / name).read_bytes() == original
