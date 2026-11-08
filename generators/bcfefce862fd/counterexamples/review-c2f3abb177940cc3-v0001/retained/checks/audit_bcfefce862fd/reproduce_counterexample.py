#!/usr/bin/env python3
"""Reproduce the size-cutoff shortcut in generator bcfefce862fd."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import types

TASK_ID = "bcfefce862fd"
HERE = Path(__file__).resolve()
PACKET = HERE.parents[2]
REPO = PACKET / "repo"
GENERATOR_PATH = REPO / "generators" / TASK_ID / "generator.py"
CANONICAL_PATH = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
RUNTIME = REPO / "shared" / "runtime"
TOOLS = REPO / "shared" / "tools"
OUT = HERE.with_name("size_cutoff_counterexample.json")

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


def bbox_info(grid):
    cells = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v != 0]
    if not cells:
        return None
    top, bottom = min(r for r, _, _ in cells), max(r for r, _, _ in cells)
    left, right = min(c for _, c, _ in cells), max(c for _, c, _ in cells)
    return top, left, bottom, right, cells[0][2]


def fill_bbox(grid):
    info = bbox_info(grid)
    if info is None:
        return copy.deepcopy(grid)
    top, left, bottom, right, color = info
    out = [[0 for _ in row] for row in grid]
    for r in range(top, bottom + 1):
        for c in range(left, right + 1):
            out[r][c] = color
    return out


def small_rectangle_only_rival(grid):
    """Wrong rule: fill only when bbox dimensions are at most 5x5."""
    info = bbox_info(grid)
    if info is None:
        return copy.deepcopy(grid)
    top, left, bottom, right, _ = info
    if bottom - top + 1 <= 5 and right - left + 1 <= 5:
        return fill_bbox(grid)
    return copy.deepcopy(grid)


def main() -> None:
    gen = load_generator()
    row = canonical_row()
    source = str(row["program_solution"])
    rule_hash = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
    bridge, fn_name = runner._open_bridge_with_rule(runner.wrap_rule(source))
    try:
        generated_input = gen.generate(0, 0, difficulty="medium")
        generated_actual = runner._apply_rule(bridge, fn_name, generated_input)
        generated_rival = small_rectangle_only_rival(generated_input)

        canonical_pairs = list(row.get("train") or [])
        tests = row.get("test") or []
        canonical_pairs.extend(tests if isinstance(tests, list) else [tests])
        canonical_pairs = [
            {"input": normalize(pair["input"]), "output": normalize(pair["output"])}
            for pair in canonical_pairs
        ]
        counter = canonical_pairs[2]
        counter_actual = runner._apply_rule(bridge, fn_name, counter["input"])
        counter_rival = small_rectangle_only_rival(counter["input"])
    finally:
        bridge.shutdown()

    census = {}
    total = small = validator_pass = strict_pass = 0
    all_hashes = set()
    span_counts = {}
    for band in ("easy", "medium", "hard"):
        band_small = band_valid = band_strict = 0
        band_hashes = set()
        for index in range(100):
            grid = gen.generate(index, index, difficulty=band)
            total += 1
            digest = hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()
            band_hashes.add(digest)
            all_hashes.add(digest)
            top, left, bottom, right, _ = bbox_info(grid)
            dims = (bottom - top + 1, right - left + 1)
            span_counts[str(dims)] = span_counts.get(str(dims), 0) + 1
            if dims[0] <= 5 and dims[1] <= 5:
                small += 1
                band_small += 1
            findings = list(gen.self_check(copy.deepcopy(grid)) or [])
            strict_findings = list(gen.strict_canonical_like(copy.deepcopy(grid)) or [])
            if not findings:
                validator_pass += 1
                band_valid += 1
            if not strict_findings:
                strict_pass += 1
                band_strict += 1
        census[band] = {
            "draws": 100,
            "bbox_at_most_5x5": band_small,
            "validator_pass": band_valid,
            "strict_validator_pass": band_strict,
            "unique_inputs": len(band_hashes),
            "seed_range": [0, 99],
            "sample_index_range": [0, 99],
        }

    canonical_fits = sum(
        small_rectangle_only_rival(pair["input"]) == pair["output"]
        for pair in canonical_pairs
    )
    counter_validator = list(gen.self_check(copy.deepcopy(counter["input"])) or [])
    counter_strict = list(gen.strict_canonical_like(copy.deepcopy(counter["input"])) or [])
    top, left, bottom, right, _ = bbox_info(counter["input"])
    payload = {
        "schema": "arcpuzzles-audit-counterexample-v1",
        "task_id": TASK_ID,
        "generator_path": str(GENERATOR_PATH.relative_to(REPO)),
        "generator_sha256": sha256(GENERATOR_PATH),
        "declared_rule_hash": getattr(gen, "RULE_HASH", None),
        "selected_rule_hash": rule_hash,
        "rival": {
            "name": "fill_bbox_only_when_both_spans_at_most_5",
            "description": "Apply the correct bbox fill only for rectangles no larger than 5x5; otherwise leave the two markers unchanged.",
            "ordinary_generator_fit": {
                "draws": total,
                "bbox_at_most_5x5": small,
                "validator_pass": validator_pass,
                "strict_validator_pass": strict_pass,
                "unique_inputs": len(all_hashes),
                "bbox_span_counts": span_counts,
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
            "strict_validator_findings": list(gen.strict_canonical_like(copy.deepcopy(generated_input)) or []),
            "documented_generator_domain": True,
        },
        "counterexample": {
            "source": "canonical train pair index 2",
            "seed": None,
            "sample_index": None,
            "difficulty": "canonical",
            "overrides": {},
            "bbox_shape": [bottom - top + 1, right - left + 1],
            "input": counter["input"],
            "stored_canonical_output": counter["output"],
            "actual_racket_output": counter_actual,
            "rival_output": counter_rival,
            "rival_matches_authority": counter_rival == counter_actual,
            "validator_findings": counter_validator,
            "strict_validator_findings": counter_strict,
            "passes_target_validator": not counter_validator,
            "passes_strict_validator": not counter_strict,
            "documented_generator_domain": False,
            "authority_domain": True,
            "domain_note": "The selected authority and canonical examples include a 7x4 marker bbox, while AXES and ordinary generation cap each rectangle span at 5.",
        },
        "command": {
            "cwd": "packet_root",
            "argv": ["python3", "run_with_racket.py", "python3", "../checks/audit_bcfefce862fd/reproduce_counterexample.py"],
        },
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "PASS" if generated_rival == generated_actual and counter_rival != counter_actual and small == total else "FAIL",
        "output": str(OUT),
        "ordinary_small": [small, total],
        "generated_rival_matches": generated_rival == generated_actual,
        "counterexample_refutes_rival": counter_rival != counter_actual,
        "canonical_fit": [canonical_fits, len(canonical_pairs)],
        "generator_sha256": payload["generator_sha256"],
        "rule_hash": rule_hash,
    }, indent=2))


if __name__ == "__main__":
    main()
