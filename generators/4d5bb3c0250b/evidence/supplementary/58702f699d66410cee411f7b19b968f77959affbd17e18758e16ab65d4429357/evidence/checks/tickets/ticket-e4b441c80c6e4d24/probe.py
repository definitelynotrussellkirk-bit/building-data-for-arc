#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time

from reviewer_support import load_selected_generator

TASK_ID = "4d5bb3c0250b"
EXPECTED_SOURCE_SHA256 = "268443a7bf130a55f9d1d6aca5767e0e820edc8bcef4de01d490867bd5be7c54"
PROBE_SEED_HEX = "ae826f3e6709c6d3eb320013afccbee10bb3ff468b6bc61692a68ab23434b16f"


def sha256_json(value):
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()
    root = Path.cwd()
    generator, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    if source_sha256 != EXPECTED_SOURCE_SHA256:
        raise AssertionError(f"source drift: {source_sha256}")

    seed = int(PROBE_SEED_HEX[:16], 16)
    witness = None
    attempts = 0
    for difficulty in (None, "easy", "medium", "hard"):
        for sample_index in range(64):
            attempts += 1
            grid = generator.generate(seed, sample_index, difficulty=difficulty)
            if generator.SEMANTIC_WITNESSES["target_not_top_left"](grid):
                intended = generator.rule_mirror(grid)
                rival = generator.SEMANTIC_RIVALS["crop_top_left_block"](grid)
                witness = {
                    "difficulty": difficulty,
                    "sample_index": sample_index,
                    "input": grid,
                    "input_sha256": sha256_json(grid),
                    "self_check": generator.self_check(grid),
                    "observed_overrides": generator.observe_overrides(grid),
                    "intended_output": intended,
                    "rival_output": rival,
                    "outputs_disagree": intended != rival,
                }
                break
        if witness is not None:
            break

    completed = bool(
        witness
        and witness["self_check"] == []
        and witness["outputs_disagree"]
    )
    result = {
        "schema": "arcpuzzles-bounded-adversarial-witness-v1",
        "ticket_id": "ticket-e4b441c80c6e4d24",
        "task_id": TASK_ID,
        "status": "completed" if completed else "unknown",
        "probe_seed": PROBE_SEED_HEX,
        "numeric_seed": seed,
        "generator_path": source_path.relative_to(root).as_posix(),
        "generator_sha256": source_sha256,
        "rule_hash": generator.RULE_HASH,
        "shortcut": "crop the top-left block without testing color cardinality",
        "declared_witness": "target_not_top_left",
        "attempts": attempts,
        "witness": witness,
        "elapsed_seconds": round(time.monotonic() - started, 6),
        "interpretation": (
            "The pinned current source emits a lawful target outside the top-left block, "
            "so its declared semantic witness refutes the fixed-location shortcut. "
            "This bounded probe is not a general no-shortcut claim."
        ),
    }
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "attempts": attempts, "generator_sha256": source_sha256}))
    return 0 if completed else 1


if __name__ == "__main__":
    raise SystemExit(main())
