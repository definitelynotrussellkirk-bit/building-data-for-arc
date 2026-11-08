"""Compare the Racket labels with the identity-crop shortcut."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def canonical_json(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def main() -> None:
    here = Path(__file__).resolve().parent
    generation = json.loads((here / "generation.json").read_text())
    racket = json.loads((here / "racket.json").read_text())
    rivals = json.loads((here / "rival.json").read_text())
    outputs = [row["output"] for row in racket["results"]]
    matches = [rival == output for rival, output in zip(rivals, outputs)]
    if matches != [True, True, True, False]:
        raise AssertionError(f"unexpected shortcut signature: {matches}")

    record = {
        "schema": "arcpuzzles-audit-counterexample-v1",
        "task_id": generation["task_id"],
        "finding": "three-demo identity-crop shortcut from invisible rotations",
        "generator_sha256": generation["generator_sha256"],
        "executed_rule_hash": racket["executed_rule_hash"],
        "rule_text_sha256": racket["rule_text_sha256"],
        "seed": generation["seed"],
        "difficulty": generation["difficulty"],
        "sample_indices": generation["sample_indices"],
        "self_check": generation["self_check"],
        "belongs_to_generated_support": True,
        "rival": "select and crop the legend-colored shape, but do not rotate it",
        "rival_matches": matches,
        "demonstrations_match_all": all(matches[:3]),
        "query_differs": not matches[3],
        "racket_output_sha256": [
            hashlib.sha256(canonical_json(output)).hexdigest() for output in outputs
        ],
        "rival_output_sha256": [
            hashlib.sha256(canonical_json(output)).hexdigest() for output in rivals
        ],
        "query_racket_output": outputs[3],
        "query_rival_output": rivals[3],
        "interpretation": (
            "all three demonstrations use 90-degree-symmetric selected crops, so "
            "the no-rotation shortcut fits them; the asymmetric query separates it"
        ),
        "evidence": {
            "generation": "checks/audit/0cb23f5660c9/generation.json",
            "inputs": "checks/audit/0cb23f5660c9/input.json",
            "racket": "checks/audit/0cb23f5660c9/racket.json",
            "rival": "checks/audit/0cb23f5660c9/rival.json",
        },
    }
    (here / "counterexample.json").write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(record, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
