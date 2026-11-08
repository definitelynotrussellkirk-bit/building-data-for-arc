#!/usr/bin/env python3
"""Emit the reusable bounded demonstration-only rival audit."""
from __future__ import annotations
import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("_motif_order_audit_proto", HERE / "prototype.py")
assert SPEC is not None and SPEC.loader is not None
PROTO = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROTO)

parser = argparse.ArgumentParser()
parser.add_argument("--out", required=True)
parser.add_argument("--seed", type=int, action="append", default=[])
args = parser.parse_args()
seeds = args.seed or [0, 17, 97]
reports = [PROTO.audit_episode(seed, mode) for seed in seeds for mode in PROTO.MODES]
payload = {
    "schema": "arcpuzzles-parametric-bounded-audit-v1",
    "task_id": PROTO.TASK_ID,
    "reports": reports,
    "harmful_survivor_count": sum(len(report["harmful_survivors"]) for report in reports),
}
path = Path(args.out)
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({"reports": len(reports), "harmful_survivor_count": payload["harmful_survivor_count"], "out": str(path)}))
