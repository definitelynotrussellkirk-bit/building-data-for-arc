from __future__ import annotations

from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path.cwd()
SOURCE = ROOT / "generators/generic_dense_field_gen4/generator.py"
SPEC = importlib.util.spec_from_file_location("audit_generic_dense_field_gen4", SOURCE)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def grid_hash(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def crop_rival(grid, out_h, out_w):
    return [row[:out_w] for row in grid[:out_h]]


def modal_fill_rival(grid, out_h, out_w):
    value = Counter(v for row in grid for v in row).most_common(1)[0][0]
    return [[value] * out_w for _ in range(out_h)]


summary = {
    "schema": "review-audit-generic-dense-field/1",
    "task_id": "generic_dense_field_gen4",
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "bands": {},
    "totals": {
        "tasks": 0,
        "pairs": 0,
        "generation_errors": 0,
        "contract_errors": 0,
        "crop_rival_disagreements": 0,
        "modal_fill_rival_disagreements": 0,
    },
    "unique_inputs": set(),
}

for band in ("easy", "medium", "hard"):
    band_stats = {"tasks": 0, "pairs": 0, "factors": Counter(), "errors": []}
    for seed in range(100):
        try:
            task = GEN.generate_task(seed, difficulty=band)
            repeated = GEN.generate_task(seed, difficulty=band)
        except Exception as exc:
            summary["totals"]["generation_errors"] += 1
            band_stats["errors"].append({"seed": seed, "error": repr(exc)})
            continue
        if task != repeated:
            band_stats["errors"].append({"seed": seed, "error": "nondeterministic"})
            summary["totals"]["contract_errors"] += 1
        factor = task["meta"]["factor"]
        band_stats["factors"][str(factor)] += 1
        expected_program = f"(rule! (lambda (g) (downscale g {factor})))"
        if task["program"] != expected_program:
            band_stats["errors"].append({"seed": seed, "error": "program/factor mismatch"})
            summary["totals"]["contract_errors"] += 1
        pairs = task["train"] + task["test"]
        if not (4 <= len(pairs) <= 6 and 3 <= len(task["train"]) <= 4 and 1 <= len(task["test"]) <= 2):
            band_stats["errors"].append({"seed": seed, "error": "pair-count contract"})
            summary["totals"]["contract_errors"] += 1
        band_stats["tasks"] += 1
        summary["totals"]["tasks"] += 1
        for index, pair in enumerate(pairs):
            gin, gout = pair["input"], pair["output"]
            band_stats["pairs"] += 1
            summary["totals"]["pairs"] += 1
            summary["unique_inputs"].add(grid_hash(gin))
            h, w = len(gin), len(gin[0])
            oh, ow = len(gout), len(gout[0])
            errors = []
            if h > 29 or w > 29 or h != oh * factor or w != ow * factor:
                errors.append("dimension/factor contract")
            if any(value == 0 for row in gin for value in row):
                errors.append("input not fully colored")
            if len({value for row in gout for value in row}) < 2:
                errors.append("constant output")
            recovered = []
            blocks_uniform = True
            for r in range(oh):
                out_row = []
                for c in range(ow):
                    block = {
                        gin[rr][cc]
                        for rr in range(r * factor, (r + 1) * factor)
                        for cc in range(c * factor, (c + 1) * factor)
                    }
                    if len(block) != 1:
                        blocks_uniform = False
                    out_row.append(gin[r * factor][c * factor])
                recovered.append(out_row)
            if not blocks_uniform:
                errors.append("nonuniform upscale block")
            if recovered != gout:
                errors.append("downscale parity")
            if crop_rival(gin, oh, ow) != gout:
                summary["totals"]["crop_rival_disagreements"] += 1
            if modal_fill_rival(gin, oh, ow) != gout:
                summary["totals"]["modal_fill_rival_disagreements"] += 1
            if errors:
                summary["totals"]["contract_errors"] += len(errors)
                band_stats["errors"].append({"seed": seed, "pair": index, "errors": errors})
    band_stats["factors"] = dict(sorted(band_stats["factors"].items()))
    summary["bands"][band] = band_stats

summary["unique_inputs"] = len(summary["unique_inputs"])
summary["status"] = (
    "no_issue_found" if summary["totals"]["generation_errors"] == 0
    and summary["totals"]["contract_errors"] == 0 else "findings"
)
print(json.dumps(summary, indent=2, sort_keys=True))
