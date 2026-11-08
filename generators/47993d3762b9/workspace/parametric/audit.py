"""Bounded, protected-Racket audit of the adjacent bbox-frame prototype.

This checks a declared finite rival set, not universal rule identification.
All labels, programs, settings and later queries stay in private evidence.
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
    spec = importlib.util.spec_from_file_location("_bbox_audit_prototype", HERE / "prototype.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


AREA = "(* (+ 1 (- (third bb) (first bb))) (+ 1 (- (fourth bb) (second bb))))"
SCORES = {
    "area": AREA,
    "pixel_count": "(third record)",
    "width": "(+ 1 (- (fourth bb) (second bb)))",
    "height": "(+ 1 (- (third bb) (first bb)))",
    "perimeter": "(+ (- (third bb) (first bb)) (- (fourth bb) (second bb)))",
    "color": "(first record)",
    "top": "(first bb)",
    "left": "(second bb)",
}


def rival_program(mode, *, score="area", comparison=None, output=None, endpoint=None):
    """Independent template; each executable hypothesis is retained verbatim."""
    comparison = comparison or ("<" if mode == "smallest_bbox_frame" else ">")
    output = output or ("corners" if mode == "all_corners" else "frame")
    cells_expr = "cells"
    if endpoint:
        # find-color is row-major; sorting makes the endpoint hypothesis explicit.
        ordered = "(sort cells (lambda (a b) (or (< (first a) (first b)) (and (= (first a) (first b)) (< (second a) (second b))))))"
        last = "(last ordered)"
        if endpoint == "farthest":
            distance = "(+ (abs (- (first cell) (first first-cell))) (abs (- (second cell) (second first-cell))))"
            last = f"(for/fold ([best (second ordered)]) ([cell (in-list (rest ordered))]) (let ([distance (lambda (cell) {distance})]) (if (> (distance cell) (distance best)) cell best)))"
        cells_expr = f"(let* ([ordered {ordered}] [first-cell (first ordered)] [last-cell {last}]) (list first-cell last-cell))"
    selected = "records" if mode == "all_corners" else "(list (for/fold ([best (first records)]) ([record (in-list (rest records))]) (if (COMPARE (score record) (score best)) record best)))".replace("COMPARE", comparison)
    if output == "corners":
        positions = "(list (list (first bb) (second bb) color) (list (first bb) (fourth bb) color) (list (third bb) (second bb) color) (list (third bb) (fourth bb) color))"
    else:
        condition = "" if output == "filled" else "#:when (or (= row (first bb)) (= row (third bb)) (= col (second bb)) (= col (fourth bb)))"
        positions = f"(for*/list ([row (in-range (first bb) (+ 1 (third bb)))] [col (in-range (second bb) (+ 1 (fourth bb)))] {condition}) (list row col color))"
    return f"""(rule!
 (let* ([records (for/list ([color (in-list (grid-colors g 0))])
                   (let* ([cells (find-color g color)] [bb (bbox-of-cells {cells_expr})])
                     (list color bb (length cells))))]
        [score (lambda (record) (let ([bb (second record)]) {SCORES[score]}))]
        [chosen {selected}])
   (for/fold ([out (empty-grid (rows g) (cols g) 0)]) ([record (in-list chosen)])
     (let ([color (first record)] [bb (second record)])
       (paint-cells out {positions})))))"""


def rivals(prototype, mode):
    candidates = {"declared:" + m: prototype.program({"mode": m}) for m in prototype.MODES}
    candidates["identity"] = "(rule! (lambda (g) g))"
    candidates["all_frames"] = rival_program("all_corners", output="frame")
    candidates["filled_bbox"] = rival_program(mode, output="filled")
    candidates["selected_corners"] = rival_program(mode, output="corners")
    for endpoint in ("last", "farthest"):
        candidates["endpoint:" + endpoint] = rival_program(mode, endpoint=endpoint)
    if mode != "all_corners":
        for score in ("pixel_count", "width", "height", "perimeter"):
            candidates["rank:" + score] = rival_program(mode, score=score)
        candidates["rank:reverse_area"] = rival_program(mode, comparison="<" if mode == "largest_bbox_frame" else ">")
        for score in ("color", "top", "left"):
            for comparison, name in (("<", "min"), (">", "max")):
                candidates[f"rank:{score}:{name}"] = rival_program(mode, score=score, comparison=comparison)
    # Exact duplicate program elimination preserves named aliases transparently.
    unique = {}
    for name, program in candidates.items():
        entry = unique.setdefault(program, {"names": [], "program": program})
        entry["names"].append(name)
    return list(unique.values())


def spread(prototype, grid):
    facts = prototype.analyze(grid)
    height, width = len(grid), len(grid[0])
    points = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    bounds = [min(r for r, _ in points), min(c for _, c in points),
              max(r for r, _ in points), max(c for _, c in points)]
    return {"height": height, "width": width, "nonbg": len(points),
            "colors": len(facts), "content_bbox": bounds,
            "bbox_spread": [(x["height"], x["width"]) for x in facts],
            "boundary_contacts": {"top": bounds[0] == 0, "left": bounds[1] == 0,
                                  "bottom": bounds[2] == height-1, "right": bounds[3] == width-1}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 17, 43])
    parser.add_argument("--demo-counts", type=int, nargs="+", default=[2, 3, 6])
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error("--out must be a new directory")
    if not 1 <= len(args.seeds) <= 8 or not 1 <= len(args.demo_counts) <= 5:
        parser.error("bounded audit allows 1..8 seeds and 1..5 demo counts")
    prototype = load_prototype()
    args.out.mkdir(parents=True)
    (args.out / "public").mkdir()
    source_paths = [HERE.parents[1] / "generator.py", HERE / "prototype.py", HERE / "adapter.py",
                    HERE / "canonical.rkt", HERE / "promotion.json", Path(__file__)]
    source = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in source_paths}
    cache, programs, inputs, labels = {}, {}, {}, {}
    executions, requests = 0, 0
    checks, failures, examples, witnesses, large, ledger = [], [], [], {}, [], []
    with _local_imports(ROOT / "shared/runtime", HERE):
        apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
        def execute(program, grid):
            nonlocal executions, requests
            requests += 1
            ph, ih = hashlib.sha256(program.encode()).hexdigest(), digest(grid)
            programs[ph], inputs[ih] = program, grid
            key = (ph, ih)
            if key not in cache:
                executions += 1
                try:
                    result = _grid(apply(program, copy.deepcopy(grid)))
                except Exception as exc:
                    failures.append({"kind": "racket_execution", "program_sha256": ph,
                                     "input_sha256": ih, "error": str(exc)})
                    (args.out / "audit.json").write_bytes(raw({"passed": False,
                        "source_sha256": source, "racket": identity, "failures": failures,
                        "racket_evaluations": executions, "failed_program": program, "failed_input": grid}))
                    raise  # Errors never count as discrimination.
                cache[key] = result
                oh = digest(result)
                labels[oh] = result
                ledger.append({"program_sha256": ph, "input_sha256": ih, "output_sha256": oh})
            return cache[key]
        try:
            for seed in args.seeds:
                for demos in args.demo_counts:
                    for mode in prototype.MODES:
                        previous_failures = len(failures)
                        settings = {"mode": mode}
                        episode = prototype.generate(seed, settings, demos, 4)
                        program = episode["program_solution"]
                        for split in ("train", "test"):
                            for index, pair in enumerate(episode[split]):
                                actual = execute(program, pair["input"])
                                if actual != pair["output"]:
                                    failures.append({"kind": "python_label_mismatch", "seed": seed,
                                                     "mode": mode, "split": split, "index": index})
                                pair["output"] = actual
                        public = prototype.public_challenge(episode)
                        one = prototype.generate(seed, settings, demos, 1)
                        changed = copy.deepcopy(episode)
                        changed["settings"] = {"mode": "private mutation"}
                        changed["program_solution"] = "private mutation"
                        changed["test"][0]["output"] = [[9]]
                        for pair in changed["test"][1:]:
                            pair["input"], pair["output"] = [[8]], [[7]]
                        if raw(public) != raw(prototype.public_challenge(one)) or raw(public) != raw(prototype.public_challenge(changed)):
                            failures.append({"kind": "first_turn_projection", "seed": seed, "mode": mode, "demos": demos})
                        public_id = prototype.public_id(episode)
                        visible_bytes = prototype._public_helpers().public_challenge_bytes(public)
                        public_path = args.out / "public" / f"{public_id}.json"
                        public_path.write_bytes(visible_bytes)
                        public_file_hash = hashlib.sha256(public_path.read_bytes()).hexdigest()
                        if public_file_hash != public_id:
                            failures.append({"kind": "public_file_identity", "seed": seed,
                                             "mode": mode, "demos": demos})
                        survivors, rejected = [], []
                        for rival in rivals(prototype, mode):
                            outputs = [execute(rival["program"], pair["input"]) for pair in episode["train"]]
                            differing = [i for i, (result, pair) in enumerate(zip(outputs, episode["train"])) if result != pair["output"]]
                            if differing:
                                rejected.extend(rival["names"])
                                key = mode + ":" + ",".join(rival["names"])
                                if key not in witnesses:
                                    i = differing[0]
                                    pair = episode["train"][i]
                                    witnesses[key] = {"seed": seed, "mode": mode, "names": rival["names"],
                                                     "demo_index": i, "input": pair["input"], "program": program,
                                                     "output": pair["output"], "rival_program": rival["program"],
                                                     "rival_output": outputs[i]}
                            else:
                                query_outputs = [execute(rival["program"], pair["input"]) for pair in episode["test"]]
                                disagreement = [i for i, (result, pair) in enumerate(zip(query_outputs, episode["test"])) if result != pair["output"]]
                                survivors.append({"names": rival["names"], "query_disagreements": disagreement})
                                if disagreement:
                                    failures.append({"kind": "teaching_hole", "seed": seed, "mode": mode,
                                                     "demos": demos, "names": rival["names"], "queries": disagreement})
                        stress = next(pair for pair in episode["test"]
                                      if len(pair["input"]) == 30 and len(pair["input"][0]) == 30)
                        stats = spread(prototype, stress["input"])
                        large.append({"seed": seed, "mode": mode, "demos": demos, **stats})
                        checks.append({"seed": seed, "mode": mode, "demos": demos, "queries": 4,
                                       "public_id": public_id, "survivors": survivors, "rejected": rejected,
                                       "public_file_sha256": public_file_hash,
                                       "public_file_identity_equal": public_file_hash == public_id,
                                       "passed": len(failures) == previous_failures})
                        if seed == 0 and demos == 3:
                            examples.append(episode)
        finally:
            bridge.close()
    source_after = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in source_paths}
    for path in source_paths:
        if source_after[str(path.relative_to(ROOT))] != source[str(path.relative_to(ROOT))]:
            failures.append({"kind": "source_changed_during_audit", "path": str(path.relative_to(ROOT))})
    # Full execution bindings are private; witnesses are bounded to one first
    # distinguishing demonstration per mode/rival, not a chronological diary.
    teaching = {"source_sha256": source, "racket": identity, "programs": programs,
                "inputs": inputs, "labels": labels, "executions": ledger,
                "witnesses": list(witnesses.values())}
    summary = {"schema": "bbox-frame-finite-rival-audit-v1", "source_sha256": source,
               "source_after_sha256": source_after, "source_unchanged": source_after == source,
               "racket": identity, "seeds": args.seeds, "demo_counts": args.demo_counts,
               "queries": 4, "episodes": len(checks), "checks": checks, "failures": failures,
               "passed": not failures, "racket_evaluations": executions,
               "execution_requests": requests, "cache_hits": requests-executions,
               "large_30x30": large, "bounded_episode_success_rate": sum(x["passed"] for x in checks)/len(checks),
               "limits": ["Only the declared finite rival programs and listed seeds were tested; no universal uniqueness claim.",
                          "Ranking rivals resolve score ties by grid-colors iteration order; unique area is required only for the intended rule.",
                          "Source-bound private teaching evidence contains all deduplicated executed program/input/output labels.",
                          "The first-query public projection is tested independently of later labels/settings and query count."]}
    for name, value in (("audit.json", summary), ("teaching.json", teaching), ("private_examples.json", examples)):
        (args.out / name).write_bytes(raw(value))
    print(json.dumps({"out": str(args.out), "passed": not failures, "episodes": len(checks),
                      "racket_evaluations": executions, "failures": failures}, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
