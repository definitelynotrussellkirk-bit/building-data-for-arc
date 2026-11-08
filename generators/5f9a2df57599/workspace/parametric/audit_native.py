#!/usr/bin/env python3
"""Independent finite teaching audit for the native side-wall family.

The Python rule and rivals do not import the generator's mirror.  Racket labels
come from this checkout's protected native evaluator, never the old prototype's
direct bridge.  Queries are examined only after the demo version space freezes.
This is bounded reviewer evidence, not acceptance or a universal uniqueness proof.
"""
from __future__ import annotations

import argparse
from collections import deque
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

TASK_ID = "5f9a2df57599"
POLICIES = ("canvas_edges", "gray_walls")
RIVALS = (
    "size_le4", "ignore_walls", "enclosed_components", "reject_l3", "only_rectangles",
    "skip_left", "skip_right", "skip_top", "skip_bottom", "ignore_column0",
    "eight_connected", "bbox_paint", "first_component", "largest_component",
    "opposite_policy",
)
DESCRIPTIONS = {
    "size_le4": "Fill every non-top/bottom zero component with bbox <=4x4, preserving only the column-zero exception; inspect no gray sides.",
    "ignore_walls": "Fill every non-top/bottom zero component except the column-zero exception, ignoring all gray sides and side policy.",
    "enclosed_components": "Use canvas-border eligibility and the column-zero exception without quantifying the complete bbox sides.",
    "reject_l3": "Use policy-aware canvas-border eligibility, but reject every nonrectangular three-cell component instead of checking any gray bbox sides.",
    "only_rectangles": "Apply the intended walls predicate only to solid rectangular zero components.",
    "skip_left": "Omit the complete left-side predicate, including its boundary condition.",
    "skip_right": "Omit the complete right-side predicate, including its boundary condition.",
    "skip_top": "Omit the complete top-side predicate, including its boundary condition.",
    "skip_bottom": "Omit the complete bottom-side predicate, including its boundary condition.",
    "ignore_column0": "Omit the multi-row column-zero exception.",
    "eight_connected": "Find zero components with eight-neighbor connectivity before the intended bbox wall test.",
    "bbox_paint": "For an eligible component paint every bbox cell, including gray cells absent from the component.",
    "first_component": "Paint only the first eligible component in row-major discovery order.",
    "largest_component": "Paint only the largest eligible component, with row-major tie breaking.",
    "opposite_policy": "Apply the other declared side-boundary policy.",
}


def raw(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def digest(value: Any) -> str:
    return hashlib.sha256(raw(value)).hexdigest()


def source_hash(source: str) -> str:
    return hashlib.sha256(source.encode()).hexdigest()


def library_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "shared/data/canonical/puzzles.jsonl").is_file():
            return parent
    raise ValueError("Cannot find the same-checkout canonical ledger")


