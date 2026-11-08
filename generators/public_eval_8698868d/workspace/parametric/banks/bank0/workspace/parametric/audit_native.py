"""Independent topology, association, and orientation audit for panel mosaics.

The Python oracle uses its own four-neighbor traversal. It locates the board by
component bounding-box area, partitions its regular tile lattice, then counts
background components and independently selects and renders each pattern.
Only runtime/ledger bookkeeping is explicitly copied from the current first
task's audit; no earlier environment, runtime, evidence or imports are reused.
"""
from __future__ import annotations
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

HOME = Path(__file__).resolve().parent
TASK = HOME.parents[1]
ROOT = HOME.parents[3]
RUNTIME = ROOT / "shared/runtime"
TASK_ID = "public_eval_8698868d"
PARENT_ID = "8698868d"
ASSIGNMENT_ID = "review-88f158cce540885b"
sys.path[:0] = [str(ROOT / "src"), str(RUNTIME)]
from arcpuzzles.parametric_worker import _local_imports, _real_evaluator

SETTINGS = ({"pattern_orientation": "as_observed"}, {"pattern_orientation": "clockwise90"})
SEEDS = (0, 17)
RIVALS = (
    "identity", "eight_connected", "hole_area", "foreground_area_rank",
    "reverse_hole_rank", "source_order", "reverse_source_order", "numeric_color_rank",
    "same_color", "nearest_pattern", "first_pattern", "largest_ink_pattern",
    "counterclockwise90", "rotate180", "flip_horizontal", "flip_vertical", "transpose",
    "antidiagonal", "rotate_whole_board", "holes_to_background", "markers_survive",
    "solid_pattern_fill", "swap_ink_holes", "no_crop", "shift_inset",
)
RIVAL_MEANINGS = {
    "identity": "Return the original input.",
    "eight_connected": "Count background holes with eight-neighbor rather than four-neighbor connectivity.",
    "hole_area": "Match the number of background pixels rather than the number of background components.",
    "foreground_area_rank": "Assign ascending pattern ink area to ascending panel hole-count rank.",
    "reverse_hole_rank": "Reverse the pattern hole-count ranking before matching panel ranks.",
    "source_order": "Assign patterns in source row-major order to panels in board row-major order.",
    "reverse_source_order": "Assign reversed source pattern order to board row-major panels.",
    "numeric_color_rank": "Pair sorted pattern colors with sorted panel colors.",
    "same_color": "Choose a pattern with the same color as its panel.",
    "nearest_pattern": "Choose the nearest source-pattern center to each panel center, using exact squared doubled-center distance.",
    "first_pattern": "Use the first source pattern for every panel.",
    "largest_ink_pattern": "Use the pattern with the most ink for every panel.",
    "counterclockwise90": "Always turn each selected pattern counterclockwise90 degrees.",
    "rotate180": "Always turn each selected pattern180 degrees.",
    "flip_horizontal": "Always reflect each selected pattern left-to-right.",
    "flip_vertical": "Always reflect each selected pattern top-to-bottom.",
    "transpose": "Always transpose each selected pattern across its main diagonal.",
    "antidiagonal": "Always reflect each selected pattern across its opposite diagonal.",
    "rotate_whole_board": "Assemble unturned patterns, then rotate the entire board clockwise90 degrees.",
    "holes_to_background": "Retain the canvas background in inserted pattern holes instead of the panel color.",
    "markers_survive": "Stamp pattern ink onto the original board without clearing old clue markers.",
    "solid_pattern_fill": "Fill every inset square with its selected pattern color, losing its holes.",
    "swap_ink_holes": "Paint selected pattern ink in the panel color and pattern holes in the pattern color.",
    "no_crop": "Render the board back into the complete input canvas and retain detached source patterns.",
    "shift_inset": "Place each selected pattern at the tile origin instead of one cell inside its frame.",
}
EXCLUDED_EQUIVALENT = {
    "force_as_observed": "Already represented by the declared as_observed setting.",
    "force_clockwise90": "Already represented by the declared clockwise90 setting.",
    "match_interior_ink_area": "For equal-size panel interiors and patterns, exact ink-area equality is equivalent to the retained hole_area rival.",
    "choose_by_bbox_area": "All admitted patterns have the same square bounding box; a first-tie size selector is represented by first_pattern.",
}
LIMITS = {"seeds": list(SEEDS), "settings": list(SETTINGS), "episode_count": 4,
    "generated_demonstrations_per_episode": 6, "fit_demonstrations_per_episode": 2,
    "queries_per_episode": 4, "original_label_count": 3,
    "max_racket_evaluations": 1200, "max_evaluation_requests": 1600,
    "wall_seconds_checked_between_calls": 300, "racket_seconds_per_call": 10,
    "racket_startup_seconds": 30,
    "candidate_totality": "Standalone rivals return the input when canonical geometry is malformed. A wrong feature with no matching pattern leaves that panel unchanged; ties use source order. All outputs remain exact ARC1..30 grids."}


