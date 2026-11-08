"""Expanded deterministic per-cell features for the dense episode model.

The machine computes facts; the model attends to them. Every channel here
is a cheap deterministic function of the visible boards — no generator
metadata, no peeking at hidden query outputs.

The first 10 channels match GRID_FEATURE_NAMES from bottleneck_tensorize
(same semantics) so this set is a strict extension. The new channels add
component geometry, board color statistics, row/col structure, symmetry
self-tests, and — for demo boards — pair-diff channels that let a demo
cell literally see what the rule did at its position (`pair_changed`,
`partner_color`). Query inputs get the NA value for pair channels: the
model must infer those, which is the task.

These functions are DATASET-SIDE (collate / dataloader workers). Never
call them inside a model forward — host-side Python loops there would
destroy GPU/TPU throughput.
"""

from __future__ import annotations

from collections import deque
from typing import Optional

import torch

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None

EPISODE_FEATURE_NAMES = (
    # -- carried over from GRID_FEATURE_NAMES (same semantics) --
    "nonzero",                # 2
    "neighbor4_nonzero",      # 5
    "neighbor8_nonzero",      # 9
    "neighbor4_same_color",   # 5
    "neighbor8_same_color",   # 9
    "top_edge",               # 2
    "bottom_edge",            # 2
    "left_edge",              # 2
    "right_edge",             # 2
    "component_size_bucket",  # 8  (occupancy component, color-blind)
    # -- new: position / component geometry (same-color components) --
    "border_dist",            # 5  min distance to real border, clamped 4
    "comp_is_rect",           # 2  same-color component fills its bbox
    "comp_touches_border",    # 2
    "comp_bbox_other",        # 2  bbox contains non-component cells
    "comp_h_bucket",          # 5
    "comp_w_bucket",          # 5
    # -- new: board color statistics --
    "color_rank",             # 11 rank by count among nonzero colors; 10 = bg/na
    "is_mode_color",          # 2
    "is_minority_color",      # 2
    # -- new: row/col structure --
    "row_nonzero_bucket",     # 5
    "col_nonzero_bucket",     # 5
    "row_uniform",            # 2
    "col_uniform",            # 2
    # -- new: symmetry self-tests within the real grid --
    "mirror_lr_eq",           # 2  cell equals its left-right mirror
    "mirror_ud_eq",           # 2
    "rot180_eq",              # 2
    # -- new: pair diff (demo boards only; NA on query inputs) --
    "pair_changed",           # 3  0=na, 1=same as partner, 2=differs
    "partner_color",          # 12 0..9 partner color, 10=outside partner, 11=na
    # -- A1: coordinates (the gather-algebra fix — MLPs can't see RoPE) --
    "row_idx",                # 30
    "col_idx",                # 30
    "row_from_bottom",        # 30  H-1-r against the real extent
    "col_from_right",         # 30  W-1-c
    # -- A2: relational addresses (neurogolf substrates) --
    "mirror_lr_color",        # 11  the color AT my lr-mirror position
    "mirror_ud_color",        # 11
    "los_up_color",           # 12  nearest non-bg color looking up (10=none)
    "los_down_color",         # 12
    "los_left_color",         # 12
    "los_right_color",        # 12
    "row_period_mismatch",    # 3   0=na (no period), 1=fits, 2=anomaly
    "col_period_mismatch",    # 3
    "enclosed_lr",            # 2   bg cell with same-color witnesses both sides in row
    "enclosed_ud",            # 2
    "neigh4_same_pattern",    # 16  WHICH cardinal neighbors share my color (bitmask)
    "comp_size_rank",         # 8   my component's size rank (0=largest; 7=bg/na)
    "panel_id",               # 10  separator-partition panel (9=on separator)
    # -- geometric expansion (run lengths, diagonal, parity, recovery) --
    "run_len_row",            # 5   same-color run length through me (span bucket)
    "run_len_col",            # 5
    "on_main_diag",           # 2   r == c
    "on_anti_diag",           # 2   r + c == W-1
    "mirror_diag_eq",         # 3   0 na (non-square), 1 no, 2 yes
    "diag_source_color",      # 12  color at my transpose position (11 na)
    "row_parity",             # 2
    "col_parity",             # 2
    "checker_parity",         # 2   (r+c) % 2
    "row_period_source_color",# 12  majority color among my vertical period-translates (11 na)
    "col_period_source_color",# 12
    "orbit_majority_color",   # 12  majority of my lr/ud/180 images — the repair value
    "orbit_disagreement",     # 4   how many of my 3 symmetry images differ from me
    # -- region expansion (enclosure, voronoi, shapes, key/hole, stamping) --
    "bg_enclosed",            # 3   0 na (nonzero), 1 bg reachable, 2 bg ENCLOSED
    "enclosure_color",        # 12  the wall color sealing my region (10 mixed, 11 na)
    "nearest_nz_color",       # 12  voronoi: nearest nonzero color (10 none)
    "nearest_nz_dist",        # 6   0 self, 1, 2, 3-4, 5+, na
    "shape_mult",             # 8   comps sharing my comp's exact shape (0 na, 7=7+)
    "shape_mult_d4",          # 8   same, counting rotated/flipped copies
    "comp_hole_count",        # 6   0 na, 1=0 holes, 2=1, 3=2, 4=3, 5=4+
    "comp_touch_count",       # 8   0 na, 1=0 other colors touched, ..., 7=6+
    "comp_touch_major_color", # 12  most-contacted other color (10 none, 11 na)
    "keyhole_match",          # 4   0 na, 1 no match, 2 exact, 3 d4 — keys AND holes
    "keyhole_partner_color",  # 12  the matching counterpart's color (11 na)
    "diff_motif_repeat",      # 3   my changed cell belongs to a repeated diff motif
)
EPISODE_FEATURE_VOCAB_SIZES = (
    2, 5, 9, 5, 9, 2, 2, 2, 2, 8,
    5, 2, 2, 2, 5, 5,
    11, 2, 2,
    5, 5, 2, 2,
    2, 2, 2,
    3, 12,
    30, 30, 30, 30,
    11, 11,
    12, 12, 12, 12,
    3, 3,
    2, 2,
    16,
    8,
    10,
    5, 5, 2, 2, 3, 12, 2, 2, 2, 12, 12, 12, 4,
    3, 12, 12, 6, 8, 8, 6, 8, 12, 4, 12, 3,
)
assert len(EPISODE_FEATURE_NAMES) == len(EPISODE_FEATURE_VOCAB_SIZES)
_IDX = {name: idx for idx, name in enumerate(EPISODE_FEATURE_NAMES)}

PAIR_CHANGED_NA = 0
PAIR_CHANGED_SAME = 1
PAIR_CHANGED_DIFF = 2
PARTNER_OUTSIDE = 10
PARTNER_NA = 11
LOS_NONE = 10
PERIOD_MISMATCH_TOLERANCE = 0.15

# Graded agreement buckets — resolution concentrated at the top, where a
# pattern "pops" (94%-symmetric IS the pattern; boolean flags read it as no).
SEMBLANCE_BUCKET_LABELS = ("na", "<50", "50-69", "70-79", "80-89", "90-94", "95-97", "98-99", "100")


def _majority_color(vals: list) -> int:
    """Most frequent value; ties broken toward the SMALLEST value (matches
    argmax-over-ascending-counts in the vectorized path)."""
    counts: dict[int, int] = {}
    for value in vals:
        counts[value] = counts.get(value, 0) + 1
    best = max(counts.values())
    return min(value for value, count in counts.items() if count == best)


def _semblance_bucket(matches: int, total: int) -> int:
    if total <= 0:
        return 0
    pct = 100.0 * matches / total
    if pct >= 100.0:
        return 8
    if pct >= 98.0:
        return 7
    if pct >= 95.0:
        return 6
    if pct >= 90.0:
        return 5
    if pct >= 80.0:
        return 4
    if pct >= 70.0:
        return 3
    if pct >= 50.0:
        return 2
    return 1

# Typed summary tokens: one token per board / per demo pair, appended to
# the attention sequence. Each channel is a small-vocab embedding.
BOARD_TOKEN_FEATURE_NAMES = (
    "height",               # 31: 0=na, 1..30
    "width",                # 31
    "num_colors",           # 11: distinct nonzero colors present
    "nonzero_bucket",       # 8
    "object_count_bucket",  # 8: 4-conn occupancy components
    "sym_lr",               # 2: grid equals its lr mirror
    "sym_ud",               # 2
    "sym_180",              # 2
    "sym_rot90",            # 3: 0=no, 1=yes, 2=not-square
    "has_full_row",         # 2: some row is one uniform nonzero color
    "has_full_col",         # 2
    "row_period",           # 31: smallest near-period (15% tolerance), 0=none
    "col_period",           # 31
    "panel_rows",           # 5: number of separator row-bands, clamp 4 (0=na)
    "panel_cols",           # 5
    # graded self-structure (semblance buckets — near-misses pop)
    "sym_lr_pct",           # 9
    "sym_ud_pct",           # 9
    "sym_180_pct",          # 9
    "sym_rot90_pct",        # 9 (na unless square)
    "sym_transpose_pct",    # 9 (na unless square)
    "period_row_pct",       # 9: best vertical period agreement strength
    "period_col_pct",       # 9
    # comparable f(board) values (so pair heads can read f(in) vs f(out))
    "mode_color",           # 11: most common nonzero color (10=na)
    "minority_color",       # 11
)
BOARD_TOKEN_FEATURE_VOCAB_SIZES = (
    31, 31, 11, 8, 8, 2, 2, 2, 3, 2, 2, 31, 31, 5, 5,
    9, 9, 9, 9, 9, 9, 9, 11, 11,
)
assert len(BOARD_TOKEN_FEATURE_NAMES) == len(BOARD_TOKEN_FEATURE_VOCAB_SIZES)

