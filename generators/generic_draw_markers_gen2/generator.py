"""gen2: recolor markers (marker_color -> NEW), then SMEAR that NEW color in a
fixed direction -- from each marker a ray of the NEW color shoots until it hits
a wall or a base-noise obstacle. Markers (a distinct color) drive WHERE rays
originate; NEW is absent from the input. Composes recolor + ray/smear.

Transform: (smear-color (recolor g marker NEW) NEW dir).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.generic.concepts.draw_markers import parity_check

VERSION = "1.3.0"
GENERATOR_ID = "draw_markers.gen2"

_DELTAS = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}


def _dims(g):
    return len(g), len(g[0])


def _recolor(g, src, dst):
    return [[dst if v == src else v for v in row] for row in g]


def _smear(g, color, direction, bg=0):
    """Byte-exact replica of prelude (smear-color g color direction bg):
    source cells from find-color on ORIGINAL g (row-major); each ray walks the
    accumulator and stops at a non-bg cell or wall."""
    h, w = _dims(g)
    dr, dc = _DELTAS[direction]
    out = [row[:] for row in g]
    sources = [(r, c) for r in range(h) for c in range(w) if g[r][c] == color]
    for (sr, sc) in sources:
        r, c = sr + dr, sc + dc
        while 0 <= r < h and 0 <= c < w and out[r][c] == bg:
            out[r][c] = color
            r += dr
            c += dc
    return out


def _apply(g, *, marker_color, new_color, direction, bg_color=0):
    return _smear(_recolor(g, marker_color, new_color), new_color, direction, bg=bg_color)


def _build_input(ctx, sample_index, *, noise_color, marker_color, direction, difficulty, bg_color=0):
    rng = ctx.draw_rng(f"input.{sample_index}")
    if difficulty == "easy":
        h, w, nmark, dens = rng.randint(8, 11), rng.randint(8, 11), rng.randint(2, 3), 0.08
    elif difficulty == "hard":
        h, w, nmark, dens = rng.randint(20, 28), rng.randint(20, 28), rng.randint(5, 8), 0.14
    else:
        h, w, nmark, dens = rng.randint(13, 19), rng.randint(13, 19), rng.randint(3, 6), 0.11
    g = [[bg_color] * w for _ in range(h)]
    # sparse base-noise obstacles (the rays bounce off these)
    for r in range(h):
        for c in range(w):
            if rng.random() < dens:
                g[r][c] = noise_color
    # markers: choose cells with at least one free step in `direction` so rays
    # are non-trivial; markers never overlap the obstacle field
    dr, dc = _DELTAS[direction]
    cells = [(r, c) for r in range(h) for c in range(w)]
    rng.shuffle(cells)
    markers = []
    for (r, c) in cells:
        if len(markers) >= nmark:
            break
        nr, nc = r + dr, c + dc
        if not (0 <= nr < h and 0 <= nc < w):
            continue
        if g[r][c] != bg_color:
            continue
        # The teaching signal is the visible ray, not just recoloring the
        # marker.  The previous generator only required the next cell to be
        # in-bounds; if that cell was base noise, the ray stopped immediately
        # and the marker branch was hidden.  Require at least one bg cell in
        # the ray direction so every marker visibly paints a first step.
        if g[nr][nc] != bg_color:
            continue
        if all(abs(r - mr) >= 2 or abs(c - mc) >= 2 for (mr, mc) in markers):
            markers.append((r, c))
    for (r, c) in markers:
        g[r][c] = marker_color
    return g


def generate_task(seed, *, difficulty="medium", n_train=3, n_test=1):
    ctx = gen_ctx(seed=seed, sample_index=0, version=VERSION,
                  task_id=GENERATOR_ID, difficulty=difficulty)
    pal = ctx.draw_rng("palette")
    # Keep nonzero background as a capability without over-correcting this
    # concept family to 100% colored-background outputs. The eval target is a
    # mixed distribution (~2/3 nonzero modal background), so sample the modal
    # background as an explicit axis while keeping semantic colors distinct.
    use_nonzero_bg = pal.randrange(3) > 0
    if use_nonzero_bg:
        bg_color, noise_color, marker_color, new_color = pal.sample(range(1, 10), 4)
    else:
        bg_color = 0
        noise_color, marker_color, new_color = pal.sample(range(1, 10), 3)
    direction = pal.choice(["up", "down", "left", "right"])

    train, test = [], []
    for i in range(n_train):
        g = _build_input(ctx, i, noise_color=noise_color, marker_color=marker_color,
                         direction=direction, difficulty=difficulty, bg_color=bg_color)
        out = _apply(g, marker_color=marker_color, new_color=new_color,
                     direction=direction, bg_color=bg_color)
        train.append({"input": g, "output": out})
    for j in range(n_test):
        g = _build_input(ctx, 100 + j, noise_color=noise_color, marker_color=marker_color,
                         direction=direction, difficulty=difficulty, bg_color=bg_color)
        out = _apply(g, marker_color=marker_color, new_color=new_color,
                     direction=direction, bg_color=bg_color)
        test.append({"input": g, "output": out})

    body = (f"(smear-color (recolor g {marker_color} {new_color})"
            f" {new_color} '{direction} {bg_color})")
    program = f"(rule! (lambda (g) {body}))"
    return {"train": train, "test": test, "program": program,
            "chain": ["recolor_markers", "smear_new_color", "modal_background_mix"],
            "new_color": new_color, "marker_color": marker_color, "bg_color": bg_color,
            "nonzero_bg": bool(bg_color)}


if __name__ == "__main__":
    parity_check(generate_task, n=25, version_label=GENERATOR_ID)

def self_check_task(task):
    msgs = []
    bg = task.get("bg_color", 0)
    marker = task.get("marker_color")
    new = task.get("new_color")
    program = task.get("program", "")
    direction = None
    for name in _DELTAS:
        if "'" + name in program:
            direction = name
            break
    if marker is None or new is None or direction is None:
        return ["missing marker/new/direction metadata"]
    dr, dc = _DELTAS[direction]
    for split in ("train", "test"):
        for idx, pair in enumerate(task.get(split, [])):
            g = pair["input"]
            out = pair["output"]
            h, w = _dims(g)
            markers = [(r, c) for r in range(h) for c in range(w) if g[r][c] == marker]
            if not markers:
                msgs.append(f"{split}[{idx}] has no marker cells")
            if any(v == new for row in g for v in row):
                msgs.append(f"{split}[{idx}] new color appears in input")
            for r, c in markers:
                nr, nc = r + dr, c + dc
                if not (0 <= nr < h and 0 <= nc < w):
                    msgs.append(f"{split}[{idx}] marker has no in-bounds first ray step")
                elif g[nr][nc] != bg:
                    msgs.append(f"{split}[{idx}] marker first ray step is blocked in input")
                elif out[nr][nc] != new:
                    msgs.append(f"{split}[{idx}] marker first ray step was not painted")
    return msgs
