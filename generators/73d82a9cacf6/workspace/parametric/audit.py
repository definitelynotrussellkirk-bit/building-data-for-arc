"""Bounded private Racket audit; publish only after all required checks pass.

Run from the packet outer directory with::

    WORK/.venv/bin/python review.py run python3 \
      generators/73d82a9cacf6/workspace/parametric/audit.py --out ../checks/73d82a9cacf6/audit

This is finite teaching evidence, not native qualification or acceptance.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib
import importlib.util
from itertools import combinations
import json
from pathlib import Path
import shutil
import sys
import tempfile
import time


sys.dont_write_bytecode = True
TASK_ID = "73d82a9cacf6"
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode()


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def _grid(value):
    if (type(value) is not list or not 1 <= len(value) <= 30
            or type(value[0]) is not list or not 1 <= len(value[0]) <= 30
            or any(type(row) is not list or len(row) != len(value[0])
                   or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
                   for row in value)):
        raise ValueError("Expected a rectangular 1..30 grid with exact integer colors 0..9")
    return deepcopy(value)


def _once(text, old, new):
    if text.count(old) != 1:
        raise ValueError(f"Rival mutation requires one exact source occurrence: {old!r}")
    return text.replace(old, new, 1)


def rival_programs(program, settings):
    """Fourteen total candidate programs, each changing one declared behavior."""
    larger = settings == {"area_order": "larger_first"}
    if not larger and settings != {"area_order": "smaller_first"}:
        raise ValueError("Unsupported audit setting")
    area = "(- (obj-size obj))" if larger else "(obj-size obj)"
    old = f"(list (hole-count obj) {area} (obj-color obj) (crop-object obj))"
    bbox = "(* (rows (crop-object obj)) (cols (crop-object obj)))"
    scan = "(+ (* (obj-r1 obj) (cols g)) (obj-c1 obj))"

    def signed(expression):
        return f"(- {expression})" if larger else expression

    def key(first="(hole-count obj)", second=area, third="(obj-color obj)"):
        return _once(program, old, f"(list {first} {second} {third} (crop-object obj))")

    rivals = {
        "wrong_area_direction": key(second="(obj-size obj)" if larger else "(- (obj-size obj))"),
        "ignore_holes_global_area": key(first="0"),
        "blank_count_instead_of_holes": key(first=f"(- {bbox} (obj-size obj))"),
        "bounding_box_area_tiebreak": key(second=signed(bbox)),
        "density_tiebreak": key(second=signed(f"(/ (* 1000000 (obj-size obj)) {bbox})")),
        "descending_hole_count": key(first="(- (hole-count obj))"),
        "hole_then_scan_order": key(second=scan),
        "hole_then_color_tiebreak": key(second="0"),
        "scan_order_only": key(first="0", second=scan),
        "color_order_only": key(first="0", second="0"),
        "eight_connected_background": _once(program, "(lambda (r c v) (free? r c)) 4)",
                                               "(lambda (r c v) (free? r c)) 8)"),
        "no_separator_columns": _once(_once(program, "(max 0 (- (length crops) 1))", "0"),
                                       "(+ left (cols (first remaining)) 1)",
                                       "(+ left (cols (first remaining)))"),
        "bottom_alignment": _once(program, "(set-cell acc r (+ left c) (at pat r c))",
                                   "(set-cell acc (+ r (- (rows out) (rows pat))) (+ left c) (at pat r c))"),
    }
    perimeter = """    (define (audit-edge-count obj)
      (apply +
        (map (lambda (p)
               (length
                 (filter (lambda (d)
                           (not (member? (list (+ (first p) (first d))
                                               (+ (second p) (second d)))
                                         (obj-cells obj))))
                         '((-1 0) (1 0) (0 -1) (0 1)))))
             (obj-cells obj))))
"""
    rivals["perimeter_tiebreak"] = _once(key(second=signed("(audit-edge-count obj)")),
                                         "    (define (crop-object obj)",
                                         perimeter + "    (define (crop-object obj)")
    if len(rivals) != 14 or len(set(rivals.values())) != 14 or program in rivals.values():
        raise ValueError("Rival construction produced duplicate or unchanged programs")
    return rivals


def _load_adapter():
    path = HERE / "adapter.py"
    if (not path.is_file() or path.resolve() != path
            or any(parent.is_symlink() for parent in path.parents if parent != ROOT.parent)):
        raise ValueError("Expected a regular same-checkout adapter.py")
    sys.path[:0] = [str(ROOT / "shared/runtime"), str(ROOT / "src"), str(HERE)]
    name = "_hole_count_audit_adapter_" + _sha(str(path).encode())[:16]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    if (getattr(module, "TASK_ID", None) != TASK_ID
            or tuple(getattr(module, "AREA_ORDERS", ())) != ("larger_first", "smaller_first")
            or any(not callable(getattr(module, name, None))
                   for name in ("program", "generate", "predict", "public_turn"))):
        raise ValueError("Adapter identity or required callable contract differs")
    return module


def _source_binding(adapter):
    catalog_module = importlib.import_module("arcpuzzles.catalog")
    if not Path(catalog_module.__file__).resolve().is_relative_to(ROOT / "src"):
        raise ValueError("Catalog must come from this checkout")
    catalog = catalog_module.Catalog(ROOT)
    selected = catalog.describe(TASK_ID)
    authority = {row.get("program_solution")
                 for row in catalog._variants().get(selected.get("rule_task_id", TASK_ID), [])}
    default = adapter.program({"area_order": "larger_first"})
    if authority != {default}:
        raise ValueError("Default Racket source does not exactly equal selected canonical authority")
    paths = [HERE / "adapter.py", HERE / "audit.py", HERE / "canonical.rkt",
             ROOT / "generators" / TASK_ID / "generator.py"]
    return {"files": {str(path.relative_to(ROOT)): _sha(path.read_bytes()) for path in paths},
            "canonical_program_sha256": _sha(default.encode()),
            "setting_programs": {order: _sha(adapter.program({"area_order": order}).encode())
                                 for order in adapter.AREA_ORDERS}}


class Evaluator:
    def __init__(self):
        bridge_module = importlib.import_module("arc_repl.racket_bridge")
        wrap_module = importlib.import_module("puzzle_generators.rule_wrap")
        for module in (bridge_module, wrap_module):
            if not Path(module.__file__).resolve().is_relative_to(ROOT / "shared/runtime"):
                raise ValueError("Racket modules must come from this checkout")
        self.bridge = bridge_module.RacketBridge(timeout=15.0)
        self.identity = dict(self.bridge.runtime_identity)
        if self.identity.get("backend") != "racket" or self.identity.get("protected") is not True:
            self.bridge.close()
            raise ValueError("Audit requires the actual protected Racket backend")
        self.wrap = wrap_module.wrap_rule
        self.cache = {}
        self.calls = 0
        self.hits = 0

    def execute(self, program, grid):
        grid = _grid(grid)
        key = (program, _bytes(grid))
        if key in self.cache:
            self.hits += 1
            return deepcopy(self.cache[key])
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        output = _grid(self.bridge.eval_text(f"({self.wrap(program)} {literal})"))
        self.calls += 1
        self.cache[key] = output
        return deepcopy(output)

    def close(self):
        self.bridge.close()


def _facts(grid):
    """Independent component/complement analysis; never used as gold labels."""
    grid = _grid(grid)
    height, width = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(height) for c in range(width) if grid[r][c]}
    objects = []
    while remaining:
        seed = min(remaining)
        color = grid[seed[0]][seed[1]]
        cells, stack = {seed}, [seed]
        remaining.remove(seed)
        while stack:
            r, c = stack.pop()
            for dr, dc in CARDINAL:
                point = (r + dr, c + dc)
                if point in remaining and grid[point[0]][point[1]] == color:
                    remaining.remove(point)
                    cells.add(point)
                    stack.append(point)
        top, bottom = min(r for r, _ in cells), max(r for r, _ in cells)
        left, right = min(c for _, c in cells), max(c for _, c in cells)
        free = {(r, c) for r in range(top - 1, bottom + 2)
                for c in range(left - 1, right + 2) if (r, c) not in cells}
        holes = 0
        while free:
            stack = [free.pop()]
            exterior = False
            while stack:
                r, c = stack.pop()
                exterior |= r in (top - 1, bottom + 1) or c in (left - 1, right + 1)
                for dr, dc in CARDINAL:
                    point = (r + dr, c + dc)
                    if point in free:
                        free.remove(point)
                        stack.append(point)
            holes += not exterior
        objects.append({"color": color, "area": len(cells), "holes": holes,
                        "bbox": [top, left, bottom, right]})
    if not objects:
        raise ValueError("Input has no objects")
    for first, second in combinations(objects, 2):
        a, b = first["bbox"], second["bbox"]
        if max(a[0], b[0]) <= min(a[2], b[2]) and max(a[1], b[1]) <= min(a[3], b[3]):
            raise ValueError("Generated object bounding boxes overlap")
    out_h = max(item["bbox"][2] - item["bbox"][0] + 1 for item in objects)
    out_w = sum(item["bbox"][3] - item["bbox"][1] + 1 for item in objects) + len(objects) - 1
    if max(out_h, out_w) > 30:
        raise ValueError("Packed dimensions exceed 30")
    return {"input_size": [height, width], "packed_size": [out_h, out_w],
            "painted_cells": sum(item["area"] for item in objects), "objects": objects}


def _normalize_episode(adapter, seed, settings, demos, queries):
    generated = adapter.generate(seed, deepcopy(settings), demos, queries)
    program = adapter.program(deepcopy(settings))
    if not isinstance(generated, dict) or generated.get("program_solution") != program:
        raise ValueError("Generated episode does not carry the selected exact program")
    splits = {}
    for split, count in (("train", demos), ("test", queries)):
        pairs = generated.get(split)
        if type(pairs) is not list or len(pairs) != count:
            raise ValueError(f"{split} count differs from request")
        splits[split] = [{"input": _grid(pair["input"]), "output": _grid(pair["output"])}
                         for pair in pairs]
    inputs = [_bytes(pair["input"]) for split in splits.values() for pair in split]
    if len(inputs) != len(set(inputs)):
        raise ValueError("Demonstration/query inputs must all be distinct")
    return generated, {"seed": seed, "settings": deepcopy(settings), "program": program, **splits}


def _projection(episode, index=None):
    tests = episode["test"] if index is None else [episode["test"][index]]
    return {"train": deepcopy(episode["train"]),
            "test": [{"input": deepcopy(pair["input"])} for pair in tests]}


def _public_files(adapter, generated, episode):
    files = {}
    whole = _bytes(_projection(episode))
    challenge = f"public/challenges/{_sha(whole)}.json"
    files[challenge] = whole
    turns = []
    altered = deepcopy(generated)
    altered["seed"] = -42
    altered["settings"] = {"private": "sentinel"}
    altered["program_solution"] = "PRIVATE_SENTINEL"
    for pair in altered["test"]:
        pair["output"] = [[9]]
    for index in range(len(episode["test"])):
        expected = _projection(episode, index)
        observed = adapter.public_turn(deepcopy(generated), index)
        if type(observed) is not bytes or observed != _bytes(expected):
            raise ValueError("Public turn must expose only demos and the current query input")
        if adapter.public_turn(deepcopy(altered), index) != _bytes(expected):
            raise ValueError("Public turn depends on private metadata or query answers")
        future_changed = deepcopy(generated)
        for other_index, pair in enumerate(future_changed["test"]):
            if other_index != index:
                pair["input"] = [[9]]
        if adapter.public_turn(future_changed, index) != _bytes(expected):
            raise ValueError("Public turn depends on another query's input")
        payload = _bytes(expected)
        path = f"public/turns/{_sha(payload)}.json"
        files[path] = payload
        turns.append(path)
    single = deepcopy(generated)
    single["test"] = single["test"][:1]
    if adapter.public_turn(single, 0) != files[turns[0]]:
        raise ValueError("First-turn content reveals whether later queries exist")
    return files, {"challenge": challenge, "turns": turns}


def _rotation_findings(pairs, outputs):
    """Reuse executed labels; findings are advisory and do not change the core gate."""
    findings, checked, total = [], 0, 0
    for demos in combinations(range(len(pairs)), 2):
        for rival, predictions in outputs.items():
            if not all(predictions[index] == pairs[index]["output"] for index in demos):
                continue
            for query in range(len(pairs)):
                if query in demos:
                    continue
                checked += 1
                if predictions[query] != pairs[query]["output"]:
                    total += 1
                    if len(findings) < 16:
                        findings.append({"demonstration_pair_indices": list(demos),
                                         "query_pair_index": query, "rival": rival})
    return {"two_demo_subsets": len(list(combinations(range(len(pairs)), 2))),
            "surviving_rival_query_comparisons": checked, "disagreement_count": total,
            "first_findings": findings, "label_basis": "cached protected Racket outputs",
            "status": "findings" if total else "no_findings_in_tested_rivals"}


def _audit_episode(adapter, evaluator, seed, settings, demos):
    generated, episode = _normalize_episode(adapter, seed, settings, demos, 4)
    pairs = episode["train"] + episode["test"]
    facts = [_facts(pair["input"]) for pair in pairs]
    for index, fact in enumerate(facts[:demos]):
        objs = fact["objects"]
        if (len({obj["holes"] for obj in objs}) < 2
                or not any(a["holes"] == b["holes"] and a["area"] != b["area"]
                           for a, b in combinations(objs, 2))):
            raise ValueError(f"Demonstration {index} does not expose both sorting keys")
    for index, pair in enumerate(pairs):
        actual = evaluator.execute(episode["program"], pair["input"])
        if actual != pair["output"]:
            raise ValueError(f"Protected Racket label mismatch in pair {index}")
        if _grid(adapter.predict(deepcopy(pair["input"]), deepcopy(settings))) != actual:
            raise ValueError(f"Independent protected replay differs from adapter.predict in pair {index}")
    programs = rival_programs(episode["program"], settings)
    outcomes = {}
    for name, program in programs.items():
        try:
            outcomes[name] = [evaluator.execute(program, pair["input"]) for pair in pairs]
        except Exception as error:
            raise ValueError(f"Rival {name} failed totality on an exercised input: {error}") from error
    checks = {}
    for count in sorted({2, demos}):
        survivors = [name for name, predictions in outcomes.items()
                     if all(predictions[index] == pairs[index]["output"] for index in range(count))]
        for name in survivors:
            if any(outcomes[name][demos + index] != pair["output"]
                   for index, pair in enumerate(episode["test"])):
                raise ValueError(f"Rival {name} fits {count} demos but changes a query answer")
        checks[str(count)] = {"survivors": survivors, "query_agreement": True,
                              "query_count": 4, "demonstrations_used": list(range(count))}
    files, public = _public_files(adapter, generated, episode)
    episode["input_facts"] = facts
    episode["rival_outputs"] = outcomes
    episode["public_files"] = public
    summary = {"seed": seed, "settings": settings, "demos": demos, "queries": 4,
               "protected_label_count": len(pairs), "rival_count": len(programs),
               "all_rivals_total": True, "demonstration_checks": checks,
               "rival_demo_match_masks": {name: [predictions[i] == pairs[i]["output"]
                                                 for i in range(demos)]
                                            for name, predictions in outcomes.items()},
               "rotations": _rotation_findings(pairs, outcomes),
               "query_sizes": [fact["input_size"] for fact in facts[demos:]],
               "query_painted_cells": [fact["painted_cells"] for fact in facts[demos:]]}
    return episode, summary, programs, files


def _census(adapter, seed_count):
    canvas, counts, unique = Counter(), Counter(), set()
    changed_pairs = 0
    for seed in range(seed_count):
        _, normal = _normalize_episode(adapter, seed, {"area_order": "larger_first"}, 3, 4)
        _, high = _normalize_episode(adapter, seed, {"area_order": "larger_first"}, 6, 4)
        _, low = _normalize_episode(adapter, seed, {"area_order": "larger_first"}, 2, 1)
        _, other = _normalize_episode(adapter, seed, {"area_order": "smaller_first"}, 3, 4)
        if (normal["train"] != high["train"][:3] or normal["test"] != high["test"]
                or normal["train"][:2] != low["train"] or normal["test"][:1] != low["test"]):
            raise ValueError("Sampler changes existing pairs when demo/query counts change")
        for split in ("train", "test"):
            for first, second in zip(normal[split], other[split]):
                if first["input"] != second["input"]:
                    raise ValueError("Sampler inputs depend on the private setting")
                changed_pairs += first["output"] != second["output"]
                fact = _facts(first["input"])
                canvas["x".join(map(str, fact["input_size"]))] += 1
                counts[str(len(fact["objects"]))] += 1
                unique.add(_sha(_bytes(first["input"])))
    return {"status": "passed" if seed_count else "not_run",
            "seed_count": seed_count, "seeds": list(range(seed_count)),
            "label_basis": "Python adapter only; these extra census labels were not Racket-replayed",
            "paired_setting_inputs_equal": True if seed_count else None,
            "demo_query_prefixes_preserved": True if seed_count else None,
            "demo_counts_exercised": [2, 3, 6] if seed_count else [],
            "query_counts_exercised": [1, 4] if seed_count else [],
            "canonical_order_input_count": seed_count * 7, "unique_input_count": len(unique),
            "setting_changed_pair_count": changed_pairs,
            "canvas_counts": dict(sorted(canvas.items())), "object_counts": dict(sorted(counts.items()))}


def audit(census_seeds=12):
    adapter = _load_adapter()
    binding = _source_binding(adapter)
    episodes, summaries, programs, files = [], [], {}, {}
    started = time.monotonic()
    evaluator = Evaluator()
    try:
        for seed, demos in ((0, 2), (17, 6)):
            for order in adapter.AREA_ORDERS:
                episode, summary, rivals, public = _audit_episode(
                    adapter, evaluator, seed, {"area_order": order}, demos)
                if episodes and episodes[-1]["seed"] == seed:
                    for split in ("train", "test"):
                        if ([pair["input"] for pair in episodes[-1][split]]
                                != [pair["input"] for pair in episode[split]]):
                            raise ValueError("Protected episode inputs differ across private settings")
                episodes.append(episode)
                summaries.append(summary)
                files.update(public)
                programs[order] = {name: {"program": program, "sha256": _sha(program.encode())}
                                   for name, program in rivals.items()}
        census = _census(adapter, census_seeds)
    finally:
        evaluator.close()
    if binding != _source_binding(adapter):
        raise ValueError("Source changed during audit; no artifacts will be published")
    files["private/examples.json"] = _bytes({"schema": "hole-count-packing-audit-examples-v1",
                                             "label_basis": "protected Racket replay", "episodes": episodes})
    files["private/rival_programs.json"] = _bytes(programs)
    summary = {"schema": "hole-count-packing-teaching-audit-v1", "task_id": TASK_ID,
               "status": "passed", "audit_source_binding": binding,
               "racket": evaluator.identity, "racket_evaluations": evaluator.calls,
               "cached_evaluation_hits": evaluator.hits, "episodes": summaries,
               "sampler_census": census, "duration_seconds": round(time.monotonic() - started, 3),
               "public_export_checks": {"query_answers_masked": True,
                                        "current_query_only_per_turn": True,
                                        "other_query_inputs_do_not_affect_turn": True,
                                        "first_turn_identical_if_stopped_after_one": True,
                                        "private_metadata_and_answer_independence": True,
                                        "names_derived_only_from_visible_content": True},
               "artifacts": {path: _sha(payload) for path, payload in sorted(files.items())},
               "limits": ["Finite named-rival evidence, not uniqueness over all possible rules.",
                          "Two-demo rotations are advisory; disagreements are reported, not hidden.",
                          "The extra sampler census uses Python labels and adds no Racket label claim.",
                          "This task-local audit grants neither native qualification nor owner acceptance."]}
    files["audit.json"] = _bytes(summary)
    return summary, files


def _publish(out, files):
    if out.exists() or out.is_symlink():
        raise ValueError("--out must name a fresh directory")
    out.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".hole-audit-staging-", dir=out.parent))
    try:
        for relative, payload in files.items():
            path = temporary / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
        if out.exists() or out.is_symlink():
            raise ValueError("Output appeared during audit; refusing to replace it")
        temporary.rename(out)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path, help="Fresh directory; public artifacts appear only after a passing audit")
    parser.add_argument("--census-seeds", type=int, default=12, help="Extra Python-only census, 0..24 seeds (default 12)")
    args = parser.parse_args(argv)
    try:
        if not 0 <= args.census_seeds <= 24:
            raise ValueError("--census-seeds must be in 0..24")
        out = args.out.absolute()
        if out.exists() or out.is_symlink():
            raise ValueError("--out must name a fresh directory")
        summary, files = audit(args.census_seeds)
        _publish(out, files)
    except Exception as error:
        print(f"AUDIT FAILED; no result directory published: {error}", file=sys.stderr)
        return 1
    print(json.dumps({"status": summary["status"], "audit": str(out / "audit.json"),
                      "episodes": len(summary["episodes"]),
                      "racket_evaluations": summary["racket_evaluations"],
                      "rotation_disagreements": sum(row["rotations"]["disagreement_count"]
                                                    for row in summary["episodes"])}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
