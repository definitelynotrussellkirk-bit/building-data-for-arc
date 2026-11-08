#!/usr/bin/env python3
"""Audit overlapping lesson windows and every query rotation for ambiguity.

This task-local authoring tool complements the repository lesson census.  It
materializes a deterministic sequence for each difficulty band, checks every
four-pair consecutive window, rotates each pair through the query position, and
retains any declared rival that fits all demonstrations but disagrees on the
query.  Labels come from the generator's source-bound ``rule_mirror``; canonical
Racket parity must be established separately by the battery's rule/authority
stages.

Typical use from the packet root::

    python3 run_with_racket.py python3 \
      generators/0bb8813a21dc/workspace/lesson_probe.py \
      --starts 100 --out ../checks/lesson-window-probe.json
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Iterable

TASK = "0bb8813a21dc"
HOME = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[3]
DEFAULT_DIFFICULTIES = ("easy", "medium", "hard")
LESSON_SIZE = 4


def _load_generator(path: Path):
    path = path.resolve()
    spec = importlib.util.spec_from_file_location(f"lesson_probe_{TASK}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _json_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _source_hash(module: Any) -> str | None:
    path = getattr(module, "__file__", None)
    if not path:
        return None
    candidate = Path(path)
    if not candidate.is_file():
        return None
    return hashlib.sha256(candidate.read_bytes()).hexdigest()


def _profile_name(module: Any, grid: list[list[int]]) -> str:
    observer = getattr(module, "observe_overrides", None)
    if observer is None:
        return "<no-observer>"
    observed = observer(grid)
    if isinstance(observed, dict) and "scene_profile" in observed:
        return str(observed["scene_profile"])
    return json.dumps(observed, sort_keys=True, separators=(",", ":"))


def _copy_pair(pair: dict[str, Any]) -> dict[str, Any]:
    return {
        "input": [row[:] for row in pair["input"]],
        "output": [row[:] for row in pair["output"]],
    }


def audit_schedule(
    module: Any,
    *,
    starts: int,
    seed: int,
    difficulties: Iterable[str] = DEFAULT_DIFFICULTIES,
    max_failures: int = 100,
) -> dict[str, Any]:
    """Return a deterministic, JSON-serializable lesson-window audit.

    ``starts`` consecutive windows are checked per band.  A fixed seed is used
    for the underlying sequence, so overlapping windows genuinely share the
    same materialized pair rather than redrawing it under another seed.
    """
    if starts < 1:
        raise ValueError("starts must be positive")
    if max_failures < 1:
        raise ValueError("max_failures must be positive")
    bands = tuple(difficulties)
    if not bands:
        raise ValueError("at least one difficulty is required")

    rivals = dict(getattr(module, "LESSON_COMPETITORS", {}) or {})
    hook = getattr(module, "lesson_identifiable", None)
    strict = getattr(module, "strict_canonical_like", None)
    counts: Counter[str] = Counter()
    all_input_hashes: set[str] = set()
    failures: list[dict[str, Any]] = []
    failure_totals: Counter[str] = Counter()
    by_band: dict[str, dict[str, Any]] = {}

    def retain(row: dict[str, Any]) -> None:
        kind = str(row["kind"])
        failure_totals[kind] += 1
        if len(failures) < max_failures:
            failures.append(row)

    for difficulty in bands:
        profile_counts: Counter[str] = Counter()
        band_hashes: set[str] = set()
        # starts windows of four need starts+3 source pairs.
        sequence: list[dict[str, Any]] = []
        for sample_index in range(starts + LESSON_SIZE - 1):
            counts["generation_calls"] += 1
            try:
                grid = module.generate(seed, sample_index, difficulty=difficulty)
                repeat = module.generate(seed, sample_index, difficulty=difficulty)
                if grid != repeat:
                    retain(
                        {
                            "kind": "nondeterministic_generation",
                            "difficulty": difficulty,
                            "sample_index": sample_index,
                            "seed": seed,
                        }
                    )
                issues = list(module.self_check(grid))
                if issues:
                    retain(
                        {
                            "kind": "self_check_failure",
                            "difficulty": difficulty,
                            "sample_index": sample_index,
                            "seed": seed,
                            "issues": issues,
                            "input": grid,
                        }
                    )
                if strict is not None:
                    strict_issues = list(strict(grid))
                    if strict_issues:
                        retain(
                            {
                                "kind": "strict_profile_failure",
                                "difficulty": difficulty,
                                "sample_index": sample_index,
                                "seed": seed,
                                "issues": strict_issues,
                                "input": grid,
                            }
                        )
                output = module.rule_mirror(grid)
                pair = {"input": grid, "output": output}
                digest = _json_hash(grid)
                all_input_hashes.add(digest)
                band_hashes.add(digest)
                profile_counts[_profile_name(module, grid)] += 1
                sequence.append(pair)
            except Exception as exc:  # retain exact source coordinates and continue
                retain(
                    {
                        "kind": "materialization_error",
                        "difficulty": difficulty,
                        "sample_index": sample_index,
                        "seed": seed,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
                sequence.append({"input": [], "output": [], "invalid": True})

        band_rotation_count = 0
        band_ambiguities = 0
        band_hook_failures = 0
        for start in range(starts):
            counts["lessons"] += 1
            window = sequence[start : start + LESSON_SIZE]
            if any(pair.get("invalid") for pair in window):
                retain(
                    {
                        "kind": "invalid_window",
                        "difficulty": difficulty,
                        "start": start,
                        "seed": seed,
                    }
                )
                continue
            for query_offset in range(LESSON_SIZE):
                counts["rotations"] += 1
                band_rotation_count += 1
                query = window[query_offset]
                demos = [pair for i, pair in enumerate(window) if i != query_offset]

                if hook is not None:
                    try:
                        hook_reasons = list(hook(demos, query))
                    except Exception as exc:
                        hook_reasons = [f"{type(exc).__name__}: {exc}"]
                    if hook_reasons:
                        counts["hook_failures"] += 1
                        band_hook_failures += 1
                        retain(
                            {
                                "kind": "lesson_hook_failure",
                                "difficulty": difficulty,
                                "start": start,
                                "query_offset": query_offset,
                                "seed": seed,
                                "reasons": hook_reasons,
                                "demos": [_copy_pair(pair) for pair in demos],
                                "query": _copy_pair(query),
                            }
                        )

                for rival_name, rival in rivals.items():
                    counts["rival_rotation_checks"] += 1
                    try:
                        fits_demos = all(
                            rival(pair["input"]) == pair["output"] for pair in demos
                        )
                        if fits_demos:
                            counts["rival_demo_survivals"] += 1
                            rival_query = rival(query["input"])
                            if rival_query != query["output"]:
                                counts["ambiguous_rotations"] += 1
                                band_ambiguities += 1
                                retain(
                                    {
                                        "kind": "rival_ambiguity",
                                        "difficulty": difficulty,
                                        "start": start,
                                        "query_offset": query_offset,
                                        "seed": seed,
                                        "rival": rival_name,
                                        "demos": [_copy_pair(pair) for pair in demos],
                                        "query": _copy_pair(query),
                                        "rival_query_output": rival_query,
                                    }
                                )
                            else:
                                counts["rival_full_lesson_agreements"] += 1
                    except Exception as exc:
                        counts["rival_errors"] += 1
                        retain(
                            {
                                "kind": "rival_error",
                                "difficulty": difficulty,
                                "start": start,
                                "query_offset": query_offset,
                                "seed": seed,
                                "rival": rival_name,
                                "error": f"{type(exc).__name__}: {exc}",
                            }
                        )

        by_band[str(difficulty)] = {
            "source_pairs": len(sequence),
            "lessons": starts,
            "rotations": band_rotation_count,
            "unique_inputs": len(band_hashes),
            "profile_counts": dict(sorted(profile_counts.items())),
            "ambiguous_rotations": band_ambiguities,
            "hook_failures": band_hook_failures,
        }

    counts["unique_inputs"] = len(all_input_hashes)
    for key in (
        "hook_failures",
        "rival_errors",
        "rival_demo_survivals",
        "rival_full_lesson_agreements",
        "ambiguous_rotations",
    ):
        counts.setdefault(key, 0)
    report = {
        "schema": "0bb8813a21dc-lesson-window-probe-v1",
        "task_id": TASK,
        "generator_version": getattr(module, "VERSION", None),
        "generator_sha256": _source_hash(module),
        "rule_hash": getattr(module, "RULE_HASH", None),
        "parameters": {
            "seed": seed,
            "starts_per_band": starts,
            "lesson_size": LESSON_SIZE,
            "query_policy": "every pair held out once",
            "difficulties": list(bands),
            "max_retained_failures": max_failures,
        },
        "declared_rivals": sorted(rivals),
        "counts": dict(counts),
        "by_band": by_band,
        "failure_totals": dict(sorted(failure_totals.items())),
        "failures": failures,
        "failure_records_truncated": sum(failure_totals.values()) > len(failures),
        "authority_note": (
            "Labels were computed by the source-bound Python rule_mirror. "
            "Use the repository rule_smoke and authority_sync stages for Racket parity."
        ),
    }
    report["passed"] = not failure_totals
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path, default=HOME / "generator.py")
    parser.add_argument("--starts", type=int, default=100)
    parser.add_argument("--seed", type=int, default=1701)
    parser.add_argument("--max-failures", type=int, default=100)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.starts < 1:
        parser.error("--starts must be positive")
    if args.max_failures < 1:
        parser.error("--max-failures must be positive")

    module = _load_generator(args.generator)
    report = audit_schedule(
        module,
        starts=args.starts,
        seed=args.seed,
        max_failures=args.max_failures,
    )
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.out = args.out.resolve()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    summary = {
        "passed": report["passed"],
        "generator_sha256": report["generator_sha256"],
        "lessons": report["counts"].get("lessons", 0),
        "rotations": report["counts"].get("rotations", 0),
        "unique_inputs": report["counts"].get("unique_inputs", 0),
        "ambiguous_rotations": report["counts"].get("ambiguous_rotations", 0),
        "hook_failures": report["counts"].get("hook_failures", 0),
        "failure_totals": report["failure_totals"],
        "out": str(args.out),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
