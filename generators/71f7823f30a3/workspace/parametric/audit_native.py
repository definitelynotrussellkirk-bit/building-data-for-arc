#!/usr/bin/env python3
"""Independent, bounded teaching audit for row-local mirror variants.

Only demonstrations select surviving hypotheses. Each query is checked against
that frozen set, without using another query's answer. Demo-refuted hypotheses
are never executed on queries. Retained labels come from protected Racket and
are checked against the independent Python semantics below.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve()
ROOT = next(parent for parent in HERE.parents if (parent / "shared/runtime").is_dir())
TASK_ID = "71f7823f30a3"
POLICIES = ("all", "nearest_color", "farthest_color")
RIVALS = (
    "policy_all", "policy_nearest_color", "policy_farthest_color",
    "nearest_cell", "farthest_cell", "global_first_anchor", "center_axis",
    "left_only", "right_only", "global_nearest_color", "global_farthest_color",
    "most_frequent_color", "least_frequent_color",
    "most_frequent_nearest_tie", "most_frequent_farthest_tie",
    "least_frequent_nearest_tie", "least_frequent_farthest_tie",
    "minimum_mean_color", "maximum_mean_color",
    "minimum_max_distance_color", "maximum_min_distance_color",
    *(f"fixed_color_{color}" for color in range(1, 9)),
    "reflect_orphans", "move_sources",
)


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _policy(settings):
    if not isinstance(settings, dict) or set(settings) - {"copy_policy"}:
        raise ValueError("settings must contain only copy_policy")
    policy = settings.get("copy_policy", "all")
    if policy not in POLICIES:
        raise ValueError(f"unknown copy_policy {policy!r}")
    return policy


def _configuration(settings, name=None):
    config = {"selector": _policy(settings), "axis": "row", "side": "both",
              "orphans": False, "move": False, "global_cue": False}
    if name is None:
        return config
    if name not in RIVALS:
        raise ValueError(f"unknown rival {name!r}")
    if name.startswith("policy_"):
        config["selector"] = name[len("policy_"):]
    elif (name in ("nearest_cell", "farthest_cell") or "frequent" in name
          or name.startswith(("fixed_color_", "minimum_", "maximum_"))):
        config["selector"] = name
    elif name in ("global_first_anchor", "center_axis"):
        config["axis"] = name
    elif name in ("left_only", "right_only"):
        config["side"] = name
    elif name in ("global_nearest_color", "global_farthest_color"):
        config["global_cue"] = True
        config["selector"] = name[len("global_"):]
    elif name == "reflect_orphans":
        config["orphans"] = True
    elif name == "move_sources":
        config["move"] = True
    return config


def _sources(row):
    return [col for col, color in enumerate(row) if 1 <= color <= 8]


def _anchor(row):
    return next((col for col, color in enumerate(row) if color == 9), -1)


def _selected(row, sources, anchor, selector):
    if not sources:
        return []
    if selector == "all":
        return sources[:]
    if selector.startswith("fixed_color_"):
        color = int(selector.rsplit("_", 1)[1])
        return [col for col in sources if row[col] == color]
    distance = lambda col: abs(col - anchor)
    if selector in ("nearest_color", "nearest_cell"):
        cue = min(sources, key=distance)
    elif selector in ("farthest_color", "farthest_cell"):
        cue = max(sources, key=distance)
    elif selector.startswith(("minimum_", "maximum_")):
        distances = {color: [distance(col) for col in sources if row[col] == color]
                     for color in {row[col] for col in sources}}
        if "mean" in selector:
            key = lambda col: Fraction(sum(distances[row[col]]), len(distances[row[col]]))
        elif selector == "minimum_max_distance_color":
            key = lambda col: max(distances[row[col]])
        else:
            key = lambda col: min(distances[row[col]])
        cue = (min if selector.startswith("minimum_") else max)(sources, key=key)
    else:
        counts = Counter(row[col] for col in sources)
        most = selector.startswith("most_frequent")
        if selector.endswith("nearest_tie"):
            key = lambda col: ((-1 if most else 1) * counts[row[col]], distance(col))
        elif selector.endswith("farthest_tie"):
            key = lambda col: ((-1 if most else 1) * counts[row[col]], -distance(col))
        else:
            key = lambda col: ((-1 if most else 1) * counts[row[col]], col)
        cue = min(sources, key=key)
    if selector.endswith("_cell"):
        return [cue]
    return [col for col in sources if row[col] == row[cue]]


def _transform(grid, config):
    """Pure snapshot semantics; no native-family helpers or program mutations."""
    result = deepcopy(grid)
    width = len(grid[0])
    anchors = [_anchor(row) for row in grid]
    first_row = next((row for row, anchor in enumerate(anchors) if anchor >= 0), None)
    first_anchor = anchors[first_row] if first_row is not None else -1
    global_color = -1
    if config["global_cue"] and first_row is not None:
        row = grid[first_row]
        selected = _selected(row, _sources(row), first_anchor, config["selector"])
        if selected:
            global_color = row[selected[0]]
    for r, row in enumerate(grid):
        anchor = anchors[r]
        if anchor < 0:
            if config["orphans"]:
                anchor = first_anchor
            else:
                continue
        elif config["axis"] == "global_first_anchor":
            anchor = first_anchor
        elif config["axis"] == "center_axis":
            anchor = width // 2
        if anchor < 0:
            continue
        sources = _sources(row)
        selected = ([col for col in sources if row[col] == global_color]
                    if config["global_cue"] else _selected(row, sources, anchor, config["selector"]))
        if config["side"] == "left_only":
            selected = [col for col in selected if col < anchor]
        elif config["side"] == "right_only":
            selected = [col for col in selected if col > anchor]
        for col in selected:
            target = 2 * anchor - col
            if 0 <= target < width and row[target] == 0:
                if config["move"]:
                    result[r][col] = 0
                result[r][target] = row[col]
    return result


def python_intended(grid, settings):
    return _transform(grid, _configuration(settings))


def python_rival(grid, settings, name):
    return _transform(grid, _configuration(settings, name))


def intermediate(grid, settings):
    """Reviewer interpretation: each row's cue color and every consumer of it."""
    policy = _policy(settings)
    result = []
    for r, row in enumerate(grid):
        anchor = _anchor(row)
        sources = _sources(row)
        if anchor < 0 or not sources:
            continue
        selected = _selected(row, sources, anchor, policy)
        cue = (None if policy == "all" else
               (min if policy == "nearest_color" else max)(sources, key=lambda col: abs(col - anchor)))
        result.append({"row": r, "anchor": anchor, "cue_column": cue,
                       "cue_distance": None if cue is None else abs(cue - anchor),
                       "selected_color": None if cue is None else row[cue],
                       "matching_source_columns": selected,
                       "reflected_target_columns": [2 * anchor - col for col in selected]})
    return result


