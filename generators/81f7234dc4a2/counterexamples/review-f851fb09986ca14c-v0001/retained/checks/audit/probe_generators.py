from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "repo"
OUT = Path(__file__).resolve().parent


def load(tid: str):
    path = ROOT / "generators" / tid / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{tid}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module, path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def grid_key(grid):
    return tuple(tuple(row) for row in grid)


def audit_b3():
    tid = "b3b409a9afe5"
    gen, path = load(tid)
    report = {
        "task_id": tid,
        "generator_sha256": sha(path),
        "draws": 0,
        "generation_failures": [],
        "self_check_rejections": [],
        "bbox_shortcut_refuting_draws": 0,
        "repeated_color_draws": 0,
        "irregular_draws": 0,
        "unique_inputs": 0,
        "unique_outputs": 0,
    }
    inputs, outputs = set(), set()
    racket_inputs = []
    for band in ("easy", "medium", "hard"):
        for index in range(200):
            seed = 910000 + 10000 * ("easy", "medium", "hard").index(band) + index
            sample_index = 37 * index + 11
            try:
                grid = gen.generate(seed, sample_index, difficulty=band)
            except Exception as exc:
                report["generation_failures"].append({"band": band, "index": index, "error": repr(exc)})
                continue
            report["draws"] += 1
            findings = gen.self_check(grid, difficulty=band)
            if findings:
                report["self_check_rejections"].append({"band": band, "index": index, "findings": findings})
            facts = gen.semantic_observables(grid)
            if facts["repeated_color"]:
                report["repeated_color_draws"] += 1
            if facts["irregular_components"]:
                report["irregular_draws"] += 1
            mismatch = False
            for comp in gen._components(grid):
                r0, c0, r1, c1 = gen._bbox(comp["cells"])
                bbox_guess = math.ceil(min(r1 - r0 + 1, c1 - c0 + 1) / 2)
                mismatch |= bbox_guess != gen._onion_depth(comp["cells"])
            if mismatch:
                report["bbox_shortcut_refuting_draws"] += 1
            inputs.add(grid_key(grid))
            outputs.add(grid_key(gen.rule_mirror(grid)))
            if len(racket_inputs) < 12:
                racket_inputs.append(grid)
    report["unique_inputs"] = len(inputs)
    report["unique_outputs"] = len(outputs)

    # Canonical acceptance from the public normalized ledger helper.
    import sys
    sys.path.insert(0, str(ROOT / "shared" / "runtime"))
    from reviewer_support import canonical_pairs
    pairs = canonical_pairs(tid, root=ROOT, labeled_only=True)
    report["canonical_pairs"] = len(pairs)
    report["canonical_rejections"] = [
        {"index": i, "findings": gen.self_check(pair["input"])}
        for i, pair in enumerate(pairs) if gen.self_check(pair["input"])
    ]
    (OUT / f"{tid}_racket_inputs.json").write_text(json.dumps({"inputs": racket_inputs}, indent=2) + "\n")
    return report


def audit_81():
    tid = "81f7234dc4a2"
    gen, path = load(tid)
    report = {
        "task_id": tid,
        "generator_sha256": sha(path),
        "draws": 1000,
        "no_selected_body_ones": 0,
        "no_unselected_body_ones": 0,
        "both_selected_and_unselected": 0,
        "self_check_rejections": 0,
        "first_noop": None,
    }
    noop_grid = None
    for index in range(1000):
        grid = gen.generate(730000 + index, 13 * index + 5, difficulty="medium")
        report["self_check_rejections"] += bool(gen.self_check(grid))
        marks = {c for c, value in enumerate(grid[0]) if value == 2}
        selected = sum(grid[r][c] == 1 for r in range(1, len(grid)) for c in marks)
        unselected = sum(grid[r][c] == 1 for r in range(1, len(grid)) for c in range(len(grid[0])) if c not in marks)
        if selected == 0:
            report["no_selected_body_ones"] += 1
            if noop_grid is None and unselected > 0:
                noop_grid = grid
                report["first_noop"] = {
                    "seed": 730000 + index,
                    "sample_index": 13 * index + 5,
                    "marks": sorted(marks),
                    "selected_body_ones": selected,
                    "unselected_body_ones": unselected,
                }
        if unselected == 0:
            report["no_unselected_body_ones"] += 1
        if selected > 0 and unselected > 0:
            report["both_selected_and_unselected"] += 1

    override_cases = [
        {"n_marks": 1},
        {"n_marks": 5},
        {"grid_h": 12, "grid_w": 14},
        {"palette_kind": "dense"},
        {"texture": "irregular"},
    ]
    report["override_probes"] = []
    for overrides in override_cases:
        row = {"overrides": overrides}
        try:
            grid = gen.generate(1, 2, **overrides)
            row.update({
                "status": "returned",
                "shape": [len(grid), len(grid[0])],
                "observed_marks": sum(value == 2 for value in grid[0]),
                "self_check": gen.self_check(grid),
            })
        except Exception as exc:
            row.update({"status": "error", "error": f"{type(exc).__name__}: {exc}"})
        report["override_probes"].append(row)

    report["self_check_impostors"] = {
        "all_zero_7x9": gen.self_check([[0] * 9 for _ in range(7)]),
        "top_row_unexpected_1": gen.self_check([[1, 0, 2, 0, 0, 2, 0, 0, 0]] + [[0] * 9 for _ in range(6)]),
    }
    assert noop_grid is not None
    (OUT / f"{tid}_noop_input.json").write_text(json.dumps({"input": noop_grid}, indent=2) + "\n")
    return report


if __name__ == "__main__":
    report = {"b3b409a9afe5": audit_b3(), "81f7234dc4a2": audit_81()}
    path = OUT / "audit_probe_report.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
