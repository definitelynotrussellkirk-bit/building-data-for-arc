#!/usr/bin/env python3
"""Racket-backed lesson census for task 2dae2c34641b.

The outer mode stages the repository's supported isolated runtime.  The staged
mode then uses the official semantic gate's ``materialize_lessons`` function,
so every label comes from the selected canonical Racket rule and every lesson
comes from the actual generator sampler.  Rival names are read from the final
generator declarations rather than copied into this tool.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Any

TASK_ID = "2dae2c34641b"
BANDS = ("easy", "medium", "hard")
DEFAULT_SCHEDULE_MODULUS = 3


def _normalize_grid(grid: Any) -> Any:
    if isinstance(grid, list) and grid and isinstance(grid[0], str):
        return [[int(ch) for ch in row] for row in grid]
    return grid


def _equal(left: Any, right: Any) -> bool:
    return _normalize_grid(left) == _normalize_grid(right)


def _grid_hash(grid: Any) -> str:
    payload = json.dumps(_normalize_grid(grid), separators=(",", ":"), sort_keys=False)
    return hashlib.sha256(payload.encode()).hexdigest()


def _lesson_hash(lesson: dict[str, Any]) -> str:
    payload = {
        "demos": [
            {"input": _normalize_grid(pair["input"]), "output": _normalize_grid(pair["output"])}
            for pair in lesson["demos"]
        ],
        "query": {
            "input": _normalize_grid(lesson["query"]["input"]),
            "output": _normalize_grid(lesson["query"].get("output")),
        },
    }
    return hashlib.sha256(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    ).hexdigest()


def summarize_lessons(
    generator,
    lessons: list[dict[str, Any]],
    canonical: list[dict[str, Any]],
    *,
    schedule_modulus: int = DEFAULT_SCHEDULE_MODULUS,
) -> dict[str, Any]:
    """Score actual lessons against declarations without inventing rival names."""
    if schedule_modulus < 1:
        raise ValueError("schedule_modulus must be positive")

    declared_competitors = dict(getattr(generator, "LESSON_COMPETITORS", {}) or {})
    shortcuts = dict(getattr(generator, "CANONICAL_SHORTCUTS", {}) or {})
    scored_competitors = dict(declared_competitors)
    for name, fn in shortcuts.items():
        scored_competitors.setdefault(name, fn)

    competitor_rows = {
        name: {
            "demo_pair_total": 0,
            "demo_pair_disagreements": 0,
            "query_total": 0,
            "query_disagreements": 0,
            "refuted_lessons": 0,
            "survived_demo_lessons": 0,
            "survived_all_lessons": 0,
            "query_discriminating_lessons": 0,
            "errors": [],
        }
        for name in scored_competitors
    }
    shortcut_rows: dict[str, dict[str, Any]] = {}
    for name, fn in shortcuts.items():
        fits = 0
        errors: list[str] = []
        for index, pair in enumerate(canonical):
            try:
                fits += int(_equal(fn(copy.deepcopy(pair["input"])), pair["output"]))
            except Exception as exc:  # evidence must retain a broken declaration
                errors.append(f"pair {index}: {type(exc).__name__}: {exc}")
        shortcut_rows[name] = {
            "canonical_pairs": len(canonical),
            "canonical_pairs_fit": fits,
            "fits_all_canonical_pairs": fits == len(canonical) and not errors,
            "errors": errors,
        }

    per_band: dict[str, Counter] = defaultdict(Counter)
    residue_counts: Counter[int] = Counter()
    residue_by_band: dict[str, Counter[int]] = defaultdict(Counter)
    witness_hits: Counter[str] = Counter()
    all_input_hashes: list[str] = []
    lesson_hashes: list[str] = []
    hook_errors: list[dict[str, Any]] = []
    unidentifiable: list[dict[str, Any]] = []
    domain_failures: list[dict[str, Any]] = []
    seeds_by_band: dict[str, list[int]] = defaultdict(list)
    starts_by_band: dict[str, list[int]] = defaultdict(list)

    witnesses = dict(getattr(generator, "SEMANTIC_WITNESSES", {}) or {})
    hook = getattr(generator, "lesson_identifiable", None)
    checker = getattr(generator, "self_check", None)

    for lesson in lessons:
        band = str(lesson.get("band", "unknown"))
        sample_index = int(lesson.get("sample_index", 0))
        seed = int(lesson.get("seed", 0))
        per_band[band]["lessons"] += 1
        seeds_by_band[band].append(seed)
        starts_by_band[band].append(sample_index)
        residue = sample_index % schedule_modulus
        residue_counts[residue] += 1
        residue_by_band[band][residue] += 1
        lesson_hashes.append(_lesson_hash(lesson))

        pairs = [*lesson["demos"], lesson["query"]]
        for pair_index, pair in enumerate(pairs):
            grid = pair["input"]
            all_input_hashes.append(_grid_hash(grid))
            if callable(checker):
                try:
                    reasons = checker(copy.deepcopy(grid))
                except Exception as exc:
                    reasons = [f"self_check raised {type(exc).__name__}: {exc}"]
                if reasons:
                    domain_failures.append(
                        {
                            "replay": lesson.get("replay"),
                            "pair_index": pair_index,
                            "reasons": list(reasons)[:5],
                        }
                    )
            for name, predicate in witnesses.items():
                try:
                    witness_hits[name] += int(bool(predicate(copy.deepcopy(grid))))
                except Exception as exc:
                    domain_failures.append(
                        {
                            "replay": lesson.get("replay"),
                            "pair_index": pair_index,
                            "reasons": [f"witness {name!r} raised {type(exc).__name__}: {exc}"],
                        }
                    )

        for name, rival in scored_competitors.items():
            row = competitor_rows[name]
            demo_fits = True
            try:
                for demo in lesson["demos"]:
                    row["demo_pair_total"] += 1
                    agrees = _equal(rival(copy.deepcopy(demo["input"])), demo["output"])
                    row["demo_pair_disagreements"] += int(not agrees)
                    demo_fits = demo_fits and agrees
                row["query_total"] += 1
                query_agrees = _equal(
                    rival(copy.deepcopy(lesson["query"]["input"])),
                    lesson["query"]["output"],
                )
                row["query_disagreements"] += int(not query_agrees)
                if demo_fits:
                    row["survived_demo_lessons"] += 1
                    if query_agrees:
                        row["survived_all_lessons"] += 1
                    else:
                        row["query_discriminating_lessons"] += 1
                else:
                    row["refuted_lessons"] += 1
            except Exception as exc:
                row["errors"].append(
                    f"{lesson.get('replay')}: {type(exc).__name__}: {exc}"
                )

        if callable(hook):
            try:
                reasons = hook(copy.deepcopy(lesson["demos"]), copy.deepcopy(lesson["query"]))
                if not isinstance(reasons, list):
                    raise TypeError(f"returned {type(reasons).__name__}, expected list[str]")
            except Exception as exc:
                hook_errors.append(
                    {"replay": lesson.get("replay"), "error": f"{type(exc).__name__}: {exc}"}
                )
            else:
                if reasons:
                    unidentifiable.append(
                        {"replay": lesson.get("replay"), "reasons": reasons[:5]}
                    )
                else:
                    per_band[band]["identifiable"] += 1

    unique_inputs = set(all_input_hashes)
    unique_lessons = set(lesson_hashes)
    band_report: dict[str, Any] = {}
    for band in sorted(per_band):
        seeds = seeds_by_band[band]
        starts = starts_by_band[band]
        band_report[band] = {
            **dict(per_band[band]),
            "seed_count": len(seeds),
            "seed_min": min(seeds) if seeds else None,
            "seed_max": max(seeds) if seeds else None,
            "sample_index_min": min(starts) if starts else None,
            "sample_index_max": max(starts) if starts else None,
            "sample_index_values": starts,
            "seed_values": seeds,
            "start_residue_counts": {
                str(i): residue_by_band[band][i] for i in range(schedule_modulus)
            },
        }

    return {
        "lessons_materialized": len(lessons),
        "demos_per_lesson": (
            len(lessons[0]["demos"]) if lessons else getattr(generator, "EXAMPLES_NEEDED", None)
        ),
        "queries_per_lesson": 1,
        "input_occurrences": len(all_input_hashes),
        "unique_input_count": len(unique_inputs),
        "duplicate_input_occurrences": len(all_input_hashes) - len(unique_inputs),
        "unique_lesson_count": len(unique_lessons),
        "duplicate_lesson_occurrences": len(lesson_hashes) - len(unique_lessons),
        "bands": band_report,
        "schedule_modulus": schedule_modulus,
        "sample_start_residue_counts": {
            str(i): residue_counts[i] for i in range(schedule_modulus)
        },
        "competitors_declared": sorted(declared_competitors),
        "competitors_scored": sorted(scored_competitors),
        "canonical_shortcuts_declared": sorted(shortcuts),
        "competitor_results": competitor_rows,
        "canonical_shortcut_results": shortcut_rows,
        "witness_hits": {name: witness_hits[name] for name in sorted(witnesses)},
        "unidentifiable_lessons": len(unidentifiable),
        "unidentifiable_examples": unidentifiable[:10],
        "hook_error_lessons": len(hook_errors),
        "hook_error_examples": hook_errors[:10],
        "domain_validation_failures": len(domain_failures),
        "domain_failure_examples": domain_failures[:10],
    }


def _load_generator(path: Path):
    spec = importlib.util.spec_from_file_location(f"lesson_probe_generator_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _runtime_probe(per_band: int, schedule_modulus: int) -> dict[str, Any]:
    from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash
    from scripts.generator_module_loader import load_module_from_path
    from scripts.generator_semantic_gate import (
        BANDS as OFFICIAL_BANDS,
        LESSON_SAMPLE_STRIDE,
        materialize_lessons,
    )

    if tuple(OFFICIAL_BANDS) != BANDS:
        raise RuntimeError(f"official band set changed: {OFFICIAL_BANDS!r}")
    generator_path = Path("puzzle_generators") / "per_puzzle" / TASK_ID / "generator.py"
    generator = load_module_from_path(f"lesson_probe_{TASK_ID}", generator_path)
    count = per_band * len(BANDS)
    n_demos = int(getattr(generator, "EXAMPLES_NEEDED", 3))
    lessons, materialize_errors = materialize_lessons(
        TASK_ID,
        count,
        n_demos=n_demos,
        bands=BANDS,
        pass_difficulty=True,
        legacy=False,
    )
    report = summarize_lessons(
        generator,
        lessons,
        canonical_pairs(TASK_ID),
        schedule_modulus=schedule_modulus,
    )
    report.update(
        {
            "schema": "2dae2c34641b-lesson-probe-v1",
            "task_id": TASK_ID,
            "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
            "declared_rule_hash": getattr(generator, "RULE_HASH", None),
            "canonical_rule_hash": canonical_rule_hash(TASK_ID),
            "axes": copy.deepcopy(getattr(generator, "AXES", {})),
            "strict_fraction_declared": getattr(generator, "MIN_STRICT_FRAC", None),
            "requested_per_band": per_band,
            "requested_total": count,
            "official_sampler": (
                "scripts.generator_semantic_gate.materialize_lessons -> "
                "puzzle_generators.runner.run_one; canonical Racket outputs"
            ),
            "lesson_sample_stride": LESSON_SAMPLE_STRIDE,
            "materialize_errors": materialize_errors,
            "materialized_per_band": {
                band: report["bands"].get(band, {}).get("lessons", 0) for band in BANDS
            },
            "domain_limits": {
                "bands": list(BANDS),
                "axes": copy.deepcopy(getattr(generator, "AXES", {})),
                "examples_needed": n_demos,
                "one_query_per_lesson": True,
                "claim_scope": (
                    "finite pinned census only; no claim of universal induction or exhaustive seeds"
                ),
            },
        }
    )

    competitor_failures = {
        name: row["survived_demo_lessons"]
        for name, row in report["competitor_results"].items()
        if row["survived_demo_lessons"] or row["errors"]
    }
    bad_shortcuts = [
        name
        for name, row in report["canonical_shortcut_results"].items()
        if not row["fits_all_canonical_pairs"]
    ]
    per_band_ok = all(
        report["materialized_per_band"].get(band) == per_band for band in BANDS
    )
    report["passed"] = not any(
        (
            materialize_errors,
            report["hook_error_lessons"],
            report["unidentifiable_lessons"],
            report["domain_validation_failures"],
            competitor_failures,
            bad_shortcuts,
            not per_band_ok,
            report["declared_rule_hash"] != report["canonical_rule_hash"],
        )
    )
    report["failure_summary"] = {
        "materialize_errors": len(materialize_errors),
        "hook_error_lessons": report["hook_error_lessons"],
        "unidentifiable_lessons": report["unidentifiable_lessons"],
        "domain_validation_failures": report["domain_validation_failures"],
        "competitor_survivors_or_errors": competitor_failures,
        "canonical_shortcuts_not_fitting_all_canonical_pairs": bad_shortcuts,
        "per_band_count_mismatch": not per_band_ok,
        "rule_hash_mismatch": report["declared_rule_hash"] != report["canonical_rule_hash"],
    }
    return report


def _outer_probe(args: argparse.Namespace) -> int:
    repo_root = Path(__file__).resolve().parents[3]
    generator_path = repo_root / "generators" / TASK_ID / "generator.py"
    source_generator_hash = hashlib.sha256(generator_path.read_bytes()).hexdigest()
    probe_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()

    sys.path.insert(0, str(repo_root / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    with tempfile.TemporaryDirectory(prefix=f"{TASK_ID}-lesson-probe-") as directory:
        stage = Path(directory)
        receipt = prepare_runtime(Catalog(repo_root), stage, TASK_ID)
        staged_script = stage / "lesson_probe.py"
        shutil.copy2(Path(__file__), staged_script)
        staged_output = stage / "lesson-report.json"
        command = [
            sys.executable,
            "-B",
            staged_script.name,
            "--in-runtime",
            "--per-band",
            str(args.per_band),
            "--schedule-modulus",
            str(args.schedule_modulus),
            "--out",
            staged_output.name,
        ]
        result = run_process(command, stage, timeout=args.timeout)
        if result["timed_out"] or result["exit_code"] not in (0, 1):
            raise RuntimeError(
                "staged lesson probe failed: "
                f"exit={result['exit_code']} timeout={result['timed_out']} "
                f"stderr={result['stderr'][-2000:]}"
            )
        if not staged_output.is_file():
            raise RuntimeError("staged lesson probe produced no report")
        report = json.loads(staged_output.read_text())
        report.update(
            {
                "probe_sha256": probe_hash,
                "source_generator_sha256": source_generator_hash,
                "runtime_manifest_sha256": hashlib.sha256(
                    json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode()
                ).hexdigest(),
                "command": [str(item) for item in command],
                "working_directory": str(stage),
                "source_working_directory": str(Path.cwd()),
                "staged_exit_code": result["exit_code"],
                "staged_timed_out": result["timed_out"],
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
                "passed": report["passed"],
                "lessons_materialized": report["lessons_materialized"],
                "materialized_per_band": report["materialized_per_band"],
                "unique_input_count": report["unique_input_count"],
                "unique_lesson_count": report["unique_lesson_count"],
                "competitor_survivors": {
                    name: row["survived_demo_lessons"]
                    for name, row in report["competitor_results"].items()
                },
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if report["passed"] else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--schedule-modulus", type=int, default=DEFAULT_SCHEDULE_MODULUS)
    parser.add_argument("--timeout", type=float, default=1800.0)
    parser.add_argument("--in-runtime", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.per_band < 1:
        parser.error("--per-band must be positive")
    if args.schedule_modulus < 1:
        parser.error("--schedule-modulus must be positive")
    if args.timeout <= 0:
        parser.error("--timeout must be positive")

    if args.in_runtime:
        report = _runtime_probe(args.per_band, args.schedule_modulus)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("x", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, sort_keys=True)
            handle.write("\n")
        return 0 if report["passed"] else 1
    return _outer_probe(args)


if __name__ == "__main__":
    raise SystemExit(main())
