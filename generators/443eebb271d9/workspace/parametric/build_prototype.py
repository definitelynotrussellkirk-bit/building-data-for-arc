#!/usr/bin/env python3
"""Bounded protected-Racket evidence, finite-rival audit and safe public views."""
from __future__ import annotations
import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

from arcpuzzles.parametric_worker import evaluate_contract, _real_evaluator
from reviewer_support import find_root, load_selected_generator, public_challenge_bytes

TASK_ID = "443eebb271d9"
HERE = Path(__file__).resolve().parent

def _load(name):
    path = HERE / f"{name}.py"
    key = "_443_native_evidence_" + name + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(key, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def _sha(data):
    return hashlib.sha256(data if isinstance(data, bytes) else data.encode()).hexdigest()

def _write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")

def public_views(episode):
    """Independent single-query projections; ordering and full pool stay private."""
    return [public_challenge_bytes({"train": episode["train"], "test": [pair]})
            for pair in episode["test"]]

def write_public_views(directory, episode):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    identifiers = []
    for body in public_views(episode):
        identifier = _sha(body)
        path = directory / (identifier + ".json")
        if path.exists() and path.read_bytes() != body:
            raise ValueError("public content ID collision")
        path.write_bytes(body)
        identifiers.append(identifier)
    return identifiers

def rival_programs(period):
    """Nearby total competitors on this family's admitted nonempty glyph inputs."""
    prototype = _load("prototype")
    base = prototype.racket_program({"special_period": period})
    def change(old, new):
        if old not in base:
            raise AssertionError("Racket source anchor changed: " + old)
        return base.replace(old, new)
    propagation = f"(or (zero? row-rep)\n                    (= (mod inst {period}) {period - 1}))"
    phase = change(f"(mod inst {period}) {period - 1}", f"(mod inst {period}) 0")
    phase = phase.replace(f"{period})\n                          {period - 1})",
                          f"{period})\n                          0)")
    single = change(f"(= (mod inst {period}) {period - 1})", f"(= inst {period - 1})")
    single = single.replace(f"(= (mod (quotient (- c c0) hstep) {period})\n                          {period - 1})",
                            f"(= (quotient (- c c0) hstep) {period - 1})")
    biggest = f"""(lambda (g)
  (let* ((cells (obj-cells (largest-object g 0)))
         (source (cellmap g (r c v) (if (member (list r c) cells) 7 0))))
    ({base} source)))"""
    clipped = change("(< local-r gh)",
                     "(and (< local-r gh) (<= (+ r0 (* row-rep vstep) gh) h))")
    clipped = clipped.replace("(< local-c gw)",
                              "(and (< local-c gw) (<= (+ c0 (* inst hstep) gw) w))")
    rivals = {
        "other_period": prototype.racket_program({"special_period": 5 - period}),
        "largest_component_only": biggest,
        "filled_bounding_rectangle": change("(= (safe-at g (+ r0 local-r) (+ c0 local-c) 0) 7)", "#t"),
        "fixed_horizontal_pitch_3": change("(define hstep (+ gw 1))", "(define hstep 3)"),
        "fixed_vertical_pitch_3": change("(define vstep (+ gh 1))", "(define vstep 3)"),
        "zero_gap": base.replace("(define hstep (+ gw 1))", "(define hstep gw)")
                        .replace("(define vstep (+ gh 1))", "(define vstep gh)"),
        "two_cell_gap": base.replace("(define hstep (+ gw 1))", "(define hstep (+ gw 2))")
                            .replace("(define vstep (+ gh 1))", "(define vstep (+ gh 2))"),
        "canvas_origin_bbox": base.replace("(define r0 (first bb))", "(define r0 0)")
                                  .replace("(define c0 (second bb))", "(define c0 0)"),
        "first_instance_phase": phase,
        "only_first_special_instance": single,
        "top_row_only": change(propagation, "(zero? row-rep)"),
        "all_columns_down": change(propagation, "#t"),
        "drop_partial_copies": clipped,
    }
    return {name: "(rule! " + source + ")" for name, source in rivals.items()}

def _different(left, right):
    if len(left) != len(right) or any(len(a) != len(b) for a, b in zip(left, right)):
        return -1
    return sum(a != b for lr, rr in zip(left, right) for a, b in zip(lr, rr))

def audit_lessons(episodes, runtime):
    apply, identity, bridge = _real_evaluator(runtime)
    result, witnesses, programs, calls = [], [], {}, 0
    try:
        for episode in episodes:
            if len(episode["train"]) != 2:
                continue
            period = episode["settings"]["special_period"]
            rivals = rival_programs(period)
            programs[str(period)] = rivals
            for name, program in rivals.items():
                demo_labels = [apply(program, p["input"]) for p in episode["train"]]
                query_labels = [apply(program, p["input"]) for p in episode["test"]]
                calls += len(demo_labels) + len(query_labels)
                # Errors are fatal, never evidence that a competing rule was refuted.
                for label in demo_labels + query_labels:
                    if (type(label) is not list or not label or type(label[0]) is not list
                        or not label[0] or any(type(row) is not list or len(row) != len(label[0])
                        or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in label)):
                        raise ValueError("Rival returned invalid grid: " + name)
                rejected = [i for i, (label, pair) in enumerate(zip(demo_labels, episode["train"]))
                            if label != pair["output"]]
                changes = [_different(label, pair["output"])
                           for label, pair in zip(query_labels, episode["test"])]
                ambiguity = not rejected and any(changes)
                result.append({"seed": episode["seed"], "settings": episode["settings"],
                               "rival": name, "program_sha256": _sha(program),
                               "rejecting_demo_indices": rejected,
                               "query_difference_cells": changes, "ambiguity": ambiguity})
                if ambiguity:
                    raise AssertionError("Demo-fit/query-diverge rival: " + name)
                if not any(w["settings"] == episode["settings"] and w["rival"] == name
                           for w in witnesses) and rejected:
                    index = rejected[0]
                    pair = episode["train"][index]
                    witnesses.append({"settings": episode["settings"], "rival": name,
                                      "seed": episode["seed"], "demo_index": index,
                                      "input": pair["input"], "output": pair["output"],
                                      "rival_output": demo_labels[index]})
    finally:
        bridge.close()
    return {"racket": identity, "racket_evaluations": calls, "checks": result,
            "minimal_witnesses": witnesses, "programs": programs,
            "limit": "Finite listed rivals on the bounded two-demo lessons; not universal uniqueness."}

def _projection_checks(adapter, episodes, public_dir):
    checked, public_files = 0, []
    for episode in episodes:
        if len(episode["train"]) != 3 or episode["seed"] != 0:
            continue
        identifiers = write_public_views(public_dir, episode)
        public_files.append({"settings": episode["settings"], "seed": episode["seed"],
                             "query_public_ids": identifiers})
        body = public_views(episode)[0]
        single = adapter.generate(episode["seed"], episode["settings"], 3, 1)
        if public_views(single)[0] != body:
            raise AssertionError("one/four-query first turn differs")
        hidden = deepcopy(episode)
        hidden["seed"] = -1
        hidden["settings"] = {"changed": "private"}
        hidden["program"] = "private altered source"
        for pair in hidden["test"]:
            pair["output"] = [[9]]
        if public_views(hidden) != public_views(episode):
            raise AssertionError("public identity depends on private metadata/answers")
        first = deepcopy(episode)
        first["test"][1:] = []
        if public_views(first)[0] != body:
            raise AssertionError("first turn depends on later queries")
        parsed = json.loads(body)
        if set(parsed) != {"train", "test"} or len(parsed["test"]) != 1 or set(parsed["test"][0]) != {"input"}:
            raise AssertionError("unexpected public fields")
        checked += 1
    bad_cases, sample = [], deepcopy(episodes[0])
    for value in (True, 1.0, -1, 10):
        bad = deepcopy(sample)
        bad["test"][0]["input"][0][0] = value
        try:
            public_views(bad)
        except ValueError:
            bad_cases.append(repr(value))
        else:
            raise AssertionError("public serializer accepted invalid color")
    bad = deepcopy(sample)
    bad["test"][0]["input"][0].pop()
    try:
        public_views(bad)
    except ValueError:
        bad_cases.append("ragged")
    else:
        raise AssertionError("public serializer accepted ragged input")
    return {"settings_checked": checked, "query_views": 4 * checked,
            "first_turn_identical": True, "private_metadata_invariant": True,
            "future_queries_not_visible": True, "rejected_bad_grids": bad_cases,
            "private_public_map": public_files}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()
    out = args.out_dir.resolve()
    if out.exists():
        parser.error("output already exists; choose a fresh evidence directory")
    root = Path(find_root(__file__))
    adapter = _load("adapter")
    contract = json.loads((HERE / "promotion.json").read_text())
    jobs = [{"seed": seed, "settings": {"special_period": period}, "demos": demos, "queries": 4}
            for demos in (2, 3, 6) for period in (3, 2) for seed in (0, 2, 17)]
    execution = evaluate_contract(root, TASK_ID, contract, jobs)
    audit = audit_lessons(execution["episodes"], root / "shared/runtime")
    generator, _, source_sha = load_selected_generator(TASK_ID, root=root)
    coverage = []
    for episode in execution["episodes"]:
        for split in ("train", "test"):
            for pair in episode[split]:
                errors = generator.self_check(pair["input"])
                if errors:
                    raise AssertionError(errors)
                positions = [(r, c) for r, row in enumerate(pair["output"])
                             for c, v in enumerate(row) if v]
                coverage.append({"seed": episode["seed"], "settings": episode["settings"],
                                 "split": split, "size": [len(pair["input"]), len(pair["input"][0])],
                                 "nonzero_output": len(positions),
                                 "furthest_row": max(r for r, _ in positions),
                                 "furthest_col": max(c for _, c in positions)})
    draws, failures = 0, []
    for seed in (0, 2, 17):
        for demos in range(2, 7):
            for period in (3, 2):
                draws += 1
                try:
                    e = adapter.generate(seed, {"special_period": period}, demos, 4)
                    assert len(e["train"]) == demos and len(e["test"]) == 4
                    assert len({_sha(json.dumps(p["input"])) for p in e["train"] + e["test"]}) == demos + 4
                except Exception as exc:
                    failures.append({"seed": seed, "demos": demos, "period": period, "error": str(exc)})
    if failures:
        raise AssertionError(failures)
    projection = _projection_checks(adapter, execution["episodes"], out / "public")
    _write(out / "private/execution.json", execution)
    _write(out / "private/teaching.json", audit)
    _write(out / "private/public-map.json", projection.pop("private_public_map"))
    _write(out / "private/coverage.json", coverage)
    summary = {"schema": "arcpuzzles-native-authoring-evidence-v1", "task_id": TASK_ID,
               "status": "reviewer_checked_owner_acceptance_pending", "training_admitted": False,
               "generator_sha256": source_sha,
               "source_sha256": {p.name: _sha(p.read_bytes()) for p in sorted(HERE.glob("*"))
                                  if p.is_file() and p.suffix in (".py", ".rkt", ".json")},
               "racket": execution["racket"], "executed_jobs": len(jobs),
               "executed_labels": sum(c["label_count"] for c in execution["checks"]),
               "native_racket_evaluations": execution["racket_evaluations"],
               "teaching_racket_evaluations": audit["racket_evaluations"],
               "rivals_per_setting": len(rival_programs(3)),
               "teaching_lessons": sum(len(e["train"]) == 2 for e in execution["episodes"]),
               "unrefuted_query_divergent_rivals": 0,
               "request_census": {"attempts": draws, "successes": draws - len(failures), "failures": failures},
               "sizes": sorted({tuple(c["size"]) for c in coverage}), "public_projection": projection,
               "command": {"cwd": "repo", "argv": ["python3", str(Path(__file__).relative_to(root)),
                                                   "--out-dir", str(args.out_dir)]},
               "limits": ["Finite setting/seed/rival checks, not universal uniqueness or measured model benefit.",
                          "Derived geometry controls subsequent placement; this is not iterative grid-state simulation.",
                          "Every source color-7 fragment is a glyph part; unrelated distractors are outside the grammar.",
                          "Old special-period-v1/final examples are superseded historical evidence, not public training inputs."]}
    _write(out / "summary.json", summary)
    print(json.dumps({k: summary[k] for k in ("status", "executed_jobs", "executed_labels", "rivals_per_setting",
                                            "unrefuted_query_divergent_rivals", "request_census", "sizes")}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

