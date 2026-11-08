#!/usr/bin/env python3
"""One bounded source-pinned shortcut witness for ticket-1257fe617c6e2a9e."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TICKET_ID = "ticket-1257fe617c6e2a9e"
TASK_ID = "3f26d45b9f51"
PROBE_SEED = "6298f8ec86c0459bf666ebaae11eed7351d47e0e32065f8c12719be4fa9fd74c"
PINNED_SHA = "1bd4448f9ff51545858cb402a42521bd7238925667727911e797a8259ee06f5a"
ROOT = Path(__file__).resolve().parents[3] / "repo"
HOME = ROOT / "generators" / TASK_ID
sys.path.insert(0, str(ROOT / "shared/runtime"))
from reviewer_support import canonical_pairs  # noqa: E402


def load_generator():
    path = HOME / "generator.py"
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != PINNED_SHA:
        raise RuntimeError(f"pinned source drift: {digest}")
    spec = importlib.util.spec_from_file_location("ticket_3f26_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, digest


def differences(left, right):
    return [
        [r, c, a, b]
        for r, (lrow, rrow) in enumerate(zip(left, right))
        for c, (a, b) in enumerate(zip(lrow, rrow))
        if a != b
    ]


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    gen, source_sha = load_generator()
    rival = gen.SEMANTIC_RIVALS["nearest_pair_only"]
    canon = canonical_pairs(TASK_ID, root=ROOT)
    canonical_fit = [rival(pair["input"]) == pair["output"] for pair in canon]
    if not all(canonical_fit):
        raise AssertionError("nearest-pair rival no longer fits every canonical pair")

    seed = int(PROBE_SEED[:16], 16)
    sample_index = int(PROBE_SEED[16:24], 16) % gen.LESSON_SCHEDULE_PERIOD
    grid = gen.generate(seed, sample_index, difficulty="medium", K=7, n_colors=3)
    self_findings = gen.self_check(grid)
    strict_findings = gen.strict_canonical_like(grid)
    intended = gen._solve_python(grid)
    shortcut = rival(grid)
    diff = differences(shortcut, intended)
    if self_findings or strict_findings or not gen._w_three_collinear(grid) or not diff:
        raise AssertionError("generated case is not a lawful distinguishing witness")
    info = gen._analyze(grid)

    report = {
        "schema": "arcpuzzles-adversarial-witness-v1",
        "ticket_id": TICKET_ID,
        "task_id": TASK_ID,
        "probe_seed": PROBE_SEED,
        "generator_sha256": source_sha,
        "rule_hash": gen.RULE_HASH,
        "shortcut": {
            "name": "nearest_pair_only",
            "description": (
                "For each occupied row or column, connect only the closest adjacent "
                "same-color marker pair instead of the full outermost interval."
            ),
            "canonical_pair_fit": canonical_fit,
        },
        "witness": {
            "generation": {
                "seed": seed,
                "sample_index": sample_index,
                "difficulty": "medium",
                "K": 7,
                "n_colors": 3,
            },
            "lawful": {
                "self_check": self_findings,
                "strict_canonical_like": strict_findings,
                "three_collinear_markers": True,
            },
            "marker_cells": {str(k): v for k, v in info["markers"].items()},
            "difference_count": len(diff),
            "first_differences": diff[:20],
            "input": grid,
            "intended_output": intended,
            "shortcut_output": shortcut,
        },
        "assessment": (
            "Current pinned source contains a lawful ordinary generated witness that "
            "refutes the canonical-fitting nearest-pair shortcut; no new peer safety finding."
        ),
        "limits": "One source-pinned generated witness; no peer battery or census.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": "completed",
        "source_sha256": source_sha,
        "canonical_pairs_fit": sum(canonical_fit),
        "difference_count": len(diff),
        "out": str(args.out),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
