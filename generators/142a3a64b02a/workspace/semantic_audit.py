#!/usr/bin/env python3
"""Exhaustively rotate small lesson windows against declared semantic rivals.

This task-local probe complements the shared lesson census.  It checks every
query position in every consecutive ``EXAMPLES_NEEDED + 1`` window for a chosen
set of bands, seeds, and schedule starts.  Rival functions are read from the
reviewed generator itself, so the probe cannot silently drift to a copied list.

Run from the packet root through the verified wrapper, for example::

    python3 run_with_racket.py python3 \
      generators/142a3a64b02a/workspace/semantic_audit.py \
      --seeds 32 --starts 6 --out ../checks/semantic-audit-final.json

The probe uses the generator's independent Python mirror for labels.  It does
not replace the Racket smoke/authority checks or the shared source-bound census.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any, Iterable, Sequence


DEFAULT_BANDS = ("easy", "medium", "hard")


def _grid_hash(grid: Any) -> str:
    payload = json.dumps(grid, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _strict_equal(left: Any, right: Any) -> bool:
    return left == right


def _load_generator(path: Path) -> ModuleType:
    path = path.resolve()
    spec = importlib.util.spec_from_file_location(
        "semantic_audit_target_142a3a64b02a", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def audit_generator(
    generator: ModuleType,
    *,
    generator_path: Path,
    bands: Sequence[str] = DEFAULT_BANDS,
    seeds: Iterable[int] = range(32),
    starts: Iterable[int] = range(6),
    max_failure_examples: int = 20,
) -> dict[str, Any]:
    """Return a compact schedule-and-rival audit for ``generator``.

    A failure is any rotated lesson for which the generator's own
    ``lesson_identifiable`` hook reports a problem, a declared rival fits every
    demonstration but disagrees on the held-out query, or the hook and direct
    rival calculation disagree.  All failures are counted; only the first
    ``max_failure_examples`` are retained to keep evidence small.
    """
    if max_failure_examples < 0:
        raise ValueError("max_failure_examples must be nonnegative")

    examples_needed = int(generator.EXAMPLES_NEEDED)
    if examples_needed < 1:
        raise ValueError("EXAMPLES_NEEDED must be positive")
    rivals = dict(generator.LESSON_COMPETITORS)
    if not rivals:
        raise ValueError("LESSON_COMPETITORS must declare at least one rival")

    band_values = tuple(bands)
    seed_values = tuple(int(seed) for seed in seeds)
    start_values = tuple(int(start) for start in starts)
    if not band_values or not seed_values or not start_values:
        raise ValueError("bands, seeds, and starts must all be nonempty")
    if any(start < 0 for start in start_values):
        raise ValueError("starts must be nonnegative")

    input_hashes: set[str] = set()
    failure_examples: list[dict[str, Any]] = []
    failure_count = 0
    lessons = 0
    rotations = 0
    generated_pairs = 0
    per_band: dict[str, dict[str, Any]] = {}
    rival_counts = {
        name: {
            "refuted_by_demos": 0,
            "survives_and_agrees_on_query": 0,
            "survives_and_disagrees_on_query": 0,
            "errors": 0,
        }
        for name in sorted(rivals)
    }

    for band in band_values:
        band_stats = {
            "lessons": 0,
            "rotations": 0,
            "failures": 0,
            "generated_pairs": 0,
        }
        per_band[band] = band_stats
        for seed in seed_values:
            for start in start_values:
                pairs: list[dict[str, Any]] = []
                pair_errors: list[str] = []
                for offset in range(examples_needed + 1):
                    sample_index = start + offset
                    try:
                        grid = generator.generate(
                            seed,
                            sample_index,
                            difficulty=band,
                        )
                        validation = list(
                            generator.self_check(grid, difficulty=band)
                        )
                        if validation:
                            pair_errors.append(
                                f"sample_index {sample_index}: self_check: "
                                + "; ".join(validation)
                            )
                        output = generator.rule_mirror(grid)
                    except Exception as exc:  # evidence probe must retain crashes
                        pair_errors.append(
                            f"sample_index {sample_index}: "
                            f"{type(exc).__name__}: {exc}"
                        )
                        continue
                    pairs.append(
                        {
                            "sample_index": sample_index,
                            "input": grid,
                            "output": output,
                        }
                    )
                    input_hashes.add(_grid_hash(grid))
                    generated_pairs += 1
                    band_stats["generated_pairs"] += 1

                lessons += 1
                band_stats["lessons"] += 1
                if len(pairs) != examples_needed + 1:
                    failure_count += 1
                    band_stats["failures"] += 1
                    if len(failure_examples) < max_failure_examples:
                        failure_examples.append(
                            {
                                "band": band,
                                "seed": seed,
                                "start": start,
                                "query_offset": None,
                                "reasons": pair_errors or [
                                    "lesson materialization returned too few pairs"
                                ],
                            }
                        )
                    continue

                for query_offset, query in enumerate(pairs):
                    demos = [
                        pair for index, pair in enumerate(pairs)
                        if index != query_offset
                    ]
                    rotations += 1
                    band_stats["rotations"] += 1
                    hook_reasons = list(generator.lesson_identifiable(demos, query))
                    direct_ambiguous: list[str] = []
                    rival_errors: list[str] = []

                    for name in sorted(rivals):
                        rival = rivals[name]
                        try:
                            fits_demos = all(
                                _strict_equal(rival(pair["input"]), pair["output"])
                                for pair in demos
                            )
                            query_differs = not _strict_equal(
                                rival(query["input"]), query["output"]
                            )
                        except Exception as exc:
                            rival_counts[name]["errors"] += 1
                            rival_errors.append(
                                f"rival {name} raised {type(exc).__name__}: {exc}"
                            )
                            continue
                        if not fits_demos:
                            rival_counts[name]["refuted_by_demos"] += 1
                        elif query_differs:
                            rival_counts[name][
                                "survives_and_disagrees_on_query"
                            ] += 1
                            direct_ambiguous.append(name)
                        else:
                            rival_counts[name][
                                "survives_and_agrees_on_query"
                            ] += 1

                    expected_hook = [
                        f"demos do not falsify rival: {name}"
                        for name in direct_ambiguous
                    ]
                    mismatch = sorted(hook_reasons) != sorted(expected_hook)
                    reasons = list(pair_errors) + hook_reasons + rival_errors
                    if mismatch:
                        reasons.append(
                            "lesson_identifiable disagrees with direct rival audit: "
                            f"hook={hook_reasons!r}, direct={expected_hook!r}"
                        )
                    if direct_ambiguous and not hook_reasons:
                        reasons.extend(expected_hook)

                    if reasons:
                        failure_count += 1
                        band_stats["failures"] += 1
                        if len(failure_examples) < max_failure_examples:
                            failure_examples.append(
                                {
                                    "band": band,
                                    "seed": seed,
                                    "start": start,
                                    "query_offset": query_offset,
                                    "query_sample_index": query["sample_index"],
                                    "demo_sample_indices": [
                                        pair["sample_index"] for pair in demos
                                    ],
                                    "direct_ambiguous_rivals": direct_ambiguous,
                                    "reasons": reasons,
                                }
                            )

    generator_path = generator_path.resolve()
    report = {
        "schema": "142a3a64b02a-semantic-audit-v1",
        "task_id": str(generator.TASK_ID),
        "generator_version": str(generator.VERSION),
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "rule_hash": str(generator.RULE_HASH),
        "lesson_assembly": {
            "examples_needed": examples_needed,
            "window_pairs": examples_needed + 1,
            "policy": "consecutive sample indexes; hold out every pair once",
        },
        "bands": list(band_values),
        "seeds": {
            "count": len(seed_values),
            "values": list(seed_values),
        },
        "starts": {
            "count": len(start_values),
            "values": list(start_values),
        },
        "rivals": sorted(rivals),
        "lessons": lessons,
        "rotations": rotations,
        "generated_pairs": generated_pairs,
        "unique_inputs": len(input_hashes),
        "failure_count": failure_count,
        "failure_examples_retained": len(failure_examples),
        "failure_examples": failure_examples,
        "rival_counts": rival_counts,
        "per_band": per_band,
        "status": "pass" if failure_count == 0 else "finding",
        "limits": (
            "Finite audit of declared rivals and selected seed/start ranges; "
            "not a proof against undeclared rules or all possible inputs."
        ),
    }
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--generator",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "generator.py",
        help="generator.py to audit (defaults to the adjacent task generator)",
    )
    parser.add_argument(
        "--band",
        dest="bands",
        action="append",
        choices=DEFAULT_BANDS,
        help="difficulty band; repeat to select several (default: all three)",
    )
    parser.add_argument(
        "--seeds",
        type=int,
        default=32,
        help="audit integer seeds 0..N-1 (default: 32)",
    )
    parser.add_argument(
        "--starts",
        type=int,
        default=6,
        help="audit consecutive schedule starts 0..N-1 (default: 6)",
    )
    parser.add_argument(
        "--max-failure-examples",
        type=int,
        default=20,
        help="retain at most this many exact failed rotations (default: 20)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="write JSON report here; stdout is always concise JSON",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.seeds < 1 or args.starts < 1:
        raise SystemExit("--seeds and --starts must be positive")
    generator = _load_generator(args.generator)
    report = audit_generator(
        generator,
        generator_path=args.generator,
        bands=tuple(args.bands or DEFAULT_BANDS),
        seeds=range(args.seeds),
        starts=range(args.starts),
        max_failure_examples=args.max_failure_examples,
    )
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    concise = {
        key: report[key]
        for key in (
            "task_id",
            "generator_version",
            "generator_sha256",
            "lessons",
            "rotations",
            "unique_inputs",
            "failure_count",
            "status",
        )
    }
    if args.out:
        concise["report"] = str(args.out)
    print(json.dumps(concise, indent=2))
    return 0 if report["failure_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
