#!/usr/bin/env python3
"""Verify source-bound per-stage battery receipts without inventing a verdict.

This helper is for review environments where each battery stage completed in a
separate portable runtime.  It validates that a complete set of successful
receipts and ``.ok`` markers belongs to one exact battery subject and records the
artifact hashes.  It deliberately does *not* synthesize a battery summary or
journal row: the official ``run_generator_battery.sh ... --resume`` reconciler
must still import the receipts and produce the aggregate verdict.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Iterable, Sequence


STAGES: tuple[str, ...] = (
    "lint",
    "selfcheck",
    "rule_smoke",
    "defect_lint",
    "dist_gate",
    "profile_floor",
    "semantic_gate",
    "diversity",
    "override",
    "grammar",
    "racket_lint",
    "authority_sync",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _checks_dir(source: Path) -> Path:
    nested = source / "checks"
    return nested if nested.is_dir() else source


def _read_receipt(path: Path) -> tuple[dict | None, str | None]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return None, f"unreadable receipt {path}: {exc}"
    if not isinstance(value, dict):
        return None, f"receipt is not an object: {path}"
    return value, None


def collect_receipts(
    *,
    task: str,
    phase: str,
    source_dirs: Iterable[Path | str],
    stages: Sequence[str] = STAGES,
    expected_subject: str | None = None,
) -> dict:
    """Return a hash-bound manifest of successful stage receipts.

    A stage is selectable only when its child receipt exits zero, did not time
    out, and has a same-subject ``.ok`` marker.  Duplicate valid receipts are
    harmless; the latest ``utc_end`` (then lexicographic source path) is selected
    deterministically and every candidate remains listed in the report.
    """
    sources = [Path(item).resolve() for item in source_dirs]
    problems: list[str] = []
    candidates: dict[str, list[dict]] = {stage: [] for stage in stages}

    if not task or not phase:
        raise ValueError("task and phase must be non-empty")
    if not sources:
        raise ValueError("at least one source directory is required")

    for source in sources:
        checks = _checks_dir(source)
        if not checks.is_dir():
            problems.append(f"source has no checks directory: {source}")
            continue
        for stage in stages:
            prefix = checks / f"{task}_{phase}_{stage}"
            receipt_path = prefix.with_suffix(".receipt")
            if not receipt_path.is_file():
                continue
            receipt, error = _read_receipt(receipt_path)
            if error:
                problems.append(error)
                continue
            assert receipt is not None
            ok_path = prefix.with_suffix(".ok")
            log_path = prefix.with_suffix(".log")
            marker = ok_path.read_text(encoding="utf-8").strip() if ok_path.is_file() else None
            candidates[stage].append(
                {
                    "stage": stage,
                    "source_dir": str(source),
                    "receipt_path": str(receipt_path),
                    "receipt_sha256": _sha256(receipt_path),
                    "ok_path": str(ok_path) if ok_path.is_file() else None,
                    "ok_sha256": _sha256(ok_path) if ok_path.is_file() else None,
                    "log_path": str(log_path) if log_path.is_file() else None,
                    "log_sha256": _sha256(log_path) if log_path.is_file() else None,
                    "subject_sha16": receipt.get("subject_sha16"),
                    "exit": receipt.get("exit"),
                    "timed_out": bool(receipt.get("timed_out")),
                    "utc_end": receipt.get("utc_end"),
                    "run_id": receipt.get("run_id"),
                    "ok_marker": marker,
                }
            )

    successful_subjects = sorted(
        {
            row["subject_sha16"]
            for rows in candidates.values()
            for row in rows
            if row["exit"] == 0
            and not row["timed_out"]
            and row["subject_sha16"]
            and row["ok_marker"] == row["subject_sha16"]
        }
    )
    subject = expected_subject
    if subject is None:
        if len(successful_subjects) == 1:
            subject = successful_subjects[0]
        elif not successful_subjects:
            problems.append("no successful source-bound receipt/marker pair was found")
        else:
            problems.append(
                "multiple successful battery subjects found; pass --expected-subject: "
                + ", ".join(successful_subjects)
            )
    elif subject not in successful_subjects:
        problems.append(f"expected subject {subject!r} has no successful receipt/marker pair")

    selected: list[dict] = []
    missing: list[str] = []
    rejected: list[dict] = []
    for stage in stages:
        valid: list[dict] = []
        for row in candidates[stage]:
            reasons = []
            if subject is None or row["subject_sha16"] != subject:
                reasons.append("different subject")
            if row["exit"] != 0:
                reasons.append(f"exit={row['exit']!r}")
            if row["timed_out"]:
                reasons.append("timed out")
            if row["ok_marker"] != row["subject_sha16"]:
                reasons.append("missing or mismatched .ok marker")
            if row["log_path"] is None:
                reasons.append("missing log")
            if reasons:
                rejected.append({**row, "reasons": reasons})
            else:
                valid.append(row)
        if not valid:
            missing.append(stage)
            continue
        valid.sort(key=lambda row: (row.get("utc_end") or "", row["source_dir"]))
        chosen = dict(valid[-1])
        chosen["duplicate_valid_candidates"] = len(valid) - 1
        selected.append(chosen)

    if rejected:
        problems.append(f"{len(rejected)} receipt candidate(s) were rejected; inspect rejected_candidates")

    complete = bool(subject) and not missing and len(selected) == len(stages)
    return {
        "schema": "arcpuzzles-stage-receipt-manifest-v1",
        "task_id": task,
        "phase": phase,
        "subject_sha16": subject,
        "expected_stages": list(stages),
        "source_dirs": [str(path) for path in sources],
        "complete": complete,
        "selected": selected,
        "missing_stages": missing,
        "problems": problems,
        "rejected_candidates": rejected,
        "official_next_step": (
            "Run the official battery --resume reconciler in a prepared runtime after "
            "copying the selected artifacts; this manifest is not an aggregate verdict."
        ),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", required=True)
    parser.add_argument("--phase", required=True)
    parser.add_argument("--source", action="append", required=True, type=Path)
    parser.add_argument("--expected-subject")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    if args.out.exists():
        raise SystemExit(f"refusing to overwrite existing report: {args.out}")
    report = collect_receipts(
        task=args.task,
        phase=args.phase,
        source_dirs=args.source,
        expected_subject=args.expected_subject,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "complete": report["complete"],
                "subject_sha16": report["subject_sha16"],
                "selected": len(report["selected"]),
                "missing_stages": report["missing_stages"],
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )
    return 0 if report["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
