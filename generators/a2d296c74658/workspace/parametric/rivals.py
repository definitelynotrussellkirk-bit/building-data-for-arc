"""Independent semantic oracle and finite executable rivals for a2d296c74658.

No prototype, adapter, generator, or mirror is imported here.  Python predicates
and standalone Racket programs implement the same declared counterrules.  The
bank is finite evidence, not a uniqueness proof.  Within-stage in-place updates
and repetition to a fixed point are equivalent to the intended stages and are
therefore not included as wrong rules.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import dataclass


def _grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30
            or any(type(row) is not list or len(row) != len(grid[0])
                   or any(type(v) is not int or not 0 <= v <= 9 for v in row)
                   for row in grid)):
        raise ValueError("Expected a strict rectangular 1..30 ARC integer grid")
    return deepcopy(grid)


def _mode(settings):
    if (type(settings) is not dict or set(settings) != {"completion_mode"}
            or settings["completion_mode"] not in ("vertical", "cascade")):
        raise ValueError("Expected completion_mode vertical or cascade")
    return settings["completion_mode"]


def first_stage(grid):
    """Independently computed stage A, reading the unchanged original grid."""
    source = _grid(grid)
    return [[4 if (value == 0 and 0 < r < len(source) - 1
                   and source[r - 1][c] == source[r + 1][c] == 7)
             else value for c, value in enumerate(row)]
            for r, row in enumerate(source)]


def oracle(grid, settings):
    mode = _mode(settings)
    intermediate = first_stage(grid)
    if mode == "vertical":
        return intermediate
    return [[2 if (value == 0 and 0 < c < len(row) - 1
                   and row[c - 1] == row[c + 1] == 4)
             else value for c, value in enumerate(row)] for row in intermediate]


def describe(grid):
    source = _grid(grid)
    intermediate = first_stage(source)
    output = oracle(source, {"completion_mode": "cascade"})
    a = [(r, c) for r in range(len(source)) for c in range(len(source[0]))
         if source[r][c] != intermediate[r][c]]
    b = [(r, c) for r in range(len(source)) for c in range(len(source[0]))
         if intermediate[r][c] != output[r][c]]
    origins = Counter({key: 0 for key in ("old_old", "old_new", "new_old", "new_new")})
    for r, c in b:
        left = "old" if source[r][c - 1] == 4 else "new"
        right = "old" if source[r][c + 1] == 4 else "new"
        origins[left + "_" + right] += 1
    a_columns = Counter(c for r, c in a)
    b_rows = Counter(r for r, c in b)
    return {
        "height": len(source), "width": len(source[0]),
        "nonzero_cells": sum(v != 0 for row in source for v in row),
        "a_cells": [list(p) for p in a], "b_cells": [list(p) for p in b],
        "a_count": len(a), "b_count": len(b), "b_endpoint_origins": dict(origins),
        "max_a_per_column": max(a_columns.values(), default=0),
        "max_b_per_row": max(b_rows.values(), default=0),
        "a_interior_count": sum(0 < c < len(source[0]) - 1 for r, c in a),
        "a_edge_count": sum(c in (0, len(source[0]) - 1) for r, c in a),
        "occupied_rows": sum(any(v != 0 for v in row) for row in source),
        "occupied_columns": sum(any(row[c] != 0 for row in source)
                                for c in range(len(source[0]))),
    }


def _pair(source, r, c, dr, dc, color):
    h, w = len(source), len(source[0])
    if not (0 <= r - dr < h and 0 <= r + dr < h
            and 0 <= c - dc < w and 0 <= c + dc < w):
        return False
    left, right = source[r - dr][c - dc], source[r + dr][c + dc]
    return left == right and (left != 0 if color is None else left == color)


def _wide(source, r, c, dr, dc, color):
    for sign in (-1, 1):
        rr, cc = r + sign * dr, c + sign * dc
        while 0 <= rr < len(source) and 0 <= cc < len(source[0]) and source[rr][cc] == 0:
            rr += sign * dr
            cc += sign * dc
        if not (0 <= rr < len(source) and 0 <= cc < len(source[0]) and source[rr][cc] == color):
            return False
    return True


def _context_ok(source, r, c, kind):
    """Extraneous local restrictions from the independent retained review."""
    diagonal = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    if kind == "lateral_no_seven":
        offsets, allowed, denied = [(0, -1), (0, 1)], None, 7
    elif kind == "endpoint_lateral_no_seven":
        offsets, allowed, denied = diagonal, None, 7
    elif kind == "outer_vertical_no_seven":
        offsets, allowed, denied = [(-2, 0), (2, 0)], None, 7
    elif kind == "vertical_no_four":
        offsets, allowed, denied = [(-1, 0), (1, 0)], None, 4
    elif kind == "endpoint_vertical_no_four":
        offsets, allowed, denied = diagonal, None, 4
    elif kind == "outer_lateral_zero":
        offsets, allowed, denied = [(0, -2), (0, 2)], {0}, None
    elif kind == "no_third_color":
        offsets, allowed, denied = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)], {0, 4, 7}, None
    elif kind == "ignore_edge_columns":
        return c not in (0, len(source[0]) - 1)
    elif kind == "ignore_near_boundary_rows":
        return r not in (1, len(source) - 2)
    else:
        return True
    values = [source[r + dr][c + dc] for dr, dc in offsets
              if 0 <= r + dr < len(source) and 0 <= c + dc < len(source[0])]
    return all(v in allowed for v in values) if allowed is not None else all(v != denied for v in values)


def _stage_a(source, kind="normal"):
    h, w = len(source), len(source[0])
    targets = []
    for r in range(h):
        for c in range(w):
            if source[r][c] != 0 and kind != "overwrite":
                continue
            vertical = _pair(source, r, c, 1, 0, 7)
            if kind == "horizontal":
                eligible = _pair(source, r, c, 0, 1, 7)
            elif kind == "diagonal":
                eligible = _pair(source, r, c, 1, 1, 7) or _pair(source, r, c, 1, -1, 7)
            elif kind == "both_axes":
                eligible = vertical or _pair(source, r, c, 0, 1, 7)
            elif kind == "equal_nonzero":
                eligible = _pair(source, r, c, 1, 0, None)
            elif kind == "wide":
                eligible = _wide(source, r, c, 1, 0, 7)
            else:
                eligible = vertical
            if eligible and _context_ok(source, r, c, kind):
                targets.append((r, c))
    selected = targets
    if kind == "first":
        selected = targets[:1]
    elif kind == "cap_three_total":
        selected = targets[:3]
    elif kind == "cap_thirty_two_total":
        selected = targets[:32]
    elif kind in ("cap_two_column", "cap_four_column"):
        cap = 2 if kind == "cap_two_column" else 4
        selected = [(r, c) for r, c in targets
                    if sum(cc == c and rr <= r for rr, cc in targets) <= cap]
    elif kind == "edge_chains":
        counts = Counter(c for r, c in targets)
        selected = [(r, c) for r, c in targets if counts[c] == 1 or c in (0, w - 1)]
    elif kind == "isolated":
        selected = [(r, c) for r, c in targets
                    if (r - 2, c) not in targets and (r + 2, c) not in targets]
    out = deepcopy(source)
    for r, c in selected:
        out[r][c] = 2 if kind == "paint_two" else 4
    return out


def _stage_b(source, original, kind="normal", destination=None):
    targets = []
    for r in range(len(source)):
        for c in range(len(source[0])):
            if source[r][c] != 0 and kind != "overwrite":
                continue
            horizontal = _pair(source, r, c, 0, 1, 4)
            if kind == "vertical":
                eligible = _pair(source, r, c, 1, 0, 4)
            elif kind == "both_axes":
                eligible = horizontal or _pair(source, r, c, 1, 0, 4)
            elif kind == "wide":
                eligible = _wide(source, r, c, 0, 1, 4)
            else:
                eligible = horizontal
            if not eligible or not _context_ok(source, r, c, kind):
                continue
            if kind in ("old_only", "new_only", "mixed_only", "some_new"):
                old_count = int(original[r][c - 1] == 4) + int(original[r][c + 1] == 4)
                if ((kind == "old_only" and old_count != 2)
                        or (kind == "new_only" and old_count != 0)
                        or (kind == "mixed_only" and old_count != 1)
                        or (kind == "some_new" and old_count == 2)):
                    continue
            targets.append((r, c))
    if kind == "first":
        targets = targets[:1]
    elif kind == "cap_thirty_two_total":
        targets = targets[:32]
    elif kind in ("cap_two_row", "cap_four_row"):
        cap = 2 if kind == "cap_two_row" else 4
        targets = [(r, c) for r, c in targets
                   if sum(rr == r and cc <= c for rr, cc in targets) <= cap]
    out = deepcopy(source if destination is None else destination)
    for r, c in targets:
        out[r][c] = 4 if kind == "paint_four" else 2
    return out


_RACKET = r"""(rule! (lambda (g)
  (let ((h (rows g)) (w (cols g)))
    (define ak '@AK@)
    (define bk '@BK@)
    (define mode '@MODE@)
    (define special '@SPECIAL@)
    (define (inside? r c) (and (<= 0 r) (< r h) (<= 0 c) (< c w)))
    (define (pair? src r c dr dc color)
      (and (inside? (- r dr) (- c dc)) (inside? (+ r dr) (+ c dc))
        (= (at src (- r dr) (- c dc)) (at src (+ r dr) (+ c dc)))
        (if (= color -1) (not (= (at src (- r dr) (- c dc)) 0))
            (= (at src (- r dr) (- c dc)) color))))
    (define (seek? src r c dr dc color)
      (and (inside? r c)
        (if (= (at src r c) 0) (seek? src (+ r dr) (+ c dc) dr dc color)
            (= (at src r c) color))))
    (define (wide? src r c dr dc color)
      (and (seek? src (- r dr) (- c dc) (- dr) (- dc) color)
           (seek? src (+ r dr) (+ c dc) dr dc color)))
    (define diagonal (list (list -1 -1) (list -1 1) (list 1 -1) (list 1 1)))
    (define box (for*/list ((dr (in-range -1 2)) (dc (in-range -1 2))) (list dr dc)))
    (define (neighbors-ok? src r c offsets allowed forbidden)
      (for/and ((p offsets))
        (let ((rr (+ r (first p))) (cc (+ c (second p))))
          (or (not (inside? rr cc))
              (if (= forbidden -1) (member? (at src rr cc) allowed)
                  (not (= (at src rr cc) forbidden)))))))
    (define (context-ok? kind src r c)
      (cond ((eq? kind 'lateral_no_seven)
             (neighbors-ok? src r c (list (list 0 -1) (list 0 1)) (list) 7))
            ((eq? kind 'endpoint_lateral_no_seven) (neighbors-ok? src r c diagonal (list) 7))
            ((eq? kind 'outer_vertical_no_seven)
             (neighbors-ok? src r c (list (list -2 0) (list 2 0)) (list) 7))
            ((eq? kind 'vertical_no_four)
             (neighbors-ok? src r c (list (list -1 0) (list 1 0)) (list) 4))
            ((eq? kind 'endpoint_vertical_no_four) (neighbors-ok? src r c diagonal (list) 4))
            ((eq? kind 'outer_lateral_zero)
             (neighbors-ok? src r c (list (list 0 -2) (list 0 2)) (list 0) -1))
            ((eq? kind 'no_third_color) (neighbors-ok? src r c box (list 0 4 7) -1))
            ((eq? kind 'ignore_edge_columns) (and (< 0 c) (< c (- w 1))))
            ((eq? kind 'ignore_near_boundary_rows) (and (not (= r 1)) (not (= r (- h 2)))))
            (else #t)))
    (define (a? src r c)
      (and (context-ok? ak src r c) (or (eq? ak 'overwrite) (= (at src r c) 0))
        (cond ((eq? ak 'horizontal) (pair? src r c 0 1 7))
              ((eq? ak 'diagonal) (or (pair? src r c 1 1 7) (pair? src r c 1 -1 7)))
              ((eq? ak 'both_axes) (or (pair? src r c 1 0 7) (pair? src r c 0 1 7)))
              ((eq? ak 'equal_nonzero) (pair? src r c 1 0 -1))
              ((eq? ak 'wide) (wide? src r c 1 0 7))
              (else (pair? src r c 1 0 7)))))
    (define (stage-a src)
      (define ps (for*/list ((r (in-range h)) (c (in-range w)) #:when (a? src r c)) (list r c)))
      (define selected
        (cond ((eq? ak 'first) (take ps (min 1 (length ps))))
              ((eq? ak 'cap_three_total) (take ps (min 3 (length ps))))
              ((eq? ak 'cap_thirty_two_total) (take ps (min 32 (length ps))))
              ((member? ak (list 'cap_two_column 'cap_four_column))
               (filter (lambda (p) (<= (length (filter (lambda (q)
                 (and (= (second p) (second q)) (<= (first q) (first p)))) ps))
                 (if (eq? ak 'cap_two_column) 2 4))) ps))
              ((eq? ak 'edge_chains)
               (filter (lambda (p) (or (= (second p) 0) (= (second p) (- w 1))
                 (= 1 (length (filter (lambda (q) (= (second p) (second q))) ps))))) ps))
              ((eq? ak 'isolated)
               (filter (lambda (p) (and (not (member? (list (- (first p) 2) (second p)) ps))
                                      (not (member? (list (+ (first p) 2) (second p)) ps)))) ps))
              (else ps)))
      (for/fold ((out src)) ((p selected))
        (set-cell out (first p) (second p) (if (eq? ak 'paint_two) 2 4))))
    (define (b? src r c)
      (and (context-ok? bk src r c) (or (eq? bk 'overwrite) (= (at src r c) 0))
        (cond ((eq? bk 'vertical) (pair? src r c 1 0 4))
              ((eq? bk 'both_axes) (or (pair? src r c 0 1 4) (pair? src r c 1 0 4)))
              ((eq? bk 'wide) (wide? src r c 0 1 4))
              (else (pair? src r c 0 1 4)))
        (if (member? bk (list 'old_only 'new_only 'mixed_only 'some_new))
          (let ((old (+ (if (= (at g r (- c 1)) 4) 1 0) (if (= (at g r (+ c 1)) 4) 1 0))))
            (cond ((eq? bk 'old_only) (= old 2))
                  ((eq? bk 'new_only) (= old 0))
                  ((eq? bk 'mixed_only) (= old 1))
                  (else (< old 2)))) #t)))
    (define (stage-b src destination)
      (define ps (for*/list ((r (in-range h)) (c (in-range w)) #:when (b? src r c)) (list r c)))
      (define selected
        (cond ((eq? bk 'first) (take ps (min 1 (length ps))))
              ((eq? bk 'cap_thirty_two_total) (take ps (min 32 (length ps))))
              ((member? bk (list 'cap_two_row 'cap_four_row))
               (filter (lambda (p) (<= (length (filter (lambda (q)
                 (and (= (first p) (first q)) (<= (second q) (second p)))) ps))
                 (if (eq? bk 'cap_two_row) 2 4))) ps))
              (else ps)))
      (for/fold ((out destination)) ((p selected))
        (set-cell out (first p) (second p) (if (eq? bk 'paint_four) 4 2))))
    (cond ((eq? special 'identity) g)
          ((eq? special 'skip_a) (stage-b g g))
          ((eq? special 'reverse) (stage-a (stage-b g g)))
          (else
            (let* ((a (stage-a g))
                   (out (cond ((or (eq? special 'skip_b) (eq? mode 'vertical)) a)
                              ((eq? special 'stale) (stage-b g a))
                              (else (stage-b a a)))))
              (if (eq? special 'erase_a)
                (build-grid h w (r c) (if (and (= (at g r c) 0) (= (at a r c) 4)) 0 (at out r c)))
                out)))))))"""


@dataclass(frozen=True)
class Rival:
    name: str
    description: str
    mode: str
    a_kind: str = "normal"
    b_kind: str = "normal"
    special: str = "normal"
    equivalence_group: str = ""

    @property
    def program(self):
        result = _RACKET
        for key, value in (("AK", self.a_kind), ("BK", self.b_kind),
                           ("MODE", self.mode), ("SPECIAL", self.special)):
            result = result.replace("@" + key + "@", value)
        return result

    def apply(self, grid):
        source = _grid(grid)
        if self.special == "identity":
            return source
        if self.special == "skip_a":
            return _stage_b(source, source, self.b_kind)
        if self.special == "reverse":
            return _stage_a(_stage_b(source, source, self.b_kind), self.a_kind)
        a = _stage_a(source, self.a_kind)
        if self.mode == "vertical" or self.special == "skip_b":
            return a
        if self.special == "stale":
            return _stage_b(source, source, self.b_kind, destination=a)
        output = _stage_b(a, source, self.b_kind)
        if self.special == "erase_a":
            for r, row in enumerate(source):
                for c, value in enumerate(row):
                    if value == 0 and a[r][c] == 4:
                        output[r][c] = 0
        return output


def bank(settings):
    mode = _mode(settings)
    rows = [Rival("identity", "Return the unchanged input.", mode, special="identity")]
    mutations = (
        ("a_horizontal", "horizontal", "Use horizontal rather than vertical 7 endpoints."),
        ("a_diagonal", "diagonal", "Use either diagonal pair of 7 endpoints."),
        ("a_both_axes", "both_axes", "Accept horizontal as well as vertical 7 endpoints."),
        ("a_equal_nonzero_endpoints", "equal_nonzero", "Accept matching nonzero endpoints of any color."),
        ("a_fill_wide_gaps", "wide", "Fill whole empty vertical runs bounded by 7s."),
        ("a_overwrite_occupied", "overwrite", "Overwrite a nonzero center between vertical 7s."),
        ("a_first_only", "first", "Paint only the first row-major A target."),
        ("a_cap_two_per_column", "cap_two_column", "Retained shortcut: at most two A targets per column."),
        ("a_shared_chains_only_at_edges", "edge_chains", "Retained shortcut: multiple targets per column only at an edge."),
        ("a_cap_three_total", "cap_three_total", "Paint only the first three A targets globally."),
        ("a_no_shared_endpoints", "isolated", "Omit targets whose 7 endpoint is shared with another target."),
        ("a_paint_two", "paint_two", "Paint A targets 2 instead of 4, then apply B normally."),
        ("a_lateral_no_seven", "lateral_no_seven", "Require no 7 immediately beside an otherwise valid A center."),
        ("a_endpoint_lateral_no_seven", "endpoint_lateral_no_seven", "Require no 7 beside either vertical endpoint."),
        ("a_endpoint_outer_vertical_no_seven", "outer_vertical_no_seven", "Require no 7 just beyond either endpoint along A's vertical axis."),
        ("a_neighborhood_no_third_color", "no_third_color", "Require A's 3x3 neighborhood to contain only 0, 4 and 7."),
        ("a_ignore_edge_columns", "ignore_edge_columns", "Omit valid A centers in the first or last column."),
        ("a_ignore_near_boundary_rows", "ignore_near_boundary_rows", "Omit A centers adjacent to the top or bottom row."),
        ("a_cap_four_per_column", "cap_four_column", "Paint at most four valid A centers per column."),
        ("a_cap_thirty_two_total", "cap_thirty_two_total", "Paint at most 32 valid A centers globally."),
    )
    rows.extend(Rival(name, description, mode, a_kind=kind) for name, kind, description in mutations)
    if mode == "vertical":
        rows.append(Rival("apply_cascade", "Apply the cascade setting to a vertical-only lesson.", "cascade"))
        return tuple(rows)
    specials = (
        ("skip_a", "skip_a", "Run B directly on the original input, omitting A."),
        ("skip_b", "skip_b", "Return completed A without B."),
        ("b_before_a", "reverse", "Execute B before A; original B centers have priority."),
        ("b_reads_original", "stale", "Evaluate B's entire predicate on the original grid and overwrite completed A."),
        ("erase_a_after_b", "erase_a", "Run both stages then erase every A-created 4."),
    )
    rows.extend(Rival(name, description, mode, special=special,
                      equivalence_group="original_b_priority" if special in ("reverse", "stale") else name)
                for name, special, description in specials)
    b_mutations = (
        ("b_old_four_only", "old_only", "Use only pairs of original 4s, with current A zero eligibility."),
        ("b_new_four_only", "new_only", "Require both 4 endpoints to have been created by A."),
        ("b_mixed_four_only", "mixed_only", "Require exactly one old and one A-created 4 endpoint."),
        ("b_at_least_one_new_four", "some_new", "Exclude original-original 4 endpoint pairs."),
        ("b_vertical", "vertical", "Use vertical rather than horizontal 4 endpoints."),
        ("b_both_axes", "both_axes", "Accept vertical as well as horizontal 4 endpoints."),
        ("b_fill_wide_gaps", "wide", "Fill whole empty horizontal runs bounded by 4s."),
        ("b_overwrite_occupied", "overwrite", "Overwrite a nonzero center between horizontal 4s."),
        ("b_first_only", "first", "Paint only the first row-major B target."),
        ("b_cap_two_per_row", "cap_two_row", "Paint at most two B targets in each row."),
        ("b_paint_four", "paint_four", "Paint B targets 4 instead of 2."),
        ("b_vertical_no_four", "vertical_no_four", "Require no 4 directly above or below a valid B center."),
        ("b_endpoint_vertical_no_four", "endpoint_vertical_no_four", "Require no 4 directly above or below either B endpoint."),
        ("b_endpoint_outer_lateral_zero", "outer_lateral_zero", "Require blank cells just outside B's two endpoints."),
        ("b_neighborhood_no_third_color", "no_third_color", "Require B's 3x3 neighborhood to contain only 0, 4 and 7."),
        ("b_cap_four_per_row", "cap_four_row", "Paint at most four valid B centers per row."),
        ("b_cap_thirty_two_total", "cap_thirty_two_total", "Paint at most 32 valid B centers globally."),
    )
    rows.extend(Rival(name, description, mode, b_kind=kind) for name, kind, description in b_mutations)
    return tuple(rows)


def audit_lesson(episode, settings, execute=None):
    """Demo-first audit; errors never count as semantic refutations.

    ``execute`` accepts a Rival and a grid, and may run a protected implementation.
    Queries are examined only after all supplied demonstrations fit exactly.
    """
    execute = execute or (lambda rival, grid: rival.apply(grid))
    rows, findings, errors = [], [], []
    for rival in bank(settings):
        row = {"rival": rival.name, "equivalence_group": rival.equivalence_group or rival.name,
               "demo_checks": 0, "query_checks": 0, "demo_matches": [], "query_matches": [],
               "fits_all_demos": None, "status": "checked"}
        try:
            for index, pair in enumerate(episode["train"]):
                row["demo_checks"] += 1
                predicted = execute(rival, deepcopy(pair["input"]))
                match = predicted == pair["output"]
                row["demo_matches"].append(match)
                if not match:
                    row["first_refuting_demo"] = index
                    row["fits_all_demos"] = False
                    break
            else:
                row["fits_all_demos"] = True
                for index, pair in enumerate(episode["test"]):
                    row["query_checks"] += 1
                    predicted = execute(rival, deepcopy(pair["input"]))
                    match = predicted == pair["output"]
                    row["query_matches"].append(match)
                    if not match:
                        findings.append({"rival": rival.name,
                                         "equivalence_group": rival.equivalence_group or rival.name,
                                         "program": rival.program, "query_index": index,
                                         "train": deepcopy(episode["train"]),
                                         "input": deepcopy(pair["input"]),
                                         "output": deepcopy(pair["output"]),
                                         "rival_output": predicted})
        except Exception as exc:
            row["status"] = "error"
            row["fits_all_demos"] = None
            errors.append({"rival": rival.name, "error": f"{type(exc).__name__}: {exc}"})
        rows.append(row)
    return {"rivals": rows, "findings": findings, "errors": errors}
