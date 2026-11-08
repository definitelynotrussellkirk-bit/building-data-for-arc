#!/usr/bin/env python3
"""Independent bounded teaching audit for marked-tile turns and rigid settling.

Only the two required demonstrations determine rival survival. Query answers
never teach subsequent queries. Exact protected Racket programs are checked
against an independently written coordinate-set oracle. Execution errors are
audit errors, never refutations; finite success does not establish uniqueness.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve()
HOME = HERE.parent
ROOT = next(parent for parent in HERE.parents if (parent / "shared/runtime").is_dir())
TASK_ID = "1ee7274bdbb0"
CANONICAL_SHA256 = "a23915e769b96d7ca844d36d4b8408b311d672bca58166fad83378fa83cf8660"
SETTINGS = tuple({"turn": turn, "post": post}
                 for turn in ("cw", "ccw") for post in ("none", "settle_down"))
BASE_RIVALS = (
    "copy_all", "rotate_all", "rotate_unmarked", "center_only", "exactly_one",
    "single_center", "skip_two", "skip_three", "alternating_from_first",
    "connected_only", "disconnected_only", "marked_180", "marked_flip_h",
    "marked_flip_v", "motif_bbox_turn", "marker_pivot_turn",
    "marker_cells_as_answer", "one_cell_per_tile", "marker_turn_count",
)
SETTLE_RIVALS = (
    "component_settle", "pixel_column_pack", "wrong_order", "settle_marked_only",
    "settle_unmarked_only", "drop_from_motif_and_markers",
)


def _digest(body):
    return hashlib.sha256(body).hexdigest()


def _json_bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _hash(value):
    return _digest(_json_bytes(value))


def _write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _grid(value):
    """Typed rectangular grid validation, also used for arbitrary rival outputs."""
    if (type(value) is not list or not 3 <= len(value) <= 30
            or type(value[0]) is not list or not 3 <= len(value[0]) <= 30
            or any(type(row) is not list or len(row) != len(value[0])
                   or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
                   for row in value)):
        raise ValueError("audit grids require rectangular 3..30 exact integer colors 0..9")
    return deepcopy(value)


def _parse(value):
    """Derive uniform square tiles from full separators, independently of native code."""
    grid = _grid(value)
    if any(cell not in (0, 2, 3, 9) for row in grid for cell in row):
        raise ValueError("input colors must be exactly 0, 2, 3, or 9")
    height, width = len(grid), len(grid[0])
    row_lines = [r for r in range(height) if all(cell == 9 for cell in grid[r])]
    col_lines = [c for c in range(width) if all(grid[r][c] == 9 for r in range(height))]
    if any(line in (0, height - 1) for line in row_lines) or any(line in (0, width - 1) for line in col_lines):
        raise ValueError("outer separator frames are forbidden")
    if any((grid[r][c] == 9) != (r in row_lines or c in col_lines)
           for r in range(height) for c in range(width)):
        raise ValueError("every 9 must belong to a full separator")
    row_edges, col_edges = [-1, *row_lines, height], [-1, *col_lines, width]
    heights = [b - a - 1 for a, b in zip(row_edges, row_edges[1:])]
    widths = [b - a - 1 for a, b in zip(col_edges, col_edges[1:])]
    size = heights[0]
    if not 3 <= size <= 30 or any(n != size for n in heights + widths):
        raise ValueError("separators must delimit equal square tiles of side 3..30")
    tiles = []
    for row0 in (edge + 1 for edge in row_edges[:-1]):
        for col0 in (edge + 1 for edge in col_edges[:-1]):
            motif = {(r, c) for r in range(size) for c in range(size) if grid[row0 + r][col0 + c] == 2}
            markers = {(r, c) for r in range(size) for c in range(size) if grid[row0 + r][col0 + c] == 3}
            tiles.append((row0, col0, motif, markers))
    return grid, size, tiles


def _settings(settings):
    if (type(settings) is not dict or set(settings) != {"turn", "post"}
            or type(settings["turn"]) is not str or settings["turn"] not in ("cw", "ccw")
            or type(settings["post"]) is not str or settings["post"] not in ("none", "settle_down")):
        raise ValueError("settings must be exactly turn=cw|ccw, post=none|settle_down")
    return settings["turn"], settings["post"]


def _native_name(settings):
    turn, post = _settings(settings)
    return "native_" + turn + "_" + post


def rivals(settings):
    _, post = _settings(settings)
    native = tuple(_native_name(other) for other in SETTINGS if other != settings)
    return BASE_RIVALS + native + (SETTLE_RIVALS if post == "settle_down" else ())


def _choice(settings, name=None):
    turn, post = _settings(settings)
    if name is not None and name not in rivals(settings):
        raise ValueError(f"undeclared rival: {name!r}")
    for other in SETTINGS:
        if name == _native_name(other):
            return _settings(other)
    return turn, post


def _components(points):
    unseen, components = set(points), []
    while unseen:
        start = min(unseen)
        component, frontier = {start}, [start]
        unseen.remove(start)
        while frontier:
            row, col = frontier.pop()
            for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    component.add(neighbor)
                    frontier.append(neighbor)
        components.append(component)
    return components


def _turn(points, size, direction):
    if direction == "cw":
        return {(c, size - 1 - r) for r, c in points}
    return {(size - 1 - c, r) for r, c in points}


def _settle(points, size):
    if not points:
        return set()
    drop = size - 1 - max(r for r, _ in points)
    return {(r + drop, c) for r, c in points}


def _python_apply(value, settings, name=None):
    turn, post = _choice(settings, name)
    grid, size, tiles = _parse(value)
    first_marked = bool(tiles[0][3])
    output = [[9 if cell == 9 else 0 for cell in row] for row in grid]
    for index, (row0, col0, raw, markers) in enumerate(tiles):
        marked, count = bool(markers), len(markers)
        center_marked = (size // 2, size // 2) in markers
        active = marked
        if name == "copy_all":
            active = False
        elif name == "rotate_all":
            active = True
        elif name == "rotate_unmarked":
            active = not marked
        elif name == "center_only":
            active = center_marked
        elif name == "exactly_one":
            active = count == 1
        elif name == "single_center":
            active = marked and (count > 1 or center_marked)
        elif name == "skip_two":
            active = marked and count != 2
        elif name == "skip_three":
            active = marked and count != 3
        elif name == "alternating_from_first":
            active = first_marked != bool(index % 2)
        elif name == "connected_only":
            active = len(_components(raw)) == 1
        elif name == "disconnected_only":
            active = len(_components(raw)) > 1

        if name == "wrong_order":
            fallen = _settle(raw, size)
            points = _turn(fallen, size, turn) if marked else fallen
        elif name == "marker_cells_as_answer":
            points = set(markers if marked else raw)
        elif name == "marker_turn_count":
            points = set(raw)
            for _ in range(count):
                points = _turn(points, size, turn)
        elif active and name == "marked_180":
            points = {(size - 1 - r, size - 1 - c) for r, c in raw}
        elif active and name == "marked_flip_h":
            points = {(r, size - 1 - c) for r, c in raw}
        elif active and name == "marked_flip_v":
            points = {(size - 1 - r, c) for r, c in raw}
        elif active and name == "motif_bbox_turn":
            points = set()
            if raw:
                lo_r, hi_r = min(r for r, _ in raw), max(r for r, _ in raw)
                lo_c, hi_c = min(c for _, c in raw), max(c for _, c in raw)
                if turn == "cw":
                    points = {(lo_r + c - lo_c, lo_c + hi_r - r) for r, c in raw}
                else:
                    points = {(lo_r + hi_c - c, lo_c + r - lo_r) for r, c in raw}
        elif active and name == "marker_pivot_turn":
            pr, pc = min(markers)
            if turn == "cw":
                points = {(pr + c - pc, pc + pr - r) for r, c in raw}
            else:
                points = {(pr + pc - c, pc + r - pr) for r, c in raw}
        else:
            points = _turn(raw, size, turn) if active else set(raw)

        # Bbox/pivot rivals may leave the tile; clipping precedes every post step.
        points = {(r, c) for r, c in points if 0 <= r < size and 0 <= c < size}
        if name == "one_cell_per_tile" and points:
            points = {min(points)}
        if post == "settle_down" and name != "wrong_order":
            if name == "component_settle":
                points = set().union(*(_settle(part, size) for part in _components(points)))
            elif name == "pixel_column_pack":
                counts = {c: sum(pc == c for _, pc in points) for c in range(size)}
                points = {(r, c) for c, n in counts.items() for r in range(size - n, size)}
            elif name == "drop_from_motif_and_markers":
                union = points | markers
                drop = size - 1 - max(r for r, _ in union) if union else 0
                points = {(r + drop, c) for r, c in points}
            elif not ((name == "settle_marked_only" and not marked)
                      or (name == "settle_unmarked_only" and marked)):
                points = _settle(points, size)
        for row, col in points:
            output[row0 + row][col0 + col] = 8
    return output


def python_intended(grid, settings):
    """Independent intended labels; never calls native_family.transform."""
    return _python_apply(grid, settings)


def python_rival(grid, settings, name):
    return _python_apply(grid, settings, name)


def rival_program(settings, name):
    """Return the exact declared Racket rival, retaining the selected post step."""
    turn, post = _choice(settings, name)
    if name.startswith("native_"):
        # These are the actual alternative family programs, not lookalike programs.
        return _load_family().program({"turn": turn, "post": post})
    turn_point = "(list (second p) (- s 1 (first p)))" if turn == "cw" else "(list (- s 1 (second p)) (first p))"
    active = {
        "copy_all": "#f", "rotate_all": "#t", "rotate_unmarked": "(not marked)",
        "center_only": "(member (list (quotient s 2) (quotient s 2)) marks)",
        "exactly_one": "(= (length marks) 1)",
        "single_center": "(and marked (or (> (length marks) 1) (member (list (quotient s 2) (quotient s 2)) marks)))",
        "skip_two": "(and marked (not (= (length marks) 2)))",
        "skip_three": "(and marked (not (= (length marks) 3)))",
        "alternating_from_first": "(if (even? tile-index) first-marked (not first-marked))",
        "connected_only": "(= (length (parts ps)) 1)",
        "disconnected_only": "(> (length (parts ps)) 1)",
    }.get(name, "marked")
    turned = "(turn-points ps)"
    if name in ("marked_180", "marked_flip_h", "marked_flip_v"):
        point = {
            "marked_180": "(list (- s 1 (first p)) (- s 1 (second p)))",
            "marked_flip_h": "(list (first p) (- s 1 (second p)))",
            "marked_flip_v": "(list (- s 1 (first p)) (second p))",
        }[name]
        turned = f"(map (lambda (p) {point}) ps)"
    elif name == "motif_bbox_turn":
        point = ("(list (+ lo-r (- (second p) lo-c)) (+ lo-c (- hi-r (first p))))"
                 if turn == "cw" else
                 "(list (+ lo-r (- hi-c (second p))) (+ lo-c (- (first p) lo-r)))")
        turned = f"""(if (null? ps) '()
          (let ([lo-r (apply min (map first ps))] [hi-r (apply max (map first ps))]
                [lo-c (apply min (map second ps))] [hi-c (apply max (map second ps))])
            (map (lambda (p) {point}) ps)))"""
    elif name == "marker_pivot_turn":
        point = ("(list (+ pr (- (second p) pc)) (+ pc (- pr (first p))))"
                 if turn == "cw" else
                 "(list (+ pr (- pc (second p))) (+ pc (- (first p) pr)))")
        turned = f"""(let ([pr (first (first marks))] [pc (second (first marks))])
          (map (lambda (p) {point}) ps))"""
    moved = f"(if active {turned} ps)"
    if name == "marker_cells_as_answer":
        moved = "(if marked marks ps)"
    elif name == "marker_turn_count":
        moved = "(let loop ([answer ps] [n (length marks)]) (if (= n 0) answer (loop (turn-points answer) (- n 1))))"
    elif name == "wrong_order":
        moved = "(if marked (turn-points (settle ps)) (settle ps))"
    stage_a = "inside"
    if name == "one_cell_per_tile":
        stage_a = "(if (null? inside) '() (list (first (sort inside point-before?))))"
    finished = "stage-a"
    if post == "settle_down" and name != "wrong_order":
        finished = "(settle stage-a)"
        if name == "component_settle":
            finished = "(remove-duplicates (append* (map settle (parts stage-a))))"
        elif name == "pixel_column_pack":
            finished = """(append* (for/list ([c (in-range s)])
              (let ([n (length (filter (lambda (p) (= (second p) c)) stage-a))])
                (for/list ([r (in-range (- s n) s)]) (list r c)))))"""
        elif name == "settle_marked_only":
            finished = "(if marked (settle stage-a) stage-a)"
        elif name == "settle_unmarked_only":
            finished = "(if marked stage-a (settle stage-a))"
        elif name == "drop_from_motif_and_markers":
            finished = """(let* ([all-points (append stage-a marks)]
              [drop (if (null? all-points) 0 (- s 1 (apply max (map first all-points))))])
              (map (lambda (p) (list (+ (first p) drop) (second p))) stage-a))"""
    parts = ""
    if name in ("connected_only", "disconnected_only", "component_settle"):
        parts = """[parts (lambda (ps)
          (let loop ([left ps] [out '()])
            (if (null? left) out
                (let flood ([seen (list (first left))] [front (list (first left))])
                  (if (null? front)
                      (loop (filter (lambda (p) (not (member p seen))) left) (cons seen out))
                      (let* ([a (first front)]
                             [near (filter (lambda (p)
                               (= 1 (+ (abs (- (first p) (first a)))
                                       (abs (- (second p) (second a)))))) left)]
                             [fresh (filter (lambda (p) (not (member p seen))) near)])
                        (flood (append fresh seen) (append (rest front) fresh))))))))]"""
    return f"""(rule! (lambda (g)
  (let* ([h (rows g)] [w (cols g)]
         [s (or (for/first ([c (in-range w)] #:when (= (cell-at g 0 c) 9)) c) w)]
         [turn-points (lambda (ps) (map (lambda (p) {turn_point}) ps))]
         [clip (lambda (ps) (remove-duplicates (filter (lambda (p)
           (and (<= 0 (first p)) (< (first p) s) (<= 0 (second p)) (< (second p) s))) ps)))]
         [settle (lambda (ps) (if (null? ps) '()
           (let ([drop (- s 1 (apply max (map first ps)))])
             (map (lambda (p) (list (+ (first p) drop) (second p))) ps))))]
         [point-before? (lambda (a b)
           (< (+ (* s (first a)) (second a)) (+ (* s (first b)) (second b))))]
         {parts}
         [first-marked (for*/or ([r (in-range s)] [c (in-range s)]) (= (cell-at g r c) 3))]
         [answers (append* (for*/list ([r0 (in-range 0 h (+ s 1))] [c0 (in-range 0 w (+ s 1))])
           (let* ([ps (for*/list ([r (in-range s)] [c (in-range s)]
                       #:when (= (cell-at g (+ r0 r) (+ c0 c)) 2)) (list r c))]
                  [marks (for*/list ([r (in-range s)] [c (in-range s)]
                          #:when (= (cell-at g (+ r0 r) (+ c0 c)) 3)) (list r c))]
                  [marked (not (null? marks))]
                  [tile-index (+ (* (quotient r0 (+ s 1)) (quotient (+ w 1) (+ s 1)))
                                 (quotient c0 (+ s 1)))]
                  [active {active}] [moved {moved}] [inside (clip moved)]
                  [stage-a {stage_a}] [finished {finished}])
             (map (lambda (p) (list (+ r0 (first p)) (+ c0 (second p)))) finished))))])
    (grid-from-fn h w (lambda (r c)
      (cond [(= (cell-at g r c) 9) 9] [(member (list r c) answers) 8] [else 0]))))))"""


class ExecutionCache:
    """Retain each exact program/input/output evaluation once, including errors."""

    def __init__(self, apply, identity, budget=512):
        self.apply = apply
        self.identity = deepcopy(identity)
        self.identity_after = None
        self.budget = budget
        self.request_count = 0
        self.execution_count = 0
        self.programs = {}
        self.inputs = {}
        self.records = {}

    def evaluate(self, program, grid):
        grid = _parse(grid)[0]
        if type(program) is not str or not program.strip():
            raise ValueError("program must be nonempty text")
        self.request_count += 1
        program_hash, input_hash = _digest(program.encode()), _hash(grid)
        key = program_hash + ":" + input_hash
        if key not in self.records:
            if self.execution_count >= self.budget:
                raise RuntimeError(f"bounded audit execution budget exceeded ({self.budget})")
            self.programs[program_hash] = program
            self.inputs[input_hash] = deepcopy(grid)
            row = {"execution_id": key, "program_sha256": program_hash, "input_sha256": input_hash}
            self.execution_count += 1
            try:
                output = _grid(self.apply(program, deepcopy(grid)))
                if (len(output), len(output[0])) != (len(grid), len(grid[0])):
                    raise ValueError("rival output changed grid dimensions")
            except Exception as error:
                row.update(status="error", error_type=type(error).__name__, error=str(error))
            else:
                row.update(status="ok", output=output, output_sha256=_hash(output))
            self.records[key] = row
        return deepcopy(self.records[key])


@contextmanager
def protected_evaluator():
    """Use the current same-checkout protected runtime and bind it before/after."""
    runtime = ROOT / "shared/runtime"
    before = list(sys.path)
    sys.path[:0] = [str(ROOT / "src"), str(runtime)]
    try:
        from arcpuzzles.parametric_worker import _local_imports, _real_evaluator
        with _local_imports(runtime, HOME):
            apply, identity, bridge = _real_evaluator(runtime)
            executor = ExecutionCache(apply, identity)
            try:
                yield executor
            finally:
                try:
                    current = bridge.runtime_identity
                    executor.identity_after = {key: current[key] for key in identity}
                finally:
                    bridge.close()
    finally:
        sys.path[:] = before


def assess_program(executor, name, program, train, queries, oracle=None):
    """Stop on first demo refutation; assess every query of a surviving rule."""
    if not train or not queries:
        raise ValueError("a lesson needs demonstrations and independent queries")
    result = {
        "name": name, "program_sha256": _digest(program.encode()), "status": "running",
        "demo_indices_checked": [], "query_indices_checked": [],
        "demo_executions": [], "query_executions": [], "refuting_demo_index": None,
        "disagreeing_query_indices": [], "first_teaching_hole": None,
    }
    for phase, pairs in (("demo", train), ("query", queries)):
        for index, pair in enumerate(pairs):
            intended = _grid(pair["output"])
            row = executor.evaluate(program, pair["input"])
            result[f"{phase}_indices_checked"].append(index)
            result[f"{phase}_executions"].append(row["execution_id"])
            if row["status"] != "ok":
                result.update(status="execution_error", error=row)
                return result
            independent = oracle(pair["input"]) if oracle is not None else None
            if oracle is not None and row["output"] != independent:
                result.update(status="oracle_mismatch", error={
                    "phase": phase, "index": index, "racket_output": row["output"],
                    "independent_output": independent,
                })
                return result
            if row["output"] != intended:
                if phase == "demo":
                    result.update(status="demo_refuted", refuting_demo_index=index)
                    return result
                result["disagreeing_query_indices"].append(index)
                if result["first_teaching_hole"] is None:
                    result["first_teaching_hole"] = {
                        "train": deepcopy(train), "test": [deepcopy(pair)], "query_index": index,
                        "rival_name": name, "rival_program": program, "rival_output": row["output"],
                        "minimization": "First disagreeing query with the required two demos; cells not minimized.",
                    }
    result["status"] = "teaching_hole" if result["disagreeing_query_indices"] else "query_agreeing_survivor"
    return result


def assess_rival(executor, settings, name, train, queries):
    return assess_program(executor, name, rival_program(settings, name), train, queries,
                          oracle=lambda grid: python_rival(grid, settings, name))


def _load_family():
    path = HOME / "native_family.py"
    spec = importlib.util.spec_from_file_location("tiles_native_family_for_independent_audit", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load same-task native family")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _source_binding():
    paths = [HOME / name for name in ("audit_native.py", "native_family.py", "canonical.rkt",
                                      "adapter.py", "promotion.json")]
    paths += [HOME.parents[1] / "generator.py", HOME.parents[1] / "tests/test_native_audit.py",
              ROOT / "src/arcpuzzles/parametric_worker.py", ROOT / "src/arcpuzzles/catalog.py",
              ROOT / "shared/runtime/arc_repl/racket_bridge.py",
              ROOT / "shared/runtime/arc_repl/security.py",
              ROOT / "shared/runtime/puzzle_generators/rule_wrap.py",
              ROOT / "shared/tools/comment_solutions.py",
              ROOT / "shared/runtime/arc_repl/racket_prelude/arc-prelude.rkt"]
    return {str(path.relative_to(ROOT)): _digest(path.read_bytes()) for path in paths}


def _bank(episode, demos=6, queries=4):
    if (type(episode) is not dict or type(episode.get("train")) is not list
            or type(episode.get("test")) is not list
            or len(episode["train"]) != demos or len(episode["test"]) != queries):
        raise ValueError("native family returned incorrect bank counts")
    inputs = []
    for pair in episode["train"] + episode["test"]:
        if type(pair) is not dict or not {"input", "output"} <= set(pair):
            raise ValueError("bank pair needs input and output")
        source, output = _parse(pair["input"])[0], _grid(pair["output"])
        if (len(source), len(source[0])) != (len(output), len(output[0])):
            raise ValueError("intended output dimensions differ from input")
        inputs.append(_hash(source))
    if len(inputs) != len(set(inputs)):
        raise ValueError("bank demonstration/query inputs must be distinct")
    return deepcopy(episode)


def _features(grid):
    value, size, tiles = _parse(grid)
    return {"shape": [len(value), len(value[0])], "tile_size": size, "tile_count": len(tiles),
            "marker_counts": [len(markers) for _, _, _, markers in tiles],
            "motif_sizes": [len(motif) for _, _, motif, _ in tiles],
            "component_counts": [len(_components(motif)) for _, _, motif, _ in tiles]}


def run(out):
    """Audit the declared finite bank, preserving all exact execution evidence."""
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    report = {
        "schema": "1ee7274bdbb0-native-teaching-audit-v1", "task_id": TASK_ID,
        "status": "running", "started_utc": datetime.now(timezone.utc).isoformat(),
        "canonical_program_sha256": CANONICAL_SHA256, "seeds": [0, 17],
        "counts": {"teaching_demos": 2, "verified_bank_demos": 6, "queries": 4,
                   "settings": 4, "intended_labels_expected": 80},
        "episodes": [], "failures": [], "intended_labels_verified": 0,
        "excluded_inactive_hypotheses": {
            "settle_rivals_at_post_none": "These B-stage variants are inactive or equivalent when no post step is selected.",
        },
        "limits": [
            "Finite declared-rival audit over four settings and seeds 0,17; no universal identification claim.",
            "Every 6-demo/4-query label is compared with independently written Python and protected Racket.",
            "Only the first two demonstrations teach; rivals stop at their first demonstration refutation.",
            "Only demonstration survivors execute queries, and query labels never update that survivor set.",
            "Grammar includes the declared single-square-tile extension needed for exact 30x30 stress.",
            "This authoring evidence does not resolve production audits, grant approval, or admit training data.",
        ],
    }
    executor = None
    try:
        source_binding = _source_binding()
        report["source_files_sha256"] = source_binding
        family = _load_family()
        if len(family.SETTINGS) != 4 or {_hash(s) for s in family.SETTINGS} != {_hash(s) for s in SETTINGS}:
            raise AssertionError("native settings differ from the four declared combinations")
        canonical = family.program({"turn": "cw", "post": "none"})
        if _digest(canonical.encode()) != CANONICAL_SHA256:
            raise AssertionError("default program differs from pinned canonical Catalog rule")
        if canonical != (HOME / "canonical.rkt").read_text(encoding="utf-8"):
            raise AssertionError("canonical program file does not match the exact native default")
        with protected_evaluator() as executor:
            report["racket"] = deepcopy(executor.identity)
            for seed in (0, 17):
                shared_inputs = None
                for settings in SETTINGS:
                    bank = _bank(family.generate(seed, deepcopy(settings), demos=6, queries=4))
                    minimum = _bank(family.generate(seed, deepcopy(settings), demos=2, queries=4), demos=2)
                    if minimum["train"] != bank["train"][:2] or minimum["test"] != bank["test"]:
                        raise AssertionError("minimum teaching episode differs from full bank prefix")
                    program = family.program(settings)
                    if bank["program_solution"] != program or minimum["program_solution"] != program:
                        raise AssertionError("episode does not bind the selected exact program")
                    pairs = bank["train"] + bank["test"]
                    input_hashes = [_hash(pair["input"]) for pair in pairs]
                    if shared_inputs is not None and input_hashes != shared_inputs:
                        raise AssertionError("input bank changes with the selected rule settings")
                    shared_inputs = input_hashes
                    features = [_features(pair["input"]) for pair in pairs]
                    if any(set(feature["marker_counts"]) != {0, 1, 2, 3} for feature in features[:2]):
                        raise AssertionError("each teaching core must exhibit marker counts 0,1,2,3")
                    intended_executions = []
                    for pair in pairs:
                        row = executor.evaluate(program, pair["input"])
                        intended_executions.append(row["execution_id"])
                        if row["status"] != "ok":
                            raise AssertionError(f"intended Racket execution error: {row}")
                        independent = python_intended(pair["input"], settings)
                        if row["output"] != pair["output"] or row["output"] != independent:
                            raise AssertionError("intended Racket, independent Python and native labels disagree")
                        report["intended_labels_verified"] += 1
                    assessments = []
                    for name in rivals(settings):
                        assessment = assess_rival(executor, settings, name, minimum["train"], bank["test"])
                        assessments.append(assessment)
                        if assessment["status"] in ("teaching_hole", "execution_error", "oracle_mismatch"):
                            report["failures"].append({"seed": seed, "settings": deepcopy(settings), **assessment})
                    episode_row = {
                        "seed": seed, "settings": deepcopy(settings), "program_sha256": _digest(program.encode()),
                        "train": bank["train"], "test": bank["test"], "input_sha256": input_hashes,
                        "features": features, "intended_executions": intended_executions, "rivals": assessments,
                        "refuted_rivals": [r["name"] for r in assessments if r["status"] == "demo_refuted"],
                        "query_agreeing_survivors": [r["name"] for r in assessments if r["status"] == "query_agreeing_survivor"],
                        "query_disagreeing_survivors": [r["name"] for r in assessments if r["status"] == "teaching_hole"],
                    }
                    report["episodes"].append(episode_row)
                    print(json.dumps({"seed": seed, "settings": settings,
                                      "refuted": len(episode_row["refuted_rivals"]),
                                      "query_agreeing_survivors": episode_row["query_agreeing_survivors"],
                                      "teaching_holes": episode_row["query_disagreeing_survivors"],
                                      "distinct_racket_evaluations": executor.execution_count}), flush=True)
        report["source_files_sha256_after"] = _source_binding()
        report["source_stable"] = report["source_files_sha256_after"] == source_binding
        report["racket_after"] = deepcopy(executor.identity_after)
        report["runtime_stable"] = executor.identity == executor.identity_after
        if not report["source_stable"] or not report["runtime_stable"]:
            raise AssertionError("audited source or runtime changed during the run")
        report["status"] = "passed" if not report["failures"] else "failed"
    except Exception as error:
        report["status"] = "failed"
        report["failure"] = {"type": type(error).__name__, "message": str(error)}
    finally:
        if executor is not None:
            report["racket_evaluations"] = executor.execution_count
            report["evaluation_requests"] = executor.request_count
            report["cache_hits"] = executor.request_count - executor.execution_count
            evidence = {"schema": "1ee7274bdbb0-exact-racket-executions-v1",
                        "racket": executor.identity, "racket_after": executor.identity_after,
                        "programs": executor.programs, "inputs": executor.inputs,
                        "executions": list(executor.records.values())}
            _write_json(out / "executions.json", evidence)
            report["executions_file"] = {"path": "executions.json",
                                          "sha256": _digest((out / "executions.json").read_bytes())}
        hole = next((row for row in report["failures"] if row["status"] == "teaching_hole"), None)
        if hole is not None:
            _write_json(out / "minimal-teaching-hole.json", {
                "task_id": TASK_ID, "seed": hole["seed"], "settings": hole["settings"],
                **hole["first_teaching_hole"],
            })
            report["minimal_teaching_hole_file"] = {
                "path": "minimal-teaching-hole.json",
                "sha256": _digest((out / "minimal-teaching-hole.json").read_bytes()),
            }
        report["finished_utc"] = datetime.now(timezone.utc).isoformat()
        _write_json(out / "audit.json", report)
    print(json.dumps({"status": report["status"], "episodes": len(report["episodes"]),
                      "failures": len(report["failures"]), "out": str(out)}), flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="new task-owned evidence directory")
    args = parser.parse_args()
    return 0 if run(args.out)["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
