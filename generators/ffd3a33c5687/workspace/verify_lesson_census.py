#!/usr/bin/env python3
"""Verify a completed lesson census when the shared canonical reader rejects an unlabeled query.

The shared census currently treats the normal ARC test item (input without output) as a
canonical-data error.  It nevertheless materializes and scores every requested generated
lesson.  This verifier is deliberately narrow and fail-closed: it accepts only that one
known top-level reader error, checks every saved lesson/rotation/result count, then checks
the declared rivals against labeled canonical train pairs and an independent conflict
witness.  It never changes the shared report and does not convert other failures to passes.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Callable

TASK_ID = "ffd3a33c5687"
KNOWN_CANONICAL_ERROR = "canonical: ValueError: Expected a nonempty grid"
KNOWN_CANONICAL_READ_ERROR = "ValueError: Expected a nonempty grid"
BANDS = ("easy", "medium", "hard")
SUMMARY_EXPECTED = {
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
}
BAND_EXPECTED = {
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
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _check_fields(
    errors: list[str], payload: dict[str, Any], expected: dict[str, int], prefix: str
) -> None:
    for key, wanted in expected.items():
        got = payload.get(key)
        if got != wanted:
            errors.append(f"{prefix}.{key}: expected {wanted}, got {got!r}")


def validate_shared_report(
    report: dict[str, Any], *, expected_task_id: str, expected_hash: str
) -> list[str]:
    """Return failures; accept only a complete census plus the one known reader error."""
    errors: list[str] = []
    if report.get("schema") != "arcpuzzles-lesson-census-v1":
        errors.append(f"unexpected schema: {report.get('schema')!r}")
    if report.get("task_id") != expected_task_id:
        errors.append(
            f"task_id: expected {expected_task_id!r}, got {report.get('task_id')!r}"
        )
    if report.get("generator_sha256") != expected_hash:
        errors.append(
            "generator_sha256: expected "
            f"{expected_hash!r}, got {report.get('generator_sha256')!r}"
        )

    top_errors = report.get("errors")
    if top_errors != [KNOWN_CANONICAL_ERROR]:
        errors.append(
            "unexpected top-level errors: expected only the unlabeled-query reader "
            f"limitation, got {top_errors!r}"
        )
    if report.get("canonical_read_error") != KNOWN_CANONICAL_READ_ERROR:
        errors.append(
            "unexpected canonical_read_error: "
            f"{report.get('canonical_read_error')!r}"
        )
    if report.get("status") != "error":
        errors.append(
            "shared report status should remain 'error' rather than being rewritten, "
            f"got {report.get('status')!r}"
        )

    summary = report.get("summary")
    if not isinstance(summary, dict):
        errors.append("summary is missing or not an object")
    else:
        _check_fields(errors, summary, SUMMARY_EXPECTED, "summary")

    rival_names = report.get("rivals")
    if not isinstance(rival_names, list) or not rival_names:
        errors.append("declared rival list is missing or empty")
        rival_names = []
    elif len(rival_names) != len(set(rival_names)):
        errors.append("declared rival list contains duplicates")

    per_band = report.get("per_band")
    if not isinstance(per_band, dict):
        errors.append("per_band is missing or not an object")
        per_band = {}
    for band in BANDS:
        payload = per_band.get(band)
        if not isinstance(payload, dict):
            errors.append(f"missing per-band result for {band}")
            continue
        _check_fields(errors, payload, BAND_EXPECTED, band)
        band_rivals = payload.get("rivals")
        if not isinstance(band_rivals, dict):
            errors.append(f"{band} rivals are missing or not an object")
            continue
        if set(band_rivals) != set(rival_names):
            errors.append(
                f"{band} rival names differ from the declared rival list: "
                f"{sorted(set(band_rivals) ^ set(rival_names))}"
            )
        for name in rival_names:
            result = band_rivals.get(name)
            if result != {"refuted": 100}:
                errors.append(
                    f"{band} rival {name}: expected {{'refuted': 100}}, got {result!r}"
                )

    lessons = report.get("lessons")
    if not isinstance(lessons, list) or len(lessons) != 300:
        errors.append(
            f"expected 300 saved lessons, got {len(lessons) if isinstance(lessons, list) else type(lessons).__name__}"
        )
        lessons = lessons if isinstance(lessons, list) else []
    band_counts = {band: 0 for band in BANDS}
    for index, lesson in enumerate(lessons):
        if not isinstance(lesson, dict):
            errors.append(f"lesson {index} is not an object")
            continue
        band = lesson.get("band")
        if band in band_counts:
            band_counts[band] += 1
        else:
            errors.append(f"lesson {index} has unexpected band {band!r}")
        if lesson.get("errors") != []:
            errors.append(f"lesson errors at index {index}: {lesson.get('errors')!r}")
        if lesson.get("warnings") != []:
            errors.append(f"lesson warnings at index {index}: {lesson.get('warnings')!r}")
        if lesson.get("ambiguous") is not False:
            errors.append(f"lesson {index} is not unambiguous")
        lesson_rivals = lesson.get("rivals")
        if not isinstance(lesson_rivals, dict):
            errors.append(f"lesson {index} rivals are missing")
        else:
            for name in rival_names:
                if lesson_rivals.get(name) != "refuted":
                    errors.append(
                        f"lesson {index} rival {name} is {lesson_rivals.get(name)!r}, not 'refuted'"
                    )
        rotations = lesson.get("rotations")
        if not isinstance(rotations, list) or len(rotations) != 4:
            errors.append(
                f"lesson {index} expected 4 query rotations, got "
                f"{len(rotations) if isinstance(rotations, list) else type(rotations).__name__}"
            )
            continue
        for rotation_index, rotation in enumerate(rotations):
            if rotation.get("errors") != []:
                errors.append(
                    f"lesson {index} rotation {rotation_index} errors: {rotation.get('errors')!r}"
                )
            if rotation.get("warnings") != []:
                errors.append(
                    f"lesson {index} rotation {rotation_index} warnings: {rotation.get('warnings')!r}"
                )
            if rotation.get("ambiguous") is not False:
                errors.append(f"lesson {index} rotation {rotation_index} is ambiguous")
            rotation_rivals = rotation.get("rivals")
            if not isinstance(rotation_rivals, dict):
                errors.append(f"lesson {index} rotation {rotation_index} rivals missing")
                continue
            for name in rival_names:
                if rotation_rivals.get(name) != "refuted":
                    errors.append(
                        f"lesson {index} rotation {rotation_index} rival {name} is "
                        f"{rotation_rivals.get(name)!r}, not 'refuted'"
                    )
    for band, count in band_counts.items():
        if count != 100:
            errors.append(f"saved lesson count for {band}: expected 100, got {count}")
    return errors


def bootstrap_runtime(repo_root: Path) -> Path:
    """Put the packet's source-bound runtime first on sys.path."""
    runtime = repo_root / "shared" / "runtime"
    if not (runtime / "puzzle_generators").is_dir():
        raise FileNotFoundError(
            f"source-bound runtime is missing puzzle_generators: {runtime}"
        )
    runtime_text = str(runtime)
    if runtime_text in sys.path:
        sys.path.remove(runtime_text)
    sys.path.insert(0, runtime_text)
    return runtime


