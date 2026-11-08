"""Finite protected-Racket audit of original-object bbox and diagonal-gap completion.

Run through review.py run, with --out pointing to a fresh private directory.
The report retains programs, labels, source hashes and finite rival results.
It grants neither owner acceptance nor training admission.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


HOME = Path(__file__).resolve().parent
TASK = HOME.parents[1]
ROOT = HOME.parents[3]
RUNTIME = ROOT / "shared/runtime"
sys.path[:0] = [str(ROOT / "src"), str(RUNTIME)]
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator


CANONICAL = "(rule! (lambda (g) (fill-object-bboxes-8 g 7)))"
SETTINGS = ({"completion": "bbox"}, {"completion": "diagonal_gaps"})
JOBS = ((0, 2), (17, 3), (22, 6))
RIVALS = ("bbox4", "global_bbox", "per_color_bbox", "skip_boundary", "boundary_only",
          "bridge_rows", "bridge_columns", "bridge_union", "nearest_pair", "raw_equal_v",
          "same_color_pairs", "slash_only", "resegment_after_bbox", "bridges_only", "identity",
          "color_blind_components")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def packed(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _setting(settings):
    if (type(settings) is not dict or set(settings) != {"completion"}
            or type(settings["completion"]) is not str
            or settings["completion"] not in ("bbox", "diagonal_gaps")):
        raise ValueError("Expected one exact completion setting")
    return settings["completion"]


def objects(grid, connectivity=8, color_blind=False):
    """Independent monochrome flood fill on the original pixels."""
    height, width = len(grid), len(grid[0])
    steps = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if connectivity == 8:
        steps += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    seen, result = set(), []
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if not color or (r, c) in seen:
                continue
            pending, cells = [(r, c)], []
            seen.add((r, c))
            while pending:
                rr, cc = pending.pop()
                cells.append((rr, cc))
                for dr, dc in steps:
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < height and 0 <= nc < width and (nr, nc) not in seen
                            and (grid[nr][nc] != 0 if color_blind else grid[nr][nc] == color)):
                        seen.add((nr, nc))
                        pending.append((nr, nc))
            result.append(_record(cells, color))
    return result


def _record(cells, color):
    cells = sorted(cells)
    rs, cs = [p[0] for p in cells], [p[1] for p in cells]
    us, vs = [r + c for r, c in cells], [r - c for r, c in cells]
    return {"cells": cells, "color": color, "r": (min(rs), max(rs)),
            "c": (min(cs), max(cs)), "u": (min(us), max(us)),
            "v": (min(vs), max(vs)), "v_values": set(vs)}


def _fill_boxes(grid, objs):
    result = deepcopy(grid)
    for obj in objs:
        for r in range(obj["r"][0], obj["r"][1] + 1):
            for c in range(obj["c"][0], obj["c"][1] + 1):
                if result[r][c] == 0:
                    result[r][c] = 7
    return result


def _selected_objects(grid, name):
    objs = objects(grid, 4 if name == "bbox4" else 8, name == "color_blind_components")
    all_cells = [cell for obj in objs for cell in obj["cells"]]
    if name == "global_bbox":
        return [_record(all_cells, 0)] if all_cells else []
    if name == "per_color_bbox":
        colors = sorted({obj["color"] for obj in objs})
        return [_record([cell for obj in objs if obj["color"] == color for cell in obj["cells"]], color)
                for color in colors]
    if name in ("skip_boundary", "boundary_only"):
        def boundary(obj):
            return (obj["r"][0] == 0 or obj["c"][0] == 0 or
                    obj["r"][1] == len(grid) - 1 or obj["c"][1] == len(grid[0]) - 1)
        objs = [obj for obj in objs if boundary(obj) == (name == "boundary_only")]
    return objs


def rival_reference(grid, settings, name):
    policy = _setting(settings)
    if name not in (*RIVALS, "reference"):
        raise ValueError("Unknown rival: " + name)
    if name == "identity":
        return deepcopy(grid)
    objs = _selected_objects(grid, name)
    result = deepcopy(grid) if name == "bridges_only" else _fill_boxes(grid, objs)
    if policy == "bbox":
        return result
    if name == "resegment_after_bbox":
        objs = objects(result)
    axis, other = (("r", "c") if name == "bridge_rows" else
                   ("c", "r") if name == "bridge_columns" else ("u", "v"))
    for left in objs:
        for right in objs:
            if left[axis][1] >= right[axis][0]:
                continue
            lower = (min(left[other][0], right[other][0]) if name == "bridge_union"
                     else max(left[other][0], right[other][0]))
            upper = (max(left[other][1], right[other][1]) if name == "bridge_union"
                     else min(left[other][1], right[other][1]))
            if lower > upper:
                continue
            if name == "same_color_pairs" and left["color"] != right["color"]:
                continue
            if name == "slash_only" and (left["u"][0] != left["u"][1] or right["u"][0] != right["u"][1]):
                continue
            if name == "nearest_pair":
                eligible = [obj[axis][0] for obj in objs if left[axis][1] < obj[axis][0]
                            and max(left[other][0], obj[other][0]) <= min(left[other][1], obj[other][1])]
                if right[axis][0] != min(eligible):
                    continue
            for r in range(len(grid)):
                for c in range(len(grid[0])):
                    x, y = ((r, c) if axis == "r" else (c, r) if axis == "c" else (r + c, r - c))
                    if (left[axis][1] < x < right[axis][0] and lower <= y <= upper
                            and (name != "raw_equal_v" or y in left["v_values"] & right["v_values"])
                            and result[r][c] == 0):
                        result[r][c] = 7
    return result


def reference(grid, settings):
    return rival_reference(grid, settings, "reference")


def rival_program(settings, name):
    """Independent complete Racket programs for each explicitly named rule."""
    policy = _setting(settings)
    if name not in (*RIVALS, "reference"):
        raise ValueError("Unknown rival: " + name)
    if name == "identity":
        return "(rule! (lambda (g) g))"
    if name == "reference" and policy == "bbox":
        return CANONICAL
    raw = "objects" if name == "bbox4" else "objects-multicolor" if name == "color_blind_components" else "objects-8"
    selection = "original"
    if name == "global_bbox":
        selection = "(if (empty? all-cells) (list) (list (pack all-cells 0)))"
    elif name == "per_color_bbox":
        selection = "(map (lambda (color) (pack (filter (lambda (p) (= (at g (first p) (second p)) color)) all-cells) color)) colors)"
    elif name == "skip_boundary":
        selection = "(filter (lambda (o) (not (boundary? o))) original)"
    elif name == "boundary_only":
        selection = "(filter boundary? original)"
    xlo, xhi, ylo, yhi, x, y = (2, 3, 4, 5, "r", "c") if name == "bridge_rows" else (
        (4, 5, 2, 3, "c", "r") if name == "bridge_columns" else (6, 7, 8, 9, "(+ r c)", "(- r c)"))
    lo_op, hi_op = ("min", "max") if name == "bridge_union" else ("max", "min")
    pair_extra = {"same_color_pairs": "(= (list-ref a 0) (list-ref b 0))",
                  "slash_only": "(and (= (list-ref a 6) (list-ref a 7)) (= (list-ref b 6) (list-ref b 7)))",
                  "nearest_pair": "(= (xlo b) (apply min (map xlo (filter (lambda (o) (and (< (xhi a) (xlo o)) (<= (max (ylo a) (ylo o)) (min (yhi a) (yhi o))))) bridge-objs))))"}.get(name, "#t")
    point_extra = f"(and (member {y} (list-ref a 10)) (member {y} (list-ref b 10)))" if name == "raw_equal_v" else "#t"
    base = "g" if name == "bridges_only" else "(fill-boxes selected)"
    bridge_objs = "(map from-object (objects-8 base 0))" if name == "resegment_after_bbox" else "selected"
    final = "base" if policy == "bbox" else f"""
      (for*/fold ((out base)) ((a (in-list bridge-objs)) (b (in-list bridge-objs)))
        (if (and (< (xhi a) (xlo b))
                 (<= ({lo_op} (ylo a) (ylo b)) ({hi_op} (yhi a) (yhi b))) {pair_extra})
            (grid-from-fn (rows g) (cols g) (lambda (r c)
              (if (and (= (at out r c) 0) (< (xhi a) {x}) (< {x} (xlo b))
                       (<= ({lo_op} (ylo a) (ylo b)) {y}) (<= {y} ({hi_op} (yhi a) (yhi b)))
                       {point_extra}) 7 (at out r c))))
            out))"""
    return f"""(rule! (lambda (g)
  (define (pack cells color)
    (let ((rs (map first cells)) (cs (map second cells))
          (us (map (lambda (p) (+ (first p) (second p))) cells))
          (vs (map (lambda (p) (- (first p) (second p))) cells)))
      (list color cells (apply min rs) (apply max rs) (apply min cs) (apply max cs)
            (apply min us) (apply max us) (apply min vs) (apply max vs) (remove-duplicates vs))))
  (define (from-object o) (pack (obj-cells o) (obj-color o)))
  (define (boundary? o) (or (= (list-ref o 2) 0) (= (list-ref o 4) 0)
                           (= (list-ref o 3) (- (rows g) 1)) (= (list-ref o 5) (- (cols g) 1))))
  (define (fill-boxes objs)
    (for/fold ((out g)) ((o (in-list objs)))
      (grid-from-fn (rows g) (cols g) (lambda (r c)
        (if (and (= (at out r c) 0) (<= (list-ref o 2) r) (<= r (list-ref o 3))
                 (<= (list-ref o 4) c) (<= c (list-ref o 5))) 7 (at out r c))))))
  (define (xlo o) (list-ref o {xlo}))
  (define (xhi o) (list-ref o {xhi}))
  (define (ylo o) (list-ref o {ylo}))
  (define (yhi o) (list-ref o {yhi}))
  (let* ((raw ({raw} g 0)) (original (map from-object raw))
         (all-cells (apply append (map obj-cells raw)))
         (colors (sort (remove-duplicates (map obj-color raw)) <))
         (selected {selection}) (base {base}) (bridge-objs {bridge_objs}))
    {final})))"""


class CachedEvaluator:
    def __init__(self, apply):
        self.apply, self.cache = apply, {}
        self.requests = self.evaluations = self.cache_hits = 0
        self.last_request = None

    def __call__(self, program, grid):
        self.requests += 1
        key = program, packed(grid)
        if key in self.cache:
            self.cache_hits += 1
            return deepcopy(self.cache[key])
        self.last_request = {"program_sha256": sha(program.encode()), "input_sha256": sha(key[1])}
        self.evaluations += 1
        result = _grid(self.apply(program, deepcopy(grid)))
        self.cache[key] = deepcopy(result)
        return result


def assess(name, program, train, test, execute):
    outputs = [execute(program, pair["input"]) for pair in train]
    rejected = [i for i, (out, pair) in enumerate(zip(outputs, train)) if out != pair["output"]]
    survives, prefix = not rejected, not any(i < 2 for i in rejected)
    checked_for = (["all_demonstrations"] if survives else []) + (["first_two_prefix"] if prefix else [])
    queries = [execute(program, pair["input"]) for pair in test] if checked_for else None
    differences = [i for i, (out, pair) in enumerate(zip(queries, test)) if out != pair["output"]] if queries is not None else None
    return {"name": name, "program_sha256": sha(program.encode()), "demo_outputs": outputs,
            "rejected_by_demo_indices": rejected, "survives_demonstrations": survives,
            "survives_first_two": prefix, "query_checked_for": checked_for,
            "query_outputs": queries, "query_disagreement_indices": differences}


def scene_facts(grid):
    grid = _grid(grid)
    points = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v]
    if not points or any(v == 7 for row in grid for v in row):
        raise ValueError("Admitted scene needs foreground and excludes input fill color7")
    h, w = len(grid), len(grid[0])
    bbox, gaps = reference(grid, SETTINGS[0]), reference(grid, SETTINGS[1])
    return {"shape": [h, w], "foreground_cells": len(points),
            "colors": sorted({grid[r][c] for r, c in points}),
            "components8": len(objects(grid)), "components4": len(objects(grid, 4)),
            "occupied_rows": len({r for r, c in points}), "occupied_columns": len({c for r, c in points}),
            "foreground_bbox": [min(r for r, c in points), min(c for r, c in points), max(r for r, c in points), max(c for r, c in points)],
            "quadrant_foreground": [sum((r >= h // 2) == bottom and (c >= w // 2) == right for r, c in points)
                                    for bottom, right in ((False, False), (False, True), (True, False), (True, True))],
            "bbox_fill_cells": sum(bbox[r][c] == 7 for r in range(h) for c in range(w)),
            "bridge_extra_cells": sum(gaps[r][c] == 7 and bbox[r][c] == 0 for r in range(h) for c in range(w))}


def _load(path):
    name = "_bbox_audit_" + sha(str(path).encode())[:16]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def source_binding():
    paths = list(HOME.glob("*.py")) + list((TASK / "tests").glob("*.py"))
    paths += [TASK / "generator.py", HOME / "promotion.json", ROOT / "src/arcpuzzles/parametric_worker.py",
              RUNTIME / "puzzle_generators/rule_wrap.py", RUNTIME / "arc_repl/racket_bridge.py"]
    paths += list(HOME.glob("*.rkt"))
    return {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in sorted(set(paths))}


def run(out):
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    private = out / "private"
    private.mkdir()
    report = {"schema": "68a312813b77-native-finite-audit-v1", "status": "running", "visibility": "controller_private",
              "source_files_sha256": source_binding(), "settings": deepcopy(SETTINGS),
              "jobs": [{"seed": s, "demos": d, "queries": 4} for s, d in JOBS],
              "extra_rivals": list(RIVALS), "programs": {}, "episodes": [], "findings": [], "first_two_prefix_findings": [],
              "limits": "Six episodes, two declared programs and16 extra executable hypotheses; finite same-source evidence only. No universal identifiability, owner acceptance or training admission."}
    bridge, engine = None, None
    phase = "setup"
    try:
        with _local_imports(RUNTIME, HOME):
            adapter = _load(HOME / "adapter.py")
            apply, identity, bridge = _real_evaluator(RUNTIME)
            if identity.get("backend") != "racket" or identity.get("protected") is not True:
                raise ValueError("Audit requires protected Racket")
            engine = CachedEvaluator(apply)
            report["racket"] = identity
            programs = {s["completion"]: adapter.program(deepcopy(s)) for s in SETTINGS}
            if programs["bbox"] != CANONICAL:
                raise AssertionError("Default program is not the exact canonical text")
            def retain(program):
                identifier = sha(program.encode())
                report["programs"][identifier] = program
                return identifier
            for seed, demos in JOBS:
                shared = None
                for settings in SETTINGS:
                    mode = settings["completion"]
                    phase = f"generate:{seed}:{demos}:{mode}"
                    ep = adapter.generate(seed, deepcopy(settings), demos, 4)
                    if ep["program_solution"] != programs[mode]:
                        raise AssertionError("Generated program differs from selected rule")
                    pairs = {}
                    for split, count in (("train", demos), ("test", 4)):
                        if type(ep[split]) is not list or len(ep[split]) != count:
                            raise ValueError("Incorrect demonstration/query count")
                        pairs[split] = [{"input": _grid(p["input"]), "output": _grid(p["output"])} for p in ep[split]]
                    inputs = [p["input"] for p in pairs["train"] + pairs["test"]]
                    if len({packed(g) for g in inputs}) != len(inputs):
                        raise ValueError("Demonstration and query inputs must all differ")
                    if shared is not None and shared != inputs:
                        raise ValueError("Inputs differ across settings")
                    shared = inputs
                    facts = [scene_facts(g) for g in inputs]
                    phase = f"reference:{seed}:{demos}:{mode}"
                    for pair in pairs["train"] + pairs["test"]:
                        actual = engine(programs[mode], pair["input"])
                        if actual != pair["output"] or actual != reference(pair["input"], settings):
                            raise AssertionError("Native reference disagrees with labels or independent semantics")
                    record = {"seed": seed, "settings": deepcopy(settings), "demos": demos, "queries": 4,
                              "program_sha256": retain(programs[mode]), **pairs,
                              "scene_facts": {"train": facts[:demos], "test": facts[demos:]}, "hypotheses": []}
                    report["episodes"].append(record)
                    hypotheses = [("declared:" + s["completion"], programs[s["completion"]], s) for s in SETTINGS]
                    hypotheses += [(name, rival_program(settings, name), None) for name in RIVALS]
                    survivors = []
                    for name, program, declared in hypotheses:
                        phase = f"hypothesis:{seed}:{demos}:{mode}:{name}"
                        retain(program)
                        def execute(source, grid, declared=declared, name=name):
                            actual = engine(source, grid)
                            expected = reference(grid, declared) if declared is not None else rival_reference(grid, settings, name)
                            if actual != expected:
                                raise AssertionError("Executable rival differs from its independent meaning: " + name)
                            return actual
                        row = assess(name, program, pairs["train"], pairs["test"], execute)
                        record["hypotheses"].append(row)
                        if declared is not None and row["survives_demonstrations"]:
                            survivors.append(declared["completion"])
                        finding = {"episode_index": len(report["episodes"]) - 1, "seed": seed,
                                   "settings": deepcopy(settings), "rival": name, "query_indices": row["query_disagreement_indices"]}
                        if row["survives_demonstrations"] and row["query_disagreement_indices"]:
                            report["findings"].append(dict(finding, kind="demo_survivor_query_disagreement"))
                        if row["survives_first_two"] and row["query_disagreement_indices"]:
                            report["first_two_prefix_findings"].append(dict(finding, kind="prefix_survivor_query_disagreement"))
                    record["declared_survivors"] = survivors
                    record["extra_survivors"] = [r["name"] for r in record["hypotheses"] if not r["name"].startswith("declared:") and r["survives_demonstrations"]]
                    if survivors != [mode]:
                        report["findings"].append({"kind": "declared_policy_not_identified", "episode_index": len(report["episodes"]) - 1})
                    stress = facts[-1]
                    stress_ok = (stress["shape"] == [30, 30] and stress["foreground_cells"] >= 32
                                 and stress["occupied_rows"] >= 20 and stress["occupied_columns"] >= 20
                                 and min(stress["quadrant_foreground"]) >= 3)
                    record["stress_check"] = {"passed": stress_ok, "scope": "Exact30x30,>=32foreground,>=20occupiedrows/columns,>=3foregroundperquadrant; detailed fill counts retained, no high-density assumption."}
                    if not stress_ok:
                        report["findings"].append({"kind": "insufficient_30x30_content", "episode_index": len(report["episodes"]) - 1, "facts": stress})
                    print(json.dumps({"seed": seed, "demos": demos, "completion": mode, "evaluations": engine.evaluations,
                                      "extra_survivors": record["extra_survivors"], "findings": len(report["findings"])}), flush=True)
            if source_binding() != report["source_files_sha256"]:
                raise AssertionError("Sources changed during audit")
            report["reference_label_count"] = sum(d + 4 for s, d in JOBS) * 2
            report["status"] = "failed" if report["findings"] else "passed"
            report["matched_inputs_across_settings"] = True
    except Exception as error:
        report["status"] = "failed"
        report["execution_failure"] = {"phase": phase, "type": type(error).__name__, "message": str(error),
                                       "last_native_request": engine.last_request if engine else None}
    finally:
        if bridge is not None:
            bridge.close()
        if engine is not None:
            report["execution"] = {"requests": engine.requests, "racket_evaluations": engine.evaluations,
                "cache_hits": engine.cache_hits, "successful_cached_results": len(engine.cache),
                "cache_key": "exact complete program and exact validated grid"}
        target = private / "audit.json"
        target.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"status": report["status"], "report": str(target), "findings": len(report["findings"]),
                      "execution_failure": report.get("execution_failure")}), flush=True)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    result = run(parser.parse_args().out)
    raise SystemExit(0 if result["status"] == "passed" else 1)
