#!/usr/bin/env python3
"""Finite demonstration-only shortcut audit for the tail-order family."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("tail_order_prototype_audit", HERE / "prototype.py")
if SPEC is None or SPEC.loader is None:
    raise ImportError("cannot load adjacent prototype")
prototype = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = prototype
SPEC.loader.exec_module(prototype)


def audit_family(seeds=(0, 17), demo_counts=(2, 3, 6), queries=4):
    cases = []
    for seed in seeds:
        for demos in demo_counts:
            for order in prototype.TAIL_ORDERS:
                episode = prototype.generate_episode(seed, order, demos, queries)
                result = prototype.audit_episode(episode, order)
                cases.append({"seed": seed, "demos": demos, "queries": queries,
                              "settings": {"tail_order": order}, **result})
    passed = all(case["survivors"] == [f"setting:{case['selected']}"]
                 and not case["ambiguous_query_rivals"] for case in cases)
    return {
        "schema": "arcpuzzles-tail-order-self-audit-v1",
        "status": "passed" if passed else "failed",
        "limits": {"seeds": list(seeds), "demo_counts": list(demo_counts),
                   "queries": queries,
                   "candidate_family": "three declared settings plus anchor-removal, horizontal-only, color-order, reverse-tail, and identity shortcuts"},
        "cases": cases,
        "conclusion": "Finite enumerated rivals only; not a universal uniqueness proof.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, action="append", dest="seeds")
    parser.add_argument("--demos", type=int, action="append", dest="demos")
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = audit_family(tuple(args.seeds or (0, 17)), tuple(args.demos or (2, 3, 6)), args.queries)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "cases": len(report["cases"]),
                      "out": str(args.out)}, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
