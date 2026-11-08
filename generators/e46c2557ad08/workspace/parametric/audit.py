"""Bounded protected-Racket audit and qualification-derived private evidence.

Run through the packet's review.py run launcher.  Without --qualification,
exercise two and six demonstrations at seed 29 for both settings.  With a
native qualification, publish public-byte-named examples and a causal witness.
Every destination must be new.  Neither mode accepts variants or training data.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TASK_ID = "e46c2557ad08"
HOME = Path(__file__).resolve().parent
ROOT = HOME.parents[3]
STEP_A = (
    "Merge blue (1) into gray (5), then discover maximal four-connected gray "
    "components in the merged grid."
)
INTERMEDIATE = (
    "The merged grid and the newly computed gray components, including each "
    "component's cells and normalized shape."
)
STEP_B = (
    "Select resulting gray components with normalized cells [[0,0],[0,1]] "
    "and recolor all their cells cyan (8)."
)
WHY_B_DEPENDS_ON_A = (
    "A blue cell can complete a gray singleton into a horizontal domino or "
    "attach to an original gray domino and make a larger non-target. Target "
    "membership must therefore be determined after the components are "
    "recomputed; the witness contains both creation and destruction."
)
DEPENDENCY = {
    "step_a": STEP_A,
    "intermediate": INTERMEDIATE,
    "step_b": STEP_B,
    "why_b_depends_on_a": WHY_B_DEPENDS_ON_A,
}
LIMITS = (
    "Finite declared settings, named executable rivals and sampled inputs only; "
    "no universal identifiability, universal depth, acceptance or training admission."
)
_H2 = "(equal? (sort (normalize-cells (obj-cells obj)) cell<) '((0 0) (0 1)))"
_MERGE = "(recolor g 1 5)"


def _bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode()


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def _write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_bytes(value))


def _new_output(path):
    if path.exists() or path.is_symlink():
        raise FileExistsError(f"Refusing existing evidence destination: {path}")


def _prototype():
    path = HOME / "prototype.py"
    name = "_e46c2557ad08_audit_" + _sha(str(path).encode())
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load adjacent prototype: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _sources():
    paths = [HOME / name for name in
             ("prototype.py", "adapter.py", "promotion.json", "canonical.rkt", "audit.py")]
    paths.append(ROOT / "generators" / TASK_ID / "generator.py")
    return {path.relative_to(ROOT).as_posix(): _sha(path.read_bytes()) for path in paths}


@contextmanager
def _racket():
    from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator

    runtime = ROOT / "shared/runtime"
    with _local_imports(runtime, HOME):
        apply, _, bridge = _real_evaluator(runtime)
        calls = {"evaluations": 0}

        def execute(program, grid, *, grid_result=True):
            calls["evaluations"] += 1
            result = apply(program, _grid(grid))
            return _grid(result) if grid_result else result

        try:
            yield execute, bridge.runtime_identity, calls
        finally:
            bridge.close()


def wrong_order_program(prototype, settings):
    from puzzle_generators.rule_wrap import strip_rule_wrapper

    if settings["preprocess"] == "none":
        return prototype.CANONICAL_PROGRAM
    body = strip_rule_wrapper(prototype.CANONICAL_PROGRAM)
    return f"(rule! (recolor {body} 1 5))"


def _rivals(prototype, settings):
    if settings["preprocess"] == "nearest_vertical":
        base = prototype.NEAREST_VERTICAL_PROGRAM
        distance = """(+ (abs (- (first ca) (first cb)))
           (abs (- (second ca) (second cb))))"""
        squared = """(let ((dr (- (first ca) (first cb))) (dc (- (second ca) (second cb))))
           (+ (* dr dr) (* dc dc)))"""
        chebyshev = """(max (abs (- (first ca) (first cb)))
           (abs (- (second ca) (second cb))))"""
        rivals = {
            "all_horizontal": prototype.program({"preprocess": "none"}),
            "merge_then_all_horizontal": prototype.program({"preprocess": "blue_to_gray"}),
            "fixed_top_left": prototype.TOP_LEFT_COUNTERFACTUAL_PROGRAM,
            "farthest_vertical": base.replace("(< da db)", "(> da db)"),
            "squared_euclidean": base.replace(distance, squared),
            "chebyshev": base.replace(distance, chebyshev),
        }
        # Reuse the exact color/shape selector, replacing only distance with
        # an extremum score. The retained lexicographic tie break is total.
        for name, score in {
            "leftmost": "(min-list (map second (obj-cells b)))",
            "rightmost": "(- (max-list (map second (obj-cells b))))",
            "topmost": "(min-list (map first (obj-cells b)))",
            "bottommost": "(- (max-list (map first (obj-cells b))))",
        }.items():
            start = base.index("  (define (obj-distance a b)")
            end = base.index("  (define gray", start)
            rivals[name] = base[:start] + "  (define (obj-distance a b) " + score + ")\n" + base[end:]
        return rivals
    merged = settings["preprocess"] == "blue_to_gray"
    pre = _MERGE if merged else "g"

    def object_rule(predicate, *, objects="objects", color=True, first=False):
        select = f"(and (= (obj-color obj) 5) {predicate})" if color else predicate
        chosen = "(if (null? targets) '() (list (car targets)))" if first else "targets"
        return (
            f"(rule! (let ((g {pre})) "
            f"(define targets (filter (lambda (obj) {select}) ({objects} g 0))) "
            f"(for/fold ((out g)) ((obj (in-list {chosen}))) "
            "(paint-cells out (obj-cells obj) 8))))"
        )

    eligible = "(or (= (obj-color obj) 1) (= (obj-color obj) 5))" if merged else "(= (obj-color obj) 5)"
    stale = (
        f"(rule! (let ((pre {pre})) "
        "(for/fold ((out pre)) ((obj (in-list (objects g 0)))) "
        f"(if (and {eligible} {_H2}) (paint-cells out (obj-cells obj) 8) out))))"
    )
    adjacent = (
        "(for/or ((cell (in-list (obj-cells obj)))) "
        "(member (list (first cell) (+ 1 (second cell))) (obj-cells obj)))"
    )
    multicolor = (
        f"(rule! (let* ((g {pre}) "
        "(mask (cellmap g (r c v) (if (= v 0) 0 1)))) "
        "(for/fold ((out g)) ((obj (in-list (objects mask 0)))) "
        f"(if (and {_H2} (andmap (lambda (cell) "
        "(= (cell-at g (first cell) (second cell)) 5)) (obj-cells obj))) "
        "(paint-cells out (obj-cells obj) 8) out))))"
    )
    other = {"preprocess": "none" if merged else "blue_to_gray"}
    return {
        "other_parameter": prototype.program(other),
        "wrong_order": wrong_order_program(prototype, settings),
        "no_regroup_original_monochrome_components": stale,
        "any_horizontal_adjacency": object_rule(adjacent),
        "any_two_cell": object_rule("(= (obj-size obj) 2)"),
        "ignore_color": object_rule(_H2, color=False),
        "eight_connected": object_rule(_H2, objects="objects-8"),
        "multicolor_four_connected_gray_targets": multicolor,
        "preprocess_only": f"(rule! (let ((out {pre})) out))",
        "first_target_only": object_rule(_H2, first=True),
    }


def _episode(prototype, seed, settings, demos):
    from arcpuzzles.parametric_worker import _grid

    episode = prototype.generate(seed, deepcopy(settings), demos, 4)
    if episode.get("program_solution") != prototype.program(settings):
        raise ValueError("Generated program differs from the setting program")
    for split, count in (("train", demos), ("test", 4)):
        if type(episode.get(split)) is not list or len(episode[split]) != count:
            raise ValueError(f"Incorrect independent {split} count")
        for pair in episode[split]:
            pair["input"], pair["output"] = _grid(pair["input"]), _grid(pair["output"])
    inputs = [_bytes(pair["input"]) for pair in episode["train"] + episode["test"]]
    if len(set(inputs)) != len(inputs):
        raise ValueError("Repeated demonstration/query input")
    return episode


def _coverage(grid):
    height, width = len(grid), len(grid[0])
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    rows, cols = {r for r, _ in cells}, {c for _, c in cells}
    palette = {str(color): sum(row.count(color) for row in grid) for color in sorted({v for row in grid for v in row})}
    return {
        "shape": [height, width], "foreground_cells": len(cells),
        "density": round(len(cells) / (height * width), 6), "palette_counts": palette,
        "occupied_rows": len(rows), "occupied_columns": len(cols),
        "foreground_bbox": [min(rows), min(cols), max(rows), max(cols)] if cells else None,
        "boundary_contacts": {"top": 0 in rows, "bottom": height - 1 in rows,
                              "left": 0 in cols, "right": width - 1 in cols},
    }


def _prequalification(prototype, output):
    from arcpuzzles import Catalog

    before = _sources()
    row = Catalog(ROOT).describe(TASK_ID)
    failures, episodes, witnesses, programs, matched, generated = [], [], {}, {}, [], {}
    with _racket() as (execute, identity, calls):
        for demos in (2, 6):
            for settings in prototype.SETTINGS:
                key = _bytes(settings).decode().strip()
                item = {"seed": 29, "settings": deepcopy(settings), "demos": demos, "queries": 4}
                start_failures = len(failures)
                try:
                    episode = _episode(prototype, 29, settings, demos)
                    generated[(demos, key)] = episode
                    program = prototype.program(settings)
                    pairs = episode["train"] + episode["test"]
                    actual = [execute(program, pair["input"]) for pair in pairs]
                    bad_labels = [i for i, (pair, result) in enumerate(zip(pairs, actual, strict=True)) if pair["output"] != result]
                    item["label_mismatches"] = bad_labels
                    item["coverage"] = {split: [_coverage(pair["input"]) for pair in episode[split]] for split in ("train", "test")}
                    if bad_labels:
                        index = bad_labels[0]
                        failures.append({**item, "kind": "label_mismatch", "index": index,
                                         "input": pairs[index]["input"], "claimed": pairs[index]["output"], "executed": actual[index]})
                    rivals = _rivals(prototype, settings)
                    programs[key] = {"selected": program, "rivals": rivals}
                    item["rivals"] = {}
                    for name, rival in rivals.items():
                        try:
                            # Fitting is complete before any query is evaluated.
                            demo_outputs = [execute(rival, pair["input"]) for pair in episode["train"]]
                            rejected = [i for i, result in enumerate(demo_outputs) if result != actual[i]]
                            query_outputs = [execute(rival, pair["input"]) for pair in episode["test"]]
                            disagreements = [i for i, result in enumerate(query_outputs) if result != actual[demos + i]]
                            status = "rejected_by_demonstrations" if rejected else (
                                "underidentified_on_query" if disagreements else "equivalent_on_sampled_queries")
                            item["rivals"][name] = {"status": status, "demo_rejections": rejected,
                                                   "query_disagreements": disagreements}
                            if status == "underidentified_on_query":
                                failures.append({"kind": status, "settings": settings, "demos": demos, "rival": name})
                            differing = rejected + [demos + i for i in disagreements]
                            if differing:
                                index = min(differing, key=lambda i: len(pairs[i]["input"]) * len(pairs[i]["input"][0]))
                                candidate = {"settings": deepcopy(settings), "rival": name, "seed": 29,
                                             "demos": demos, "split": "train" if index < demos else "test",
                                             "index": index if index < demos else index - demos,
                                             "input": pairs[index]["input"], "program": program, "output": actual[index],
                                             "rival_program": rival, "rival_output": (demo_outputs + query_outputs)[index]}
                                witness_key = key + ":" + name
                                old = witnesses.get(witness_key)
                                if old is None or len(_bytes(candidate["input"])) < len(_bytes(old["input"])):
                                    witnesses[witness_key] = candidate
                        except Exception as error:
                            item["rivals"][name] = {"status": "execution_error", "error": f"{type(error).__name__}: {error}"}
                            failures.append({"kind": "rival_execution_error", "settings": settings, "demos": demos, "rival": name,
                                             "error": f"{type(error).__name__}: {error}"})
                except Exception as error:
                    failures.append({"kind": "episode_error", "settings": settings, "demos": demos,
                                     "error": f"{type(error).__name__}: {error}"})
                item["status"] = "passed" if len(failures) == start_failures else "failed"
                episodes.append(item)
        for demos in (2, 6):
            values = [generated.get((demos, _bytes(s).decode().strip())) for s in prototype.SETTINGS]
            equal = all(value is not None for value in values) and all(
                [p["input"] for split in ("train", "test") for p in values[0][split]] ==
                [p["input"] for split in ("train", "test") for p in value[split]] for value in values[1:])
            matched.append({"seed": 29, "demos": demos, "queries": 4, "same_inputs_across_settings": equal})
            if not equal:
                failures.append({"kind": "unmatched_setting_inputs", "demos": demos})
    if before != _sources():
        failures.append({"kind": "source_changed_during_audit"})
    report = {
        "task_id": TASK_ID, "mode": "bounded_prequalification", "status": "failed" if failures else "passed",
        "reviewer_reported": True, "training_admitted": False, "owner_acceptance": "pending",
        "source_sha256": before, "canonical_rule_hash": row["rule_hash"],
        "canonical_program_sha256": _sha(prototype.CANONICAL_PROGRAM.encode()),
        "racket": identity, **calls, "attempted_episodes": len(episodes),
        "successful_episodes": sum(item["status"] == "passed" for item in episodes),
        "failure_count": len(failures), "failures": failures, "episodes": episodes,
        "matched_inputs": matched, "limits": LIMITS,
    }
    _new_output(output)
    output.mkdir(parents=True)
    _write(output / "report.json", report)
    _write(output / "private-rival-programs.json", programs)
    _write(output / "private-rival-witnesses.json", list(witnesses.values()))
    return report


def _probe_input():
    grid = [[0] * 9 for _ in range(8)]
    grid[0][:2] = [5, 1]
    grid[2][:3] = [5, 5, 1]
    grid[4][0], grid[5][0] = 5, 1
    grid[7][7:] = [5, 5]
    return grid


def _qualified(prototype, qualification, output):
    from arcpuzzles import Catalog
    from arcpuzzles.parametric_promotion import _check_execution, _ready
    from reviewer_support import public_challenge_bytes, public_challenge_id
    from teammate.make_data import prompt_target

    before = _sources()
    raw_qualification = qualification.read_bytes()
    report = json.loads(raw_qualification)
    execution_path = qualification.with_name("execution.json")
    raw_execution = execution_path.read_bytes()
    execution = json.loads(raw_execution)
    if (report.get("schema") != "arcpuzzles-parametric-qualification-v1"
            or report.get("status") != "qualified" or report.get("task_id") != TASK_ID
            or report.get("execution") != {"path": "execution.json", "sha256": _sha(raw_execution)}):
        raise ValueError("Qualification identity or execution hash does not match")
    contract, binding = _ready(Catalog(ROOT), TASK_ID)
    if report.get("source_binding") != binding or report.get("contract") != contract:
        raise ValueError("Qualification does not bind the current source")
    if _check_execution(execution, report["jobs"], binding, contract) != report["programs"]:
        raise ValueError("Native execution program map differs")
    plans, projections = [], []
    for index, episode in enumerate(execution["episodes"]):
        if len(episode["test"]) != 4:
            raise ValueError("This evidence export requires four qualified queries")
        payload, identifier = public_challenge_bytes(episode), public_challenge_id(episode)
        changed = deepcopy(episode)
        changed.update(seed=episode["seed"] + 1, settings={"private": "changed"}, program="private changed")
        changed["program_sha256"] = "private changed"
        for pair in changed["test"]:
            pair["output"] = [[9]]
        if public_challenge_bytes(changed) != payload or public_challenge_id(changed) != identifier:
            raise AssertionError("Private metadata changed public bytes or identifier")
        one = prototype.generate(episode["seed"], episode["settings"], len(episode["train"]), 1)
        first = prompt_target(episode, "grids")[0]
        if first != prompt_target(one, "grids")[0]:
            raise AssertionError("Actual one-query request changes first-turn content")
        if first != prompt_target({"train": episode["train"], "test": episode["test"][:1]}, "grids")[0]:
            raise AssertionError("Four-query container changes first-turn projection")
        future_changed = deepcopy(changed)
        for pair in future_changed["test"][1:]:
            pair["input"] = [[9]]
        if prompt_target(future_changed, "grids")[0] != first:
            raise AssertionError("First turn leaks private fields or future queries")
        turns = []
        for pair in episode["test"]:
            prompt, target = prompt_target({"train": episode["train"], "test": [pair]}, "grids")
            turns.append({"prompt": prompt, "target": target})
        plans.append((identifier, payload))
        projections.append({"episode_id": identifier, "qualification_episode_index": index,
                            "seed": episode["seed"], "settings": episode["settings"],
                            "first_turn_sha256": _sha(first.encode()), "turns": turns})
    if len({identifier for identifier, _ in plans}) != len(plans):
        raise ValueError("Duplicate visible challenge in qualified examples")

    settings = {"preprocess": "blue_to_gray"}
    program = prototype.program(settings)
    setting_key = _bytes(settings).decode().strip()
    if report["programs"].get(setting_key) != _sha(program.encode()):
        raise ValueError("Witness setting program is not natively qualified")
    grid = _probe_input()
    with _racket() as (execute, identity, calls):
        counterfactual = wrong_order_program(prototype, settings)
        actual, alternative = execute(program, grid), execute(counterfactual, grid)
        merged = execute(f"(rule! {_MERGE})", grid)
        components_program = (
            f"(rule! (map (lambda (obj) (sort (obj-cells obj) cell<)) "
            f"(filter (lambda (obj) (= (obj-color obj) 5)) (objects {_MERGE} 0))))"
        )
        components = execute(components_program, grid, grid_result=False)
        if merged != prototype.merge_blue(grid) or actual != prototype.transform(grid, settings):
            raise ValueError("Witness Python claims differ from protected Racket")
        if actual == alternative:
            raise ValueError("Wrong-order ablation did not change the final output")
    shapes = [[[r - min(rr for rr, _ in cells), c - min(cc for _, cc in cells)] for r, c in cells] for cells in components]
    witness = {
        "schema": "arcpuzzles-sequential-dependency-witness-v1", "source_binding": binding,
        **DEPENDENCY, "racket": {"backend": "racket", "protected": True},
        "cases": [{"input": grid, "settings": settings,
                   "intermediate_value": {"merged_grid": merged, "gray_components": components, "normalized_shapes": shapes},
                   "program": program, "output": actual, "counterfactual_program": counterfactual,
                   "counterfactual_output": alternative, "ablation": "wrong_order"}],
        "limits": LIMITS,
    }
    nearest_settings = {"preprocess": "nearest_vertical"}
    nearest_program = prototype.program(nearest_settings)
    nearest_key = _bytes(nearest_settings).decode().strip()
    if report["programs"].get(nearest_key) != _sha(nearest_program.encode()):
        raise ValueError("Nearest witness program is not natively qualified")
    nearest_grid = prototype.generate(0, nearest_settings, 2, 1)["train"][0]["input"]
    anchor_program = (
        "(rule! (obj-cells (find-first (lambda (obj) (and (= (obj-color obj) 5) "
        "(equal? (sort (normalize-cells (obj-cells obj)) cell<) '((0 0) (1 0))))) "
        "(objects g 0))))"
    )
    with _racket() as (execute, _, nearest_calls):
        nearest_actual = execute(nearest_program, nearest_grid)
        nearest_counter = execute(prototype.TOP_LEFT_COUNTERFACTUAL_PROGRAM, nearest_grid)
        anchor_cells = execute(anchor_program, nearest_grid, grid_result=False)
    if (nearest_actual == nearest_counter
            or nearest_actual != prototype.transform(nearest_grid, nearest_settings)
            or sorted(map(tuple, anchor_cells)) != sorted(prototype.nearest_analysis(nearest_grid)[0])):
        raise ValueError("Nearest causal witness failed protected replay")
    nearest_witness = {
        "schema": "arcpuzzles-sequential-dependency-witness-v1", "source_binding": binding,
        "racket": {"backend": "racket", "protected": True},
        "step_a": "Locate the unique original vertical gray domino and retain its absolute cells.",
        "intermediate": "Anchor cells used for minimum Manhattan cell distance to each exact horizontal gray domino.",
        "step_b": "Select the uniquely closest horizontal gray domino and recolor it cyan.",
        "why_b_depends_on_a": "Skipping the input-dependent anchor and choosing the top-left target changes the protected output.",
        "cases": [{"input": nearest_grid, "settings": nearest_settings,
                   "intermediate_value": anchor_cells,
                   "program": nearest_program, "output": nearest_actual,
                   "counterfactual_program": prototype.TOP_LEFT_COUNTERFACTUAL_PROGRAM,
                   "counterfactual_output": nearest_counter, "ablation": "skip_a"}],
        "intermediate_program": anchor_program, "racket_evaluations": nearest_calls["evaluations"],
        "limits": LIMITS,
    }
    if before != _sources():
        raise ValueError("Source changed while building qualification-derived evidence")
    result = {
        "task_id": TASK_ID, "mode": "qualification_derived_examples", "status": "passed",
        "reviewer_reported": True, "owner_acceptance": "pending", "training_admitted": False,
        "qualification_sha256": _sha(raw_qualification), "execution_sha256": _sha(raw_execution),
        "source_sha256": before, "racket": identity, **calls,
        "public_files": len(plans), "private_field_invariance": True,
        "actual_single_four_first_turn_equal": True, "future_queries_excluded_from_first_turn": True,
        "public_ids": sorted(identifier for identifier, _ in plans), "failure_count": 0,
        "intermediate_programs": [f"(rule! {_MERGE})", components_program],
        "projection_scope": "Existing prompt_target serializer; all targets stay private. The consumer reveals each next query after the previous answer; no turn controller is implemented here.",
        "limits": LIMITS,
    }
    _new_output(output)
    output.mkdir(parents=True)
    (output / "public").mkdir()
    for identifier, payload in sorted(plans):
        (output / "public" / f"{identifier}.json").write_bytes(payload)
    _write(output / "private" / "projections.json", sorted(projections, key=lambda item: item["episode_id"]))
    _write(output / "sequential-witness.json", witness)
    _write(output / "nearest-sequential-witness.json", nearest_witness)
    _write(output / "report.json", result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--qualification", type=Path)
    args = parser.parse_args(argv)
    _new_output(args.out)
    # Bind imports to this source tree even when invoked by absolute path.
    sys.path[:0] = [str(ROOT / "src"), str(ROOT / "shared/runtime")]
    prototype = _prototype()
    result = (_qualified(prototype, args.qualification, args.out) if args.qualification
              else _prequalification(prototype, args.out))
    print(json.dumps({"status": result["status"], "failure_count": result["failure_count"],
                      "report": str(args.out / "report.json")}, sort_keys=True))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
