#!/usr/bin/env python3
"""Reproduce the strongest canonical-fitting shortcut counterexample.

Run from anywhere:
    python3 repo/generators/5e0575c16ab4/workspace/shortcut_probe.py \
        --out repo/generators/5e0575c16ab4/workspace/shortcut_counterexample.json
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve()
TASK_ROOT = HERE.parent.parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / "shared" / "runtime"))

spec = importlib.util.spec_from_file_location("review_5e0575c16ab4", TASK_ROOT / "generator.py")
assert spec and spec.loader
GEN = importlib.util.module_from_spec(spec)
spec.loader.exec_module(GEN)

WITNESS = [
    [2, 0, 0, 0, 0, 0, 2],
    [0, 0, 0, 0, 0, 0, 0],
    [2, 0, 0, 0, 2, 0, 0],
    [4, 0, 0, 4, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0],
]


def build_report() -> dict[str, Any]:
    intended = GEN.rule_mirror(WITNESS)
    shortcut = GEN.row_local_pairs(WITNESS)
    generated = GEN.generate(712, 8, profile="global_repeat")
    generated_intended = GEN.rule_mirror(generated)
    generated_shortcut = GEN.row_local_pairs(generated)

    assert GEN.self_check(WITNESS) == []
    assert intended != shortcut
    assert GEN.self_check(generated) == []
    assert generated_intended != generated_shortcut

    return {
        "schema": "arc-generator-shortcut-probe/1",
        "task_id": GEN.TASK_ID,
        "rule_hash": GEN.RULE_HASH,
        "shortcut": "row_local_pairs",
        "description": (
            "Fill any blank same-color endpoint pair independently per row, "
            "ignoring the color's total count in the grid."
        ),
        "witness_input": WITNESS,
        "intended_output": intended,
        "shortcut_output": shortcut,
        "disagreement_cells": [
            [r, c]
            for r, (expected_row, rival_row) in enumerate(zip(intended, shortcut))
            for c, (expected, rival) in enumerate(zip(expected_row, rival_row))
            if expected != rival
        ],
        "generated_profile": "global_repeat",
        "generated_input": generated,
        "generated_intended_output": generated_intended,
        "generated_shortcut_output": generated_shortcut,
        "generated_disagrees": generated_intended != generated_shortcut,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = build_report()
    rendered = json.dumps(report, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
