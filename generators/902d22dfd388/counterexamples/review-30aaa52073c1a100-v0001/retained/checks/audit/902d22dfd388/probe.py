#!/usr/bin/env python3
"""Reproduce the perimeter-filter shortcut for audit target 902d22dfd388.

Run from the packet root through run_with_racket.py. The script materializes the
lawful hand-built input before the public Racket apply command, then incorporates
the receipt on a second run.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs

TASK_ID = "902d22dfd388"
PACKET = Path(__file__).resolve().parents[3]
REPO = PACKET / "repo"
HERE = PACKET / "checks" / "audit" / TASK_ID
GEN_PATH = REPO / "generators" / TASK_ID / "generator.py"


def load_generator():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", GEN_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def perimeter_filter_rival(grid: list[list[int]]) -> list[list[int]]:
    """Never locate the frame: discard 7 and canvas-perimeter cells, then center."""
    h, w = len(grid), len(grid[0])
    kept = [
        (r, c, grid[r][c])
        for r in range(1, h - 1)
        for c in range(1, w - 1)
        if grid[r][c] not in (0, 7)
    ]
    out = [[0 for _ in range(w)] for _ in range(h)]
    if not kept:
        return out
    r1 = min(r for r, _, _ in kept)
    c1 = min(c for _, c, _ in kept)
    r2 = max(r for r, _, _ in kept)
    c2 = max(c for _, c, _ in kept)
    crop = [
        [0 if grid[r][c] == 7 else grid[r][c] for c in range(c1, c2 + 1)]
        for r in range(r1, r2 + 1)
    ]
    top = (h - len(crop)) // 2
    left = (w - len(crop[0])) // 2
    for rr, row in enumerate(crop):
        for cc, value in enumerate(row):
            if value:
                out[top + rr][left + cc] = value
    return out


def nonzero_cells(grid: list[list[int]]) -> list[list[int]]:
    return [[r, c, value] for r, row in enumerate(grid) for c, value in enumerate(row) if value]


def load_racket_output(path: Path) -> tuple[list[list[int]], dict[str, Any]]:
    receipt = json.loads(path.read_text())
    # Public apply receipts have changed shape over time; accept the documented
    # single-grid forms while retaining the whole receipt as evidence.
    candidates: list[Any] = []
    for key in ("output", "outputs", "results", "cases"):
        if key in receipt:
            candidates.append(receipt[key])
    def grid_like(value: Any) -> bool:
        return (
            isinstance(value, list) and value and all(isinstance(row, list) and row for row in value)
            and all(all(type(cell) is int for cell in row) for row in value)
        )
    for candidate in candidates:
        if grid_like(candidate):
            return candidate, receipt
        if isinstance(candidate, list) and len(candidate) == 1:
            one = candidate[0]
            if grid_like(one):
                return one, receipt
            if isinstance(one, dict):
                for key in ("output", "grid", "result"):
                    if grid_like(one.get(key)):
                        return one[key], receipt
        if isinstance(candidate, dict):
            for key in ("output", "grid", "result"):
                if grid_like(candidate.get(key)):
                    return candidate[key], receipt
    raise ValueError(f"could not locate single output grid in {path}")


def main() -> int:
    HERE.mkdir(parents=True, exist_ok=True)
    module = load_generator()
    canonical = canonical_pairs(TASK_ID, root=REPO)
    canonical_fit = [perimeter_filter_rival(pair["input"]) == pair["output"] for pair in canonical]

    generated = []
    for index in range(4):
        grid = module.generate(44, index, difficulty="easy")
        generated.append(
            {
                "seed": 44,
                "sample_index": index,
                "difficulty": "easy",
                "profile": module.schedule_profile(44, index, "easy"),
                "rival_matches_mirror": perimeter_filter_rival(grid) == module.rule_mirror(grid),
            }
        )

    original = module.generate(44, 1, difficulty="easy")
    analysis = module._analyze(original)
    outside = list(analysis["outside"])
    assert outside == [(7, 9, outside[0][2])], outside
    moved_color = outside[0][2]
    handbuilt = [row[:] for row in original]
    handbuilt[7][9] = 0
    handbuilt[6][8] = moved_color
    self_errors = module.self_check(handbuilt, difficulty="easy")
    strict_errors = module.strict_canonical_like(handbuilt)
    observed = module.observe_overrides(handbuilt)
    intended = module.rule_mirror(handbuilt)
    rival = perimeter_filter_rival(handbuilt)
    assert self_errors == [], self_errors
    assert strict_errors == [], strict_errors
    assert intended != rival

    (HERE / "input.json").write_text(json.dumps(handbuilt, indent=2) + "\n")
    (HERE / "rival-output.json").write_text(json.dumps(rival, indent=2) + "\n")

    evidence: dict[str, Any] = {
        "schema": "arcpuzzles-audit-counterexample-v1",
        "task_id": TASK_ID,
        "finding": "perimeter filtering bypasses frame isolation",
        "generator_path": str(GEN_PATH.relative_to(REPO)),
        "generator_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
        "declared_rule_hash": getattr(module, "RULE_HASH", None),
        "canonical_fit": {
            "matched": sum(canonical_fit),
            "total": len(canonical_fit),
            "all": all(canonical_fit),
        },
        "ordinary_cycle": generated,
        "construction": {
            "kind": "lawful handbuilt mutation of generate(44, 1, difficulty='easy')",
            "moved_cell": {"from": [7, 9], "to": [6, 8], "color": moved_color},
            "validator_errors": self_errors,
            "strict_errors": strict_errors,
            "observable_axes": observed,
            "belongs_to_documented_domain": True,
            "default_generator_emits_off_perimeter_outside_cells": False,
        },
        "input": handbuilt,
        "intended_python_mirror": intended,
        "rival_output": rival,
        "intended_nonzero_cells": nonzero_cells(intended),
        "rival_nonzero_cells": nonzero_cells(rival),
        "public_apply": {
            "cwd": "packet_root",
            "argv": [
                "python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply",
                TASK_ID, "--input", f"../checks/audit/{TASK_ID}/input.json",
                "--out", f"../checks/audit/{TASK_ID}/racket.json",
            ],
            "receipt": f"checks/audit/{TASK_ID}/racket.json",
        },
    }

    receipt_path = HERE / "racket.json"
    if receipt_path.exists():
        actual, receipt = load_racket_output(receipt_path)
        evidence["actual_racket_output"] = actual
        evidence["racket_matches_python_mirror"] = actual == intended
        evidence["racket_differs_from_rival"] = actual != rival
        evidence["actual_racket_nonzero_cells"] = nonzero_cells(actual)
        evidence["racket_receipt_sha256"] = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
        for key in ("executed_rule_hash", "catalog_rule_hash", "rule_text_sha256", "generator_sha256", "source_sha256", "input_sha256", "output_sha256"):
            if key in receipt:
                evidence.setdefault("receipt_fields", {})[key] = receipt[key]
        assert actual == intended
        assert actual != rival
    else:
        evidence["status"] = "prepared; run public apply command, then rerun probe"

    (HERE / "evidence.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "canonical_fit": evidence["canonical_fit"],
        "ordinary_cycle_all_fit": all(row["rival_matches_mirror"] for row in generated),
        "validator_errors": self_errors,
        "strict_errors": strict_errors,
        "racket_receipt_present": receipt_path.exists(),
        "racket_matches_python_mirror": evidence.get("racket_matches_python_mirror"),
        "racket_differs_from_rival": evidence.get("racket_differs_from_rival"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
