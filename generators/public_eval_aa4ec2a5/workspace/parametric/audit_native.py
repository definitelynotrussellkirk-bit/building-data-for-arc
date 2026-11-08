"""Independent padded-flood audit of component-local cavities and outlines.

The oracle independently floods a virtual one-cell pad around each foreground
component. Shared-domain checks exclude diagonal component contacts and nested
foreground under four-connectivity. Runtime and ledger bookkeeping alone are
explicit source copies; no previous runtime, environment or receipts are used.
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
TASK_ID = "public_eval_aa4ec2a5"
PARENT_ID = "aa4ec2a5"
ASSIGNMENT_ID = "review-08f305aef7d53dae"
sys.path[:0] = [str(ROOT / "src"), str(RUNTIME)]
from arcpuzzles.parametric_worker import _local_imports, _real_evaluator

SETTINGS = ({"hole_connectivity": 4}, {"hole_connectivity": 8})
SEEDS = (0, 17, 15)
RIVALS = (
    "identity", "invert_roles", "fixed_background4", "fixed_foreground1",
    "bbox_cavities", "global_bbox_cavities", "largest_component_only", "first_component_only",
    "largest_hole_only", "singleton_holes_only", "deep_hole_border_only", "outline4",
    "outline_radius2", "outline_bbox", "outline_holes_too", "no_outline", "no_fill",
    "no_recolor", "recolor_all", "recolor_near_holes", "only_holed_outline",
    "only_solid_outline", "swap_hole_body_colors", "fill_same_as_body", "crop_result",
)
RIVAL_MEANINGS = {
    "identity": "Return unchanged input.",
    "invert_roles": "Treat the modal background as foreground and the other input color as background.",
    "fixed_background4": "Assume background4; return input if color4 is absent.",
    "fixed_foreground1": "Assume foreground1; return input if color1 is absent.",
    "bbox_cavities": "Treat every missing cell inside each component bounding box as a cavity, including open concavities.",
    "global_bbox_cavities": "Treat all foreground as one object and every gap in its bounding box as a cavity.",
    "largest_component_only": "Classify, fill and outline only the largest foreground component; ties use occupied-anchor order.",
    "first_component_only": "Classify, fill and outline only the first component in row-major order.",
    "largest_hole_only": "Retain only the largest cavity per component; discarded cavities are subsequently treated as exterior.",
    "singleton_holes_only": "Recognize only one-cell cavity regions.",
    "deep_hole_border_only": "Fill only cavity cells within Chebyshev distance1 of original foreground, leaving deep cavity centers unchanged.",
    "outline4": "Use a four-neighbor external outline instead of an eight-neighbor outline.",
    "outline_radius2": "Use a two-cell Chebyshev external outline.",
    "outline_bbox": "Outline bounding rectangles rather than actual filled component supports.",
    "outline_holes_too": "Outline raw foreground on both sides, painting inner cavity boundaries2 over their fill.",
    "no_outline": "Classify and fill cavities without adding an outline.",
    "no_fill": "Recolor hollow components and outline them but leave their cavities in the input background color.",
    "no_recolor": "Fill cavities and outline objects but retain all original foreground colors.",
    "recolor_all": "Recolor all foreground8, including solid components.",
    "recolor_near_holes": "Recolor only foreground cells within Chebyshev distance1 of a cavity.",
    "only_holed_outline": "Outline only hollow components.",
    "only_solid_outline": "Outline only solid components.",
    "swap_hole_body_colors": "Use body6 and cavity8 instead of body8 and cavity6.",
    "fill_same_as_body": "Use color8 for both hollow foreground and cavity fill.",
    "crop_result": "Crop the final non-background content instead of preserving the canvas.",
}
for _color in range(10):
    RIVAL_MEANINGS.setdefault(f"fixed_background{_color}", f"Assume background color {_color}; return input when that color is absent.")
    RIVAL_MEANINGS.setdefault(f"fixed_foreground{_color}", f"Assume foreground color {_color}; return input when that color is absent.")
EXCLUDED_EQUIVALENT = {
    "force_connectivity4": "Already represented by the declared four-connectivity setting.",
    "force_connectivity8": "Already represented by the declared eight-connectivity setting.",
    "foreground_connectivity8": "The admitted separation rule excludes eight-neighbor contact between distinct four-connected foreground components, so this cannot change their grouping.",
    "raw_foreground_outline_with_cavities_masked": "For an enclosed component cavity, external one-cell dilation is unchanged when filled cavity cells are included; correct cavity masking gives the same outline.",
}
LIMITS = {"seeds": list(SEEDS), "settings": list(SETTINGS), "episode_count": 6,
    "generated_demonstrations_per_episode": 6, "fit_demonstrations_per_episode": 2,
    "queries_per_episode": 4, "original_label_count": 4,
    "max_racket_evaluations": 1200, "max_evaluation_requests": 1600,
    "wall_seconds_checked_between_calls": 300, "racket_seconds_per_call": 10,
    "racket_startup_seconds": 30,
    "candidate_totality": "All standalone rivals return the input on exact ARC rectangles outside the shared binary/separation grammar. Inside that grammar every rival deterministically returns an exact ARC grid; missing assumed colors also produce identity."}
LIMITS["learned_role_candidates"] = "Instantiate background and foreground constants from demonstration0 input only; deduplicate them against the fixed bank and fit them on demonstrations0–1."


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
    if (type(value) is not dict or set(value) != {"hole_connectivity"}
            or type(value["hole_connectivity"]) is not int
            or value["hole_connectivity"] not in (4, 8)):
        raise ValueError("Expected exactly hole_connectivity=4 or8")
    return value["hole_connectivity"]


def equivalent_aliases(settings):
    setting(settings)
    return {}


def role_constant(name):
    if type(name) is str:
        for prefix in ("fixed_background", "fixed_foreground"):
            suffix = name[len(prefix):] if name.startswith(prefix) else ""
            if suffix in tuple(str(v) for v in range(10)):
                return prefix, int(suffix)
    return None


def learned_role_names(demonstrations):
    if not demonstrations:
        raise ValueError("Need demonstration0 input to instantiate learned colors")
    info = scene(demonstrations[0]["input"], 4)
    return [f"fixed_background{info['background']}", f"fixed_foreground{info['foreground']}"]


def offsets(connectivity=8, radius=1):
    return [(dr, dc) for dr in range(-radius, radius+1) for dc in range(-radius, radius+1)
            if (dr or dc) and (connectivity == 8 or abs(dr)+abs(dc) <= radius)]


def components(cells, connectivity=4):
    remaining, result = set(cells), []
    steps = offsets(connectivity)
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        pending, reached = [start], {start}
        while pending:
            r, c = pending.pop()
            for dr, dc in steps:
                p = r+dr, c+dc
                if p in remaining:
                    remaining.remove(p)
                    pending.append(p)
                    reached.add(p)
        result.append(tuple(sorted(reached)))
    return result


def box(cells):
    return min(r for r, c in cells), min(c for r, c in cells), max(r for r, c in cells), max(c for r, c in cells)


def rectangle(cells):
    r0, c0, r1, c1 = box(cells)
    return {(r, c) for r in range(r0, r1+1) for c in range(c0, c1+1)}


def padded_holes(cells, connectivity):
    cells = set(cells)
    r0, c0, r1, c1 = box(cells)
    allowed = {(r, c) for r in range(r0-1, r1+2) for c in range(c0-1, c1+2)} - cells
    pending, exterior = [(r0-1, c0-1)], set()
    steps = offsets(connectivity)
    while pending:
        p = r, c = pending.pop()
        if p not in allowed or p in exterior:
            continue
        exterior.add(p)
        pending.extend((r+dr, c+dc) for dr, dc in steps)
    return allowed - exterior


def dilate(cells, connectivity=8, radius=1):
    steps = [(0, 0), *offsets(connectivity, radius)]
    return {(r+dr, c+dc) for r, c in cells for dr, dc in steps}


def analyze(grid, bg, fg, connectivity):
    source = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == fg}
    objects = [{"cells": set(cc), "holes": padded_holes(cc, connectivity)} for cc in components(source)]
    return {"background": bg, "foreground": fg, "source": source, "objects": objects}


def scene(grid, connectivity):
    setting({"hole_connectivity": connectivity})
    grid = grid_copy(grid)
    counts = Counter(v for row in grid for v in row)
    if len(counts) != 2 or set(counts) & {2, 6, 8} or len(set(counts.values())) != 2:
        raise ValueError("Need two admitted colors and a unique modal background")
    bg = max(counts, key=counts.get)
    fg = next(v for v in counts if v != bg)
    info = analyze(grid, bg, fg, connectivity)
    labels = {p: i for i, obj in enumerate(info["objects"]) for p in obj["cells"]}
    for (r, c), i in labels.items():
        if any((r+dr, c+dc) in labels and labels[(r+dr, c+dc)] != i for dr, dc in offsets(8)):
            raise ValueError("Distinct foreground components may not touch diagonally")
    for obj in info["objects"]:
        if padded_holes(obj["cells"], 4) & info["source"]:
            raise ValueError("Foreground may not be nested in another component cavity")
    return info


def rival_reference(grid, settings, name):
    connectivity = setting(settings)
    constant = role_constant(name)
    if name not in ("reference", *RIVALS) and constant is None:
        raise ValueError("Unknown hypothesis: " + str(name))
    grid = grid_copy(grid)
    if name == "identity":
        return grid
    try:
        info = scene(grid, connectivity)
    except ValueError:
        return grid
    bg, fg = info["background"], info["foreground"]
    if name == "invert_roles":
        bg, fg = fg, bg
    elif constant is not None and constant[0] == "fixed_background":
        color = constant[1]
        if color not in (bg, fg):
            return grid
        bg, fg = color, next(v for v in (bg, fg) if v != color)
    elif constant is not None and constant[0] == "fixed_foreground":
        color = constant[1]
        if color not in (bg, fg):
            return grid
        bg, fg = next(v for v in (bg, fg) if v != color), color
    if (bg, fg) != (info["background"], info["foreground"]):
        info = analyze(grid, bg, fg, connectivity)
    objects = deepcopy(info["objects"])
    if name == "global_bbox_cavities":
        objects = [{"cells": set(info["source"]), "holes": rectangle(info["source"]) - info["source"]}]
    elif name == "first_component_only":
        objects = objects[:1]
    elif name == "largest_component_only":
        objects = [min(objects, key=lambda o: (-len(o["cells"]), min(o["cells"])))]
    for obj in objects:
        if name == "bbox_cavities":
            obj["holes"] = rectangle(obj["cells"]) - obj["cells"]
        elif name in ("largest_hole_only", "singleton_holes_only"):
            regions = components(obj["holes"], connectivity)
            if name == "largest_hole_only":
                obj["holes"] = set(min(regions, key=lambda cc: (-len(cc), cc[0]))) if regions else set()
            else:
                obj["holes"] = {p for cc in regions if len(cc) == 1 for p in cc}
    selected_source = {p for obj in objects for p in obj["cells"]}
    cavities = {p for obj in objects for p in obj["holes"]}
    holed = {p for obj in objects if obj["holes"] for p in obj["cells"]}
    support = selected_source | cavities
    if name == "no_recolor":
        holed = set()
    elif name == "recolor_all":
        holed = set(info["source"])
    elif name == "recolor_near_holes":
        holed = info["source"] & dilate(cavities)
    eligible = support
    if name in ("only_holed_outline", "only_solid_outline"):
        eligible = {p for obj in objects if bool(obj["holes"]) == (name == "only_holed_outline") for p in obj["cells"] | obj["holes"]}
    rim = dilate(eligible, 4 if name == "outline4" else 8, 2 if name == "outline_radius2" else 1) - support
    if name == "no_outline":
        rim = set()
    elif name == "outline_bbox":
        rim = {p for obj in objects for p in dilate(rectangle(obj["cells"])) - rectangle(obj["cells"])} - support
    elif name == "outline_holes_too":
        rim = dilate(selected_source) - selected_source
    near = dilate(selected_source)
    result = deepcopy(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            p = r, c
            if p in info["source"]:
                result[r][c] = (6 if name == "swap_hole_body_colors" else 8) if p in holed else fg
            elif name == "outline_holes_too" and p in rim:
                result[r][c] = 2
            elif p in cavities:
                if name == "no_fill" or name == "deep_hole_border_only" and p not in near:
                    result[r][c] = bg
                else:
                    result[r][c] = 8 if name in ("swap_hole_body_colors", "fill_same_as_body") else 6
            elif p in rim:
                result[r][c] = 2
            else:
                result[r][c] = bg
    if name == "crop_result":
        occupied = [(r, c) for r, row in enumerate(result) for c, v in enumerate(row) if v != bg]
        if not occupied:
            return [[0]]
        r0, c0, r1, c1 = box(occupied)
        result = [row[c0:c1+1] for row in result[r0:r1+1]]
    return result


def reference(grid, settings):
    return rival_reference(grid, settings, "reference")


def rival_program(settings, name):
    connectivity = setting(settings)
    constant = role_constant(name)
    if name not in ("reference", *RIVALS) and constant is None:
        raise ValueError("Unknown hypothesis: " + str(name))
    if name == "identity":
        return "(rule! (lambda (g) g))"
    role_guard, vbg, vfg = "#t", "bg", "fg"
    if name == "invert_roles":
        vbg, vfg = "fg", "bg"
    elif constant is not None and constant[0] == "fixed_background":
        color = constant[1]
        role_guard, vbg, vfg = f"(member? {color} palette)", str(color), f"(if (= bg {color}) fg bg)"
    elif constant is not None and constant[0] == "fixed_foreground":
        color = constant[1]
        role_guard, vbg, vfg = f"(member? {color} palette)", f"(if (= fg {color}) bg fg)", str(color)
    chosen = "vobjects"
    if name == "global_bbox_cavities":
        chosen = "(list vsource)"
    elif name == "first_component_only":
        chosen = "(list (first vobjects))"
    elif name == "largest_component_only":
        chosen = "(list (first (sort vobjects (lambda (a b) (if (= (length a) (length b)) (point< (first a) (first b)) (> (length a) (length b)))))))"
    hole_expression = f"(holes cells {connectivity})"
    if name in ("bbox_cavities", "global_bbox_cavities"):
        hole_expression = "(filter (lambda (p) (not (member? p cells))) (rectangle cells))"
    elif name == "largest_hole_only":
        hole_expression = f"(let ((parts (regions (holes cells {connectivity}) {connectivity}))) (if (empty? parts) '() (first (sort parts (lambda (a b) (if (= (length a) (length b)) (point< (first a) (first b)) (> (length a) (length b))))))))"
    elif name == "singleton_holes_only":
        hole_expression = f"(append-map values (filter (lambda (cc) (= (length cc) 1)) (regions (holes cells {connectivity}) {connectivity})))"
    body = "holed-cells"
    if name == "no_recolor":
        body = "'()"
    elif name == "recolor_all":
        body = "vsource"
    elif name == "recolor_near_holes":
        body = "(filter (lambda (p) (member? p (dilate cavities 8 1))) vsource)"
    eligible = "support"
    if name in ("only_holed_outline", "only_solid_outline"):
        predicate = "(not (empty? (second o)))" if name == "only_holed_outline" else "(empty? (second o))"
        eligible = f"(remove-duplicates (append-map (lambda (o) (append (first o) (second o))) (filter (lambda (o) {predicate}) classified)))"
    rim = f"(filter (lambda (p) (not (member? p support))) (dilate eligible {4 if name == 'outline4' else 8} {2 if name == 'outline_radius2' else 1}))"
    if name == "no_outline":
        rim = "'()"
    elif name == "outline_bbox":
        rim = "(filter (lambda (p) (not (member? p support))) (remove-duplicates (append-map (lambda (o) (let ((rect (rectangle (first o)))) (filter (lambda (p) (not (member? p rect))) (dilate rect 8 1)))) classified)))"
    elif name == "outline_holes_too":
        rim = "(filter (lambda (p) (not (member? p selected-source))) (dilate selected-source 8 1))"
    body_color = "6" if name == "swap_hole_body_colors" else "8"
    fill = "8" if name in ("swap_hole_body_colors", "fill_same_as_body") else "6"
    if name == "no_fill":
        fill = "vbg"
    elif name == "deep_hole_border_only":
        fill = "(if (member? p near-source) 6 vbg)"
    inner_priority = "((member? p rim) 2)" if name == "outline_holes_too" else ""
    finish = "result"
    if name == "crop_result":
        finish = "(let ((points (filter (lambda (p) (!= (at result (first p) (second p)) vbg)) (grid-positions result)))) (if (empty? points) '((0)) (let ((b (bbox-of-cells points))) (subgrid result (first b) (second b) (third b) (fourth b)))))"
    template = r'''(rule! (let ()
  (define (point< a b) (or (< (first a) (first b)) (and (= (first a) (first b)) (< (second a) (second b)))))
  (define (neighbors p conn radius)
    (for*/list ((dr (in-range (- radius) (+ radius 1))) (dc (in-range (- radius) (+ radius 1)))
                #:when (and (or (!= dr 0) (!= dc 0)) (or (= conn 8) (<= (+ (abs dr) (abs dc)) radius))))
      (list (+ (first p) dr) (+ (second p) dc))))
  (define (dilate cells conn radius) (remove-duplicates (append cells (append-map (lambda (p) (neighbors p conn radius)) cells))))
  (define (flood allowed starts conn)
    (let loop ((pending starts) (seen '()))
      (if (empty? pending) seen
        (let ((p (first pending)))
          (if (or (member? p seen) (not (member? p allowed))) (loop (rest pending) seen)
            (loop (append (neighbors p conn 1) (rest pending)) (cons p seen)))))))
  (define (regions cells conn)
    (let loop ((left (sort cells point<)) (answer '()))
      (if (empty? left) (reverse answer)
        (let ((found (sort (flood left (list (first left)) conn) point<)))
          (loop (filter (lambda (p) (not (member? p found))) left) (cons found answer))))))
  (define (rectangle cells)
    (let ((b (bbox-of-cells cells)))
      (for*/list ((r (in-range (first b) (+ 1 (third b)))) (c (in-range (second b) (+ 1 (fourth b))))) (list r c))))
  (define (holes cells conn)
    (let* ((b (bbox-of-cells cells))
           (allowed (filter (lambda (p) (not (member? p cells)))
             (for*/list ((r (in-range (- (first b) 1) (+ (third b) 2))) (c (in-range (- (second b) 1) (+ (fourth b) 2)))) (list r c))))
           (outside (flood allowed (list (list (- (first b) 1) (- (second b) 1))) conn)))
      (filter (lambda (p) (not (member? p outside))) allowed)))
  (define positions (grid-positions g))
  (define palette (sort (remove-duplicates (map (lambda (p) (at g (first p) (second p))) positions)) <))
  (define (frequency color) (count (lambda (p) (= (at g (first p) (second p)) color)) positions))
  (define (foreground-objects color)
    (sort (map (lambda (o) (sort (obj-cells o) point<))
      (objects (grid-from-fn h w (lambda (r c) (if (= (at g r c) color) 1 0))) 0))
      (lambda (a b) (point< (first a) (first b)))))
  (if (or (!= (length palette) 2) (ormap (lambda (v) (member? v '(2 6 8))) palette)) g
    (if (= (frequency (first palette)) (frequency (second palette))) g
      (let* ((bg (if (> (frequency (first palette)) (frequency (second palette))) (first palette) (second palette)))
             (fg (if (= bg (first palette)) (second palette) (first palette)))
             (source (find-color g fg)) (raw-objects (foreground-objects fg))
             (classified4 (map (lambda (cells) (list cells (holes cells 4))) raw-objects))
             (separated (andmap (lambda (a) (andmap (lambda (b)
               (or (equal? a b) (not (ormap (lambda (p) (member? p (dilate b 8 1))) a)))) raw-objects)) raw-objects))
             (unnested (andmap (lambda (o) (not (ormap (lambda (p) (member? p source)) (second o)))) classified4)))
        (if (not (and separated unnested @ROLE_GUARD@)) g
          (let* ((vbg @VBG@) (vfg @VFG@) (vsource (find-color g vfg))
                 (vobjects (if (= vfg fg) raw-objects (foreground-objects vfg)))
                 (chosen @CHOSEN@)
                 (classified (map (lambda (cells) (list cells @HOLES@)) chosen))
                 (selected-source (remove-duplicates (append-map first classified)))
                 (cavities (remove-duplicates (append-map second classified)))
                 (holed-cells (remove-duplicates (append-map first (filter (lambda (o) (not (empty? (second o)))) classified))))
                 (support (remove-duplicates (append selected-source cavities)))
                 (body @BODY@) (eligible @ELIGIBLE@) (rim @RIM@)
                 (near-source (dilate selected-source 8 1))
                 (result (grid-from-fn h w (lambda (r c)
                   (let ((p (list r c)))
                     (cond ((member? p vsource) (if (member? p body) @BODY_COLOR@ vfg))
                       @INNER_PRIORITY@
                       ((member? p cavities) @FILL@) ((member? p rim) 2) (else vbg)))))))
            @FINISH@)))))))'''
    values = {"ROLE_GUARD": role_guard, "VBG": vbg, "VFG": vfg, "CHOSEN": chosen,
        "HOLES": hole_expression, "BODY": body, "ELIGIBLE": eligible, "RIM": rim,
        "BODY_COLOR": body_color, "FILL": fill, "INNER_PRIORITY": inner_priority, "FINISH": finish}
    for key, value in values.items():
        template = template.replace("@"+key+"@", value)
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
    spec = importlib.util.spec_from_file_location("_public_eval_aa4ec2a5_frozen_native_audit", HOME / "native_family.py")
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
    four, eight = scene(grid, 4), scene(grid, 8)
    return {"input_shape": [len(grid), len(grid[0])], "output_shape": [len(output), len(output[0])],
        "background": four["background"], "foreground": four["foreground"],
        "component_sizes": [len(o["cells"]) for o in four["objects"]],
        "cavity_areas4": [len(o["holes"]) for o in four["objects"]],
        "cavity_areas8": [len(o["holes"]) for o in eight["objects"]],
        "input_occupied": len(four["source"]),
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
    report = {"schema": "public-eval-aa4ec2a5-independent-teaching-audit-v1", "status": "running",
              "task_id": TASK_ID, "assignment_id": ASSIGNMENT_ID,
              "source_files_sha256_before": binding, "runtime_files_sha256_before": runtime_before,
              "limits": deepcopy(LIMITS), "rival_meanings": RIVAL_MEANINGS,
              "excluded_equivalent_hypotheses": EXCLUDED_EQUIVALENT,
              "episodes": [], "findings": [], "reference_label_count": 0, "original_label_count": 0,
              "visibility": "controller_private", "training_admitted": False,
              "scope": "Six episodes only; all6+4 generated labels plus all four official labels checked independently. Learned color constants read demonstration0 input only; exactly first2 demos determine survivors, then every survivor receives all4 query scores. No universal identifiability, owner acceptance, or training admission."}
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
                        candidates = [("declared:hole_connectivity=" + str(other["hole_connectivity"]), family.program(other),
                                       lambda grid, other=other: reference(grid, other)) for other in SETTINGS]
                        learned = learned_role_names(train[:1])
                        rival_names = list(dict.fromkeys((*RIVALS, *learned)))
                        candidates += [(name, rival_program(settings, name),
                                        lambda grid, name=name: rival_reference(grid, settings, name)) for name in rival_names]
                        row = {"seed": seed, "settings": deepcopy(settings), "train": train, "test": test,
                               "fit_demo_indices": [0, 1], "label_checks": [], "hypotheses": [],
                               "learned_role_candidates": learned, "learned_role_input_demo_index": 0}
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
                        intended_name = "declared:hole_connectivity=" + str(mode)
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


