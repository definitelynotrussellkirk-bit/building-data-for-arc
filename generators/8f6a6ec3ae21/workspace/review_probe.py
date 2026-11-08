#!/usr/bin/env python3
"""Reproducible contract probe for generator 8f6a6ec3ae21.

Checks the complete advertised joint override domain, canonical-shortcut claims,
and default witness/competitor coverage.  This is deliberately independent of
the review battery so a future author can rerun the task-specific assumptions
while editing the sampler.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from itertools import product
from pathlib import Path
import sys

TASK_ID = "8f6a6ec3ae21"
HERE = Path(__file__).resolve().parent
TASK_DIR = HERE.parent


def load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", TASK_DIR / "generator.py"))
    spec = importlib.util.spec_from_file_location(f"probe_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def canonical_pairs():
    from reviewer_support import canonical_pairs as read_pairs, find_root

    return read_pairs(TASK_ID, root=find_root(__file__))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--default-per-band", type=int, default=100)
    args = parser.parse_args()

    gen, source = load_generator()
    errors: list[dict] = []
    override_cases = 0
    for h, w, n1, n2, rd, cd in product(
        range(6, 11), range(7, 13), range(2, 5), range(2, 5), range(2), range(2)
    ):
        expected = {
            "grid_h": h,
            "grid_w": w,
            "n_marks_1": n1,
            "n_marks_2": n2,
            "n_row_decoys": rd,
            "n_col_decoys": cd,
        }
        override_cases += 1
        try:
            grid = gen.generate(20261004, override_cases, difficulty="hard", **expected)
            findings = gen.self_check(grid)
            observed = gen.observe_overrides(grid)
        except Exception as exc:
            errors.append({"kind": "override_exception", "case": expected, "error": repr(exc)})
            continue
        if findings:
            errors.append({"kind": "override_self_check", "case": expected, "findings": findings})
        if observed != expected:
            errors.append({"kind": "override_mismatch", "case": expected, "observed": observed})

    canonical = canonical_pairs()
    shortcut_results = {}
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        fits = [rival(pair["input"]) == pair["output"] for pair in canonical]
        shortcut_results[name] = {
            "pairs": len(fits),
            "fits_all": all(fits),
            "fits": fits,
        }
        if not all(fits):
            errors.append({"kind": "false_canonical_shortcut_claim", "name": name, "fits": fits})

    bands = {}
    for band in ("easy", "medium", "hard"):
        witness_hits = {name: 0 for name in gen.SEMANTIC_WITNESSES}
        rival_refutations = {name: 0 for name in gen.LESSON_COMPETITORS}
        unique = set()
        canonical_profiles = 0
        for index in range(args.default_per_band):
            grid = gen.generate(900000 + index, index, difficulty=band)
            frozen = tuple(tuple(row) for row in grid)
            unique.add(frozen)
            official = gen.rule_mirror(grid)
            profile = (len(grid), len(grid[0]), len({v for row in grid for v in row}))
            canonical_profiles += profile in {(6, 8, 3), (6, 9, 3), (7, 9, 3)}
            for name, witness in gen.SEMANTIC_WITNESSES.items():
                witness_hits[name] += bool(witness(grid))
            for name, rival in gen.LESSON_COMPETITORS.items():
                rival_refutations[name] += rival(grid) != official
        bands[band] = {
            "draws": args.default_per_band,
            "unique_inputs": len(unique),
            "canonical_profile_hits": canonical_profiles,
            "witness_hits": witness_hits,
            "rival_refutations": rival_refutations,
        }
        for name, count in witness_hits.items():
            if count == 0:
                errors.append({"kind": "missing_default_witness", "band": band, "name": name})
        for name, count in rival_refutations.items():
            if count == 0:
                errors.append({"kind": "unrefuted_default_rival", "band": band, "name": name})
        if canonical_profiles == 0:
            errors.append({"kind": "missing_canonical_profile", "band": band})

    report = {
        "schema": "8f6a6ec3ae21-review-probe/1",
        "task_id": TASK_ID,
        "generator_sha256": sha256(source),
        "rule_hash": gen.RULE_HASH,
        "override_domain": {
            "cases": override_cases,
            "all_constructive": not any(e["kind"].startswith("override_") for e in errors),
            "ranges": {
                "grid_h": [6, 10],
                "grid_w": [7, 12],
                "n_marks_1": [2, 4],
                "n_marks_2": [2, 4],
                "n_row_decoys": [0, 1],
                "n_col_decoys": [0, 1],
            },
        },
        "canonical_shortcuts": shortcut_results,
        "default_census": bands,
        "limitations": [
            "finite default census; not a proof against undeclared rivals",
            "Racket parity is owned by the battery rule_smoke stage, not this local probe",
        ],
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }
    text = json.dumps(report, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        sys.stdout.write(text)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
