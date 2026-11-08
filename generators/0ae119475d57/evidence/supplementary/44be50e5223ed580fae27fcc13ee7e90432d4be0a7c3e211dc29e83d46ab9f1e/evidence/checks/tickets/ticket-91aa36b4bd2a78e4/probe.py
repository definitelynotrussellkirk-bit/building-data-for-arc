#!/usr/bin/env python3
"""One bounded valid/invalid override comparison for ticket-91aa36b4bd2a78e4."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve()
REPO = HERE.parents[3] / "repo"
for path in (REPO / "shared" / "runtime", REPO / "src"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from reviewer_support import load_selected_generator

TICKET_ID = "ticket-91aa36b4bd2a78e4"
TASK_ID = "0ae119475d57"
PINNED_SEED = "8e83fbf15eeb70d3e9355a49263c2c639c0c97098e2fe443b9127077d436218e"
EXPECTED_SHA = "42967d2de4dc05ab714039499533e569aa8cb5c62b02449bbb8e88638f43c83b"
RULE_HASH = "c286c869b037"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()
    module, source, digest = load_selected_generator(TASK_ID, root=REPO)
    seed = int(PINNED_SEED[:16], 16) & 0x7FFFFFFF

    valid = module.generate(seed, 0, difficulty="hard", grid_w=4)
    valid_result = {
        "call": {"seed": seed, "sample_index": 0, "difficulty": "hard", "grid_w": 4},
        "width": len(valid[0]),
        "height": len(valid),
        "strict_canonical_like": module.strict_canonical_like(valid),
        "observed_role_colors": module.observe_overrides(valid),
    }

    invalid_result = {
        "call": {"seed": seed, "sample_index": 0, "difficulty": "hard", "grid_w": True},
        "raised": None,
        "message": None,
    }
    try:
        module.generate(seed, 0, difficulty="hard", grid_w=True)
    except Exception as exc:  # exact observed boundary behavior
        invalid_result["raised"] = type(exc).__name__
        invalid_result["message"] = str(exc)

    passed = (
        digest == EXPECTED_SHA
        and valid_result["width"] == 4
        and valid_result["strict_canonical_like"] == []
        and invalid_result["raised"] == "ValueError"
        and "integer" in (invalid_result["message"] or "")
    )
    report = {
        "ticket_id": TICKET_ID,
        "type": "api_boundary",
        "consumer": "target_current_audit",
        "task_id": TASK_ID,
        "pinned_seed": PINNED_SEED,
        "derived_integer_seed": seed,
        "source_path": str(source.relative_to(REPO)),
        "source_sha256": digest,
        "expected_source_sha256": EXPECTED_SHA,
        "rule_hash": RULE_HASH,
        "boundary": "grid_w exact-integer override at the minimum advertised width",
        "valid_call": valid_result,
        "invalid_call": invalid_result,
        "passed": passed,
        "elapsed_seconds": time.monotonic() - started,
        "conclusion": (
            "grid_w=4 is accepted and observable; bool True is rejected rather than "
            "coerced to integer 1"
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
