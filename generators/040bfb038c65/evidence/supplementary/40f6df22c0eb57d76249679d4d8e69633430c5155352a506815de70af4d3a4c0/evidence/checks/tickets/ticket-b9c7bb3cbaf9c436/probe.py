#!/usr/bin/env python3
"""One source-bound lower-height override comparison; not a domain census."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
RUNTIME = REPO / "shared/runtime"
TASK_ID = "040bfb038c65"
TICKET_ID = "ticket-b9c7bb3cbaf9c436"
SOURCE_SHA256 = "c7bc4573dc3efe33da4b079eacdd52588f67b7294ca53df9c66efdf100a1615e"
RULE_HASH = "80d289c11e33"
SEED_HEX = "adf5f82925143e60d6a76e67b9c65e392e6bfc1a83e66acb2c3339afc62fb90f"
SEED = int(SEED_HEX, 16)
EVIDENCE_ROOT = f"checks/tickets/{TICKET_ID}"
sys.path[:0] = [str(RUNTIME), str(RUNTIME / "src")]

started = time.perf_counter()
result = {
    "ticket_id": TICKET_ID,
    "type": "api_boundary",
    "consumer": "target_current_audit",
    "task_id": TASK_ID,
    "rule_hash": RULE_HASH,
    "expected_generator_sha256": SOURCE_SHA256,
    "seed_hex": SEED_HEX,
    "seed_integer": SEED,
    "seed_interpretation": "int(seed_hex, 16)",
    "probe_count": 1,
    "boundary": "advertised grid_h lower bound: 7 accepted; 6 rejected",
    "scope": "Exactly two generate calls at one fixed seed, sample index, difficulty, and other override values.",
    "limitations": "No broader override-domain, seed, difficulty, lesson, or canonical-rule coverage is claimed.",
}
status = "unknown"
summary = "The bounded comparison did not establish an outcome."
try:
    from reviewer_support import load_selected_generator

    module, source, actual_hash = load_selected_generator(TASK_ID, root=REPO)
    result["source_path"] = str(source.relative_to(WORK))
    result["generator_sha256"] = actual_hash
    if actual_hash != SOURCE_SHA256:
        raise RuntimeError(f"Pinned source mismatch: {actual_hash}")
    if module.RULE_HASH != RULE_HASH:
        raise RuntimeError(f"Pinned rule mismatch: {module.RULE_HASH}")
    result["advertised_axis"] = module.AXES["grid_h"]
    fixed = {
        "sample_index": 0,
        "difficulty": "hard",
        "grid_w": 9,
        "n_majority": 3,
        "texture": "same_size_odd",
    }
    outcomes = []
    for label, height in (("valid", 7), ("invalid", 6)):
        kwargs = dict(fixed, grid_h=height)
        outcome = {"case": label, "call": {"seed": SEED, **kwargs}}
        try:
            grid = module.generate(SEED, **kwargs)
            encoded = (json.dumps(grid, separators=(",", ":")) + "\n").encode()
            outcome.update({
                "returned": True,
                "grid": grid,
                "grid_sha256": hashlib.sha256(encoded).hexdigest(),
                "height": len(grid),
                "width": len(grid[0]),
                "self_check": module.self_check(grid),
                "observed_overrides": module.observe_overrides(grid),
            })
        except Exception as exc:
            outcome.update({
                "returned": False,
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
            })
        outcomes.append(outcome)
    result["calls"] = outcomes
    valid, invalid = outcomes
    wanted = {"grid_h": 7, "grid_w": 9, "n_majority": 3, "texture": "same_size_odd"}
    valid_ok = (
        valid.get("returned") is True
        and valid.get("self_check") == []
        and valid.get("observed_overrides") == wanted
    )
    invalid_ok = (
        invalid.get("returned") is False
        and invalid.get("exception_type") == "ValueError"
    )
    result["valid_case_matches_advertised_controls"] = valid_ok
    result["invalid_case_rejected_with_value_error"] = invalid_ok
    if valid_ok and invalid_ok:
        status = "completed"
        summary = (
            "The one bounded API comparison reproduced the advertised lower grid_h boundary: "
            "grid_h=7 returned a 7x9 grid with three majority objects and same_size_odd texture, "
            "passing the generator's self_check; grid_h=6 raised ValueError. "
            "No issue was observed in these two calls; this is not a broader safety clearance."
        )
    else:
        status = "finding"
        summary = (
            "The one source-bound lower grid_h comparison contradicted the advertised boundary: "
            f"valid_case_matches_advertised_controls={valid_ok}, "
            f"invalid_case_rejected_with_value_error={invalid_ok}. "
            "See result.json for exact calls, returned grid or exception, and pinned source identity."
        )
except Exception as exc:
    status = "blocked"
    summary = "The bounded API comparison was blocked before a conclusive outcome: " + type(exc).__name__ + ": " + str(exc)
    result["error"] = {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}
result["probe_elapsed_seconds"] = time.perf_counter() - started
result["status"] = status
result["summary"] = summary
row = {
    "ticket_id": TICKET_ID,
    "type": "api_boundary",
    "status": status,
    "summary": summary,
    "evidence_paths": [f"{EVIDENCE_ROOT}/{name}" for name in ("probe.py", "result.json", "result.log")],
    "elapsed_minutes": None,
}
(HERE / "result.json").write_text(json.dumps(result, indent=2) + "\n")
(HERE / "ticket_result.json").write_text(json.dumps(row, indent=2) + "\n")
print(json.dumps(result, indent=2))
