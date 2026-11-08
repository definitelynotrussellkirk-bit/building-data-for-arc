#!/usr/bin/env python3
"""Source-bound lesson probe for declared shortcuts and competitors.

The probe deliberately reads ``CANONICAL_SHORTCUTS``, ``LESSON_COMPETITORS``
and ``SEMANTIC_WITNESSES`` from the selected generator.  It does not carry a
second hand-maintained rival list.  Authoritative labels are obtained only via
``python -m arcpuzzles apply`` and every batch is checked against the exact
selected generator hash and executed Racket rule hash.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_TASK_ID = Path(__file__).resolve().parents[1].name
DEFAULT_BANDS = ("easy", "medium", "hard")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _grid_key(grid: Any) -> str:
    payload = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return _sha256_bytes(payload)


def _same_grid(left: Any, right: Any) -> bool:
    try:
        return [list(row) for row in left] == [list(row) for row in right]
    except TypeError:
        return False


def _stable_seed(task_id: str, band: str, lesson_index: int) -> int:
    digest = hashlib.sha256(
        f"{task_id}|lesson-rival-probe-v1|{band}|{lesson_index}".encode()
    ).digest()
    return int.from_bytes(digest[:8], "big")


def build_lesson_plan(
    *,
    task_id: str,
    band: str,
    lessons: int,
    examples_per_lesson: int,
    schedule_period: int,
) -> list[dict[str, Any]]:
    """Build deterministic, nonoverlapping consecutive-example lessons.

    A stride equal to ``examples_per_lesson`` makes all generated inputs unique
    by sample index.  Five-example lessons against a four-slot schedule advance
    the start residue by one each lesson, so all cyclic starts are exercised.
    """
    if lessons <= 0:
        raise ValueError("lessons must be positive")
    if examples_per_lesson < 2:
        raise ValueError("examples_per_lesson must include demos and a query")
    if schedule_period <= 0:
        raise ValueError("schedule_period must be positive")

    plan = []
    for lesson_index in range(lessons):
        start = lesson_index * examples_per_lesson
        indices = list(range(start, start + examples_per_lesson))
        plan.append(
            {
                "lesson_index": lesson_index,
                "seed": _stable_seed(task_id, band, lesson_index),
                "sample_indices": indices,
                "start_residue": start % schedule_period,
            }
        )
    return plan


def _load_module(path: Path):
    spec = importlib.util.spec_from_file_location(
        f"lesson_probe_generator_{path.parent.name}", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_pairs(task_id: str) -> list[dict[str, Any]]:
    source = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in source.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") != task_id:
            continue
        pairs: list[dict[str, Any]] = []
        for split in ("train", "test"):
            raw = row.get(split, [])
            if isinstance(raw, dict):
                raw = [raw]
            for pair in raw:
                pairs.append(
                    {
                        "split": split,
                        "input": pair["input"],
                        "output": pair["output"],
                    }
                )
        return pairs
    raise RuntimeError(f"canonical task {task_id!r} not found in {source}")


def _callable_map(module: Any, name: str) -> dict[str, Callable]:
    value = getattr(module, name, {})
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise TypeError(f"{name} must be a dict, got {type(value).__name__}")
    bad = [key for key, fn in value.items() if not isinstance(key, str) or not callable(fn)]
    if bad:
        raise TypeError(f"{name} contains non-callable or non-string entries: {bad!r}")
    return dict(value)


def _apply_batches(
    *,
    task_id: str,
    grids: list[Any],
    out_dir: Path,
    expected_generator_sha256: str,
    expected_rule_hash: str,
    batch_size: int,
) -> tuple[list[Any], list[dict[str, Any]]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Any] = []
    receipts: list[dict[str, Any]] = []

    for batch_index, offset in enumerate(range(0, len(grids), batch_size)):
        chunk = grids[offset : offset + batch_size]
        input_path = out_dir / f"batch-{batch_index:03d}-input.json"
        output_path = out_dir / f"batch-{batch_index:03d}-racket.json"
        input_path.write_text(json.dumps({"inputs": chunk}, separators=(",", ":")) + "\n")
        output_path.unlink(missing_ok=True)
        command = [
            sys.executable,
            "-m",
            "arcpuzzles",
            "apply",
            task_id,
            "--input",
            str(input_path),
            "--out",
            str(output_path),
        ]
        completed = subprocess.run(
            command,
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                f"authority batch {batch_index} failed with exit {completed.returncode}: "
                f"stdout={completed.stdout[-1000:]!r} stderr={completed.stderr[-1000:]!r}"
            )
        payload = json.loads(output_path.read_text())
        if payload.get("generator_sha256") != expected_generator_sha256:
            raise RuntimeError(
                f"batch {batch_index} generator hash {payload.get('generator_sha256')} "
                f"!= source {expected_generator_sha256}"
            )
        if payload.get("executed_rule_hash") != expected_rule_hash:
            raise RuntimeError(
                f"batch {batch_index} rule hash {payload.get('executed_rule_hash')} "
                f"!= declared {expected_rule_hash}"
            )
        rows = payload.get("results") or []
        if len(rows) != len(chunk):
            raise RuntimeError(
                f"batch {batch_index} returned {len(rows)} outputs for {len(chunk)} inputs"
            )
        for row in rows:
            if row.get("error") or not row.get("valid_output"):
                raise RuntimeError(f"authority batch {batch_index} invalid row: {row}")
            outputs.append(row["output"])
        receipts.append(
            {
                "batch_index": batch_index,
                "input_count": len(chunk),
                "input_path": str(input_path.relative_to(REPO_ROOT.parent)),
                "output_path": str(output_path.relative_to(REPO_ROOT.parent)),
                "output_sha256": _sha256_file(output_path),
                "executed_rule_hash": payload["executed_rule_hash"],
                "generator_sha256": payload["generator_sha256"],
                "elapsed_seconds": payload.get("elapsed_seconds"),
            }
        )
    return outputs, receipts


def _canonical_shortcut_results(
    shortcuts: dict[str, Callable], canonical_pairs: list[dict[str, Any]]
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, rival in shortcuts.items():
        matches = []
        for index, pair in enumerate(canonical_pairs):
            actual = rival(pair["input"])
            matches.append(
                {
                    "pair_index": index,
                    "split": pair["split"],
                    "matches": _same_grid(actual, pair["output"]),
                }
            )
        result[name] = {
            "matched": sum(row["matches"] for row in matches),
            "total": len(matches),
            "fits_every_canonical_pair": all(row["matches"] for row in matches),
            "pairs": matches,
        }
    return result


def _score_band(
    *,
    module: Any,
    band: str,
    plan: list[dict[str, Any]],
    grids: list[Any],
    outputs: list[Any],
    witnesses: dict[str, Callable],
    competitors: dict[str, Callable],
    demos_per_lesson: int,
) -> dict[str, Any]:
    if len(grids) != len(outputs):
        raise ValueError("input/output count mismatch")
    examples_per_lesson = demos_per_lesson + 1
    witness_hits = Counter()
    competitor_disagreements = Counter()
    per_example: list[dict[str, Any]] = []

    for grid, authoritative in zip(grids, outputs):
        fired = []
        for name, predicate in witnesses.items():
            value = predicate(grid)
            if type(value) is not bool:
                raise TypeError(f"witness {name!r} returned {type(value).__name__}")
            if value:
                witness_hits[name] += 1
                fired.append(name)
        disagreements = []
        for name, rival in competitors.items():
            if not _same_grid(rival(grid), authoritative):
                competitor_disagreements[name] += 1
                disagreements.append(name)
        per_example.append(
            {
                "witnesses": fired,
                "competitor_disagreements": disagreements,
            }
        )

    lesson_stats = {
        name: {
            "refuted_by_demos": 0,
            "survived_all_demos": 0,
            "survived_demos_and_disagreed_on_query": 0,
            "survived_demos_and_matched_query": 0,
        }
        for name in competitors
    }
    witness_demo_coverage = Counter()
    schedule_sequences = Counter()
    for lesson_index, lesson in enumerate(plan):
        begin = lesson_index * examples_per_lesson
        demo_rows = per_example[begin : begin + demos_per_lesson]
        query_row = per_example[begin + demos_per_lesson]
        for name in witnesses:
            if any(name in row["witnesses"] for row in demo_rows):
                witness_demo_coverage[name] += 1
        profiles = tuple(
            module.schedule_profile(
                lesson["seed"], sample_index, difficulty=band
            )
            for sample_index in lesson["sample_indices"]
        )
        schedule_sequences[repr(profiles)] += 1
        for name in competitors:
            survives = all(
                name not in row["competitor_disagreements"] for row in demo_rows
            )
            query_disagrees = name in query_row["competitor_disagreements"]
            stats = lesson_stats[name]
            if survives:
                stats["survived_all_demos"] += 1
                if query_disagrees:
                    stats["survived_demos_and_disagreed_on_query"] += 1
                else:
                    stats["survived_demos_and_matched_query"] += 1
            else:
                stats["refuted_by_demos"] += 1

    return {
        "band": band,
        "lessons": len(plan),
        "demos_per_lesson": demos_per_lesson,
        "queries_per_lesson": 1,
        "generated_inputs": len(grids),
        "unique_inputs": len({_grid_key(grid) for grid in grids}),
        "schedule_start_residues": dict(
            sorted(Counter(row["start_residue"] for row in plan).items())
        ),
        "schedule_sequences": dict(schedule_sequences),
        "witness_input_hits": {
            name: witness_hits[name] for name in sorted(witnesses)
        },
        "witness_demo_lesson_coverage": {
            name: witness_demo_coverage[name] for name in sorted(witnesses)
        },
        "competitor_input_disagreements": {
            name: competitor_disagreements[name] for name in sorted(competitors)
        },
        "competitor_lesson_results": lesson_stats,
        "all_declared_competitors_refuted_in_every_lesson": all(
            stats["survived_all_demos"] == 0 for stats in lesson_stats.values()
        ),
    }


def _markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Lesson rival probe: {report['task_id']}",
        "",
        f"- Generator SHA-256: `{report['generator_sha256']}`",
        f"- Executed rule hash: `{report['rule_hash']}`",
        f"- Canonical pairs: {report['canonical_pair_count']}",
        f"- Declared shortcuts: {', '.join(report['declared']['canonical_shortcuts']) or '(none)' }",
        f"- Declared competitors: {', '.join(report['declared']['lesson_competitors']) or '(none)' }",
        f"- Verdict: **{report['verdict']}**",
        "",
        "## Canonical shortcut check",
        "",
    ]
    for name, stats in report["canonical_shortcuts"].items():
        lines.append(
            f"- `{name}`: {stats['matched']}/{stats['total']} canonical pairs; "
            f"fits all = `{stats['fits_every_canonical_pair']}`"
        )
    lines.extend(["", "## Lesson results", ""])
    for band, stats in report["bands"].items():
        lines.extend(
            [
                f"### {band}",
                "",
                f"- {stats['lessons']} lessons, {stats['generated_inputs']} inputs, "
                f"{stats['unique_inputs']} unique inputs",
                f"- Start residues: `{stats['schedule_start_residues']}`",
                f"- Witness demo coverage: `{stats['witness_demo_lesson_coverage']}`",
                f"- Competitor lesson results: `{stats['competitor_lesson_results']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Limits",
            "",
            *[f"- {item}" for item in report["limits"]],
            "",
        ]
    )
    return "\n".join(lines)


def run(args: argparse.Namespace) -> dict[str, Any]:
    generator_path = (
        Path(args.generator).resolve()
        if args.generator
        else REPO_ROOT / "generators" / args.task_id / "generator.py"
    )
    module = _load_module(generator_path)
    source_sha = _sha256_file(generator_path)
    declared_rule_hash = getattr(module, "RULE_HASH", None)
    if not isinstance(declared_rule_hash, str):
        raise RuntimeError("generator does not declare RULE_HASH")

    shortcuts = _callable_map(module, "CANONICAL_SHORTCUTS")
    lesson_competitors = _callable_map(module, "LESSON_COMPETITORS")
    witnesses = _callable_map(module, "SEMANTIC_WITNESSES")
    if not shortcuts:
        raise RuntimeError("no CANONICAL_SHORTCUTS declared")
    if not lesson_competitors:
        raise RuntimeError("no LESSON_COMPETITORS declared")
    if not witnesses:
        raise RuntimeError("no SEMANTIC_WITNESSES declared")
    if not callable(getattr(module, "schedule_profile", None)):
        raise RuntimeError("schedule_profile is required for cyclic-start evidence")

    schedule_period = len(getattr(module, "SCHEDULE_PROFILES", ()) or ())
    if schedule_period <= 0:
        raise RuntimeError("SCHEDULE_PROFILES must enumerate the schedule period")
    examples_per_lesson = args.demos_per_lesson + 1
    canonical_pairs = _canonical_pairs(args.task_id)
    canonical_results = _canonical_shortcut_results(shortcuts, canonical_pairs)

    # Competitors are read from the generator, with canonical-only shortcuts
    # added if necessary so every declared rival is tested at lesson level.
    competitors = dict(lesson_competitors)
    for name, fn in shortcuts.items():
        competitors.setdefault(name, fn)

    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    bands: dict[str, Any] = {}
    authority_receipts: dict[str, Any] = {}
    for band in args.bands:
        plan = build_lesson_plan(
            task_id=args.task_id,
            band=band,
            lessons=args.lessons_per_band,
            examples_per_lesson=examples_per_lesson,
            schedule_period=schedule_period,
        )
        grids: list[Any] = []
        for lesson in plan:
            for sample_index in lesson["sample_indices"]:
                grid = module.generate(
                    lesson["seed"], sample_index, difficulty=band
                )
                errors = module.self_check(grid, difficulty=band)
                if errors:
                    raise RuntimeError(
                        f"generated input failed self_check: band={band} "
                        f"seed={lesson['seed']} sample_index={sample_index}: {errors}"
                    )
                grids.append(grid)
        outputs, receipts = _apply_batches(
            task_id=args.task_id,
            grids=grids,
            out_dir=out_dir / "authority" / band,
            expected_generator_sha256=source_sha,
            expected_rule_hash=declared_rule_hash,
            batch_size=args.batch_size,
        )
        bands[band] = _score_band(
            module=module,
            band=band,
            plan=plan,
            grids=grids,
            outputs=outputs,
            witnesses=witnesses,
            competitors=competitors,
            demos_per_lesson=args.demos_per_lesson,
        )
        authority_receipts[band] = receipts

    failures = []
    for name, stats in canonical_results.items():
        if not stats["fits_every_canonical_pair"]:
            failures.append(
                f"declared canonical shortcut {name!r} fits only "
                f"{stats['matched']}/{stats['total']} canonical pairs"
            )
    for band, stats in bands.items():
        if stats["unique_inputs"] != stats["generated_inputs"]:
            failures.append(
                f"{band}: only {stats['unique_inputs']}/{stats['generated_inputs']} "
                "generated inputs are unique"
            )
        if not stats["all_declared_competitors_refuted_in_every_lesson"]:
            failures.append(f"{band}: at least one declared competitor survived a lesson")
        for name, count in stats["witness_demo_lesson_coverage"].items():
            if count != stats["lessons"]:
                failures.append(
                    f"{band}: witness {name!r} appears in demos for "
                    f"{count}/{stats['lessons']} lessons"
                )

    report = {
        "schema": "bc5e668b7668-lesson-rival-probe-v1",
        "task_id": args.task_id,
        "generator_path": str(generator_path.relative_to(REPO_ROOT)),
        "generator_sha256": source_sha,
        "rule_hash": declared_rule_hash,
        "canonical_pair_count": len(canonical_pairs),
        "sampler": {
            "lesson_seed": "sha256(task|lesson-rival-probe-v1|band|lesson_index)[:8]",
            "sample_indices": "nonoverlapping consecutive windows of demos+query",
            "lessons_per_band": args.lessons_per_band,
            "demos_per_lesson": args.demos_per_lesson,
            "queries_per_lesson": 1,
            "bands": list(args.bands),
            "schedule_period": schedule_period,
            "all_cyclic_starts_policy": (
                "examples_per_lesson is coprime to schedule period; starts cycle "
                "through every residue"
            ),
        },
        "declared": {
            "canonical_shortcuts": sorted(shortcuts),
            "lesson_competitors": sorted(lesson_competitors),
            "tested_competitors_union": sorted(competitors),
            "semantic_witnesses": sorted(witnesses),
        },
        "canonical_shortcuts": canonical_results,
        "bands": bands,
        "authority_batches": authority_receipts,
        "limits": [
            "This falsifies only the generator-declared shortcuts and competitors; it is not universal induction over all possible ARC rules.",
            "The census covers 100 deterministic lessons per requested band and every cyclic start of the declared four-slot schedule.",
            "All labels come from the selected canonical Racket authority through arcpuzzles apply; the Python rivals are never used as label authority.",
        ],
        "failures": failures,
        "verdict": "PASS" if not failures else "FAIL",
    }
    summary_path = out_dir / "lesson_rival_probe.json"
    markdown_path = out_dir / "lesson_rival_probe.md"
    summary_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    markdown_path.write_text(_markdown(report))
    return report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-id", default=DEFAULT_TASK_ID)
    parser.add_argument("--generator")
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--demos-per-lesson", type=int, default=4)
    parser.add_argument("--bands", nargs="+", default=list(DEFAULT_BANDS))
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument(
        "--out-dir",
        default=str(REPO_ROOT.parent / "checks" / "lesson-probe"),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report = run(args)
    except Exception as exc:  # fail loud for a durable review command
        print(f"lesson-rival-probe: ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({
        "task_id": report["task_id"],
        "generator_sha256": report["generator_sha256"],
        "rule_hash": report["rule_hash"],
        "verdict": report["verdict"],
        "failures": report["failures"],
    }, indent=2))
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