def _racket_selected(selector, row="r", sources="ss", anchor="axis"):
    if selector == "all":
        return sources
    if selector.startswith("fixed_color_"):
        color = selector.rsplit("_", 1)[1]
        return f"(filter (lambda (p) (= (cell-at g {row} p) {color})) {sources})"
    distance = f"(abs (- p {anchor}))"
    if selector in ("nearest_color", "nearest_cell", "farthest_color", "farthest_cell"):
        aggregate = "argmin" if selector.startswith("nearest") else "argmax"
        cue = f"({aggregate} (lambda (p) {distance}) {sources})"
    elif selector in ("minimum_mean_color", "maximum_mean_color"):
        comparison = "<" if selector.startswith("minimum_") else ">"
        # The protected DSL truncates division. Compare exact means by cross-product.
        cue = f"""(for/fold ([best (first {sources})]) ([p (rest {sources})])
          (let* ([current-cells (filter (lambda (q) (= (cell-at g {row} q) (cell-at g {row} p))) {sources})]
                 [best-cells (filter (lambda (q) (= (cell-at g {row} q) (cell-at g {row} best))) {sources})]
                 [current-sum (apply + (map (lambda (q) (abs (- q {anchor}))) current-cells))]
                 [best-sum (apply + (map (lambda (q) (abs (- q {anchor}))) best-cells))])
            (if ({comparison} (* current-sum (length best-cells)) (* best-sum (length current-cells))) p best)))"""
    elif selector in ("minimum_max_distance_color", "maximum_min_distance_color"):
        aggregate, inner = (("argmin", "max") if selector.startswith("minimum_") else ("argmax", "min"))
        key = (f"(apply {inner} (map (lambda (q) (abs (- q {anchor}))) "
               f"(filter (lambda (q) (= (cell-at g {row} q) (cell-at g {row} p))) {sources})))")
        cue = f"({aggregate} (lambda (p) {key}) {sources})"
    else:
        # The (w+1) factor makes frequency primary and distance a strict tie-break.
        count = f"(length (filter (lambda (q) (= (cell-at g {row} p) (cell-at g {row} q))) {sources}))"
        most = selector.startswith("most_frequent")
        aggregate = "argmax" if most else "argmin"
        if selector.endswith("nearest_tie"):
            key = f"({'-' if most else '+'} (* {count} (+ w 1)) {distance})"
        elif selector.endswith("farthest_tie"):
            key = f"({'+' if most else '-'} (* {count} (+ w 1)) {distance})"
        else:
            key = count
        cue = f"({aggregate} (lambda (p) {key}) {sources})"
    selected = f"(list {cue})" if selector.endswith("_cell") else (
        f"(let ([chosen (cell-at g {row} {cue})]) "
        f"(filter (lambda (p) (= (cell-at g {row} p) chosen)) {sources}))")
    return f"(if (empty? {sources}) '() {selected})"


