"""Reproduce reference parity and the two assigned findings-only audits.

Run through the packet's run_with_racket.py from packet_root:
 python3 run_with_racket.py python3 generators/4a6d26e0b6ae/workspace/reference_and_audits.py --mode reference --out ../checks/reference
 python3 run_with_racket.py python3 generators/4a6d26e0b6ae/workspace/reference_and_audits.py --mode audits --out ../checks/audits

This is a reviewer experiment, NOT a training-label producer or a blind solve.
The audit command never modifies either audit target.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]


def load(task):
    path = ROOT / "generators" / task / "generator.py"
    spec = importlib.util.spec_from_file_location("review_" + task, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    row = next(json.loads(line) for line in (ROOT / "shared/data/canonical/puzzles.jsonl").open()
               if json.loads(line).get("task_id") == task)
    return mod, row, hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_pairs(row):
    for split in ("train", "test"):
        pairs = row.get(split, [])
        if isinstance(pairs, dict):
            pairs = [pairs]
        for i, pair in enumerate(pairs):
            if "output" in pair:
                yield {"kind": "canonical", "split": split, "index": i, **pair}


def sexpr(value):
    if isinstance(value, (list, tuple)):
        return "(" + " ".join(sexpr(x) for x in value) + ")"
    if type(value) is not int:
        raise TypeError(f"Only integer lists may enter grid literal: {type(value)}")
    return str(value)


def apply_many(bridge, rule, grids):
    outputs = []
    for i in range(0, len(grids), 16):
        batch = grids[i:i+16]
        actual = bridge.eval_text(f"(map {wrap_rule(rule)} '{sexpr(batch)})")
        if not isinstance(actual, list) or len(actual) != len(batch):
            raise ValueError("Reference returned the wrong number of grids")
        outputs.extend(actual)
    return outputs


def bridge_expectation(grid):
    # Separate diagnostic implementation: never used to label generator output.
    result = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    for r in range(h):
        for c in range(w):
            if grid[r][c]:
                continue
            for a, b in (((r,c-1),(r,c+1)), ((r-1,c),(r+1,c))):
                if (0 <= a[0] < h and 0 <= b[0] < h and 0 <= a[1] < w and 0 <= b[1] < w
                        and grid[a[0]][a[1]] != 0 and grid[a[0]][a[1]] == grid[b[0]][b[1]]):
                    result[r][c] = grid[a[0]][a[1]]
                    break
    return result


def swap(grid):
    return [[8 if x == 5 else 5 if x == 8 else x for x in row] for row in grid]


def anchored_rival(grid):
    result = swap(grid)
    result[0][0], result[-1][-1] = 8, 5
    return result


def save_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def reference(out):
    mod, row, digest = load("4a6d26e0b6ae")
    cases = list(canonical_pairs(row))
    for band in (None, "easy", "medium", "hard"):
        for seed in range(50):
            cases.append({"kind": "default", "seed": seed, "sample_index": seed % 11,
                          "difficulty": band, "input": mod.generate(seed, seed % 11, difficulty=band)})
    for texture in mod.HELPFUL_TEXTURES:
        for count in (1, 3, 8):
            for seed in range(3):
                overrides = {"grid_h": 14, "grid_w": 14, "gap_count": count, "texture": texture}
                cases.append({"kind": "override", "seed": seed, "sample_index": 2,
                              "overrides": overrides, "input": mod.generate(seed, 2, **overrides)})
    for texture in mod.DEGENERATE_TEXTURES:
        for seed in range(10):
            cases.append({"kind": "explicit_negative", "seed": seed, "sample_index": 0,
                          "overrides": {"texture": texture}, "input": mod.generate(seed, 0, texture=texture)})
    # Rule extension probes, NOT admitted generator scenes.
    g = [[0]*5 for _ in range(5)]; g[1][1] = g[1][3] = g[3][2] = 4
    cases.append({"kind": "rule_extension_only", "name": "one_pass_not_iterative", "input": g})
    g = [[0]*5 for _ in range(5)]; g[2][1] = g[2][3] = 2; g[1][2] = g[3][2] = 3
    cases.append({"kind": "rule_extension_only", "name": "horizontal_priority", "input": g})
    g = [[0]*5 for _ in range(5)]; g[0][0] = g[0][2] = 9; g[3][1] = g[3][3] = 2; g[3][2] = 7
    cases.append({"kind": "rule_extension_only", "name": "edge_and_occupied_center", "input": g})
    bridge = RacketBridge(max_calls_before_restart=48)
    try:
        outputs = apply_many(bridge, row["program_solution"], [x["input"] for x in cases])
    finally:
        bridge.close()
    failures = []
    with (out / "cases.jsonl").open("w") as handle:
        for i, (case, actual) in enumerate(zip(cases, outputs)):
            expected = case.get("output", bridge_expectation(case["input"]))
            checked = {**case, "racket_output": actual, "expected_output": expected, "passed": actual == expected}
            handle.write(json.dumps(checked) + "\n")
            if actual != expected:
                failures.append(i)
    summary = {"source_sha256": digest, "rule_sha256": hashlib.sha256(row["program_solution"].encode()).hexdigest(),
               "cases": len(cases), "returned_outputs": len(outputs), "by_kind": dict(Counter(c["kind"] for c in cases)),
               "failed_case_indices": failures, "passed": len(outputs) == len(cases) and not failures,
               "scope": "Racket vs canonical outputs/independent diagnostic expectation; not model or hidden-query scoring."}
    save_json(out / "summary.json", summary)
    return summary


def audits(out):
    bridge = RacketBridge(max_calls_before_restart=48)
    reports = {}
    try:
        mod, row, digest = load("117cf3dc2da3")
        cases = [{"seed": s, "sample_index": s % 11, "difficulty": band,
                  "input": mod.generate(s, s % 11, difficulty=band)}
                 for band in ("easy", "medium", "hard") for s in range(300)]
        actuals = apply_many(bridge, row["program_solution"], [x["input"] for x in cases])
        agrees = sum(anchored_rival(c["input"]) == a for c, a in zip(cases, actuals))
        canon = list(canonical_pairs(row))
        canon_actual = apply_many(bridge, row["program_solution"], [c["input"] for c in canon])
        controls = []
        for overrides in ({"bg_color": 0}, {"distractor_count": 0}, {"grid_h": 5}):
            try:
                g = mod.generate(0, 0, difficulty="easy", **overrides)
                controls.append({"overrides": overrides, "difficulty": "easy", "input": g})
            except Exception as exc:
                controls.append({"overrides": overrides, "difficulty": "easy", "error": f"{type(exc).__name__}: {exc}"})
        reports[mod.TASK_ID] = {
            "source_sha256": digest, "sample": {"seed_start": 0, "seed_stop_exclusive": 300, "sample_index": "seed % 11", "bands": ["easy","medium","hard"]},
            "draws": len(cases), "unique_inputs": len({json.dumps(c["input"]) for c in cases}),
            "fixed_corner_inputs": sum(c["input"][0][0] == 5 and c["input"][-1][-1] == 8 for c in cases),
            "rival_racket_agreements": agrees,
            "canonical_pairs": [{**c, "racket_output": a, "rival_output": anchored_rival(c["input"]),
                                 "rival_matches": anchored_rival(c["input"]) == a,
                                 "self_check": mod.self_check(c["input"])} for c,a in zip(canon,canon_actual)],
            "control_rejections": controls,
            "classification": "Reproduced fixed-corner shortcut support; no claim that a trained model learned it."}
        with (out / "117cf3dc2da3-census.jsonl").open("w") as f:
            for c, a in zip(cases, actuals):
                f.write(json.dumps({**c, "racket_output": a, "rival_matches": anchored_rival(c["input"]) == a}) + "\n")

        mod, row, digest = load("b8cd4b7fd7a4")
        controls = []
        for seed in range(100):
            g = mod.generate(seed, 0, grid_h=14, grid_w=5)
            controls.append({"seed": seed, "sample_index": 0, "overrides": {"grid_h":14,"grid_w":5},
                             "input":g, "observed_shape":[len(g),len(g[0])],
                             "same_as_no_overrides":g == mod.generate(seed,0)})
        probes = []
        for name, kwargs in (("default_seed0",{}),("blank",{"texture":"no_endpoints"}),
                             ("non_aligned",{"texture":"non_aligned"}),
                             ("adjacent",{"texture":"adjacent_endpoints"})):
            g = mod.generate(0,0,**kwargs)
            record = {"name":name,"seed":0,"sample_index":0,"overrides":kwargs,"input":g,"self_check":mod.self_check(g)}
            try:
                record["racket_output"] = apply_many(bridge,row["program_solution"],[g])[0]
            except Exception as exc:
                record["racket_error"] = f"{type(exc).__name__}: {exc}"
            probes.append(record)
        canon = list(canonical_pairs(row))
        canonical_checks = []
        for c in canon:
            try:
                actual = apply_many(bridge,row["program_solution"],[c["input"]])[0]
                canonical_checks.append({**c,"racket_output":actual,"passed":actual == c["output"]})
            except Exception as exc:
                canonical_checks.append({**c,"error":f"{type(exc).__name__}: {exc}","passed":False})
        reports[mod.TASK_ID] = {"source_sha256":digest,"draws":len(controls),
                               "sample":{"seed_start":0,"seed_stop_exclusive":100,"sample_index":0,"difficulty":None,"overrides":{"grid_h":14,"grid_w":5}},
                               "ignored_dimension_overrides":sum(c["same_as_no_overrides"] for c in controls),
                               "probes":probes,"canonical_checks":canonical_checks,
                               "classification":"Reproduced ignored controls and domain/self-check failures; execution results recorded separately."}
        with (out / "b8cd4b7fd7a4-controls.jsonl").open("w") as f:
            for c in controls:
                f.write(json.dumps(c)+"\n")
    finally:
        bridge.close()
    save_json(out / "summary.json", reports)
    return {task:{k:v for k,v in r.items() if k not in ("canonical_pairs","probes","canonical_checks","control_rejections")} for task,r in reports.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode",choices=("reference","audits"),required=True)
    parser.add_argument("--out",type=Path,required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    # The shared runtime imports scripts.*; source-directory aliases are not a
    # substitute for the repository's declared portable execution layout.
    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles.catalog import Catalog
    from arcpuzzles.runtime import prepare_runtime
    tasks = ["4a6d26e0b6ae"] if args.mode == "reference" else ["117cf3dc2da3", "b8cd4b7fd7a4"]
    with tempfile.TemporaryDirectory(prefix="arcpuzzles-review-e15551ff-") as directory:
        manifest = prepare_runtime(Catalog(ROOT), Path(directory), task_ids=tasks)
        save_json(args.out / "runtime-manifest.json", manifest)
        save_json(args.out / "runtime-location.json", {"command_cwd": str(Path.cwd()), "runtime_directory": directory,
                  "scope": "Shared execution helpers loaded from a fresh copied runtime; no sibling/predecessor imports."})
        sys.path.insert(0, directory)
        global RacketBridge, wrap_rule
        from arc_repl.racket_bridge import RacketBridge
        from puzzle_generators.rule_wrap import wrap_rule
        result = reference(args.out) if args.mode == "reference" else audits(args.out)
    print(json.dumps(result,indent=2))
    return 0 if args.mode == "audits" or result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
