#!/usr/bin/env python3
"""One-call-pair probe of ff76baf6c2d9's advertised grid_size boundary."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
TASK = "ff76baf6c2d9"
TICKET = "ticket-7f0214b0bee7e0dc"
TICKET_SEED = "d84ebf191b98ec9be7dcba351e546b8ab325cdbc29ec8a250f6f2ea629c3e67a"
SOURCE_SHA256 = "2a34c30b086a28f6f71b5743cff1203d73c7528e0dc1f5658476f421b0b7c80c"
RULE_HASH = "d31dc299f026"
SOURCE = REPO / "generators" / TASK / "generator.py"
OUT = HERE / "result.json"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_json(value: object) -> str:
    return sha256_bytes(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    )


def load_generator():
    spec = importlib.util.spec_from_file_location("ticket_ff76baf6c2d9", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    if OUT.exists():
        raise FileExistsError(OUT)
    assert sha256_file(SOURCE) == SOURCE_SHA256
    generator = load_generator()
    assert generator.RULE_HASH == RULE_HASH
    assert generator.AXES["grid_size"]["valid"] == "13..24"

    seed = int(TICKET_SEED[:16], 16)
    valid_kwargs = {"grid_size": 13, "n_sources": 1, "n_targets": 1}
    valid_grid = generator.generate(seed, 0, difficulty="easy", **valid_kwargs)
    valid_errors = generator.self_check(copy.deepcopy(valid_grid), difficulty="easy")
    valid_observed = generator.observe_overrides(copy.deepcopy(valid_grid))
    valid_output = generator.rule_mirror(copy.deepcopy(valid_grid))
    assert valid_errors == []
    assert valid_observed == valid_kwargs
    assert len(valid_grid) == 13 and all(len(row) == 13 for row in valid_grid)

    invalid_kwargs = {"grid_size": 12, "n_sources": 1, "n_targets": 1}
    try:
        generator.generate(seed, 0, difficulty="easy", **invalid_kwargs)
    except Exception as exc:  # retain exact public behavior
        invalid_behavior = {
            "accepted": False,
            "exception_type": type(exc).__name__,
            "message": str(exc),
        }
    else:
        invalid_behavior = {
            "accepted": True,
            "exception_type": None,
            "message": None,
        }
    assert invalid_behavior == {
        "accepted": False,
        "exception_type": "ValueError",
        "message": "grid_size must be an integer in [13, 24]",
    }

    report = {
        "schema": "arcpuzzles-api-boundary-ticket-v1",
        "ticket_id": TICKET,
        "status": "completed",
        "task_id": TASK,
        "source_binding": {
            "generator_sha256": SOURCE_SHA256,
            "rule_hash": RULE_HASH,
            "ticket_seed": TICKET_SEED,
        },
        "boundary": {
            "axis": "grid_size",
            "advertised_valid": "13..24",
            "comparison": "lower endpoint 13 versus immediate predecessor 12",
        },
        "valid_call": {
            "seed": seed,
            "sample_index": 0,
            "difficulty": "easy",
            "overrides": valid_kwargs,
            "accepted": True,
            "shape": [len(valid_grid), len(valid_grid[0])],
            "self_check_errors": valid_errors,
            "observed_overrides": valid_observed,
            "input_sha256": sha256_json(valid_grid),
            "output_sha256": sha256_json(valid_output),
        },
        "invalid_call": {
            "seed": seed,
            "sample_index": 0,
            "difficulty": "easy",
            "overrides": invalid_kwargs,
            **invalid_behavior,
        },
        "conclusion": (
            "The advertised lower grid_size boundary is enforced exactly: 13 is "
            "generated, self-validating, and observable as requested; 12 is rejected "
            "before generation with the documented ValueError range."
        ),
        "limitations": [
            "This ticket exercises one advertised boundary only.",
            "It does not constitute a full API or distribution audit.",
        ],
        "command": (
            "python3 review.py run python3 "
            "../checks/tickets/ticket-7f0214b0bee7e0dc/probe.py"
        ),
        "probe_sha256": sha256_file(Path(__file__)),
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": report["status"],
                "valid_shape": report["valid_call"]["shape"],
                "invalid_behavior": invalid_behavior,
                "out": str(OUT),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
