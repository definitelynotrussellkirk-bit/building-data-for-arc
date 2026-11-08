#!/usr/bin/env python3
"""One valid/invalid advertised-override comparison for ticket-0e673e595014cd4b."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

WORK = Path(__file__).resolve().parents[3]
REPO = WORK / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))

from reviewer_support import load_selected_generator  # noqa: E402

TASK = "ad41fc0cda2b"
EXPECTED_SOURCE = "63239c4ae181be3da1d0221826f243495fb7104ac5a2c38a1a513e2bd993425a"
TICKET_SEED = "c4501949bcd8abdbd8561686fc3a30a24fcd51b2de85b37121484ba2d2672697"


def call(module, *, scene_variant: str):
    seed = int(TICKET_SEED[:16], 16)
    sample_index = int(TICKET_SEED[16:24], 16)
    row = {
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": "hard",
        "overrides": {"scene_variant": scene_variant, "palette_band": "high"},
    }
    try:
        grid = module.generate(
            seed,
            sample_index,
            difficulty="hard",
            scene_variant=scene_variant,
            palette_band="high",
        )
        row.update(
            status="accepted",
            shape=[len(grid), len(grid[0])],
            self_check=module.self_check(grid),
            observed_overrides=module.observe_overrides(grid),
        )
    except Exception as exc:  # evidence captures the public call behavior
        row.update(status="rejected", error=f"{type(exc).__name__}: {exc}")
    return row


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)

    module, source, source_hash = load_selected_generator(TASK, root=REPO)
    valid = call(module, scene_variant="large_tee")
    invalid = call(module, scene_variant="not_declared")
    passed = (
        source_hash == EXPECTED_SOURCE
        and valid.get("status") == "accepted"
        and valid.get("self_check") == []
        and valid.get("observed_overrides")
        == {"scene_variant": "large_tee", "palette_band": "high"}
        and invalid.get("status") == "rejected"
        and invalid.get("error", "").startswith("ValueError:")
    )
    payload = {
        "schema": "ticket-api-boundary-v1",
        "ticket_id": "ticket-0e673e595014cd4b",
        "task_id": TASK,
        "ticket_seed": TICKET_SEED,
        "source_path": str(source.relative_to(REPO)),
        "source_sha256": source_hash,
        "expected_source_sha256": EXPECTED_SOURCE,
        "advertised_axis": {"scene_variant": module.AXES["scene_variant"]},
        "valid_call": valid,
        "invalid_call": invalid,
        "passed": passed,
        "stopping_reason": "completed the single pinned valid/invalid API comparison",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
