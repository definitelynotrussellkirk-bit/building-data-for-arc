#!/usr/bin/env python3
"""Run the bounded finite-rival self-audit for this parametric family."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("header_measure_audit_prototype", HERE / "prototype.py")
if SPEC is None or SPEC.loader is None:
    raise ImportError("cannot load prototype")
prototype = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prototype)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=64)
    parser.add_argument("--demos", type=int, default=2)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if not 1 <= args.seeds <= 4096:
        raise ValueError("seeds must be in 1..4096")
    rows = []
    for seed in range(args.seeds):
        for setting in prototype.SETTINGS:
            episode = prototype.generate_episode(
                seed, setting, demos=args.demos, queries=args.queries
            )
            rows.append(
                {
                    "seed": seed,
                    "settings": setting,
                    **prototype.audit_episode(episode),
                }
            )
    result = {
        "schema": "1f9fef86a482-header-measure-self-audit-v1",
        "status": "passed"
        if all(not row["ambiguous_query_rivals"] for row in rows)
        else "failed",
        "seeds": args.seeds,
        "settings": len(prototype.SETTINGS),
        "episodes": len(rows),
        "tested_rivals_per_episode": rows[0]["tested_rivals"] if rows else 0,
        "ambiguous_episodes": sum(bool(row["ambiguous_query_rivals"]) for row in rows),
        "rows": rows,
        "limit": "Finite declared rivals only; this is not a universal uniqueness proof.",
    }
    raw = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(raw, encoding="utf-8")
    else:
        print(raw, end="")
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
