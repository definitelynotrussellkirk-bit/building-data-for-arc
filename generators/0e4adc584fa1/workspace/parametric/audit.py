#!/usr/bin/env python3
"""Finite source-bound self-review for the 0e4adc584fa1 native family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


def _load():
    path = Path(__file__).resolve().with_name("native_family.py")
    spec = importlib.util.spec_from_file_location("_audit_0e4adc584fa1", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, default=12)
    args = parser.parse_args()
    family = _load()
    rows = []
    failures = []
    for seed in range(args.seeds):
        for settings in family.SETTINGS:
            for demos in (2, 3, 6):
                episode = family.generate(seed, settings, demos, 4)
                survivors = family.teaching_survivors(episode["train"], settings)
                row = {
                    "seed": seed,
                    "settings": settings,
                    "demos": demos,
                    "survivors": list(survivors),
                    "query_shapes": [
                        [len(pair["input"]), len(pair["input"][0])]
                        for pair in episode["test"]
                    ],
                }
                rows.append(row)
                if survivors != (family.setting_name(settings),):
                    failures.append(row)
    source = Path(family.__file__).read_bytes()
    report = {
        "schema": "0e4adc584fa1-finite-native-audit-v1",
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "settings": list(family.SETTINGS),
        "seeds": args.seeds,
        "demo_counts": [2, 3, 6],
        "episodes": len(rows),
        "failures": failures,
        "rows": rows,
        "limits": "Finite declared-rival audit; not a proof of unique induction.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"episodes": len(rows), "failures": len(failures), "out": str(args.out)}))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
