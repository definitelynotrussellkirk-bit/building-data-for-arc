#!/usr/bin/env python3
"""One bounded valid/invalid comparison for a peer generator override API."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import time

TICKET_ID = "ticket-af45a12013bef348"
TASK_ID = "a857cb7c0790"
PROBE_SEED = "759c0dc7123bf1343fc896935435b48e16fc11020d2af06028addd6f46a93cf6"
EXPECTED_GENERATOR_SHA256 = "83a2ccd00caf1d1a9d5cf4de5184672fb83c99e6f25224ab8318ff6c9003bec8"
VALID_TEXTURE = "default"
INVALID_TEXTURE = "definitely-not-a-declared-texture"


def grid_sha(grid) -> str:
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode("utf-8")).hexdigest()


def call(module, seed: int, texture: str) -> dict:
    try:
        grid = module.generate(seed, 0, texture=texture)
    except Exception as exc:  # retain actual boundary behavior, including type/message
        return {"ok": False, "exception_type": type(exc).__name__, "exception": str(exc)}
    return {
        "ok": True,
        "grid": grid,
        "grid_sha256": grid_sha(grid),
        "shape": [len(grid), len(grid[0])],
        "self_check": module.self_check(grid),
    }


def main() -> int:
    started = time.monotonic()
    here = Path(__file__).resolve()
    work = here.parents[3]
    repo = work / "repo"
    sys.path.insert(0, str(repo / "shared/runtime"))
    from reviewer_support import load_selected_generator

    module, source_path, source_sha = load_selected_generator(TASK_ID, root=repo)
    assert source_sha == EXPECTED_GENERATOR_SHA256
    declared = module.AXES["texture"]["valid"].split("|")
    assert VALID_TEXTURE in declared
    assert INVALID_TEXTURE not in declared

    seed = int(PROBE_SEED, 16)
    valid = call(module, seed, VALID_TEXTURE)
    invalid = call(module, seed, INVALID_TEXTURE)
    identical = valid.get("ok") and invalid.get("ok") and valid["grid"] == invalid["grid"]

    report = {
        "schema": "arcpuzzles-api-boundary-ticket-v1",
        "ticket_id": TICKET_ID,
        "type": "api_boundary",
        "status": "finding",
        "task_id": TASK_ID,
        "probe_seed": PROBE_SEED,
        "source": source_path.relative_to(work).as_posix(),
        "source_sha256": source_sha,
        "advertised_boundary": {
            "axis": "texture",
            "declared_valid": declared,
            "valid_value": VALID_TEXTURE,
            "invalid_value": INVALID_TEXTURE,
        },
        "targeted_probe": {
            "calls": 2,
            "valid_call": valid,
            "invalid_call": invalid,
            "invalid_was_rejected": not invalid.get("ok", False),
            "outputs_identical": identical,
        },
        "finding": {
            "summary": (
                "The advertised texture override accepts an undeclared value without error; the invalid and valid "
                "calls return byte-identical valid grids. Helpful texture values are also not consumed by GenCtx, "
                "so this public axis boundary is not enforced."
            ),
            "impact": (
                "Callers can believe a requested texture was honored when it was silently ignored, undermining exact "
                "override replay and axis observability. Degenerate texture names remain a separate direct branch."
            ),
            "suggested_repair": (
                "Validate texture against HELPFUL_TEXTURES + DEGENERATE_TEXTURES and either consume helpful values "
                "through a declared keyed draw or remove the unsupported helpful texture axis. Add a valid/invalid regression."
            ),
        },
        "limitations": [
            "This is one seeded valid/invalid comparison, not a peer battery or distribution census.",
            "No peer source was edited and no approval state was changed.",
        ],
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "elapsed_minutes": None,
    }
    assert valid.get("ok") and invalid.get("ok") and identical, report
    out = here.with_name("probe.json")
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"report": out.relative_to(work).as_posix(), "status": report["status"], "invalid_was_rejected": False, "outputs_identical": True}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
