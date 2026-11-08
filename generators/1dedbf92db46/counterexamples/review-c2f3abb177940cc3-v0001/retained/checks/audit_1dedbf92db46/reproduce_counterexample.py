#!/usr/bin/env python3
"""Reproduce the fixed-center-hole shortcut in generator 1dedbf92db46."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import types

TASK_ID = "1dedbf92db46"
HERE = Path(__file__).resolve()
PACKET = HERE.parents[2]
REPO = PACKET / "repo"
GENERATOR_PATH = REPO / "generators" / TASK_ID / "generator.py"
CANONICAL_PATH = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
RUNTIME = REPO / "shared" / "runtime"
TOOLS = REPO / "shared" / "tools"
OUT = HERE.with_name("fixed_center_hole_counterexample.json")

sys.path.insert(0, str(RUNTIME))
if "scripts" not in sys.modules:
    pkg = types.ModuleType("scripts")
    pkg.__path__ = [str(TOOLS)]
    sys.modules["scripts"] = pkg

from puzzle_generators import runner  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_generator():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {GENERATOR_PATH}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def canonical_row() -> dict:
    for line in CANONICAL_PATH.open(encoding="utf-8"):
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise RuntimeError(f"missing canonical row {TASK_ID}")


def normalize(grid):
    if grid and isinstance(grid[0], str):
        return [[int(v) for v in row] for row in grid]
    return [list(row) for row in grid]


def components(grid):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    out = []
    while unseen:
        start = min(unseen)
        stack = [start]
        unseen.remove(start)
        cells = []
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            for rr, cc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if (rr, cc) in unseen:
                    unseen.remove((rr, cc))
                    stack.append((rr, cc))
        out.append(cells)
    return sorted(out, key=lambda cells: min(c for _, c in cells))


def fixed_center_hole_rival(grid):
    """Wrong rule fitting every ordinary generator draw: erase right [1,1]."""
    h, w = len(grid), len(grid[0])
    result = [[0 for _ in range(w)] for _ in range(h)]
    comps = components(grid)
    if len(comps) < 2:
        return result
    left, right = comps[0], comps[1]
    for r, c in left:
        result[r][c] = grid[r][c]
    for r, c in right:
        result[r][c] = grid[r][c]
    top = min(r for r, _ in right)
    left_col = min(c for _, c in right)
    if top + 1 < h and left_col + 1 < w:
        result[top + 1][left_col + 1] = 0
    return result


def signature(grid):
    comps = components(grid)
    rows = []
    for cells in comps:
        top, bottom = min(r for r, _ in cells), max(r for r, _ in cells)
        left, right = min(c for _, c in cells), max(c for _, c in cells)
        rel = sorted((r-top, c-left) for r, c in cells)
        rows.append({
            "bbox_shape": [bottom-top+1, right-left+1],
            "support": [list(p) for p in rel],
        })
    return rows


def main() -> None:
    gen = load_generator()
    row = canonical_row()
    source = str(row["program_solution"])
    rule_hash = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
    bridge, fn_name = runner._open_bridge_with_rule(runner.wrap_rule(source))
    try:
        generated_input = gen.generate(0, 0, difficulty="medium")
        generated_actual = runner._apply_rule(bridge, fn_name, generated_input)
        generated_rival = fixed_center_hole_rival(generated_input)

        canonical_pairs = list(row.get("train") or [])
        tests = row.get("test") or []
        canonical_pairs.extend(tests if isinstance(tests, list) else [tests])
        canonical_pairs = [
            {"input": normalize(pair["input"]), "output": normalize(pair["output"])}
            for pair in canonical_pairs
        ]
        counter = canonical_pairs[1]
        counter_actual = runner._apply_rule(bridge, fn_name, counter["input"])
        counter_rival = fixed_center_hole_rival(counter["input"])
    finally:
        bridge.shutdown()

    census = {}
    all_hashes = set()
    total = fixed = validator_pass = 0
    for band in ("easy", "medium", "hard"):
        band_fixed = band_valid = 0
        band_hashes = set()
        for index in range(100):
            grid = gen.generate(index, index, difficulty=band)
            total += 1
            digest = hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()
            band_hashes.add(digest)
            all_hashes.add(digest)
            sig = signature(grid)
            ordinary = (
                len(sig) == 2
                and sig[0]["bbox_shape"] == [3, 3]
                and sig[1]["bbox_shape"] == [3, 3]
                and sig[0]["support"] == [[0,0],[0,1],[0,2],[1,0],[1,2],[2,0],[2,1],[2,2]]
                and sig[1]["support"] == [[0,0],[0,1],[0,2],[1,0],[1,1],[1,2],[2,0],[2,1],[2,2]]
            )
            if ordinary:
                fixed += 1
                band_fixed += 1
            findings = list(gen.self_check(copy.deepcopy(grid)) or [])
            if not findings:
                validator_pass += 1
                band_valid += 1
        census[band] = {
            "draws": 100,
            "fixed_3x3_center_hole_signature": band_fixed,
            "validator_pass": band_valid,
            "unique_inputs": len(band_hashes),
            "seed_range": [0, 99],
            "sample_index_range": [0, 99],
        }

    canonical_fits = sum(
        fixed_center_hole_rival(pair["input"]) == pair["output"]
        for pair in canonical_pairs
    )
    counter_validator = list(gen.self_check(copy.deepcopy(counter["input"])) or [])
    payload = {
        "schema": "arcpuzzles-audit-counterexample-v1",
        "task_id": TASK_ID,
        "generator_path": str(GENERATOR_PATH.relative_to(REPO)),
        "generator_sha256": sha256(GENERATOR_PATH),
        "declared_rule_hash": getattr(gen, "RULE_HASH", None),
        "selected_rule_hash": rule_hash,
        "rival": {
            "name": "fixed_center_hole_on_right",
            "description": "Preserve the left object and the solid right object, but erase only the cell at relative offset (1,1) in the right bbox.",
            "ordinary_generator_fit": {
                "draws": total,
                "fits_by_input_signature": fixed,
                "validator_pass": validator_pass,
                "unique_inputs": len(all_hashes),
                "bands": census,
                "sampler": "generate(seed=i, sample_index=i, difficulty=band), i=0..99",
            },
            "canonical_fit": {
                "fits": canonical_fits,
                "usable_pairs": len(canonical_pairs),
            },
        },
        "generated_example": {
            "seed": 0,
            "sample_index": 0,
            "difficulty": "medium",
            "overrides": {},
            "input": generated_input,
            "actual_racket_output": generated_actual,
            "rival_output": generated_rival,
            "rival_matches_authority": generated_rival == generated_actual,
            "validator_findings": list(gen.self_check(copy.deepcopy(generated_input)) or []),
            "documented_generator_domain": True,
        },
        "counterexample": {
            "source": "canonical train pair index 1",
            "seed": None,
            "sample_index": None,
            "difficulty": "canonical",
            "overrides": {},
            "input": counter["input"],
            "stored_canonical_output": counter["output"],
            "actual_racket_output": counter_actual,
            "rival_output": counter_rival,
            "rival_matches_authority": counter_rival == counter_actual,
            "validator_findings": counter_validator,
            "passes_target_validator": not counter_validator,
            "documented_generator_domain": False,
            "authority_domain": True,
            "domain_note": "The selected authority and canonical examples allow a 4x3 irregular left support copied into a 4x4 right bbox; ordinary generator draws document and emit only 3x3 center-hole frames.",
        },
        "command": {
            "cwd": "packet_root",
            "argv": ["python3", "run_with_racket.py", "python3", "../checks/audit_1dedbf92db46/reproduce_counterexample.py"],
        },
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "PASS" if generated_rival == generated_actual and counter_rival != counter_actual and fixed == total else "FAIL",
        "output": str(OUT),
        "ordinary_fixed": [fixed, total],
        "generated_rival_matches": generated_rival == generated_actual,
        "counterexample_refutes_rival": counter_rival != counter_actual,
        "canonical_fit": [canonical_fits, len(canonical_pairs)],
        "generator_sha256": payload["generator_sha256"],
        "rule_hash": rule_hash,
    }, indent=2))


if __name__ == "__main__":
    main()
