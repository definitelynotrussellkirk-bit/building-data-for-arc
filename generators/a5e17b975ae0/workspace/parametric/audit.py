"""Bounded teaching and sampler audit for the a5e17b975ae0 family."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("_a5e17b975ae0_audit_impl", HERE / "prototype.py")
assert SPEC is not None and SPEC.loader is not None
P = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P)


def run(seeds: int = 16) -> dict:
    rows = []
    failures = []
    for seed in range(seeds):
        for demos in (2, 3, 6):
            for policy in P.SETTINGS:
                episode = P.generate(seed, {"fill_color_policy": policy}, demos, 4)
                report = P.audit_episode(episode, policy)
                row = {"seed": seed, "demos": demos, "policy": policy, **report}
                rows.append(row)
                if report["harmful_survivors"]:
                    failures.append(row)
    return {
        "schema": "arcpuzzles-parametric-finite-audit-v1",
        "task_id": P.TASK_ID,
        "seeds": seeds,
        "episodes": len(rows),
        "declared_hypotheses": list(P.RIVALS),
        "failures": failures,
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=16)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run(args.seeds)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        print(text, end="")
    return 1 if report["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
