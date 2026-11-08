#!/usr/bin/env python3
"""Replay the saved sequential-dependency witness through protected Racket."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from arcpuzzles.review_sequential_replay import replay_witness


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--witness", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    root = Path.cwd().resolve()
    witness = json.loads(args.witness.resolve().read_text(encoding="utf-8"))
    result = replay_witness(root, witness)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "evaluations": result["evaluations"], "out": str(args.out)}, sort_keys=True))
    return 0 if result.get("status") == "owner_replayed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
