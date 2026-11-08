#!/usr/bin/env python3
"""Reproduce both task-local adversarial audit probes from packet_root."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "repo"


def load(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module, path


def components(grid, color=4):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    out = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        comp = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for q in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if q in unseen:
                    unseen.remove(q)
                    comp.add(q)
                    stack.append(q)
        out.append(comp)
    return out


def audit_db7() -> None:
    task_id = "db7f22490768"
    module, source = load(task_id)
    outdir = ROOT / "checks" / "audit" / task_id
    outdir.mkdir(parents=True, exist_ok=True)
    base = module.generate(123, 7, difficulty="medium")
    cases = []
    for overrides in [
        {"palette_kind": "warm"}, {"palette_kind": "cool"}, {"palette_size": 1},
        {"n_distinct_colors": 1}, {"position_bias": "scattered_hollow_rects"},
        {"density": "sparse"}, {"unknown_axis": 99},
    ]:
        try:
            grid = module.generate(123, 7, difficulty="medium", **overrides)
            cases.append({"overrides": overrides, "accepted": True,
                          "identical_to_default": grid == base,
                          "self_check": module.self_check(grid, difficulty="medium")})
        except Exception as exc:  # evidence, not a production error path
            cases.append({"overrides": overrides, "accepted": False,
                          "error": f"{type(exc).__name__}: {exc}"})
    bands = {}
    for name, difficulty in (("easy", "easy"), ("medium", None), ("hard", "hard")):
        seen = set()
        errors = 0
        for i in range(200):
            grid = module.generate(40000 + i, i, difficulty=difficulty)
            errors += bool(module.self_check(grid, difficulty=difficulty))
            seen.add(json.dumps(grid, separators=(",", ":")))
        bands[name] = {"draws": 200, "validator_errors": errors,
                       "distinct_inputs": len(seen)}
    report = {
        "schema": "audit-reproducer-v1", "task_id": task_id,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "seed": 123, "sample_index": 7, "difficulty": "medium",
        "default_grid_sha256": hashlib.sha256(
            json.dumps(base, separators=(",", ":")).encode()).hexdigest(),
        "finding": "advertised axes and unknown key are accepted but have no observable effect",
        "cases": cases,
        "sampling": {"seed_formula": "40000+i", "sample_index": "i",
                     "draws_per_band": 200, "bands": bands},
        "command": {"cwd": "packet_root", "argv": [
            "env", "PYTHONPATH=repo/shared/runtime", "/opt/pyvenv/bin/python3",
            "checks/audit/run_local_probes.py"]},
    }
    (outdir / "override_reproducer.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n")


def audit_a110() -> None:
    task_id = "a1105be40960"
    module, source = load(task_id)
    outdir = ROOT / "checks" / "audit" / task_id
    outdir.mkdir(parents=True, exist_ok=True)

    grid = [[0] * 15 for _ in range(10)]
    for r in range(1, 6):
        for c in range(1, 6):
            if r in (1, 5) or c in (1, 5):
                grid[r][c] = 4  # bbox 25, 16 pixels
    for r in range(1, 5):
        for c in range(9, 14):
            grid[r][c] = 4  # bbox 20, 20 pixels
    grid[8][0] = 1
    errors = module.self_check(grid)
    assert errors == [], errors
    (outdir / "input.json").write_text(json.dumps(grid) + "\n")
    (outdir / "counterexample_meta.json").write_text(json.dumps({
        "schema": "audit-counterexample-v1", "task_id": task_id,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "validator_errors": errors, "selector_k": 1,
        "objects": [
            {"label": "A_hollow", "bbox": [1, 1, 5, 5], "bbox_area": 25, "cell_count": 16},
            {"label": "B_solid", "bbox": [1, 9, 4, 13], "bbox_area": 20, "cell_count": 20},
        ],
        "expected_distinction": "Racket chooses A by bbox area; pixel-count rival chooses B",
    }, indent=2, sort_keys=True) + "\n")

    comps = components(grid)
    chosen = sorted(comps, key=len, reverse=True)[0]
    rival = [row[:] for row in grid]
    for r, c in chosen:
        rival[r][c] = 3
    (outdir / "pixel_count_rival.json").write_text(json.dumps({
        "task_id": task_id,
        "rival": "rank color-4 components by cell count descending",
        "output": rival,
    }, indent=2) + "\n")

    total = {"draws": 0, "validator_errors": 0, "all_components_solid_rectangles": 0,
             "bbox_and_cell_order_same": 0, "distinct_inputs": 0}
    all_inputs = set()
    per_band = {}
    for name, difficulty in (("easy", "easy"), ("medium", None), ("hard", "hard")):
        band = {key: 0 for key in total if key != "distinct_inputs"}
        for i in range(200):
            sample = module.generate(30000 + i, i, difficulty=difficulty)
            band["draws"] += 1
            total["draws"] += 1
            invalid = bool(module.self_check(sample, difficulty=difficulty))
            band["validator_errors"] += invalid
            total["validator_errors"] += invalid
            all_inputs.add(json.dumps(sample, separators=(",", ":")))
            objects = []
            for comp in components(sample):
                r1, r2 = min(r for r, _ in comp), max(r for r, _ in comp)
                c1, c2 = min(c for _, c in comp), max(c for _, c in comp)
                objects.append(((r2 - r1 + 1) * (c2 - c1 + 1), len(comp)))
            solid = all(area == count for area, count in objects)
            same = (sorted(range(len(objects)), key=lambda j: objects[j][0], reverse=True)
                    == sorted(range(len(objects)), key=lambda j: objects[j][1], reverse=True))
            band["all_components_solid_rectangles"] += int(solid)
            total["all_components_solid_rectangles"] += int(solid)
            band["bbox_and_cell_order_same"] += int(same)
            total["bbox_and_cell_order_same"] += int(same)
        per_band[name] = band
    total["distinct_inputs"] = len(all_inputs)
    racket_path = outdir / "racket.json"
    executed_rule_hash = json.loads(racket_path.read_text())["executed_rule_hash"] if racket_path.exists() else None
    report = {
        "schema": "audit-shortcut-census-v1", "task_id": task_id,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "executed_rule_hash": executed_rule_hash,
        "sampling": {"seed_formula": "30000+i", "sample_index": "i",
                     "draws_per_band": 200, "bands": ["easy", "medium(None)", "hard"]},
        "counts": total, "by_band": per_band,
        "shortcut": "rank the k-th largest color-4 component by pixel count rather than bbox area",
        "counterexample": {
            "input": "checks/audit/a1105be40960/input.json", "validator_errors": [],
            "racket_output": "checks/audit/a1105be40960/racket.json",
            "rival_output": "checks/audit/a1105be40960/pixel_count_rival.json",
            "distinction": "Racket recolors the hollow 5x5 frame; the rival recolors the solid 4x5 rectangle.",
        },
        "domain_note": "Validator-accepted and canonical-topology-relevant, but outside the selected all-solid generator distribution.",
    }
    (outdir / "shortcut_census.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    audit_db7()
    audit_a110()
    print("wrote both audit probe reports")
