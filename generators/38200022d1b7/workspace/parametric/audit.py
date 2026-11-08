"""Bounded protected-Racket teaching/export audit; all retained evidence is private.

Checks a finite, explicitly executable rival family, never universal uniqueness.
Run from this checkout with the packet's run_with_racket.py launcher.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src"))
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator


def raw(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(raw(value)).hexdigest()


def load_prototype():
    spec = importlib.util.spec_from_file_location("_reflection_audit_prototype", HERE / "prototype.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rival_program(mode, *, metric="manhattan", rank="extreme", selector_center=False,
                  reflection_center=False, subset="color", geometry="point", fixed=None):
    """Independent complete executable rival, with deterministic color-order ties.

    Ranking color scores uses source-cell extrema, true mean distance or true
    color-centroid distance. Separate mean_integer/centroid_integer rivals
    preserve this DSL's truncating integer division. True versions force an
    inexact denominator so mathematical means survive the DSL's arc/ wrapper.
    Component rivals use 4-connected monochrome sources.
    """
    comparison = "<" if mode == "nearest_color" else ">"
    extremum = "min" if mode == "nearest_color" else "max"
    center = "(list (quotient (rows g) 2) (quotient (cols g) 2))"
    select_center = center if selector_center else "pivot"
    reflect_center = center if reflection_center else "pivot"
    distance = {
        "manhattan": "(+ (abs dr) (abs dc))",
        "euclidean_squared": "(+ (* dr dr) (* dc dc))",
        "chebyshev": "(max (abs dr) (abs dc))",
    }[metric]
    scores = {
        "extreme": f"(apply {extremum} (map distance cells))",
        "mean": "(/ (apply + (map distance cells)) (* 1.0 (length cells)))",
        "centroid": "(distance (list (/ (apply + (map first cells)) (* 1.0 (length cells))) (/ (apply + (map second cells)) (* 1.0 (length cells)))))",
        "mean_integer": "(/ (apply + (map distance cells)) (length cells))",
        "centroid_integer": "(distance (list (/ (apply + (map first cells)) (length cells)) (/ (apply + (map second cells)) (length cells))))",
        "color": "color",
        "count": "(length cells)",
        "width": "(- (apply max (map second cells)) (apply min (map second cells)))",
        "height": "(- (apply max (map first cells)) (apply min (map first cells)))",
        "top": "(apply min (map first cells))",
        "left": "(apply min (map second cells))",
    }
    chosen = "#f" if mode == "all_sources" else (
        str(fixed) if fixed is not None else
        f"(for/fold ([best (first colors)]) ([color (in-list (rest colors))]) (if ({comparison} (score color) (score best)) color best))"
    )
    selected = "sources" if mode == "all_sources" else "(filter (lambda (p) (= (at g (first p) (second p)) chosen)) sources)"
    if subset in ("cell", "extreme_cells", "component"):
        seed = f"(for/fold ([best (first selected)]) ([p (in-list (rest selected))]) (if ({comparison} (distance p) (distance best)) p best))"
        if subset == "cell":
            selected = f"(let ([selected {selected}]) (list {seed}))"
        elif subset == "extreme_cells":
            selected = f"(let* ([selected {selected}] [seed {seed}]) (filter (lambda (p) (= (distance p) (distance seed))) selected))"
        else:
            selected = f"""(let* ([selected {selected}] [seed {seed}])
              (let loop ([seen (list seed)])
                (let ([next (filter (lambda (p) (or (member p seen)
                    (ormap (lambda (q) (= (+ (abs (- (first p) (first q))) (abs (- (second p) (second q)))) 1)) seen))) selected)])
                  (if (= (length seen) (length next)) next (loop next)))))"""
    if geometry == "above_only":
        selected = f"(filter (lambda (p) (< (first p) (first pivot))) {selected})"
    rr = "(first p)" if geometry == "horizontal" else "(- (* 2 (first reflection)) (first p))"
    cc = "(second p)" if geometry == "vertical" else "(- (* 2 (second reflection)) (second p))"
    initial = "(for/fold ([out g]) ([p (in-list selected)]) (set-cell out (first p) (second p) 0))" if geometry == "move" else "g"
    return f"""(rule!
      (let* ([pivot (first (find-color g 5))]
             [selector {select_center}] [reflection {reflect_center}]
             [sources (for*/list ([r (in-range (rows g))] [c (in-range (cols g))]
                        #:when (and (not (= (at g r c) 0)) (not (= (at g r c) 5)))) (list r c))]
             [colors (sort (remove-duplicates (map (lambda (p) (at g (first p) (second p))) sources)) <)]
             [distance (lambda (p) (let ([dr (- (first p) (first selector))] [dc (- (second p) (second selector))]) {distance}))]
             [score (lambda (color) (let ([cells (filter (lambda (p) (= (at g (first p) (second p)) color)) sources)]) {scores[rank]}))]
             [chosen {chosen}] [selected {selected}])
        (for/fold ([out {initial}]) ([p (in-list selected)])
          (let ([rr {rr}] [cc {cc}])
            (if (in-bounds? rr cc (rows g) (cols g))
                (set-cell out rr cc (at g (first p) (second p))) out)))))"""


def rivals(prototype, mode):
    candidates = {"declared:" + m: prototype.program({"mode": m}) for m in prototype.MODES}
    candidates["identity"] = "(rule! (lambda (g) g))"
    if mode != "all_sources":
        for metric in ("euclidean_squared", "chebyshev"):
            candidates["metric:" + metric] = rival_program(mode, metric=metric)
        for rank in ("mean", "centroid", "mean_integer", "centroid_integer",
                     "color", "count", "width", "height", "top", "left"):
            candidates["selector:" + rank] = rival_program(mode, rank=rank)
        # Both literal numerical-color orders are plausible, irrespective of mode.
        other = "farthest_color" if mode == "nearest_color" else "nearest_color"
        candidates["selector:reverse_color"] = rival_program(other, rank="color")
        candidates["selector:grid_center"] = rival_program(mode, selector_center=True)
        for subset in ("cell", "extreme_cells", "component"):
            candidates["source_subset:" + subset] = rival_program(mode, subset=subset)
    for geometry in ("horizontal", "vertical", "move", "above_only"):
        candidates["geometry:" + geometry] = rival_program(mode, geometry=geometry)
    candidates["geometry:grid_center"] = rival_program(mode, reflection_center=True)
    candidates["geometry:grid_center_both"] = rival_program(mode, selector_center=True, reflection_center=True)
    unique = {}
    for name, program in candidates.items():
        unique.setdefault(program, {"names": [], "program": program})["names"].append(name)
    return list(unique.values())


def spread(grid):
    points = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v]
    bounds = [min(r for r, _ in points), min(c for _, c in points),
              max(r for r, _ in points), max(c for _, c in points)]
    return {"height": len(grid), "width": len(grid[0]), "nonbg": len(points),
            "content_bbox": bounds, "content_height": bounds[2]-bounds[0]+1,
            "content_width": bounds[3]-bounds[1]+1}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 17])
    parser.add_argument("--demo-counts", type=int, nargs="+", default=[2, 3, 6])
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error("--out must be new")
    allowed = (HERE / "evidence", ROOT.parent / "checks")
    if not any(args.out.resolve().is_relative_to(p.resolve()) for p in allowed):
        parser.error("evidence must stay below this task's evidence/ or WORK/checks/")
    if not 1 <= len(args.seeds) <= 4 or not all(x in range(2, 7) for x in args.demo_counts):
        parser.error("bounded audit requires 1..4 seeds and demo counts 2..6")
    prototype = load_prototype()
    args.out.mkdir(parents=True)
    (args.out / "public").mkdir()
    source_paths = [HERE.parents[1] / "generator.py", HERE / "prototype.py", HERE / "adapter.py",
                    HERE / "canonical.rkt", HERE / "promotion.json", Path(__file__)]
    source = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}
    cache, programs, inputs, labels = {}, {}, {}, {}
    executions = requests = 0
    checks, failures, examples, witnesses, large, ledger = [], [], [], {}, [], []
    paired_inputs = {}
    with _local_imports(ROOT / "shared/runtime", HERE):
        apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
        def execute(program, grid):
            nonlocal executions, requests
            requests += 1
            ph, ih = hashlib.sha256(program.encode()).hexdigest(), digest(grid)
            programs[ph], inputs[ih] = program, grid
            key = ph, ih
            if key not in cache:
                executions += 1
                try:
                    output = _grid(apply(program, copy.deepcopy(grid)))
                except Exception as exc:
                    failures.append({"kind": "racket_execution", "program_sha256": ph,
                                     "input_sha256": ih, "error": str(exc)})
                    (args.out / "audit.json").write_bytes(raw({"passed": False, "source_sha256": source,
                        "racket": identity, "failures": failures, "failed_program": program, "failed_input": grid}))
                    raise  # Execution errors are failures, never rejected hypotheses.
                cache[key] = output
                oh = digest(output)
                labels[oh] = output
                ledger.append({"program_sha256": ph, "input_sha256": ih, "output_sha256": oh})
            return cache[key]
        try:
            for seed in args.seeds:
                for demos in args.demo_counts:
                    for mode in prototype.MODES:
                        previous = len(failures)
                        settings = {"mode": mode}
                        ep = prototype.generate(seed, settings, demos, 4)
                        program = prototype.program(settings)
                        episode_inputs = [pair["input"] for split in ("train", "test") for pair in ep[split]]
                        shared = paired_inputs.setdefault((seed, demos), episode_inputs)
                        if shared != episode_inputs:
                            failures.append({"kind": "setting_dependent_input", "seed": seed, "mode": mode, "demos": demos})
                        if len({digest(g) for g in episode_inputs}) != demos + 4:
                            failures.append({"kind": "duplicate_pair_inputs", "seed": seed, "mode": mode, "demos": demos})
                        for split in ("train", "test"):
                            for index, pair in enumerate(ep[split]):
                                actual = execute(program, pair["input"])
                                if actual != pair["output"]:
                                    failures.append({"kind": "python_label_mismatch", "seed": seed, "mode": mode, "split": split, "index": index})
                                pair["output"] = actual
                        one = prototype.generate(seed, settings, demos, 1)
                        changed = copy.deepcopy(ep)
                        changed.update(settings={"mode": "PRIVATE_MUTATION"}, program_solution="PRIVATE_MUTATION", seed=-999)
                        changed["test"][0]["output"] = [[9]]
                        for pair in changed["test"][1:]:
                            pair["input"], pair["output"] = [[8]], [[7]]
                        visible = prototype.public_turn_bytes(ep, 0)
                        if visible != prototype.public_turn_bytes(one, 0) or visible != prototype.public_turn_bytes(changed, 0):
                            failures.append({"kind": "first_turn_projection", "seed": seed, "mode": mode, "demos": demos})
                        public_path = Path(prototype.write_public(ep, args.out / "public", 0))
                        public_hash = hashlib.sha256(visible).hexdigest()
                        if (public_path.name != public_hash + ".json"
                                or public_path.parent.resolve() != (args.out / "public").resolve()
                                or not public_path.is_file() or public_path.read_bytes() != visible
                                or hashlib.sha256(public_path.read_bytes()).hexdigest() != public_hash):
                            failures.append({"kind": "public_file_identity", "seed": seed, "mode": mode, "demos": demos, "writer_result": str(public_path)})
                        for projection_case, projected_episode in (("one_query", one), ("private_mutation", changed)):
                            projected_path = Path(prototype.write_public(projected_episode, args.out / "public", 0))
                            if (projected_path.resolve() != public_path.resolve()
                                    or projected_path.name != public_hash + ".json"
                                    or projected_path.read_bytes() != visible):
                                failures.append({"kind": "public_writer_projection", "case": projection_case,
                                                 "seed": seed, "mode": mode, "demos": demos})
                        public_obj = json.loads(visible)
                        if set(public_obj) != {"train", "test"} or len(public_obj["test"]) != 1 or set(public_obj["test"][0]) != {"input"}:
                            failures.append({"kind": "public_shape_or_leak", "seed": seed, "mode": mode, "demos": demos})
                        survivors, rejected = [], []
                        for rival in rivals(prototype, mode):
                            outputs = [execute(rival["program"], p["input"]) for p in ep["train"]]
                            differences = [i for i, (out, p) in enumerate(zip(outputs, ep["train"])) if out != p["output"]]
                            if differences:
                                rejected.extend(rival["names"])
                                key = mode + ":" + ",".join(rival["names"])
                                if key not in witnesses:
                                    i = differences[0]
                                    witnesses[key] = {"seed": seed, "mode": mode, "names": rival["names"], "demo_index": i,
                                        "input": ep["train"][i]["input"], "program": program, "output": ep["train"][i]["output"],
                                        "rival_program": rival["program"], "rival_output": outputs[i]}
                            else:
                                predictions = [execute(rival["program"], p["input"]) for p in ep["test"]]
                                differences = [i for i, (out, p) in enumerate(zip(predictions, ep["test"])) if out != p["output"]]
                                survivors.append({"names": rival["names"], "query_disagreements": differences})
                                if differences:
                                    failures.append({"kind": "teaching_hole", "seed": seed, "mode": mode,
                                                     "demos": demos, "names": rival["names"], "queries": differences})
                        stresses = [p for p in ep["test"] if len(p["input"]) == len(p["input"][0]) == 30]
                        if not stresses:
                            failures.append({"kind": "missing_30x30", "seed": seed, "mode": mode, "demos": demos})
                        for stress in stresses:
                            stats = spread(stress["input"])
                            facts = prototype.analyze(stress["input"])
                            added = sum(before == 0 and after != 0
                                        for input_row, output_row in zip(stress["input"], stress["output"])
                                        for before, after in zip(input_row, output_row))
                            stats.update(source_count=len(facts["sources"]), added_cells=added,
                                         analyze_valid=True)
                            if (stats["source_count"] != 420 or stats["content_height"] != 29
                                    or stats["content_width"] != 29 or added < 3):
                                failures.append({"kind": "insubstantial_30x30", "seed": seed,
                                                 "mode": mode, "demos": demos, "stats": stats})
                            large.append({"seed": seed, "mode": mode, "demos": demos, **stats})
                        checks.append({"seed": seed, "mode": mode, "demos": demos, "queries": 4,
                            "survivors": survivors, "rejected": rejected, "public_sha256": public_hash,
                            "public_files": [str(public_path.relative_to(args.out))], "passed": len(failures) == previous})
                        if seed == 0 and demos == 3:
                            examples.append(ep)
        finally:
            bridge.close()
    after = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}
    if after != source:
        failures.append({"kind": "source_changed_during_audit"})
    teaching = {"source_sha256": source, "racket": identity, "programs": programs, "inputs": inputs,
                "labels": labels, "executions": ledger, "witnesses": list(witnesses.values())}
    summary = {"schema": "pivot-color-finite-rival-audit-v1", "source_sha256": source, "source_after_sha256": after,
               "source_unchanged": source == after, "racket": identity, "seeds": args.seeds,
               "demo_counts": args.demo_counts, "queries": 4, "episodes": len(checks), "checks": checks,
               "failures": failures, "passed": not failures, "racket_evaluations": executions,
               "execution_requests": requests, "cache_hits": requests-executions, "large_30x30": large,
               "limits": ["Only the named finite rival programs, seeds and counts were tested; no universal uniqueness claim.",
                   "Rival score ties choose the first numerical color; extremal-cell ties choose row-major first.",
                   "Mean/centroid rivals include both mathematical means using inexact denominators and the DSL's truncating integer versions.",
                   "Component rival is 4-connected and monochrome; full private program/input/output bindings retained.",
                   "Public first turn is checked against 1-vs-4 queries and mutation of private metadata, labels and later inputs."]}
    for name, value in (("audit.json", summary), ("teaching.json", teaching), ("private_examples.json", examples)):
        (args.out / name).write_bytes(raw(value))
    print(json.dumps({"out": str(args.out), "passed": not failures, "episodes": len(checks),
                      "racket_evaluations": executions, "failures": failures}, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
