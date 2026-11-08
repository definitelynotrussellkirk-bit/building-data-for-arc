#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time

from reviewer_support import load_selected_generator

TASK_ID = "02a33ab58da6"
EXPECTED_SOURCE_SHA256 = "65c640287726bf5cfb9e8b983ff265e830642374e3aee48cb2779d9e7f8ee355"
PROBE_SEED_HEX = "8e9fa046e528370e4157f63ff69717304cf625e3224a25dc72f5ada1abce9e58"


def main() -> None:
    started = time.monotonic()
    root = Path.cwd()
    module, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    if source_sha256 != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(f"source hash mismatch: {source_sha256}")
    seed = int(PROBE_SEED_HEX, 16) & 0x7FFFFFFF
    valid = module.generate(seed, 0, difficulty="medium", scene_family="public")
    valid_result = {
        "override": {"scene_family": "public"},
        "dimensions": [len(valid), len(valid[0])],
        "observed_overrides": module.observe_overrides(valid),
        "self_check": module.self_check(valid),
    }
    invalid_result = {"override": {"scene_family": "PUBLIC"}}
    try:
        module.generate(seed, 0, difficulty="medium", scene_family="PUBLIC")
    except Exception as exc:  # evidence records exact API behavior
        invalid_result.update({"exception_type": type(exc).__name__, "message": str(exc)})
    else:
        invalid_result.update({"exception_type": None, "message": None})
    result = {
        "schema": "arcpuzzles-ticket-api-boundary-v1",
        "ticket_id": "ticket-b72f5a9899af5ce4",
        "task_id": TASK_ID,
        "consumer": "target_current_audit",
        "probe_seed_hex": PROBE_SEED_HEX,
        "effective_seed": seed,
        "sample_index": 0,
        "difficulty": "medium",
        "source_path": str(source_path.relative_to(root)),
        "source_sha256": source_sha256,
        "valid_call": valid_result,
        "invalid_call": invalid_result,
        "boundary_behaved": (
            valid_result["observed_overrides"] == {"scene_family": "public"}
            and valid_result["self_check"] == []
            and invalid_result.get("exception_type") in {"ValueError", "TypeError"}
        ),
        "elapsed_seconds": round(time.monotonic() - started, 6),
    }
    Path("../checks/tickets/ticket-b72f5a9899af5ce4/result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
