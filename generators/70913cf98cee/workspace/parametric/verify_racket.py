#!/usr/bin/env python3
"""Protected-Racket smoke verification for both finite settings."""
from __future__ import annotations

import json
from pathlib import Path

from arcpuzzles.parametric_worker import evaluate_contract


def main() -> None:
    root = Path(__file__).resolve().parents[4]
    contract = json.loads((Path(__file__).with_name("promotion.json")).read_text())
    jobs = [
        {"seed": seed, "settings": {"postprocess": setting}, "demos": 2, "queries": 4}
        for setting in ("direct", "cycle_dominoes")
        for seed in (0, 17)
    ]
    result = evaluate_contract(root, "70913cf98cee", contract, jobs)
    print(json.dumps({
        "status": "passed",
        "jobs": len(jobs),
        "episodes": len(result["episodes"]),
        "checks": result["checks"],
        "racket": result["racket"],
        "racket_evaluations": result["racket_evaluations"],
    }, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
