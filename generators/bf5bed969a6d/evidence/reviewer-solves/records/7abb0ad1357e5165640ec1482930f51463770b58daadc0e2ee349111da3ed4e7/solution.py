"""Visible-only ARC solution for the blind episode.

The red (2) component is a binary stamp.  Each other non-background color
outlines one rectangular frame, possibly with border cells hidden by another
frame.  Remove the red exemplar and copy its shape, in the frame's color,
centered in every frame interior.  When frames overlap, also copy the stamp at
the overlapped corner of the smaller/earlier frame; this is required by the
first visible example, where the two crossed frames create a third copy.
"""


def _bbox(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), max(rows), min(cols), max(cols)


def _paint(out, mask, top, left, color, *, overwrite):
    h, w = len(out), len(out[0])
    for dr, row in enumerate(mask):
        for dc, on in enumerate(row):
            if not on:
                continue
            r, c = top + dr, left + dc
            if 0 <= r < h and 0 <= c < w:
                if overwrite or out[r][c] == 0:
                    out[r][c] = color


def solve(grid):
    out = [row[:] for row in grid]
    h, w = len(out), len(out[0])

    marker_cells = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] == 2
    ]
    if not marker_cells:
        return out

    mr0, mr1, mc0, mc1 = _bbox(marker_cells)
    marker_set = set(marker_cells)
    mask = [
        [(mr0 + dr, mc0 + dc) in marker_set for dc in range(mc1 - mc0 + 1)]
        for dr in range(mr1 - mr0 + 1)
    ]
    mh, mw = len(mask), len(mask[0])

    # Erase the exemplar before placing colored copies.
    for r, c in marker_cells:
        out[r][c] = 0

    colors = sorted({v for row in grid for v in row if v not in (0, 2)})
    frames = []
    for color in colors:
        cells = [
            (r, c)
            for r in range(h)
            for c in range(w)
            if grid[r][c] == color
        ]
        if not cells:
            continue
        r0, r1, c0, c1 = _bbox(cells)
        frames.append({
            "color": color,
            "r0": r0,
            "r1": r1,
            "c0": c0,
            "c1": c1,
            "area": (r1 - r0 + 1) * (c1 - c0 + 1),
        })

    # Ordinary copies: center the exemplar in each frame's interior and do not
    # overwrite a crossing frame border.
    for f in frames:
        ir0, ir1 = f["r0"] + 1, f["r1"] - 1
        ic0, ic1 = f["c0"] + 1, f["c1"] - 1
        ih, iw = ir1 - ir0 + 1, ic1 - ic0 + 1
        top = ir0 + (ih - mh) // 2
        left = ic0 + (iw - mw) // 2
        _paint(out, mask, top, left, f["color"], overwrite=False)

    # Crossed-frame copy.  In the only visible crossed case, the smaller
    # frame's corner inside the other frame is the center of an additional
    # stamp and that copy sits on top of the crossed borders.
    ordered = sorted(frames, key=lambda f: (f["area"], f["r0"], f["c0"], f["color"]))
    for i, a in enumerate(ordered):
        for b in ordered[i + 1:]:
            rr0, rr1 = max(a["r0"], b["r0"]), min(a["r1"], b["r1"])
            cc0, cc1 = max(a["c0"], b["c0"]), min(a["c1"], b["c1"])
            # A one-cell-high/one-cell-wide intersection is only a shared
            # border.  Visible example 2 shows that border contact does not
            # create the additional crossed-frame copy.
            if rr1 - rr0 + 1 < 2 or cc1 - cc0 + 1 < 2:
                continue

            corners = [
                (a["r0"], a["c0"]),
                (a["r0"], a["c1"]),
                (a["r1"], a["c0"]),
                (a["r1"], a["c1"]),
            ]
            inside = [
                (r, c)
                for r, c in corners
                if b["r0"] <= r <= b["r1"] and b["c0"] <= c <= b["c1"]
            ]
            if not inside:
                continue

            # Prefer the corner nearest the overlap's upper-left-biased center.
            target_r = (rr0 + rr1) // 2
            target_c = (cc0 + cc1) // 2
            anchor_r, anchor_c = min(
                inside,
                key=lambda p: (abs(p[0] - target_r) + abs(p[1] - target_c), p[0], p[1]),
            )
            top = anchor_r - (mh - 1) // 2
            left = anchor_c - (mw - 1) // 2
            _paint(out, mask, top, left, a["color"], overwrite=True)

    return out
