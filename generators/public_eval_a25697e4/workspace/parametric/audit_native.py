"""Independent finite audit of two-color keys fitted to edge sockets.

Geometry is independently inferred from the public parent. The oracle floods
from boundary seeds, enumerates signed coordinate permutations, then searches a
global one-to-one placement assignment. It does not import native semantics.
Only runtime/ledger bookkeeping is source-copied, with separate provenance.
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
TASK_ID = "public_eval_a25697e4"
PARENT_ID = "a25697e4"
ASSIGNMENT_ID = "review-88f158cce540885b"
sys.path[:0] = [str(ROOT / "src"), str(RUNTIME)]
from arcpuzzles.parametric_worker import _local_imports, _real_evaluator

SETTINGS = ({"reflection_colors": "swap"}, {"reflection_colors": "preserve"})
SEEDS = (0, 17)
RIVALS = (
    "identity", "rotations_only", "reflections_only", "translation_only",
    "global_color_sockets", "component_sockets", "fixed_background0", "fixed_background1",
    "ignore_collision", "ignore_bounds", "always_swap", "swap_proper", "swap_odd_turns",
    "swap_by_color_order", "matching_half_only", "tail_only", "copy_sources",
    "first_key_only", "largest_key_only", "first_socket_only", "paint_plug_anchor",
    "paint_all_anchor", "paint_all_part", "paint_all_other",
)
RIVAL_MEANINGS = {
    "identity": "Leave the input unchanged.",
    "rotations_only": "Search only the four proper rotations, with declared painting semantics.",
    "reflections_only": "Search only the four improper D4 transformations.",
    "translation_only": "Search only unrotated, unreflected translations.",
    "global_color_sockets": "Merge all edge-anchored cells of each color, even across different edges.",
    "component_sockets": "Treat each same-color edge-connected component as a separate socket.",
    "fixed_background0": "Treat color0 as background regardless of its frequency.",
    "fixed_background1": "Treat color1 as background regardless of its frequency.",
    "ignore_collision": "Accept an exact head/cavity match even if its tail overlaps stationary cells.",
    "ignore_bounds": "Accept placements with out-of-bounds tails and clip those cells when painting.",
    "always_swap": "Swap the two key colors for every placement, including proper rotations.",
    "swap_proper": "Swap colors precisely for proper, rather than improper, transforms.",
    "swap_odd_turns": "Swap colors when the transform's quarter-turn index is odd.",
    "swap_by_color_order": "Swap colors when the cavity-matching region has the smaller color number.",
    "matching_half_only": "Erase the moved key but paint only the region matching the cavity.",
    "tail_only": "Erase the moved key but paint only its exterior region.",
    "copy_sources": "Paint fitted keys without erasing their source locations.",
    "first_key_only": "Execute only the first key's placement in source row-major order.",
    "largest_key_only": "Execute only the largest source key; ties use source order.",
    "first_socket_only": "Execute only the placement for the first socket in edge/color order.",
    "paint_plug_anchor": "Paint the cavity-matching region in the socket color.",
    "paint_all_anchor": "Paint the entire fitted key in the socket color.",
    "paint_all_part": "Paint the entire fitted key in the original cavity-region color.",
    "paint_all_other": "Paint the entire fitted key in the other original key color.",
}
EXCLUDED_EQUIVALENT = {
    "never_swap": "Exactly the declared preserve setting, already fitted independently.",
    "swap_iff_reflected": "Exactly the declared swap setting, already fitted independently.",
}
LIMITS = {"seeds": list(SEEDS), "settings": list(SETTINGS), "episode_count": 4,
    "generated_demonstrations_per_episode": 6, "fit_demonstrations_per_episode": 2,
    "queries_per_episode": 4, "original_label_count": 5,
    "max_racket_evaluations": 1200, "max_evaluation_requests": 1600,
    "wall_seconds_checked_between_calls": 300, "racket_seconds_per_call": 10,
    "racket_startup_seconds": 30,
    "candidate_totality": "Standalone generated rivals operate on every exact ARC1..30 rectangle. Malformed/no-solution geometry returns the input; ambiguous geometry chooses its first finite assignment. Only the declared unique-placement grammar is used for intended-label claims."}


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
    if (type(value) is not dict or set(value) != {"reflection_colors"}
            or type(value["reflection_colors"]) is not str
            or value["reflection_colors"] not in ("swap", "preserve")):
        raise ValueError("Expected exactly reflection_colors=swap or preserve")
    return value["reflection_colors"]


def equivalent_aliases(settings):
    setting(settings)
    return {}


def flood(allowed, seeds):
    allowed, found, pending = set(allowed), set(), list(seeds)
    while pending:
        p = r, c = pending.pop()
        if p in found or p not in allowed:
            continue
        found.add(p)
        pending.extend(((r-1, c), (r+1, c), (r, c-1), (r, c+1)))
    return found


def groups(cells):
    pending, result = set(cells), []
    while pending:
        reached = flood(pending, [min(pending)])
        result.append(tuple(sorted(reached)))
        pending.difference_update(reached)
    return result


def edge_cell(point, edge, h, w):
    r, c = point
    return (r == 0, c == w-1, r == h-1, c == 0)[edge]


def scene(grid, name="reference"):
    grid = grid_copy(grid)
    h, w = len(grid), len(grid[0])
    counts = Counter(v for row in grid for v in row)
    bg = min(counts, key=lambda v: (-counts[v], v))
    if name == "fixed_background0":
        bg = 0
    elif name == "fixed_background1":
        bg = 1
    foreground = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v != bg}
    colors = sorted({grid[r][c] for r, c in foreground})
    anchor_groups = []
    for edge in range(4):
        for color in colors:
            allowed = {p for p in foreground if grid[p[0]][p[1]] == color}
            seeds = {p for p in allowed if edge_cell(p, edge, h, w)}
            if not seeds:
                continue
            reached = flood(allowed, seeds)
            for cells in groups(reached) if name == "component_sockets" else [tuple(sorted(reached))]:
                anchor_groups.append((edge, color, cells))
    anchored = {p for _, _, cells in anchor_groups for p in cells}
    if name == "global_color_sockets":
        anchor_groups = [(-1, color, tuple(sorted({p for _, v, cells in anchor_groups if v == color for p in cells})))
            for color in colors if any(v == color for _, v, _ in anchor_groups)]
    sockets = []
    for edge, color, cells in anchor_groups:
        r0, c0 = min(r for r, c in cells), min(c for r, c in cells)
        r1, c1 = max(r for r, c in cells), max(c for r, c in cells)
        holes = {(r, c) for r in range(r0, r1+1) for c in range(c0, c1+1)} - set(cells)
        if holes:
            sockets.append({"index": len(sockets), "edge": edge, "color": color,
                "cells": tuple(cells), "holes": tuple(sorted(holes)), "bbox": (r0, c0, r1, c1)})
    keys = []
    for cells in groups(foreground - anchored):
        palette = sorted({grid[r][c] for r, c in cells})
        if len(palette) == 2:
            keys.append({"index": len(keys), "cells": cells, "colors": palette})
    source = {p for key in keys for p in key["cells"]}
    return {"background": bg, "height": h, "width": w, "sockets": sockets,
        "keys": keys, "stationary": foreground - source}


def transformed(point, code):
    r, c = point
    return ((r, c), (c, -r), (-r, -c), (-c, r),
            (r, -c), (-c, -r), (-r, c), (c, r))[code]


def candidates(grid, info, name="reference"):
    codes = range(4) if name == "rotations_only" else range(4, 8) if name == "reflections_only" else [0] if name == "translation_only" else range(8)
    result = []
    for key in info["keys"]:
        for socket in info["sockets"]:
            holes = set(socket["holes"])
            for code in codes:
                for head in key["colors"]:
                    head_points = [transformed(p, code) for p in key["cells"] if grid[p[0]][p[1]] == head]
                    dy = min(r for r, c in holes) - min(r for r, c in head_points)
                    dx = min(c for r, c in holes) - min(c for r, c in head_points)
                    if {(r+dy, c+dx) for r, c in head_points} != holes:
                        continue
                    moved = [(transformed((r, c), code)[0]+dy, transformed((r, c), code)[1]+dx, grid[r][c])
                             for r, c in key["cells"]]
                    if name != "ignore_bounds" and any(not (0 <= r < info["height"] and 0 <= c < info["width"]) for r, c, v in moved):
                        continue
                    if name != "ignore_collision" and any((r, c) in info["stationary"] for r, c, v in moved):
                        continue
                    result.append({"key": key["index"], "socket": socket["index"], "code": code,
                        "head": head, "colors": key["colors"], "cells": moved, "translation": (dy, dx)})
    return result


def placement(info, choices):
    def search(remaining, selected, used, occupied):
        if not remaining:
            return selected
        for choice in choices:
            if choice["key"] != remaining[0]["index"] or choice["socket"] in used:
                continue
            cells = {(r, c) for r, c, _ in choice["cells"]}
            if cells & occupied:
                continue
            answer = search(remaining[1:], selected+[choice], used | {choice["socket"]}, occupied | cells)
            if answer is not None:
                return answer
        return None
    return search(info["keys"], [], set(), set())


def rival_reference(grid, settings, name):
    mode = setting(settings)
    if name not in ("reference", *RIVALS):
        raise ValueError("Unknown hypothesis: " + str(name))
    output = grid_copy(grid)
    if name == "identity":
        return output
    info = scene(grid, name)
    selected = placement(info, candidates(grid, info, name))
    if not selected:
        return output
    if name == "first_key_only":
        selected = [min(selected, key=lambda p: p["key"])]
    elif name == "largest_key_only":
        selected = [min(selected, key=lambda p: (-len(info["keys"][p["key"]]["cells"]), p["key"]))]
    elif name == "first_socket_only":
        selected = [min(selected, key=lambda p: p["socket"])]
    if name != "copy_sources":
        for part in selected:
            for r, c in info["keys"][part["key"]]["cells"]:
                output[r][c] = info["background"]
    for part in selected:
        swap = mode == "swap" and part["code"] >= 4
        if name == "always_swap":
            swap = True
        elif name == "swap_proper":
            swap = part["code"] < 4
        elif name == "swap_odd_turns":
            swap = part["code"] % 2 == 1
        elif name == "swap_by_color_order":
            swap = part["head"] == min(part["colors"])
        other = next(v for v in part["colors"] if v != part["head"])
        for r, c, color in part["cells"]:
            if name == "matching_half_only" and color != part["head"]:
                continue
            if name == "tail_only" and color == part["head"]:
                continue
            value = next(v for v in part["colors"] if v != color) if swap else color
            if name == "paint_all_anchor" or name == "paint_plug_anchor" and color == part["head"]:
                value = info["sockets"][part["socket"]]["color"]
            elif name == "paint_all_part":
                value = part["head"]
            elif name == "paint_all_other":
                value = other
            if 0 <= r < info["height"] and 0 <= c < info["width"]:
                output[r][c] = value
    return output


def reference(grid, settings):
    return rival_reference(grid, settings, "reference")


def rival_program(settings, name):
    mode = setting(settings)
    if name not in ("reference", *RIVALS):
        raise ValueError("Unknown hypothesis: " + str(name))
    if name == "identity":
        return "(rule! (lambda (g) g))"
    bg = "0" if name == "fixed_background0" else "1" if name == "fixed_background1" else "modal"
    codes = "(range 4)" if name == "rotations_only" else "(range 4 8)" if name == "reflections_only" else "'(0)" if name == "translation_only" else "(range 8)"
    anchor_groups = "(append-map (lambda (a) (map (lambda (cc) (list (first a) (second a) cc)) (components (third a)))) raw-anchors)" if name == "component_sockets" else "raw-anchors"
    if name == "global_color_sockets":
        anchor_groups = "(filter values (map (lambda (color) (let ((cells (sort (remove-duplicates (append-map third (filter (lambda (a) (= (second a) color)) raw-anchors))) point<))) (if (empty? cells) #f (list -1 color cells)))) colors))"
    bounds = "#t" if name == "ignore_bounds" else "(andmap (lambda (p) (in-bounds? (first p) (second p) h w)) moved)"
    collision = "#t" if name == "ignore_collision" else "(andmap (lambda (p) (not (member? (list (first p) (second p)) stationary))) moved)"
    select = "solution"
    if name == "first_key_only":
        select = "(list (first (sort solution (lambda (a b) (< (first a) (first b))))))"
    elif name == "largest_key_only":
        select = "(list (first (sort solution (lambda (a b) (let ((na (length (second (list-ref keys (first a))))) (nb (length (second (list-ref keys (first b)))))) (if (= na nb) (< (first a) (first b)) (> na nb)))))))"
    elif name == "first_socket_only":
        select = "(list (first (sort solution (lambda (a b) (< (second a) (second b))))))"
    clear = "g" if name == "copy_sources" else "(for/fold ((out g)) ((p (in-list selected))) (for/fold ((acc out)) ((cell (in-list (second (list-ref keys (first p)))))) (set-cell acc (first cell) (second cell) bg)))"
    swap = "(>= code 4)" if mode == "swap" else "#f"
    if name == "always_swap":
        swap = "#t"
    elif name == "swap_proper":
        swap = "(< code 4)"
    elif name == "swap_odd_turns":
        swap = "(odd? code)"
    elif name == "swap_by_color_order":
        swap = "(= head (first palette))"
    keep = "(= color head)" if name == "matching_half_only" else "(!= color head)" if name == "tail_only" else "#t"
    paint = "(if swap (if (= color (first palette)) (second palette) (first palette)) color)"
    if name == "paint_plug_anchor":
        paint = f"(if (= color head) (second (list-ref sockets (second p))) {paint})"
    elif name == "paint_all_anchor":
        paint = "(second (list-ref sockets (second p)))"
    elif name == "paint_all_part":
        paint = "head"
    elif name == "paint_all_other":
        paint = "(if (= head (first palette)) (second palette) (first palette))"
    template = r'''(rule! (let ()
  (define (point< a b) (or (< (first a) (first b)) (and (= (first a) (first b)) (< (second a) (second b)))))
  (define (neighbors p) (let ((r (first p)) (c (second p))) (list (list (- r 1) c) (list (+ r 1) c) (list r (- c 1)) (list r (+ c 1)))))
  (define (flood allowed starts)
    (let loop ((todo starts) (seen '()))
      (if (empty? todo) (sort seen point<)
        (let ((p (first todo)))
          (if (or (member? p seen) (not (member? p allowed))) (loop (rest todo) seen)
            (loop (append (neighbors p) (rest todo)) (cons p seen)))))))
  (define (components cells)
    (let loop ((remaining (sort cells point<)) (answer '()))
      (if (empty? remaining) (reverse answer)
        (let ((cc (flood remaining (list (first remaining)))))
          (loop (filter (lambda (p) (not (member? p cc))) remaining) (cons cc answer))))))
  (define positions (grid-positions g))
  (define modal (for/fold ((best 0)) ((color (in-range 1 10)))
    (if (> (count (lambda (p) (= (at g (first p) (second p)) color)) positions)
           (count (lambda (p) (= (at g (first p) (second p)) best)) positions)) color best)))
  (define bg @BG@)
  (define foreground (filter (lambda (p) (!= (at g (first p) (second p)) bg)) positions))
  (define colors (sort (remove-duplicates (map (lambda (p) (at g (first p) (second p))) foreground)) <))
  (define (edge? p e) (case e ((0) (= (first p) 0)) ((1) (= (second p) (- w 1))) ((2) (= (first p) (- h 1))) (else (= (second p) 0))))
  (define raw-anchors
    (filter values (for*/list ((edge (in-range 4)) (color (in-list colors)))
      (let* ((allowed (filter (lambda (p) (= (at g (first p) (second p)) color)) foreground))
             (seeds (filter (lambda (p) (edge? p edge)) allowed)))
        (if (empty? seeds) #f (list edge color (flood allowed seeds)))))))
  (define anchored (remove-duplicates (append-map third raw-anchors)))
  (define anchors @ANCHORS@)
  (define sockets
    (filter values (map (lambda (a)
      (let* ((cells (third a)) (bb (bbox-of-cells cells))
             (holes (filter (lambda (p) (not (member? p cells)))
               (for*/list ((r (in-range (first bb) (+ 1 (third bb)))) (c (in-range (second bb) (+ 1 (fourth bb))))) (list r c)))))
        (if (empty? holes) #f (list (first a) (second a) cells holes bb)))) anchors)))
  (define raw-keys (filter (lambda (cc) (= 2 (length (remove-duplicates (map (lambda (p) (at g (first p) (second p))) cc)))))
    (components (filter (lambda (p) (not (member? p anchored))) foreground))))
  (define keys (for/list ((cc (in-list raw-keys)) (i (in-naturals)))
    (list i cc (sort (remove-duplicates (map (lambda (p) (at g (first p) (second p))) cc)) <))))
  (define source (append-map second keys))
  (define stationary (filter (lambda (p) (not (member? p source))) foreground))
  (define (transform p code)
    (let ((r (first p)) (c (second p)))
      (list-ref (list (list r c) (list c (- r)) (list (- r) (- c)) (list (- c) r)
        (list r (- c)) (list (- c) (- r)) (list (- r) c) (list c r)) code)))
  (define choices
    (filter values (for*/list ((key (in-list keys)) (si (in-range (length sockets))) (code (in-list @CODES@)) (head (in-list (third key))))
      (let* ((socket (list-ref sockets si)) (holes (fourth socket))
             (head-points (map (lambda (p) (transform p code)) (filter (lambda (p) (= (at g (first p) (second p)) head)) (second key))))
             (dy (- (apply min (map first holes)) (apply min (map first head-points))))
             (dx (- (apply min (map second holes)) (apply min (map second head-points))))
             (shifted (sort (map (lambda (p) (list (+ dy (first p)) (+ dx (second p)))) head-points) point<))
             (moved (map (lambda (p) (let ((q (transform p code))) (list (+ dy (first q)) (+ dx (second q)) (at g (first p) (second p))))) (second key))))
        (if (and (equal? shifted (sort holes point<)) @BOUNDS@ @COLLISION@)
          (list (first key) si code head (third key) moved) #f)))))
  (define (search remaining selected used occupied)
    (if (empty? remaining) (reverse selected)
      (let loop ((options (filter (lambda (p) (= (first p) (first (first remaining)))) choices)))
        (if (empty? options) #f
          (let* ((p (first options)) (cells (map (lambda (v) (list (first v) (second v))) (list-ref p 5))))
            (if (or (member? (second p) used) (ormap (lambda (v) (member? v occupied)) cells)) (loop (rest options))
              (let ((answer (search (rest remaining) (cons p selected) (cons (second p) used) (append cells occupied))))
                (if answer answer (loop (rest options))))))))))
  (define solution (search keys '() '() '()))
  (if (or (not solution) (empty? solution)) g
    (let* ((selected @SELECT@) (cleared @CLEAR@))
      (for/fold ((out cleared)) ((p (in-list selected)))
        (let* ((code (third p)) (head (fourth p)) (palette (list-ref p 4)) (swap @SWAP@))
          (for/fold ((acc out)) ((cell (in-list (list-ref p 5))))
            (let ((r (first cell)) (c (second cell)) (color (third cell)))
              (if (and @KEEP@ (in-bounds? r c h w)) (set-cell acc r c @PAINT@) acc)))))))))'''
    for key, value in {"BG": bg, "ANCHORS": anchor_groups, "CODES": codes,
            "BOUNDS": bounds, "COLLISION": collision, "SELECT": select,
            "CLEAR": clear, "SWAP": swap, "KEEP": keep, "PAINT": paint}.items():
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
    spec = importlib.util.spec_from_file_location("_public_eval_a25697e4_frozen_native_audit", HOME / "native_family.py")
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
    parts = scene(grid)
    plan = placement(parts, candidates(grid, parts)) or []
    return {"input_shape": [len(grid), len(grid[0])],
        "output_shape": [len(output), len(output[0])],
        "background": parts["background"], "socket_count": len(parts["sockets"]),
        "key_count": len(parts["keys"]),
        "placement_parities": ["reflected" if p["code"] >= 4 else "proper" for p in plan],
        "input_occupied": sum(v != parts["background"] for row in grid for v in row),
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
    report = {"schema": "public-eval-a25697e4-independent-teaching-audit-v1", "status": "running",
              "task_id": TASK_ID, "assignment_id": ASSIGNMENT_ID,
              "source_files_sha256_before": binding, "runtime_files_sha256_before": runtime_before,
              "limits": deepcopy(LIMITS), "rival_meanings": RIVAL_MEANINGS,
              "excluded_equivalent_hypotheses": EXCLUDED_EQUIVALENT,
              "episodes": [], "findings": [], "reference_label_count": 0, "original_label_count": 0,
              "visibility": "controller_private", "training_admitted": False,
              "scope": "Four episodes only; all6+4 generated labels plus all five official labels checked independently. Exactly first2 demos determine survivors, then every survivor receives all4 query scores. No universal identifiability, owner acceptance, or training admission."}
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
                        candidates = [("declared:reflection_colors=" + other["reflection_colors"], family.program(other),
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
                        intended_name = "declared:reflection_colors=" + mode
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