def packed(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


def grid_copy(value):
    if (type(value) is not list or not 1 <= len(value) <= 30
            or type(value[0]) is not list or not 1 <= len(value[0]) <= 30
            or any(type(row) is not list or len(row) != len(value[0])
                   or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
                   for row in value)):
        raise ValueError("Expected an exact-integer rectangular ARC1..30 grid")
    return [row[:] for row in value]


def setting(value):
    if (type(value) is not dict or set(value) != {"pattern_orientation"}
            or type(value["pattern_orientation"]) is not str
            or value["pattern_orientation"] not in ("as_observed", "clockwise90")):
        raise ValueError("Expected exactly pattern_orientation=as_observed or clockwise90")
    return value["pattern_orientation"]


def equivalent_aliases(settings):
    setting(settings)
    return {}


def components(cells, diagonal=False):
    remaining, result = set(cells), []
    offsets = ((-1, 0), (1, 0), (0, -1), (0, 1))
    if diagonal:
        offsets += ((-1, -1), (-1, 1), (1, -1), (1, 1))
    while remaining:
        first = min(remaining)
        remaining.remove(first)
        pending, found = [first], [first]
        while pending:
            r, c = pending.pop()
            for dr, dc in offsets:
                p = (r+dr, c+dc)
                if p in remaining:
                    remaining.remove(p)
                    found.append(p)
                    pending.append(p)
        result.append(tuple(sorted(found)))
    return result


def box(cells):
    return (min(r for r, c in cells), min(c for r, c in cells),
            max(r for r, c in cells), max(c for r, c in cells))


def crop(grid, bb):
    r0, c0, r1, c1 = bb
    return [row[c0:c1+1] for row in grid[r0:r1+1]]


def holes(patch, bg, diagonal=False):
    return len(components([(r, c) for r, row in enumerate(patch) for c, v in enumerate(row) if v == bg], diagonal))


def framed(patch, bg):
    color = patch[0][0]
    h, w = len(patch), len(patch[0])
    return color != bg and all(v in (color, bg) and (v == color if r in (0, h-1) or c in (0, w-1) else True)
        for r, row in enumerate(patch) for c, v in enumerate(row))


def scene(grid):
    grid = grid_copy(grid)
    counts = Counter(v for row in grid for v in row)
    bg = min(counts, key=lambda v: (-counts[v], v))
    objects = components([(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v != bg])
    if len(objects) < 2:
        raise ValueError("Need a board and detached patterns")
    def area(obj):
        r0, c0, r1, c1 = box(obj)
        return (r1-r0+1) * (c1-c0+1)
    board = min(objects, key=lambda obj: (-area(obj), obj[0]))
    board_box = box(board)
    others = [obj for obj in objects if obj != board]
    n = box(others[0])[2] - box(others[0])[0] + 1
    tile = n + 2
    board_patch = crop(grid, board_box)
    height, width = len(board_patch), len(board_patch[0])
    if height % tile or width % tile or height * width // tile**2 != len(others):
        raise ValueError("Board lattice does not match pattern inventory")
    patterns = []
    for i, obj in enumerate(others):
        bb = box(obj)
        patch = crop(grid, bb)
        if len(patch) != n or len(patch[0]) != n or not framed(patch, bg):
            raise ValueError("Patterns must be equally sized framed monochrome squares")
        pixels = sum(v == bg for row in patch for v in row)
        patterns.append({"index": i, "color": patch[0][0], "patch": patch, "box": bb,
            "count": holes(patch, bg), "area": pixels, "ink": n*n-pixels})
    panels = []
    for r in range(0, height, tile):
        for c in range(0, width, tile):
            patch = [row[c:c+tile] for row in board_patch[r:r+tile]]
            if not framed(patch, bg):
                raise ValueError("Every panel must have a solid uniform frame")
            panels.append({"index": len(panels), "row": r, "col": c, "color": patch[0][0],
                "patch": patch, "count": holes(patch, bg), "area": sum(v == bg for row in patch for v in row)})
    pattern_counts, panel_counts = [p["count"] for p in patterns], [p["count"] for p in panels]
    if (len(set(pattern_counts)) != len(pattern_counts) or len(set(panel_counts)) != len(panel_counts)
            or sorted(pattern_counts) != sorted(panel_counts)):
        raise ValueError("Pattern/panel counts must give a unique complete association")
    return {"background": bg, "board_box": board_box, "board": board_patch,
        "height": height, "width": width, "pattern_side": n, "tile_side": tile,
        "patterns": patterns, "panels": panels}


def orient(patch, name):
    n = len(patch)
    if name == "as_observed":
        return [row[:] for row in patch]
    index = {
        "clockwise90": lambda r, c: (n-1-c, r),
        "counterclockwise90": lambda r, c: (c, n-1-r),
        "rotate180": lambda r, c: (n-1-r, n-1-c),
        "flip_horizontal": lambda r, c: (r, n-1-c),
        "flip_vertical": lambda r, c: (n-1-r, c),
        "transpose": lambda r, c: (c, r),
        "antidiagonal": lambda r, c: (n-1-c, n-1-r),
    }[name]
    return [[patch[index(r, c)[0]][index(r, c)[1]] for c in range(n)] for r in range(n)]


def selected_pattern(info, panel, name):
    patterns, panels = info["patterns"], info["panels"]
    bg = info["background"]
    if name in ("eight_connected", "hole_area"):
        value = holes(panel["patch"], bg, True) if name == "eight_connected" else panel["area"]
        return next((p for p in patterns if (holes(p["patch"], bg, True) if name == "eight_connected" else p["area"]) == value), None)
    rank = sorted(panels, key=lambda p: (p["count"], p["index"])).index(panel)
    if name == "foreground_area_rank":
        return sorted(patterns, key=lambda p: (p["ink"], p["index"]))[rank]
    if name == "reverse_hole_rank":
        return sorted(patterns, key=lambda p: (p["count"], p["index"]), reverse=True)[rank]
    if name == "source_order":
        return patterns[panel["index"]]
    if name == "reverse_source_order":
        return patterns[-1-panel["index"]]
    if name == "numeric_color_rank":
        rank = sorted(panels, key=lambda p: (p["color"], p["index"])).index(panel)
        return sorted(patterns, key=lambda p: (p["color"], p["index"]))[rank]
    if name == "same_color":
        return next((p for p in patterns if p["color"] == panel["color"]), None)
    if name == "nearest_pattern":
        center = (2*(info["board_box"][0]+panel["row"])+info["tile_side"]-1,
                  2*(info["board_box"][1]+panel["col"])+info["tile_side"]-1)
        return min(patterns, key=lambda p: ((p["box"][0]+p["box"][2]-center[0])**2 +
                                            (p["box"][1]+p["box"][3]-center[1])**2, p["index"]))
    if name == "first_pattern":
        return patterns[0]
    if name == "largest_ink_pattern":
        return min(patterns, key=lambda p: (-p["ink"], p["index"]))
    return next(p for p in patterns if p["count"] == panel["count"])


def rival_reference(grid, settings, name):
    mode = setting(settings)
    if name not in ("reference", *RIVALS):
        raise ValueError("Unknown hypothesis: " + str(name))
    grid = grid_copy(grid)
    if name == "identity":
        return grid
    try:
        info = scene(grid)
    except ValueError:
        return grid
    out = deepcopy(info["board"])
    bg, n, tile = info["background"], info["pattern_side"], info["tile_side"]
    wrong_orientations = {"counterclockwise90", "rotate180", "flip_horizontal", "flip_vertical", "transpose", "antidiagonal"}
    turn = name if name in wrong_orientations else "as_observed" if name == "rotate_whole_board" else mode
    for panel in info["panels"]:
        pattern = selected_pattern(info, panel, name)
        if pattern is None:
            continue
        r0, c0, base = panel["row"], panel["col"], panel["color"]
        if name != "markers_survive":
            for r in range(tile):
                for c in range(tile):
                    out[r0+r][c0+c] = base
        patch = orient(pattern["patch"], turn)
        offset = 0 if name == "shift_inset" else 1
        for r in range(n):
            for c in range(n):
                value = patch[r][c]
                if name == "solid_pattern_fill":
                    value = pattern["color"]
                elif name == "swap_ink_holes":
                    value = pattern["color"] if value == bg else base
                elif value == bg and name != "holes_to_background":
                    continue
                out[r0+r+offset][c0+c+offset] = value
    if name == "rotate_whole_board":
        out = [list(row) for row in zip(*out[::-1])]
    if name == "no_crop":
        full = deepcopy(grid)
        r0, c0, _, _ = info["board_box"]
        for r, row in enumerate(out):
            full[r0+r][c0:c0+len(row)] = row
        out = full
    return out


def reference(grid, settings):
    return rival_reference(grid, settings, "reference")


def rival_program(settings, name):
    mode = setting(settings)
    if name not in ("reference", *RIVALS):
        raise ValueError("Unknown hypothesis: " + str(name))
    if name == "identity":
        return "(rule! (lambda (g) g))"
    select = "(first-or-false (filter (lambda (p) (= (list-ref p 4) (list-ref panel 5))) patterns))"
    if name == "eight_connected":
        select = "(first-or-false (filter (lambda (p) (= (holes8 (third p)) (holes8 (fifth panel)))) patterns))"
    elif name == "hole_area":
        select = "(first-or-false (filter (lambda (p) (= (list-ref p 5) (list-ref panel 6))) patterns))"
    elif name == "foreground_area_rank":
        select = "(list-ref (sort-field patterns 6) (index-of (sort-field panels 5) panel))"
    elif name == "reverse_hole_rank":
        select = "(list-ref (reverse (sort-field patterns 4)) (index-of (sort-field panels 5) panel))"
    elif name == "source_order":
        select = "(list-ref patterns (first panel))"
    elif name == "reverse_source_order":
        select = "(list-ref (reverse patterns) (first panel))"
    elif name == "numeric_color_rank":
        select = "(list-ref (sort-field patterns 1) (index-of (sort-field panels 3) panel))"
    elif name == "same_color":
        select = "(first-or-false (filter (lambda (p) (= (second p) (fourth panel))) patterns))"
    elif name == "nearest_pattern":
        select = "(first (sort patterns (lambda (a b) (let ((da (distance a panel)) (db (distance b panel))) (if (= da db) (< (first a) (first b)) (< da db))))))"
    elif name == "first_pattern":
        select = "(first patterns)"
    elif name == "largest_ink_pattern":
        select = "(first (sort patterns (lambda (a b) (if (= (list-ref a 6) (list-ref b 6)) (< (first a) (first b)) (> (list-ref a 6) (list-ref b 6))))))"
    wrong = {"counterclockwise90", "rotate180", "flip_horizontal", "flip_vertical", "transpose", "antidiagonal"}
    turn = name if name in wrong else "as_observed" if name == "rotate_whole_board" else mode
    coordinates = {"as_observed": "r c", "clockwise90": "(- n 1 c) r",
        "counterclockwise90": "c (- n 1 r)", "rotate180": "(- n 1 r) (- n 1 c)",
        "flip_horizontal": "r (- n 1 c)", "flip_vertical": "(- n 1 r) c",
        "transpose": "c r", "antidiagonal": "(- n 1 c) (- n 1 r)"}[turn]
    cleared = "out" if name == "markers_survive" else "(for*/fold ((acc out)) ((r (in-range t)) (c (in-range t))) (set-cell acc (+ r0 r) (+ c0 c) base))"
    offset = "0" if name == "shift_inset" else "1"
    should_paint = "#t" if name in ("holes_to_background", "solid_pattern_fill", "swap_ink_holes") else "(!= value bg)"
    paint = "(second selected)" if name == "solid_pattern_fill" else "(if (= value bg) (second selected) base)" if name == "swap_ink_holes" else "value"
    finish = "result"
    if name == "rotate_whole_board":
        finish = "(grid-from-fn (cols result) (rows result) (lambda (r c) (at result (- (rows result) 1 c) r)))"
    elif name == "no_crop":
        finish = "(for*/fold ((out g)) ((r (in-range bh)) (c (in-range bw))) (set-cell out (+ (first bb) r) (+ (second bb) c) (at result r c)))"
    template = r'''(rule! (let ()
  (define (point< a b) (or (< (first a) (first b)) (and (= (first a) (first b)) (< (second a) (second b)))))
  (define positions (grid-positions g))
  (define bg (for/fold ((best 0)) ((color (in-range 1 10)))
    (if (> (count (lambda (p) (= (at g (first p) (second p)) color)) positions)
           (count (lambda (p) (= (at g (first p) (second p)) best)) positions)) color best)))
  (define mask (grid-from-fn h w (lambda (r c) (if (= (at g r c) bg) 0 1))))
  (define objects4 (sort (map (lambda (o) (sort (obj-cells o) point<)) (objects mask 0)) (lambda (a b) (point< (first a) (first b)))))
  (define (area cells) (let ((b (bbox-of-cells cells))) (* (+ 1 (- (third b) (first b))) (+ 1 (- (fourth b) (second b))))))
  (define (framed? patch)
    (let ((ph (rows patch)) (pw (cols patch)) (base (at patch 0 0)))
      (and (!= base bg) (andmap (lambda (p) (let* ((r (first p)) (c (second p)) (v (at patch r c)))
        (and (member? v (list base bg)) (or (and (> r 0) (< r (- ph 1)) (> c 0) (< c (- pw 1))) (= v base))))) (grid-positions patch)))))
  (define (hole-area patch) (count (lambda (p) (= (at patch (first p) (second p)) bg)) (grid-positions patch)))
  (define (holes4 patch) (length (objects (grid-from-fn (rows patch) (cols patch) (lambda (r c) (if (= (at patch r c) bg) 1 0))) 0)))
  (define (holes8 patch)
    (define allowed (filter (lambda (p) (= (at patch (first p) (second p)) bg)) (grid-positions patch)))
    (define (flood todo seen)
      (if (empty? todo) seen
        (let ((p (first todo)))
          (if (or (member? p seen) (not (member? p allowed))) (flood (rest todo) seen)
            (flood (append (for*/list ((dr (in-range -1 2)) (dc (in-range -1 2))) (list (+ (first p) dr) (+ (second p) dc))) (rest todo)) (cons p seen))))))
    (let loop ((remaining allowed) (total 0))
      (if (empty? remaining) total
        (let ((found (flood (list (first remaining)) '())))
          (loop (filter (lambda (p) (not (member? p found))) remaining) (+ total 1))))))
  (define (sort-field xs k) (sort xs (lambda (a b) (if (= (list-ref a k) (list-ref b k)) (< (first a) (first b)) (< (list-ref a k) (list-ref b k))))))
  (define (first-or-false xs) (if (empty? xs) #f (first xs)))
  (if (< (length objects4) 2) g
    (let* ((board (first (sort objects4 (lambda (a b) (if (= (area a) (area b)) (point< (first a) (first b)) (> (area a) (area b)))))))
           (bb (bbox-of-cells board)) (original (subgrid g (first bb) (second bb) (third bb) (fourth bb)))
           (others (filter (lambda (cc) (not (equal? cc board))) objects4))
           (nb (bbox-of-cells (first others))) (n (+ 1 (- (third nb) (first nb)))) (t (+ n 2))
           (bh (rows original)) (bw (cols original)))
      (if (or (!= (modulo bh t) 0) (!= (modulo bw t) 0) (!= (* (quotient bh t) (quotient bw t)) (length others))) g
        (let* ((patterns (for/list ((cc (in-list others)) (i (in-naturals)))
                 (let* ((b (bbox-of-cells cc)) (patch (subgrid g (first b) (second b) (third b) (fourth b))) (ha (hole-area patch)))
                   (list i (at patch 0 0) patch b (holes4 patch) ha (- (* n n) ha)))))
               (raw-panels (for*/list ((r (in-range 0 bh t)) (c (in-range 0 bw t)))
                 (let ((patch (subgrid original r c (+ r t -1) (+ c t -1)))) (list r c (at patch 0 0) patch (holes4 patch) (hole-area patch)))))
               (panels (for/list ((p (in-list raw-panels)) (i (in-naturals))) (cons i p)))
               (pc (map (lambda (p) (list-ref p 4)) patterns)) (tc (map (lambda (p) (list-ref p 5)) panels)))
          (if (not (and (andmap (lambda (p) (and (= (rows (third p)) n) (= (cols (third p)) n) (framed? (third p)))) patterns)
                        (andmap (lambda (p) (framed? (fifth p))) panels)
                        (= (length pc) (length (remove-duplicates pc))) (= (length tc) (length (remove-duplicates tc)))
                        (equal? (sort pc <) (sort tc <)))) g
            (let ()
              (define (distance p panel)
                (let* ((b (fourth p)) (dr (- (+ (first b) (third b)) (+ (* 2 (+ (first bb) (second panel))) t -1)))
                       (dc (- (+ (second b) (fourth b)) (+ (* 2 (+ (second bb) (third panel))) t -1)))) (+ (* dr dr) (* dc dc))))
              (define result
                (for/fold ((out original)) ((panel (in-list panels)))
                  (let ((selected @SELECT@))
                    (if (not selected) out
                      (let* ((r0 (second panel)) (c0 (third panel)) (base (fourth panel)) (patch (third selected))
                             (cleared @CLEAR@))
                        (for*/fold ((acc cleared)) ((r (in-range n)) (c (in-range n)))
                          (let ((value (at patch @COORDINATES@)))
                            (if @SHOULD_PAINT@ (set-cell acc (+ r0 r @OFFSET@) (+ c0 c @OFFSET@) @PAINT@) acc))))))))
              @FINISH@))))))))'''
    for key, value in {"SELECT": select, "CLEAR": cleared, "COORDINATES": coordinates,
            "SHOULD_PAINT": should_paint, "OFFSET": offset, "PAINT": paint, "FINISH": finish}.items():
        template = template.replace("@" + key + "@", value)
    return template


class CachedEvaluator:
    """Exact executable/input cache with an append-only request/execution ledger."""
    def __init__(self, apply, *, ledger=None):
        self.apply, self.ledger = apply, ledger
        self.cache, self.programs, self.records = {}, {}, []
        self.requests = self.evaluations = self.cache_hits = 0
        self.last_request = None
        self.context = {}
        self.started = time.monotonic()

    def __call__(self, program, grid):
        if self.requests >= LIMITS["max_evaluation_requests"]:
            raise RuntimeError("Finite evaluation request budget exhausted")
        if time.monotonic() - self.started > LIMITS["wall_seconds_checked_between_calls"]:
            raise TimeoutError("Finite audit wall budget exhausted between calls")
        value = grid_copy(grid)
        program_hash = sha(program.encode())
        self.programs[program_hash] = program
        self.requests += 1
        key = program, packed(value)
        row = {"request_index": self.requests, "program_sha256": program_hash,
               "input_sha256": sha(key[1]), "input": value,
               "context": deepcopy(self.context), "cache_hit": key in self.cache}
        self.last_request = deepcopy(row)
        try:
            if key in self.cache:
                self.cache_hits += 1
                output, execution_index = self.cache[key]
            else:
                if self.evaluations >= LIMITS["max_racket_evaluations"]:
                    raise RuntimeError("Finite protected evaluation budget exhausted")
                self.evaluations += 1
                execution_index = self.evaluations
                row["execution_index"] = execution_index
                output = grid_copy(self.apply(program, deepcopy(value)))
                self.cache[key] = deepcopy(output), execution_index
            row.update(status="ok", execution_index=execution_index,
                       output=deepcopy(output), output_sha256=sha(packed(output)))
            return deepcopy(output)
        except Exception as error:
            row.update(status="error", error=f"{type(error).__name__}: {error}")
            raise
        finally:
            self.records.append(row)
            if self.ledger is not None:
                self.ledger.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
                self.ledger.flush()


def fit_hypothesis(apply, program, demonstrations, oracle=None):
    """Use exactly the first two demonstrations, never later demonstrations."""
    if len(demonstrations) < 2:
        raise ValueError("Teaching audit requires two demonstrations")
    outputs, rejected = [], []
    for index, pair in enumerate(demonstrations[:2]):
        output = grid_copy(apply(program, pair["input"]))
        if oracle is not None and output != oracle(pair["input"]):
            raise ValueError("Independent Python/Racket candidate meaning mismatch")
        outputs.append(output)
        if output != pair["output"]:
            rejected.append(index)
    return {"survives_demonstrations": not rejected,
            "executed_demo_indices": [0, 1], "rejected_by_demo_indices": rejected,
            "demo_outputs": outputs}


def source_files():
    paths = {TASK / "generator.py", TASK / "reference.rkt", TASK / "workspace/public-parent.json"}
    paths.update(path for path in HOME.iterdir() if path.is_file()
                 and path.suffix in {".py", ".rkt", ".json", ".md"})
    paths.update((TASK / "tests").glob("*.py"))
    return {path.relative_to(ROOT).as_posix(): sha(path.read_bytes()) for path in sorted(paths)}


def runtime_files():
    paths = {ROOT / "src/arcpuzzles/parametric_worker.py", ROOT / "shared/tools/comment_solutions.py",
             RUNTIME / "puzzle_generators/rule_wrap.py"}
    paths.update(path for path in (RUNTIME / "arc_repl").rglob("*")
                 if path.is_file() and path.suffix in {".py", ".rkt"})
    return {path.relative_to(ROOT).as_posix(): sha(path.read_bytes()) for path in sorted(paths)}


def load_family():
    spec = importlib.util.spec_from_file_location("_public_eval_8698868d_frozen_native_audit", HOME / "native_family.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def original_pairs():
    base = ROOT / "shared/data/raw"
    challenge = json.loads((base / "arc-agi_evaluation_challenges.json").read_text())[PARENT_ID]
    gold = json.loads((base / "arc-agi_evaluation_solutions.json").read_text())[PARENT_ID]
    if len(gold) != len(challenge["test"]):
        raise ValueError("Official query/gold count mismatch")
    pairs = [("train", i, pair) for i, pair in enumerate(challenge["train"])]
    pairs += [("test", i, {"input": pair["input"], "output": value})
              for i, (pair, value) in enumerate(zip(challenge["test"], gold))]
    return challenge, gold, pairs


def facts(grid, output):
    info = scene(grid)
    return {"input_shape": [len(grid), len(grid[0])], "output_shape": [len(output), len(output[0])],
        "background": info["background"], "board_box": info["board_box"],
        "pattern_side": info["pattern_side"], "tile_side": info["tile_side"],
        "panel_counts": [p["count"] for p in info["panels"]],
        "pattern_counts_in_source_order": [p["count"] for p in info["patterns"]],
        "pattern_hole_areas": [p["area"] for p in info["patterns"]],
        "input_occupied": sum(v != info["background"] for row in grid for v in row),
        "input_sha256": sha(packed(grid)), "output_sha256": sha(packed(output))}


def run(out):
    out = Path(out)
    if out.exists() or out.is_symlink():
        raise FileExistsError(out)
    binding, runtime_before = source_files(), runtime_files()
    out.mkdir(parents=True)
    private = out / "private"
    private.mkdir()
    for name, digest in binding.items():
        content = (ROOT / name).read_bytes()
        if sha(content) != digest:
            raise RuntimeError("Source changed while taking the initial snapshot: " + name)
        destination = out / "source" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
    report = {"schema": "public-eval-8698868d-independent-teaching-audit-v1", "status": "running",
              "task_id": TASK_ID, "assignment_id": ASSIGNMENT_ID,
              "source_files_sha256_before": binding, "runtime_files_sha256_before": runtime_before,
              "limits": deepcopy(LIMITS), "rival_meanings": RIVAL_MEANINGS,
              "excluded_equivalent_hypotheses": EXCLUDED_EQUIVALENT,
              "episodes": [], "findings": [], "reference_label_count": 0, "original_label_count": 0,
              "visibility": "controller_private", "training_admitted": False,
              "scope": "Four episodes only; all6+4 generated labels plus all three official labels checked independently. Exactly first2 demos determine survivors, then every survivor receives all4 query scores. No universal identifiability, owner acceptance, or training admission."}
    evaluator = bridge = None
    started = time.monotonic()
    try:
        family = load_family()
        with (private / "executions.jsonl").open("x") as ledger:
            with _local_imports(RUNTIME, HOME):
                apply, identity, bridge = _real_evaluator(RUNTIME)
                report["racket_before"] = identity
                evaluator = CachedEvaluator(apply, ledger=ledger)
                challenge, gold, official = original_pairs()
                authority = json.loads((TASK / "workspace/public-parent.json").read_text())
                report["parent_binding"] = {"public_task_id": PARENT_ID,
                    "challenge_sha256": sha(packed(challenge)), "test_outputs_sha256": sha(packed(gold)),
                    "authority": authority}
                if (sha(packed(challenge)) != authority["challenge_sha256"]
                        or sha(packed(gold)) != authority["test_outputs_sha256"]):
                    raise ValueError("Official parent record differs from immutable linkage")
                canonical = (TASK / "reference.rkt").read_text()
                if canonical != family.program(SETTINGS[0]):
                    raise ValueError("Default program differs from exact root reference")
                report["original_pairs"] = []
                for split, index, pair in official:
                    evaluator.context = {"phase": "verify_all_official_labels", "split": split, "index": index}
                    actual = evaluator(canonical, pair["input"])
                    independent = reference(pair["input"], SETTINGS[0])
                    item = {"split": split, "index": index, **deepcopy(pair),
                        "racket_output": actual, "python_output": independent,
                        "matched": actual == independent == pair["output"]}
                    report["original_pairs"].append(item)
                    if not item["matched"]:
                        raise ValueError("Official gold, independent Python, and protected Racket disagree")
                    report["original_label_count"] += 1
                    report["reference_label_count"] += 1
                banks = {}
                for seed in SEEDS:
                    for settings in SETTINGS:
                        mode = setting(settings)
                        episode = family.generate(seed, deepcopy(settings), demos=6, queries=4)
                        selected_program = family.program(settings)
                        if episode.get("program_solution") != selected_program:
                            raise ValueError("Episode program_solution differs from selected program")
                        train, test = deepcopy(episode["train"]), deepcopy(episode["test"])
                        if len(train) != 6 or len(test) != 4:
                            raise ValueError("Episode omitted requested demonstrations or queries")
                        for pair in train + test:
                            grid_copy(pair["input"])
                            grid_copy(pair["output"])
                        inputs = [pair["input"] for pair in train + test]
                        if len({packed(grid) for grid in inputs}) != 10:
                            raise ValueError("Repeated input inside an episode")
                        if seed in banks and inputs != banks[seed]:
                            raise ValueError("Input bank depends on the semantic setting")
                        banks[seed] = deepcopy(inputs)
                        candidates = [("declared:pattern_orientation=" + other["pattern_orientation"], family.program(other),
                                       lambda grid, other=other: reference(grid, other)) for other in SETTINGS]
                        candidates += [(name, rival_program(settings, name),
                                        lambda grid, name=name: rival_reference(grid, settings, name)) for name in RIVALS]
                        row = {"seed": seed, "settings": deepcopy(settings), "train": train, "test": test,
                               "fit_demo_indices": [0, 1], "label_checks": [], "hypotheses": []}
                        report["episodes"].append(row)
                        # Fit receives no later-demo or query labels.
                        for name, program, oracle in candidates:
                            evaluator.context = {"phase": "fit_first_two_demonstrations", "seed": seed,
                                                 "settings": settings, "hypothesis": name}
                            row["hypotheses"].append({"name": name, "program_sha256": sha(program.encode()),
                                                      **fit_hypothesis(evaluator, program, train[:2], oracle)})
                        survivors = [item["name"] for item in row["hypotheses"] if item["survives_demonstrations"]]
                        row["survivors_frozen_before_query"] = deepcopy(survivors)
                        row["survivor_set_sha256_before_queries"] = sha(packed(survivors))
                        intended_name = "declared:pattern_orientation=" + mode
                        row["extra_survivors"] = [name for name in survivors if name != intended_name]
                        aliases = equivalent_aliases(settings)
                        row["equivalent_survivor_aliases"] = {name: aliases[name] for name in row["extra_survivors"] if name in aliases}
                        row["unclassified_extra_survivors"] = [name for name in row["extra_survivors"] if name not in aliases]
                        if intended_name not in survivors:
                            raise ValueError("The intended program was refuted by its own teaching labels")
                        for split, pairs in (("train", train), ("test", test)):
                            for index, pair in enumerate(pairs):
                                evaluator.context = {"phase": "verify_all_intended_labels", "seed": seed,
                                                     "settings": settings, "split": split, "index": index}
                                actual = evaluator(selected_program, pair["input"])
                                independent = reference(pair["input"], settings)
                                check = {"split": split, "index": index,
                                         "racket_output": actual, "python_output": independent,
                                         "provided_output": pair["output"],
                                         "matched": actual == independent == pair["output"],
                                         "facts": facts(pair["input"], independent)}
                                row["label_checks"].append(check)
                                if not check["matched"]:
                                    raise ValueError("Native label, independent Python, and protected Racket disagree")
                                report["reference_label_count"] += 1
                        # Query labels score every frozen survivor and can never refit it.
                        for fitted, (name, program, oracle) in zip(row["hypotheses"], candidates):
                            fitted["query_outputs"] = None
                            fitted["query_disagreement_indices"] = None
                            if not fitted["survives_demonstrations"]:
                                continue
                            outputs = []
                            for index, pair in enumerate(test):
                                evaluator.context = {"phase": "score_frozen_survivor_queries", "seed": seed,
                                                     "settings": settings, "hypothesis": name, "index": index}
                                actual = evaluator(program, pair["input"])
                                if actual != oracle(pair["input"]):
                                    raise ValueError("Independent Python/Racket survivor query meaning mismatch")
                                outputs.append(actual)
                            disagreements = [index for index, (actual, pair) in enumerate(zip(outputs, test))
                                             if actual != pair["output"]]
                            fitted["query_outputs"] = outputs
                            fitted["query_disagreement_indices"] = disagreements
                            if disagreements:
                                report["findings"].append({"seed": seed, "settings": deepcopy(settings),
                                                           "hypothesis": name,
                                                           "query_disagreement_indices": disagreements,
                                                           "first_witness": deepcopy(test[disagreements[0]]),
                                                           "rival_output": outputs[disagreements[0]]})
                        after = [item["name"] for item in row["hypotheses"] if item["survives_demonstrations"]]
                        row["survivor_set_sha256_after_queries"] = sha(packed(after))
                        if after != survivors:
                            raise ValueError("Query scoring altered the teaching survivor set")
                report["matched_inputs_across_settings"] = True
                after_identity = bridge.runtime_identity
                report["racket_after"] = {key: after_identity[key] for key in identity}
                if report["racket_after"] != report["racket_before"]:
                    raise ValueError("Protected runtime identity changed during the audit")
                report["status"] = "passed" if not report["findings"] else "failed"
    except Exception as error:
        report["status"] = "error"
        report["error"] = f"{type(error).__name__}: {error}"
        if evaluator is not None:
            report["failed_request"] = evaluator.last_request
    finally:
        if bridge is not None:
            try:
                final_identity = bridge.runtime_identity
                report.setdefault("racket_after", {key: final_identity[key] for key in report.get("racket_before", {})})
            finally:
                bridge.close()
        report["source_files_sha256_after"] = source_files()
        report["runtime_files_sha256_after"] = runtime_files()
        report["source_unchanged"] = report["source_files_sha256_after"] == binding
        report["runtime_sources_unchanged"] = report["runtime_files_sha256_after"] == runtime_before
        if not report["source_unchanged"] or not report["runtime_sources_unchanged"]:
            report["status"] = "error"
            report["source_binding_error"] = "Source or runtime files changed during the audit"
        if evaluator is not None:
            report["programs"] = evaluator.programs
            report["execution"] = {"requests": evaluator.requests, "racket_evaluations": evaluator.evaluations,
                                   "cache_hits": evaluator.cache_hits, "successful_cached_results": len(evaluator.cache),
                                   "request_records": len(evaluator.records), "ledger": "executions.jsonl",
                                   "ledger_sha256": sha((private / "executions.jsonl").read_bytes())}
        report["elapsed_seconds"] = time.monotonic() - started
        (private / "audit.json").write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({key: report.get(key) for key in ("status", "reference_label_count", "execution", "findings", "error")}))
    return 0 if report["status"] == "passed" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    options = parser.parse_args()
    raise SystemExit(run(options.out))


if __name__ == "__main__":
    main()


