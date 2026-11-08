"""gen3: recolor base noise (A->B), then CONNECT each aligned marker pair with a
straight LINE in a NEW color. Markers come in pairs sharing a row (or a column);
each pair's two cells are joined by a segment of the NEW color, which is absent
from the input. Composes a recolor with the draw-line-between-markers step.

Transform: recolor A->B, then for each marker line/col draw-line between its two
markers in NEW.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.generic.concepts.draw_markers import parity_check

VERSION = "1.2.0"
GENERATOR_ID = "draw_markers.gen3"


def _dims(g):
    return len(g), len(g[0])


def _recolor(g, src, dst):
    return [[dst if v == src else v for v in row] for row in g]


def _line_cells(r1, c1, r2, c2):
    """Byte-exact replica of prelude line-cells (Bresenham)."""
    dr = abs(r2 - r1)
    dc = abs(c2 - c1)
    sr = 1 if r1 < r2 else -1
    sc = 1 if c1 < c2 else -1
    r, c = r1, c1
    err = dr - dc
    acc = []
    while True:
        acc.append((r, c))
        if r == r2 and c == c2:
            return acc
        e2 = 2 * err
        nr = r + sr if e2 > -dc else r
        nc = c + sc if e2 < dr else c
        ne = err + ((-dc) if e2 > -dc else 0) + (dr if e2 < dr else 0)
        r, c, err = nr, nc, ne


def _draw_line(g, r1, c1, r2, c2, color):
    out = [row[:] for row in g]
    for (r, c) in _line_cells(r1, c1, r2, c2):
        out[r][c] = color
    return out


def _apply(g, *, noise_a, noise_b, axis, pairs, new_color):
    """pairs: list of (a, b) endpoint coords, in the same order Racket folds."""
    out = _recolor(g, noise_a, noise_b)
    for ((r1, c1), (r2, c2)) in pairs:
        out = _draw_line(out, r1, c1, r2, c2, new_color)
    return out


def _build_input(ctx, sample_index, *, noise_a, marker_color, axis, difficulty, bg_color=0):
    rng = ctx.draw_rng(f"input.{sample_index}")
    if difficulty == "easy":
        h, w, npair, dens = rng.randint(8, 11), rng.randint(8, 11), rng.randint(1, 2), 0.10
    elif difficulty == "hard":
        h, w, npair, dens = rng.randint(20, 28), rng.randint(20, 28), rng.randint(3, 5), 0.16
    else:
        h, w, npair, dens = rng.randint(13, 19), rng.randint(13, 19), rng.randint(2, 4), 0.13
    g = [[bg_color] * w for _ in range(h)]
    for r in range(h):
        for c in range(w):
            if rng.random() < dens:
                g[r][c] = noise_a
    # Each pair occupies a UNIQUE row (or column): the Racket program connects
    # all markers on one line into a single segment, so two pairs may never
    # share a line or parity would break.
    pairs = []
    if axis == "row":
        rows = list(range(h))
        rng.shuffle(rows)
        for r in rows:
            if len(pairs) >= npair:
                break
            if w < 3:
                continue
            c1 = rng.randint(0, w - 2)
            c2 = rng.randint(c1 + 1, w - 1)
            pairs.append(((r, c1), (r, c2)))
        pairs.sort()  # row-major by first endpoint (one pair per row)
    else:  # axis == "col"
        cols = list(range(w))
        rng.shuffle(cols)
        for c in cols:
            if len(pairs) >= npair:
                break
            if h < 3:
                continue
            r1 = rng.randint(0, h - 2)
            r2 = rng.randint(r1 + 1, h - 1)
            pairs.append(((r1, c), (r2, c)))
        pairs.sort()  # one pair per column
    # place markers (overwriting any noise at those cells)
    for ((r1, c1), (r2, c2)) in pairs:
        g[r1][c1] = marker_color
        g[r2][c2] = marker_color
    return g, pairs


def generate_task(seed, *, difficulty="medium", n_train=3, n_test=1):
    ctx = gen_ctx(seed=seed, sample_index=0, version=VERSION,
                  task_id=GENERATOR_ID, difficulty=difficulty)
    pal = ctx.draw_rng("palette")
    # Keep the nonzero-background fix as a MIXED axis. The prior patch moved this
    # generator from 0% to 100% colored backgrounds, which overshoots the eval
    # convention (~2/3 nonzero modal background) and makes the concept stream a
    # biased background specialist.
    use_nonzero_bg = pal.randrange(3) > 0
    if use_nonzero_bg:
        bg_color, noise_a, marker_color, new_color, noise_b = pal.sample(range(1, 10), 5)
    else:
        bg_color = 0
        noise_a, marker_color, new_color, noise_b = pal.sample(range(1, 10), 4)
    axis = pal.choice(["row", "col"])

    train, test = [], []
    for i in range(n_train):
        g, pairs = _build_input(ctx, i, noise_a=noise_a, marker_color=marker_color,
                                axis=axis, difficulty=difficulty, bg_color=bg_color)
        out = _apply(g, noise_a=noise_a, noise_b=noise_b, axis=axis,
                     pairs=pairs, new_color=new_color)
        train.append({"input": g, "output": out})
    for j in range(n_test):
        g, pairs = _build_input(ctx, 100 + j, noise_a=noise_a, marker_color=marker_color,
                                axis=axis, difficulty=difficulty, bg_color=bg_color)
        out = _apply(g, noise_a=noise_a, noise_b=noise_b, axis=axis,
                     pairs=pairs, new_color=new_color)
        test.append({"input": g, "output": out})

    # Racket: recolor noise, then for each row (or col) that holds markers, draw
    # a line between the two extreme marker cells along that line.
    if axis == "row":
        # group marker cells by row, connect min-col..max-col
        body = (
            f"(let* ([ms (find-color g {marker_color})]"
            f"       [rs (sort (remove-duplicates (map first ms)) <)])"
            f" (foldl (lambda (r acc)"
            f"   (let* ([cs (map second (filter (lambda (m) (= (first m) r)) ms))]"
            f"          [c1 (apply min cs)] [c2 (apply max cs)])"
            f"     (draw-line acc r c1 r c2 {new_color})))"
            f"  (recolor g {noise_a} {noise_b}) rs))"
        )
    else:
        body = (
            f"(let* ([ms (find-color g {marker_color})]"
            f"       [cs (sort (remove-duplicates (map second ms)) <)])"
            f" (foldl (lambda (c acc)"
            f"   (let* ([rs (map first (filter (lambda (m) (= (second m) c)) ms))]"
            f"          [r1 (apply min rs)] [r2 (apply max rs)])"
            f"     (draw-line acc r1 c r2 c {new_color})))"
            f"  (recolor g {noise_a} {noise_b}) cs))"
        )
    program = f"(rule! (lambda (g) {body}))"
    return {"train": train, "test": test, "program": program,
            "chain": ["recolor", "connect_marker_pairs", "modal_background_mix"],
            "new_color": new_color, "marker_color": marker_color, "bg_color": bg_color,
            "meta": {"version": VERSION, "bg_color": bg_color,
                     "nonzero_bg": bool(bg_color),
                     "noise_a": noise_a, "noise_b": noise_b,
                     "axis": axis}}


if __name__ == "__main__":
    parity_check(generate_task, n=25, version_label=GENERATOR_ID)



def self_check_task(task) -> list[str]:
    errors: list[str] = []
    pairs = list(task.get("train", [])) + list(task.get("test", []))
    if not pairs:
        return ["task must contain train/test pairs"]
    new_color = task.get("new_color")
    marker_color = task.get("marker_color")
    meta = task.get("meta", {})
    bg_color = meta.get("bg_color")
    axis = meta.get("axis")
    if axis not in ("row", "col"):
        errors.append("meta.axis must be row or col")
    if not isinstance(new_color, int) or not isinstance(marker_color, int):
        errors.append("task must expose integer marker_color and new_color")
        return errors
    for pair in pairs:
        g = pair["input"]
        out = pair["output"]
        if not g or not out or len(g) != len(out) or len(g[0]) != len(out[0]):
            errors.append("input/output must be nonempty same-sized grids")
            continue
        if any(new_color in row for row in g):
            errors.append("new line color must be absent from the input")
        if bg_color is not None:
            flat = [v for row in out for v in row]
            if flat.count(bg_color) <= len(flat) // 2:
                errors.append("nonzero background should remain the modal output color")
        markers = [(r, c) for r, row in enumerate(g) for c, v in enumerate(row) if v == marker_color]
        if len(markers) < 2 or len(markers) % 2 != 0:
            errors.append("marker cells must form one or more endpoint pairs")
        if axis == "row":
            by = {}
            for r, c in markers:
                by.setdefault(r, []).append(c)
            if any(len(cs) != 2 for cs in by.values()):
                errors.append("row-mode examples must have exactly two markers per active row")
            for r, cs in by.items():
                if len(cs) == 2 and not all(out[r][c] == new_color for c in range(min(cs), max(cs) + 1)):
                    errors.append("output is missing a drawn horizontal marker-connection line")
        elif axis == "col":
            by = {}
            for r, c in markers:
                by.setdefault(c, []).append(r)
            if any(len(rs) != 2 for rs in by.values()):
                errors.append("col-mode examples must have exactly two markers per active column")
            for c, rs in by.items():
                if len(rs) == 2 and not all(out[r][c] == new_color for r in range(min(rs), max(rs) + 1)):
                    errors.append("output is missing a drawn vertical marker-connection line")
    return errors
