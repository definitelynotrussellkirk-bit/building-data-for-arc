"""Replay an authored distance-metric ambiguity and its three-demo repair.

This is a proposed-curriculum counterexample, not an ordinary production draw.
All retained intended and alternative labels come from protected Racket.  The
probe deliberately tests only the Euclidean and Chebyshev metric alternatives.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TASK = "fae242ae157d"
PRODUCTION_SHA = "2cc4c3997a0cebffdc3b6c25d6bdf5598f9f5811ede610d1a805b4b0b73a9f70"
CANONICAL_SHA = "ce7e86577c9974e15935224c415054977e6b7ffb2d2a5d712842ed39b1dff1e4"
DRAFT_SHA = "1b866de5023750ca280f9588fc70e53dbe2b33e2e212ce6bcec642069897985f"
sys.dont_write_bytecode = True


def sha(data):
    return hashlib.sha256(data).hexdigest()


def source_hashes():
    paths = {ROOT / "generators" / TASK / "generator.py"}
    paths.update(p for p in HERE.rglob("*")
                 if p.is_file() and p.suffix in {".py", ".rkt", ".json"}
                 and not {"__pycache__", "evidence", "examples"}.intersection(
                     p.relative_to(HERE).parts))
    return {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in sorted(paths)}


def differing_cells(a, b):
    if len(a) != len(b) or any(len(x) != len(y) for x, y in zip(a, b)):
        raise ValueError("metric rival changed grid dimensions")
    return [{"row": r, "column": c, "intended": a[r][c], "alternative": b[r][c]}
            for r in range(len(a)) for c in range(len(a[r])) if a[r][c] != b[r][c]]


def pick_rival(rivals, token):
    names = [name for name in rivals if token in name.lower()]
    if len(names) != 1:
        raise ValueError(f"expected exactly one {token} rival, found {names}")
    name = names[0]
    program = rivals[name]
    if not isinstance(program, str) or not program.lstrip().startswith("(rule!"):
        raise ValueError("alternative must be a complete standalone Racket rule")
    return name, program


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draft", type=Path,
                        default=ROOT.parent / "checks" / TASK / "distance-lesson-draft.json")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 17])
    args = parser.parse_args()
    if not 1 <= len(args.seeds) <= 2 or len(set(args.seeds)) != len(args.seeds):
        raise ValueError("this bounded probe supports one or two distinct repair seeds")
    if args.out.exists():
        raise FileExistsError(f"output must be new: {args.out}")
    before = source_hashes()
    if before[f"generators/{TASK}/generator.py"] != PRODUCTION_SHA:
        raise ValueError("production generator differs from the reviewed source")
    draft_bytes = args.draft.read_bytes()
    if sha(draft_bytes) != DRAFT_SHA:
        raise ValueError("authored draft bytes differ from the retained specification")
    draft = json.loads(draft_bytes)
    if draft["provenance"]["kind"] != "authored_proposed_curriculum_counterexample":
        raise ValueError("draft must retain its authored provenance")
    old_inputs = [_grid(pair["input"]) for pair in draft["demos"]]
    queries = [_grid(pair["input"]) for pair in draft["queries"]]
    if len(old_inputs) != 3 or len(queries) != 1:
        raise ValueError("this bounded probe requires exactly three demos and one query")
    canonical = {record["program_solution"]
                 for line in (ROOT / "shared/data/canonical/puzzles.jsonl").open()
                 if (record := json.loads(line)).get("task_id") == TASK}
    if len(canonical) != 1 or sha(next(iter(canonical)).encode()) != CANONICAL_SHA:
        raise ValueError("canonical authority differs from the reviewed source")
    cases = []
    evaluations = 0
    cache = {}
    cache_hits = 0
    with _local_imports(ROOT / "shared/runtime", HERE):
        spec = importlib.util.spec_from_file_location("_fae_distance_family", HERE / "native_family.py")
        family = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = family
        spec.loader.exec_module(family)
        if family.program({"ranking_policy": "area"}) != next(iter(canonical)):
            raise ValueError("area default no longer preserves exact canonical program bytes")
        apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            bridge.close()
            raise ValueError("the probe requires the real protected Racket evaluator")

        def execute(program, grid):
            nonlocal evaluations, cache_hits
            key = (program, json.dumps(grid, separators=(",", ":")))
            if key in cache:
                cache_hits += 1
                return deepcopy(cache[key])
            original = deepcopy(grid)
            actual = _grid(apply(program, grid))
            evaluations += 1
            if grid != original:
                raise ValueError("reference execution mutated an input")
            cache[key] = deepcopy(actual)
            return actual

        try:
            for policy in ("nearest_largest", "farthest_largest"):
                settings = {"ranking_policy": policy}
                program = family.program(settings)
                rival_map = family.rivals(settings)
                candidates = [pick_rival(rival_map, token)
                              for token in ("euclidean", "chebyshev")]
                intended_old = [execute(program, grid) for grid in old_inputs]
                intended_query = execute(program, queries[0])
                repairs = []
                for seed in args.seeds:
                    repaired = family.generate(seed, settings, 3, 4)["train"]
                    if len(repaired) != 3:
                        raise ValueError("repaired family must return exactly three demonstrations")
                    repaired_inputs = [_grid(pair["input"]) for pair in repaired]
                    intended_repaired = [execute(program, grid) for grid in repaired_inputs]
                    if any(actual != pair["output"]
                           for actual, pair in zip(intended_repaired, repaired)):
                        raise ValueError("repaired demonstration claim differs from executed Racket")
                    repairs.append({"seed": seed, "demonstrations": [
                        {"input": grid, "output": output}
                        for grid, output in zip(repaired_inputs, intended_repaired)]})
                rivals = []
                for name, alternative in candidates:
                    old_outputs = [execute(alternative, grid) for grid in old_inputs]
                    query_output = execute(alternative, queries[0])
                    demo_fits = [a == b for a, b in zip(intended_old, old_outputs)]
                    query_difference = differing_cells(intended_query, query_output)
                    repaired_results = []
                    for repair in repairs:
                        repaired_outputs = [execute(alternative, pair["input"])
                                            for pair in repair["demonstrations"]]
                        refutations = [i for i, (pair, output) in enumerate(zip(
                            repair["demonstrations"], repaired_outputs)) if pair["output"] != output]
                        if not refutations:
                            raise ValueError("the repaired three demos do not refute a metric rival")
                        repaired_results.append({"seed": repair["seed"],
                                                 "demo_outputs": repaired_outputs,
                                                 "demo_refutations": refutations})
                    if not all(demo_fits) or not query_difference:
                        raise ValueError("the retained ambiguity/repair claim failed execution")
                    rivals.append({"name": name, "program": alternative,
                                   "program_sha256": sha(alternative.encode()),
                                   "original_demo_fits": demo_fits,
                                   "original_demo_outputs": old_outputs,
                                   "query_output": query_output,
                                   "query_differences": query_difference,
                                   "query_different_cell_count": len(query_difference),
                                   "repair_checks": repaired_results})
                cases.append({
                    "settings": settings, "program": program,
                    "program_sha256": sha(program.encode()),
                    "original_lesson_scope": "authored_pre_repair_parametric_curriculum_draft",
                    "original_lesson": {
                        "train": [{"input": grid, "output": output}
                                  for grid, output in zip(old_inputs, intended_old)],
                        "test": [{"input": queries[0], "output": intended_query}]},
                    "repaired_demo_scope": "three_demos_from_current_parametric_family",
                    "repairs": repairs,
                    "rivals": rivals})
        finally:
            bridge.close()
    after = source_hashes()
    if after != before:
        raise ValueError("source changed while the bounded probe was running")
    report = {
        "schema": "arc-protected-authored-distance-lesson-v1", "task_id": TASK,
        "status": "authored_ambiguity_reproduced_and_current_three_demo_repair_verified",
        "source_hashes": after, "canonical_program_sha256": CANONICAL_SHA,
        "canonical_rule_hash": CANONICAL_SHA[:12],
        "draft_path": str(args.draft), "draft_sha256": sha(draft_bytes),
        "evaluator": identity, "protected_racket_evaluations": evaluations,
        "executed_result_cache_hits": cache_hits,
        "cases": cases,
        "limits": [
            "The original witness is an authored design draft, not an ordinary production draw, "
            "saved canonical lesson, or completed native production episode.",
            "The repair check covers at most two seeds, three demonstrations, two policies and exactly "
            "two metric rivals. It establishes no universal identifiability guarantee.",
            "Only retained inputs were reference-executed; unused generated queries were not "
            "screened by this focused probe.",
            "Execution errors abort the probe; they are never counted as rival refutations."]}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], "out": str(args.out),
                      "sha256": sha(args.out.read_bytes()), "racket_evaluations": evaluations,
                      "case_count": len(cases)}, sort_keys=True))


if __name__ == "__main__":
    main()
