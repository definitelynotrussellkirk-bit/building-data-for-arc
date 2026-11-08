#!/usr/bin/env python3
"""One bounded valid/invalid override comparison for ticket-0ba197bd2b14a510."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

TICKET_ID = "ticket-0ba197bd2b14a510"
TASK_ID = "3108da8bf9e8"
EXPECTED_SOURCE_SHA256 = "4c5d75752ec9c0899595a62b17076b1ed5e5240b3069e2d55b413477469730d3"
EXPECTED_RULE_HASH = "05977542b8d5"
PROBE_SEED = "8904252f0b15f96e70027a50475c927fb6a5be429b7e9e76f983dd6fc9325ca2"


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _load_generator(repo_root: Path):
    source = repo_root / "generators" / TASK_ID / "generator.py"
    actual = _sha(source.read_bytes())
    if actual != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(f"pinned source changed: {actual}")
    spec = importlib.util.spec_from_file_location(f"ticket_api_{TASK_ID}", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, source, actual


def build_report(repo_root: Path) -> dict[str, Any]:
    sys.path.insert(0, str(repo_root))
    sys.path.insert(0, str(repo_root / "src"))
    module, source, source_sha = _load_generator(repo_root)
    if module.RULE_HASH != EXPECTED_RULE_HASH:
        raise AssertionError((module.RULE_HASH, EXPECTED_RULE_HASH))
    advertised = module.AXES.get("omitted_count")
    if advertised != {"type": "int", "default": "keyed uniform", "valid": "0..9"}:
        raise AssertionError(f"advertised boundary changed: {advertised!r}")

    valid_grid = module.generate(
        17,
        0,
        difficulty="medium",
        omitted_count=0,
    )
    valid_errors = module.self_check(valid_grid, difficulty="medium")
    valid_observed = module.observe_overrides(valid_grid)
    if valid_errors or valid_observed != {"omitted_count": 0}:
        raise AssertionError((valid_errors, valid_observed))

    invalid: dict[str, Any]
    try:
        module.generate(17, 0, difficulty="medium", omitted_count=True)
    except Exception as error:  # the exact observed behavior is the evidence
        invalid = {
            "accepted": False,
            "error_type": type(error).__name__,
            "message": str(error),
        }
    else:
        invalid = {"accepted": True, "error_type": None, "message": None}

    if invalid["accepted"]:
        raise AssertionError("boolean override was silently accepted")
    if invalid["error_type"] != "TypeError" or "literal integer" not in invalid["message"]:
        raise AssertionError(invalid)

    return {
        "schema": "arcpuzzles-bounded-api-boundary-probe-v1",
        "ticket_id": TICKET_ID,
        "consumer": "target_current_audit",
        "probe_seed": PROBE_SEED,
        "task_id": TASK_ID,
        "source": {
            "path": str(source.relative_to(repo_root.parent)),
            "sha256": source_sha,
        },
        "rule_hash": module.RULE_HASH,
        "boundary": {
            "axis": "omitted_count",
            "advertised": advertised,
            "valid_call": {
                "seed": 17,
                "sample_index": 0,
                "difficulty": "medium",
                "overrides": {"omitted_count": 0},
                "self_check": valid_errors,
                "observed_overrides": valid_observed,
                "grid_sha256": _sha(json.dumps(valid_grid, separators=(",", ":")).encode()),
            },
            "invalid_call": {
                "seed": 17,
                "sample_index": 0,
                "difficulty": "medium",
                "overrides": {"omitted_count": True},
                **invalid,
            },
        },
        "outcome": {
            "status": "completed",
            "finding": False,
            "summary": (
                "The advertised 0..9 literal-integer override realizes and observes 0 exactly; "
                "the boolean impostor True is rejected before generation with TypeError."
            ),
            "scope_limit": (
                "One advertised override boundary and one valid/invalid comparison only; "
                "this is not a peer battery or universal API audit."
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    repo_root = Path.cwd().resolve()
    report = build_report(repo_root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report["outcome"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
