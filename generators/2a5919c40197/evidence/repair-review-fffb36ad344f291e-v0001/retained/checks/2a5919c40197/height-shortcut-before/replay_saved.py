"""Replay the saved old lesson after the sampler has been repaired.

Run through review.py run; this uses the recorded input/programs, not a new draw
from the now-repaired generator. Never overwrites the historical witness.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from arcpuzzles.parametric_worker import _real_evaluator


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    path = Path(__file__).with_name("witness.json")
    witness = json.loads(path.read_text())
    root = Path(__file__).resolve().parents[3] / "repo"
    apply, identity, bridge = _real_evaluator(root / "shared/runtime")
    try:
        for pair in witness["train"]:
            assert apply(witness["program_solution"], pair["input"]) == pair["output"]
            assert apply(witness["rival_program"], pair["input"]) == pair["output"]
        correct = apply(witness["program_solution"], witness["query_input"])
        rival = apply(witness["rival_program"], witness["query_input"])
        assert correct == witness["query_expected"]
        assert rival == witness["query_rival_output"]
        changed = sum(a != b for row_a, row_b in zip(correct, rival)
                      for a, b in zip(row_a, row_b))
        assert changed == witness["differing_query_cells"] > 0
    finally:
        bridge.close()
    result = {"status": "recorded_counterexample_replayed", "racket": identity,
              "witness_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
              "evaluations": 2 * len(witness["train"]) + 2,
              "differing_query_cells": changed,
              "scope": "Recorded pre-repair lesson only; not a claim about the current sampler."}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as handle:
        json.dump(result, handle, sort_keys=True, indent=2)
        handle.write("\n")
    print(json.dumps({"status": result["status"], "differing_query_cells": changed}))


if __name__ == "__main__":
    main()
