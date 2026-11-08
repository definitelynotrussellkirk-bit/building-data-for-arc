"""Independent oracle and a finite, executable semantic rival bank.

No prototype implementation is imported here.  The intended oracle reconstructs
UDLR-lexicographic shortest paths using reverse distance maps.  The separate
rival interpreter uses predecessor BFS, and its standalone Racket programs are
executed by audit.py.  A surviving finite bank does not prove unique induction.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _mode(settings):
    if type(settings) is not dict or set(settings) != {"route_mode"}:
        raise ValueError("settings must name exactly route_mode")
    mode = settings["route_mode"]
    if type(mode) is not str or mode not in ("direct", "via_farthest"):
        raise ValueError("route_mode must be direct or via_farthest")
    return mode


def _read(grid):
    if (type(grid) is not list or not grid or type(grid[0]) is not list
            or not grid[0] or len(grid) > 30 or len(grid[0]) > 30):
        raise ValueError("expected a rectangular integer grid of size 1..30")
    h, w = len(grid), len(grid[0])
    if any(type(row) is not list or len(row) != w
           or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid):
        raise ValueError("expected a rectangular integer grid of size 1..30")
    flat = [v for row in grid for v in row]
    if flat.count(5) < 3:
        raise ValueError("at least three wall cells preserve canonical color selection")
    points = [i for i, value in enumerate(flat) if value not in (0, 5)]
    if len(points) != 2 or flat[points[0]] != flat[points[1]] or flat[points[0]] == 1:
        raise ValueError("expected exactly two same-color endpoints excluding 0, 1 and 5")
    return h, w, flat, flat[points[0]], points[0], points[1]


def _neighbors(cell, h, w, order=DIRS):
    row, col = divmod(cell, w)
    for dr, dc in order:
        nr, nc = row + dr, col + dc
        if 0 <= nr < h and 0 <= nc < w:
            yield nr * w + nc


def _distance_map(flat, h, w, source):
    distances = [-1] * len(flat)
    distances[source] = 0
    queue = [source]
    for cell in queue:
        for nxt in _neighbors(cell, h, w):
            if flat[nxt] != 5 and distances[nxt] < 0:
                distances[nxt] = distances[cell] + 1
                queue.append(nxt)
    return distances, queue


def _canonical_path(flat, h, w, source, target):
    distances, _ = _distance_map(flat, h, w, target)
    if distances[source] < 0:
        return []
    path, current = [source], source
    while current != target:
        current = next(nxt for nxt in _neighbors(current, h, w)
                       if distances[nxt] == distances[current] - 1)
        path.append(current)
    return path


def _paint(grid, cells, color):
    out = [row[:] for row in grid]
    w = len(grid[0])
    for cell in cells:
        row, col = divmod(cell, w)
        out[row][col] = color
    return out


def _intended(grid, settings):
    mode = _mode(settings)
    h, w, flat, color, start, goal = _read(grid)
    distances, order = _distance_map(flat, h, w, start)
    if len(order) != sum(value != 5 for value in flat):
        raise ValueError("all open cells must be connected")
    greatest = max(distances)
    waypoint = distances.index(greatest)
    direct = _canonical_path(flat, h, w, start, goal)
    first = _canonical_path(flat, h, w, start, waypoint)
    second = _canonical_path(flat, h, w, waypoint, goal)
    route = direct if mode == "direct" else first + second
    return _paint(grid, route, color), {
        "height": h, "width": w, "color": color,
        "start": list(divmod(start, w)), "goal": list(divmod(goal, w)),
        "waypoint": list(divmod(waypoint, w)), "waypoint_distance": greatest,
        "farthest_ties": distances.count(greatest),
        "open_cells": len(order), "walls": len(flat) - len(order),
        "direct_length": len(direct), "first_leg_length": len(first),
        "second_leg_length": len(second), "painted_route_cells": len(set(route)),
        "added_route_cells": len(set(route) - {start, goal}),
        "via_extra_cells": len((set(first) | set(second)) - set(direct)),
        "route_boundary_depth": max(min(r, h - 1 - r, c, w - 1 - c)
                                    for r, c in (divmod(p, w) for p in route)),
    }


def oracle(grid, settings):
    """Return independently reconstructed intended labels without mutating input."""
    return _intended(grid, settings)[0]


def describe(grid, settings):
    """Input-derived semantic measurements, independent of prototype metadata."""
    return _intended(grid, settings)[1]


def _rival_path(flat, h, w, source, target, spec, monotone):
    order = spec.get("order", DIRS)
    depth_limit = spec.get("depth", -1)
    def distance(p):
        r, c = divmod(p, w)
        tr, tc = divmod(target, w)
        return abs(r - tr) + abs(c - tc)
    parents = {source: None}
    queue = [source]
    for cell in queue:
        if cell == target:
            break
        for nxt in _neighbors(cell, h, w, order):
            r, c = divmod(nxt, w)
            if nxt in parents or (flat[nxt] == 5 and not spec.get("ignore_walls")):
                continue
            if depth_limit >= 0 and nxt not in (source, target):
                if min(r, h - 1 - r, c, w - 1 - c) > depth_limit:
                    continue
            if monotone and distance(nxt) >= distance(cell):
                continue
            parents[nxt] = cell
            queue.append(nxt)
    if target not in parents:
        return []
    result, current = [], target
    while current is not None:
        result.append(current)
        current = parents[current]
    return result[::-1]


def _predict(grid, mode, spec):
    h, w, flat, color, start, goal = _read(grid)
    if spec.get("reverse"):
        start, goal = goal, start
    if spec.get("identity"):
        return [row[:] for row in grid]
    mode = spec.get("mode", mode)
    source = goal if spec.get("selector") == "goal" else start
    distances, discovery = _distance_map(flat, h, w, source)
    candidates = [p for p, v in enumerate(flat) if v != 5 and distances[p] >= 0]
    selector = spec.get("selector", "graph")
    if selector in ("boundary", "outer_boundary"):
        limit = 0 if selector == "outer_boundary" else 1
        chosen = [p for p in candidates
                  if min(p // w, h - 1 - p // w, p % w, w - 1 - p % w) <= limit]
        candidates = chosen or candidates
    elif selector == "exclude_endpoints":
        candidates = [p for p in candidates if p not in (start, goal)] or candidates
    elif selector == "leaf":
        candidates = [p for p in candidates
                      if sum(flat[q] != 5 for q in _neighbors(p, h, w)) == 1] or candidates
    if selector == "manhattan":
        sr, sc = divmod(start, w)
        scores = [abs(p // w - sr) + abs(p % w - sc) for p in range(len(flat))]
    else:
        scores = distances
    greatest = max(scores[p] for p in candidates)
    tied = [p for p in candidates if scores[p] == greatest]
    if spec.get("tie") == "last":
        waypoint = tied[-1]
    elif spec.get("tie") == "discovery":
        waypoint = next(p for p in discovery if p in tied)
    elif spec.get("tie") == "discovery_last":
        waypoint = next(p for p in reversed(discovery) if p in tied)
    else:
        waypoint = tied[0]
    if mode == "direct":
        legs = [(start, goal)]
    elif spec.get("leg") == "first":
        legs = [(start, waypoint)]
    elif spec.get("leg") == "second":
        legs = [(waypoint, goal)]
    elif spec.get("leg") == "from_goal":
        legs = [(start, waypoint), (goal, waypoint)]
    elif spec.get("leg") == "direct_plus_first":
        legs = [(start, goal), (start, waypoint)]
    else:
        legs = [(start, waypoint), (waypoint, goal)]
    if spec.get("waypoint_only"):
        return _paint(grid, [waypoint], color)
    interior = all(min(p // w, h - 1 - p // w, p % w, w - 1 - p % w) >= 2
                   for p in (start, goal))
    monotone = spec.get("monotone") == "always" or (
        spec.get("monotone") == "interior" and interior)
    kind, route = spec.get("route", "shortest"), []
    for a, b in legs:
        if kind == "flood":
            route.extend(_distance_map(flat, h, w, a)[1])
        elif kind == "all_shortest":
            da, _ = _distance_map(flat, h, w, a)
            db, _ = _distance_map(flat, h, w, b)
            route.extend(p for p in range(len(flat))
                         if da[p] >= 0 and db[p] >= 0 and da[p] + db[p] == da[b])
        elif kind in ("vertical_first", "horizontal_first", "box"):
            ar, ac = divmod(a, w)
            br, bc = divmod(b, w)
            if kind == "box":
                cells = [r * w + c for r in range(min(ar, br), max(ar, br) + 1)
                         for c in range(min(ac, bc), max(ac, bc) + 1)]
            else:
                corner_r, corner_c = (br, ac) if kind == "vertical_first" else (ar, bc)
                cells = []
                for (r0, c0), (r1, c1) in [((ar, ac), (corner_r, corner_c)),
                                           ((corner_r, corner_c), (br, bc))]:
                    if r0 == r1:
                        cells.extend(r0 * w + c for c in range(min(c0, c1), max(c0, c1) + 1))
                    else:
                        cells.extend(r * w + c0 for r in range(min(r0, r1), max(r0, r1) + 1))
            route.extend(p for p in cells if flat[p] != 5)
        else:
            route.extend(_rival_path(flat, h, w, a, b, spec, monotone))
    return _paint(grid, route, color)


_RACKET_BODY = r"""
  (let ()
    (define dirs @DIRS@)
    (define depth-limit @DEPTH@)
    (define ignore-walls @IGNORE@)
    (define route-kind '@ROUTE@)
    (define selector '@SELECTOR@)
    (define tie-kind '@TIE@)
    (define mode '@MODE@)
    (define leg-kind '@LEG@)
    (define points
      (for*/list ((r (in-range h)) (c (in-range w))
                  #:when (not (member? (at g r c) (list 0 5))))
        (list r c)))
    (define color (at g (first (first points)) (second (first points))))
    (define start (@START@ points))
    (define goal (@GOAL@ points))
    (define (depth p)
      (min (first p) (- h 1 (first p)) (second p) (- w 1 (second p))))
    (define (md a b)
      (+ (abs (- (first a) (first b))) (abs (- (second a) (second b)))))
    (define monotone
      (or @ALWAYS@ (and @INTERIOR@ (>= (depth start) 2) (>= (depth goal) 2))))
    (define (neighbors p)
      (filter (lambda (q) (in-bounds? (first q) (second q) h w))
        (map (lambda (d) (list (+ (first p) (first d)) (+ (second p) (second d)))) dirs)))
    (define (open? p) (not (= (at g (first p) (second p)) 5)))
    (define (walk source)
      (let bfs ((queue (list (list source 0))) (seen (list source)) (out (list)))
        (if (empty? queue) (reverse out)
          (let* ((item (first queue)) (cur (first item)) (dist (second item))
                 (nbrs (filter (lambda (p) (and (open? p) (not (member? p seen))))
                               (neighbors cur))))
            (bfs (append (rest queue) (map (lambda (p) (list p (+ dist 1))) nbrs))
                 (append seen nbrs) (cons item out))))))
    (define (lookup entries p)
      (let ((entry (find-first (lambda (x) (equal? (first x) p)) entries)))
        (if entry (second entry) -1)))
    (define scan (walk (if (eq? selector 'goal) goal start)))
    (define open-cells
      (for*/list ((r (in-range h)) (c (in-range w)) #:when (open? (list r c)))
        (list r c)))
    (define restricted
      (filter (lambda (p)
                (cond ((eq? selector 'boundary) (<= (depth p) 1))
                      ((eq? selector 'outer-boundary) (= (depth p) 0))
                      ((eq? selector 'exclude-endpoints)
                        (and (not (equal? p start)) (not (equal? p goal))))
                      ((eq? selector 'leaf) (= (length (filter open? (neighbors p))) 1))
                      (else #t))) open-cells))
    (define candidates (if (empty? restricted) open-cells restricted))
    (define (score p) (if (eq? selector 'manhattan) (md start p) (lookup scan p)))
    (define maximum (apply max (map score candidates)))
    (define tied (filter (lambda (p) (= (score p) maximum)) candidates))
    (define waypoint
      (cond ((eq? tie-kind 'last) (last tied))
            ((eq? tie-kind 'discovery)
              (first (find-first (lambda (x) (member? (first x) tied)) scan)))
            ((eq? tie-kind 'discovery-last)
              (first (find-first (lambda (x) (member? (first x) tied)) (reverse scan))))
            (else (first tied))))
    (define (shortest source target)
      (let bfs ((queue (list (list source (list source)))) (seen (list source)))
        (cond ((empty? queue) (list))
              (else
                (let* ((item (first queue)) (cur (first item)) (path (second item)))
                  (if (equal? cur target) (reverse path)
                    (let ((nbrs
                      (filter (lambda (p)
                        (and (not (member? p seen)) (or ignore-walls (open? p))
                             (or (< depth-limit 0) (equal? p source) (equal? p target)
                                 (<= (depth p) depth-limit))
                             (or (not monotone) (< (md p target) (md cur target)))))
                        (neighbors cur))))
                      (bfs (append (rest queue)
                                   (map (lambda (p) (list p (cons p path))) nbrs))
                           (append seen nbrs)))))))))
    (define (segment a b)
      (filter (lambda (p)
        (and (<= (min (first a) (first b)) (first p) (max (first a) (first b)))
             (<= (min (second a) (second b)) (second p) (max (second a) (second b)))))
        open-cells))
    (define (route a b)
      (cond ((eq? route-kind 'flood) (map first (walk a)))
            ((eq? route-kind 'all-shortest)
              (let* ((da (walk a)) (db (walk b)) (total (lookup da b)))
                (filter (lambda (p)
                  (let ((x (lookup da p)) (y (lookup db p)))
                    (and (>= x 0) (>= y 0) (= (+ x y) total)))) open-cells)))
            ((eq? route-kind 'box) (segment a b))
            ((eq? route-kind 'vertical-first)
              (let ((corner (list (first b) (second a))))
                (append (segment a corner) (segment corner b))))
            ((eq? route-kind 'horizontal-first)
              (let ((corner (list (first a) (second b))))
                (append (segment a corner) (segment corner b))))
            (else (shortest a b))))
    (define route-cells
      (cond (@IDENTITY@ (list))
            (@WAYPOINT_ONLY@ (list waypoint))
            ((eq? mode 'direct) (route start goal))
            ((eq? leg-kind 'first) (route start waypoint))
            ((eq? leg-kind 'second) (route waypoint goal))
            ((eq? leg-kind 'from-goal) (append (route start waypoint) (route goal waypoint)))
            ((eq? leg-kind 'direct-plus-first) (append (route start goal) (route start waypoint)))
            (else (append (route start waypoint) (route waypoint goal)))))
    (for/fold ((out g)) ((p (in-list route-cells)))
      (set-cell out (first p) (second p) color)))
"""


def _program(mode, spec):
    symbol = lambda value: value.replace("_", "-")
    boolean = lambda value: "#t" if value else "#f"
    values = {
        "DIRS": "(list " + " ".join(f"(list {r} {c})" for r, c in spec.get("order", DIRS)) + ")",
        "DEPTH": str(spec.get("depth", -1)), "IGNORE": boolean(spec.get("ignore_walls")),
        "ROUTE": symbol(spec.get("route", "shortest")),
        "SELECTOR": symbol(spec.get("selector", "graph")),
        "TIE": symbol(spec.get("tie", "first")), "MODE": symbol(spec.get("mode", mode)),
        "LEG": symbol(spec.get("leg", "both")),
        "START": "second" if spec.get("reverse") else "first",
        "GOAL": "first" if spec.get("reverse") else "second",
        "ALWAYS": boolean(spec.get("monotone") == "always"),
        "INTERIOR": boolean(spec.get("monotone") == "interior"),
        "IDENTITY": boolean(spec.get("identity")), "WAYPOINT_ONLY": boolean(spec.get("waypoint_only")),
    }
    body = _RACKET_BODY
    for key, value in values.items():
        body = body.replace("@" + key + "@", value)
    return "(rule!\n" + body + ")"


@dataclass(frozen=True)
class Rival:
    name: str
    description: str
    mode: str
    spec: dict[str, Any]

    def apply(self, grid):
        return _predict(grid, self.mode, self.spec)

    @property
    def program(self):
        return _program(self.mode, self.spec)


def bank(settings):
    """19 direct or 32 composed rivals, each a total standalone Racket rule."""
    mode = _mode(settings)
    definitions = [
        ("boundary_only", "BFS restricted to the outermost ring, plus leg endpoints", {"depth": 0}),
        ("outer_two_rings", "Inherited BFS restricted to boundary depth at most one", {"depth": 1}),
        ("interior_monotone", "Inherited monotone-only BFS when both endpoints have depth at least two", {"monotone": "interior"}),
        ("monotone_only", "Every leg may only decrease Manhattan distance to its destination", {"monotone": "always"}),
        ("reverse_endpoints", "Treat the rowmajor-last endpoint as the start", {"reverse": True}),
        ("neighbor_r_d_l_u", "BFS tie order right, down, left, up", {"order": ((0, 1), (1, 0), (0, -1), (-1, 0))}),
        ("neighbor_d_l_r_u", "BFS tie order down, left, right, up", {"order": ((1, 0), (0, -1), (0, 1), (-1, 0))}),
        ("neighbor_l_u_r_d", "BFS tie order left, up, right, down", {"order": ((0, -1), (-1, 0), (0, 1), (1, 0))}),
        ("neighbor_u_l_d_r", "BFS tie order up, left, down, right", {"order": ((-1, 0), (0, -1), (1, 0), (0, 1))}),
        ("neighbor_d_u_l_r", "BFS tie order down, up, left, right", {"order": ((1, 0), (-1, 0), (0, -1), (0, 1))}),
        ("neighbor_l_r_u_d", "BFS tie order left, right, up, down", {"order": ((0, -1), (0, 1), (-1, 0), (1, 0))}),
        ("all_shortest_paths", "Paint the union of every shortest path for each leg", {"route": "all_shortest"}),
        ("all_reachable", "Flood every wall-connected open cell", {"route": "flood"}),
        ("vertical_then_horizontal", "Draw each leg as a vertical-then-horizontal L, preserving walls", {"route": "vertical_first"}),
        ("horizontal_then_vertical", "Draw each leg as a horizontal-then-vertical L, preserving walls", {"route": "horizontal_first"}),
        ("ignore_walls_on_route", "Use shortest routes through walls as though they were open", {"ignore_walls": True}),
        ("fill_leg_rectangle", "Fill open cells in each leg's endpoint rectangle", {"route": "box"}),
    ]
    if mode == "direct":
        definitions += [
            ("via_farthest", "Use the other declared setting: route through the farthest waypoint", {"mode": "via_farthest"}),
            ("leave_unchanged", "Leave the two markers and the maze unchanged", {"identity": True}),
        ]
    else:
        definitions += [
            ("skip_waypoint", "Skip stage A and draw the direct endpoint route", {"mode": "direct"}),
            ("manhattan_farthest", "Select the waypoint by Manhattan distance, ignoring wall detours", {"selector": "manhattan"}),
            ("farthest_from_goal", "Select the farthest waypoint from the other endpoint", {"selector": "goal"}),
            ("farthest_tie_last", "Break equal farthest-distance ties by rowmajor-last", {"tie": "last"}),
            ("farthest_tie_discovery", "Break farthest-distance ties by earliest BFS discovery", {"tie": "discovery"}),
            ("farthest_tie_discovery_last", "Break farthest-distance ties by latest BFS discovery", {"tie": "discovery_last"}),
            ("first_leg_only", "Paint only start to waypoint", {"leg": "first"}),
            ("second_leg_only", "Paint only waypoint to goal", {"leg": "second"}),
            ("farthest_boundary", "Choose the farthest open cell at boundary depth at most one", {"selector": "boundary"}),
            ("farthest_outer_boundary", "Choose the farthest open cell on the outermost grid edge", {"selector": "outer_boundary"}),
            ("exclude_endpoint_waypoints", "Exclude both endpoints from waypoint candidates", {"selector": "exclude_endpoints"}),
            ("waypoint_only", "Stop after stage A and paint only its selected waypoint", {"waypoint_only": True}),
            ("second_leg_from_goal", "Reverse only the second BFS, routing goal to waypoint", {"leg": "from_goal"}),
            ("farthest_leaf", "Choose only degree-one cells as waypoint candidates, when any exist", {"selector": "leaf"}),
            ("direct_plus_first", "Paint the direct endpoint route plus start to waypoint", {"leg": "direct_plus_first"}),
        ]
    return tuple(Rival(name, description, mode, spec) for name, description, spec in definitions)


def audit_lesson(episode, settings, *, execute=None):
    """Fit demos first; inspect queries only for survivors, retaining disagreements.

    execute(rival, grid) may substitute protected execution.  Runtime errors are
    returned as errors and never counted as teaching evidence.
    """
    train, test = episode["train"], episode["test"]
    records, findings, errors = [], [], []
    for rival in bank(settings):
        checked, excluded, survivor = 0, None, True
        for index, pair in enumerate(train):
            try:
                actual = execute(rival, pair["input"]) if execute else rival.apply(pair["input"])
            except Exception as exc:
                errors.append({"rival": rival.name, "split": "train", "index": index,
                               "error": f"{type(exc).__name__}: {exc}"})
                survivor = False
                break
            checked += 1
            if actual != pair["output"]:
                excluded, survivor = index, False
                break
        query_checks, disagreements = 0, []
        if survivor:
            for index, pair in enumerate(test):
                try:
                    actual = execute(rival, pair["input"]) if execute else rival.apply(pair["input"])
                except Exception as exc:
                    errors.append({"rival": rival.name, "split": "test", "index": index,
                                   "error": f"{type(exc).__name__}: {exc}"})
                    continue
                query_checks += 1
                if actual != pair["output"]:
                    disagreements.append(index)
                    findings.append({"rival": rival.name, "description": rival.description,
                                     "settings": dict(settings), "query_index": index,
                                     "input": pair["input"], "output": pair["output"],
                                     "rival_output": actual, "program": rival.program,
                                     "train": train})
        records.append({"rival": rival.name, "demo_checks": checked,
                        "first_demo_disagreement": excluded, "fits_all_demos": survivor,
                        "query_checks": query_checks, "query_disagreements": disagreements})
    return {"rivals": records, "findings": findings, "errors": errors}
