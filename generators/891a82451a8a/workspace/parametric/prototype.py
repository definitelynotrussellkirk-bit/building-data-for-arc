"""Direct waves and a two-stage corner relay; Python labels are diagnostic claims.

Use the native qualification or audit.py to execute labels through Racket.
The canonical generator, its reference, and its approval are untouched.
"""
from __future__ import annotations

import copy
from collections import Counter
from functools import lru_cache
import hashlib
import itertools
import json
from pathlib import Path
import random

CYCLE = (0, 5, 2, 8, 9, 6, 1, 3, 4)
MODES = ("direct", "corner_relay")
HERE = Path(__file__).resolve().parent
RIVALS = {
    "direct": (
        "other_setting", "chebyshev", "fixed_zero_phase", "fixed_center",
        "fixed_top_left", "reverse_step", "background_phase", "row_only",
        "column_only", "canonical_profile_only",
    ),
    "corner_relay": (
        "other_setting", "chebyshev_first", "chebyshev_second",
        "nearest_corner", "farthest_corner", "fixed_corner_0", "fixed_corner_1",
        "fixed_corner_2", "fixed_corner_3", "highest_phase", "last_tie",
        "numeric_color_min", "no_phase_transfer", "zero_relay_phase",
        "ignore_seed_phase", "reverse_step", "nearest_tie", "farthest_tie",
        "column_major_tie",
    ),
}
QUERY_RIVALS = {"direct": (), "corner_relay": (
    tuple(f"omit_corner_{i}" for i in range(4))
    + tuple("priority_" + "".join(map(str, order)) for order in itertools.permutations(range(4))
            if order != (0, 1, 2, 3))
)}


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _mode(settings):
    if type(settings) is not dict or set(settings) != {"mode"}:
        raise ValueError("settings must contain exactly 'mode'")
    if type(settings["mode"]) is not str or settings["mode"] not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    return settings["mode"]


