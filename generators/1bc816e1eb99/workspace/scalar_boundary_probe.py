"""Audit public seed/sample-index scalar handling for generator 1bc816e1eb99.

The probe is source-bound, creates its own output directory, checks both
``generate`` and ``schedule_profile``, and exits nonzero if malformed scalars are
accepted or literal integer controls are rejected.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any, Callable

from reference_probe import load_generator


INVALID_CASES = (
    ("bool_seed", (True, 0), "seed must be an integer"),
    ("float_seed", (1.5, 0), "seed must be an integer"),
    ("string_seed", ("1", 0), "seed must be an integer"),
    ("bool_sample_index", (0, True), "sample_index must be an integer"),
    ("float_sample_index", (0, 1.5), "sample_index must be an integer"),
    ("string_sample_index", (0, "1"), "sample_index must be an integer"),
    ("negative_sample_index", (0, -1), "sample_index must be nonnegative"),
)
VALID_CASES = (
    ("zero", (0, 0), None),
    ("negative_seed", (-7, 3), "easy"),
    ("large_seed", (2**31, 4), "hard"),
)
ENTRY_POINTS = ("generate", "schedule_profile")


def _digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _call(module, entry_point: str, args: tuple[Any, Any], difficulty: str | None):
    fn: Callable[..., Any] = getattr(module, entry_point)
    return fn(*args, difficulty=difficulty)


def audit(generator: Path) -> dict[str, Any]:
    module = load_generator(generator)
    records: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    contract_errors: list[str] = []

    for entry_point in ENTRY_POINTS:
        for name, args, difficulty in VALID_CASES:
            try:
                first = _call(module, entry_point, args, difficulty)
                second = _call(module, entry_point, args, difficulty)
            except Exception as exc:  # evidence records the actual disposition
                counts["rejected_valid"] += 1
                records.append(
                    {
                        "entry_point": entry_point,
                        "case": name,
                        "valid": True,
                        "status": "rejected",
                        "exception_type": type(exc).__name__,
                        "exception": str(exc),
                    }
                )
            else:
                counts["accepted_valid"] += 1
                deterministic = first == second
                if not deterministic:
                    contract_errors.append(f"{entry_point}:{name} was nondeterministic")
                records.append(
                    {
                        "entry_point": entry_point,
                        "case": name,
                        "valid": True,
                        "status": "accepted",
                        "deterministic": deterministic,
                        "result_sha256": _digest(first),
                    }
                )

        for name, args, expected_message in INVALID_CASES:
            try:
                value = _call(module, entry_point, args, "hard")
            except Exception as exc:  # evidence records the actual disposition
                counts["rejected_invalid"] += 1
                expected_exception = type(exc) in (TypeError, ValueError)
                expected_text = expected_message in str(exc)
                if not expected_exception or not expected_text:
                    contract_errors.append(
                        f"{entry_point}:{name} rejected with {type(exc).__name__}: {exc}"
                    )
                records.append(
                    {
                        "entry_point": entry_point,
                        "case": name,
                        "valid": False,
                        "status": "rejected",
                        "exception_type": type(exc).__name__,
                        "exception": str(exc),
                        "expected_exception_family": expected_exception,
                        "expected_message": expected_text,
                    }
                )
            else:
                counts["accepted_invalid"] += 1
                records.append(
                    {
                        "entry_point": entry_point,
                        "case": name,
                        "valid": False,
                        "status": "accepted",
                        "result_sha256": _digest(value),
                    }
                )

    normalized_counts = {
        key: counts[key]
        for key in ("accepted_invalid", "accepted_valid", "rejected_invalid", "rejected_valid")
    }
    passed = (
        normalized_counts
        == {
            "accepted_invalid": 0,
            "accepted_valid": len(ENTRY_POINTS) * len(VALID_CASES),
            "rejected_invalid": len(ENTRY_POINTS) * len(INVALID_CASES),
            "rejected_valid": 0,
        }
        and not contract_errors
    )
    return {
        "schema": "1bc816e1eb99-scalar-boundary-probe-v1",
        "generator_path": str(generator.resolve()),
        "generator_sha256": hashlib.sha256(generator.read_bytes()).hexdigest(),
        "entry_points": list(ENTRY_POINTS),
        "counts": normalized_counts,
        "contract_errors": contract_errors,
        "records": records,
        "passed": passed,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    report = audit(args.generator)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": report["passed"], "counts": report["counts"]}, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
