from __future__ import annotations
import json
import os
from pathlib import Path
from reviewer_support import load_selected_generator, find_root

ROOT = Path(os.environ["ARCPUZZLES_HOME"]).resolve()
OUT_ROOT = Path(__file__).resolve().parent

def frozen(x):
    return json.dumps(x, separators=(",", ":"), sort_keys=True)

def probe_869():
    task = "869d78fabc4d"
    gen, path, sha = load_selected_generator(task, root=ROOT)
    rows = []
    for difficulty, overrides in [
        ("easy", {"n_left": 5}),
        ("easy", {"grid_h": 12}),
        ("easy", {"grid_w": 14}),
        ("hard", {"n_left": 1}),
        ("hard", {"n_right": 1}),
    ]:
        try:
            grid = gen.generate(17, 3, difficulty=difficulty, **overrides)
            rows.append({"difficulty": difficulty, "overrides": overrides, "status": "accepted", "shape": [len(grid), len(grid[0])]})
        except Exception as exc:
            rows.append({"difficulty": difficulty, "overrides": overrides, "status": "rejected", "error": f"{type(exc).__name__}: {exc}"})
    ignored = {}
    baseline = gen.generate(31, 7, difficulty="medium")
    for name, value in [
        ("position_bias", "spread"),
        ("anchor_corner", True),
        ("asymmetry_force", True),
        ("palette_size", 2),
    ]:
        candidate = gen.generate(31, 7, difficulty="medium", **{name: value})
        ignored[name] = {"value": value, "byte_identical_to_default": frozen(candidate) == frozen(baseline)}
    payload = {"task_id": task, "generator_path": str(path.relative_to(ROOT)), "generator_sha256": sha,
               "declared_domain_rejections": rows, "ignored_override_comparisons": ignored}
    out = OUT_ROOT/task/"probe.json"
    out.write_text(json.dumps(payload, indent=2)+"\n")
    print(out)

def probe_8f():
    task = "8f49fe4fdfa8"
    gen, path, sha = load_selected_generator(task, root=ROOT)
    baseline = gen.generate(31, 7, difficulty="medium")
    comparisons = {}
    for name, value in [
        ("palette_kind", "warm"),
        ("palette_size", 4),
        ("palette_size", 6),
        ("position_bias", "header_row0_objects_below"),
        ("n_distinct_colors", 4),
        ("n_distinct_colors", 6),
        ("density", "sparse"),
        ("texture", "warm"),
    ]:
        key = f"{name}={value}"
        try:
            candidate = gen.generate(31, 7, difficulty="medium", **{name: value})
            comparisons[key] = {"status": "accepted", "byte_identical_to_default": frozen(candidate) == frozen(baseline),
                                "self_check": gen.self_check(candidate)}
        except Exception as exc:
            comparisons[key] = {"status": "rejected", "error": f"{type(exc).__name__}: {exc}"}
    counts = {}
    first_failure = None
    for band in ("easy", "medium", "hard"):
        bad = 0
        unique = set()
        for i in range(500):
            grid = gen.generate(5000+i, i, difficulty=band)
            findings = gen.self_check(grid)
            unique.add(frozen(grid))
            if findings:
                bad += 1
                if first_failure is None:
                    first_failure = {"band": band, "seed": 5000+i, "sample_index": i,
                                     "findings": findings, "grid": grid}
        counts[band] = {"draws": 500, "self_check_failures": bad, "unique_inputs": len(unique)}
    payload = {"task_id": task, "generator_path": str(path.relative_to(ROOT)), "generator_sha256": sha,
               "ignored_override_comparisons": comparisons, "sample_census": counts,
               "first_self_check_failure": first_failure}
    out = OUT_ROOT/task/"probe.json"
    out.write_text(json.dumps(payload, indent=2)+"\n")
    print(out)

probe_869(); probe_8f()
