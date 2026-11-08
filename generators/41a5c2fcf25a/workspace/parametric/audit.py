"""Reproducible bounded teaching, label and public-projection audit.

Run from the repository through review.py run; --out must be a new directory.
No network, acceptance, training admission, or writes outside --out.
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
TASK = "41a5c2fcf25a"


def local_module(name):
    spec = importlib.util.spec_from_file_location("rank_audit_" + name, HERE / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def stats(grid, adapter):
    cells = [(r, c) for r in range(1, len(grid)) for c, v in enumerate(grid[r]) if v]
    return {"height": len(grid), "width": len(grid[0]), "body_cells": len(cells),
            "components": len(adapter.components(grid)),
            "row_span": max(r for r, c in cells) - min(r for r, c in cells) + 1,
            "column_span": max(c for r, c in cells) - min(c for r, c in cells) + 1,
            "touches_bottom": any(r == len(grid) - 1 for r, c in cells),
            "touches_left": any(c == 0 for r, c in cells),
            "touches_right": any(c == len(grid[0]) - 1 for r, c in cells)}


def run(out):
    if out.exists():
        raise ValueError("Refusing to replace existing audit output")
    adapter, rivals = local_module("adapter"), local_module("rivals")
    seeds = (0, 17, 29, 2**63 - 1)
    checked = []
    for seed in seeds:
        for demos in (2, 3, 6):
            matched = []
            for metric in adapter.METRICS:
                episode = adapter.generate(seed, {"rank_by": metric}, demos, 4)
                rows = rivals.check_episode(episode)
                if any(row["survives_demos"] for row in rows):
                    raise AssertionError({"seed": seed, "demos": demos, "metric": metric,
                                          "survivors": [r for r in rows if r["survives_demos"]]})
                if adapter.public_turn(episode, 0) != adapter.public_turn(
                        adapter.generate(seed, {"rank_by": metric}, demos, 1), 0):
                    raise AssertionError("first-turn content depends on hidden future queries")
                changed = copy.deepcopy(episode)
                changed.update(seed=-1, settings={"hidden": True}, program_solution="hidden")
                for pair in changed["test"]:
                    pair["output"] = [[9]]
                if (public_challenge_bytes(episode) != public_challenge_bytes(changed)
                        or public_challenge_id(episode) != public_challenge_id(changed)):
                    raise AssertionError("private metadata changes visible bytes or IDs")
                matched.append([p["input"] for split in ("train", "test") for p in episode[split]])
                checked.append({"seed": seed, "settings": episode["settings"], "demos": demos,
                                "queries": 4, "rivals": rows,
                                "query_coverage": [stats(p["input"], adapter) for p in episode["test"]]})
            if matched[0] != matched[1]:
                raise AssertionError("input distribution leaks the selected setting")

    contract = json.loads((HERE / "promotion.json").read_text())
    jobs = [{"seed": 29, "settings": {"rank_by": metric}, "demos": demos, "queries": 4}
            for metric in adapter.METRICS for demos in (2, 6)]
    execution = evaluate_contract(ROOT, TASK, contract, jobs)
    # A literal minimum accepted 5x5 grid checks the parser/domain boundary.
    minimum = [[3, 8, 0, 0, 0], [8, 0, 0, 0, 0], [8, 0, 0, 0, 0],
               [0, 0, 0, 0, 0], [0, 0, 0, 0, 8]]
    tied = [[0] * 12 for _ in range(7)]
    tied[0][:2] = [3, 4]
    first = {(1, c) for c in range(2, 9)} | {(2, 8)} | {(3, c) for c in range(4, 9)}
    second = {(r, 10) for r in range(1, 5)} | {(5, c) for c in range(2, 11)}
    for r, c in first | second:
        tied[r][c] = 8
    literal_checks = []
    with _local_imports(ROOT / "shared/runtime", HERE):
        apply, runtime, bridge = _real_evaluator(ROOT / "shared/runtime")
        try:
            for name, grid in (("minimum_5x5", minimum), ("complete_sort_key_tie", tied)):
                for metric in adapter.METRICS:
                    actual = apply(adapter.program({"rank_by": metric}), grid)
                    expected = adapter.solve(grid, metric)
                    if actual != expected:
                        raise AssertionError(name + " literal Racket mismatch")
                    if name == "complete_sort_key_tie" and (actual[1][2] != 4 or actual[1][10] != 3):
                        raise AssertionError("canonical reverse-discovery fallback changed")
                    literal_checks.append({"case": name, "settings": {"rank_by": metric},
                                           "input": grid, "output": actual})
        finally:
            bridge.close()
    if runtime != execution["racket"]:
        raise AssertionError("audit evaluator identity changed")

    examples = [e for e in execution["episodes"] if len(e["train"]) == 2]
    public, turns, private = {}, {}, []
    for episode in examples:
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
                        "reference": "qualified_prototype", "owner_acceptance": "pending",
                        "training_admitted": False, "teaching": rivals.check_episode(episode)})
    bindings = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(HERE.iterdir()) if p.suffix in (".py", ".rkt", ".json")}
    report = {"schema": "area-perimeter-audit-v1", "task_id": TASK, "passed": True,
              "source_sha256": bindings, "attempted_episodes": len(checked),
              "successful_episodes": len(checked), "failed_episodes": 0,
              "demos_exercised": [2, 3, 6], "queries": 4, "seeds": list(seeds),
              "rivals": list(rivals.RIVALS), "finite_rival_evaluations": len(checked) * len(rivals.RIVALS),
              "rival_survivors": 0, "checked_episodes": checked,
              "racket": runtime, "racket_evaluations": execution["racket_evaluations"] + len(literal_checks),
              "protected_jobs": jobs, "literal_checks": literal_checks,
              "public_examples": len(public), "single_query_turns": len(turns),
              "limits": ["Only twelve declared Python rival hypotheses and the listed seeds/counts are checked.",
                         "Protected Racket executes both declared programs and all labels on the four audit jobs; finite extra rivals are Python hypotheses.",
                         "Public four-query files are controller storage; give an actor only one public_turns file per user turn.",
                         "This audit neither accepts the family nor admits training data."]}
    out.mkdir(parents=True)
    dump(out / "report.json", report)
    dump(out / "execution.json", execution)
    dump(out / "private.json", sorted(private, key=lambda row: row["public_id"]))
    for folder, files in (("public", public), ("public_turns", turns)):
        (out / folder).mkdir()
        for identity, data in sorted(files.items()):
            (out / folder / (identity + ".json")).write_bytes(data)
    return {k: report[k] for k in ("passed", "attempted_episodes", "successful_episodes",
            "failed_episodes", "rivals", "rival_survivors", "racket_evaluations",
            "public_examples", "single_query_turns")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.out.resolve()), indent=2))