PAIR_TOKEN_FEATURE_NAMES = (
    "same_shape",               # 2
    "height_relation",          # 3: 0 same, 1 output shorter, 2 output taller
    "width_relation",           # 3
    "diff_count_bucket",        # 8: changed cells over the canvas union
    "transition_kinds_bucket",  # 8: distinct (old, new) changed-color pairs
    "consistent_mapping",       # 2: each input color maps to <=1 output color
    "object_count_delta",       # 7: signed bucket of component-count change
    "d4_transform",             # 10: 0 na, 1 id, 2 rot90, 3 rot180, 4 rot270,
                                #     5 flip-lr, 6 flip-ud, 7 transpose,
                                #     8 anti-transpose, 9 none-of-these
    "scale_relation",           # 8: 0 na, 1 same, 2 out=2x, 3 out=3x,
                                #    4 out=kx, 5 out=/2, 6 out=/k, 7 other
    # the recolor map, as a table (same-shape pairs; 11=na, 10=varies)
    "maps_color_0",             # 12: what input color 0 became
    "maps_color_1", "maps_color_2", "maps_color_3", "maps_color_4",
    "maps_color_5", "maps_color_6", "maps_color_7", "maps_color_8",
    "maps_color_9",             # 12 each
    # graded semblance: % of output explained by each relation (buckets)
    "sembl_identity",           # 9
    "sembl_rot90", "sembl_rot180", "sembl_rot270",
    "sembl_flip_lr", "sembl_flip_ud", "sembl_transpose", "sembl_anti",
    "sembl_translation",        # 9: best nonzero shift, |dr|,|dc| <= 10
    "sembl_recolor",            # 9: best-fit positionwise color-function fit
    "translation_dir",          # 10: 0 na, 1-8 compass of best >=90% shift, 9 none
    "translation_mag",          # 5: span bucket of best shift magnitude
    "mode_map",                 # 12: what the input's mode color became
    # comparable per-color count deltas (signed buckets)
    "delta_color_0",            # 7 each
    "delta_color_1", "delta_color_2", "delta_color_3", "delta_color_4",
    "delta_color_5", "delta_color_6", "delta_color_7", "delta_color_8",
    "delta_color_9",
    # stamping: structure of the edit itself (diff clusters)
    "diff_cluster_count",       # 8: 0 na, 1=0 clusters, 2=1, ..., 7=6+
    "diff_clusters_same_shape", # 3: 0 na/<2 clusters, 1 no, 2 yes (one stamp)
    "diff_cluster_size",        # 8: size bucket of the largest cluster
    # ORDER deltas: did the rule create or destroy structure?
    "dsym_lr",                  # 6: 0 na, 1 broken, 2 decreased, 3 same,
    "dsym_ud",                  #    4 increased, 5 PERFECTED
    "dsym_180",                 # 6
    "dperiod",                  # 6: best periodicity strength delta
    "dcolors",                  # 7: signed distinct-color-count delta
    "dnonzero",                 # 7: signed nonzero-count delta (fill/erase)
)
PAIR_TOKEN_FEATURE_VOCAB_SIZES = (
    2, 3, 3, 8, 8, 2, 7, 10, 8,
    12, 12, 12, 12, 12, 12, 12, 12, 12, 12,
    9, 9, 9, 9, 9, 9, 9, 9,
    9, 9, 10, 5, 12,
    7, 7, 7, 7, 7, 7, 7, 7, 7, 7,
    8, 3, 8,
    6, 6, 6, 6, 7, 7,
)
ORDER_DELTA_LABELS = ("na", "broken", "decreased", "same", "increased", "perfected")


def _order_delta(in_matches: int, in_total: int, out_matches: int, out_total: int) -> int:
    if in_total <= 0 or out_total <= 0:
        return 0
    in_frac = in_matches / in_total
    out_frac = out_matches / out_total
    if out_frac >= 1.0 > in_frac:
        return 5
    if in_frac >= 1.0 > out_frac:
        return 1
    if out_frac > in_frac + 1e-9:
        return 4
    if out_frac < in_frac - 1e-9:
        return 2
    return 3
assert len(PAIR_TOKEN_FEATURE_NAMES) == len(PAIR_TOKEN_FEATURE_VOCAB_SIZES)

_DELTAS4 = ((-1, 0), (0, -1), (0, 1), (1, 0))
_DELTAS8 = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))


def _size_bucket(size: int) -> int:
    # mirrors bottleneck_tensorize._component_size_bucket
    if size <= 0:
        return 0
    if size == 1:
        return 1
    if size == 2:
        return 2
    if size <= 4:
        return 3
    if size <= 8:
        return 4
    if size <= 16:
        return 5
    if size <= 32:
        return 6
    return 7


def _span_bucket(span: int) -> int:
    # 0 unused/na, then 1, 2, 3-4, 5+
    if span <= 0:
        return 0
    if span == 1:
        return 1
    if span == 2:
        return 2
    if span <= 4:
        return 3
    return 4


def _count_bucket5(count: int) -> int:
    # 0, 1, 2, 3-5, 6+
    if count <= 0:
        return 0
    if count == 1:
        return 1
    if count == 2:
        return 2
    if count <= 5:
        return 3
    return 4


def _components(values: list[list[int]], height: int, width: int, *, same_color: bool) -> list[list[int]]:
    """4-connected component ids; same_color=False groups all nonzero cells."""
    comp = [[-1] * width for _ in range(height)]
    next_id = 0
    for r0 in range(height):
        for c0 in range(width):
            if comp[r0][c0] != -1:
                continue
            if not same_color and values[r0][c0] == 0:
                continue
            comp[r0][c0] = next_id
            queue = deque([(r0, c0)])
            while queue:
                r, c = queue.popleft()
                for dr, dc in _DELTAS4:
                    rr, cc = r + dr, c + dc
                    if rr < 0 or rr >= height or cc < 0 or cc >= width:
                        continue
                    if comp[rr][cc] != -1:
                        continue
                    if same_color:
                        if values[rr][cc] != values[r0][c0]:
                            continue
                    elif values[rr][cc] == 0:
                        continue
                    comp[rr][cc] = next_id
                    queue.append((rr, cc))
            next_id += 1
    return comp


