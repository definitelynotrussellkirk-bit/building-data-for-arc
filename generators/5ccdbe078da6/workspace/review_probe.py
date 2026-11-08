"""Reproducible Racket-backed corpus and counterexample probe.

Run from a source checkout, normally through packet run_with_racket.py.
--mode cases --task ID --inputs cases.json provides a reusable arbitrary-task
Racket oracle. Input file: a list of objects containing an `input` grid.
Every run stages an independent runtime in /tmp; no sibling code is imported.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

MAIN = "5ccdbe078da6"
AUDITS = ("55c08ab3ce73", "449ea8b9619c")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def find_repo():
    for parent in Path(__file__).resolve().parents:
        if (parent / "src/arcpuzzles/catalog.py").is_file():
            return parent
    raise RuntimeError("Run this probe within an ARCpuzzles source checkout")


def groups(grid):
    result = {}
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v:
                result.setdefault(v, []).append((r, c))
    return result


def pair_kind(pair):
    (r, c), (s, d) = sorted(pair)
    return "horizontal" if r == s else "vertical" if c == d else "down_right" if c < d else "down_left"


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("main", "audits", "cases", "portable-tests"), default="main")
    parser.add_argument("--task", default=MAIN)
    parser.add_argument("--inputs", type=Path)
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.per_band < 1:
        parser.error("--per-band must be positive")
    if args.mode == "cases" and args.inputs is None:
        parser.error("--inputs is required for --mode cases")
    repo = find_repo()
    out = args.out.resolve()
    baseline = args.baseline.resolve() if args.baseline else None
    inputs = args.inputs.resolve() if args.inputs else None
    command_cwd = Path.cwd().resolve()
    argv = ["python3", *sys.argv]
    sys.path.insert(0, str(repo / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime
    tasks = list(AUDITS) if args.mode == "audits" else ([MAIN, AUDITS[1]] if args.mode == "portable-tests" else [args.task])
    catalog = Catalog(repo)
    report = {
        "schema": "arcpuzzles-task-review-probe-v1", "mode": args.mode,
        "command": {"cwd": str(command_cwd), "argv": argv},
        "probe_sha256": digest(__file__), "python": sys.version,
        "per_band": args.per_band, "seed_range": [0, args.per_band - 1],
        "sample_index_formula": "17 * seed + 3", "failures": [],
        "source": {},
    }
    rows = {}
    for line in (repo / "shared/data/canonical/puzzles.jsonl").open():
        row = json.loads(line)
        if row.get("task_id") in tasks:
            rows[row["task_id"]] = row
    for tid in tasks:
        report["source"][tid] = {
            "generator_sha256": digest(repo / f"generators/{tid}/generator.py"),
            "rule_sha256": hashlib.sha256(rows[tid]["program_solution"].encode()).hexdigest(),
        }
    report["canonical_ledger_sha256"] = digest(repo / "shared/data/canonical/puzzles.jsonl")
    all_cases = []
    lesson_cases = []
    previous_cwd = Path.cwd()
    with tempfile.TemporaryDirectory(prefix="arcpuzzles-review-probe-") as tmp:
        runtime = Path(tmp)
        manifest = prepare_runtime(catalog, runtime, task_ids=tasks)
        report["runtime_directory"] = str(runtime)
        report["runtime_file_count"] = len(manifest["files"])
        report["runtime_manifest_sha256"] = digest(runtime / "RUNTIME_MANIFEST.json")
        sys.path.insert(0, str(runtime))
        os.chdir(runtime)
        from arc_repl.racket_bridge import RacketBridge
        from scripts.rule_smoke import rule_application
        from scripts.coder_synth_verify import _as_pairs, _norm_grid

        modules = {tid: load_module(runtime / f"puzzle_generators/per_puzzle/{tid}/generator.py", "review_" + tid) for tid in tasks}
        bridge = RacketBridge(max_calls_before_restart=48)

        def label(tid, grids):
            labeled = []
            for start in range(0, len(grids), 12):
                batch = grids[start:start + 12]
                code = "(list " + " ".join(rule_application(rows[tid]["program_solution"], grid) for grid in batch) + ")"
                result = bridge.eval_text(code)
                if not isinstance(result, list) or len(result) != len(batch):
                    raise RuntimeError(f"Racket batch returned malformed result for {tid}")
                labeled.extend(result)
            return labeled

        def canonical(tid):
            pairs = [_ for split in ("train", "test") for _ in _as_pairs(rows[tid].get(split))]
            grids = [_norm_grid(pair["input"]) for pair in pairs]
            outputs = label(tid, grids)
            mismatches = sum(actual != _norm_grid(pair["output"]) for actual, pair in zip(outputs, pairs))
            rejected = sum(bool(modules[tid].self_check(grid)) for grid in grids)
            if mismatches or rejected:
                report["failures"].append({"kind": "canonical", "task": tid, "mismatches": mismatches, "rejected": rejected})
            return pairs, grids, outputs

        try:
            if args.mode == "main":
                contract = modules[MAIN]
                pairs, canonical_grids, canonical_outputs = canonical(MAIN)
                report["canonical"] = {"count": len(pairs), "racket_matches": len(pairs),
                    "shortcut_fits": {name: sum(fn(g) == y for g, y in zip(canonical_grids, canonical_outputs))
                                      for name, fn in contract.SEMANTIC_RIVALS.items()}}
                variants = [("final", contract, report["source"][MAIN]["generator_sha256"])]
                if baseline:
                    variants.insert(0, ("before", load_module(baseline, "review_baseline"), digest(baseline)))
                report["variants"] = {}
                for phase, gen, sha in variants:
                    samples = []
                    for band in ("easy", "medium", "hard"):
                        for seed in range(args.per_band):
                            index = 17 * seed + 3
                            grid = gen.generate(seed, index, difficulty=band)
                            samples.append({"phase": phase, "band": band, "seed": seed, "sample_index": index, "input": grid})
                    outputs = label(MAIN, [x["input"] for x in samples])
                    counts, witnesses = Counter(), {}
                    by_band = {band: Counter() for band in ("easy", "medium", "hard")}
                    unique = set()
                    for sample, output in zip(samples, outputs):
                        grid = sample["input"]
                        sample["output"] = output
                        unique.add(json.dumps(grid))
                        counts["samples"] += 1
                        counts["valid"] += not bool(gen.self_check(grid))
                        counts["nonidentity"] += grid != output
                        if phase == "final" and contract.rule_mirror(grid) != output:
                            report["failures"].append({"kind": "mirror_mismatch", **sample})
                        for orientation in {pair_kind(cells) for cells in groups(grid).values()}:
                            counts["has_" + orientation] += 1
                            by_band[sample["band"]]["has_" + orientation] += 1
                        sample["refuted_rivals"] = []
                        for name, fn in contract.SEMANTIC_RIVALS.items():
                            rival = fn(grid)
                            if rival != output:
                                counts["refutes_" + name] += 1
                                by_band[sample["band"]]["refutes_" + name] += 1
                                sample["refuted_rivals"].append(name)
                                witnesses.setdefault(name, {**sample, "rival": name, "rival_output": rival,
                                                           "task_id": MAIN, "generator_sha256": sha,
                                                           "rule_sha256": report["source"][MAIN]["rule_sha256"],
                                                           "self_check": gen.self_check(grid), "documented_domain": True})
                        all_cases.append(sample)
                    report["variants"][phase] = {"generator_sha256": sha, "counts": dict(counts), "unique_inputs": len(unique),
                                                  "by_band": by_band, "witnesses": witnesses}
                # A small reviewer-authored case refutes the strongest two canonical rivals.
                grid = [[2,0,0,0,0], [0,8,0,0,0], [0,0,0,0,0], [0,0,2,0,8]]
                output = label(MAIN, [grid])[0]
                report["minimal_counterexample"] = {
                    "task_id": MAIN, **report["source"][MAIN], "input": grid, "racket_output": output,
                    "self_check": contract.self_check(grid), "documented_domain": True,
                    "origin": "reviewer-authored; generator has constructive marker_overlap support",
                    "numeric_descending_output": contract.rival_numeric_descending(grid),
                    "keep_markers_output": contract.rival_keep_markers(grid),
                }
                # Measure non-overlapping lessons; no independence assumption about per-grid hits.
                lesson_rows = []
                lesson_unique = set()
                gen = contract
                for band in ("easy", "medium", "hard"):
                    grids = [gen.generate(seed, index, difficulty=band)
                             for seed in range(20) for index in range(4)]
                    outputs = label(MAIN, grids)
                    for seed in range(20):
                        start = seed * 4
                        lesson_g, lesson_y = grids[start:start+4], outputs[start:start+4]
                        lesson_unique.update(json.dumps(grid) for grid in lesson_g)
                        lesson_cases.append({"task_id": MAIN, "band": band, "seed": seed,
                            "train": [{"sample_index": j, "input": g, "output": y}
                                      for j, (g, y) in enumerate(zip(lesson_g[:3], lesson_y[:3]))],
                            "test": [{"sample_index": 3, "input": lesson_g[3], "output": lesson_y[3]}]})
                        survivors = [name for name, rival in contract.SEMANTIC_RIVALS.items()
                                     if all(rival(g) == y for g,y in zip(lesson_g[:3], lesson_y[:3]))
                                     and rival(lesson_g[3]) != lesson_y[3]]
                        lesson_rows.append({"band": band, "seed": seed, "demo_indexes": [0,1,2],
                                            "query_index": 3, "query_changing_survivors": survivors})
                report["lesson_audit"] = {"generator_sha256": report["source"][MAIN]["generator_sha256"],
                    "seed_range": [0,19], "lessons": 60, "unique_lesson_grids": len(lesson_unique),
                    "note": "Separate 240-draw population; not added to the main census denominator. Raw examples retained in the lessons JSONL sidecar.",
                    "unidentified_against_named_rivals": sum(bool(x["query_changing_survivors"]) for x in lesson_rows),
                    "rows": lesson_rows}
            elif args.mode == "audits":
                report["audits"] = {}
                for tid in AUDITS:
                    gen = modules[tid]
                    pairs, canonical_grids, canonical_outputs = canonical(tid)
                    samples = [{"task_id": tid, "band": band, "seed": seed, "sample_index": 17*seed+3,
                                "input": gen.generate(seed, 17*seed+3, difficulty=band)}
                               for band in ("easy", "medium", "hard") for seed in range(args.per_band)]
                    outputs = label(tid, [x["input"] for x in samples])
                    counts = Counter(samples=len(samples), canonical_pairs=len(pairs))
                    for sample, output in zip(samples, outputs):
                        sample["output"] = output
                        grid = sample["input"]
                        counts["valid"] += not bool(gen.self_check(grid))
                        counts["nonidentity"] += grid != output
                        counts["deterministic"] += grid == gen.generate(sample["seed"], sample["sample_index"], difficulty=sample["band"])
                        if tid == AUDITS[0]:
                            counts["left_edge_motif"] += any(row[0] not in (0,5) for row in grid)
                        else:
                            counts["python_racket_parity"] += gen.rule_python(grid) == output
                        all_cases.append(sample)
                    audit = {"counts": dict(counts), "unique_inputs": len({json.dumps(s["input"]) for s in samples}),
                             **report["source"][tid]}
                    if tid == AUDITS[0]:
                        grid = canonical_grids[1]; output = canonical_outputs[1]
                        rival = copy.deepcopy(output)
                        for r in range(len(grid)):
                            rival[r][-1] = 0  # canonical width 7, centered divider; omit col0 reflection
                        audit["counterexample"] = {"task_id": tid, **report["source"][tid],
                            "origin": "canonical train[1]", "input": grid, "racket_output": output,
                            "rival_output": rival, "self_check": gen.self_check(grid),
                            "documented_domain": False, "domain_note": "Canonical and validator-accepted; summary/source explicitly exclude column 0.",
                            "finding": "Generator omits an edge-touching motif branch explicitly present in canonical train[1]."}
                        # Reproduce the separate declaration/runtime mismatch without editing the target.
                        try:
                            gen.generate(0, 3, difficulty="easy", grid_h=16)
                            audit["declared_override_probe"] = {"accepted": True}
                        except Exception as exc:
                            audit["declared_override_probe"] = {"seed": 0, "sample_index": 3,
                                "difficulty": "easy", "overrides": {"grid_h": 16},
                                "accepted": False, "error": f"{type(exc).__name__}: {exc}"}
                    else:
                        audit["mutation_rejections"] = {name: gen.self_check(gen.generate(0,0,texture=name))
                                                        for name in gen.DEGENERATE_TEXTURES}
                        if counts["python_racket_parity"] != counts["samples"]:
                            report["failures"].append({"kind": "audit_parity", "task": tid})
                    if counts["valid"] != counts["samples"]:
                        report["failures"].append({"kind": "invalid_generated_audit", "task": tid})
                    report["audits"][tid] = audit
            elif args.mode == "cases":
                cases = json.loads(inputs.read_text())
                if not isinstance(cases, list) or not all(isinstance(case, dict) and "input" in case for case in cases):
                    raise ValueError("Cases file must be a list of objects containing input grids")
                outputs = label(args.task, [case["input"] for case in cases])
                for case, output in zip(cases, outputs):
                    all_cases.append({**case, "output": output,
                                      "self_check": modules[args.task].self_check(case["input"])})
                report["cases"] = all_cases
            else:
                # Existing task tests use legacy runtime/tests as their root. New task-local
                # tests find either source or runtime; run both from this actual /tmp root.
                test_root = runtime / "tests"; test_root.mkdir(exist_ok=True)
                selected = []
                for tid in tasks:
                    # prepare_runtime's inherited map predates newly added task-local tools.
                    # Copy them explicitly into this runtime, never import the source path.
                    source_workspace = repo / f"generators/{tid}/workspace"
                    target_workspace = runtime / f"puzzle_generators/per_puzzle/{tid}/workspace"
                    shutil.copytree(source_workspace, target_workspace, dirs_exist_ok=True,
                                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
                    for test in sorted((repo / f"generators/{tid}/tests").glob("test*.py")):
                        if tid == MAIN:
                            destination = runtime / f"puzzle_generators/per_puzzle/{tid}/tests" / test.name
                        else:
                            destination = test_root / test.name
                        destination.parent.mkdir(exist_ok=True, parents=True)
                        shutil.copy2(test, destination)
                        selected.append(str(destination.relative_to(runtime)))
                command = [sys.executable, "-m", "pytest", "-q", *selected]
                env = dict(os.environ); env["PYTHONPATH"] = str(runtime)
                run = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                     env=env, timeout=180)
                report["test_command"] = {"cwd": str(runtime), "argv": command, "exit_code": run.returncode,
                                           "stdout": run.stdout}
                if run.returncode:
                    report["failures"].append({"kind": "portable_tests", "exit_code": run.returncode})
        finally:
            bridge.shutdown()
            os.chdir(previous_cwd)
    cases_path = out.with_suffix(".cases.jsonl")
    cases_path.parent.mkdir(parents=True, exist_ok=True)
    with cases_path.open("w") as stream:
        for sample in all_cases:
            stream.write(json.dumps(sample, separators=(",", ":")) + "\n")
    if lesson_cases:
        lesson_path = out.with_suffix(".lessons.jsonl")
        lesson_path.write_text("".join(json.dumps(row, separators=(",", ":")) + "\n" for row in lesson_cases))
        report["lesson_cases_file"] = lesson_path.name
        report["lesson_cases_sha256"] = digest(lesson_path)
    report["cases_file"] = cases_path.name
    report["cases_sha256"] = digest(cases_path)
    report["cases_count"] = len(all_cases)
    write_json(out, report)
    print(json.dumps({"out": str(out), "cases": len(all_cases), "failures": len(report["failures"])}))
    return 1 if report["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
