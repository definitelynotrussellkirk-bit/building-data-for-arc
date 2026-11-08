#!/usr/bin/env python3
"""Fast deterministic preflight for 3233860e2d81's advertised overrides.

This task-local authoring tool enumerates the same override cases as the shared
contract checker, but uses one requested seed/sample pair.  It is intended to
find structural filtering and observability defects quickly before the larger
multi-seed battery.  It does not replace the shared gate.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

from reviewer_support import find_root, load_selected_generator


TASK_ID = "3233860e2d81"
DEFAULT_BANDS = ("easy", "medium", "hard")


def _shared_cases(root: Path, axes):
    tools = str(root / "shared" / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    from check_generator_override_contract import _build_cases

    return _build_cases(axes)


def probe(*, seed: int = 0, sample_index: int = 3,
          bands=DEFAULT_BANDS) -> dict:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer (not bool)")
    bands = tuple(bands)
    if not bands or any(band not in DEFAULT_BANDS for band in bands):
        raise ValueError(f"bands must be a nonempty subset of {DEFAULT_BANDS}")

    root = find_root(__file__)
    generator, source_path, source_sha256 = load_selected_generator(
        TASK_ID, root=root
    )
    cases = _shared_cases(root, generator.AXES)
    failures = []
    rejection_examples = []
    accepted = 0
    rejected = 0
    started = time.monotonic()

    for band in bands:
        for case_index, overrides in enumerate(cases):
            try:
                grid = generator.generate(
                    seed, sample_index, difficulty=band, **overrides
                )
            except Exception as exc:  # retain exact public-contract failure
                rejected += 1
                axes = tuple(getattr(exc, "incompatible_axes", ()) or ())
                item = {
                    "band": band,
                    "case_index": case_index,
                    "overrides": overrides,
                    "exception": type(exc).__name__,
                    "message": str(exc),
                    "incompatible_axes": list(axes),
                }
                if len(rejection_examples) < 20:
                    rejection_examples.append(item)
                declared = (
                    isinstance(exc, ValueError)
                    and len(overrides) >= 2
                    and set(axes) == set(overrides)
                )
                if not declared:
                    failures.append({**item, "kind": "undeclared_rejection"})
                continue

            accepted += 1
            errors = generator.self_check(
                grid,
                difficulty=band,
                meta={"overrides": overrides},
            )
            if errors:
                failures.append(
                    {
                        "kind": "self_check",
                        "band": band,
                        "case_index": case_index,
                        "overrides": overrides,
                        "errors": errors,
                    }
                )

            observed = generator.observe_overrides(grid)
            for axis, requested in overrides.items():
                if observed.get(axis) != requested:
                    failures.append(
                        {
                            "kind": "mismatch",
                            "band": band,
                            "case_index": case_index,
                            "overrides": overrides,
                            "axis": axis,
                            "requested": requested,
                            "observed": observed.get(axis),
                        }
                    )

    elapsed = time.monotonic() - started
    return {
        "schema": "3233860e2d81-override-preflight-v1",
        "task_id": TASK_ID,
        "scope": (
            "one deterministic seed/sample across every shared override case; "
            "not a substitute for the multi-seed contract battery"
        ),
        "generator_path": source_path.relative_to(root).as_posix(),
        "generator_sha256": source_sha256,
        "seed": seed,
        "sample_index": sample_index,
        "bands": list(bands),
        "case_count": len(cases),
        "attempted": len(cases) * len(bands),
        "accepted": accepted,
        "rejected": rejected,
        "failure_count": len(failures),
        "failures": failures[:100],
        "failure_examples_truncated": len(failures) > 100,
        "rejection_examples": rejection_examples,
        "elapsed_seconds": round(elapsed, 6),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--sample-index", type=int, default=3)
    parser.add_argument(
        "--band",
        action="append",
        choices=DEFAULT_BANDS,
        dest="bands",
        help="repeat to restrict bands; default is all three",
    )
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    report = probe(
        seed=args.seed,
        sample_index=args.sample_index,
        bands=tuple(args.bands) if args.bands else DEFAULT_BANDS,
    )
    raw = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(raw, encoding="utf-8")
    print(raw, end="")
    return 0 if report["failure_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