def _stage3_region_grids(
    values: list[list[int]],
    height: int,
    width: int,
    partner_values: Optional[list[list[int]]] = None,
    partner_real: Optional[list[list[bool]]] = None,
) -> dict[str, list[list[int]]]:
    """Region channels shared verbatim by the reference and fast paths
    (BFS floods, shape hashing, key/hole matching — region-bounded, so a
    single pure-Python implementation keeps the two paths provably
    identical). Returns name -> 2D value grid."""
    grids = {
        "bg_enclosed": [[0] * width for _ in range(height)],
        "enclosure_color": [[11] * width for _ in range(height)],
        "nearest_nz_color": [[10] * width for _ in range(height)],
        "nearest_nz_dist": [[5] * width for _ in range(height)],
        "shape_mult": [[0] * width for _ in range(height)],
        "shape_mult_d4": [[0] * width for _ in range(height)],
        "comp_hole_count": [[0] * width for _ in range(height)],
        "comp_touch_count": [[0] * width for _ in range(height)],
        "comp_touch_major_color": [[11] * width for _ in range(height)],
        "keyhole_match": [[0] * width for _ in range(height)],
        "keyhole_partner_color": [[11] * width for _ in range(height)],
        "diff_motif_repeat": [[0] * width for _ in range(height)],
    }

    def components(pred) -> list[list[tuple[int, int]]]:
        seen = [[False] * width for _ in range(height)]
        out = []
        for r0 in range(height):
            for c0 in range(width):
                if seen[r0][c0] or not pred(r0, c0):
                    continue
                stack = [(r0, c0)]
                seen[r0][c0] = True
                cells = []
                while stack:
                    r, c = stack.pop()
                    cells.append((r, c))
                    for dr, dc in _DELTAS4:
                        nr, nc = r + dr, c + dc
                        if (
                            0 <= nr < height and 0 <= nc < width
                            and not seen[nr][nc]
                            and pred(nr, nc)
                            and values[nr][nc] == values[r0][c0]
                        ):
                            seen[nr][nc] = True
                            stack.append((nr, nc))
                out.append(cells)
        return out

    def normalize(cells) -> tuple:
        min_r = min(r for r, _ in cells)
        min_c = min(c for _, c in cells)
        return tuple(sorted((r - min_r, c - min_c) for r, c in cells))

    def d4_canonical(shape: tuple) -> tuple:
        variants = [shape]
        current = list(shape)
        for _ in range(3):
            current = [(c, -r) for r, c in current]  # rotate
            min_r = min(r for r, _ in current)
            min_c = min(c for _, c in current)
            variants.append(tuple(sorted((r - min_r, c - min_c) for r, c in current)))
        flipped = [(r, -c) for r, c in shape]
        min_c = min(c for _, c in flipped)
        current = [(r, c - min_c) for r, c in flipped]
        variants.append(tuple(sorted(current)))
        for _ in range(3):
            current = [(c, -r) for r, c in current]
            min_r = min(r for r, _ in current)
            min_c2 = min(c for _, c in current)
            variants.append(tuple(sorted((r - min_r, c - min_c2) for r, c in current)))
        return min(variants)

    canon_cache: dict[tuple, tuple] = {}
    raw_d4_canonical = d4_canonical

    def d4_canonical(shape: tuple) -> tuple:  # noqa: F811 - memoized wrapper
        cached = canon_cache.get(shape)
        if cached is None:
            cached = raw_d4_canonical(shape)
            canon_cache[shape] = cached
        return cached

    all_comps = components(lambda r, c: True)  # same-color comps, bg included
    nonzero_comps = [cells for cells in all_comps if values[cells[0][0]][cells[0][1]] != 0]
    bg_regions = [cells for cells in all_comps if values[cells[0][0]][cells[0][1]] == 0]

    # enclosure: a bg region is enclosed iff it owns no border cell
    region_enclosed = []
    region_color = []
    for cells in bg_regions:
        enclosed = all(0 < r < height - 1 and 0 < c < width - 1 for r, c in cells)
        wall_colors = set()
        wall_comps = set()
        for r, c in cells:
            for dr, dc in _DELTAS4:
                nr, nc = r + dr, c + dc
                if 0 <= nr < height and 0 <= nc < width and values[nr][nc] != 0:
                    wall_colors.add(values[nr][nc])
        region_enclosed.append(enclosed)
        region_color.append(
            (min(wall_colors) if len(wall_colors) == 1 else 10) if wall_colors else 10
        )
        for r, c in cells:
            grids["bg_enclosed"][r][c] = 2 if enclosed else 1
            if enclosed:
                grids["enclosure_color"][r][c] = region_color[-1]

    # voronoi: chamfer (two-pass) Manhattan distance, all colors at once;
    # argmin over ascending color index = min color wins ties
    INF = height + width + 9
    varr = np.asarray(values, dtype=np.int64)
    dist = np.full((10, height, width), INF, dtype=np.int64)
    for color in range(1, 10):
        dist[color][varr == color] = 0
    cols = np.arange(width, dtype=np.int64)
    for r in range(height):
        if r > 0:
            np.minimum(dist[:, r], dist[:, r - 1] + 1, out=dist[:, r])
        left = np.minimum.accumulate(dist[:, r] - cols, axis=1) + cols
        np.minimum(dist[:, r], left, out=dist[:, r])
    for r in reversed(range(height)):
        if r + 1 < height:
            np.minimum(dist[:, r], dist[:, r + 1] + 1, out=dist[:, r])
        right = (
            np.minimum.accumulate((dist[:, r] + cols)[:, ::-1], axis=1)[:, ::-1] - cols
        )
        np.minimum(dist[:, r], right, out=dist[:, r])
    dist[0] = INF + 5  # color 0 is bg, never a voronoi seed
    nearest = dist.min(axis=0)
    nearest_color = dist.argmin(axis=0)
    for r in range(height):
        for c in range(width):
            if nearest[r, c] < INF:
                grids["nearest_nz_color"][r][c] = int(nearest_color[r, c])
                d = int(nearest[r, c])
                grids["nearest_nz_dist"][r][c] = 0 if d == 0 else (1 if d == 1 else (2 if d == 2 else (3 if d <= 4 else 4)))

    # shape multiplicity (exact + D4) over nonzero comps
    shapes = [normalize(cells) for cells in nonzero_comps]
    canon = [d4_canonical(shape) for shape in shapes]
    exact_counts: dict[tuple, int] = {}
    canon_counts: dict[tuple, int] = {}
    for shape in shapes:
        exact_counts[shape] = exact_counts.get(shape, 0) + 1
    for shape in canon:
        canon_counts[shape] = canon_counts.get(shape, 0) + 1
    for cells, shape, cshape in zip(nonzero_comps, shapes, canon):
        for r, c in cells:
            grids["shape_mult"][r][c] = min(exact_counts[shape], 7)
            grids["shape_mult_d4"][r][c] = min(canon_counts[cshape], 7)

    # holes per comp + touch relations
    comp_id_of: dict[tuple[int, int], int] = {}
    for idx, cells in enumerate(nonzero_comps):
        for cell in cells:
            comp_id_of[cell] = idx
    hole_counts = [0] * len(nonzero_comps)
    for cells, enclosed in zip(bg_regions, region_enclosed):
        if not enclosed:
            continue
        owners = set()
        for r, c in cells:
            for dr, dc in _DELTAS4:
                nr, nc = r + dr, c + dc
                if 0 <= nr < height and 0 <= nc < width and values[nr][nc] != 0:
                    owners.add(comp_id_of[(nr, nc)])
        if len(owners) == 1:
            hole_counts[owners.pop()] += 1
    touch: list[dict[int, int]] = [dict() for _ in nonzero_comps]
    for idx, cells in enumerate(nonzero_comps):
        color = values[cells[0][0]][cells[0][1]]
        for r, c in cells:
            for dr, dc in _DELTAS4:
                nr, nc = r + dr, c + dc
                if 0 <= nr < height and 0 <= nc < width:
                    other = values[nr][nc]
                    if other != 0 and other != color:
                        touch[idx][other] = touch[idx].get(other, 0) + 1
    for idx, cells in enumerate(nonzero_comps):
        n_touch = len(touch[idx])
        major = (
            min(color for color, n in touch[idx].items() if n == max(touch[idx].values()))
            if touch[idx]
            else 10
        )
        for r, c in cells:
            grids["comp_hole_count"][r][c] = 1 + min(hole_counts[idx], 4)
            grids["comp_touch_count"][r][c] = 1 + min(n_touch, 6)
            grids["comp_touch_major_color"][r][c] = major

    # key/hole complementarity: enclosed bg regions vs nonzero comp shapes
    hole_entries = [
        (normalize(cells), d4_canonical(normalize(cells)), cells, region_color[idx])
        for idx, cells in enumerate(bg_regions)
        if region_enclosed[idx]
    ]
    for cells, shape, cshape in zip(nonzero_comps, shapes, canon):
        match, partner = 1, 11
        for h_shape, h_canon, h_cells, h_color in hole_entries:
            if shape == h_shape:
                match, partner = 2, h_color
                break
        if match == 1:
            for h_shape, h_canon, h_cells, h_color in hole_entries:
                if cshape == h_canon:
                    match, partner = 3, h_color
                    break
        for r, c in cells:
            grids["keyhole_match"][r][c] = match
            grids["keyhole_partner_color"][r][c] = partner
    comp_color = lambda cells: values[cells[0][0]][cells[0][1]]
    for h_shape, h_canon, h_cells, _h_color in hole_entries:
        match, partner = 1, 11
        for cells, shape, cshape in zip(nonzero_comps, shapes, canon):
            if shape == h_shape:
                match, partner = 2, comp_color(cells)
                break
        if match == 1:
            for cells, shape, cshape in zip(nonzero_comps, shapes, canon):
                if cshape == h_canon:
                    match, partner = 3, comp_color(cells)
                    break
        for r, c in h_cells:
            grids["keyhole_match"][r][c] = match
            grids["keyhole_partner_color"][r][c] = partner

    # stamping: diff-motif repetition against the partner board
    if partner_values is not None and partner_real is not None:
        changed = [
            [
                (not partner_real[r][c]) or partner_values[r][c] != values[r][c]
                for c in range(width)
            ]
            for r in range(height)
        ]
        seen = [[False] * width for _ in range(height)]
        clusters = []
        for r0 in range(height):
            for c0 in range(width):
                if seen[r0][c0] or not changed[r0][c0]:
                    continue
                stack = [(r0, c0)]
                seen[r0][c0] = True
                cells = []
                while stack:
                    r, c = stack.pop()
                    cells.append((r, c))
                    for dr, dc in _DELTAS4:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < height and 0 <= nc < width and changed[nr][nc] and not seen[nr][nc]:
                            seen[nr][nc] = True
                            stack.append((nr, nc))
                clusters.append(cells)
        shape_counts: dict[tuple, int] = {}
        cluster_shapes = [normalize(cells) for cells in clusters]
        for shape in cluster_shapes:
            shape_counts[shape] = shape_counts.get(shape, 0) + 1
        for cells, shape in zip(clusters, cluster_shapes):
            repeat = 2 if shape_counts[shape] >= 2 else 1
            for r, c in cells:
                grids["diff_motif_repeat"][r][c] = repeat
    return grids


STAGE3_CHANNEL_NAMES = (
    "bg_enclosed", "enclosure_color", "nearest_nz_color", "nearest_nz_dist",
    "shape_mult", "shape_mult_d4", "comp_hole_count", "comp_touch_count",
    "comp_touch_major_color", "keyhole_match", "keyhole_partner_color",
    "diff_motif_repeat",
)