def _repo_root_from_task(task_dir: Path) -> Path:
    for ancestor in [task_dir, *task_dir.parents]:
        if (ancestor / "shared" / "data" / "canonical" / "puzzles.jsonl").is_file():
            return ancestor
    raise FileNotFoundError("could not locate repo/shared/data/canonical/puzzles.jsonl")


def _canonical_labeled_pairs(repo_root: Path) -> tuple[list[dict[str, Any]], int]:
    ledger = repo_root / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in ledger.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") != TASK_ID:
            continue
        pairs = [
            pair
            for split in ("train", "test")
            for pair in row.get(split, [])
            if pair.get("output") is not None
        ]
        unlabeled = sum(
            pair.get("output") is None
            for split in ("train", "test")
            for pair in row.get(split, [])
        )
        return pairs, unlabeled
    raise KeyError(f"canonical task {TASK_ID} not found")


def _canonical_fit(
    gen: Any, labeled_pairs: list[dict[str, Any]]
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    results: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for registry_name in (
        "CANONICAL_SHORTCUTS",
        "LESSON_COMPETITORS",
        "SEMANTIC_RIVALS",
    ):
        registry = getattr(gen, registry_name, None)
        if not isinstance(registry, dict) or not registry:
            errors.append(f"{registry_name} is missing or empty")
            continue
        for rival_name, rival in registry.items():
            key = f"{registry_name}:{rival_name}"
            fits: list[bool] = []
            for pair_index, pair in enumerate(labeled_pairs):
                source = copy.deepcopy(pair["input"])
                prediction = rival(source)
                fits.append(prediction == pair["output"])
                if source != pair["input"]:
                    errors.append(f"{key} mutated canonical pair {pair_index}")
            results[key] = {
                "labeled_pairs": len(labeled_pairs),
                "fits_all": all(fits),
                "fit_vector": fits,
            }
            if not all(fits):
                errors.append(f"{key} does not fit every labeled canonical pair")
    return results, errors


def _witness_check(gen: Any, probe: Any) -> tuple[dict[str, Any], list[str]]:
    witness = probe.exact_counterexample()
    authority = probe.left_priority_output(witness)
    errors: list[str] = []
    result: dict[str, Any] = {
        "input": witness,
        "authority_output": authority,
        "rivals": {},
    }
    if gen.rule_mirror(copy.deepcopy(witness)) != authority:
        errors.append("generator rule_mirror disagrees with independent left-priority witness")
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        prediction = rival(copy.deepcopy(witness))
        differs = prediction != authority
        result["rivals"][name] = {"differs": differs, "output": prediction}
        if not differs:
            errors.append(f"witness does not refute canonical rival {name}")
    return result, errors


def verify(report_path: Path, output_path: Path) -> dict[str, Any]:
    task_dir = Path(__file__).resolve().parents[1]
    repo_root = _repo_root_from_task(task_dir)
    bootstrap_runtime(repo_root)
    generator_path = task_dir / "generator.py"
    probe_path = task_dir / "workspace" / "reference_probe.py"
    generator_hash = _sha256(generator_path)
    report_hash = _sha256(report_path)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    gen = _load_module(generator_path, f"census_verify_generator_{TASK_ID}")
    probe = _load_module(probe_path, f"census_verify_probe_{TASK_ID}")

    validation_errors = validate_shared_report(
        report, expected_task_id=TASK_ID, expected_hash=generator_hash
    )
    labeled_pairs, unlabeled_pairs = _canonical_labeled_pairs(repo_root)
    canonical_fit, fit_errors = _canonical_fit(gen, labeled_pairs)
    witness, witness_errors = _witness_check(gen, probe)
    all_errors = validation_errors + fit_errors + witness_errors

    result = {
        "schema": "task-local-lesson-census-verification-v1",
        "task_id": TASK_ID,
        "status": "verified_with_known_shared_reader_limitation"
        if not all_errors
        else "failed",
        "generator_sha256": generator_hash,
        "shared_report": {
            "path": str(report_path),
            "sha256": report_hash,
            "status": report.get("status"),
            "preserved_error": report.get("errors"),
            "summary": report.get("summary"),
            "per_band": report.get("per_band"),
        },
        "known_limitation": {
            "accepted": not validation_errors,
            "exact_error": KNOWN_CANONICAL_ERROR,
            "explanation": (
                "The canonical ledger has a normal unlabeled ARC test query. The shared "
                "census reader requires a nonempty output while computing canonical rival "
                "fit, after the generated census itself has completed."
            ),
            "unlabeled_canonical_pairs": unlabeled_pairs,
        },
        "canonical_labeled_pairs": len(labeled_pairs),
        "canonical_rival_fit": canonical_fit,
        "exact_counterexample": witness,
        "errors": all_errors,
        "limits": [
            "This verifier does not overwrite or relabel the shared census report.",
            "It accepts exactly one known reader error and fails on every other warning, error, ambiguity, missing lesson, missing rotation, source-hash mismatch, or rival shortfall.",
            "Finite declared-rival coverage is evidence against those rivals, not a proof of unique rule identifiability.",
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="shared lesson-census JSON report")
    parser.add_argument("out", type=Path, help="compact task-local verification JSON")
    args = parser.parse_args(argv)
    result = verify(args.report.resolve(), args.out.resolve())
    print(json.dumps({
        "status": result["status"],
        "generator_sha256": result["generator_sha256"],
        "canonical_labeled_pairs": result["canonical_labeled_pairs"],
        "errors": result["errors"],
        "output": str(args.out.resolve()),
    }, indent=2))
    return 0 if result["status"] == "verified_with_known_shared_reader_limitation" else 1


if __name__ == "__main__":
    raise SystemExit(main())
