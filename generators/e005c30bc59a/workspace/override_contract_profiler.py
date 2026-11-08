#!/usr/bin/env python3
"""Pinpoint slow or failing cases in the official override-contract matrix.

This uses the checker's real AXES Cartesian-case builder, but executes one
(generator, difficulty, case) tuple at a time under a short per-call deadline.
It is intended for diagnosis when the aggregate override stage appears hung.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import signal
import sys
import time
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence


class CaseDeadlineExceeded(TimeoutError):
    """Raised when one generator/override tuple exceeds the local deadline."""


def _deadline_handler(_signum, _frame) -> None:
    raise CaseDeadlineExceeded("per-case generation deadline exceeded")


def profile_cases(
    generate: Callable[..., list[list[int]]],
    observe_overrides: Callable[[list[list[int]]], Mapping[str, Any]] | None,
    *,
    cases: Sequence[Mapping[str, Any]],
    bands: Sequence[str],
    seed: int,
    sample_index: int,
    deadline_seconds: float,
    slow_threshold_seconds: float,
) -> dict[str, Any]:
    """Run exact override cases and retain only slow/error/timeout rows."""
    rows: list[dict[str, Any]] = []
    previous_handler = signal.getsignal(signal.SIGALRM)
    signal.signal(signal.SIGALRM, _deadline_handler)
    try:
        for band in bands:
            for case_index, raw_case in enumerate(cases):
                case = dict(raw_case)
                started = time.perf_counter()
                status = "ok"
                error = ""
                observed: Mapping[str, Any] | None = None
                try:
                    if deadline_seconds > 0:
                        signal.setitimer(signal.ITIMER_REAL, deadline_seconds)
                    grid = generate(
                        seed,
                        sample_index,
                        difficulty=band,
                        **case,
                    )
                    if observe_overrides is not None:
                        observed = dict(observe_overrides(grid))
                except CaseDeadlineExceeded as exc:
                    status = "timeout"
                    error = str(exc)
                except Exception as exc:  # diagnostic tool must retain exact failure
                    status = "error"
                    error = repr(exc)
                finally:
                    signal.setitimer(signal.ITIMER_REAL, 0)
                elapsed = time.perf_counter() - started
                if status != "ok" or elapsed > slow_threshold_seconds:
                    row: dict[str, Any] = {
                        "band": band,
                        "case_index": case_index,
                        "case": case,
                        "status": status,
                        "seconds": elapsed,
                        "error": error,
                    }
                    if observed is not None:
                        row["observed"] = observed
                    rows.append(row)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)

    return {
        "case_count": len(cases),
        "band_count": len(bands),
        "attempt_count": len(cases) * len(bands),
        "seed": seed,
        "sample_index": sample_index,
        "deadline_seconds": deadline_seconds,
        "slow_threshold_seconds": slow_threshold_seconds,
        "slow_or_failed_count": len(rows),
        "rows": rows,
    }


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--task-id", default="e005c30bc59a")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--sample-index", type=int, default=3)
    parser.add_argument("--bands", nargs="+", default=["easy", "medium", "hard"])
    parser.add_argument("--deadline-seconds", type=float, default=0.25)
    parser.add_argument("--slow-threshold-seconds", type=float, default=0.02)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    repo = args.repo.resolve()
    runtime = repo / "shared" / "runtime"
    if str(runtime) not in sys.path:
        sys.path.insert(0, str(runtime))
    generator_path = repo / "generators" / args.task_id / "generator.py"
    checker_path = repo / "shared" / "tools" / "check_generator_override_contract.py"
    generator = _load_module(generator_path, f"override_profile_generator_{args.task_id}")
    checker = _load_module(checker_path, "override_profile_checker")
    cases = tuple(checker._build_cases(generator.AXES))
    observe = getattr(generator, "observe_overrides", None)

    report = profile_cases(
        generator.generate,
        observe,
        cases=cases,
        bands=tuple(args.bands),
        seed=args.seed,
        sample_index=args.sample_index,
        deadline_seconds=args.deadline_seconds,
        slow_threshold_seconds=args.slow_threshold_seconds,
    )
    report.update(
        {
            "schema": "arcpuzzles-override-contract-profile-v1",
            "task_id": args.task_id,
            "generator_sha256": _sha256(generator_path),
            "command": [
                "python3",
                f"generators/{args.task_id}/workspace/override_contract_profiler.py",
                "--repo",
                ".",
                "--seed",
                str(args.seed),
                "--sample-index",
                str(args.sample_index),
                "--deadline-seconds",
                str(args.deadline_seconds),
                "--slow-threshold-seconds",
                str(args.slow_threshold_seconds),
                "--out",
                str(args.out),
            ],
            "cwd": "repo",
        }
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        f"profiled {report['attempt_count']} attempts; "
        f"retained {report['slow_or_failed_count']} slow/error rows"
    )
    print(args.out)
    return 1 if any(row["status"] != "ok" for row in report["rows"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
