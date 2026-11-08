"""Frequency-fill lessons with a genuinely input-dependent row restriction.

Labels here are claims; native qualification independently executes the exact
Racket programs. No production generator or canonical authority is modified.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import random


SCOPES = ("global", "modal_row")
CANONICAL_PROGRAM = """(rule! (lambda (g)
         (let ((h (rows g))
               (w (cols g))
               (m (mode g)))
           (grid-from-fn h w (lambda (r c) m)))))"""
MODAL_ROW_PROGRAM = """(rule! (lambda (g)
  (let* ((m (mode g))
         (amounts (map (lambda (row) (count (lambda (x) (= x m)) row)) g))
         (r (index-of amounts (apply max amounts)))
         (eligible (filter (lambda (x) (and (not (= x 0)) (not (= x m))))
                           (list-ref g r)))
         (answer (mode (list eligible))))
    (grid-from-fn (rows g) (cols g) (lambda (r c) answer)))))"""


def _settings(settings):
    if (type(settings) is not dict or set(settings) != {"scope"}
            or type(settings["scope"]) is not str or settings["scope"] not in SCOPES):
        raise ValueError("settings must be exactly {'scope': 'global'|'modal_row'}")
    return settings["scope"]


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def program(settings):
    """Return the exact native rule; the default is byte-exact canonical text."""
    return CANONICAL_PROGRAM if _settings(settings) == "global" else MODAL_ROW_PROGRAM


def _winner(values, *, exclude=(), fallback=0, strict=False):
    counts = Counter(v for v in values if v not in exclude)
    if not counts:
        if strict:
            raise ValueError("empty eligible color set")
        return fallback
    ranked = sorted(counts, key=lambda c: (-counts[c], c))
    if strict and len(ranked) > 1 and counts[ranked[0]] == counts[ranked[1]]:
        raise ValueError("frequency winner must be unique")
    return ranked[0]


def analyze(grid):
    """Validate the shared grammar and expose authoring-only intermediates."""
    if (type(grid) is not list or not 3 <= len(grid) <= 30
            or type(grid[0]) is not list or not 3 <= len(grid[0]) <= 30):
        raise ValueError("grid must have 3..30 rows and columns")
    w = len(grid[0])
    if any(type(row) is not list or len(row) != w
           or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    flat = [v for row in grid for v in row]
    counts = Counter(flat)
    if len(set(flat) - {0}) < 3:
        raise ValueError("need at least three nonzero colors")
    m = _winner(flat, exclude=(0,), strict=True)
    row_counts = [row.count(m) for row in grid]
    peak = max(row_counts)
    if row_counts.count(peak) != 1:
        raise ValueError("modal-color row must be unique")
    selected = row_counts.index(peak)
    eligible = [v for v in grid[selected] if v not in (0, m)]
    local = _winner(eligible, strict=True)
    return {"global_mode": m, "selected_row": selected, "local_mode": local,
            "global_counts": dict(sorted(counts.items())), "row_counts": row_counts,
            "local_counts": dict(sorted(Counter(eligible).items())),
            "height": len(grid), "width": w}


def rival_colors(grid):
    """Finite, total authoring rivals; ties choose the smallest color.

    Row/column alternatives remove both zero and the true global mode, with
    that global mode as the explicit fallback for an empty eligible region.
    These rivals are a bounded teaching check, never a uniqueness theorem.
    """
    info = analyze(grid)
    m, r = info["global_mode"], info["selected_row"]
    flat = [v for row in grid for v in row]
    counts = Counter(v for v in flat if v)
    ranked = sorted(counts, key=lambda c: (-counts[c], c))
    columns = [list(col) for col in zip(*grid)]
    ci = max(range(len(columns)), key=lambda c: columns[c].count(m))
    restricted = lambda row: _winner(row, exclude=(0, m), fallback=m)
    result = {
        "global": m, "modal_row": info["local_mode"],
        "global_runner_up": ranked[1],
        "overall_mode": _winner(flat),
        "first_row": restricted(grid[0]), "last_row": restricted(grid[-1]),
        "modal_column": restricted(columns[ci]),
        "local_including_zero": _winner(grid[r], exclude=(m,), fallback=m),
        "local_including_mode": _winner(grid[r], exclude=(0,), fallback=m),
        "rarest_nonzero": min(counts, key=lambda c: (counts[c], c)),
        "min_color": min(counts), "max_color": max(counts),
        "first_nonzero": next(v for v in flat if v),
    }
    result.update({f"constant_{c}": c for c in range(1, 10)})
    return result


def _rng(seed, stream, index):
    digest = hashlib.sha256(f"modal-row-v1:{seed}:{stream}:{index}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _scene(rng, h, w, profile):
    """Construct row counts, then bounded global color budgets; never pad."""
    if h == w == 3:
        m, t, a, b = rng.sample(range(1, 10), 4)
        grid = ([[m, m, t], [m, 0, 0], [a, 0, 0]] if profile == 2 else
                [[m, m, t], [m, a, a], [0, b, 0]])
        rng.shuffle(grid)
        for row in grid:
            rng.shuffle(row)
        analyze(grid)
        return grid

    for _ in range(80):
        palette = rng.sample(range(1, 10), rng.randint(4, 7))
        m, t = palette[:2]
        others = palette[2:]
        selected = rng.randrange(h)
        k = rng.randint(2, max(2, w // 2))
        row_counts = [rng.randint(max(1, k - 3), k - 1) for _ in range(h)]
        row_counts[selected] = k
        total_m = sum(row_counts)
        remainder = w - k
        # Profiles alternate ordinary rows, target-heavy rows and zero decoys.
        if profile == 0:
            nt = remainder // 2 + 1
        elif profile == 1:
            nt = rng.randint(max(1, remainder // 2), remainder)
        else:
            nt = max(1, remainder // 3)
        if nt >= total_m:
            continue
        selected_values = [m] * k + [t] * nt
        local_counts = Counter({t: nt})
        while len(selected_values) < w:
            choices = [c for c in others if local_counts[c] < nt - 1]
            if profile != 0:
                choices += [0] * (3 if profile == 2 else 1)
            if not choices:
                break
            c = rng.choice(choices)
            selected_values.append(c)
            local_counts[c] += 1
        if len(selected_values) != w:
            continue
        z0 = selected_values.count(0)
        if profile == 2:
            total_zero = max(z0, total_m + rng.randint(1, max(1, h * w // 10)))
        elif profile == 1:
            total_zero = max(z0, rng.randint(0, max(0, min(total_m - 1, h * w // 7))))
        else:
            total_zero = 0
        cells_left = h * w - total_m - total_zero
        allocated = Counter(v for v in selected_values if v not in (0, m))
        if cells_left < sum(allocated.values()) or total_zero > h * w - total_m:
            continue
        # Keep several distractor colors real and cap each below the global mode.
        for color in palette[1:]:
            allocated[color] = max(1, allocated[color])
        remaining = cells_left - sum(allocated.values())
        if remaining < 0 or any(n >= total_m for n in allocated.values()):
            continue
        weights = {c: rng.randint(1, 7) for c in palette[1:]}
        failed = False
        for _ in range(remaining):
            choices = [c for c in palette[1:] if allocated[c] < total_m - 1]
            if not choices:
                failed = True
                break
            c = rng.choices(choices, weights=[weights[c] for c in choices])[0]
            allocated[c] += 1
        if failed:
            continue
        rest = [0] * (total_zero - z0)
        for color, amount in allocated.items():
            rest.extend([color] * (amount - selected_values.count(color)))
        rng.shuffle(rest)
        cursor = 0
        grid = []
        for r, nm in enumerate(row_counts):
            if r == selected:
                row = selected_values[:]
            else:
                row = [m] * nm + rest[cursor:cursor + w - nm]
                cursor += w - nm
            rng.shuffle(row)
            grid.append(row)
        if cursor != len(rest):
            raise RuntimeError("internal color budget mismatch")
        analyze(grid)
        return grid
    raise RuntimeError(f"bounded scene construction exhausted for {h}x{w} profile {profile}")


def _demo_inputs(seed):
    """Select two constructive witnesses using only demo predictions.

    No queries or query answers are consulted. An exact finite cover rejects
    every declared wrong rival under BOTH settings, so a setting cannot leak
    through a different input sampler. Extra demos add scale/color variation.
    """
    candidates, masks = [], []
    keys = None
    dims = ((5, 7), (6, 9), (7, 5), (8, 11), (9, 7), (5, 9))
    for i in range(96):
        h, w = dims[i % len(dims)]
        grid = _scene(_rng(seed, "demo", i), h, w, i % 3)
        predictions = rival_colors(grid)
        if keys is None:
            keys = [(s, name) for s in SCOPES for name in predictions if name != s]
        mask = sum(1 << j for j, (s, name) in enumerate(keys)
                   if predictions[name] != predictions[s])
        full = (1 << len(keys)) - 1
        for j, other_mask in enumerate(masks):
            if (mask | other_mask) == full:
                return [candidates[j], grid]
        candidates.append(grid)
        masks.append(mask)
    raise RuntimeError("no two-demo cover of the finite rivals in 96 constructive candidates")


def _filled(grid, color):
    return [[color] * len(grid[0]) for _ in grid]


def generate(seed, settings, demos, queries):
    """Generate one lesson, with independent bounded demo/query counts.

    Query streams do not depend on demos, queries, or scope. Consequently a
    one-query and four-query request have exactly the same first visible turn.
    """
    _integer(seed, 0, 2**63 - 1, "seed")
    scope = _settings(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    trains = _demo_inputs(seed)
    for i in range(2, demos):
        h, w = ((3, 3), (11, 13), (13, 17), (17, 19))[i - 2]
        trains.append(_scene(_rng(seed, "extra_demo", i), h, w, i % 3))
    tests = []
    for i in range(queries):
        rng = _rng(seed, "query", i)
        h, w = ((3, 3), (8, 13), (rng.randint(21, 29), rng.randint(21, 29)), (30, 30))[i]
        tests.append(_scene(rng, h, w, i % 3))
    seen = set()
    for grid in trains + tests:
        key = tuple(map(tuple, grid))
        if key in seen:
            raise RuntimeError("duplicate input in independently generated lesson")
        seen.add(key)
    def pairs(grids):
        result = []
        for grid in grids:
            info = analyze(grid)
            color = info["global_mode" if scope == "global" else "local_mode"]
            result.append({"input": grid, "output": _filled(grid, color)})
        return result
    return {"train": pairs(trains), "test": pairs(tests), "program_solution": program(settings)}
