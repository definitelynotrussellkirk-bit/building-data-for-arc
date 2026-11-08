"""Bounded protected-Racket checks and private causal evidence for this prototype.

Run through the packet's ``review.py run`` or ``run_with_racket.py`` wrapper.
This tool never qualifies, accepts, or admits the prototype to training.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

from arcpuzzles.catalog import Catalog
from arcpuzzles.runtime import validate_grid
from reviewer_support import canonical_pairs, public_challenge_bytes, public_challenge_id


TASK = "9af68e46cf69"
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SETTINGS = ({"selection": "all_enclosed"}, {"selection": "largest_enclosed_region"})
DEPENDENCY = {
    "step_a": "Discover complete four-connected background-9 regions, identify the entire regions strictly enclosed by each foreground object's bounding box, and compute each object's maximum single-region area.",
    "intermediate": "The enclosed region cell sets and their areas for each object, together with the maximum single-region area used as that object's score.",
    "step_b": "Rank the positive object scores globally and recolor every whole object attaining the maximum score, retaining all ties.",
    "why_b_depends_on_a": "The selected objects depend on the input's connected background regions and their separate areas. Summing an object's enclosed areas instead of taking the largest single region can change the winning object or break a true tie, so the later ranking needs the computed region structure and scores.",
}


def _raw(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode()


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _relative(path):
    return Path(os.path.relpath(Path(path).resolve(), ROOT)).as_posix()


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(_raw(value))


def _load_adapter():
    path = HERE / "adapter.py"
    name = "_verify_9af68e46cf69_adapter_" + _sha(path)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load adjacent adapter: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _source_snapshot():
    catalog = Catalog(ROOT)
    row = catalog.describe(TASK)
    authority = row.get("rule_task_id", TASK)
    programs = {item.get("program_solution") for item in catalog._variants().get(authority, [])}
    _require(len(programs) == 1 and all(type(p) is str and p for p in programs),
             "Expected one exact canonical program")
    canonical = next(iter(programs))
    files = {ROOT / row["generator"]}
    files.update(path for path in HERE.rglob("*") if path.is_file()
                 and path.suffix in {".py", ".rkt", ".json"}
                 and not {"evidence", "examples", "__pycache__"}.intersection(path.relative_to(HERE).parts))
    snapshot = {
        "task_id": TASK, "rule_task_id": authority,
        "generator_sha256": _sha(ROOT / row["generator"]),
        "canonical_rule_hash": row["rule_hash"],
        "canonical_program_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
        "files": [{"path": path.relative_to(ROOT).as_posix(), "sha256": _sha(path)}
                  for path in sorted(files)],
    }
    return snapshot, canonical


class RacketEvaluator:
    """Execute each program/input combination once through the public bridge API."""

    def __init__(self):
        from arc_repl.racket_bridge import RacketBridge
        from puzzle_generators.rule_wrap import wrap_rule

        runtime = ROOT / "shared/runtime"
        for module_name in ("arc_repl.racket_bridge", "puzzle_generators.rule_wrap"):
            module_path = Path(sys.modules[module_name].__file__).resolve()
            _require(module_path.is_relative_to(runtime), "Racket helpers must belong to this checkout")
        self.bridge = RacketBridge()
        try:
            self.identity = self.bridge.runtime_identity
            _require(self.identity.get("backend") == "racket"
                     and self.identity.get("protected") is True,
                     "A live protected Racket runtime is required")
        except BaseException:
            self.bridge.close()
            raise
        self.wrap_rule = wrap_rule
        self.wrapped = {}
        self.cache = {}
        self.evaluations = 0

    def apply(self, program, grid):
        validate_grid(grid)
        key = (program, _raw(grid))
        if key not in self.cache:
            if program not in self.wrapped:
                self.wrapped[program] = self.wrap_rule(program)
            wrapped = self.wrapped[program]
            literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
            self.evaluations += 1
            self.cache[key] = deepcopy(validate_grid(self.bridge.eval_text(f"({wrapped} {literal})")))
        return deepcopy(self.cache[key])

    def close(self):
        self.bridge.close()


def _public_bytes(adapter, episode, index=0):
    view = adapter.public_view(episode, query_index=index)
    _require(type(view) is dict and set(view) == {"train", "test"}, "Public view leaks metadata")
    _require(type(view["train"]) is list and type(view["test"]) is list
             and len(view["test"]) == 1, "Public view must expose one query")
    _require(all(type(pair) is dict and set(pair) == {"input", "output"} for pair in view["train"]),
             "Public demonstration fields differ")
    _require(all(type(pair) is dict and set(pair) == {"input"} for pair in view["test"]),
             "Public query leaks an answer or metadata")
    payload = public_challenge_bytes(view)
    _require(hashlib.sha256(payload).hexdigest() == public_challenge_id(view), "Public byte/ID mismatch")
    return payload


def _components(grid, color):
    remaining = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}
    result = []
    while remaining:
        first = min(remaining)
        remaining.remove(first)
        cells, todo = {first}, [first]
        while todo:
            r, c = todo.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in remaining:
                    remaining.remove(point)
                    cells.add(point)
                    todo.append(point)
        result.append(cells)
    return result


def _bbox(cells):
    return (min(r for r, _ in cells), min(c for _, c in cells),
            max(r for r, _ in cells), max(c for _, c in cells))


def _topology(grid):
    """Independent flood fill for geometry receipts, without adapter helpers."""
    backgrounds = _components(grid, 9)
    objects = []
    for cells in _components(grid, 1):
        r1, c1, r2, c2 = _bbox(cells)
        regions = [sorted(region) for region in backgrounds
                   if all(r1 < r < r2 and c1 < c < c2 for r, c in region)]
        areas = sorted(len(region) for region in regions)
        border = {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
                  if r in (r1, r2) or c in (c1, c2)}
        objects.append({"cells": sorted(cells), "bbox": [r1, c1, r2, c2],
                        "hole_areas": areas, "score": max(areas, default=0),
                        "enclosed_regions": regions,
                        "irregular": cells != border,
                        "has_bbox_background": any(grid[r][c] == 9
                                                   for r in range(r1 + 1, r2)
                                                   for c in range(c1 + 1, c2))})
    return objects


def _facts(grid):
    validate_grid(grid)
    h, w = len(grid), len(grid[0])
    _require(9 <= h <= 30 and 11 <= w <= 30, "Input dimensions outside prototype grammar")
    _require({cell for row in grid for cell in row} <= {1, 9}, "Input palette must use foreground 1 and background 9")
    objects = _topology(grid)
    positives = [obj for obj in objects if obj["score"] > 0]
    negatives = [obj for obj in objects if obj["score"] == 0]
    _require(2 <= len(positives) <= 3 and 1 <= len(negatives) <= 4,
             "Input must contain 2..3 positive and 1..4 negative objects")
    _require(any(obj["irregular"] for obj in positives), "Missing irregular hole-bearing positive")
    _require(any(obj["has_bbox_background"] for obj in negatives), "Missing open-bbox negative decoy")
    for i, first in enumerate(objects):
        a, b, c, d = first["bbox"]
        for second in objects[i + 1:]:
            e, f, g, k = second["bbox"]
            _require(c < e or g < a or d < f or k < b, "Object bounding boxes must be disjoint")
    cells = [cell for obj in objects for cell in obj["cells"]]
    r1, c1, r2, c2 = _bbox(cells)
    return {"shape": [h, w], "foreground_cells": len(cells),
            "foreground_extent": [r2 - r1 + 1, c2 - c1 + 1],
            "n_holey": len(positives), "n_solid": len(negatives),
            "maximum_score": max(obj["score"] for obj in objects),
            "objects": [{key: obj[key] for key in ("bbox", "hole_areas", "score")}
                        for obj in objects],
            "irregular_positive": True, "open_bbox_negative": True,
            "touches_canvas_boundary": r1 == 0 or c1 == 0 or r2 == h - 1 or c2 == w - 1}


def _check_analysis(adapter, grid):
    expected = _topology(grid)
    observed = adapter.analyze(grid)
    def signature(obj):
        return (tuple(tuple(cell) for cell in sorted(obj["cells"])), tuple(obj["bbox"]),
                tuple(sorted(obj["hole_areas"])), obj["score"])
    _require(sorted(signature(obj) for obj in observed["objects"])
             == sorted(signature(obj) for obj in expected), "Adapter's component/region scores differ from independent flood fill")
    _require(observed["maximum_score"] == max(obj["score"] for obj in expected)
             and observed["height"] == len(grid) and observed["width"] == len(grid[0]),
             "Adapter's maximum score or dimensions differ")
    return expected


def check(output):
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    output.mkdir(parents=True, exist_ok=False)
    report = {"schema": "9af68e46cf69-parametric-focused-checks-v1", "success": False,
              "command": sys.argv, "cwd": _relative(Path.cwd()), "errors": [], "episodes": [],
              "training_admitted": False,
              "scope": "Two settings; seeds 0 and 17; demos 2, 3, 6; four queries. Finite Racket labels and teaching rivals, not universal identifiability or native acceptance."}
    examples, public_files, inputs, shapes, paired = [], {}, {}, Counter(), {}
    evaluator = None
    try:
        adapter = _load_adapter()
        snapshot, canonical = _source_snapshot()
        report["source_hashes"] = snapshot
        programs = {s["selection"]: adapter.program(deepcopy(s)) for s in SETTINGS}
        _require(programs["all_enclosed"] == canonical, "Default program differs from exact selected canonical bytes")
        report["program_sha256"] = {selection: hashlib.sha256(p.encode()).hexdigest()
                                     for selection, p in programs.items()}
        evaluator = RacketEvaluator()
        report["racket"] = evaluator.identity
        for settings in SETTINGS:
            selection = settings["selection"]
            for seed in (0, 17):
                for demos in (2, 3, 6):
                    episode = adapter.generate(seed, deepcopy(settings), demos, 4)
                    _require(episode.get("program_solution") == programs[selection], "Emitted program differs")
                    _require(len(episode.get("train", [])) == demos and len(episode.get("test", [])) == 4,
                             "Independent demonstration/query counts differ")
                    all_pairs = episode["train"] + episode["test"]
                    keys = [_raw(pair["input"]) for pair in all_pairs]
                    _require(len(set(keys)) == len(keys), "An episode repeats an input")
                    input_order = [pair["input"] for pair in all_pairs]
                    pair_key = (seed, demos)
                    if pair_key in paired:
                        _require(input_order == paired[pair_key], "Inputs depend on private setting")
                    else:
                        paired[pair_key] = deepcopy(input_order)
                    for pair in all_pairs:
                        grid = pair["input"]
                        facts = _facts(grid)
                        topology = _check_analysis(adapter, grid)
                        inputs.setdefault(_raw(grid), facts)
                        shapes[f"{facts['shape'][0]}x{facts['shape'][1]}"] += 1
                        validate_grid(pair["output"])
                        for rival in SETTINGS:
                            actual = evaluator.apply(programs[rival["selection"]], grid)
                            expected = deepcopy(grid)
                            for obj in topology:
                                if obj["score"] > 0 and (rival["selection"] == "all_enclosed"
                                                         or obj["score"] == facts["maximum_score"]):
                                    for r, c in obj["cells"]:
                                        expected[r][c] = 8
                            _require(actual == expected, "Racket differs from independently derived whole-object selection")
                            _require(actual == adapter.mirror(grid, deepcopy(rival)),
                                     "Racket label differs from the independent prototype mirror")
                        _require(evaluator.apply(programs[selection], grid) == pair["output"], "Claimed label differs from Racket")
                    survivors = [rival["selection"] for rival in SETTINGS
                                 if all(evaluator.apply(programs[rival["selection"]], p["input"]) == p["output"]
                                        for p in episode["train"])]
                    _require(survivors == [selection], "Demonstrations do not identify the declared setting")
                    teaching = adapter.teaching_check(episode, deepcopy(settings))
                    _require(type(teaching) is dict and not teaching.get("harmful_survivors"),
                             "A declared harmful teaching rival survives")
                    _require(isinstance(teaching.get("survivors"), list)
                             and isinstance(teaching.get("eliminated"), dict), "Malformed teaching certificate")
                    for rejected, indices in teaching["eliminated"].items():
                        _require(isinstance(rejected, str) and isinstance(indices, list)
                                 and all(type(i) is int and 0 <= i < demos for i in indices),
                                 "Teaching elimination cites evidence outside demonstrations")
                    private_changed = deepcopy(episode)
                    private_changed.update(seed=-999, settings={"selection": "private-mutation"},
                                           program_solution="private-mutation", hidden={"answer": 9})
                    for pair in private_changed["test"]:
                        pair["output"] = [[9]]
                    _require(adapter.teaching_check(private_changed, deepcopy(settings)) == teaching,
                             "Query answers or private metadata affect teaching evidence")
                    one = adapter.generate(seed, deepcopy(settings), demos, 1)
                    _require(len(one.get("test", [])) == 1
                             and one["test"][0] == episode["test"][0]
                             and _public_bytes(adapter, one) == _public_bytes(adapter, episode),
                             "First turn differs between one-query and four-query requests")
                    for index in range(4):
                        payload = _public_bytes(adapter, episode, index)
                        _require(payload == _public_bytes(adapter, private_changed, index),
                                 "Public bytes depend on private metadata or query answers")
                        public_files[hashlib.sha256(payload).hexdigest()] = payload
                    query_facts = [_facts(p["input"]) for p in episode["test"]]
                    _require(query_facts[0]["shape"] == [9, 11]
                             and query_facts[1]["shape"] == [12, 16]
                             and query_facts[2]["shape"] == [22, 26]
                             and query_facts[3]["shape"] == [30, 30], "Required query size profiles differ")
                    stress = query_facts[3]
                    _require(min(stress["foreground_extent"]) >= 27
                             and stress["foreground_cells"] >= 100
                             and stress["maximum_score"] >= 20,
                             "30x30 stress requires extent >=27x27, >=100 foreground cells, and an enclosed region of area >=20")
                    row = {"seed": seed, "settings": deepcopy(settings), "demos": demos, "queries": 4,
                           "racket_setting_survivors": survivors, "teaching": teaching, "query_geometry": query_facts}
                    report["episodes"].append(row)
                    examples.append({**row, **deepcopy(episode)})
        canonical_examples = canonical_pairs(TASK, root=ROOT, labeled_only=True)[:5]
        for pair in canonical_examples:
            _require(evaluator.apply(canonical, pair["input"]) == pair["output"], "Canonical source pair differs from Racket")
        report["canonical_pairs_checked"] = len(canonical_examples)
        negative = 0
        for grid in ([[True]], [[1.0]], [[1], [1, 2]], [[0] * 31]):
            invalid = deepcopy(examples[0])
            invalid["train"][0]["input"] = grid
            try:
                _public_bytes(adapter, invalid)
            except (ValueError, TypeError):
                negative += 1
            else:
                raise ValueError("Public projection accepted an invalid typed grid")
        report["invalid_public_grid_rejections"] = negative
        _require(_source_snapshot()[0] == snapshot, "Prototype source changed during checks")
        (output / "public").mkdir()
        for identifier, payload in sorted(public_files.items()):
            path = output / "public" / f"{identifier}.json"
            with path.open("xb") as stream:
                stream.write(payload)
            _require(path.read_bytes() == payload and _sha(path) == identifier, "Serialized public hash/bytes differ")
        report.update(success=True, declared_setting_totality_checks=2 * len(inputs),
                      first_turn_invariance_checks=len(examples), private_mutation_invariance_checks=len(examples),
                      matched_input_comparisons=len(paired), public_challenges=len(public_files))
    except Exception as error:
        report["errors"].append({"type": type(error).__name__, "message": str(error)})
    finally:
        if evaluator is not None:
            report["racket_evaluations"] = evaluator.evaluations
            evaluator.close()
    report.update(episodes_completed=len(examples), labels_checked=sum(r["demos"] + r["queries"] for r in report["episodes"]),
                  unique_inputs=len(inputs), shape_counts=dict(sorted(shapes.items())),
                  private_examples="private-examples.json", public_directory="public")
    _write_new(output / "private-examples.json", {"private": True, "episodes": examples})
    _write_new(output / "checks.json", report)
    print(json.dumps({"success": report["success"], "checks": _relative(output / "checks.json"),
                      "episodes": len(examples), "racket_evaluations": report.get("racket_evaluations", 0),
                      "errors": report["errors"]}, sort_keys=True))
    return 0 if report["success"] else 1


def witness(qualification, output):
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    qualification = json.loads(Path(qualification).read_text())
    _require(qualification.get("schema") == "arcpuzzles-parametric-qualification-v1"
             and qualification.get("status") == "qualified" and qualification.get("task_id") == TASK,
             "Witness requires this task's successful native qualification")
    for item in qualification["source_binding"]["files"]:
        _require(_sha(ROOT / item["path"]) == item["sha256"], "Qualified source changed: " + item["path"])
    adapter = _load_adapter()
    settings = {"selection": "largest_enclosed_region"}
    program = adapter.program(settings)
    counterfactual = (HERE / "largest_total.rkt").read_text()
    setting_key = _raw(settings).decode().strip()
    _require(hashlib.sha256(program.encode()).hexdigest() == qualification["programs"].get(setting_key),
             "Witness rule is not the qualified setting program")
    episode = adapter.generate(0, settings, 3, 4)
    evaluator = RacketEvaluator()
    try:
        cases = []
        for pair in episode["train"][:2]:
            grid = pair["input"]
            topology = _check_analysis(adapter, grid)
            facts = _facts(grid)
            actual, alternate = evaluator.apply(program, grid), evaluator.apply(counterfactual, grid)
            _require(actual == pair["output"] and actual != alternate, "Causal counterfactual must change the Racket label")
            total_maximum = max(sum(obj["hole_areas"]) for obj in topology)
            expected_wrong = deepcopy(grid)
            for obj in topology:
                if sum(obj["hole_areas"]) > 0 and sum(obj["hole_areas"]) == total_maximum:
                    for r, c in obj["cells"]:
                        expected_wrong[r][c] = 8
            _require(alternate == expected_wrong,
                     "Counterfactual does not implement largest-total-enclosed-area scoring")
            cases.append({"input": deepcopy(grid), "settings": deepcopy(settings),
                          "intermediate_value": {
                              "objects": [{"bbox": obj["bbox"], "hole_areas": obj["hole_areas"],
                                           "maximum_single_region_score": obj["score"],
                                           "counterfactual_sum_score": sum(obj["hole_areas"]),
                                           "enclosed_regions": obj["enclosed_regions"]}
                                          for obj in topology],
                              "global_maximum_single_region_score": facts["maximum_score"],
                              "maximum_score_tie_count": sum(obj["score"] == facts["maximum_score"]
                                                             for obj in topology),
                              "counterfactual_global_maximum_sum_score": total_maximum},
                          "program": program, "output": actual, "counterfactual_program": counterfactual,
                          "counterfactual_output": alternate, "ablation": "wrong_intermediate"})
        _require(any(case["intermediate_value"]["maximum_score_tie_count"] > 1 for case in cases),
                 "The two witness cases must include a true maximum-score tie")
        value = {"schema": "arcpuzzles-sequential-dependency-witness-v1",
                 "source_binding": qualification["source_binding"], **DEPENDENCY,
                 "racket": {"backend": "racket", "protected": True}, "cases": cases,
                 "execution_identity": evaluator.identity, "racket_evaluations": evaluator.evaluations,
                 "limits": "Two finite wrong-intermediate witnesses, including a tied maximum; causal interpretation requires review and is not a universal depth proof."}
    finally:
        evaluator.close()
    for item in qualification["source_binding"]["files"]:
        _require(_sha(ROOT / item["path"]) == item["sha256"], "Qualified source changed during witness: " + item["path"])
    _write_new(output, value)
    print(json.dumps({"success": True, "witness": _relative(output), "cases": len(cases),
                      "sha256": _sha(output), "racket_evaluations": value["racket_evaluations"]}, sort_keys=True))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    focused = actions.add_parser("check", help="run the bounded protected-Racket and projection checks")
    focused.add_argument("--out", type=Path, required=True)
    causal = actions.add_parser("witness", help="write protected-Racket causal evidence for qualified bytes")
    causal.add_argument("--qualification", type=Path, required=True)
    causal.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        return check(args.out) if args.action == "check" else witness(args.qualification, args.out)
    except Exception as error:
        print(json.dumps({"success": False, "error": type(error).__name__, "message": str(error)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
