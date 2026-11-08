#!/usr/bin/env python3
"""Materialize the canonical-fitting full-vertical-guide shortcut witness.

Run from a staged task runtime or the review packet repo.  The report is pure
Python evidence; use ``arcpuzzles apply`` on its ``input`` field for selected
Racket authority evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

for ancestor in Path(__file__).resolve().parents:
    runtime = ancestor / "shared" / "runtime"
    if (runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(runtime))
        break
    if (ancestor / "reviewer_support.py").is_file():
        sys.path.insert(0, str(ancestor))
        break

from reviewer_support import canonical_pairs, find_root  # noqa: E402

TASK_ID = "aad4e3a1d5e3"
ROOT = find_root(__file__)
DEFAULT = ROOT / "generators" / TASK_ID / "generator.py"
if not DEFAULT.is_file():
    DEFAULT = ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", DEFAULT))
SPEC = importlib.util.spec_from_file_location(f"shortcut_probe_{TASK_ID}", GENERATOR_PATH)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)


def build_report() -> dict:
    grid = GEN.generate(0, 1, difficulty="medium")
    rival = GEN.CANONICAL_SHORTCUTS["require_unbroken_vertical_guide"]
    intended = GEN.rule_mirror(grid)
    rival_output = rival(grid)
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    return {
        "schema": "aad4e3a1d5e3-shortcut-witness/1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
        "seed": 0,
        "sample_index": 1,
        "difficulty": "medium",
        "observed_axes": GEN.observe_overrides(grid),
        "self_check": GEN.self_check(grid),
        "witness": GEN.SEMANTIC_WITNESSES["broken_vertical_guide"](grid),
        "canonical_pairs_fit_by_rival": all(
            rival(pair["input"]) == pair["output"] for pair in pairs
        ),
        "input": grid,
        "intended_python": intended,
        "rival_python": rival_output,
        "rival_disagrees": rival_output != intended,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = build_report()
    text = json.dumps(report, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if report["self_check"] == [] and report["witness"] and report["rival_disagrees"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
