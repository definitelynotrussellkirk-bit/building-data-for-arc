from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

TASK_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = TASK_DIR / "workspace" / "verify_lesson_census.py"
SPEC = importlib.util.spec_from_file_location("verify_lesson_census_ffd3a33c5687", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
verifier = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verifier)


def _complete_report() -> dict:
    rival_names = [
        f"{registry}:{name}"
        for registry in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS", "SEMANTIC_RIVALS")
        for name in ("preserve_occupied_conflicts", "right_priority")
    ]
    band_summary = {
        "requested": 100,
        "materialized": 100,
        "materialization_errors": 0,
        "pairs": 400,
        "ambiguous": 0,
        "hook_warnings": 0,
        "scoring_errors": 0,
        "rotations": 400,
        "ambiguous_rotations": 0,
        "rotation_hook_warnings": 0,
        "rotation_scoring_errors": 0,
        "unique_inputs": 400,
        "rivals": {name: {"refuted": 100} for name in rival_names},
    }
    lesson_rivals = {name: "refuted" for name in rival_names}
    rotations = [
        {
            "errors": [],
            "warnings": [],
            "ambiguous": False,
            "rivals": dict(lesson_rivals),
        }
        for _ in range(4)
    ]
    return {
        "schema": "arcpuzzles-lesson-census-v1",
        "task_id": "ffd3a33c5687",
        "generator_sha256": "abc123",
        "status": "error",
        "errors": ["canonical: ValueError: Expected a nonempty grid"],
        "canonical_read_error": "ValueError: Expected a nonempty grid",
        "rivals": rival_names,
        "summary": {
            "requested": 300,
            "materialized": 300,
            "materialization_errors": 0,
            "pairs": 1200,
            "ambiguous": 0,
            "hook_warnings": 0,
            "scoring_errors": 0,
            "rotations": 1200,
            "ambiguous_rotations": 0,
            "rotation_hook_warnings": 0,
            "rotation_scoring_errors": 0,
            "unique_inputs": 1200,
        },
        "per_band": {band: dict(band_summary) for band in ("easy", "medium", "hard")},
        "lessons": [
            {
                "band": band,
                "errors": [],
                "warnings": [],
                "ambiguous": False,
                "rivals": dict(lesson_rivals),
                "rotations": [dict(rotation) for rotation in rotations],
            }
            for band in ("easy", "medium", "hard")
            for _ in range(100)
        ],
    }


def test_accepts_only_the_known_unlabelled_query_reader_limitation():
    report = _complete_report()
    result = verifier.validate_shared_report(report, expected_task_id="ffd3a33c5687", expected_hash="abc123")
    assert result == []


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda report: report["errors"].append("other failure"), "unexpected top-level errors"),
        (lambda report: report["summary"].__setitem__("ambiguous", 1), "summary.ambiguous"),
        (
            lambda report: report["per_band"]["hard"]["rivals"][
                "SEMANTIC_RIVALS:right_priority"
            ].__setitem__("refuted", 99),
            "hard rival SEMANTIC_RIVALS:right_priority",
        ),
        (lambda report: report["lessons"][0].__setitem__("errors", ["boom"]), "lesson errors"),
    ],
)
def test_rejects_incomplete_or_differently_failed_census(mutation, message):
    report = _complete_report()
    mutation(report)
    errors = verifier.validate_shared_report(
        report, expected_task_id="ffd3a33c5687", expected_hash="abc123"
    )
    assert any(message in error for error in errors), errors


def test_runtime_bootstrap_adds_packet_shared_runtime(tmp_path, monkeypatch):
    runtime = tmp_path / "shared" / "runtime"
    (runtime / "puzzle_generators").mkdir(parents=True)
    monkeypatch.setattr(verifier.sys, "path", ["sentinel"])
    selected = verifier.bootstrap_runtime(tmp_path)
    assert selected == runtime
    assert verifier.sys.path[0] == str(runtime)
