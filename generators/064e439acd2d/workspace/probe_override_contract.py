"""Source-bound finite override census with exact failure witnesses.

Run through the packet wrapper, for example:
  python3 review.py run python3 generators/064e439acd2d/workspace/probe_override_contract.py --out ../checks/override-probe.json

Only pixel/API behavior is measured; this probe does not execute Racket labels.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


def _support():
    here = Path(__file__).resolve()
    for directory in (here.parent, *here.parents):
        candidate = directory / "tests/contract_support.py"
        if directory.name == "064e439acd2d" and candidate.is_file():
            spec = importlib.util.spec_from_file_location("projection_contract_support", candidate)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module, candidate
    raise FileNotFoundError("Task-local tests/contract_support.py was not retained")


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, default=8, help="Consecutive seeds, beginning at zero")
    parser.add_argument("--start-index", type=int, default=7, help="Sample index is start-index + seed")
    args = parser.parse_args(argv)
    if args.seeds < 1:
        parser.error("--seeds must be positive")
    if args.out.exists():
        parser.error("--out must be a new path; retain earlier source-bound evidence")
    support, helper_path = _support()
    generator, source, root = support.load_generator(__file__)
    source_sha = _sha(source)
    counts, failures, unique_inputs = Counter(), [], set()
    cases = []
    for name, band, overrides in support.valid_cases():
        cases.append((name, band, overrides, "realize", ()))
    for name, bad in support.invalid_cases():
        overrides = dict(grid_h=9, grid_w=10, n_dots=2, shape_kind="rect", texture="plain")
        overrides.update(bad)
        cases.append((name, None, overrides, "reject", ()))
    for name, overrides, context in support.incompatible_cases():
        cases.append((name, None, overrides, "incompatible", context))
    case_reports = []
    for name, band, overrides, expected, context in cases:
        case_counts = Counter()
        first_failure = None
        for seed in range(args.seeds):
            sample_index = args.start_index + seed
            grid, actual, generation_error = None, None, None
            try:
                grid = generator.generate(seed, sample_index, difficulty=band, **overrides)
            except Exception as error:
                generation_error = error
            try:
                if expected == "realize":
                    if generation_error is not None:
                        raise generation_error
                    actual = support.assert_realization(generator, grid, overrides, band)
                elif expected == "reject":
                    assert isinstance(generation_error, (TypeError, ValueError)), "invalid override was accepted or failed with an unexpected error"
                else:
                    assert generation_error is not None, "incompatible request returned a partial/substituted board"
                    support.assert_incompatibility(generation_error, context)
            except Exception as error:
                counts["failed"] += 1
                case_counts["failed"] += 1
                if first_failure is None:
                    if grid is not None:
                        try:
                            actual = support.observe(grid)
                        except AssertionError:
                            pass
                    first_failure = {"case": name, "seed": seed, "sample_index": sample_index,
                                     "difficulty": band, "overrides": overrides, "expected": expected,
                                     "error_type": type(error).__name__, "error": str(error),
                                     "input": grid, "observed": actual}
                    failures.append(first_failure)
            else:
                counts["passed"] += 1
                case_counts["passed"] += 1
            if grid is not None:
                unique_inputs.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
        case_reports.append({"case": name, "difficulty": band, "overrides": overrides,
                             "expected": expected, "counts": dict(case_counts)})
    if _sha(source) != source_sha:
        raise RuntimeError("Generator source changed while the probe ran; receipt was not written")
    report = {"schema": "arcpuzzles-task-override-probe-v1", "task_id": support.TASK_ID,
              "generator_path": str(source.relative_to(root)), "generator_sha256": source_sha,
              "probe_sha256": _sha(Path(__file__).resolve()), "helper_sha256": _sha(helper_path),
              "canonical_ledger_sha256": _sha(support.canonical_path(root)),
              "cwd": str(Path.cwd()), "argv": [sys.executable, *sys.argv],
              "scope": "finite pixel/API contract census; no Racket labels executed",
              "seed_range": [0, args.seeds - 1],
              "sample_index_range": [args.start_index, args.start_index + args.seeds - 1],
              "case_count": len(cases), "call_count": len(cases) * args.seeds,
              "unique_generated_inputs": len(unique_inputs), "counts": dict(counts),
              "cases": case_reports, "first_failure_per_case": failures,
              "status": "failed" if counts["failed"] else "passed"}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("status", "generator_sha256", "case_count", "call_count", "unique_generated_inputs", "counts")}, sort_keys=True))
    return 1 if counts["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
