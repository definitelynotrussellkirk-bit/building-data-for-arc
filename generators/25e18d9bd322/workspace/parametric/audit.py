"""Bounded teaching, protected-label and public-projection audit for this family.

Run through review.py run with --out pointing to a new directory. The audit
never changes production, accepts a family, or admits examples to training.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

from arcpuzzles.parametric_worker import evaluate_contract, _local_imports, _real_evaluator
from reviewer_support import public_challenge_bytes, public_challenge_id


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TASK = "25e18d9bd322"


def local_module(name):
    spec = importlib.util.spec_from_file_location("nearest_audit_" + name, HERE / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def coverage(grid, adapter):
    marker, objs = adapter.analyze(grid)
    return {"height": len(grid), "width": len(grid[0]), "components": len(objs),
            "candidate_cells": sum(len(o["cells"]) for o in objs),
            "interior_candidate_cells": sum(v not in (0, 9) for row in grid[1:-1] for v in row[1:-1]),
            "marker": marker,
            "largest_component": max(len(o["cells"]) for o in objs),
            "selected_bbox": {metric: [len(adapter.solve(grid, metric)), len(adapter.solve(grid, metric)[0])]
                              for metric in adapter.METRICS}}


def run(out):
    if out.exists() or out.is_symlink():
        raise ValueError("Choose a new output directory; existing evidence is never overwritten")
    out = out.resolve()
    adapter, rivals = local_module("adapter"), local_module("rivals")
    seeds = (0, 17, 29, 2**63 - 1)
    checked = []
    for seed in seeds:
        for demos in (2, 3, 6):
            inputs = []
            for metric in adapter.METRICS:
                episode = adapter.generate(seed, {"metric": metric}, demos, 4)
                rows = rivals.check_episode(episode)
                if any(row["survives_demos"] for row in rows):
                    raise AssertionError({"seed": seed, "demos": demos, "metric": metric,
                                          "survivors": [r for r in rows if r["survives_demos"]]})
                one = adapter.generate(seed, {"metric": metric}, demos, 1)
                if adapter.public_turn(episode, 0) != adapter.public_turn(one, 0):
                    raise AssertionError("first visible turn depends on hidden future queries")
                altered = copy.deepcopy(episode)
                altered.update(seed=-1, settings={"private": True}, program_solution="private")
                for pair in altered["train"]:
                    pair.update(seed=-1, settings={"private": True}, program_solution="private")
                for pair in altered["test"]:
                    pair["output"] = [[9]]
                if (public_challenge_bytes(episode) != public_challenge_bytes(altered)
                        or public_challenge_id(episode) != public_challenge_id(altered)
                        or adapter.public_turn(episode, 0) != adapter.public_turn(altered, 0)):
                    raise AssertionError("private metadata leaked to public bytes, IDs or single-query turns")
                inputs.append([p["input"] for split in ("train", "test") for p in episode[split]])
                checked.append({"seed": seed, "settings": episode["settings"], "demos": demos,
                                "queries": 4, "rivals": rows,
                                "query_coverage": [coverage(p["input"], adapter) for p in episode["test"]]})
            if inputs[0] != inputs[1]:
                raise AssertionError("input distribution depends on selected setting")

    contract = json.loads((HERE / "promotion.json").read_text())
    jobs = [{"seed": 29, "settings": {"metric": metric}, "demos": demos, "queries": 4}
            for metric in adapter.METRICS for demos in (2, 6)]
    execution = evaluate_contract(ROOT, TASK, contract, jobs)
    minimum = [[9, 3, 0, 0, 0], [0, 3, 0, 0, 0], [0] * 5, [0] * 5, [0, 0, 0, 0, 4]]
    tied = [[0] * 12 for _ in range(7)]
    tied[0][9] = 9
    a = {(1, c) for c in range(2, 9)} | {(2, 8)} | {(3, c) for c in range(4, 9)}
    b = {(r, 10) for r in range(1, 5)} | {(5, c) for c in range(2, 11)}
    for cells, color in ((a, 7), (b, 2)):
        for r, c in cells:
            tied[r][c] = color
    literal_checks = []
    with _local_imports(ROOT / "shared/runtime", HERE):
        apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
        try:
            for name, grid in (("minimum_5x5_marker_contact", minimum), ("complete_key_tie", tied)):
                for metric in adapter.METRICS:
                    actual = apply(adapter.program({"metric": metric}), grid)
                    if actual != adapter.solve(grid, metric):
                        raise AssertionError(name + " differs from protected Racket")
                    literal_checks.append({"case": name, "settings": {"metric": metric},
                                           "input": grid, "output": actual})
        finally:
            bridge.close()
    if identity != execution["racket"]:
        raise AssertionError("protected runtime changed during audit")

    public, turns, private = {}, {}, []
    for episode in (e for e in execution["episodes"] if len(e["train"]) == 2):
        public_id = public_challenge_id(episode)
        if public_id in public:
            raise AssertionError("duplicate visible challenge")
        public[public_id] = public_challenge_bytes(episode)
        turn_ids = []
        for index in range(4):
            turn = adapter.public_turn(episode, index)
            turn_id = public_challenge_id(turn)
            if turn_id in turns:
                raise AssertionError("duplicate visible turn")
            turns[turn_id] = public_challenge_bytes(turn)
            turn_ids.append(turn_id)
        private.append({"public_id": public_id, "turn_ids": turn_ids, "seed": episode["seed"],
                        "settings": episode["settings"], "program": episode["program"],
                        "program_sha256": episode["program_sha256"],
                        "query_answers": [p["output"] for p in episode["test"]],
                        "teaching": rivals.check_episode(episode), "reference": "qualified_prototype",
                        "owner_acceptance": "pending", "training_admitted": False})
    source = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(HERE.iterdir()) if p.suffix in (".py", ".rkt", ".json")}
    report = {"schema": "nearest-object-metric-audit-v1", "task_id": TASK, "passed": True,
              "source_sha256": source, "attempted_episodes": len(checked),
              "successful_episodes": len(checked), "failed_episodes": 0,
              "seeds": list(seeds), "demos_exercised": [2, 3, 6], "queries": 4,
              "rivals": list(rivals.RIVALS), "rival_survivors": 0,
              "finite_rival_evaluations": len(checked) * len(rivals.RIVALS),
              "checked_episodes": checked, "protected_jobs": jobs,
              "racket": identity, "racket_evaluations": execution["racket_evaluations"] + len(literal_checks),
              "literal_checks": literal_checks, "public_examples": len(public),
              "single_query_turns": len(turns), "owner_acceptance": "pending", "training_admitted": False,
              "limits": ["Twenty-two declared Python rivals and the listed seeds/counts; no universal uniqueness claim.",
                         "Protected Racket executes both declared metric programs and all labels on the four audit jobs plus literal boundaries; extra rivals are Python hypotheses.",
                         "Four-query public files are private controller storage; reveal only one public_turns file to an actor per user turn.",
                         "The native worker's generic reference string does not grant owner acceptance or training admission."]}
    out.mkdir(parents=True, exist_ok=False)
    write_json(out / "report.json", report)
    write_json(out / "execution.json", execution)
    write_json(out / "private.json", sorted(private, key=lambda row: row["public_id"]))
    for folder, files in (("public", public), ("public_turns", turns)):
        (out / folder).mkdir()
        for public_id, data in sorted(files.items()):
            (out / folder / (public_id + ".json")).write_bytes(data)
    return {k: report[k] for k in ("passed", "attempted_episodes", "successful_episodes",
            "failed_episodes", "rival_survivors", "finite_rival_evaluations",
            "racket_evaluations", "public_examples", "single_query_turns")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    print(json.dumps(run(parser.parse_args().out), indent=2))