def analyze(grid):
    if (type(grid) is not list or not 5 <= len(grid) <= 30
            or type(grid[0]) is not list or not 5 <= len(grid[0]) <= 30):
        raise ValueError("grid dimensions must be 5..30")
    h, w = len(grid), len(grid[0])
    if any(type(row) is not list or len(row) != w
           or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    counts = Counter(v for row in grid for v in row)
    bg, count = counts.most_common(1)[0]
    if bg == 0 or count != h * w - 1 or len(counts) != 2:
        raise ValueError("need one seed on a uniform nonzero modal background")
    r, c = next((r, c) for r in range(h) for c in range(w) if grid[r][c] != bg)
    color = grid[r][c]
    if color not in CYCLE:
        raise ValueError("seed must belong to the canonical color cycle")
    return h, w, r, c, CYCLE.index(color), bg


def intermediate(grid):
    h, w, sr, sc, phase, _ = analyze(grid)
    corners = ((0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1))
    phases = [(phase + abs(r - sr) + abs(c - sc)) % 9 for r, c in corners]
    chosen = min(range(4), key=lambda i: (phases[i], i))
    return {"seed": [sr, sc], "seed_phase": phase,
            "corner_phases": phases, "corner_colors": [CYCLE[p] for p in phases],
            "relay": list(corners[chosen]), "relay_phase": phases[chosen],
            "selected_corner_index": chosen}


def _extra_corner(state, rival):
    """Exact corner selector for fixed-subset and fixed-priority diagnostic rivals."""
    order = list(range(4))
    if rival.startswith("omit_corner_"):
        order.remove(int(rival[-1]))
    elif rival.startswith("priority_"):
        order = list(map(int, rival.split("_")[1]))
    else:
        raise ValueError("unknown extra corner selector")
    return min(order, key=lambda i: state["corner_phases"][i])


def solve(grid, settings, rival=None):
    """Independent Python diagnostic mirror, also used for constructive teaching."""
    mode = _mode(settings)
    if rival is not None and rival not in RIVALS[mode] + QUERY_RIVALS[mode]:
        raise ValueError(f"unknown {mode} rival {rival!r}")
    if rival == "other_setting":
        return solve(grid, {"mode": MODES[1 - MODES.index(mode)]})
    h, w, sr, sc, start, bg = analyze(grid)
    if mode == "direct":
        ar, ac, phase = sr, sc, start
        if rival == "fixed_zero_phase":
            phase = 0
        elif rival == "background_phase":
            phase = CYCLE.index(bg) if bg in CYCLE else 0
        elif rival == "fixed_center":
            ar, ac = h // 2, w // 2
        elif rival == "fixed_top_left":
            ar, ac = 0, 0
        elif rival == "canonical_profile_only" and (h, w, bg) != (8, 8, 7):
            return copy.deepcopy(grid)
    else:
        corners = ((0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1))
        distances = [abs(r - sr) + abs(c - sc) for r, c in corners]
        first_distances = ([max(abs(r - sr), abs(c - sc)) for r, c in corners]
                           if rival == "chebyshev_first" else distances)
        first_phase = 0 if rival == "ignore_seed_phase" else start
        phases = [(first_phase + d) % 9 for d in first_distances]
        scores = phases
        if rival in ("nearest_corner", "farthest_corner"):
            scores = distances
        elif rival == "numeric_color_min":
            scores = [CYCLE[p] for p in phases]
        choose_max = rival in ("highest_phase", "farthest_corner")
        indices = (list(range(3, -1, -1)) if rival == "last_tie"
                   else [0, 2, 1, 3] if rival == "column_major_tie" else list(range(4)))
        if rival and rival.startswith("omit_corner_"):
            indices.remove(int(rival[-1]))
        elif rival and rival.startswith("priority_"):
            indices = list(map(int, rival.split("_")[1]))
        if rival in ("nearest_tie", "farthest_tie"):
            sign = -1 if rival == "farthest_tie" else 1
            chosen = min(indices, key=lambda i: (phases[i], sign * distances[i], i))
        else:
            chosen = min(indices, key=lambda i: -scores[i] if choose_max else scores[i])
        if rival and rival.startswith("fixed_corner_"):
            chosen = int(rival[-1])
        ar, ac = corners[chosen]
        phase = phases[chosen]
        if rival == "no_phase_transfer":
            phase = start
        elif rival == "zero_relay_phase":
            phase = 0

    def color(r, c):
        dr, dc = abs(r - ar), abs(c - ac)
        distance = (max(dr, dc) if rival in ("chebyshev", "chebyshev_second")
                    else dr if rival == "row_only" else dc if rival == "column_only"
                    else dr + dc)
        return CYCLE[(phase + (-distance if rival == "reverse_step" else distance)) % 9]
    return [[color(r, c) for c in range(w)] for r in range(h)]


def _racket(mode, rival=None):
    """Materialize standalone rules; no runtime mutation or Python label oracle."""
    if rival == "other_setting":
        return program({"mode": MODES[1 - MODES.index(mode)]})
    first_distance = ("(max (abs (- r sr)) (abs (- c sc)))"
                      if rival == "chebyshev_first" else "(+ (abs (- r sr)) (abs (- c sc)))")
    wave_start = "0" if rival == "ignore_seed_phase" else "seed-start"
    scores = "phases"
    if rival in ("nearest_corner", "farthest_corner"):
        scores = "distances"
    elif rival == "numeric_color_min":
        scores = "corner-colors"
    extreme = "max" if rival in ("highest_phase", "farthest_corner") else "min"
    indices = [i for i in range(4) if rival != f"omit_corner_{i}"]
    extrema = " ".join(f"(list-ref scores {i})" for i in indices)
    order = ("(list 3 2 1 0)" if rival == "last_tie"
             else "(list 0 2 1 3)" if rival == "column_major_tie"
             else "(list " + " ".join(map(str, indices)) + ")" if len(indices) < 4
             else "(range 0 4)")
    if rival and rival.startswith("priority_"):
        order = "(list " + " ".join(rival.split("_")[1]) + ")"
    chosen = (f"(find-first (lambda (i) (= (list-ref scores i) best)) {order})")
    if rival in ("nearest_tie", "farthest_tie"):
        fn, sentinel = ("max", -1) if rival == "farthest_tie" else ("min", 1000)
        terms = " ".join(f"(if (= (list-ref phases {i}) best) (list-ref distances {i}) {sentinel})" for i in indices)
        chosen = (f"(find-first (lambda (i) (and (= (list-ref phases i) best) "
                  f"(= (list-ref distances i) ({fn} {terms})))) {order})")
    if rival and rival.startswith("fixed_corner_"):
        chosen = rival[-1]
    if mode == "direct":
        ar, ac, out_start = "sr", "sc", "seed-start"
        if rival == "fixed_zero_phase":
            out_start = "0"
        elif rival == "background_phase":
            out_start = "(if (= bg 7) 0 (find-first (lambda (i) (= (list-ref cycle i) bg)) (range 0 9)))"
        elif rival == "fixed_center":
            ar, ac = "(quotient h 2)", "(quotient w 2)"
        elif rival == "fixed_top_left":
            ar, ac = "0", "0"
    else:
        ar, ac, out_start = "(first relay)", "(second relay)", "(list-ref phases chosen)"
        if rival == "no_phase_transfer":
            out_start = "seed-start"
        elif rival == "zero_relay_phase":
            out_start = "0"
    distance = "(+ (abs (- r ar)) (abs (- c ac)))"
    if rival in ("chebyshev", "chebyshev_second"):
        distance = "(max (abs (- r ar)) (abs (- c ac)))"
    elif rival == "row_only":
        distance = "(abs (- r ar))"
    elif rival == "column_only":
        distance = "(abs (- c ac))"
    op = "-" if rival == "reverse_step" else "+"
    output = f"(cellmap g (r c v) (list-ref cycle (modulo ({op} output-start {distance}) 9)))"
    if rival == "canonical_profile_only":
        output = f"(if (and (= h 8) (= w 8) (= bg 7)) {output} g)"
    return f'''(rule! (lambda (g)
  (let* ((h (rows g)) (w (cols g)) (bg (mode g))
         (seed (first (positions-of g (lambda (v) (!= v bg)))))
         (sr (first seed)) (sc (second seed))
         (cycle (list 0 5 2 8 9 6 1 3 4))
         (seed-start (find-first (lambda (i) (= (list-ref cycle i) (at g sr sc))) (range 0 9)))
         (first-wave (cellmap g (r c v) (list-ref cycle (modulo (+ {wave_start} {first_distance}) 9))))
         (corners (list (list 0 0) (list 0 (- w 1)) (list (- h 1) 0) (list (- h 1) (- w 1))))
         (distances (map (lambda (p) (+ (abs (- (first p) sr)) (abs (- (second p) sc)))) corners))
         (corner-colors (map (lambda (p) (at first-wave (first p) (second p))) corners))
         (phases (map (lambda (v) (find-first (lambda (i) (= (list-ref cycle i) v)) (range 0 9))) corner-colors))
         (scores {scores})
         (best ({extreme} {extrema}))
         (chosen {chosen}) (relay (list-ref corners chosen))
         (ar {ar}) (ac {ac}) (output-start {out_start}))
    {output})))'''


def program(settings):
    mode = _mode(settings)
    return (HERE / "canonical.rkt").read_text() if mode == "direct" else _racket(mode)


def rival_program(settings, rival):
    mode = _mode(settings)
    if rival not in RIVALS[mode] + QUERY_RIVALS[mode]:
        raise ValueError("undeclared rival")
    return _racket(mode, rival)


def teaching_report(demos, settings):
    mode = _mode(settings)
    if type(demos) is not list or not 2 <= len(demos) <= 6:
        raise ValueError("teaching requires 2..6 demonstrations")
    for pair in demos:
        output = pair["output"]
        if (type(output) is not list or not output
                or any(type(row) is not list or not row
                       or any(type(v) is not int or not 0 <= v <= 9 for v in row)
                       for row in output)
                or output != solve(pair["input"], settings)):
            raise ValueError("demonstration label disagrees with the intended rule")
    refutations = {}
    for rival in RIVALS[mode]:
        refutations[rival] = [i for i, p in enumerate(demos)
                             if solve(p["input"], settings, rival) != p["output"]]
    return {"all_refuted": all(refutations.values()), "refutations": refutations,
            "uses_query_answers": False, "scope": "finite declared rivals only"}


def query_safety_report(demos, queries, settings):
    """Fit extra rivals on demos only, then compare predictions on query inputs.

    Query answers never participate in fitting or this agreement check.
    """
    mode = _mode(settings)
    teaching_report(demos, settings)
    survivors = [name for name in QUERY_RIVALS[mode]
                 if all(solve(p["input"], settings, name) == p["output"] for p in demos)]
    safe = [all(solve(p["input"], settings, name) == solve(p["input"], settings)
                for name in survivors) for p in queries]
    return {"survivors_from_demos": survivors, "query_agreement": safe,
            "all_queries_safe": all(safe), "uses_query_answers": False}


def _rng(seed, stream):
    digest = hashlib.sha256(f"891a82451a8a/corner-relay/v1/{seed}/{stream}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _input(rng, h, w, region=None):
    color = rng.choice(CYCLE)
    bg = rng.choice([v for v in range(1, 10) if v != color])
    if region == "corner":
        r, c = rng.choice([(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)])
    elif region == "edge":
        r, c = rng.choice([(0, rng.randrange(1, w - 1)), (h - 1, rng.randrange(1, w - 1)),
                           (rng.randrange(1, h - 1), 0), (rng.randrange(1, h - 1), w - 1)])
    elif region == "interior":
        r, c = rng.randrange(1, h - 1), rng.randrange(1, w - 1)
    else:
        r, c = rng.randrange(h), rng.randrange(w)
    g = [[bg] * w for _ in range(h)]
    g[r][c] = color
    return g


@lru_cache(maxsize=32)
def _inputs(seed):
    """Select two joint teaching inputs, then independent stable query streams.

    Settings never enter this procedure. A bounded pair cover makes both modes'
    demonstrations refute all their declared rivals without extra demo tokens.
    """
    rng = _rng(seed, "teaching")
    universe = [(mode, rival) for mode in MODES for rival in RIVALS[mode]]
    full = (1 << len(universe)) - 1
    candidates = []
    pair = None
    for attempt in range(384):
        g = _input(rng, rng.randint(6, 16), rng.randint(6, 16))
        h, w, r, c, _, _ = analyze(g)
        if max(r, h - 1 - r) + max(c, w - 1 - c) < 9:
            continue  # Every core demo exposes all cycle transitions, including wrap.
        intended = {mode: solve(g, {"mode": mode}) for mode in MODES}
        mask = sum(1 << i for i, (mode, rival) in enumerate(universe)
                   if solve(g, {"mode": mode}, rival) != intended[mode])
        for old, old_mask in candidates:
            if old_mask | mask == full and analyze(old)[4] != analyze(g)[4] and analyze(old)[5] != analyze(g)[5]:
                pair = [old, g]
                break
        if pair is not None:
            break
        candidates.append((g, mask))
    if pair is None:
        raise RuntimeError("no joint two-demo teaching cover within 384 candidates")
    seen = {json.dumps(g) for g in pair}
    demos = pair[:]
    taught = {intermediate(g)["selected_corner_index"] for g in demos}
    for extra, (h, w) in enumerate(((8, 8), (13, 17), (18, 11), (5, 8))):
        target = rng.choice(sorted(set(range(4)) - taught)) if extra < 2 else None
        for _ in range(256):
            g = _input(rng, h, w)
            key = json.dumps(g)
            winner = intermediate(g)["selected_corner_index"]
            if key not in seen and (target is None or winner == target):
                demos.append(g)
                seen.add(key)
                taught.add(winner)
                break
        else:
            raise RuntimeError("distinct demonstration sampling exhausted")
    return json.dumps({"demos": demos, "teaching_candidates": attempt + 1})


@lru_cache(maxsize=96)
def _query_inputs(seed, demos):
    inputs = json.loads(_inputs(seed))["demos"]
    seen = {json.dumps(g) for g in inputs}
    taught = sorted({intermediate(g)["selected_corner_index"] for g in inputs[:demos]})
    states = [intermediate(g) for g in inputs[:demos]]
    survivors = [name for name in QUERY_RIVALS["corner_relay"]
                 if all(_extra_corner(s, name) == s["selected_corner_index"] for s in states)]
    qrng = _rng(seed, "queries")
    queries = []
    shapes = [(5, 5), (14, 23), (23, 18), (30, 30), (18, 30), (30, 9), (9, 30), (21, 25)]
    regions = ("corner", "edge", "interior", "interior", None, "edge", "corner", None)
    for index, ((h, w), region) in enumerate(zip(shapes, regions)):
        target = taught[(index + seed) % len(taught)]
        for _ in range(256):
            g = _input(qrng, h, w, region)
            key = json.dumps(g)
            state = intermediate(g)
            if (key not in seen and state["selected_corner_index"] == target
                    and all(_extra_corner(state, name) == target for name in survivors)):
                queries.append(g)
                seen.add(key)
                break
        else:
            raise RuntimeError("distinct query sampling exhausted")
    return json.dumps(queries)


def generate(seed, settings, demos=3, queries=4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 8, "queries")
    mode = _mode(settings)
    inputs = json.loads(_inputs(seed))
    pairs = lambda seq: [{"input": g, "output": solve(g, settings)} for g in seq]
    train = pairs(inputs["demos"][:demos])
    report = teaching_report(train, settings)
    if not report["all_refuted"]:
        raise RuntimeError("constructive teaching contract failed")
    tests = pairs(json.loads(_query_inputs(seed, min(demos, 4)))[:queries])
    query_report = query_safety_report(train, tests, settings)
    if not query_report["all_queries_safe"]:
        raise RuntimeError("an extra rival survives demos and changes a query")
    return {"train": train, "test": tests,
            "program_solution": program(settings), "settings": {"mode": mode},
            "seed": seed, "teaching": report,
            "query_safety": query_report,
            "teaching_candidates": inputs["teaching_candidates"],
            "label_status": "python_claims_until_protected_racket_execution"}


def turn_challenge(episode, index):
    """Project a turn without future inputs, answers, private settings or totals.

    This is a standalone visible challenge at any index. The existing consumer
    sends the demonstrations only on turn zero and sends the new query input on
    subsequent turns. This helper does not implement a controller.
    """
    _integer(index, 0, len(episode["test"]) - 1, "query index")
    return copy.deepcopy({"train": [{"input": p["input"], "output": p["output"]}
                                    for p in episode["train"]],
                          "test": [{"input": episode["test"][index]["input"]}]})