def episode_feature_channels_reference(
    padded: torch.Tensor,
    mask: torch.Tensor,
    *,
    partner: Optional[torch.Tensor] = None,
    partner_mask: Optional[torch.Tensor] = None,
    null_color_id: int = 10,
) -> torch.Tensor:
    """Pure-Python reference for the per-cell channels (the oracle the
    vectorized path is tested against — keep semantics in lockstep).

    `padded`/`mask` are (canvas, canvas). `partner` is the other board of
    the same demo pair (output for an input board, input for an output
    board), or None for query inputs — pair channels then read NA.
    Returns (canvas, canvas, len(EPISODE_FEATURE_NAMES)) long tensor;
    cells outside the real grid are all-zero.
    """
    if padded.shape != mask.shape:
        raise ValueError(f"padded/mask shape mismatch: {padded.shape} vs {mask.shape}")
    canvas_h, canvas_w = padded.shape
    num_features = len(EPISODE_FEATURE_NAMES)
    features = torch.zeros((canvas_h, canvas_w, num_features), dtype=torch.long)
    mask_bool = mask.to(torch.bool)
    if not bool(mask_bool.any()):
        return features

    # Boards are top-left anchored rectangles; recover the real extent.
    height = int(mask_bool.any(dim=1).nonzero().max()) + 1
    width = int(mask_bool.any(dim=0).nonzero().max()) + 1
    values = [[int(padded[r, c]) for c in range(width)] for r in range(height)]
    nonzero = [
        [values[r][c] != 0 and values[r][c] != null_color_id for c in range(width)]
        for r in range(height)
    ]

    occ_comp = _components(values, height, width, same_color=False)
    color_comp = _components(values, height, width, same_color=True)
    comp_cells: dict[int, list[tuple[int, int]]] = {}
    occ_sizes: dict[int, int] = {}
    for r in range(height):
        for c in range(width):
            color_comp_id = color_comp[r][c]
            comp_cells.setdefault(color_comp_id, []).append((r, c))
            occ_id = occ_comp[r][c]
            if occ_id != -1:
                occ_sizes[occ_id] = occ_sizes.get(occ_id, 0) + 1
    comp_stats: dict[int, tuple[int, int, int, bool, bool, bool]] = {}
    for comp_id, cells in comp_cells.items():
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        comp_h = max(rs) - min(rs) + 1
        comp_w = max(cs) - min(cs) + 1
        is_rect = len(cells) == comp_h * comp_w
        touches = min(rs) == 0 or min(cs) == 0 or max(rs) == height - 1 or max(cs) == width - 1
        bbox_other = not is_rect
        comp_stats[comp_id] = (len(cells), comp_h, comp_w, is_rect, touches, bbox_other)

    color_counts = [0] * 10
    for r in range(height):
        for c in range(width):
            if nonzero[r][c]:
                color_counts[values[r][c]] += 1
    present = [color for color in range(10) if color_counts[color] > 0]
    by_count = sorted(present, key=lambda color: (-color_counts[color], color))
    rank_of = {color: rank for rank, color in enumerate(by_count)}
    mode_color = by_count[0] if by_count else -1
    minority_color = by_count[-1] if by_count else -1

    row_nonzero = [sum(1 for c in range(width) if nonzero[r][c]) for r in range(height)]
    col_nonzero = [sum(1 for r in range(height) if nonzero[r][c]) for c in range(width)]
    row_uniform = [all(values[r][c] == values[r][0] for c in range(width)) for r in range(height)]
    col_uniform = [all(values[r][c] == values[0][c] for r in range(height)) for c in range(width)]

    has_partner = partner is not None
    if has_partner:
        if partner_mask is None:
            partner_mask = partner != null_color_id
        partner_mask = partner_mask.to(torch.bool)

    # --- A2 precomputation: line-of-sight, periods, enclosure, ranks, panels ---
    los_up = [[LOS_NONE] * width for _ in range(height)]
    los_down = [[LOS_NONE] * width for _ in range(height)]
    los_left = [[LOS_NONE] * width for _ in range(height)]
    los_right = [[LOS_NONE] * width for _ in range(height)]
    for cc in range(width):
        last = LOS_NONE
        for rr in range(height):
            los_up[rr][cc] = last
            if nonzero[rr][cc]:
                last = values[rr][cc]
        last = LOS_NONE
        for rr in reversed(range(height)):
            los_down[rr][cc] = last
            if nonzero[rr][cc]:
                last = values[rr][cc]
    for rr in range(height):
        last = LOS_NONE
        for cc in range(width):
            los_left[rr][cc] = last
            if nonzero[rr][cc]:
                last = values[rr][cc]
        last = LOS_NONE
        for cc in reversed(range(width)):
            los_right[rr][cc] = last
            if nonzero[rr][cc]:
                last = values[rr][cc]

    row_period, col_period = _near_periods(values, height, width)

    # same-color run lengths along rows/cols
    run_row = [[0] * width for _ in range(height)]
    for rr in range(height):
        cc = 0
        while cc < width:
            end = cc
            while end + 1 < width and values[rr][end + 1] == values[rr][cc]:
                end += 1
            for k in range(cc, end + 1):
                run_row[rr][k] = end - cc + 1
            cc = end + 1
    run_col = [[0] * width for _ in range(height)]
    for cc in range(width):
        rr = 0
        while rr < height:
            end = rr
            while end + 1 < height and values[end + 1][cc] == values[rr][cc]:
                end += 1
            for k in range(rr, end + 1):
                run_col[k][cc] = end - rr + 1
            rr = end + 1

    stage3 = _stage3_region_grids(
        values,
        height,
        width,
        partner[:height, :width].tolist() if has_partner else None,
        partner_mask[:height, :width].tolist() if has_partner else None,
    )

    # per-row / per-col first/last occurrence of each nonzero color (enclosure)
    row_first = [[width] * 10 for _ in range(height)]
    row_last = [[-1] * 10 for _ in range(height)]
    col_first = [[height] * 10 for _ in range(width)]
    col_last = [[-1] * 10 for _ in range(width)]
    for rr in range(height):
        for cc in range(width):
            if not nonzero[rr][cc]:
                continue
            color = values[rr][cc]
            row_first[rr][color] = min(row_first[rr][color], cc)
            row_last[rr][color] = max(row_last[rr][color], cc)
            col_first[cc][color] = min(col_first[cc][color], rr)
            col_last[cc][color] = max(col_last[cc][color], rr)

    # same-color component size ranks (nonzero components only)
    nonzero_comp_sizes = sorted(
        {
            comp_id: stats[0]
            for comp_id, stats in comp_stats.items()
            if values[comp_cells[comp_id][0][0]][comp_cells[comp_id][0][1]] != 0
        }.items(),
        key=lambda item: (-item[1], item[0]),
    )
    comp_rank_of = {comp_id: min(rank, 6) for rank, (comp_id, _) in enumerate(nonzero_comp_sizes)}

    # separator-partition panels
    row_band, col_band, _n_row_bands, n_col_bands, has_panels = _panel_bands(values, height, width)

    for r in range(height):
        for c in range(width):
            center = values[r][c]
            center_nonzero = nonzero[r][c]
            n4 = n8 = same4 = same8 = 0
            for dr, dc in _DELTAS8:
                rr, cc = r + dr, c + dc
                if rr < 0 or rr >= height or cc < 0 or cc >= width:
                    continue
                if not nonzero[rr][cc]:
                    continue
                n8 += 1
                same = center_nonzero and values[rr][cc] == center
                if same:
                    same8 += 1
                if (dr, dc) in _DELTAS4:
                    n4 += 1
                    if same:
                        same4 += 1
            occ_id = occ_comp[r][c]
            size, comp_h, comp_w, is_rect, touches, bbox_other = comp_stats[color_comp[r][c]]
            features[r, c, 0] = int(center_nonzero)
            features[r, c, 1] = n4
            features[r, c, 2] = n8
            features[r, c, 3] = same4
            features[r, c, 4] = same8
            features[r, c, 5] = int(r == 0)
            features[r, c, 6] = int(r == height - 1)
            features[r, c, 7] = int(c == 0)
            features[r, c, 8] = int(c == width - 1)
            features[r, c, 9] = _size_bucket(occ_sizes.get(occ_id, 0)) if occ_id != -1 else 0
            features[r, c, 10] = min(r, c, height - 1 - r, width - 1 - c, 4)
            features[r, c, 11] = int(is_rect)
            features[r, c, 12] = int(touches)
            features[r, c, 13] = int(bbox_other)
            features[r, c, 14] = _span_bucket(comp_h)
            features[r, c, 15] = _span_bucket(comp_w)
            features[r, c, 16] = rank_of.get(center, 10) if center_nonzero else 10
            features[r, c, 17] = int(center_nonzero and center == mode_color)
            features[r, c, 18] = int(center_nonzero and center == minority_color)
            features[r, c, 19] = _count_bucket5(row_nonzero[r])
            features[r, c, 20] = _count_bucket5(col_nonzero[c])
            features[r, c, 21] = int(row_uniform[r])
            features[r, c, 22] = int(col_uniform[c])
            features[r, c, 23] = int(values[r][width - 1 - c] == center)
            features[r, c, 24] = int(values[height - 1 - r][c] == center)
            features[r, c, 25] = int(values[height - 1 - r][width - 1 - c] == center)
            if not has_partner:
                features[r, c, 26] = PAIR_CHANGED_NA
                features[r, c, 27] = PARTNER_NA
            elif bool(partner_mask[r, c]):
                partner_color = int(partner[r, c])
                features[r, c, 26] = (
                    PAIR_CHANGED_SAME if partner_color == center else PAIR_CHANGED_DIFF
                )
                features[r, c, 27] = min(max(partner_color, 0), 9)
            else:
                # Real cell here, no cell there: changed by shape.
                features[r, c, 26] = PAIR_CHANGED_DIFF
                features[r, c, 27] = PARTNER_OUTSIDE

            # A1: coordinates against the real extent
            features[r, c, _IDX["row_idx"]] = min(r, 29)
            features[r, c, _IDX["col_idx"]] = min(c, 29)
            features[r, c, _IDX["row_from_bottom"]] = min(height - 1 - r, 29)
            features[r, c, _IDX["col_from_right"]] = min(width - 1 - c, 29)
            # A2: relational addresses
            features[r, c, _IDX["mirror_lr_color"]] = values[r][width - 1 - c]
            features[r, c, _IDX["mirror_ud_color"]] = values[height - 1 - r][c]
            features[r, c, _IDX["los_up_color"]] = los_up[r][c]
            features[r, c, _IDX["los_down_color"]] = los_down[r][c]
            features[r, c, _IDX["los_left_color"]] = los_left[r][c]
            features[r, c, _IDX["los_right_color"]] = los_right[r][c]
            if row_period:
                up_diff = r >= row_period and values[r][c] != values[r - row_period][c]
                down_diff = r + row_period < height and values[r][c] != values[r + row_period][c]
                features[r, c, _IDX["row_period_mismatch"]] = 2 if (up_diff or down_diff) else 1
            if col_period:
                left_diff = c >= col_period and values[r][c] != values[r][c - col_period]
                right_diff = c + col_period < width and values[r][c] != values[r][c + col_period]
                features[r, c, _IDX["col_period_mismatch"]] = 2 if (left_diff or right_diff) else 1
            if center == 0:
                features[r, c, _IDX["enclosed_lr"]] = int(
                    any(row_first[r][color] < c < row_last[r][color] for color in range(1, 10))
                )
                features[r, c, _IDX["enclosed_ud"]] = int(
                    any(col_first[c][color] < r < col_last[c][color] for color in range(1, 10))
                )
            if center_nonzero:
                pattern = 0
                if r > 0 and values[r - 1][c] == center:
                    pattern |= 1
                if r + 1 < height and values[r + 1][c] == center:
                    pattern |= 2
                if c > 0 and values[r][c - 1] == center:
                    pattern |= 4
                if c + 1 < width and values[r][c + 1] == center:
                    pattern |= 8
                features[r, c, _IDX["neigh4_same_pattern"]] = pattern
                features[r, c, _IDX["comp_size_rank"]] = comp_rank_of.get(color_comp[r][c], 6)
            else:
                features[r, c, _IDX["comp_size_rank"]] = 7
            if has_panels:
                if row_band[r] < 0 or col_band[c] < 0:
                    features[r, c, _IDX["panel_id"]] = 9
                else:
                    features[r, c, _IDX["panel_id"]] = min(
                        row_band[r] * n_col_bands + col_band[c], 8
                    )
            # geometric expansion
            features[r, c, _IDX["run_len_row"]] = _span_bucket(run_row[r][c])
            features[r, c, _IDX["run_len_col"]] = _span_bucket(run_col[r][c])
            features[r, c, _IDX["on_main_diag"]] = int(r == c)
            features[r, c, _IDX["on_anti_diag"]] = int(r + c == width - 1)
            if height == width:
                features[r, c, _IDX["mirror_diag_eq"]] = 1 + int(values[c][r] == center)
                features[r, c, _IDX["diag_source_color"]] = values[c][r]
            else:
                features[r, c, _IDX["diag_source_color"]] = 11
            features[r, c, _IDX["row_parity"]] = r % 2
            features[r, c, _IDX["col_parity"]] = c % 2
            features[r, c, _IDX["checker_parity"]] = (r + c) % 2
            if row_period:
                translates = [
                    values[r + k * row_period][c]
                    for k in range(-(r // row_period), (height - 1 - r) // row_period + 1)
                    if k != 0
                ]
                features[r, c, _IDX["row_period_source_color"]] = (
                    _majority_color(translates) if translates else 11
                )
            else:
                features[r, c, _IDX["row_period_source_color"]] = 11
            if col_period:
                translates = [
                    values[r][c + k * col_period]
                    for k in range(-(c // col_period), (width - 1 - c) // col_period + 1)
                    if k != 0
                ]
                features[r, c, _IDX["col_period_source_color"]] = (
                    _majority_color(translates) if translates else 11
                )
            else:
                features[r, c, _IDX["col_period_source_color"]] = 11
            orbit = [
                values[r][width - 1 - c],
                values[height - 1 - r][c],
                values[height - 1 - r][width - 1 - c],
            ]
            features[r, c, _IDX["orbit_majority_color"]] = _majority_color(orbit)
            features[r, c, _IDX["orbit_disagreement"]] = sum(
                1 for img in orbit if img != center
            )
            for name in STAGE3_CHANNEL_NAMES:
                features[r, c, _IDX[name]] = stage3[name][r][c]
    return features


def episode_feature_channels(
    padded: torch.Tensor,
    mask: torch.Tensor,
    *,
    partner: Optional[torch.Tensor] = None,
    partner_mask: Optional[torch.Tensor] = None,
    null_color_id: int = 10,
) -> torch.Tensor:
    """Vectorized per-cell channels (numpy fast path; ~50x the reference).

    Semantics are pinned to episode_feature_channels_reference by the
    equality tests in tests/test_arc_episode_model.py — change both or
    neither.
    """
    if np is None:  # pragma: no cover - numpy ships with torch installs
        return episode_feature_channels_reference(
            padded, mask, partner=partner, partner_mask=partner_mask, null_color_id=null_color_id
        )
    if padded.shape != mask.shape:
        raise ValueError(f"padded/mask shape mismatch: {padded.shape} vs {mask.shape}")
    canvas_h, canvas_w = padded.shape
    num_features = len(EPISODE_FEATURE_NAMES)
    out = torch.zeros((canvas_h, canvas_w, num_features), dtype=torch.long)
    mask_bool = mask.to(torch.bool)
    if not bool(mask_bool.any()):
        return out
    height, width = _real_extent(mask_bool)
    v = padded[:height, :width].numpy().astype(np.int64)
    nz = (v != 0) & (v != null_color_id)
    F = np.zeros((height, width, num_features), dtype=np.int64)
    rgrid, cgrid = np.indices((height, width))

    # padded views for neighbor algebra (value pad -1 never matches 0..10)
    VP = np.full((height + 2, width + 2), -1, dtype=np.int64)
    VP[1:-1, 1:-1] = v
    NP = np.zeros((height + 2, width + 2), dtype=bool)
    NP[1:-1, 1:-1] = nz
    card = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    diag = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

    def shifted(arr, dr, dc):
        return arr[1 + dr : 1 + dr + height, 1 + dc : 1 + dc + width]

    nz_card = [shifted(NP, dr, dc) for dr, dc in card]
    nz_diag = [shifted(NP, dr, dc) for dr, dc in diag]
    eq_card = [(shifted(VP, dr, dc) == v) & s for (dr, dc), s in zip(card, nz_card)]
    eq_diag = [(shifted(VP, dr, dc) == v) & s for (dr, dc), s in zip(diag, nz_diag)]

    F[..., 0] = nz
    F[..., 1] = sum(s.astype(np.int64) for s in nz_card)
    F[..., 2] = F[..., 1] + sum(s.astype(np.int64) for s in nz_diag)
    F[..., 3] = nz * sum(e.astype(np.int64) for e in eq_card)
    F[..., 4] = F[..., 3] + nz * sum(e.astype(np.int64) for e in eq_diag)
    F[..., 5] = rgrid == 0
    F[..., 6] = rgrid == height - 1
    F[..., 7] = cgrid == 0
    F[..., 8] = cgrid == width - 1

    size_thresholds = np.array([1, 2, 3, 5, 9, 17, 33])
    span_thresholds = np.array([1, 2, 3, 5])
    count5_thresholds = np.array([1, 2, 3, 6])

    def propagate_labels(equal_fn) -> np.ndarray:
        # cell (r, c) may take the label of neighbor (r+dr, c+dc) when the
        # equality mask (indexed at the cell) says they're connected
        labels = (rgrid * width + cgrid).astype(np.int64)
        while True:
            best = labels.copy()
            for (dr, dc) in card:
                r0, r1 = max(0, -dr), height - max(0, dr)
                c0, c1 = max(0, -dc), width - max(0, dc)
                if r0 >= r1 or c0 >= c1:
                    continue
                src = labels[r0 + dr : r1 + dr, c0 + dc : c1 + dc]
                ok = equal_fn(dr, dc)[r0:r1, c0:c1]
                region = best[r0:r1, c0:c1]
                np.minimum(region, np.where(ok, src, region), out=region)
            if np.array_equal(best, labels):
                return labels
            labels = best

    # occupancy components (nonzero cells, color-blind)
    occ_eq = {
        (dr, dc): shifted(NP, dr, dc) & nz for dr, dc in card
    }
    occ_labels = propagate_labels(lambda dr, dc: occ_eq[(dr, dc)])
    occ_labels_masked = np.where(nz, occ_labels, -1)
    occ_sizes = np.bincount(occ_labels_masked[occ_labels_masked >= 0], minlength=height * width)
    occ_bucket = np.searchsorted(size_thresholds, occ_sizes, side="right")
    F[..., 9] = np.where(nz, occ_bucket[np.clip(occ_labels_masked, 0, None)], 0)

    F[..., 10] = np.minimum.reduce([rgrid, cgrid, height - 1 - rgrid, width - 1 - cgrid, np.full_like(rgrid, 4)])

    # same-color components (all cells)
    color_eq = {(dr, dc): (shifted(VP, dr, dc) == v) for dr, dc in card}
    comp_labels = propagate_labels(lambda dr, dc: color_eq[(dr, dc)])
    flat_labels = comp_labels.ravel()
    n_slots = height * width
    comp_sizes = np.bincount(flat_labels, minlength=n_slots)
    rmin = np.full(n_slots, height, dtype=np.int64)
    rmax = np.full(n_slots, -1, dtype=np.int64)
    cmin = np.full(n_slots, width, dtype=np.int64)
    cmax = np.full(n_slots, -1, dtype=np.int64)
    np.minimum.at(rmin, flat_labels, rgrid.ravel())
    np.maximum.at(rmax, flat_labels, rgrid.ravel())
    np.minimum.at(cmin, flat_labels, cgrid.ravel())
    np.maximum.at(cmax, flat_labels, cgrid.ravel())
    comp_h = rmax - rmin + 1
    comp_w = cmax - cmin + 1
    is_rect = comp_sizes == comp_h * comp_w
    touches = (rmin == 0) | (cmin == 0) | (rmax == height - 1) | (cmax == width - 1)
    F[..., 11] = is_rect[comp_labels]
    F[..., 12] = touches[comp_labels]
    F[..., 13] = ~is_rect[comp_labels]
    F[..., 14] = np.searchsorted(span_thresholds, comp_h, side="right")[comp_labels]
    F[..., 15] = np.searchsorted(span_thresholds, comp_w, side="right")[comp_labels]

    color_counts = np.bincount(v[nz], minlength=10) if nz.any() else np.zeros(10, dtype=np.int64)
    present = [color for color in range(10) if color > 0 and color_counts[color] > 0]
    by_count = sorted(present, key=lambda color: (-int(color_counts[color]), color))
    rank_arr = np.full(11, 10, dtype=np.int64)
    for rank, color in enumerate(by_count):
        rank_arr[color] = rank
    F[..., 16] = np.where(nz, rank_arr[np.clip(v, 0, 10)], 10)
    if by_count:
        F[..., 17] = nz & (v == by_count[0])
        F[..., 18] = nz & (v == by_count[-1])

    row_nz = nz.sum(axis=1)
    col_nz = nz.sum(axis=0)
    F[..., 19] = np.searchsorted(count5_thresholds, row_nz, side="right")[:, None]
    F[..., 20] = np.searchsorted(count5_thresholds, col_nz, side="right")[None, :]
    F[..., 21] = (v == v[:, :1]).all(axis=1)[:, None]
    F[..., 22] = (v == v[:1, :]).all(axis=0)[None, :]
    F[..., 23] = v == v[:, ::-1]
    F[..., 24] = v == v[::-1, :]
    F[..., 25] = v == v[::-1, ::-1]

    if partner is not None:
        if partner_mask is None:
            partner_mask = partner != null_color_id
        pv = partner[:height, :width].numpy().astype(np.int64)
        pm = partner_mask[:height, :width].numpy().astype(bool)
        F[..., 26] = np.where(pm, np.where(pv == v, PAIR_CHANGED_SAME, PAIR_CHANGED_DIFF), PAIR_CHANGED_DIFF)
        F[..., 27] = np.where(pm, np.clip(pv, 0, 9), PARTNER_OUTSIDE)
    else:
        F[..., 26] = PAIR_CHANGED_NA
        F[..., 27] = PARTNER_NA

    F[..., _IDX["row_idx"]] = np.minimum(rgrid, 29)
    F[..., _IDX["col_idx"]] = np.minimum(cgrid, 29)
    F[..., _IDX["row_from_bottom"]] = np.minimum(height - 1 - rgrid, 29)
    F[..., _IDX["col_from_right"]] = np.minimum(width - 1 - cgrid, 29)
    F[..., _IDX["mirror_lr_color"]] = v[:, ::-1]
    F[..., _IDX["mirror_ud_color"]] = v[::-1, :]

    # line of sight: nearest nonzero strictly before me along each direction
    def los_along_rows(values_arr, nz_arr):
        idx = np.where(nz_arr, rgrid, -1)
        run = np.maximum.accumulate(idx, axis=0)
        prev = np.vstack([np.full((1, width), -1, dtype=np.int64), run[:-1]])
        colors = np.where(
            prev >= 0,
            np.take_along_axis(values_arr, np.clip(prev, 0, None), axis=0),
            LOS_NONE,
        )
        return colors

    F[..., _IDX["los_up_color"]] = los_along_rows(v, nz)
    F[..., _IDX["los_down_color"]] = los_along_rows(v[::-1, :], nz[::-1, :])[::-1, :]

    def los_along_cols(values_arr, nz_arr):
        idx = np.where(nz_arr, cgrid, -1)
        run = np.maximum.accumulate(idx, axis=1)
        prev = np.hstack([np.full((height, 1), -1, dtype=np.int64), run[:, :-1]])
        colors = np.where(
            prev >= 0,
            np.take_along_axis(values_arr, np.clip(prev, 0, None), axis=1),
            LOS_NONE,
        )
        return colors

    F[..., _IDX["los_left_color"]] = los_along_cols(v, nz)
    F[..., _IDX["los_right_color"]] = los_along_cols(v[:, ::-1], nz[:, ::-1])[:, ::-1]

    row_period = 0
    for p in range(1, height):
        diff = (v[p:] != v[:-p]).sum()
        if diff / ((height - p) * width) <= PERIOD_MISMATCH_TOLERANCE:
            row_period = p
            break
    col_period = 0
    for p in range(1, width):
        diff = (v[:, p:] != v[:, :-p]).sum()
        if diff / ((width - p) * height) <= PERIOD_MISMATCH_TOLERANCE:
            col_period = p
            break
    if row_period:
        up_diff = np.zeros((height, width), dtype=bool)
        up_diff[row_period:] = v[row_period:] != v[:-row_period]
        down_diff = np.zeros((height, width), dtype=bool)
        down_diff[:-row_period] = v[:-row_period] != v[row_period:]
        F[..., _IDX["row_period_mismatch"]] = 1 + (up_diff | down_diff)
    if col_period:
        left_diff = np.zeros((height, width), dtype=bool)
        left_diff[:, col_period:] = v[:, col_period:] != v[:, :-col_period]
        right_diff = np.zeros((height, width), dtype=bool)
        right_diff[:, :-col_period] = v[:, :-col_period] != v[:, col_period:]
        F[..., _IDX["col_period_mismatch"]] = 1 + (left_diff | right_diff)

    enclosed_lr = np.zeros((height, width), dtype=bool)
    enclosed_ud = np.zeros((height, width), dtype=bool)
    for color in range(1, 10):
        m = v == color
        if not m.any():
            continue
        row_has = m.any(axis=1)
        first_c = np.where(row_has, m.argmax(axis=1), width)
        last_c = np.where(row_has, width - 1 - m[:, ::-1].argmax(axis=1), -1)
        enclosed_lr |= (cgrid > first_c[:, None]) & (cgrid < last_c[:, None])
        col_has = m.any(axis=0)
        first_r = np.where(col_has, m.argmax(axis=0), height)
        last_r = np.where(col_has, height - 1 - m[::-1, :].argmax(axis=0), -1)
        enclosed_ud |= (rgrid > first_r[None, :]) & (rgrid < last_r[None, :])
    F[..., _IDX["enclosed_lr"]] = (v == 0) & enclosed_lr
    F[..., _IDX["enclosed_ud"]] = (v == 0) & enclosed_ud

    pattern = (
        eq_card[0].astype(np.int64) * 1
        + eq_card[1].astype(np.int64) * 2
        + eq_card[2].astype(np.int64) * 4
        + eq_card[3].astype(np.int64) * 8
    )
    F[..., _IDX["neigh4_same_pattern"]] = np.where(nz, pattern, 0)

    # component size rank: nonzero same-color components ordered by
    # (-size, first-raster-cell). Propagated label IS the first raster
    # index, matching the reference's BFS comp-id order.
    unique_labels = np.unique(flat_labels)
    nonzero_labels = [
        int(lab) for lab in unique_labels if v.ravel()[lab] != 0
    ]
    ordered = sorted(nonzero_labels, key=lambda lab: (-int(comp_sizes[lab]), lab))
    rank_of = np.full(n_slots, 7, dtype=np.int64)
    for rank, lab in enumerate(ordered):
        rank_of[lab] = min(rank, 6)
    F[..., _IDX["comp_size_rank"]] = np.where(nz, rank_of[comp_labels], 7)

    values_list = v.tolist()
    row_band, col_band, _nrb, n_col_bands, has_panels = _panel_bands(values_list, height, width)
    if has_panels:
        rb = np.array(row_band, dtype=np.int64)[:, None]
        cb = np.array(col_band, dtype=np.int64)[None, :]
        on_sep = (rb < 0) | (cb < 0)
        panel = np.minimum(rb * max(n_col_bands, 1) + cb, 8)
        F[..., _IDX["panel_id"]] = np.where(on_sep, 9, np.clip(panel, 0, 8))

    # --- geometric expansion ---
    def _runs_along_rows(arr: np.ndarray) -> np.ndarray:
        h_, w_ = arr.shape
        change = np.zeros((h_, w_), dtype=np.int64)
        if w_ > 1:
            change[:, 1:] = (arr[:, 1:] != arr[:, :-1]).astype(np.int64)
        seg = np.cumsum(change, axis=1) + np.arange(h_)[:, None] * w_
        counts = np.bincount(seg.ravel(), minlength=h_ * w_)
        return counts[seg]

    F[..., _IDX["run_len_row"]] = np.searchsorted(span_thresholds, _runs_along_rows(v), side="right")
    F[..., _IDX["run_len_col"]] = np.searchsorted(span_thresholds, _runs_along_rows(v.T).T, side="right")
    F[..., _IDX["on_main_diag"]] = rgrid == cgrid
    F[..., _IDX["on_anti_diag"]] = (rgrid + cgrid) == (width - 1)
    if height == width:
        F[..., _IDX["mirror_diag_eq"]] = 1 + (v.T == v).astype(np.int64)
        F[..., _IDX["diag_source_color"]] = v.T
    else:
        F[..., _IDX["diag_source_color"]] = 11
    F[..., _IDX["row_parity"]] = rgrid % 2
    F[..., _IDX["col_parity"]] = cgrid % 2
    F[..., _IDX["checker_parity"]] = (rgrid + cgrid) % 2

    def _period_source(period: int, axis: int) -> np.ndarray:
        cnt = np.zeros((10, height, width), dtype=np.int64)
        extent = height if axis == 0 else width
        max_k = (extent - 1) // period
        for k in range(-max_k, max_k + 1):
            if k == 0:
                continue
            shift = k * period
            if axis == 0:
                r0, r1 = max(0, -shift), height - max(0, shift)
                if r0 >= r1:
                    continue
                src = v[r0 + shift : r1 + shift, :]
                np.add.at(cnt, (src, rgrid[r0:r1, :], cgrid[r0:r1, :]), 1)
            else:
                c0, c1 = max(0, -shift), width - max(0, shift)
                if c0 >= c1:
                    continue
                src = v[:, c0 + shift : c1 + shift]
                np.add.at(cnt, (src, rgrid[:, c0:c1], cgrid[:, c0:c1]), 1)
        total = cnt.sum(axis=0)
        return np.where(total > 0, cnt.argmax(axis=0), 11)

    F[..., _IDX["row_period_source_color"]] = _period_source(row_period, 0) if row_period else 11
    F[..., _IDX["col_period_source_color"]] = _period_source(col_period, 1) if col_period else 11

    images = np.stack([v[:, ::-1], v[::-1, :], v[::-1, ::-1]])
    orbit_counts = np.zeros((10, height, width), dtype=np.int64)
    for color in range(10):
        orbit_counts[color] = (images == color).sum(axis=0)
    F[..., _IDX["orbit_majority_color"]] = orbit_counts.argmax(axis=0)
    F[..., _IDX["orbit_disagreement"]] = (images != v[None, :, :]).sum(axis=0)

    # --- region expansion (shared analyzer — provably identical to reference) ---
    stage3 = _stage3_region_grids(
        values_list,
        height,
        width,
        partner[:height, :width].tolist() if partner is not None else None,
        partner_mask[:height, :width].to(torch.bool).tolist() if partner is not None else None,
    )
    for name in STAGE3_CHANNEL_NAMES:
        F[..., _IDX[name]] = np.asarray(stage3[name], dtype=np.int64)

    out[:height, :width, :] = torch.from_numpy(F)
    return out


def _real_extent(mask_bool: torch.Tensor) -> tuple[int, int]:
    if not bool(mask_bool.any()):
        return 0, 0
    height = int(mask_bool.any(dim=1).nonzero().max()) + 1
    width = int(mask_bool.any(dim=0).nonzero().max()) + 1
    return height, width


def _occupancy_component_count(values: list[list[int]], height: int, width: int) -> int:
    comp = _components(values, height, width, same_color=False)
    return len({comp[r][c] for r in range(height) for c in range(width) if comp[r][c] != -1})


def _signed_delta_bucket(delta: int) -> int:
    # <=-8, -7..-2, -1, 0, 1, 2..7, >=8
    if delta <= -8:
        return 0
    if delta <= -2:
        return 1
    if delta == -1:
        return 2
    if delta == 0:
        return 3
    if delta == 1:
        return 4
    if delta < 8:
        return 5
    return 6


def _near_periods(values: list[list[int]], height: int, width: int) -> tuple[int, int]:
    """Smallest row/col shift whose pairwise agreement tolerates a few
    anomalies (periodic pattern with occlusions — the common ARC case)."""
    row_period = 0
    for p in range(1, height):
        comparisons = (height - p) * width
        if comparisons <= 0:
            break
        mismatches = sum(
            1
            for rr in range(p, height)
            for cc in range(width)
            if values[rr][cc] != values[rr - p][cc]
        )
        if mismatches / comparisons <= PERIOD_MISMATCH_TOLERANCE:
            row_period = p
            break
    col_period = 0
    for p in range(1, width):
        comparisons = (width - p) * height
        if comparisons <= 0:
            break
        mismatches = sum(
            1
            for rr in range(height)
            for cc in range(p, width)
            if values[rr][cc] != values[rr][cc - p]
        )
        if mismatches / comparisons <= PERIOD_MISMATCH_TOLERANCE:
            col_period = p
            break
    return row_period, col_period


def _d4_code(in_grid: torch.Tensor, out_grid: torch.Tensor) -> int:
    """Which dihedral transform maps input exactly to output. 1=identity,
    2/3/4=rot90/180/270, 5=flip-lr, 6=flip-ud, 7=transpose,
    8=anti-transpose, 9=none."""
    candidates = (
        (1, in_grid),
        (2, torch.rot90(in_grid, 1, (0, 1))),
        (3, torch.rot90(in_grid, 2, (0, 1))),
        (4, torch.rot90(in_grid, 3, (0, 1))),
        (5, torch.flip(in_grid, dims=[1])),
        (6, torch.flip(in_grid, dims=[0])),
        (7, in_grid.t()),
        (8, torch.rot90(in_grid.t(), 2, (0, 1))),
    )
    for code, candidate in candidates:
        if candidate.shape == out_grid.shape and torch.equal(candidate, out_grid):
            return code
    return 9


def _scale_code(in_h: int, in_w: int, out_h: int, out_w: int) -> int:
    """Integer scale relation between input and output extents."""
    if in_h <= 0 or out_h <= 0:
        return 0
    if (out_h, out_w) == (in_h, in_w):
        return 1
    if out_h % in_h == 0 and out_w % in_w == 0 and out_h // in_h == out_w // in_w and out_h // in_h > 1:
        factor = out_h // in_h
        return 2 if factor == 2 else (3 if factor == 3 else 4)
    if in_h % out_h == 0 and in_w % out_w == 0 and in_h // out_h == in_w // out_w and in_h // out_h > 1:
        return 5 if in_h // out_h == 2 else 6
    return 7


def _panel_bands(values: list[list[int]], height: int, width: int):
    """Separator-partition structure: full uniform nonzero rows/cols split
    the board into panels. Returns (row_band, col_band, n_row_bands,
    n_col_bands, has_panels); band -1 = on a separator."""
    sep_rows = {
        rr
        for rr in range(height)
        if width > 1 and values[rr][0] != 0 and all(values[rr][cc] == values[rr][0] for cc in range(width))
    }
    sep_cols = {
        cc
        for cc in range(width)
        if height > 1 and values[0][cc] != 0 and all(values[rr][cc] == values[0][cc] for rr in range(height))
    }
    has_panels = bool(sep_rows or sep_cols)

    def bands(n: int, seps: set) -> list:
        out = [-1] * n
        current = -1
        in_band = False
        for i in range(n):
            if i in seps:
                in_band = False
                continue
            if not in_band:
                current += 1
                in_band = True
            out[i] = current
        return out

    row_band = bands(height, sep_rows)
    col_band = bands(width, sep_cols)
    n_row_bands = max((b for b in row_band if b >= 0), default=-1) + 1
    n_col_bands = max((b for b in col_band if b >= 0), default=-1) + 1
    return row_band, col_band, n_row_bands, n_col_bands, has_panels


def board_token_features(
    padded: torch.Tensor,
    mask: torch.Tensor,
    *,
    null_color_id: int = 10,
) -> torch.Tensor:
    """Board-level facts as one (len(BOARD_TOKEN_FEATURE_NAMES),) long vector."""
    out = torch.zeros(len(BOARD_TOKEN_FEATURE_NAMES), dtype=torch.long)
    mask_bool = mask.to(torch.bool)
    height, width = _real_extent(mask_bool)
    if height == 0:
        return out
    values = [[int(padded[r, c]) for c in range(width)] for r in range(height)]
    nonzero_count = 0
    colors = set()
    for r in range(height):
        for c in range(width):
            value = values[r][c]
            if value != 0 and value != null_color_id:
                nonzero_count += 1
                colors.add(value)
    grid = torch.tensor(values, dtype=torch.long)
    out[0] = min(height, 30)
    out[1] = min(width, 30)
    out[2] = min(len(colors), 10)
    out[3] = _size_bucket(nonzero_count)
    out[4] = _size_bucket(_occupancy_component_count(values, height, width))
    out[5] = int(torch.equal(grid, torch.flip(grid, dims=[1])))
    out[6] = int(torch.equal(grid, torch.flip(grid, dims=[0])))
    out[7] = int(torch.equal(grid, torch.flip(grid, dims=[0, 1])))
    if height == width:
        out[8] = int(torch.equal(grid, torch.rot90(grid, k=1, dims=(0, 1))))
    else:
        out[8] = 2
    out[9] = int(
        any(
            values[r][0] != 0 and all(values[r][c] == values[r][0] for c in range(width))
            for r in range(height)
        )
    )
    out[10] = int(
        any(
            values[0][c] != 0 and all(values[r][c] == values[0][c] for r in range(height))
            for c in range(width)
        )
    )
    row_period, col_period = _near_periods(values, height, width)
    out[11] = min(row_period, 30)
    out[12] = min(col_period, 30)
    _row_band, _col_band, n_row_bands, n_col_bands, has_panels = _panel_bands(values, height, width)
    if has_panels:
        out[13] = min(n_row_bands, 4)
        out[14] = min(n_col_bands, 4)

    # graded self-structure: near-miss symmetry/periodicity pops here
    total_cells = height * width

    def _agree(other: torch.Tensor) -> int:
        return _semblance_bucket(int((grid == other).sum()), total_cells)

    out[15] = _agree(torch.flip(grid, dims=[1]))
    out[16] = _agree(torch.flip(grid, dims=[0]))
    out[17] = _agree(torch.flip(grid, dims=[0, 1]))
    if height == width:
        out[18] = _agree(torch.rot90(grid, 1, (0, 1)))
        out[19] = _agree(grid.t())

    def _period_strength(axis: int) -> tuple[int, int]:
        best_m, best_t = 0, 0
        n = height if axis == 0 else width
        for p in range(1, n):
            if axis == 0:
                m = int((grid[p:] == grid[:-p]).sum())
                t = (n - p) * width
            else:
                m = int((grid[:, p:] == grid[:, :-p]).sum())
                t = (n - p) * height
            if t > 0 and (best_t == 0 or m * best_t > best_m * t):
                best_m, best_t = m, t
        return best_m, best_t

    if height > 1:
        out[20] = _semblance_bucket(*_period_strength(0))
    if width > 1:
        out[21] = _semblance_bucket(*_period_strength(1))

    color_counts: dict[int, int] = {}
    for r in range(height):
        for c in range(width):
            val = values[r][c]
            if val != 0 and val != null_color_id:
                color_counts[val] = color_counts.get(val, 0) + 1
    if color_counts:
        ordered = sorted(color_counts, key=lambda color: (-color_counts[color], color))
        out[22] = ordered[0]
        out[23] = ordered[-1]
    else:
        out[22] = 10
        out[23] = 10
    return out


def pair_token_features(
    input_ids: torch.Tensor,
    input_mask: torch.Tensor,
    output_ids: torch.Tensor,
    output_mask: torch.Tensor,
    *,
    null_color_id: int = 10,
) -> torch.Tensor:
    """Pair-level facts as one (len(PAIR_TOKEN_FEATURE_NAMES),) long vector."""
    out = torch.zeros(len(PAIR_TOKEN_FEATURE_NAMES), dtype=torch.long)
    in_mask = input_mask.to(torch.bool)
    out_mask = output_mask.to(torch.bool)
    in_h, in_w = _real_extent(in_mask)
    out_h, out_w = _real_extent(out_mask)
    if in_h == 0 or out_h == 0:
        return out
    out[0] = int(in_h == out_h and in_w == out_w)
    out[1] = 0 if out_h == in_h else (1 if out_h < in_h else 2)
    out[2] = 0 if out_w == in_w else (1 if out_w < in_w else 2)

    both = in_mask & out_mask
    either = in_mask | out_mask
    diff = (input_ids != output_ids) & both
    diff_count = int(diff.sum()) + int((either & ~both).sum())
    out[3] = _size_bucket(diff_count)
    transitions = set()
    mapping: dict[int, set[int]] = {}
    rows, cols = both.shape
    for r in range(rows):
        for c in range(cols):
            if not bool(both[r, c]):
                continue
            old = int(input_ids[r, c])
            new = int(output_ids[r, c])
            mapping.setdefault(old, set()).add(new)
            if old != new:
                transitions.add((old, new))
    out[4] = _size_bucket(len(transitions))
    out[5] = int(all(len(targets) <= 1 for targets in mapping.values()))

    def occupancy_count(ids: torch.Tensor, height: int, width: int) -> int:
        values = [[int(ids[r, c]) for c in range(width)] for r in range(height)]
        return _occupancy_component_count(values, height, width)

    delta = occupancy_count(output_ids, out_h, out_w) - occupancy_count(input_ids, in_h, in_w)
    out[6] = _signed_delta_bucket(delta)
    out[7] = _d4_code(input_ids[:in_h, :in_w], output_ids[:out_h, :out_w])
    out[8] = _scale_code(in_h, in_w, out_h, out_w)

    inp = input_ids[:in_h, :in_w].numpy()
    outp = output_ids[:out_h, :out_w].numpy()
    same_shape = (in_h, in_w) == (out_h, out_w)
    out_total = out_h * out_w

    # recolor map table: what each input color became, position-wise
    for color in range(10):
        if not same_shape:
            out[9 + color] = 11
            continue
        sel = outp[inp == color]
        if sel.size == 0:
            out[9 + color] = 11
        else:
            uniq = np.unique(sel)
            out[9 + color] = int(uniq[0]) if uniq.size == 1 else 10

    # graded D4 semblances: % of output explained by each transform
    transforms = (
        inp, np.rot90(inp, 1), np.rot90(inp, 2), np.rot90(inp, 3),
        inp[:, ::-1], inp[::-1, :], inp.T, np.rot90(inp.T, 2),
    )
    for idx, candidate in enumerate(transforms):
        if candidate.shape == outp.shape:
            out[19 + idx] = _semblance_bucket(int((candidate == outp).sum()), out_total)

    # best translation (small shifts), with direction/magnitude when strong
    if same_shape and (in_h > 1 or in_w > 1):
        best_score, best_shift = -1, None
        best_perfect = None  # (overlap, (dr, dc)): exact-in-overlap shifts
        for dr in range(-min(10, in_h - 1), min(10, in_h - 1) + 1):
            for dc in range(-min(10, in_w - 1), min(10, in_w - 1) + 1):
                if dr == 0 and dc == 0:
                    continue
                r0, r1 = max(0, dr), in_h + min(0, dr)
                c0, c1 = max(0, dc), in_w + min(0, dc)
                if r0 >= r1 or c0 >= c1:
                    continue
                overlap = (r1 - r0) * (c1 - c0)
                m = int((inp[r0 - dr : r1 - dr, c0 - dc : c1 - dc] == outp[r0:r1, c0:c1]).sum())
                if m > best_score:
                    best_score, best_shift = m, (dr, dc)
                if m == overlap and overlap * 2 >= out_total:
                    if best_perfect is None or overlap > best_perfect[0]:
                        best_perfect = (overlap, (dr, dc))
        if best_shift is not None:
            out[27] = _semblance_bucket(best_score, out_total)
            if best_perfect is not None:
                # a shift that explains the overlap EXACTLY (and covers at
                # least half the board) is a detected translation
                dr, dc = best_perfect[1]
                compass = {
                    (-1, 0): 1, (-1, 1): 2, (0, 1): 3, (1, 1): 4,
                    (1, 0): 5, (1, -1): 6, (0, -1): 7, (-1, -1): 8,
                }
                out[29] = compass[(int(np.sign(dr)), int(np.sign(dc)))]
                out[30] = _span_bucket(max(abs(dr), abs(dc)))
            else:
                out[29] = 9

    # best-fit recolor consistency + mode map
    if same_shape:
        codes = inp.astype(np.int64) * 10 + outp.astype(np.int64)
        cooc = np.bincount(codes.ravel(), minlength=100).reshape(10, 10)
        out[28] = _semblance_bucket(int(cooc.max(axis=1).sum()), out_total)
        nz_counts = np.bincount(inp.ravel(), minlength=10)
        nz_counts[0] = 0
        if nz_counts.sum() > 0:
            mode_color = int(nz_counts.argmax())
            sel = outp[inp == mode_color]
            uniq = np.unique(sel)
            out[31] = int(uniq[0]) if uniq.size == 1 else 10
        else:
            out[31] = 11
    else:
        out[31] = 11

    # comparable per-color count deltas (any shapes)
    in_counts = np.bincount(inp.ravel(), minlength=10)
    out_counts = np.bincount(outp.ravel(), minlength=10)
    for color in range(10):
        out[32 + color] = _signed_delta_bucket(int(out_counts[color] - in_counts[color]))

    # stamping: connected clusters of changed cells
    if same_shape:
        changed = inp != outp
        cluster_cells: list[list[tuple[int, int]]] = []
        seen = np.zeros_like(changed)
        for r in range(in_h):
            for c in range(in_w):
                if not changed[r, c] or seen[r, c]:
                    continue
                stack = [(r, c)]
                seen[r, c] = True
                cells = []
                while stack:
                    rr, cc = stack.pop()
                    cells.append((rr, cc))
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        nr, nc = rr + dr, cc + dc
                        if 0 <= nr < in_h and 0 <= nc < in_w and changed[nr, nc] and not seen[nr, nc]:
                            seen[nr, nc] = True
                            stack.append((nr, nc))
                cluster_cells.append(cells)
        n_clusters = len(cluster_cells)
        out[42] = 1 + min(n_clusters, 6)
        if n_clusters >= 2:
            shapes = {
                tuple(sorted((r - min(x for x, _ in cells), c - min(y for _, y in cells)) for r, c in cells))
                for cells in cluster_cells
            }
            out[43] = 2 if len(shapes) == 1 else 1
        if n_clusters:
            out[44] = _size_bucket(max(len(cells) for cells in cluster_cells))

    # ORDER deltas: did the rule create or destroy structure?
    def _structure(g: np.ndarray) -> dict:
        h, w = g.shape
        total = h * w
        metrics = {
            "lr": (int((g == g[:, ::-1]).sum()), total),
            "ud": (int((g == g[::-1, :]).sum()), total),
            "r180": (int((g == g[::-1, ::-1]).sum()), total),
        }
        best_m, best_t = 0, 0
        for p in range(1, h):
            m, t = int((g[p:] == g[:-p]).sum()), (h - p) * w
            if t > 0 and (best_t == 0 or m * best_t > best_m * t):
                best_m, best_t = m, t
        for p in range(1, w):
            m, t = int((g[:, p:] == g[:, :-p]).sum()), (w - p) * h
            if t > 0 and (best_t == 0 or m * best_t > best_m * t):
                best_m, best_t = m, t
        metrics["period"] = (best_m, best_t)
        counts = np.bincount(g.ravel(), minlength=10)
        metrics["n_colors"] = int((counts[1:] > 0).sum())
        metrics["nonzero"] = int(counts[1:].sum())
        return metrics

    s_in, s_out = _structure(inp), _structure(outp)
    out[45] = _order_delta(*s_in["lr"], *s_out["lr"])
    out[46] = _order_delta(*s_in["ud"], *s_out["ud"])
    out[47] = _order_delta(*s_in["r180"], *s_out["r180"])
    out[48] = _order_delta(*s_in["period"], *s_out["period"])
    out[49] = _signed_delta_bucket(s_out["n_colors"] - s_in["n_colors"])
    out[50] = _signed_delta_bucket(s_out["nonzero"] - s_in["nonzero"])
    return out


def _board_set_features(
    ids: torch.Tensor,
    masks: torch.Tensor,
    partners: Optional[torch.Tensor],
    partner_masks: Optional[torch.Tensor],
    canvas_size: int,
    null_color_id: int,
) -> torch.Tensor:
    """ids/masks: (..., canvas*canvas) -> (..., canvas*canvas, C)."""
    lead_shape = ids.shape[:-1]
    flat_ids = ids.reshape(-1, canvas_size, canvas_size)
    flat_masks = masks.reshape(-1, canvas_size, canvas_size)
    flat_partners = (
        partners.reshape(-1, canvas_size, canvas_size) if partners is not None else None
    )
    flat_partner_masks = (
        partner_masks.reshape(-1, canvas_size, canvas_size) if partner_masks is not None else None
    )
    out = []
    for idx in range(flat_ids.shape[0]):
        out.append(
            episode_feature_channels(
                flat_ids[idx],
                flat_masks[idx],
                partner=flat_partners[idx] if flat_partners is not None else None,
                partner_mask=flat_partner_masks[idx] if flat_partner_masks is not None else None,
                null_color_id=null_color_id,
            )
        )
    stacked = torch.stack(out, dim=0)
    return stacked.reshape(*lead_shape, canvas_size * canvas_size, len(EPISODE_FEATURE_NAMES))


def add_episode_features_to_batch(
    batch: dict[str, torch.Tensor],
    *,
    null_color_id: int = 10,
) -> dict[str, torch.Tensor]:
    """Replace the 10-channel GRID features in a bottleneck batch with the
    expanded episode set. Demo boards get pair-diff channels against their
    partner; query inputs get NA there. Call from collate/dataloader."""
    demo_input_ids = batch["demo_input_ids"]
    demo_output_ids = batch["demo_output_ids"]
    num_cells = demo_input_ids.shape[-1]
    canvas_size = int(num_cells ** 0.5)
    if canvas_size * canvas_size != num_cells:
        raise ValueError(f"non-square cell count {num_cells}")
    demo_input_masks = batch.get("demo_input_masks")
    if demo_input_masks is None:
        demo_input_masks = demo_input_ids != null_color_id
    demo_output_masks = batch.get("demo_output_masks")
    if demo_output_masks is None:
        demo_output_masks = demo_output_ids != null_color_id
    query_input_ids = batch["query_input_ids"]
    query_input_mask = batch.get("query_input_mask")
    if query_input_mask is None:
        query_input_mask = query_input_ids != null_color_id

    out = dict(batch)
    out["demo_input_features"] = _board_set_features(
        demo_input_ids, demo_input_masks, demo_output_ids, demo_output_masks,
        canvas_size, null_color_id,
    )
    out["demo_output_features"] = _board_set_features(
        demo_output_ids, demo_output_masks, demo_input_ids, demo_input_masks,
        canvas_size, null_color_id,
    )
    out["query_input_features"] = _board_set_features(
        query_input_ids, query_input_mask, None, None, canvas_size, null_color_id,
    )

    def board_tokens(ids: torch.Tensor, masks: torch.Tensor) -> torch.Tensor:
        lead_shape = ids.shape[:-1]
        flat_ids = ids.reshape(-1, canvas_size, canvas_size)
        flat_masks = masks.reshape(-1, canvas_size, canvas_size)
        rows = [
            board_token_features(flat_ids[idx], flat_masks[idx], null_color_id=null_color_id)
            for idx in range(flat_ids.shape[0])
        ]
        return torch.stack(rows, dim=0).reshape(*lead_shape, len(BOARD_TOKEN_FEATURE_NAMES))

    out["demo_input_board_features"] = board_tokens(demo_input_ids, demo_input_masks)
    out["demo_output_board_features"] = board_tokens(demo_output_ids, demo_output_masks)
    out["query_board_features"] = board_tokens(query_input_ids, query_input_mask)

    bsz, pairs, _ = demo_input_ids.shape
    flat_in = demo_input_ids.reshape(-1, canvas_size, canvas_size)
    flat_in_mask = demo_input_masks.reshape(-1, canvas_size, canvas_size)
    flat_out = demo_output_ids.reshape(-1, canvas_size, canvas_size)
    flat_out_mask = demo_output_masks.reshape(-1, canvas_size, canvas_size)
    pair_rows = [
        pair_token_features(
            flat_in[idx], flat_in_mask[idx], flat_out[idx], flat_out_mask[idx],
            null_color_id=null_color_id,
        )
        for idx in range(flat_in.shape[0])
    ]
    out["pair_features"] = torch.stack(pair_rows, dim=0).reshape(
        bsz, pairs, len(PAIR_TOKEN_FEATURE_NAMES)
    )
    return out


__all__ = [
    "BOARD_TOKEN_FEATURE_NAMES",
    "BOARD_TOKEN_FEATURE_VOCAB_SIZES",
    "EPISODE_FEATURE_NAMES",
    "EPISODE_FEATURE_VOCAB_SIZES",
    "PAIR_TOKEN_FEATURE_NAMES",
    "PAIR_TOKEN_FEATURE_VOCAB_SIZES",
    "board_token_features",
    "pair_token_features",
    "PAIR_CHANGED_DIFF",
    "PAIR_CHANGED_NA",
    "PAIR_CHANGED_SAME",
    "PARTNER_NA",
    "PARTNER_OUTSIDE",
    "add_episode_features_to_batch",
    "episode_feature_channels",
    "episode_feature_channels_reference",
]