def rival_program(settings, name):
    """Standalone hypotheses, built independently of every native program."""
    config = _configuration(settings, name)
    if config["axis"] == "global_first_anchor":
        anchored_axis = "first-axis"
    elif config["axis"] == "center_axis":
        anchored_axis = "(quotient w 2)"
    else:
        anchored_axis = "actual-axis"
    absent_axis = "first-axis" if config["orphans"] else "-1"
    axis = f"(if (< actual-axis 0) {absent_axis} {anchored_axis})"
    chosen = _racket_selected(config["selector"])
    if config["global_cue"]:
        global_selected = _racket_selected(config["selector"], "first-row", "first-sources", "first-axis")
        global_binding = f"""[first-sources (row-sources first-row)]
       [global-selected {global_selected}]
       [global-color (if (empty? global-selected) -1 (cell-at g first-row (first global-selected)))]"""
        chosen = "(filter (lambda (p) (= (cell-at g r p) global-color)) ss)"
    else:
        global_binding = ""
    if config["side"] == "left_only":
        side_filter = "(filter (lambda (p) (< p axis)) picked)"
    elif config["side"] == "right_only":
        side_filter = "(filter (lambda (p) (> p axis)) picked)"
    else:
        side_filter = "picked"
    moved = ("(and (member c selected) (>= reflected 0) (< reflected w) "
             "(= (cell-at g r reflected) 0))" if config["move"] else "#f")
    return f"""(rule! (lambda (g)
  (let* ([h (rows g)]
       [w (cols g)]
       [row-anchor (lambda (r)
         (let ([found (filter (lambda (c) (= (cell-at g r c) 9)) (range w))])
           (if (empty? found) -1 (first found))))]
       [row-sources (lambda (r)
         (filter (lambda (c) (and (> (cell-at g r c) 0) (< (cell-at g r c) 9))) (range w)))]
       [anchor-rows (filter (lambda (r) (>= (row-anchor r) 0)) (range h))]
       [first-row (if (empty? anchor-rows) 0 (first anchor-rows))]
       [first-axis (if (empty? anchor-rows) -1 (row-anchor first-row))]
       {global_binding}
       [plans (map (lambda (r)
         (let* ([actual-axis (row-anchor r)]
                [axis {axis}]
                [ss (row-sources r)]
                [picked {chosen}]
                [selected {side_filter}])
           (list axis selected))) (range h))])
    (grid-from-fn h w (lambda (r c)
      (let* ([plan (list-ref plans r)]
             [axis (first plan)]
             [selected (second plan)]
             [original (cell-at g r c)]
             [reflected (- (* 2 axis) c)])
        (if (< axis 0) original
          (if (> original 0)
            (if {moved} 0 original)
            (if (and (>= reflected 0) (< reflected w) (member reflected selected))
              (cell-at g r reflected) original)))))))))"""


