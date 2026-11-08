"""Reusable bounded teaching and sampler audit for the contact-degree family."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from contact_degree_family import FINISHES, analyze, audit_episode, sample_query


def run(seeds=(0, 17, 97), demo_counts=(2, 3, 6)):
    rows = [audit_episode(seed, finish, demos=demos, queries=4)
            for seed in seeds for demos in demo_counts for finish in FINISHES]
    large = [analyze(sample_query(seed, 3)) for seed in seeds]
    if any(row["surviving_rivals"] for row in rows):
        raise AssertionError("a declared rival survived a visible teaching set")
    if any(row["has_30x30_query"] is not True for row in rows):
        raise AssertionError("an audited episode omitted the 30x30 query")
    return {
        "schema": "arcpuzzles-parametric-authoring-audit-v1",
        "task_id": "24b83272f157", "status": "passed", "jobs": len(rows),
        "seeds": list(seeds), "demo_counts": list(demo_counts),
        "settings": list(FINISHES), "declared_rivals": 10,
        "survivor_count": 0, "large_query": large, "rows": rows,
        "scope": "bounded Python mirror audit; protected Racket labels are supplied by native qualification",
        "training_admitted": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv); result = run()
    payload = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.out:
        if args.out.exists(): raise FileExistsError(args.out)
        args.out.parent.mkdir(parents=True, exist_ok=True); args.out.write_text(payload, encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "rows"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
