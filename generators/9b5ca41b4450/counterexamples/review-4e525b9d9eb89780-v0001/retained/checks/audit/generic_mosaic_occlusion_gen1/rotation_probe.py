from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GEN = ROOT / "repo/generators/generic_mosaic_occlusion_gen1/generator.py"
spec = importlib.util.spec_from_file_location("audit_generic_mosaic", GEN)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)

report = {
    "schema": "generic-mosaic-rotation-audit-v1",
    "generator": str(GEN.relative_to(ROOT)),
    "version": mod.VERSION,
    "seeds_per_band": 40,
    "bands": {},
    "totals": {
        "tasks": 0,
        "generation_errors": 0,
        "self_check_failures": 0,
        "rotations": 0,
        "ambiguous_rotations": 0,
    },
    "first_counterexample": None,
}

for difficulty in ("easy", "medium", "hard"):
    band = {
        "tasks": 0,
        "generation_errors": [],
        "self_check_failures": [],
        "rotations": 0,
        "ambiguous_rotations": 0,
    }
    for seed in range(report["seeds_per_band"]):
        try:
            task = mod.generate_task(seed, difficulty=difficulty)
        except Exception as exc:
            band["generation_errors"].append({"seed": seed, "error": f"{type(exc).__name__}: {exc}"})
            report["totals"]["generation_errors"] += 1
            continue
        band["tasks"] += 1
        report["totals"]["tasks"] += 1
        task_errors = mod.self_check_task(task)
        if task_errors:
            band["self_check_failures"].append({"seed": seed, "errors": task_errors})
            report["totals"]["self_check_failures"] += 1

        pairs = list(task["train"]) + list(task["test"])
        for query_index, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            errors = mod.lesson_identifiable(demos, {"input": query["input"]})
            band["rotations"] += 1
            report["totals"]["rotations"] += 1
            if errors:
                band["ambiguous_rotations"] += 1
                report["totals"]["ambiguous_rotations"] += 1
                if report["first_counterexample"] is None:
                    supports = []
                    for pair in pairs:
                        g = pair["input"]
                        al = mod._detect_axis(g, True)
                        au = mod._detect_axis(g, False)
                        supports.append({
                            "al_offset": al - (len(g[0]) - 1),
                            "au_offset": au - (len(g) - 1),
                            "output_shape": [len(pair["output"]), len(pair["output"][0])],
                            "support": mod._support_counts(g, al, au),
                        })
                    report["first_counterexample"] = {
                        "difficulty": difficulty,
                        "seed": seed,
                        "original_train_count": len(task["train"]),
                        "original_test_count": len(task["test"]),
                        "held_out_pair_index": query_index,
                        "errors": errors,
                        "pair_summaries": supports,
                        "task": task,
                    }
    report["bands"][difficulty] = band

out = Path(__file__).with_name("rotation_probe.json")
out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps({
    "totals": report["totals"],
    "first_counterexample": None if report["first_counterexample"] is None else {
        key: value for key, value in report["first_counterexample"].items() if key != "task"
    },
    "out": str(out),
}, indent=2, sort_keys=True))
