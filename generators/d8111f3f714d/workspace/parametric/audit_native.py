#!/usr/bin/env python3
"""Bounded, demonstration-only rival audit for native branch-direction lessons.

The geometry and candidate renderer do not use either generator's analysis or
claim labels. Exact intended programs come from the retained prototype. Every
reported label comparison is backed by protected Racket execution; a cache
deduplicates only identical program bytes and identical input bytes.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Callable


TASK_ID = "d8111f3f714d"
HERE = Path(__file__).resolve().parent
RIVALS = (
    "opposite_direction", "trunk_only", "branches_only", "negative_side_only",
    "positive_side_only", "vertical_only", "horizontal_only", "full_axis_trunk",
    "one_step_branches", "nearest_canvas_edge", "centered_trunk",
    "first_branch_only", "first_five_only",
)
SETTINGS = ("toward_trunk", "away_to_edge")


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode()


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def write_json(path: Path, value: Any) -> None:
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")


def _setting(settings=None) -> str:
    if settings is None:
        return SETTINGS[0]
    if type(settings) is not dict or set(settings) - {"branch_direction"}:
        raise ValueError("settings must contain only branch_direction")
    value = settings.get("branch_direction", SETTINGS[0])
    if type(value) is not str or value not in SETTINGS:
        raise ValueError("unknown branch_direction")
    return value


def _grid(value, palette) -> list[list[int]]:
    if type(value) is not list or not 10 <= len(value) <= 30:
        raise ValueError("grid height must be 10..30")
    if any(type(row) is not list for row in value):
        raise ValueError("grid rows must be lists")
    width = len(value[0])
    if not 10 <= width <= 30 or any(len(row) != width for row in value):
        raise ValueError("grid must be rectangular with width 10..30")
    if any(type(cell) is not int or cell not in palette for row in value for cell in row):
        raise ValueError("grid contains a non-exact integer or invalid color")
    return deepcopy(value)


def analyze_scene(grid) -> dict[str, Any]:
    """Derive the native grammar independently of production/native helpers."""
    value = _grid(grid, {0, 2})
    reds = [(r, c) for r, row in enumerate(value) for c, color in enumerate(row) if color == 2]
    if not 3 <= len(reds) <= 29:
        raise ValueError("need two endpoints and 1..27 branches")
    pairs = [(a, b) for i, a in enumerate(reds) for b in reds[i + 1:]
             if a[0] == b[0] or a[1] == b[1]]
    if len(pairs) != 1:
        raise ValueError("need exactly one aligned red pair")
    first, second = pairs[0]
    vertical = first[1] == second[1]
    major, minor = (0, 1) if vertical else (1, 0)
    line = first[minor]
    start, end = sorted([first[major], second[major]])
    branches = [p for p in reds if p not in (first, second)]
    if any(not start < p[major] < end or abs(p[minor] - line) < 2 for p in branches):
        raise ValueError("branches must lie inside the span and two cells off the line")
    if len({p[major] for p in branches}) != len(branches) or len({p[minor] for p in branches}) != len(branches):
        raise ValueError("branches must have unique major and minor coordinates")
    sides = {"negative": sum(p[minor] < line for p in branches),
             "positive": sum(p[minor] > line for p in branches)}
    if len(branches) > 1 and not all(sides.values()):
        raise ValueError("multi-branch scenes must cover both sides")
    return {"shape": [len(value), len(value[0])], "reds": [list(p) for p in reds],
            "trunk": [list(first), list(second)], "orientation": "v" if vertical else "h",
            "trunk_line": line, "trunk_span": [start, end],
            "branches": [list(p) for p in branches], "side_counts": sides}


def independent_apply(grid, settings=None, rival="intended") -> list[list[int]]:
    """Render the intended rule or one explicit finite rival from input facts."""
    direction = _setting(settings)
    if rival not in ("intended", *RIVALS):
        raise ValueError("unknown rival")
    facts = analyze_scene(grid)
    output = deepcopy(grid)
    vertical = facts["orientation"] == "v"
    if (rival == "vertical_only" and not vertical) or (rival == "horizontal_only" and vertical):
        return output
    major, minor = (0, 1) if vertical else (1, 0)
    major_limit, minor_limit = facts["shape"][major], facts["shape"][minor]
    line = minor_limit // 2 if rival == "centered_trunk" else facts["trunk_line"]
    if rival == "opposite_direction":
        direction = SETTINGS[1 - SETTINGS.index(direction)]

    def put(a, b):
        r, c = (a, b) if vertical else (b, a)
        if 0 <= r < len(grid) and 0 <= c < len(grid[0]) and grid[r][c] == 0:
            output[r][c] = 3

    start, end = facts["trunk_span"]
    if rival != "branches_only":
        for a in (range(major_limit) if rival == "full_axis_trunk" else range(start + 1, end)):
            put(a, line)
    branches = facts["branches"]
    if rival == "first_branch_only":
        branches = branches[:1]
    elif rival == "first_five_only":
        branches = branches[:5]
    for p in ([] if rival == "trunk_only" else branches):
        a, b = p[major], p[minor]
        if rival == "negative_side_only" and b > line:
            continue
        if rival == "positive_side_only" and b < line:
            continue
        if rival == "nearest_canvas_edge":
            columns = range(b) if b <= minor_limit - 1 - b else range(b + 1, minor_limit)
        elif rival == "one_step_branches":
            step = (1 if b < line else -1) * (1 if direction == "toward_trunk" else -1)
            columns = (b + step,)
        elif direction == "toward_trunk":
            columns = range(min(b, line) + 1, max(b, line))
        else:
            columns = range(b) if b < line else range(b + 1, minor_limit)
        for b2 in columns:
            put(a, b2)
    return output


@lru_cache(maxsize=None)
def _load(name):
    path = HERE / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_branch_audit_{name}", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rival_program(settings, name: str) -> str:
    """Materialize a total candidate over the declared unique-trunk grammar."""
    direction = _setting(settings)
    if name == "intended":
        return _load("prototype").program_for(direction)
    if name not in RIVALS:
        raise ValueError("unknown rival")
    if name == "opposite_direction":
        return _load("prototype").program_for(SETTINGS[1 - SETTINGS.index(direction)])
    active = "vertical" if name == "vertical_only" else "(not vertical)" if name == "horizontal_only" else "#t"
    line = "(quotient minor-limit 2)" if name == "centered_trunk" else "actual-line"
    trunk_range = "(range 0 major-limit)" if name == "full_axis_trunk" else "(range (+ start 1) end)"
    trunk = "(void)" if name == "branches_only" else f"(for ((a {trunk_range})) (put a line))"
    branch_list = "'()" if name == "trunk_only" else "branches"
    if name in {"first_branch_only", "first_five_only"}:
        limit = 1 if name == "first_branch_only" else 5
        branch_list = f"(take branches (min {limit} (length branches)))"
    side = "(< b line)" if name == "negative_side_only" else "(> b line)" if name == "positive_side_only" else "#t"
    if name == "nearest_canvas_edge":
        columns = "(if (<= b (- minor-limit 1 b)) (range 0 b) (range (+ b 1) minor-limit))"
    elif name == "one_step_branches":
        sign = "1" if direction == "toward_trunk" else "-1"
        columns = f"(list (+ b (* {sign} (if (< b line) 1 -1))))"
    elif direction == "toward_trunk":
        columns = "(range (+ (min b line) 1) (max b line))"
    else:
        columns = "(if (< b line) (range 0 b) (range (+ b 1) minor-limit))"
    # No unused branch direction is embedded for trunk-only candidates.
    if name == "trunk_only":
        columns = "'()"
    return f"""(rule! (lambda (g)
  (let* ((h (rows g)) (w (cols g))
         (reds (for*/list ((r (range h)) (c (range w)) #:when (= (at g r c) 2)) (list r c)))
         (pairs (for*/list ((i (range (length reds))) (j (range (+ i 1) (length reds)))
                           #:when (let ((a (list-ref reds i)) (b (list-ref reds j)))
                                    (or (= (first a) (first b)) (= (second a) (second b)))))
                  (list (list-ref reds i) (list-ref reds j))))
         (pair (first pairs)) (t1 (first pair)) (t2 (second pair))
         (vertical (= (second t1) (second t2)))
         (major-limit (if vertical h w)) (minor-limit (if vertical w h))
         (actual-line (if vertical (second t1) (first t1)))
         (line {line})
         (start (min (if vertical (first t1) (second t1)) (if vertical (first t2) (second t2))))
         (end (max (if vertical (first t1) (second t1)) (if vertical (first t2) (second t2))))
         (branches (filter (lambda (p) (and (not (equal? p t1)) (not (equal? p t2)))) reds))
         (painted (make-hash)))
    (let ((put (lambda (a b)
                 (let ((r (if vertical a b)) (c (if vertical b a)))
                   (when (and (<= 0 r) (< r h) (<= 0 c) (< c w) (= (at g r c) 0))
                     (hash-set! painted (list r c) 3))))))
      (when {active}
        {trunk}
        (for ((red {branch_list}))
          (let ((a (if vertical (first red) (second red)))
                (b (if vertical (second red) (first red))))
            (when {side}
              (for ((b2 {columns})) (put a b2)))))))
    (cellmap g (r c v) (hash-ref painted (list r c) v)))))"""


def rival_programs(settings=None) -> dict[str, str]:
    return {name: rival_program(settings, name) for name in RIVALS}


class ProtectedExecutor:
    """One protected application per cache miss, retaining exact inputs/programs."""
    def __init__(self, bridge):
        self.bridge = bridge
        self.cache = {}
        self.cache_hits = 0
        self.evaluations = []
        self.inputs = {}
        self.programs = {}

    def apply(self, program, grid):
        from puzzle_generators.rule_wrap import strip_rule_wrapper
        value = _grid(grid, {0, 2})
        program_hash, input_hash = sha(program.encode()), sha(json_bytes(value))
        key = (program_hash, input_hash)
        self.programs[program_hash] = program
        self.inputs[input_hash] = value
        if key in self.cache:
            self.cache_hits += 1
            return deepcopy(self.cache[key])
        literal = "(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in value) + ")"
        body = strip_rule_wrapper(program)
        result = _grid(self.bridge.eval_text(f"({body} '{literal})"), {0, 2, 3})
        if (len(result), len(result[0])) != (len(value), len(value[0])):
            raise ValueError("candidate output changed grid shape")
        self.cache[key] = result
        self.evaluations.append({"index": len(self.evaluations), "program_sha256": program_hash,
                                 "input_sha256": input_hash, "output_sha256": sha(json_bytes(result)),
                                 "output": result})
        return deepcopy(result)


def fit_demonstrations(demos, candidates, evaluate: Callable) -> dict[str, Any]:
    """Freeze candidate survivors without receiving or inspecting any queries."""
    disagreements = {}
    for name, program in candidates.items():
        disagreements[name] = [i for i, pair in enumerate(demos)
                               if evaluate(program, pair["input"]) != pair["output"]]
    return {"survivors": [name for name, bad in disagreements.items() if not bad],
            "demo_disagreements": disagreements, "query_accessed": False,
            "demonstrations_sha256": sha(json_bytes(demos))}


def audit_episode(episode, settings, executor) -> dict[str, Any]:
    direction = _setting(settings)
    intended = rival_program(settings, "intended")
    if episode.get("program_solution") != intended:
        raise ValueError("episode does not carry the exact intended program")
    demos = deepcopy(episode["train"])
    for pair in demos:
        reference = executor.apply(intended, pair["input"])
        if reference != pair["output"] or reference != independent_apply(pair["input"], settings):
            raise ValueError("intended demo label mismatch")
    candidates = rival_programs(settings)

    def checked_candidate(program, grid):
        result = executor.apply(program, grid)
        names = [name for name, value in candidates.items() if value == program]
        for name in names:
            if result != independent_apply(grid, settings, name):
                raise ValueError("candidate Python/Racket mismatch: " + name)
        return result

    certificate = fit_demonstrations(demos, candidates, checked_candidate)
    frozen = json_bytes(certificate)
    # The query split is first accessed only after candidate fitting is complete.
    queries = deepcopy(episode["test"])
    query_checks = []
    survivor_disagreements = {name: [] for name in certificate["survivors"]}
    for i, pair in enumerate(queries):
        grid = pair["input"]
        reference = executor.apply(intended, grid)
        if reference != pair["output"] or reference != independent_apply(grid, settings):
            raise ValueError("intended query label mismatch")
        opposite = executor.apply(candidates["opposite_direction"], grid)
        if opposite != independent_apply(grid, settings, "opposite_direction"):
            raise ValueError("opposite-setting query parity mismatch")
        for name in certificate["survivors"]:
            prediction = checked_candidate(candidates[name], grid)
            if prediction != reference:
                survivor_disagreements[name].append(i)
        painted = [(r, c) for r, row in enumerate(reference) for c, color in enumerate(row) if color == 3]
        query_checks.append({"index": i, "shape": [len(grid), len(grid[0])],
                             "input_sha256": sha(json_bytes(grid)), "painted_cells": len(painted),
                             "painted_rows": len({r for r, _ in painted}),
                             "painted_columns": len({c for _, c in painted}),
                             "painted_quadrants": sorted({int(r >= len(grid) / 2) * 2 + int(c >= len(grid[0]) / 2) for r, c in painted}),
                             "settings_disagree": opposite != reference})
    if json_bytes(certificate) != frozen:
        raise ValueError("query processing mutated the frozen demo certificate")
    first_two_refute = {name: any(i < 2 for i in bad) for name, bad in certificate["demo_disagreements"].items()}
    failures = []
    if not all(first_two_refute.values()):
        failures.append("first two demos leave declared non-equivalent rivals unrefuted")
    if any(survivor_disagreements.values()):
        failures.append("a demo-surviving rival disagrees on a query")
    if not all(row["settings_disagree"] for row in query_checks):
        failures.append("a query does not distinguish the setting")
    return {"setting": direction, "demonstrations": len(demos), "queries": len(queries),
            "program_sha256": sha(intended.encode()), "demo_certificate": certificate,
            "frozen_demo_certificate_sha256": sha(frozen), "survivors_frozen_before_queries": True,
            "first_two_refute": first_two_refute, "survivor_query_disagreements": survivor_disagreements,
            "query_checks": query_checks, "failures": failures}


def run(out: Path, seeds=(0, 17)) -> dict[str, Any]:
    from arc_repl.racket_bridge import RacketBridge
    from reviewer_support import find_root, canonical_path
    root = find_root(__file__)
    if out.exists():
        raise FileExistsError(out)
    out.mkdir(parents=True)
    native = _load("native_family")
    source_paths = [Path(__file__), HERE / "native_family.py", HERE / "adapter.py", HERE / "prototype.py",
                    HERE.parent.parent / "generator.py", canonical_path(root),
                    root / "shared/runtime/arc_repl/racket_bridge.py",
                    root / "shared/runtime/puzzle_generators/rule_wrap.py",
                    root / "shared/runtime/reviewer_support.py",
                    HERE.parent.parent / "tests/test_native_branch_audit.py"]
    source_hashes = {p.relative_to(root).as_posix(): sha(p.read_bytes()) for p in source_paths}
    episodes, jobs, geometry = [], [], []
    with RacketBridge(timeout=30, max_calls_before_restart=512) as bridge:
        executor = ProtectedExecutor(bridge)
        runtime = bridge.runtime_identity
        try:
            for seed in seeds:
                for direction in SETTINGS:
                    settings = {"branch_direction": direction}
                    episode = native.generate(seed, settings, demos=2, queries=4)
                    job = audit_episode(episode, settings, executor)
                    job["seed"] = seed
                    jobs.append(job)
                    episodes.append({"seed": seed, "settings": settings, "episode": episode})
                    geometry.append({"seed": seed, "settings": settings,
                                     "train": [analyze_scene(p["input"]) for p in episode["train"]],
                                     "test": [analyze_scene(p["input"]) for p in episode["test"]]})
        except Exception as exc:
            write_json(out / "failure.json", {"error": type(exc).__name__, "detail": str(exc),
                                              "source_sha256": source_hashes, "runtime": runtime,
                                              "completed_jobs": jobs, "evaluations": executor.evaluations})
            raise
    if source_hashes != {p.relative_to(root).as_posix(): sha(p.read_bytes()) for p in source_paths}:
        raise ValueError("audit source changed while it was executing")
    (out / "programs").mkdir()
    for digest, program in executor.programs.items():
        (out / "programs" / (digest + ".rkt")).write_text(program, encoding="utf-8")
    artifacts = {"episodes.json": episodes, "independent-geometry.json": geometry,
                 "inputs.json": executor.inputs, "evaluations.json": executor.evaluations}
    for name, value in artifacts.items():
        write_json(out / name, value)
    failures = [dict(seed=job["seed"], setting=job["setting"], reason=reason)
                for job in jobs for reason in job["failures"]]
    report = {"schema": "arcpuzzles-native-branch-teaching-audit-v1", "task_id": TASK_ID,
              "status": "failed" if failures else "passed", "jobs": jobs, "failures": failures,
              "source_sha256": source_hashes, "racket": runtime,
              "racket_evaluations": len(executor.evaluations), "exact_cache_hits": executor.cache_hits,
              "distinct_programs": len(executor.programs), "distinct_inputs": len(executor.inputs),
              "named_non_equivalent_rivals_per_setting": len(RIVALS),
              "artifact_sha256": {name: sha((out / name).read_bytes()) for name in artifacts},
              "program_sha256": {f"programs/{digest}.rkt": digest for digest in sorted(executor.programs)},
              "owner_acceptance": "not_performed", "training_admitted": False,
              "limits": ["Two seeds, two settings and a finite named rival set; no universal uniqueness or learning-benefit claim.",
                         "Rivals are fitted using demonstrations only. Query labels never select the survivors.",
                         "Only intended/opposite-setting programs and any demo survivors are applied to queries; refuted rivals need no query evaluation.",
                         "Cached results reuse only exact program and input bytes; each reported evaluation is an actual protected application.",
                         "The native grammar extends the unchanged production size and branch-count limits; this does not approve or modify production."]}
    write_json(out / "report.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.out)
    print(json.dumps({"status": report["status"], "jobs": len(report["jobs"]),
                      "racket_evaluations": report["racket_evaluations"],
                      "rivals_per_setting": report["named_non_equivalent_rivals_per_setting"],
                      "failures": report["failures"]}, sort_keys=True))
    return int(report["status"] != "passed")


if __name__ == "__main__":
    raise SystemExit(main())
