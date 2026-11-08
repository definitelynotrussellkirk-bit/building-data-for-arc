#!/usr/bin/env python3
"""Source-bound lesson census for audit target 5b3c69ad7276.

Materializes lessons with the repository's official semantic-gate sampler and
canonical Racket oracle, then scores the plausible rival: draw the full cross
except when the single seed is in a corner, where the rival leaves it unchanged.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Any

TASK_ID = "5b3c69ad7276"
BANDS = ("easy", "medium", "hard")
N_DEMOS = 3


def _normalize(grid: Any) -> list[list[int]]:
    if grid and isinstance(grid[0], str):
        return [[int(ch) for ch in row] for row in grid]
    return [list(row) for row in grid]


def _hash_grid(grid: Any) -> str:
    return hashlib.sha256(
        json.dumps(_normalize(grid), separators=(",", ":")).encode()
    ).hexdigest()


def _seed_info(grid: Any) -> tuple[int, int, int, str]:
    grid = _normalize(grid)
    cells = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    if len(cells) != 1:
        raise ValueError(f"expected one seed, found {len(cells)}")
    row, col, color = cells[0]
    height, width = len(grid), len(grid[0])
    if row in (0, height - 1) and col in (0, width - 1):
        kind = "corner"
    elif row in (0, height - 1) or col in (0, width - 1):
        kind = "edge"
    else:
        kind = "interior"
    return row, col, color, kind


def _cross(grid: Any) -> list[list[int]]:
    grid = _normalize(grid)
    row, col, color, _ = _seed_info(grid)
    return [
        [color if r == row or c == col else 0 for c in range(len(grid[0]))]
        for r in range(len(grid))
    ]


def _rival(grid: Any) -> list[list[int]]:
    normalized = _normalize(grid)
    *_, kind = _seed_info(normalized)
    return copy.deepcopy(normalized) if kind == "corner" else _cross(normalized)


def _runtime_probe(per_band: int) -> dict[str, Any]:
    from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash
    from scripts.generator_module_loader import load_module_from_path
    from scripts.generator_semantic_gate import (
        LESSON_SAMPLE_STRIDE,
        materialize_lessons,
    )

    generator_path = Path("puzzle_generators") / "per_puzzle" / TASK_ID / "generator.py"
    generator = load_module_from_path(f"audit_lesson_probe_{TASK_ID}", generator_path)
    lessons, errors = materialize_lessons(
        TASK_ID,
        per_band * len(BANDS),
        n_demos=N_DEMOS,
        n_queries=1,
        bands=BANDS,
        pass_difficulty=True,
        legacy=False,
    )

    canonical_rows = []
    for index, pair in enumerate(canonical_pairs(TASK_ID)):
        input_grid = _normalize(pair["input"])
        canonical_rows.append(
            {
                "pair_index": index,
                "anchor_kind": _seed_info(input_grid)[3],
                "rival_fits": _rival(input_grid) == _normalize(pair["output"]),
            }
        )

    by_band: dict[str, dict[str, int]] = {
        band: {
            "lessons": 0,
            "demo_corner_occurrences": 0,
            "query_corner_occurrences": 0,
            "rival_survived_demos": 0,
            "query_discriminating_lessons": 0,
            "rival_survived_entire_lesson": 0,
            "domain_failures": 0,
        }
        for band in BANDS
    }
    unique_inputs: set[str] = set()
    discriminating_examples: list[dict[str, Any]] = []
    domain_failures: list[dict[str, Any]] = []

    for lesson in lessons:
        band = lesson["band"]
        row = by_band[band]
        row["lessons"] += 1
        demo_fits = True
        demo_kinds = []
        for pair_index, pair in enumerate(lesson["demos"]):
            grid = _normalize(pair["input"])
            unique_inputs.add(_hash_grid(grid))
            kind = _seed_info(grid)[3]
            demo_kinds.append(kind)
            row["demo_corner_occurrences"] += int(kind == "corner")
            reasons = generator.self_check(copy.deepcopy(grid))
            if reasons:
                row["domain_failures"] += 1
                if len(domain_failures) < 10:
                    domain_failures.append(
                        {
                            "replay": lesson["replay"],
                            "pair_index": pair_index,
                            "reasons": reasons,
                        }
                    )
            demo_fits = demo_fits and (
                _rival(grid) == _normalize(pair["output"])
            )

        query_grid = _normalize(lesson["query"]["input"])
        unique_inputs.add(_hash_grid(query_grid))
        query_kind = _seed_info(query_grid)[3]
        row["query_corner_occurrences"] += int(query_kind == "corner")
        query_fits = _rival(query_grid) == _normalize(lesson["query"]["output"])
        reasons = generator.self_check(copy.deepcopy(query_grid))
        if reasons:
            row["domain_failures"] += 1
            if len(domain_failures) < 10:
                domain_failures.append(
                    {
                        "replay": lesson["replay"],
                        "pair_index": N_DEMOS,
                        "reasons": reasons,
                    }
                )

        if demo_fits:
            row["rival_survived_demos"] += 1
            if query_fits:
                row["rival_survived_entire_lesson"] += 1
            else:
                row["query_discriminating_lessons"] += 1
                if len(discriminating_examples) < 10:
                    discriminating_examples.append(
                        {
                            "replay": lesson["replay"],
                            "demo_anchor_kinds": demo_kinds,
                            "query_anchor_kind": query_kind,
                            "query_input": query_grid,
                            "racket_output": _normalize(lesson["query"]["output"]),
                            "rival_output": _rival(query_grid),
                        }
                    )

    report = {
        "schema": "arcpuzzles-audit-lesson-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "declared_rule_hash": getattr(generator, "RULE_HASH", None),
        "canonical_rule_hash": canonical_rule_hash(TASK_ID),
        "official_sampler": (
            "scripts.generator_semantic_gate.materialize_lessons -> "
            "puzzle_generators.runner.run_one; canonical Racket outputs"
        ),
        "lesson_sample_stride": LESSON_SAMPLE_STRIDE,
        "n_demos": N_DEMOS,
        "n_queries": 1,
        "requested_per_band": per_band,
        "requested_total": per_band * len(BANDS),
        "lessons_materialized": len(lessons),
        "materialize_errors": errors,
        "unique_input_count": len(unique_inputs),
        "input_occurrences": len(lessons) * (N_DEMOS + 1),
        "canonical_rival_fit": canonical_rows,
        "rival_fits_all_canonical_pairs": bool(canonical_rows)
        and all(row["rival_fits"] for row in canonical_rows),
        "bands": by_band,
        "totals": {
            key: sum(row[key] for row in by_band.values())
            for key in next(iter(by_band.values()))
        },
        "discriminating_examples": discriminating_examples,
        "domain_failure_examples": domain_failures,
        "claim_scope": (
            "finite pinned census only; it demonstrates actual sampler failures, "
            "not a universal induction claim"
        ),
    }
    report["passed_as_audit_reproducer"] = (
        not errors
        and report["rival_fits_all_canonical_pairs"]
        and report["totals"]["query_discriminating_lessons"] > 0
        and report["totals"]["domain_failures"] == 0
        and len(lessons) == per_band * len(BANDS)
        and report["declared_rule_hash"] == report["canonical_rule_hash"]
    )
    return report


def _outer_probe(args: argparse.Namespace) -> int:
    packet_root = Path(__file__).resolve().parents[3]
    repo_root = packet_root / "repo"
    source = repo_root / "generators" / TASK_ID / "generator.py"
    probe_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()

    sys.path.insert(0, str(repo_root / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    with tempfile.TemporaryDirectory(prefix=f"{TASK_ID}-audit-probe-") as directory:
        stage = Path(directory)
        receipt = prepare_runtime(Catalog(repo_root), stage, TASK_ID)
        staged_script = stage / "lesson_probe.py"
        shutil.copy2(Path(__file__), staged_script)
        staged_output = stage / "report.json"
        command = [
            sys.executable,
            "-B",
            staged_script.name,
            "--in-runtime",
            "--per-band",
            str(args.per_band),
            "--out",
            staged_output.name,
        ]
        result = run_process(command, stage, timeout=args.timeout)
        if result["timed_out"] or result["exit_code"] not in (0, 1):
            raise RuntimeError(
                f"staged probe failed: exit={result['exit_code']} "
                f"timeout={result['timed_out']} stderr={result['stderr'][-2000:]}"
            )
        report = json.loads(staged_output.read_text())
        report.update(
            {
                "probe_sha256": probe_hash,
                "source_generator_sha256": source_hash,
                "runtime_manifest_sha256": hashlib.sha256(
                    json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode()
                ).hexdigest(),
                "staged_command": command,
                "staged_exit_code": result["exit_code"],
                "staged_timed_out": result["timed_out"],
                "source_cwd": str(Path.cwd()),
                "staged_cwd": str(stage),
                "staged_stdout_tail": result["stdout"][-2000:],
                "staged_stderr_tail": result["stderr"][-2000:],
            }
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(
        json.dumps(
            {
                "passed_as_audit_reproducer": report["passed_as_audit_reproducer"],
                "lessons_materialized": report["lessons_materialized"],
                "unique_input_count": report["unique_input_count"],
                "rival_fits_all_canonical_pairs": report[
                    "rival_fits_all_canonical_pairs"
                ],
                "totals": report["totals"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if report["passed_as_audit_reproducer"] else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--timeout", type=float, default=1800)
    parser.add_argument("--in-runtime", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.per_band < 1:
        parser.error("--per-band must be positive")
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    if args.in_runtime:
        report = _runtime_probe(args.per_band)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("x", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, sort_keys=True)
            handle.write("\n")
        return 0 if report["passed_as_audit_reproducer"] else 1
    return _outer_probe(args)


if __name__ == "__main__":
    raise SystemExit(main())
