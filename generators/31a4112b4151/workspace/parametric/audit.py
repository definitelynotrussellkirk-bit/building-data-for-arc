#!/usr/bin/env python3
"""Write the bounded target-scope rival audit used by the source inventory."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("_audit_31a_prototype", HERE / "prototype.py")
if SPEC is None or SPEC.loader is None:
    raise ImportError(HERE / "prototype.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, default=64)
    args = parser.parse_args()
    report = MODULE.bounded_audit(seeds=range(args.seeds), demos=2, queries=4)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"episodes": report["episodes"], "harmful_survivors": len(report["harmful_survivors"])}))
    return 0 if not report["harmful_survivors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