def score_lesson(intended_demos, intended_queries, rival_demos, rival_queries):
    """Query labels cannot remove a rival that survives every demonstration."""
    if not intended_demos or not intended_queries:
        raise ValueError("a lesson requires demonstrations and queries")
    if any(len(values) != len(intended_demos) for values in rival_demos.values()):
        raise ValueError("rival label count differs from the lesson")
    survivors = sorted(name for name, values in rival_demos.items() if values == intended_demos)
    if not set(survivors) <= set(rival_queries) <= set(rival_demos):
        raise ValueError("query labels must cover every demo survivor and no undeclared rivals")
    if any(len(values) != len(intended_queries) for values in rival_queries.values()):
        raise ValueError("rival label count differs from the lesson")
    queries = []
    for index, output in enumerate(intended_queries):
        disagreeing = [name for name in survivors if rival_queries[name][index] != output]
        queries.append({"query_index": index, "surviving_disagreeing_rivals": disagreeing,
                        "identified_within_declared_rivals": not disagreeing})
    return {"surviving_rivals_after_demonstrations": survivors,
            "refuted_rivals": sorted(set(rival_demos) - set(survivors)),
            "queries": queries,
            "ok": all(query["identified_within_declared_rivals"] for query in queries)}


def _load_family():
    for path in (ROOT / "src", ROOT / "shared/runtime", HERE.parent):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
    spec = importlib.util.spec_from_file_location("native_teaching_family_71f7823f30a3", HERE.with_name("native_family.py"))
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load native family")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def build_report(seeds=(0, 1), demonstrations=2):
    if type(demonstrations) is not int or not 2 <= demonstrations <= 6:
        raise ValueError("audit demonstrations must lie in 2..6")
    if not seeds or len(seeds) > 4 or any(type(seed) is not int or seed < 0 for seed in seeds):
        raise ValueError("audit requires one to four nonnegative exact integer seeds")
    family = _load_family()
    from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator
    runtime = ROOT / "shared/runtime"
    rows, failures, candidates, program_inventory = [], [], [], {}
    executed = 0
    input_sets = {}
    with _local_imports(runtime, HERE.parent):
        apply, identity, bridge = _real_evaluator(runtime)
        try:
            for seed in seeds:
                for policy in POLICIES:
                    settings = {"copy_policy": policy}
                    episode = family.generate(seed, settings, demos=demonstrations, queries=4)
                    pairs = episode["train"] + episode["test"]
                    program = family.program(settings)
                    intended = [_grid(apply(program, pair["input"])) for pair in pairs]
                    executed += len(pairs)
                    if intended != [pair["output"] for pair in pairs]:
                        raise AssertionError("intended Racket label differs from generated claim")
                    if intended != [python_intended(pair["input"], settings) for pair in pairs]:
                        raise AssertionError("intended labels differ between independent Python and Racket")
                    demos, programs = {}, {}
                    for name in RIVALS:
                        programs[name] = rival_program(settings, name)
                        digest = hashlib.sha256(programs[name].encode()).hexdigest()
                        program_inventory[digest] = programs[name]
                        demos[name] = [_grid(apply(programs[name], pair["input"])) for pair in episode["train"]]
                        executed += demonstrations
                        independent = [python_rival(pair["input"], settings, name) for pair in episode["train"]]
                        if demos[name] != independent:
                            raise AssertionError(f"rival {name} differs between independent Python and Racket")
                    # Freeze survivors before executing any rival on any query.
                    survivors = sorted(name for name, labels in demos.items() if labels == intended[:demonstrations])
                    queries = {}
                    for name in survivors:
                        queries[name] = [_grid(apply(programs[name], pair["input"])) for pair in episode["test"]]
                        executed += 4
                        independent = [python_rival(pair["input"], settings, name) for pair in episode["test"]]
                        if queries[name] != independent:
                            raise AssertionError(f"surviving rival {name} differs between independent Python and Racket")
                    scored = score_lesson(intended[:demonstrations], intended[demonstrations:], demos, queries)
                    rival_checks = {name: {
                        "program_sha256": hashlib.sha256(programs[name].encode()).hexdigest(),
                        "same_policy_control": name == f"policy_{policy}",
                        "refuting_demonstrations": [i for i in range(demonstrations) if demos[name][i] != intended[i]],
                        "query_execution": "executed" if name in queries else "not_run_already_refuted",
                        "disagreeing_queries": ([i for i in range(4) if queries[name][i] != intended[demonstrations + i]]
                                                if name in queries else None),
                        "demonstration_label_sha256": [_hash(output) for output in demos[name]],
                        "query_label_sha256": [_hash(output) for output in queries.get(name, [])],
                    } for name in RIVALS}
                    inputs = [_hash(pair["input"]) for pair in pairs]
                    input_sets.setdefault(seed, []).append(inputs)
                    rows.append({"seed": seed, "settings": settings, "demonstrations": demonstrations,
                                 "query_count": 4, "program": program,
                                 "input_sha256": inputs, "unique_inputs": len(set(inputs)),
                                 "intended_label_sha256": [_hash(output) for output in intended],
                                 "rival_checks": rival_checks, **scored})
                    for query in scored["queries"]:
                        for name in query["surviving_disagreeing_rivals"]:
                            index = query["query_index"]
                            failures.append({"seed": seed, "settings": settings, "program": program,
                                             "train": deepcopy(episode["train"]), "query_index": index,
                                             "input": episode["test"][index]["input"],
                                             "output": intended[demonstrations + index], "rival": name,
                                             "rival_program": programs[name], "rival_output": queries[name][index]})
                    if policy != "all" and seed == seeds[0]:
                        opposite = "policy_farthest_color" if policy == "nearest_color" else "policy_nearest_color"
                        if demos[opposite][0] != intended[0]:
                            candidates.append({"seed": seed, "settings": settings, "program": program,
                                               "input": pairs[0]["input"], "output": intended[0],
                                               "counterfactual_program": programs[opposite],
                                               "counterfactual_output": demos[opposite][0],
                                               "ablation": "wrong_intermediate",
                                               "intermediate_value": intermediate(pairs[0]["input"], settings)})
                    print(json.dumps({"completed_seed": seed, "copy_policy": policy,
                                      "surviving_rivals": survivors, "ok": scored["ok"]}), flush=True)
        finally:
            bridge.close()
    source_names = ("native_family.py", "adapter.py", "promotion.json", "audit_native.py", "canonical.rkt")
    inventory = {name: hashlib.sha256(HERE.with_name(name).read_bytes()).hexdigest()
                 for name in source_names if HERE.with_name(name).is_file()}
    shared_inputs = all(all(group == groups[0] for group in groups) for groups in input_sets.values())
    return {"schema": "71f7823f30a3-native-teaching-audit-v1", "task_id": TASK_ID,
            "source_sha256": inventory, "racket": identity, "executed_labels": executed,
            "seeds": list(seeds), "rivals": list(RIVALS), "rival_programs": program_inventory,
            "episodes": rows, "counterexamples": failures, "causal_candidates": candidates,
            "all_intended_and_rival_labels_match_independent_python": True,
            "identical_inputs_across_settings": shared_inputs,
            "execution_scope": "All intended labels; every rival on demonstrations; only demo-surviving rivals on queries.",
            "ok": shared_inputs and not failures and all(row["ok"] and row["unique_inputs"] == demonstrations + 4 for row in rows),
            "limits": [
                "Finite declared-rival audit; no universal identification claim or native acceptance.",
                "The matching policy hypothesis is an answer-equivalent positive control, not a wrong-rule ambiguity.",
                "All rivals retain source cells unless explicitly testing movement; occupied and out-of-bounds targets are skipped.",
                "The center-axis rival uses floor(width/2); missing anchors normally preserve the entire row.",
                "Reflect-orphans uses the first anchored row's axis for rows that have no anchor.",
                "Frequency ties use first source in column order, nearest source, and farthest source as separate hypotheses.",
                "Color means use exact rational comparison; group-distance rivals also minimize the maximum or maximize the minimum distance.",
                "Only demonstrations determine survivor hypotheses; queries are assessed independently.",
            ]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1])
    parser.add_argument("--demos", type=int, default=2)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = build_report(tuple(args.seeds), args.demos)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"ok": report["ok"], "episodes": len(report["episodes"]),
                      "rivals": len(RIVALS), "executed_labels": report["executed_labels"],
                      "counterexamples": len(report["counterexamples"]), "out": str(args.out)}, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
