"""Bounded, reproducible protected-Racket audit for the diagonal gap prototype.

Run through the packet's review.py run wrapper. This is authoring evidence, not
native acceptance or a universal identification proof. No controller is built.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arcpuzzles.parametric_worker import evaluate_contract, _real_evaluator
from puzzle_generators.rule_wrap import strip_rule_wrapper, wrap_rule
from reviewer_support import public_challenge_bytes, public_challenge_id

TASK_ID = "59a7762bc6da"
HERE = Path(__file__).resolve().parent
HOME = HERE.parents[1]
ROOT = HERE.parents[3]
POLICIES = ("keep", "bridge_once")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")


def load_adapter():
    spec = importlib.util.spec_from_file_location("_diagonal_gap_audit_adapter", HERE / "adapter.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def pair_condition(dr, dc):
    return (f"(and (= (safe-at g (+ r {dr}) (+ c {dc}) 7) 5) "
            f"(= (safe-at g (- r {dr}) (- c {dc}) 7) 5))")


def bridge_definition(directions=((1, 1), (1, -1))):
    condition = "(or " + " ".join(pair_condition(*d) for d in directions) + ")"
    return f"(define (bridge g) (cellmap g (r c v) (if (and (= v 7) {condition}) 5 v)))"


def compose(core, policy, *, mode="once", directions=((1, 1), (1, -1))):
    """Attach independently authored preprocessing to a complete core rule."""
    if policy == "keep":
        return core
    body = strip_rule_wrapper(core)
    bridge = bridge_definition(directions)
    if mode == "once":
        result = f"({body} (bridge g))"
    elif mode == "iterative":
        result = (f"({body} (let loop ((v g) (remaining 900)) "
                  "(let ((next (bridge v))) (if (or (= remaining 0) (equal? next v)) "
                  "next (loop next (- remaining 1))))))")
    elif mode == "wrong_order":
        result = f"(bridge ({body} g))"
    else:
        raise ValueError(mode)
    return f"(rule! (lambda (g) {bridge} {result}))"


def rivals(canonical, policy):
    predicate = "(>= (maxdiag cells) 3)"
    assert canonical.count(predicate) == 1
    directions = "(list (list 1 1) (list 1 -1))"
    assert canonical.count(directions) == 1
    core = {
        "threshold_two": canonical.replace(predicate, "(>= (maxdiag cells) 2)"),
        "threshold_four": canonical.replace(predicate, "(>= (maxdiag cells) 4)"),
        "exactly_three": canonical.replace(predicate, "(= (maxdiag cells) 3)"),
        "down_right_only": canonical.replace(directions, "(list (list 1 1))"),
        "down_left_only": canonical.replace(directions, "(list (list 1 -1))"),
        "four_connectivity": canonical.replace("(objects-8 g 7)", "(objects g 7)"),
        "size_at_least_three": canonical.replace(predicate, "(>= (length cells) 3)"),
        "bbox_at_least_three": canonical.replace(predicate,
            "(let ((bb (obj-bbox obj))) (and (>= (- (third bb) (first bb)) 2) "
            "(>= (- (fourth bb) (second bb)) 2)))"),
        "every_component": canonical.replace(predicate, "#t"),
        "largest_component_only": canonical.replace(predicate,
            "(and (>= (maxdiag cells) 3) "
            "(= (length cells) (apply max 0 (map obj-size (objects-8 g 7)))))"),
        "orthogonal_runs_also_qualify": canonical.replace(directions,
            "(list (list 1 1) (list 1 -1) (list 1 0) (list 0 1))"),
    }
    on_run = """(filter (lambda (p)
      (ormap (lambda (d)
        (>= (- (+ (run-from cells (fst p) (snd p) (fst d) (snd d))
                  (run-from cells (fst p) (snd p) (- (fst d)) (- (snd d)))) 1) 3))
        (list (list 1 1) (list 1 -1)))) cells)"""
    core["diagonal_cells_only"] = canonical.replace("(recolor-cells acc cells 8)",
                                                     f"(recolor-cells acc {on_run} 8)")
    result = {name: compose(source, policy) for name, source in core.items()}
    if policy == "keep":
        result["bridge_despite_keep"] = compose(canonical, "bridge_once")
    else:
        result.update({
            "skip_bridge": canonical,
            "iterative_bridge": compose(canonical, policy, mode="iterative"),
            "classify_before_bridge": compose(canonical, policy, mode="wrong_order"),
            "bridge_down_right_only": compose(canonical, policy, directions=((1, 1),)),
            "bridge_down_left_only": compose(canonical, policy, directions=((1, -1),)),
            "bridge_orthogonal_too": compose(canonical, policy,
                directions=((1, 1), (1, -1), (1, 0), (0, 1))),
        })
    for source in result.values():
        wrap_rule(source)  # Parse errors are failures, never a refutation.
    return result


def census(adapter):
    rows = []
    failures = []
    for seed in range(20):
        paired = {}
        for policy in POLICIES:
            for demos in (2, 3, 6):
                request = {"seed": seed, "settings": {"gap_policy": policy}, "demos": demos, "queries": 4}
                try:
                    episode = adapter.generate(**request)
                    assert len(episode["train"]) == demos and len(episode["test"]) == 4
                    inputs = [json.dumps(p["input"]) for split in ("train", "test") for p in episode[split]]
                    assert len(inputs) == len(set(inputs))
                    assert all(16 <= len(p["input"]) <= 30 and 16 <= len(p["input"][0]) <= 30
                               for split in ("train", "test") for p in episode[split])
                    shorter = adapter.generate(seed, {"gap_policy": policy}, 2, 1)
                    assert shorter["train"] == episode["train"][:2]
                    assert shorter["test"] == episode["test"][:1]
                    key = demos
                    if policy == "keep":
                        paired[key] = inputs
                    else:
                        assert paired[key] == inputs
                    rows.append(request)
                except Exception as exc:
                    failures.append({**request, "error": f"{type(exc).__name__}: {exc}"})
    return {"requested": 120, "succeeded": len(rows), "failed": len(failures),
            "failures": failures, "scope": "Python construction/count/uniqueness/prefix/paired-input checks only; protected labels are checked separately."}


def export_views(adapter, episodes):
    public = {}
    private = []
    for episode in episodes:
        if episode["seed"] != 0 or len(episode["train"]) != 3:
            continue
        views = []
        for pair_index, pair in enumerate(episode["test"]):
            view = {"train": episode["train"], "test": [pair]}
            raw = public_challenge_bytes(view)
            identifier = public_challenge_id(view)
            assert sha(raw) == identifier
            decoded = json.loads(raw)
            assert set(decoded) == {"train", "test"}
            assert len(decoded["test"]) == 1 and set(decoded["test"][0]) == {"input"}
            assert all(set(p) == {"input", "output"} for p in decoded["train"])
            mutated = copy.deepcopy(view)
            mutated.update({"seed": 812, "settings": {"gap_policy": "redacted"},
                            "program_solution": "private program", "future_queries": []})
            mutated["test"][0]["output"] = [[9]]
            assert public_challenge_bytes(mutated) == raw
            assert public_challenge_id(mutated) == identifier
            if pair_index == 0:
                first = adapter.generate(0, episode["settings"], 3, 1)
                assert public_challenge_bytes(first) == raw
            public[identifier] = raw
            views.append({"query_index": pair_index, "public_id": identifier,
                          "path": f"public/{identifier}.json"})
        private.append({"settings": episode["settings"], "seed": 0, "demos": 3,
                        "views_in_private_order": views})
    assert len(private) == 2 and len(public) == 8
    return public, {"episodes": private,
        "checked": ["one visible query per view", "first turn byte-identical to single-query generation",
                    "opaque SHA256 names depend only on visible bytes", "private metadata and query answers do not affect ID"],
        "consumer_instruction": "The existing consumer selects exactly one view per turn using this private order. Never expose this map, the directory listing, future views, total count, programs or query labels to the model. No controller is included."}


def run(out):
    if not out.resolve().is_relative_to((HERE / "evidence").resolve()):
        raise ValueError("Evidence output must remain under this task's parametric/evidence directory")
    adapter = load_adapter()
    contract = json.loads((HERE / "promotion.json").read_text())
    canonical = (HERE / "canonical.rkt").read_text()
    source_paths = [HERE / "adapter.py", HERE / "promotion.json", HERE / "canonical.rkt", Path(__file__), HOME / "generator.py"]
    source_hashes = {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in source_paths}
    jobs = [{"seed": seed, "settings": {"gap_policy": policy}, "demos": demos, "queries": 4}
            for seed in (0, 17) for policy in POLICIES for demos in (2, 3, 6)]
    execution = evaluate_contract(ROOT, TASK_ID, contract, jobs)
    assert execution["racket"]["backend"] == "racket" and execution["racket"]["protected"] is True
    census_result = census(adapter)
    public, exports = export_views(adapter, execution["episodes"])

    apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
    extra_evaluations = 0
    def execute(program, grid):
        nonlocal extra_evaluations
        extra_evaluations += 1
        value = apply(program, grid)
        assert type(value) is list and len(value) == len(grid)
        assert all(type(row) is list and len(row) == len(grid[0]) and
                   all(type(v) is int and 0 <= v <= 9 for v in row) for row in value)
        return value

    teaching = []
    boundary = []
    canonical_checks = []
    unresolved = []
    try:
        for episode_index, episode in enumerate(execution["episodes"]):
            if len(episode["train"]) != 2:
                continue
            policy = episode["settings"]["gap_policy"]
            results = []
            for name, source in rivals(canonical, policy).items():
                refutation = None
                for pair_index, pair in enumerate(episode["train"]):
                    output = execute(source, pair["input"])
                    if output != pair["output"]:
                        refutation = {"demo_index": pair_index, "input": pair["input"],
                                      "reference_output": pair["output"], "rival_output": output}
                        break
                row = {"name": name, "program": source, "program_sha256": sha(source.encode())}
                if refutation is not None:
                    row.update({"status": "refuted_by_visible_demo", "case": refutation})
                else:
                    # Queries are inspected only AFTER a rival has survived every demo.
                    disagreement = []
                    for pair_index, pair in enumerate(episode["test"]):
                        output = execute(source, pair["input"])
                        if output != pair["output"]:
                            disagreement.append({"query_index": pair_index, "input": pair["input"],
                                "reference_output": pair["output"], "rival_output": output})
                    row.update({"status": "survives_demonstrations", "query_disagreements": disagreement})
                    unresolved.append({"seed": episode["seed"], "settings": episode["settings"],
                                       "rival": name, "query_disagreement_count": len(disagreement)})
                results.append(row)
            teaching.append({"episode_index": episode_index, "seed": episode["seed"],
                             "settings": episode["settings"], "demos_used": 2, "rivals": results,
                             "longer_demo_result": "Same first two demonstrations retained for counts 3 and 6; checked by census."})

        for height, width in ((16, 16), (16, 30), (30, 16), (30, 30)):
            grid = adapter.sample_input(17, "test", 3, height=height, width=width)
            cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 5]
            stats = {"height": height, "width": width, "gray_cells": len(cells),
                     "row_extent": [min(r for r, c in cells), max(r for r, c in cells)],
                     "column_extent": [min(c for r, c in cells), max(c for r, c in cells)],
                     "occupied_quadrants": len({(r >= height / 2, c >= width / 2) for r, c in cells})}
            assert stats["row_extent"] == [0, height - 1]
            assert stats["column_extent"] == [0, width - 1]
            assert stats["occupied_quadrants"] == 4
            if height == width == 30:
                assert len(cells) >= 40
            for policy in POLICIES:
                setting = {"gap_policy": policy}
                program = adapter.program(setting)
                output = execute(program, grid)
                assert output == adapter.transform(grid, setting)
                assert {5, 7, 8} == {v for row in output for v in row}
                boundary.append({**stats, "settings": setting, "input": grid, "output": output,
                                 "program_sha256": sha(program.encode())})

        canonical_row = next(json.loads(line) for line in
            (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
            if json.loads(line).get("task_id") == TASK_ID)
        assert canonical_row["program_solution"] == adapter.program({"gap_policy": "keep"}) == canonical
        for split in ("train", "test"):
            for index, pair in enumerate(canonical_row[split]):
                output = execute(canonical, pair["input"])
                assert output == pair["output"] == adapter.transform(pair["input"], {"gap_policy": "keep"})
                canonical_checks.append({"split": split, "index": index, "input": pair["input"], "output": output})
    finally:
        bridge.close()

    status = "pass" if not unresolved and census_result["failed"] == 0 else "needs_repair"
    summary = {"schema": "arcpuzzles-task-local-authoring-audit-v1", "task_id": TASK_ID,
        "status": status, "source_hashes": source_hashes, "racket": identity,
        "native_jobs": len(execution["episodes"]), "native_labels": sum(c["label_count"] for c in execution["checks"]),
        "native_racket_evaluations": execution["racket_evaluations"], "additional_racket_evaluations": extra_evaluations,
        "teaching_prefixes": len(teaching), "rival_checks": sum(len(t["rivals"]) for t in teaching),
        "refuted_rival_checks": sum(r["status"] == "refuted_by_visible_demo" for t in teaching for r in t["rivals"]),
        "unresolved_rivals": unresolved, "boundary_labels": len(boundary), "canonical_labels": len(canonical_checks),
        "public_views": len(public), "sampling": census_result,
        "limits": "Finite rival set and bounded seeds only, not universal uniqueness or proof over all seeds. Python census does not independently execute labels. Native acceptance and training admission remain pending."}
    dump(out / "execution.json", execution)
    dump(out / "teaching.json", {"source_hashes": source_hashes, "racket": identity, "prefixes": teaching,
        "scope": "Each rival is tested only against visible demonstrations; query answers are used only after complete demo survival to diagnose ambiguity. Errors are fatal rather than refutations."})
    dump(out / "boundary.json", {"source_hashes": source_hashes, "racket": identity, "cases": boundary})
    dump(out / "canonical.json", {"source_hashes": source_hashes, "racket": identity, "cases": canonical_checks})
    dump(out / "private-export-map.json", exports)
    for identifier, raw in public.items():
        path = out / "public" / (identifier + ".json")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    dump(out / "summary.json", summary)
    print(json.dumps({k: summary[k] for k in ("status", "native_jobs", "native_labels", "native_racket_evaluations",
        "additional_racket_evaluations", "rival_checks", "refuted_rival_checks", "unresolved_rivals", "boundary_labels",
        "canonical_labels", "public_views", "sampling")}, sort_keys=True))
    return 0 if status == "pass" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=HERE / "evidence/current")
    args = parser.parse_args()
    return run(args.out)


if __name__ == "__main__":
    raise SystemExit(main())
