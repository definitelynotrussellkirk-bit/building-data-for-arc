#!/usr/bin/env python3
"""Exhaust every advertised joint override combination for 9de65c6eed00."""
from __future__ import annotations

import argparse
import importlib.util
import itertools
import json
from pathlib import Path


def load(path: Path):
    spec = importlib.util.spec_from_file_location("generator_under_probe", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generator", type=Path,
                        default=Path(__file__).resolve().parents[1] / "generator.py")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    gen = load(args.generator)
    failures = []
    total = 0
    for band, h, w, profile, palette in itertools.product(
            (None, "easy", "medium", "hard"), range(6, 15), range(9, 19), range(4), range(6)):
        total += 1
        options = {"grid_h": h, "grid_w": w, "profile_id": profile, "palette_id": palette}
        try:
            grid = gen.generate(1907, total, difficulty=band, **options)
            observed = gen.observe_overrides(grid)
            reasons = gen.self_check(grid, difficulty=band)
            if observed != options or reasons:
                failures.append({"band": band, "options": options,
                                 "observed": observed, "reasons": reasons})
        except Exception as exc:
            failures.append({"band": band, "options": options,
                             "error": f"{type(exc).__name__}: {exc}"})
    report = {"schema": "9de65c6eed00-control-probe-v1", "cases": total,
              "failures": failures, "status": "pass" if not failures else "fail"}
    raw = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(raw)
    print(raw, end="")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
