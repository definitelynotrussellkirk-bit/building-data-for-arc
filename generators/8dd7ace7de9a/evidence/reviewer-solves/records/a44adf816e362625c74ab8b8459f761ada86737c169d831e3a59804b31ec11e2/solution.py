from collections import Counter


def _best_lattice(grid, color):
    """Return (score, row_period, row_phase, col_period, col_phase)."""
    h, w = len(grid), len(grid[0])
    positions = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color}
    total = len(positions)
    best = None

    # The examples show a repeated Cartesian lattice, so require at least two
    # selected rows and columns and at least four lattice cells.
    for rp in range(2, h + 1):
        for ra in range(rp):
            rows = [r for r in range(h) if r % rp == ra]
            if len(rows) < 2:
                continue
            for cp in range(2, w + 1):
                for ca in range(cp):
                    cols = [c for c in range(w) if c % cp == ca]
                    if len(cols) < 2:
                        continue
                    lattice_n = len(rows) * len(cols)
                    tp = sum((r, c) in positions for r in rows for c in cols)
                    if tp < 3:
                        continue
                    precision = tp / total
                    occupancy = tp / lattice_n
                    # F1 balances "all marker pixels lie on the lattice" with
                    # "the lattice is visibly populated despite corruption".
                    score = 2 * precision * occupancy / (precision + occupancy)
                    # Prefer more direct evidence, then the denser/smaller-period
                    # explanation when numerical scores tie.
                    key = (score, tp, -lattice_n, -rp - cp)
                    if best is None or key > best[0]:
                        best = (key, rp, ra, cp, ca)
    return None if best is None else (best[0][0], *best[1:])


def solve(grid):
    counts = Counter(v for row in grid for v in row)
    background = counts.most_common(1)[0][0]

    candidates = []
    for color in counts:
        if color == background:
            continue
        fit = _best_lattice(grid, color)
        if fit is not None:
            score, rp, ra, cp, ca = fit
            candidates.append((score, counts[color], color, rp, ra, cp, ca))

    if not candidates:
        return [row[:] for row in grid]

    _, _, marker, rp, ra, cp, ca = max(candidates)
    return [
        [marker if r % rp == ra and c % cp == ca else background for c in range(len(grid[0]))]
        for r in range(len(grid))
    ]