def _load_adjacent(name: str):
    path = Path(__file__).with_name(name + ".py").resolve()
    key = "_wall_audit_" + name + "_" + source_hash(str(path))[:16]
    spec = importlib.util.spec_from_file_location(key, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[key] = module
    spec.loader.exec_module(module)
    return module


def policy_value(policy: Any) -> str:
    if type(policy) is dict:
        if set(policy) != {"side_boundary_policy"}:
            raise ValueError("settings must contain exactly side_boundary_policy")
        policy = policy["side_boundary_policy"]
    if type(policy) is not str or policy not in POLICIES:
        raise ValueError("unknown side_boundary_policy")
    return policy


def grid_value(grid: Any, *, input_grid: bool = True) -> list[list[int]]:
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(grid[0])
    colors = (0, 5) if input_grid else tuple(range(10))
    if any(type(row) is not list or len(row) != width or any(
            type(cell) is not int or cell not in colors for cell in row) for row in grid):
        raise ValueError("grid must be rectangular with exact allowed integer colors")
    return deepcopy(grid)


def _components(grid, connectivity=4):
    height, width = len(grid), len(grid[0])
    seen = set()
    steps = ((-1, 0), (0, -1), (0, 1), (1, 0))
    if connectivity == 8:
        steps += ((-1, -1), (-1, 1), (1, -1), (1, 1))
    found = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while queue:
                cell = queue.popleft()
                cells.append(cell)
                for dr, dc in steps:
                    nr, nc = cell[0] + dr, cell[1] + dc
                    if (0 <= nr < height and 0 <= nc < width
                            and grid[nr][nc] == 0 and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            found.append(sorted(cells))
    return found


def facts(grid: Any, policy: Any = "canvas_edges", *, connectivity: int = 4) -> list[dict]:
    """Independent component membership, bbox, side values, and eligibility."""
    selected = policy_value(policy)
    grid = grid_value(grid)
    if type(connectivity) is not int or connectivity not in (4, 8):
        raise ValueError("connectivity must be 4 or 8")
    height, width = len(grid), len(grid[0])
    result = []
    for cells in _components(grid, connectivity):
        r0, c0 = map(min, zip(*cells))
        r1, c1 = map(max, zip(*cells))
        sides = {
            "top": [grid[r0 - 1][c] for c in range(c0, c1 + 1)] if r0 else None,
            "bottom": [grid[r1 + 1][c] for c in range(c0, c1 + 1)] if r1 + 1 < height else None,
            "left": [grid[r][c0 - 1] for r in range(r0, r1 + 1)] if c0 else None,
            "right": [grid[r][c1 + 1] for r in range(r0, r1 + 1)] if c1 + 1 < width else None,
        }
        walls = {side: values is not None and all(value == 5 for value in values)
                 for side, values in sides.items()}
        if selected == "canvas_edges":
            walls["left"] = walls["left"] or c0 == 0
            walls["right"] = walls["right"] or c1 == width - 1
        excluded = c0 == c1 == 0 and r1 > r0
        result.append({
            "cells": [list(cell) for cell in cells], "bbox": [r0, c0, r1, c1],
            "shape": [r1 - r0 + 1, c1 - c0 + 1], "size": len(cells),
            "rectangle": len(cells) == (r1 - r0 + 1) * (c1 - c0 + 1),
            "side_values": sides, "walls": walls,
            "excluded_left_vertical": excluded,
            "eligible": all(walls.values()) and not excluded,
        })
    return result


def reference(grid: Any, policy: Any = "canvas_edges") -> list[list[int]]:
    """Fresh BFS reference; no production, prototype, or native mirror calls."""
    output = grid_value(grid)
    for region in facts(grid, policy):
        if region["eligible"]:
            for row, col in region["cells"]:
                output[row][col] = 4
    return output


def rival_output(grid: Any, policy: Any, name: str) -> list[list[int]]:
    selected = policy_value(policy)
    if name not in RIVALS:
        raise ValueError("unknown rival: " + str(name))
    if name == "opposite_policy":
        return reference(grid, POLICIES[1 - POLICIES.index(selected)])
    output = grid_value(grid)
    height, width = len(output), len(output[0])
    regions = facts(grid, selected, connectivity=8 if name == "eight_connected" else 4)
    chosen = []
    for region in regions:
        r0, c0, r1, c1 = region["bbox"]
        walls = region["walls"]
        exception_ok = not region["excluded_left_vertical"]
        eligible = region["eligible"]
        if name in ("size_le4", "ignore_walls", "enclosed_components", "reject_l3"):
            eligible = r0 > 0 and r1 < height - 1 and exception_ok
            if name == "size_le4":
                eligible = eligible and max(region["shape"]) <= 4
            if name in ("enclosed_components", "reject_l3") and selected == "gray_walls":
                eligible = eligible and c0 > 0 and c1 < width - 1
            if name == "reject_l3":
                eligible = eligible and not (region["size"] == 3 and not region["rectangle"])
        elif name.startswith("skip_"):
            omitted = name[5:]
            eligible = exception_ok and all(value for side, value in walls.items() if side != omitted)
        elif name == "ignore_column0":
            eligible = all(walls.values())
        elif name == "only_rectangles":
            eligible = eligible and region["rectangle"]
        if eligible:
            chosen.append(region)
    if chosen and name == "first_component":
        chosen = chosen[:1]
    if chosen and name == "largest_component":
        chosen = [max(chosen, key=lambda region: region["size"])]
    for region in chosen:
        cells = region["cells"]
        if name == "bbox_paint":
            r0, c0, r1, c1 = region["bbox"]
            cells = [(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)]
        for row, col in cells:
            output[row][col] = 4
    return output


def teaching_features(train: list[dict], policy: Any) -> dict:
    """A small proposed size/wall teaching gate, derived from visible pairs."""
    selected = policy_value(policy)
    result = {"eligible_large": [], "small_rejected_full_side": []}
    for pair_index, pair in enumerate(train):
        expected = reference(pair["input"], selected)
        if grid_value(pair["output"], input_grid=False) != expected:
            raise ValueError("claimed demonstration label differs from independent reference")
        for index, region in enumerate(facts(pair["input"], selected)):
            item = {"pair_index": pair_index, "component_index": index,
                    "bbox": region["bbox"], "size": region["size"]}
            if region["eligible"] and max(region["shape"]) > 4:
                result["eligible_large"].append(item)
            if (not region["eligible"] and max(region["shape"]) <= 4
                    and not region["excluded_left_vertical"]
                    and any(values is not None and 0 in values
                            for values in region["side_values"].values())):
                r0, c0, r1, c1 = region["bbox"]
                h, w = len(pair["input"]), len(pair["input"][0])
                boundary_ok = r0 > 0 and r1 < h - 1
                if selected == "gray_walls":
                    boundary_ok = boundary_ok and c0 > 0 and c1 < w - 1
                if boundary_ok:
                    result["small_rejected_full_side"].append(item)
    result["passed"] = all(result[key] for key in ("eligible_large", "small_rejected_full_side"))
    return result


def canonical_program(policy: Any, *, root: Path | None = None) -> str:
    return _load_adjacent("prototype").materialize_program(policy_value(policy), root=root or library_root())


def rival_program(policy: Any, name: str, *, root: Path | None = None) -> str:
    """A complete retained rule, independently composed from native primitives."""
    selected = policy_value(policy)
    if name not in RIVALS:
        raise ValueError("unknown rival: " + str(name))
    if name == "opposite_policy":
        return canonical_program(POLICIES[1 - POLICIES.index(selected)], root=root)
    walls = {
        "top": "(and (> r1 0) (for/and ((c (range c1 (+ c2 1)))) (= (at g (- r1 1) c) 5)))",
        "bottom": "(and (< r2 (- h 1)) (for/and ((c (range c1 (+ c2 1)))) (= (at g (+ r2 1) c) 5)))",
        "left": "(for/and ((r (range r1 (+ r2 1)))) (= (at g r (- c1 1)) 5))",
        "right": "(for/and ((r (range r1 (+ r2 1)))) (= (at g r (+ c2 1)) 5))",
    }
    if selected == "canvas_edges":
        walls["left"] = "(or (= c1 0) " + walls["left"] + ")"
        walls["right"] = "(or (= c2 (- w 1)) " + walls["right"] + ")"
    else:
        walls["left"] = "(and (> c1 0) " + walls["left"] + ")"
        walls["right"] = "(and (< c2 (- w 1)) " + walls["right"] + ")"
    exception = "(not (and (= c1 0) (= c2 0) (> r2 r1)))"
    terms = [value for side, value in walls.items() if name != "skip_" + side]
    if name != "ignore_column0":
        terms.append(exception)
    if name in ("size_le4", "ignore_walls", "enclosed_components", "reject_l3"):
        terms = ["(> r1 0)", "(< r2 (- h 1))", exception]
        if name == "size_le4":
            terms += ["(<= (+ (- r2 r1) 1) 4)", "(<= (+ (- c2 c1) 1) 4)"]
        if name in ("enclosed_components", "reject_l3") and selected == "gray_walls":
            terms += ["(> c1 0)", "(< c2 (- w 1))"]
        if name == "reject_l3":
            terms.append("(not (and (= (obj-size obj) 3) (not (= (obj-size obj) (* (+ (- r2 r1) 1) (+ (- c2 c1) 1))))))")
    if name == "only_rectangles":
        terms.append("(= (obj-size obj) (* (+ (- r2 r1) 1) (+ (- c2 c1) 1)))")
    predicate = "(lambda (obj) (with-bbox obj (r1 c1 r2 c2) (and " + " ".join(terms) + ")))"
    objects = "objects-8" if name == "eight_connected" else "objects"
    subset = "eligible"
    if name == "first_component":
        subset = "(if (empty? eligible) '() (list (first eligible)))"
    if name == "largest_component":
        subset = "(if (empty? eligible) '() (list (argmax obj-size eligible)))"
    paint = "(paint-objects g selected 4)"
    if name == "bbox_paint":
        paint = """(for/fold ((out g)) ((obj selected))
          (with-bbox obj (r1 c1 r2 c2)
            (paint-cells out (for*/list ((r (range r1 (+ r2 1)))
                                        (c (range c1 (+ c2 1)))) (list r c)) 4)))"""
    return f"""(rule! (lambda (g)
      (let* ((h (rows g)) (w (cols g))
             (zero-regions ({objects} g 5))
             (eligible (filter {predicate} zero-regions))
             (selected {subset}))
        {paint})))"""


def structural_equivalence(policy: Any, name: str) -> dict | None:
    selected = policy_value(policy)
    if name == "ignore_column0" and selected == "gray_walls":
        return {"equivalent_to": "intended", "reason":
                "The strict left-wall predicate already requires c1>0, so a component confined to column zero is rejected before its exception matters."}
    if name == "enclosed_components" and selected == "canvas_edges":
        return {"equivalent_to": "ignore_walls", "reason":
                "Both programs require only non-top/bottom bounds and the same column-zero exception; the canonical policy adds no lateral boundary restriction."}
    return None


class CachedEvaluator:
    """Exact-source/input cache over the current protected native API."""

    def __init__(self, root: Path | str | None = None):
        self.root = Path(root or library_root()).resolve()
        self.cache = {}
        self.programs = {}
        self.inputs = {}
        self.evaluations = 0
        self.cache_hits = 0
        self.identity = None
        self._manager = self._bridge = self._apply = None

    def __enter__(self):
        from arcpuzzles.parametric_worker import _local_imports, _real_evaluator
        runtime = self.root / "shared/runtime"
        self._manager = _local_imports(runtime, runtime)
        self._manager.__enter__()
        try:
            self._apply, self.identity, self._bridge = _real_evaluator(runtime)
            from arc_repl.parser import parse_all, Symbol
            self._parse, self._symbol = parse_all, Symbol
        except BaseException:
            self._manager.__exit__(*sys.exc_info())
            self._manager = None
            raise
        return self

    def __exit__(self, *error):
        if self._bridge is not None:
            self._bridge.close()
        if self._manager is not None:
            self._manager.__exit__(*error)
        self._apply = None

    def __call__(self, program: str, grid: Any) -> list[list[int]]:
        if self._apply is None:
            raise ValueError("CachedEvaluator must be used as a context manager")
        normalized = grid_value(grid)
        if type(program) is not str or not 0 < len(program.encode()) <= 100000:
            raise ValueError("program must be complete bounded Racket source")
        if program not in self.programs:
            forms = self._parse(program)
            if (len(forms) != 1 or type(forms[0]) is not list or len(forms[0]) != 2
                    or forms[0][0] != self._symbol("rule!")):
                raise ValueError("program must be exactly one complete rule! expression")
            self.programs[program] = source_hash(program)
        key = (program, raw(normalized))
        if key in self.cache:
            self.cache_hits += 1
            return deepcopy(self.cache[key])
        self.evaluations += 1
        actual = grid_value(self._apply(program, normalized), input_grid=False)
        self.cache[key] = actual
        self.inputs[digest(normalized)] = normalized
        return deepcopy(actual)

    def evidence(self) -> dict:
        return {"racket": self.identity, "actual_evaluations": self.evaluations,
                "cache_hits": self.cache_hits, "unique_inputs": len(self.inputs),
                "unique_programs": len(self.programs),
                "evaluations": [{"program_sha256": source_hash(program),
                                 "input_sha256": digest(json.loads(input_bytes)),
                                 "output": output, "output_sha256": digest(output)}
                                for (program, input_bytes), output in self.cache.items()]}


def audit_episode(episode: dict, policy: Any, evaluator, *, root: Path | None = None) -> dict:
    """Freeze demo survivors before reading/evaluating any private query."""
    selected = policy_value(policy)
    program = canonical_program(selected, root=root)
    if episode.get("program_solution") != program:
        raise ValueError("episode program does not equal exact selected setting program")
    train = episode.get("train")
    if type(train) is not list or not 2 <= len(train) <= 6:
        raise ValueError("audit requires 2..6 demonstrations")
    demo_predictions = {}
    demo_inputs = []
    labels = []
    for pair in train:
        grid = grid_value(pair["input"])
        claimed = grid_value(pair["output"], input_grid=False)
        actual = evaluator(program, grid)
        if actual != claimed:
            raise ValueError("claimed demonstration label differs from protected Racket")
        if reference(grid, selected) != actual:
            raise ValueError("independent Python/Racket demonstration mismatch")
        demo_inputs.append(grid)
        labels.append(actual)
    rows = []
    programs = {}
    for name in RIVALS:
        candidate = rival_program(selected, name, root=root)
        programs[name] = candidate
        predicted = [evaluator(candidate, grid) for grid in demo_inputs]
        python = [rival_output(grid, selected, name) for grid in demo_inputs]
        if predicted != python:
            raise ValueError("independent Python/Racket rival demonstration mismatch: " + name)
        mismatches = [i for i, (a, b) in enumerate(zip(predicted, labels)) if a != b]
        demo_predictions[name] = predicted
        rows.append({"name": name, "description": DESCRIPTIONS[name],
                     "program_sha256": source_hash(candidate),
                     "demo_mismatch_indices": mismatches,
                     "first_two_demo_mismatch_indices": [i for i in mismatches if i < 2],
                     "structural_equivalence": structural_equivalence(selected, name)})
    # No test input or label is read before these immutable tuples exist.
    survivors = tuple(row["name"] for row in rows if not row["demo_mismatch_indices"])
    first_two_survivors = tuple(row["name"] for row in rows if not row["first_two_demo_mismatch_indices"])
    test = episode.get("test")
    if type(test) is not list or len(test) != 4:
        raise ValueError("audit requires four queries")
    query_inputs, query_labels, query_predictions = [], [], {name: [] for name in RIVALS}
    for pair in test:
        grid = grid_value(pair["input"])
        actual = evaluator(program, grid)
        if actual != grid_value(pair["output"], input_grid=False):
            raise ValueError("claimed query label differs from protected Racket")
        if reference(grid, selected) != actual:
            raise ValueError("independent Python/Racket query mismatch")
        query_inputs.append(grid)
        query_labels.append(actual)
        for name in RIVALS:
            predicted = evaluator(programs[name], grid)
            if predicted != rival_output(grid, selected, name):
                raise ValueError("independent Python/Racket rival query mismatch: " + name)
            query_predictions[name].append(predicted)
    for row in rows:
        name = row["name"]
        row["query_mismatch_indices"] = [i for i, (a, b) in enumerate(
            zip(query_predictions[name], query_labels)) if a != b]
        if row["demo_mismatch_indices"]:
            row["status"] = "refuted_by_demonstrations"
        elif row["query_mismatch_indices"]:
            row["status"] = "teaching_gap"
        elif row["structural_equivalence"] and row["structural_equivalence"]["equivalent_to"] == "intended":
            row["status"] = "structurally_equivalent_to_intended"
        else:
            row["status"] = "unrefuted_without_checked_query_disagreement"
    inputs = demo_inputs + query_inputs
    hashes = [digest(grid) for grid in inputs]
    if len(hashes) != len(set(hashes)):
        raise ValueError("demonstration/query inputs must be distinct")
    response_groups = {}
    for name in RIVALS:
        response_groups.setdefault(digest(demo_predictions[name] + query_predictions[name]), []).append(name)
    nontrivial30 = []
    for index, grid in enumerate(query_inputs):
        if len(grid) == len(grid[0]) == 30:
            regions = facts(grid, selected)
            eligible = [region for region in regions if region["eligible"]]
            quadrants = sorted({(r // 15, c // 15) for region in eligible for r, c in region["cells"]})
            nontrivial30.append({"query_index": index, "regions": len(regions),
                                 "eligible_regions": len(eligible),
                                 "rejected_regions": len(regions) - len(eligible),
                                 "changed_cells": sum(region["size"] for region in eligible),
                                 "eligible_quadrants": [list(q) for q in quadrants],
                                 "passed": len(eligible) >= 2 and len(eligible) < len(regions)
                                           and len(quadrants) == 4})
    two_demo_complete = all(row["first_two_demo_mismatch_indices"] or (
        row["structural_equivalence"] is not None
        and row["structural_equivalence"]["equivalent_to"] == "intended"
        and not row["query_mismatch_indices"]) for row in rows)
    features = teaching_features(train[:2], selected)
    redundant = [row["name"] for row in rows if row["structural_equivalence"] is not None]
    return {"settings": {"side_boundary_policy": selected},
            "program_sha256": source_hash(program),
            "counts": {"demos": len(train), "queries": len(test)},
            "demo_survivors_frozen_before_queries": list(survivors),
            "first_two_demo_survivors": list(first_two_survivors),
            "version_space_used_query_labels": False,
            "rivals": rows, "equal_response_groups_on_checked_inputs": list(response_groups.values()),
            "named_rival_count": len(rows),
            "independent_non_equivalent_rival_count": len(rows) - len(redundant),
            "structurally_redundant_rival_names": redundant,
            "input_hashes": hashes, "two_demo_teaching_complete": two_demo_complete,
            "first_two_size_wall_features": features, "nontrivial_30x30": nontrivial30,
            "passed": not any(row["status"] == "teaching_gap" for row in rows)
                      and two_demo_complete and features["passed"]
                      and bool(nontrivial30) and all(row["passed"] for row in nontrivial30)}


def source_binding(root: Path) -> dict:
    base = root / f"generators/{TASK_ID}"
    paths = [base / "generator.py", base / "tests/test_native_wall_audit.py"]
    paths += [path for path in (base / "workspace/parametric").iterdir()
              if path.is_file() and path.suffix in (".py", ".json", ".rkt")]
    paths += [root / "src/arcpuzzles/parametric_worker.py",
              root / "shared/runtime/puzzle_generators/rule_wrap.py",
              root / "shared/tools/comment_solutions.py",
              root / "shared/runtime/arc_repl/parser.py"]
    files = []
    for path in sorted(set(paths)):
        if path.is_symlink() or not path.is_file():
            raise ValueError("Source binding requires regular current files: " + str(path))
        files.append({"path": path.relative_to(root).as_posix(),
                      "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    return {"task_id": TASK_ID, "files": files,
            "canonical_program_sha256": source_hash(canonical_program("canvas_edges", root=root))}


def write_audit(out: Path | str) -> dict:
    root = library_root()
    destination = Path(out).resolve()
    if destination.exists():
        raise FileExistsError("Audit output must be new: " + str(destination))
    binding = source_binding(root)
    native = _load_adjacent("native_family")
    episodes, checks = [], []
    with CachedEvaluator(root) as evaluator:
        for seed, demos in ((0, 2), (17, 2), (101, 6)):
            setting_checks = []
            for policy in POLICIES:
                episode = native.generate(seed, {"side_boundary_policy": policy}, demos=demos, queries=4)
                checked = audit_episode(episode, policy, evaluator, root=root)
                checked["seed"] = seed
                episodes.append({"seed": seed, "settings": {"side_boundary_policy": policy}, **episode})
                checks.append(checked)
                setting_checks.append(checked)
            if setting_checks[0]["input_hashes"] != setting_checks[1]["input_hashes"]:
                raise ValueError("Same seed/counts must yield identical input geometry across policies")
        evidence = evaluator.evidence()
        programs = dict(evaluator.programs)
        inputs = dict(evaluator.inputs)
    if source_binding(root) != binding:
        raise ValueError("Audited source drifted during evaluation")
    destination.mkdir(parents=True)
    (destination / "programs").mkdir()
    program_rows = []
    for program, sha in sorted(programs.items(), key=lambda item: item[1]):
        relative = "programs/" + sha + ".rkt"
        (destination / relative).write_text(program, encoding="utf-8")
        program_rows.append({"path": relative, "sha256": sha})
    geometry = {key: {policy: facts(grid, policy) for policy in POLICIES}
                for key, grid in inputs.items()}
    for name, value in (("episodes.json", episodes), ("inputs.json", inputs),
                        ("independent-geometry.json", geometry),
                        ("evaluations.json", evidence), ("checks.json", checks)):
        (destination / name).write_bytes(raw(value))
    result = {"schema": "arcpuzzles-wall-teaching-audit-v1", "task_id": TASK_ID,
              "status": "passed" if all(row["passed"] for row in checks) else "teaching_gap",
              "approved": False, "source_binding": binding, "racket": evidence["racket"],
              "seeds": [0, 17, 101], "jobs": len(checks), "settings": list(POLICIES),
              "demonstrations": sum(row["counts"]["demos"] for row in checks),
              "queries": sum(row["counts"]["queries"] for row in checks),
              "actual_evaluations": evidence["actual_evaluations"],
              "cache_hits": evidence["cache_hits"], "unique_programs": len(program_rows),
              "unique_inputs": evidence["unique_inputs"],
              "programs": program_rows, "query_labels_used_for_hypothesis_selection": False,
              "named_rivals_per_setting": len(RIVALS),
              "independent_non_equivalent_rivals_per_setting": len(RIVALS) - 1,
              "redundant_rivals": {policy: {name: structural_equivalence(policy, name)
                                            for name in RIVALS if structural_equivalence(policy, name)}
                                    for policy in POLICIES},
              "same_geometry_across_settings": True,
              "two_demo_teaching_complete": all(row["two_demo_teaching_complete"] for row in checks),
              "limits": "Finite named rivals and three seeds only; protected final-label parity does not establish universal rule uniqueness, all-seed coverage, owner acceptance, or training admission."}
    result["artifacts"] = [{"path": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                           for path in sorted(destination.iterdir()) if path.is_file()]
    (destination / "report.json").write_bytes(raw(result))
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    result = write_audit(args.out)
    print(json.dumps({key: result[key] for key in (
        "status", "jobs", "demonstrations", "queries", "actual_evaluations", "cache_hits",
        "unique_programs", "unique_inputs", "two_demo_teaching_complete")}, sort_keys=True))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
