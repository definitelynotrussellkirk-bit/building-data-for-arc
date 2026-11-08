"""gen1: diamond rings on a checkerboard; flanking segments fire rays.

Scene: a two-color CHECKERBOARD field holds 1-3 diamond rings (|r-cr| +
|c-cc| = k). Each ring gets 1-4 of its sides flanked by a parallel diagonal
SEGMENT one step outward, each segment in its own color. Transform: every
free chain end (exactly one same-color diagonal neighbor) fires rays
perpendicular to its chain in each diagonal direction that opens onto
background, painting its color over the checkerboard to the edge (shapes
block). Rings never fire (no free ends); segment middles never fire.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

VERSION = "1.0.0"
TASK_ID = "generic_checker_rays_gen1"

DIAG = ((-1, -1), (-1, 1), (1, -1), (1, 1))

PROGRAM = """(rule!
 ;; Checkerboard field (the two most frequent colors are the background).
 ;; Foreground colors form diagonal chains: closed diamond RINGS (every cell
 ;; has two same-color diagonal neighbors) and open SEGMENTS. Every FREE END
 ;; (exactly one same-color diagonal neighbor) fires rays PERPENDICULAR to
 ;; its segment, in each diagonal direction whose adjacent cell is
 ;; background, painting its color over the checkerboard until a shape or
 ;; the edge stops it. Rings have no free ends, so they never fire.
 (lambda (g)
   (let ()
     (define h (rows g))
     (define w (cols g))
     (define bg-pair
       (let ((sorted (sort (grid-colors g)
                           (lambda (a b) (> (length (find-color g a))
                                            (length (find-color g b)))))))
         (list (first sorted) (second sorted))))
     (define (bg? v) (member? v bg-pair))
     (define (same-at? r c v)
       (and (in-bounds? r c h w) (= (at g r c) v)))
     (define (diag-neighbors r c v)
       (filter (lambda (d) (same-at? (+ r (first d)) (+ c (second d)) v))
               diagonal-deltas))
     (define (paint-ray out r c dr dc v)
       (let loop ((rr r) (cc c) (acc out))
         (if (and (in-bounds? rr cc h w) (bg? (at g rr cc)))
             (loop (+ rr dr) (+ cc dc) (set-cell acc rr cc v))
             acc)))
     (for*/fold ((out g)) ((r (in-range h)) (c (in-range w)))
       (let ((v (at g r c)))
         (if (bg? v)
             out
             (let ((nbrs (diag-neighbors r c v)))
               (if (!= (length nbrs) 1)
                   out
                   (let* ((d (first nbrs))
                          (pr (second d))
                          (pc (- (first d))))
                     (paint-ray
                      (paint-ray out (+ r pr) (+ c pc) pr pc v)
                      (- r pr) (- c pc) (- pr) (- pc) v))))))))))"""


def _apply(g, bg_pair):
    """Python mirror of PROGRAM (same scan order, paints over ORIGINAL bg)."""
    h, w = len(g), len(g[0])
    bg = set(bg_pair)
    out = [row[:] for row in g]
    for r in range(h):
        for c in range(w):
            v = g[r][c]
            if v in bg:
                continue
            nbrs = [(dr, dc) for dr, dc in DIAG
                    if 0 <= r + dr < h and 0 <= c + dc < w
                    and g[r + dr][c + dc] == v]
            if len(nbrs) != 1:
                continue
            (dr, dc) = nbrs[0]
            pr, pc = dc, -dr
            for sr, sc in ((pr, pc), (-pr, -pc)):
                rr, cc = r + sr, c + sc
                while 0 <= rr < h and 0 <= cc < w and g[rr][cc] in bg:
                    out[rr][cc] = v
                    rr += sr
                    cc += sc
    return out


def _ring_cells(cr, cc, k):
    return [(cr + dr, cc + dc)
            for dr in range(-k, k + 1)
            for dc in range(-k, k + 1)
            if abs(dr) + abs(dc) == k]


def _side_segment(cr, cc, k, side, lo, hi):
    """The ring side's cells shifted one step outward (the flanking segment).
    side 0 = upper-left, 1 = upper-right, 2 = lower-left, 3 = lower-right.
    Returns the sub-run [lo, hi] of the k+1 side positions."""
    out = []
    for i in range(lo, hi + 1):
        if side == 0:
            r, c = cr - k + i - 1, cc - i - 1        # top -> left, shifted NW
        elif side == 1:
            r, c = cr - k + i - 1, cc + i + 1        # top -> right, shifted NE
        elif side == 2:
            r, c = cr + k - i + 1, cc - i - 1        # bottom -> left, shifted SW
        else:
            r, c = cr + k - i + 1, cc + i + 1        # bottom -> right, shifted SE
        out.append((r, c))
    return out


def _dims_for(difficulty):
    if difficulty == "easy":
        return (14, 18), 1
    if difficulty == "hard":
        return (22, 30), 3
    return (16, 26), 2


def _build_input(ctx, idx, bg_pair, gh, gw, max_rings):
    rng = ctx.draw_rng(f"input_{idx}")
    ca, cb = bg_pair
    parity = rng.randint(0, 1)
    g = [[ca if (r + c) % 2 == parity else cb for c in range(gw)]
         for r in range(gh)]
    fg_pool = [v for v in range(10) if v not in (ca, cb)]
    rng.shuffle(fg_pool)
    ring_color = fg_pool[0]
    seg_colors = fg_pool[1:]
    used = set()
    placed = 0
    for _ring in range(max_rings):
        for _try in range(40):
            k = rng.randint(2, 3)
            cr = rng.randint(k + 2, gh - k - 3)
            cc = rng.randint(k + 2, gw - k - 3)
            cells = _ring_cells(cr, cc, k)
            # segments occupy the shifted ring border: keep a 2-pad clearance
            pad = {(r + dr, c + dc) for r, c in cells
                   for dr in (-2, -1, 0, 1, 2) for dc in (-2, -1, 0, 1, 2)}
            if pad & used:
                continue
            for r, c in cells:
                g[r][c] = ring_color
            used |= pad
            sides = rng.sample(range(4), rng.randint(1, 4))
            for si, side in enumerate(sides):
                # a length-2..k+1 sub-run of the side, hugging the ring
                seg_len = rng.randint(2, k + 1)
                lo = rng.randint(0, k + 1 - seg_len)
                seg = _side_segment(cr, cc, k, side, lo, lo + seg_len - 1)
                if any(not (0 <= r < gh and 0 <= c < gw) for r, c in seg):
                    continue
                color = seg_colors[(placed * 4 + si) % len(seg_colors)]
                for r, c in seg:
                    g[r][c] = color
            placed += 1
            break
    if placed == 0:
        raise ValueError("could not place any ring")
    return g


def generate_task(seed, *, difficulty="medium"):
    ctx = gen_ctx(seed=seed, sample_index=0, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty)
    (glo, ghi), max_rings = _dims_for(difficulty)
    rng = ctx.draw_rng("task")
    # the classic blue/black checkerboard half the time, any distinct pair else
    if rng.random() < 0.5:
        bg_pair = (1, 0)
    else:
        a = rng.randint(0, 9)
        b = rng.choice([v for v in range(10) if v != a])
        bg_pair = (a, b)
    n_train = ctx.draw_int("n_train", 2, 4)
    n_test = ctx.draw_int("n_test", 1, 2)
    pairs = []
    for idx in range(n_train + n_test):
        gh = ctx.draw_int(f"gh_{idx}", glo, ghi)
        gw = ctx.draw_int(f"gw_{idx}", glo, ghi)
        gin = _build_input(ctx, idx, bg_pair, gh, gw, max_rings)
        pairs.append({"input": gin, "output": _apply(gin, bg_pair)})
    return {
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "program": PROGRAM,
        "concept": "checker_rays",
        "difficulty": difficulty,
    }


if __name__ == "__main__":
    from puzzle_generators.generic.concepts.checker_rays import parity_check
    parity_check(generate_task, n=25, version_label=f"checker_rays gen1 v{VERSION}")
