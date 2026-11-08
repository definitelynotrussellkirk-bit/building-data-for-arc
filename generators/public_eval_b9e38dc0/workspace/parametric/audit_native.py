"""Independent complement-flood audit of stepped nozzle filling and shadows.

The Python geometry is an explicit, adapted source copy of the current packet's
independent design probe. It does not import production semantics. Runtime and
ledger bookkeeping is explicitly source-copied from the completed first target;
all executions, source snapshots, identities and receipts are fresh.
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
TASK_ID = "public_eval_b9e38dc0"
PARENT_ID = "b9e38dc0"
ASSIGNMENT_ID = "review-08f305aef7d53dae"
sys.path[:0] = [str(ROOT / "src"), str(RUNTIME)]
from arcpuzzles.parametric_worker import _local_imports, _real_evaluator

SETTINGS = ({"obstacle_mode": "opaque"}, {"obstacle_mode": "transparent"})
SEEDS = (0, 17, 1)
RIVALS = (
    "identity", "body_only", "outlet_only", "stride1", "stride2", "freeze_rails",
    "include_virtual_rails", "symmetric_mouth_only", "largest_dye", "minimum_dye",
    "first_scan_dye", "global_shadows", "wall_shadows", "whole_cross_section_shadow",
    "slanted_shadows", "backward_shadows", "overwrite_blockers", "one_blocker_color",
    "source_as_blocker", "crop_result",
)
RIVAL_MEANINGS = {
    "identity": "Leave the input unchanged.",
    "body_only": "Fill only through the later of the two mouth tips; omit the projected outlet.",
    "outlet_only": "Fill only beyond both tips; omit the reservoir and throat.",
    "stride1": "Project both rails with one forward cell per outward step, regardless of the observed cadence.",
    "stride2": "Project both rails with two forward cells per outward step, regardless of the observed cadence.",
    "freeze_rails": "Extend each terminal rail parallel to the flow instead of continuing its outward slope.",
    "include_virtual_rails": "Fill the virtual projected boundary pixels as well as the strict interior.",
    "symmetric_mouth_only": "Assume both tips lie at the same forward station; otherwise return the unchanged input.",
    "largest_dye": "Use the most frequent non-background, non-wall color globally; resolve ties by smallest numeric color.",
    "minimum_dye": "Use the smallest numeric non-background, non-wall color globally.",
    "first_scan_dye": "Use the first non-background, non-wall color in original canvas row-major order.",
    "global_shadows": "Let every foreign marker cast a parallel forward shadow, including markers outside the inferred band.",
    "wall_shadows": "Let observed wall pixels also cast forward shadows into the widened band.",
    "whole_cross_section_shadow": "Stop all transverse rays after the earliest in-band blocker anywhere.",
    "slanted_shadows": "Move each shadow one transverse cell right per forward cell, instead of keeping it parallel to the flow.",
    "backward_shadows": "Cast same-column shadows backward toward the cap rather than forward.",
    "overwrite_blockers": "Paint reachable foreign marker cells with dye instead of preserving their colors.",
    "one_blocker_color": "Only the numerically smallest in-band foreign color casts shadows.",
    "source_as_blocker": "Treat dye seed cells as opaque blockers as well as other in-band markers.",
    "crop_result": "Crop the completed result to all non-background content instead of retaining the canvas.",
}
for _role in ("background", "wall", "dye"):
    for _color in range(10):
        RIVAL_MEANINGS[f"fixed_{_role}{_color}"] = (
            f"Assume {_role} color {_color}; apply the complete inferred rule only when that role matches, otherwise return the input.")
for _turns, _direction in enumerate(("down", "right", "up", "left")):
    RIVAL_MEANINGS[f"fixed_flow{_turns}"] = (
        f"Assume flow points {_direction} (normalization turns={_turns}); apply the complete rule only for that inferred flow, otherwise return the input.")
SHADOW_ONLY = ("global_shadows", "wall_shadows", "whole_cross_section_shadow",
               "slanted_shadows", "backward_shadows", "one_blocker_color", "source_as_blocker")
EXCLUDED_EQUIVALENT = {
    "ignore_all_shadows": "Already represented by the declared transparent setting.",
    "force_ordinary_shadows": "Already represented by the declared opaque setting.",
}
LIMITS = {"seeds": list(SEEDS), "settings": list(SETTINGS), "episode_count": 6,
    "generated_demonstrations_per_episode": 6, "fit_demonstrations_per_episode": 2,
    "queries_per_episode": 4, "original_label_count": 4,
    "max_racket_evaluations": 1200, "max_evaluation_requests": 1600,
    "wall_seconds_checked_between_calls": 300, "racket_seconds_per_call": 10,
    "racket_startup_seconds": 30,
    "candidate_totality": "Every complete Racket candidate first checks the shared nozzle grammar; non-domain exact ARC rectangles produce identity. The checked candidate body runs outside the domain-check exception handler, so valid-domain execution failures remain audit errors.",
    "learned_role_candidates": "Learn background, wall, dye and normalization-flow constants from demonstration0 input only; fit only demonstrations0–1.",
    "partial_terminal_runs": "Excluded: both complete terminal and immediately preceding inward runs must have equal positive length, shared by both rails."}


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
    if (type(value) is not dict or set(value) != {"obstacle_mode"}
            or type(value["obstacle_mode"]) is not str
            or value["obstacle_mode"] not in ("opaque", "transparent")):
        raise ValueError("Expected exactly obstacle_mode=opaque or transparent")
    return value["obstacle_mode"]


def equivalent_aliases(settings):
    if setting(settings) != "transparent":
        return {}
    return {name: "Equivalent on every admitted input under transparent mode: only blocker/frontier or shadow calculations change, and rendering ignores shadows when opaque is false."
            for name in SHADOW_ONLY}


def role_constant(name):
    if type(name) is str:
        for role in ("background", "wall", "dye"):
            prefix = "fixed_" + role
            suffix = name[len(prefix):] if name.startswith(prefix) else ""
            if suffix in tuple(str(v) for v in range(10)):
                return role, int(suffix)
    return None


def flow_constant(name):
    if type(name) is str and name in tuple(f"fixed_flow{v}" for v in range(4)):
        return int(name[-1])
    return None


def learned_role_names(demonstrations):
    if not demonstrations:
        raise ValueError("Need demonstration0 input to instantiate learned colors")
    info = scene(demonstrations[0]["input"])
    return [f"fixed_background{info['background']}", f"fixed_wall{info['wall']}",
            f"fixed_dye{info['dye']}", f"fixed_flow{info['turns']}"]


FOUR = ((-1, 0), (1, 0), (0, -1), (0, 1))
EIGHT = tuple((dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if dr or dc)


def need(condition, message):
    if not condition:
        raise ValueError(message)


def component(allowed, start):
    found, pending = {start}, [start]
    while pending:
        r, c = pending.pop()
        for dr, dc in FOUR:
            p = r + dr, c + dc
            if p in allowed and p not in found:
                found.add(p)
                pending.append(p)
    return found


def rotate(grid, turns=1):
    for _ in range(turns % 4):
        grid = [list(row) for row in zip(*grid[::-1])]
    return grid


def wall_data(grid):
    counts = Counter(v for row in grid for v in row)
    ranked = counts.most_common()
    need(len(ranked) >= 3 and ranked[0][1] > ranked[1][1] > ranked[2][1],
         "Need unique modal background and unique most-frequent wall")
    bg, wall = ranked[0][0], ranked[1][0]
    cells = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == wall}
    neighbors = {p: {(p[0] + dr, p[1] + dc) for dr, dc in EIGHT} & cells for p in cells}
    ends = sorted(p for p in cells if len(neighbors[p]) == 1)
    need(len(ends) == 2, "Wall needs exactly two eight-neighbor endpoints")
    seen, pending = {ends[0]}, [ends[0]]
    while pending:
        p = pending.pop()
        for q in neighbors[p] - seen:
            seen.add(q)
            pending.append(q)
    need(seen == cells, "Wall must be one eight-connected component")
    tangent = [tuple(a-b for a, b in zip(p, next(iter(neighbors[p])))) for p in ends]
    dy, dx = (sum(v[i] for v in tangent) for i in (0, 1))
    need(abs(dy) != abs(dx), "Endpoint tangents must determine a unique cardinal flow")
    flow = ((1 if dy > 0 else -1), 0) if abs(dy) > abs(dx) else (0, (1 if dx > 0 else -1))
    return bg, wall, cells, ends, flow


def flood_band(base, cells, records, cap_row, *, stride=None, freeze=False):
    height, width = len(base), len(base[0])
    virtual = set()
    for record in records:
        row, col = record["endpoint"]
        cadence = record["stride"] if stride is None else stride
        for r in range(row + 1, height):
            c = col if freeze else col + record["side"] * ((r - row + cadence - 1) // cadence)
            if 0 <= c < width:
                virtual.add((r, c))
    row = cap_row + 1
    boundary = sorted(c for r, c in cells if r == row)
    starts = [(row, c) for c in range(boundary[0] + 1, boundary[-1])
              if (row, c) not in cells | virtual]
    need(bool(starts), "Need an interior immediately ahead of the rear cap")
    allowed = {(r, c) for r in range(height) for c in range(width)} - cells - virtual
    inside = component(allowed, starts[0])
    need(all(p in inside for p in starts), "The rear interior must be connected")
    need(all(r > cap_row for r, c in inside), "The boundary must seal the rear cap")
    return inside, virtual


def scene(grid):
    original = grid_copy(grid)
    bg, wall, _, _, flow = wall_data(original)
    turns = {(1, 0): 0, (0, 1): 1, (-1, 0): 2, (0, -1): 3}[flow]
    base = rotate(original, turns)
    _, _, cells, ends, normalized_flow = wall_data(base)
    need(normalized_flow == (1, 0), "Normalization must make the flow downward")
    ends.sort(key=lambda p: p[1])
    need(ends[0][1] < ends[1][1], "Need distinct left and right tips")
    records = []
    for side, (row, col) in zip((-1, 1), ends):
        start = row
        while (start - 1, col) in cells:
            start -= 1
        stride = row - start + 1
        inner_col, inner_end = col - side, start - 1
        need((inner_end, inner_col) in cells, "Need an immediately preceding inward run")
        inner_start = inner_end
        while (inner_start - 1, inner_col) in cells:
            inner_start -= 1
        need(inner_end - inner_start + 1 == stride, "Terminal and preceding runs must be complete and equal")
        records.append({"endpoint": (row, col), "side": side, "stride": stride, "run_start": start})
    need(records[0]["stride"] == records[1]["stride"], "Both rails must share their cadence")
    cap_row = min(r for r, c in cells)
    cap = sorted(c for r, c in cells if r == cap_row)
    need(len(cap) >= 3 and cap == list(range(cap[0], cap[-1]+1)), "Need a contiguous rear cap")
    inside, virtual = flood_band(base, cells, records, cap_row)
    previous = None
    for row in range(cap_row + 1, len(base)):
        columns = sorted(c for r, c in cells if r == row)
        runs = sum(i == 0 or c != columns[i-1] + 1 for i, c in enumerate(columns))
        need(runs == sum(row <= rec["endpoint"][0] for rec in records), "Need the observed side-wall runs before each tip")
        current = {c for r, c in inside if r == row}
        need(current and (previous is None or bool(current & previous)), "Every interior row must overlap its predecessor")
        previous = current
    markers = sorted((r, c, base[r][c]) for r, c in inside if base[r][c] not in (bg, wall))
    need(bool(markers), "Need an in-band dye marker")
    earliest = {v for r, c, v in markers if r == markers[0][0]}
    need(len(earliest) == 1, "The earliest marker row must determine one dye color")
    return {"original": original, "base": base, "turns": turns, "flow": flow,
            "background": bg, "wall": wall, "cells": cells, "records": records,
            "cap_row": cap_row, "inside": inside, "virtual": virtual,
            "dye": earliest.pop(), "markers": markers}


def rival_reference(grid, settings, name):
    opaque = setting(settings) == "opaque"
    original = grid_copy(grid)
    constant = role_constant(name)
    fixed_flow = flow_constant(name)
    if name not in ("reference", *RIVALS) and constant is None and fixed_flow is None:
        raise ValueError("Unknown bounded hypothesis: " + str(name))
    if name == "identity":
        return original
    try:
        state = scene(original)
    except ValueError:
        return original
    base, bg, wall = state["base"], state["background"], state["wall"]
    cells, records = state["cells"], state["records"]
    inside, virtual = state["inside"], state["virtual"]
    if name in ("stride1", "stride2", "freeze_rails"):
        stride = int(name[-1]) if name.startswith("stride") else None
        inside, virtual = flood_band(base, cells, records, state["cap_row"], stride=stride, freeze=name == "freeze_rails")
    if name == "include_virtual_rails":
        inside = inside | virtual
    if name == "symmetric_mouth_only" and records[0]["endpoint"][0] != records[1]["endpoint"][0]:
        return original
    dye = state["dye"]
    foreign = [v for row in original for v in row if v not in (bg, wall)]
    if name == "largest_dye":
        frequencies = Counter(foreign)
        dye = min(frequencies, key=lambda v: (-frequencies[v], v))
    elif name == "minimum_dye":
        dye = min(foreign)
    elif name == "first_scan_dye":
        dye = foreign[0]
    if constant is not None and state[constant[0]] != constant[1]:
        return original
    if fixed_flow is not None and state["turns"] != fixed_flow:
        return original
    markers = {(r, c) for r, c in inside if base[r][c] not in (bg, wall)}
    blockers = {p for p in markers if base[p[0]][p[1]] != dye}
    if name == "global_shadows":
        blockers = {(r, c) for r, row in enumerate(base) for c, v in enumerate(row) if v not in (bg, wall, dye)}
    elif name == "wall_shadows":
        blockers |= cells
    elif name == "source_as_blocker":
        blockers = markers
    elif name == "one_blocker_color" and blockers:
        chosen = min(base[r][c] for r, c in blockers)
        blockers = {(r, c) for r, c in blockers if base[r][c] == chosen}
    shadow = set()
    if opaque:
        for r, c in inside:
            if name == "whole_cross_section_shadow":
                blocked = any(r > br for br, bc in blockers)
            elif name == "slanted_shadows":
                blocked = any(r > br and c == bc + r - br for br, bc in blockers)
            elif name == "backward_shadows":
                blocked = any(r < br and c == bc for br, bc in blockers)
            else:
                blocked = any(r > br and c == bc for br, bc in blockers)
            if blocked:
                shadow.add((r, c))
    permitted = inside - shadow
    last_tip = max(record["endpoint"][0] for record in records)
    if name == "body_only":
        permitted = {p for p in permitted if p[0] <= last_tip}
    elif name == "outlet_only":
        permitted = {p for p in permitted if p[0] > last_tip}
    output = deepcopy(base)
    for r, c in permitted:
        if base[r][c] == bg or name == "overwrite_blockers":
            output[r][c] = dye
    output = rotate(output, -state["turns"])
    if name == "crop_result":
        occupied = [(r, c) for r, row in enumerate(output) for c, v in enumerate(row) if v != bg]
        r0, r1 = min(p[0] for p in occupied), max(p[0] for p in occupied)
        c0, c1 = min(p[1] for p in occupied), max(p[1] for p in occupied)
        output = [row[c0:c1+1] for row in output[r0:r1+1]]
    return output


def reference(grid, settings):
    return rival_reference(grid, settings, "reference")


# The complete canonical body is copied into every returned program, not imported
# by the executable. Its grammar check is evaluated before the candidate body.
FINAL = "(turn painted (modulo (- 4 turns) 4))"
GUARD_RESULT = r"""(let* ((flat (apply append g))
          (counts (sort (map (lambda (v) (count (lambda (x) (= x v)) flat)) (remove-duplicates flat)) >))
          (cap (sort (map second (filter (lambda (p) (= (first p) cap-row)) cells)) <)))
  (and (>= (length counts) 3) (> (first counts) (second counts) (third counts))
       (= (length original-ends) 2) (= (length ends) 2)
       (not (= (abs dy) (abs dx))) (< (second (first ends)) (second (second ends)))
       (let loop ((todo (list (first cells))) (seen '()))
         (cond ((null? todo) (= (length seen) (length cells)))
               ((member? (first todo) seen) (loop (rest todo) seen))
               (else (loop (append (adjacent (first todo) cells) (rest todo)) (cons (first todo) seen)))))
       (>= (length cap) 3) (equal? cap (range (first cap) (+ 1 (last cap))))
       (= (third (first records)) (third (second records)))
       (andmap (lambda (rec)
         (let* ((r (first rec)) (c (second rec)) (stride (third rec)) (side (fourth rec))
                (inner-end (- r stride)) (inner-c (- c side))
                (missing (filter (lambda (y) (not (member? (list y inner-c) cells))) (range inner-end)))
                (inner-start (+ 1 (apply max (cons -1 missing)))))
           (and (member? (list inner-end inner-c) cells) (= (+ 1 (- inner-end inner-start)) stride)))) records)
       (for/and ((r (in-range (+ cap-row 1) (rows base))))
         (let* ((columns (map second (filter (lambda (p) (= (first p) r)) cells)))
                (run-count (length (filter (lambda (c) (not (member? (- c 1) columns))) columns)))
                (current (map second (filter (lambda (p) (= (first p) r)) inside)))
                (previous (map second (filter (lambda (p) (= (first p) (- r 1))) inside))))
           (and (= run-count (length (filter (lambda (rec) (<= r (first rec))) records)))
                (not (null? current))
                (or (= r (+ cap-row 1)) (ormap (lambda (c) (member? c previous)) current)))))
       (= (length (remove-duplicates
                   (map (lambda (p) (at base (first p) (second p)))
                        (filter (lambda (p) (= (first p) (first first-marker))) markers)))) 1)))"""


def substitute_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError("Canonical edit anchor is not unique: " + old)
    return source.replace(old, new, 1)


def rival_program(settings, name):
    mode = setting(settings)
    constant = role_constant(name)
    fixed_flow = flow_constant(name)
    if name not in ("reference", *RIVALS) and constant is None and fixed_flow is None:
        raise ValueError("Unknown bounded hypothesis: " + str(name))
    if name == "identity":
        return "(rule! (let ((answer g)) answer))\n"
    source = (HOME / "canonical.rkt").read_text().strip()
    if not source.startswith("(rule!") or not source.endswith(")"):
        raise ValueError("Expected a complete rule! canonical source")
    body = source[len("(rule!"):].strip()[:-1].strip()
    guard = substitute_once(body, FINAL, GUARD_RESULT)
    body = substitute_once(body, "(opaque #t)", "(opaque " + ("#t" if mode == "opaque" else "#f") + ")")
    if name in ("stride1", "stride2"):
        body = substitute_once(body, "(stride (+ 1 (- r start)))", "(stride " + name[-1] + ")")
    if name == "freeze_rails":
        body = substitute_once(body, "(+ end-c (* side (quotient (+ (- r end-r) stride -1) stride)))", "end-c")
    if name == "include_virtual_rails":
        body = substitute_once(body, "(< (edge-at r (first records)) c (edge-at r (second records)))",
                               "(<= (edge-at r (first records)) c (edge-at r (second records)))")
    if name in ("body_only", "outlet_only"):
        comparison = "<=" if name == "body_only" else ">"
        body = substitute_once(body, "(member? (list r c) inside)",
            "(and (member? (list r c) inside) (" + comparison + " r (apply max (map first ends))))")
    foreign = "(filter (lambda (v) (and (not (= v bg)) (not (= v wall)))) (apply append g))"
    if name == "largest_dye":
        choice = """(let ((values %s))
          (first (sort (remove-duplicates values)
            (lambda (a b) (let ((na (count (lambda (x) (= x a)) values))
                               (nb (count (lambda (x) (= x b)) values)))
              (if (= na nb) (< a b) (> na nb)))))))""" % foreign
        body = substitute_once(body, "(dye (at base (first first-marker) (second first-marker)))", "(dye " + choice + ")")
    elif name in ("minimum_dye", "first_scan_dye"):
        choice = "(apply min " + foreign + ")" if name == "minimum_dye" else "(first " + foreign + ")"
        body = substitute_once(body, "(dye (at base (first first-marker) (second first-marker)))", "(dye " + choice + ")")
    blocker_expr = "(filter (lambda (p) (not (= (at base (first p) (second p)) dye))) markers)"
    if name == "global_shadows":
        replacement = "(filter (lambda (p) (not (member? (at base (first p) (second p)) (list bg wall dye)))) (grid-positions base))"
        body = substitute_once(body, blocker_expr, replacement)
    elif name == "wall_shadows":
        body = substitute_once(body, blocker_expr, "(append cells " + blocker_expr + ")")
    elif name == "source_as_blocker":
        body = substitute_once(body, blocker_expr, "markers")
    elif name == "one_blocker_color":
        replacement = """(let ((others %s))
          (if (null? others) '()
            (let ((chosen (apply min (map (lambda (p) (at base (first p) (second p))) others))))
              (filter (lambda (p) (= (at base (first p) (second p)) chosen)) others))))""" % blocker_expr
        body = substitute_once(body, blocker_expr, replacement)
    if name == "whole_cross_section_shadow":
        body = substitute_once(body, "(map first (filter (lambda (p) (= (second p) c)) blockers))", "(map first blockers)")
    elif name == "backward_shadows":
        body = substitute_once(body, "(apply min (cons (rows base)", "(apply max (cons -1")
        body = substitute_once(body, "(<= r (list-ref frontiers c))", "(>= r (list-ref frontiers c))")
    elif name == "slanted_shadows":
        body = substitute_once(body, "(<= r (list-ref frontiers c))",
            "(not (ormap (lambda (p) (and (> r (first p)) (= c (+ (second p) (- r (first p)))))) blockers))")
    if name == "overwrite_blockers":
        body = substitute_once(body, "(= (at base r c) bg)", "(not (= (at base r c) wall))")
    result = FINAL
    if name == "symmetric_mouth_only":
        result = "(if (= (first (first ends)) (first (second ends))) " + result + " g)"
    if constant is not None:
        variable = {"background": "bg", "wall": "wall", "dye": "dye"}[constant[0]]
        result = "(if (= " + variable + " " + str(constant[1]) + ") " + result + " g)"
    if fixed_flow is not None:
        result = "(if (= turns " + str(fixed_flow) + ") " + result + " g)"
    if name == "crop_result":
        result = """(let* ((answer %s)
          (occupied (filter (lambda (p) (not (= (at answer (first p) (second p)) bg))) (grid-positions answer)))
          (r0 (apply min (map first occupied))) (r1 (apply max (map first occupied)))
          (c0 (apply min (map second occupied))) (c1 (apply max (map second occupied))))
          (grid-from-fn (+ 1 (- r1 r0)) (+ 1 (- c1 c0)) (lambda (r c) (at answer (+ r r0) (+ c c0)))))""" % FINAL
    if result != FINAL:
        body = substitute_once(body, FINAL, result)
    return "(rule!\n (if (with-handlers ((exn:fail? (lambda (invalid-domain) #f)))\n" + guard + ")\n" + body + "\n g))\n"


SOURCE_COPY_PROVENANCE = {'runtime_and_ledger_framework': {'source_path': 'WORK/repo/generators/public_eval_aa4ec2a5/workspace/parametric/audit_native.py', 'sha256': '418a5e4906df588c23520f1d79169fb726535d97f18c8e1d1e65fe800fa1bf59', 'method': 'Explicit current-packet source copy of CachedEvaluator, fit isolation, source/runtime closure and run bookkeeping; adapted task identifiers, settings, facts and episode scope. No source/runtime/evidence imports.'}, 'independent_complement_flood': {'source_path': 'WORK/checks/public_eval_b9e38dc0/design_rule_probe.py', 'sha256': '1f35766dd47ddff6f1b5ef5d31b75a7455124c71305a711ff23f31dc0c94e3d2', 'method': 'Explicit source-copy adaptation of wall_data, component, normalization and virtual-wall complement flood. Added exact grammar checks and candidate semantics; no production geometry imports.'}}


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
    spec = importlib.util.spec_from_file_location("_public_eval_b9e38dc0_frozen_native_audit", HOME / "native_family.py")
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
    blockers = [(r, c) for r, c, v in info["markers"] if v != info["dye"]]
    return {"input_shape": [len(grid), len(grid[0])], "output_shape": [len(output), len(output[0])],
        "background": info["background"], "wall_color": info["wall"], "dye": info["dye"],
        "flow": list(info["flow"]), "endpoint_records": info["records"],
        "wall_cells": len(info["cells"]), "interior_cells": len(info["inside"]),
        "blockers": blockers, "input_sha256": sha(packed(grid)), "output_sha256": sha(packed(output))}


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
    report = {"schema": "public-eval-b9e38dc0-independent-teaching-audit-v1", "status": "running",
              "task_id": TASK_ID, "assignment_id": ASSIGNMENT_ID,
              "source_files_sha256_before": binding, "runtime_files_sha256_before": runtime_before,
              "limits": deepcopy(LIMITS), "rival_meanings": RIVAL_MEANINGS,
              "source_copy_provenance": SOURCE_COPY_PROVENANCE,
              "excluded_equivalent_hypotheses": EXCLUDED_EQUIVALENT,
              "episodes": [], "findings": [], "reference_label_count": 0, "original_label_count": 0,
              "visibility": "controller_private", "training_admitted": False,
              "scope": "Six episodes only; all6+4 generated labels plus all four official labels checked independently. Learned color and flow constants read demonstration0 input only; exactly first2 demos determine survivors, then every survivor receives all4 query scores. No universal identifiability, owner acceptance, or training admission."}
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
                        candidates = [("declared:obstacle_mode=" + str(other["obstacle_mode"]), family.program(other),
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
                        intended_name = "declared:obstacle_mode=" + str(mode)
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


