#!/usr/bin/env python3
"""Bounded Racket teaching audit, one-query export, and native witness recipe.

Run through review.py run. All public files contain one query only; the report,
parameter maps, programs, future queries and answers stay controller-private.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_pairs, find_root, normalize_grid, public_challenge_bytes, public_challenge_id


HOME = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("_audited_native_frame_family", HOME / "family.py")
family = importlib.util.module_from_spec(spec)
spec.loader.exec_module(family)
DEPENDENCY = {
    "step_a": "Move the original row-major first marker to the first empty cell in the diagonally opposite exterior corner, scanning row-major.",
    "intermediate": "The changed grid and its newly ordered pair of markers; relocation can change which color is row-major first.",
    "step_b": "Extract the markers again from the changed grid, derive the new first marker's quadrant parity, and execute the canonical frame fill.",
    "why_b_depends_on_a": "The relocated marker can move after the other marker while preserving its own parity. Filling from the original marker binding then changes interior colors even when both programs perform identical exterior relocation.",
}


def raw(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw(value))


def evaluator(bridge):
    cache, wrapped = {}, {}
    def execute(program, grid):
        key = (program, raw(grid))
        if key not in cache:
            if program not in wrapped:
                wrapped[program] = wrap_rule(program)
            literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
            cache[key] = normalize_grid(bridge.eval_text(f"({wrapped[program]} {literal})"))
        return cache[key]
    return execute, cache


def run_audit(out, seeds=(0, 17), demo_counts=(3, 6)):
    out = Path(out)
    if out.exists():
        raise FileExistsError(out)
    root = find_root(__file__)
    public_files, episodes, checks, geometries = {}, [], [], []
    programs = {mode: family.program({"phase_relation": mode}) for mode in family.SETTINGS}
    with RacketBridge() as bridge:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise ValueError("audit requires the actual protected Racket backend")
        execute, cache = evaluator(bridge)
        canonical_checked = 0
        for pair in canonical_pairs(family.TASK_ID, root=root, labeled_only=True):
            if execute(programs["same"], pair["input"]) != pair["output"]:
                raise AssertionError("canonical label mismatch")
            canonical_checked += 1
        for seed in seeds:
            for demos in demo_counts:
                input_reference = None
                for mode in family.SETTINGS:
                    settings = {"phase_relation": mode}
                    episode = family.generate(seed, settings, demos, 4)
                    inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
                    if len({raw(grid) for grid in inputs}) != len(inputs):
                        raise AssertionError("duplicate input")
                    if input_reference is not None and inputs != input_reference:
                        raise AssertionError("settings confound the input stream")
                    input_reference = inputs
                    for pair in episode["train"] + episode["test"]:
                        if execute(programs[mode], pair["input"]) != pair["output"]:
                            raise AssertionError(f"label mismatch for {mode}, seed {seed}")
                    for pair in episode["test"]:
                        f = family.analyze(pair["input"])
                        geometries.append({"shape": [f["h"], f["w"]],
                            "frame_shape": [f["bottom"] - f["top"] + 1, f["right"] - f["left"] + 1],
                            "painted_interior_cells": (f["bottom"] - f["top"] - 1) * (f["right"] - f["left"] - 1),
                            "first_corner": family.marker_quadrant(f["markers"][0], f)})
                    rivals = {"setting:" + name: source for name, source in programs.items() if name != mode}
                    rivals.update(family.rival_programs(settings))
                    teaching = []
                    for name, source in rivals.items():
                        mismatches = [i for i, pair in enumerate(episode["train"])
                                      if execute(source, pair["input"]) != pair["output"]]
                        query_differences = []
                        if not mismatches:
                            query_differences = [i for i, pair in enumerate(episode["test"])
                                                 if execute(source, pair["input"]) != pair["output"]]
                        if query_differences:
                            raise AssertionError(f"harmful rival survives: {mode}/{seed}/{demos}/{name}/{query_differences}")
                        teaching.append({"name": name, "program_sha256": hashlib.sha256(source.encode()).hexdigest(),
                            "mismatching_demo_indices": mismatches,
                            "status": "refuted" if mismatches else "survives_agrees_on_queries"})
                    one = family.generate(seed, settings, demos, 1)
                    if public_challenge_bytes(family.public_query(one, 0)) != public_challenge_bytes(family.public_query(episode, 0)):
                        raise AssertionError("first-turn payload depends on future query count")
                    public_ids = []
                    for index in range(4):
                        public = family.public_query(episode, index)
                        payload = public_challenge_bytes(public)
                        ident = public_challenge_id(public)
                        if ident in public_files:
                            raise AssertionError("duplicate model-visible public payload")
                        public_files[ident] = payload
                        public_ids.append(ident)
                    episodes.append({"seed": seed, "settings": settings, "demos": demos,
                        "public_query_ids": public_ids, **episode})
                    checks.append({"seed": seed, "settings": settings, "demos": demos, "queries": 4,
                        "label_count": demos + 4, "teaching": teaching})

        # Minimal retained teaching hole: the first two demos permit column-only
        # phase; the third demo is the repair, and query 2 supplies a witness.
        episode = family.generate(17, {"phase_relation": "same"}, 3, 4)
        wrong = family.rival_programs({"phase_relation": "same"})["column_only"]
        demos = episode["train"][:2]
        query = episode["test"][2]
        if not all(execute(wrong, p["input"]) == p["output"] for p in demos):
            raise AssertionError("retained two-demo counterexample no longer reproduces")
        wrong_output = execute(wrong, query["input"])
        if wrong_output == query["output"] or execute(wrong, episode["train"][2]["input"]) == episode["train"][2]["output"]:
            raise AssertionError("third demo must repair the retained teaching hole")
        hole = {"status": "reproduced_and_repaired_by_third_demo", "settings": {"phase_relation": "same"},
            "train": demos, "test": [query], "distinguishing_demo": episode["train"][2],
            "program": programs["same"], "counterfactual_program": wrong,
            "counterfactual_output": wrong_output,
            "different_query_cells": sum(a != b for ar, br in zip(query["output"], wrong_output) for a, b in zip(ar, br))}
        evaluation_count = len(cache)
    # Publish only after all labels, rivals and projection checks succeeded.
    out.mkdir(parents=True)
    for ident, payload in sorted(public_files.items()):
        path = out / "public" / f"{ident}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    for index, episode in enumerate(episodes):
        write(out / "private" / "episodes" / f"{index:03}.json", episode)
    write(out / "private" / "two-demo-counterexample.json", hole)
    write(out / "private" / "teaching.json", checks)
    for mode, source in programs.items():
        p = out / "private" / "rules" / f"{mode}.rkt"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(source)
    inventory = [{"path": p.relative_to(out).as_posix(), "bytes": p.stat().st_size, "sha256": sha(p)}
                 for p in sorted(out.rglob("*")) if p.is_file()]
    rival_checks = [r for check in checks for r in check["teaching"]]
    report = {"schema": "b7c3b8bc9805-native-audit-v1", "status": "passed", "training_admitted": False,
        "task_id": family.TASK_ID, "seeds": list(seeds), "demo_counts": list(demo_counts),
        "sources": [{"path": p.relative_to(root).as_posix(), "sha256": sha(p)}
                    for p in sorted(HOME.glob("*")) if p.suffix in (".py", ".json")],
        "racket": identity, "racket_evaluations": evaluation_count,
        "counts": {"episodes_attempted": len(episodes), "episodes_successful": len(episodes),
            "episodes_failed": 0, "canonical_pairs": canonical_checked,
            "labeled_pairs": sum(c["label_count"] for c in checks), "public_one_query_challenges": len(public_files),
            "rival_checks": len(rival_checks), "rivals_refuted": sum(r["status"] == "refuted" for r in rival_checks),
            "harmful_survivors": 0},
        "query_geometry_profiles": [json.loads(value) for value in sorted({json.dumps(g, sort_keys=True) for g in geometries})],
        "public_files": sorted("public/" + ident + ".json" for ident in public_files),
        "files": inventory,
        "limits": ["Finite declared rivals and sampled seeds only; no universal identifiability or measured learning gain.",
                   "Three demonstrations are required; arbitrary two-demo or query-rotation assembly is unsupported.",
                   "Native owner acceptance and downstream training admission remain separate.",
                   "Exactly two markers and one complete frame; extra colored distractors are outside this grammar."]}
    write(out / "report.json", report)
    return report


def witness_recipe(qualification, out):
    out = Path(out)
    if out.exists():
        raise FileExistsError(out)
    qualification = Path(qualification)
    q = json.loads(qualification.read_bytes())
    execution_path = qualification.with_name("execution.json")
    if q.get("status") != "qualified" or q.get("execution") != {"path": "execution.json", "sha256": sha(execution_path)}:
        raise ValueError("qualification needs a matching execution file")
    execution = json.loads(execution_path.read_bytes())
    index = next(i for i, e in enumerate(execution["episodes"]) if e["settings"] == {"phase_relation": "move_then_fill"})
    episode = execution["episodes"][index]
    grid = episode["test"][0]["input"]
    moved = family.move_input(grid)
    if episode["program"] != family.program(episode["settings"]):
        raise ValueError("qualification program differs from current source")
    result = {**DEPENDENCY, "cases": [{"episode_index": index, "split": "test", "pair_index": 0,
        "ablation": "wrong_intermediate", "counterfactual_program": family.stale_order_program(),
        "intermediate_value": {"original_markers": family.analyze(grid)["markers"],
            "moved_markers": family.analyze(moved)["markers"], "moved_grid": moved}}]}
    write(out, result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    audit = sub.add_parser("audit")
    audit.add_argument("--out", type=Path, required=True)
    audit.add_argument("--seeds", type=int, nargs="+", default=[0, 17])
    audit.add_argument("--demos", type=int, nargs="+", default=[3, 6])
    recipe = sub.add_parser("witness-recipe")
    recipe.add_argument("--qualification", type=Path, required=True)
    recipe.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "audit":
        report = run_audit(args.out, tuple(args.seeds), tuple(args.demos))
        print(json.dumps({"status": report["status"], "counts": report["counts"], "report": str(args.out / "report.json")}))
    else:
        witness_recipe(args.qualification, args.out)
        print(json.dumps({"status": "recipe_written", "path": str(args.out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
