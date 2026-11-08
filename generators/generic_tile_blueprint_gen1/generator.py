"""gen1: separator-lattice tiles whose anomalous motif encodes a blueprint.

A separator-color lattice divides the field into equal motif tiles.  Most tiles
show one two-color NORMAL motif.  A few show the same ANOMALOUS motif, obtained
by painting a non-rectangular mask inside the normal motif with one NOVEL color.
The novel-color mask is also a blueprint at tile scale: the anomalous tiles are
only a strict subset of one translated copy of that mask.  Complete that unique
translated copy with anomalous motifs and restore every other tile to normal.
"""
from __future__ import annotations

from collections import Counter
from itertools import combinations
import hashlib

from puzzle_generators.base import gen_ctx

VERSION = "2.0.0"
TASK_ID = "generic_tile_blueprint_gen1"
GENERATOR_ID = TASK_ID
SUMMARY = (
    "Read the novel-color mask inside the anomalous tile motif, align that mask "
    "uniquely to the partially anomalous tile positions, and complete the same "
    "mask at tile scale while leaving separator lines unchanged."
)
INVARIANTS = (
    "a full separator-color border and separator rows/columns partition the input into equal tiles",
    "exactly one two-color normal motif is the strict modal tile and exactly one anomalous motif adds one novel color",
    "the novel-color motif mask is non-rectangular and contains 4..7 cells",
    "the visible anomalous tiles are a strict subset of one translated copy of that mask at tile scale",
    "the partial anomalous positions determine exactly one in-bounds translation and that translation is not the origin",
    "the output preserves dimensions, separators, motif colors, and tile geometry while adding the missing anomalous tiles",
    "each lesson varies the motif mask, novel color, and alignment so fixed-mask/fixed-color/fixed-position shortcuts fail",
)
AXES = {"difficulty": ("easy", "medium", "hard")}
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0

PROGRAM = """(rule!
 ;; Lattice of tiles separated by full separator rows/cols. One repeated
 ;; NORMAL tile motif; a few tiles carry an ANOMALOUS motif containing a
 ;; NOVEL color (absent from the normal motif and the separator). The novel
 ;; color's cell mask inside the anomalous motif is a BLUEPRINT at tile
 ;; scale: the input's anomalous tiles render part of it; complete it —
 ;; every blueprint tile gets the anomalous motif, all others the normal.
 (lambda (g)
   (let ()
     (define h (rows g))
     (define w (cols g))
     (define sep (at g 0 0))
     (define (sep-row? r) (and (row-uniform? g r) (= (at g r 0) sep)))
     (define (sep-col? c) (and (col-uniform? g c) (= (at g 0 c) sep)))
     (define row0s (filter (lambda (r) (and (not (sep-row? r))
                                            (or (= r 0) (sep-row? (- r 1)))))
                           (range 0 h)))
     (define col0s (filter (lambda (c) (and (not (sep-col? c))
                                            (or (= c 0) (sep-col? (- c 1)))))
                           (range 0 w)))
     (define th (let loop ((r (first row0s)) (n 0))
                  (if (and (< r h) (not (sep-row? r))) (loop (+ r 1) (+ n 1)) n)))
     (define tw (let loop ((c (first col0s)) (n 0))
                  (if (and (< c w) (not (sep-col? c))) (loop (+ c 1) (+ n 1)) n)))
     (define nr (length row0s))
     (define nc (length col0s))
     (define (tile-at ti tj)
       (let ((r0 (nth row0s ti)) (c0 (nth col0s tj)))
         (subgrid g r0 c0 (+ r0 (- th 1)) (+ c0 (- tw 1)))))
     (define all-pos
       (flatmap (lambda (ti) (map (lambda (tj) (list ti tj)) (range 0 nc)))
                (range 0 nr)))
     (define tiles (map (lambda (p) (tile-at (first p) (second p))) all-pos))
     (define (freq t) (count-if (lambda (u) (equal? u t)) tiles))
     (define normal
       (reduce (lambda (best t) (if (> (freq t) (freq best)) t best))
               (first tiles) tiles))
     (define anom-pos
       (filter (lambda (p) (not (equal? (tile-at (first p) (second p)) normal)))
               all-pos))
     (define pat (tile-at (first (first anom-pos)) (second (first anom-pos))))
     (define novel
       (first (filter (lambda (v) (and (!= v sep)
                                       (not (member? v (grid-colors normal)))))
                      (grid-colors pat))))
     (define mask (find-color pat novel))
     (define (pos-in? p lst)
       (< 0 (count-if (lambda (q) (and (= (first p) (first q))
                                       (= (second p) (second q))))
                      lst)))
     (define (mask-shift o)
       (map (lambda (m) (list (+ (first m) (first o))
                              (+ (second m) (second o))))
            mask))
     (define (valid-off? o)
       (let ((sm (mask-shift o)))
         (and (= (length sm)
                 (count-if (lambda (p) (and (>= (first p) 0) (< (first p) nr)
                                            (>= (second p) 0) (< (second p) nc)))
                           sm))
              (= (length anom-pos)
                 (count-if (lambda (p) (pos-in? p sm)) anom-pos)))))
     (define off
       (first (filter valid-off?
                      (flatmap (lambda (a) (map (lambda (b) (list a b))
                                                (range (- 1 tw) nc)))
                               (range (- 1 th) nr)))))
     (define target (mask-shift off))
     (for*/fold ((out g)) ((ti (in-range nr)) (tj (in-range nc)))
       (paste out (if (pos-in? (list ti tj) target) pat normal)
              (nth row0s ti) (nth col0s tj))))))"""


def _normalized_rule_text(source: str) -> str:
    # Match scripts.canonical_profile_gate.normalized_rule_hash: selected-source
    # comments are part of the pinned training authority, so this normalization
    # changes whitespace only and keeps the first 12 SHA-256 hex digits.
    return " ".join(source.split())


RULE_HASH = hashlib.sha256(_normalized_rule_text(PROGRAM).encode("utf-8")).hexdigest()[:12]

_BAND_CONFIG = {
    "easy": {"dims": (3, 3, 5, 5), "train": 3, "test": 1},
    "medium": {"dims": None, "train": 3, "test": 2},
    "hard": {"dims": (4, 4, 5, 5), "train": 4, "test": 2},
}


def _valid_grid(grid) -> bool:
    return bool(
        isinstance(grid, list)
        and grid
        and all(isinstance(row, list) and row for row in grid)
        and len({len(row) for row in grid}) == 1
        and all(
            isinstance(value, int)
            and not isinstance(value, bool)
            and 0 <= value <= 9
            for row in grid
            for value in row
        )
    )


def _apply(g):
    """Python mirror of PROGRAM (same mode tie-break and offset scan order)."""
    h, w = len(g), len(g[0])
    sep = g[0][0]
    sep_row = [all(v == sep for v in g[r]) for r in range(h)]
    sep_col = [all(g[r][c] == sep for r in range(h)) for c in range(w)]
    row0s = [r for r in range(h) if not sep_row[r] and (r == 0 or sep_row[r - 1])]
    col0s = [c for c in range(w) if not sep_col[c] and (c == 0 or sep_col[c - 1])]
    th = 0
    r = row0s[0]
    while r < h and not sep_row[r]:
        th += 1
        r += 1
    tw = 0
    c = col0s[0]
    while c < w and not sep_col[c]:
        tw += 1
        c += 1
    nr, nc = len(row0s), len(col0s)

    def tile_at(ti, tj):
        r0, c0 = row0s[ti], col0s[tj]
        return tuple(tuple(g[r0 + i][c0 + j] for j in range(tw)) for i in range(th))

    all_pos = [(ti, tj) for ti in range(nr) for tj in range(nc)]
    tiles = [tile_at(*p) for p in all_pos]

    def freq(tile):
        return sum(1 for other in tiles if other == tile)

    normal = tiles[0]
    for tile in tiles[1:]:
        if freq(tile) > freq(normal):
            normal = tile
    anom_pos = [p for p in all_pos if tile_at(*p) != normal]
    pat = tile_at(*anom_pos[0])
    normal_colors = {v for row in normal for v in row}
    novel = next(
        v for row in pat for v in row if v != sep and v not in normal_colors
    )
    mask = [(i, j) for i in range(th) for j in range(tw) if pat[i][j] == novel]

    off = None
    for a in range(1 - th, nr):
        for b in range(1 - tw, nc):
            shifted = [(mi + a, mj + b) for mi, mj in mask]
            if all(0 <= p < nr and 0 <= q < nc for p, q in shifted) and all(
                p in shifted for p in anom_pos
            ):
                off = (a, b)
                break
        if off is not None:
            break
    target = {(mi + off[0], mj + off[1]) for mi, mj in mask}
    out = [row[:] for row in g]
    for ti in range(nr):
        for tj in range(nc):
            src = pat if (ti, tj) in target else normal
            r0, c0 = row0s[ti], col0s[tj]
            for i in range(th):
                for j in range(tw):
                    out[r0 + i][c0 + j] = src[i][j]
    return out


def _profile_band(th: int, tw: int, nr: int, nc: int):
    if (th, tw, nr, nc) == (3, 3, 5, 5):
        return "easy"
    if th == tw == 3 and nr in (6, 7) and nc in (6, 7):
        return "medium"
    if (th, tw, nr, nc) == (4, 4, 5, 5):
        return "hard"
    return None


def _valid_offsets(mask, nr, nc, shown):
    shown = set(shown)
    offsets = []
    for a in range(1 - max(i for i, _ in mask) - 1, nr):
        for b in range(1 - max(j for _, j in mask) - 1, nc):
            shifted = {(i + a, j + b) for i, j in mask}
            if len(shifted) != len(mask):
                continue
            if not all(0 <= i < nr and 0 <= j < nc for i, j in shifted):
                continue
            if shown <= shifted:
                offsets.append((a, b))
    return offsets


def _parse_scene(grid):
    """Return (observable scene dict or None, grammar reasons)."""
    if not _valid_grid(grid):
        return None, ["grid must be a nonempty rectangular ARC color grid"]

    reasons = []
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30:
        reasons.append("grid dimensions must not exceed 30x30")
    sep = grid[0][0]
    sep_rows = [all(v == sep for v in grid[r]) for r in range(h)]
    sep_cols = [all(grid[r][c] == sep for r in range(h)) for c in range(w)]
    if not sep_rows[0] or not sep_rows[-1] or not sep_cols[0] or not sep_cols[-1]:
        reasons.append("separator color must form the complete outer border")

    row0s = [r for r in range(h) if not sep_rows[r] and (r == 0 or sep_rows[r - 1])]
    col0s = [c for c in range(w) if not sep_cols[c] and (c == 0 or sep_cols[c - 1])]
    if not row0s or not col0s:
        return None, sorted(set(reasons + ["separator lattice must contain motif tiles"]))

    th = 0
    r = row0s[0]
    while r < h and not sep_rows[r]:
        th += 1
        r += 1
    tw = 0
    c = col0s[0]
    while c < w and not sep_cols[c]:
        tw += 1
        c += 1
    if th <= 0 or tw <= 0:
        return None, sorted(set(reasons + ["tile dimensions must be positive"]))
    nr, nc = len(row0s), len(col0s)

    expected_sep_rows = list(range(0, h, th + 1))
    expected_sep_cols = list(range(0, w, tw + 1))
    actual_sep_rows = [r for r, flag in enumerate(sep_rows) if flag]
    actual_sep_cols = [c for c, flag in enumerate(sep_cols) if flag]
    if expected_sep_rows != actual_sep_rows or expected_sep_rows[-1] != h - 1:
        reasons.append("separator rows must occur at one exact regular tile spacing")
    if expected_sep_cols != actual_sep_cols or expected_sep_cols[-1] != w - 1:
        reasons.append("separator columns must occur at one exact regular tile spacing")
    band = _profile_band(th, tw, nr, nc)
    if band is None:
        reasons.append("tile and lattice dimensions must match exactly one difficulty profile")

    def tile_at(ti, tj):
        r0, c0 = row0s[ti], col0s[tj]
        return tuple(
            tuple(grid[r0 + i][c0 + j] for j in range(tw)) for i in range(th)
        )

    positions = [(ti, tj) for ti in range(nr) for tj in range(nc)]
    tiles = [tile_at(*p) for p in positions]
    freqs = Counter(tiles)
    if len(freqs) != 2:
        return None, sorted(set(reasons + ["lattice must contain exactly two tile motifs"]))
    max_freq = max(freqs.values())
    normal = next(tile for tile in tiles if freqs[tile] == max_freq)
    anomaly_patterns = [tile for tile in freqs if tile != normal]
    pat = anomaly_patterns[0]
    if freqs[normal] <= freqs[pat]:
        reasons.append("normal motif must be the strict modal tile")
    anomalies = [p for p in positions if tile_at(*p) != normal]

    normal_colors = {v for row in normal for v in row}
    pat_colors = {v for row in pat for v in row}
    if sep in normal_colors or sep in pat_colors:
        reasons.append("separator color must not appear inside either tile motif")
    if len(normal_colors) != 2:
        reasons.append("normal motif must use exactly two colors")
    novel_colors = pat_colors - normal_colors
    if len(novel_colors) != 1:
        reasons.append("anomalous motif must add exactly one novel color")
        novel = None
        mask = []
    else:
        novel = next(iter(novel_colors))
        mask = [(i, j) for i in range(th) for j in range(tw) if pat[i][j] == novel]
        if any(
            pat[i][j] != normal[i][j] and pat[i][j] != novel
            for i in range(th)
            for j in range(tw)
        ):
            reasons.append("anomalous motif may differ from normal only by novel-color cells")
        if any(
            pat[i][j] != normal[i][j]
            for i in range(th)
            for j in range(tw)
            if (i, j) not in mask
        ):
            reasons.append("non-mask anomalous-motif cells must equal the normal motif")

    if mask:
        if not (4 <= len(mask) <= min(7, th * tw - 1)):
            reasons.append("novel-color mask must contain 4..7 cells and leave at least one normal cell")
        mr = [i for i, _ in mask]
        mc = [j for _, j in mask]
        bbox = {
            (i, j)
            for i in range(min(mr), max(mr) + 1)
            for j in range(min(mc), max(mc) + 1)
        }
        if set(mask) == bbox:
            reasons.append("novel-color blueprint mask must be non-rectangular")
    if mask and not (2 <= len(anomalies) < len(mask)):
        reasons.append("visible anomalous tiles must be a strict subset of the blueprint mask")

    offsets = _valid_offsets(mask, nr, nc, anomalies) if mask else []
    if len(offsets) != 1:
        reasons.append("visible anomalous tiles must determine exactly one in-bounds mask translation")
    selected_offset = offsets[0] if len(offsets) == 1 else None
    if selected_offset == (0, 0):
        reasons.append("blueprint translation must be nonzero to refute origin anchoring")

    scene = {
        "h": h,
        "w": w,
        "sep": sep,
        "row0s": row0s,
        "col0s": col0s,
        "th": th,
        "tw": tw,
        "nr": nr,
        "nc": nc,
        "band": band,
        "normal": normal,
        "pat": pat,
        "novel": novel,
        "mask": tuple(mask),
        "anomalies": tuple(anomalies),
        "valid_offsets": tuple(offsets),
        "selected_offset": selected_offset,
    }
    return scene, sorted(set(reasons))


def _paint_target(grid, scene, target):
    target = set(target)
    out = [row[:] for row in grid]
    for ti in range(scene["nr"]):
        for tj in range(scene["nc"]):
            src = scene["pat"] if (ti, tj) in target else scene["normal"]
            r0, c0 = scene["row0s"][ti], scene["col0s"][tj]
            for i in range(scene["th"]):
                for j in range(scene["tw"]):
                    out[r0 + i][c0 + j] = src[i][j]
    return out


def _rival_leave_partial(grid):
    return [row[:] for row in grid]


def _rival_anchor_mask_at_origin(grid):
    scene, reasons = _parse_scene(grid)
    if scene is None:
        raise ValueError(reasons[0] if reasons else "invalid scene")
    return _paint_target(grid, scene, set(scene["mask"]))


def _rival_fill_anomaly_bbox(grid):
    scene, reasons = _parse_scene(grid)
    if scene is None or not scene["anomalies"]:
        raise ValueError(reasons[0] if reasons else "invalid scene")
    rows = [r for r, _ in scene["anomalies"]]
    cols = [c for _, c in scene["anomalies"]]
    target = {
        (r, c)
        for r in range(min(rows), max(rows) + 1)
        for c in range(min(cols), max(cols) + 1)
    }
    return _paint_target(grid, scene, target)


def _witness_unique_alignment(grid):
    scene, _ = _parse_scene(grid)
    return bool(scene and len(scene["valid_offsets"]) == 1)


def _witness_partial_blueprint(grid):
    scene, _ = _parse_scene(grid)
    return bool(scene and 2 <= len(scene["anomalies"]) < len(scene["mask"]))


def _witness_translated_blueprint(grid):
    scene, _ = _parse_scene(grid)
    return bool(scene and scene["selected_offset"] not in (None, (0, 0)))


def _witness_nonrectangular_mask(grid):
    scene, _ = _parse_scene(grid)
    if not scene or not scene["mask"]:
        return False
    rows = [r for r, _ in scene["mask"]]
    cols = [c for _, c in scene["mask"]]
    bbox = {
        (r, c)
        for r in range(min(rows), max(rows) + 1)
        for c in range(min(cols), max(cols) + 1)
    }
    return set(scene["mask"]) != bbox


def _witness_completion_changes_input(grid):
    try:
        return _apply(grid) != grid
    except Exception:
        return False


SEMANTIC_WITNESSES = {
    "unique_alignment": _witness_unique_alignment,
    "partial_blueprint": _witness_partial_blueprint,
    "translated_blueprint": _witness_translated_blueprint,
    "nonrectangular_mask": _witness_nonrectangular_mask,
    "completion_changes_input": _witness_completion_changes_input,
}
SEMANTIC_RIVALS = {
    "leave_partial_input": _rival_leave_partial,
    "anchor_mask_at_tile_origin": _rival_anchor_mask_at_origin,
    "fill_anomaly_bbox": _rival_fill_anomaly_bbox,
}
WITNESS_RIVALS = {
    "unique_alignment": ["anchor_mask_at_tile_origin"],
    "partial_blueprint": ["leave_partial_input"],
    "translated_blueprint": ["anchor_mask_at_tile_origin"],
    "nonrectangular_mask": ["fill_anomaly_bbox"],
    "completion_changes_input": ["leave_partial_input"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def strict_canonical_like(grid):
    """Reject scenes outside the unambiguous tile-blueprint teaching grammar."""
    scene, reasons = _parse_scene(grid)
    if scene is None:
        return reasons
    expected = None
    try:
        expected = _apply(grid)
    except Exception as exc:
        reasons.append(f"selected PROGRAM mirror raised {type(exc).__name__}")
    if expected is not None:
        if expected == grid:
            reasons.append("blueprint completion must change at least one tile")
        for name, rival in SEMANTIC_RIVALS.items():
            try:
                if rival(grid) == expected:
                    reasons.append(f"named shortcut {name} still matches the answer")
            except Exception as exc:
                reasons.append(f"named shortcut {name} raised {type(exc).__name__}")
    return sorted(set(reasons))


def _mask_signature(grid):
    scene, _ = _parse_scene(grid)
    return tuple(scene["mask"]) if scene else ()


def _offset_signature(grid):
    scene, _ = _parse_scene(grid)
    return scene["selected_offset"] if scene else None


def _novel_color(grid):
    scene, _ = _parse_scene(grid)
    return scene["novel"] if scene else None


def lesson_identifiable(demos, query):
    """Require enough demonstrations to rule out fixed mask/color/position shortcuts."""
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"lesson needs at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict):
        return ["query must be an input/output pair"]

    reasons = []
    pairs = list(demos) + [query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} is missing input/output")
            continue
        grammar = strict_canonical_like(pair["input"])
        if grammar:
            reasons.append(f"pair {index} is outside the grammar: {grammar[0]}")
            continue
        if _apply(pair["input"]) != pair["output"]:
            reasons.append(f"pair {index} output is not exact tile-blueprint completion")
    if reasons:
        return sorted(set(reasons))

    if len({_mask_signature(pair["input"]) for pair in demos}) < 2:
        reasons.append("demonstrations must vary the novel-color blueprint mask")
    if len({_offset_signature(pair["input"]) for pair in demos}) < 2:
        reasons.append("demonstrations must vary the blueprint translation")
    if len({_novel_color(pair["input"]) for pair in demos}) < 2:
        reasons.append("demonstrations must vary the novel motif color")

    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits = all(rival(pair["input"]) == pair["output"] for pair in demos)
        except Exception as exc:
            reasons.append(f"competitor {name} raised {type(exc).__name__}: {exc}")
            continue
        if fits:
            suffix = (
                "and also matches the query"
                if rival(query["input"]) == query["output"]
                else "but disagrees on the query"
            )
            reasons.append(f"competitor {name} fits every demonstration {suffix}")
    return sorted(set(reasons))


def _dims_for(rng, difficulty):
    """Return a difficulty-observable (th, tw, nr, nc) profile, capped at 30."""
    if difficulty == "easy":
        return 3, 3, 5, 5
    if difficulty == "medium":
        return 3, 3, rng.randint(6, 7), rng.randint(6, 7)
    if difficulty == "hard":
        return 4, 4, 5, 5
    raise ValueError(f"unsupported difficulty: {difficulty!r}")


def _nonrectangular(mask):
    rows = [r for r, _ in mask]
    cols = [c for _, c in mask]
    bbox = {
        (r, c)
        for r in range(min(rows), max(rows) + 1)
        for c in range(min(cols), max(cols) + 1)
    }
    return set(mask) != bbox


def _choose_unique_partial(rng, mask, nr, nc, offset):
    target = [(i + offset[0], j + offset[1]) for i, j in mask]
    candidates = []
    for size in range(2, len(mask)):
        for chosen in combinations(range(len(mask)), size):
            shown = {target[index] for index in chosen}
            if _valid_offsets(mask, nr, nc, shown) == [offset]:
                candidates.append(shown)
    if not candidates:
        return None
    return set(rng.choice(candidates))


def _build_pair(
    rng,
    th,
    tw,
    nr,
    nc,
    *,
    forbidden_masks=(),
    forbidden_novels=(),
    previous_offset=None,
):
    forbidden_masks = set(forbidden_masks)
    forbidden_novels = set(forbidden_novels)
    for _ in range(256):
        sep = rng.randint(0, 9)
        novel_choices = [v for v in range(10) if v != sep and v not in forbidden_novels]
        if not novel_choices:
            continue
        novel = rng.choice(novel_choices)
        normal_pool = [v for v in range(10) if v not in (sep, novel)]
        ca, cb = rng.sample(normal_pool, 2)
        while True:
            normal = [[rng.choice((ca, cb)) for _ in range(tw)] for _ in range(th)]
            if len({v for row in normal for v in row}) == 2:
                break

        cells = [(i, j) for i in range(th) for j in range(tw)]
        mask = rng.sample(cells, rng.randint(4, min(7, th * tw - 1)))
        mask_signature = tuple(sorted(mask))
        if mask_signature in forbidden_masks or not _nonrectangular(mask):
            continue
        pat = [row[:] for row in normal]
        for i, j in mask:
            pat[i][j] = novel

        feasible = []
        empty_shown = set()
        for offset in _valid_offsets(mask, nr, nc, empty_shown):
            if offset == (0, 0) or offset == previous_offset:
                continue
            partial = _choose_unique_partial(rng, mask, nr, nc, offset)
            if partial is not None:
                feasible.append((offset, partial))
        if not feasible:
            continue
        offset, shown = rng.choice(feasible)

        h, w = nr * (th + 1) + 1, nc * (tw + 1) + 1
        grid = [[sep] * w for _ in range(h)]
        for ti in range(nr):
            for tj in range(nc):
                src = pat if (ti, tj) in shown else normal
                r0, c0 = 1 + ti * (th + 1), 1 + tj * (tw + 1)
                for i in range(th):
                    for j in range(tw):
                        grid[r0 + i][c0 + j] = src[i][j]
        if strict_canonical_like(grid):
            continue
        return grid
    raise ValueError("could not build an unambiguous shortcut-refuting tile-blueprint pair")


def generate_task(seed, *, difficulty="medium"):
    if difficulty not in _BAND_CONFIG:
        raise ValueError(f"unsupported difficulty: {difficulty!r}")
    config = _BAND_CONFIG[difficulty]
    ctx = gen_ctx(
        seed=seed,
        sample_index=0,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
    )
    n_train, n_test = config["train"], config["test"]
    pairs = []
    used_masks = set()
    used_novels = set()
    previous_offset = None
    for index in range(n_train + n_test):
        rng = ctx.draw_rng(f"pair_{index}")
        th, tw, nr, nc = _dims_for(rng, difficulty)
        gin = _build_pair(
            rng,
            th,
            tw,
            nr,
            nc,
            forbidden_masks=used_masks,
            forbidden_novels=used_novels,
            previous_offset=previous_offset,
        )
        scene, reasons = _parse_scene(gin)
        if reasons or scene is None:
            raise AssertionError(f"strict builder returned invalid scene: {reasons[:2]}")
        used_masks.add(tuple(scene["mask"]))
        used_novels.add(scene["novel"])
        previous_offset = scene["selected_offset"]
        pairs.append({"input": gin, "output": _apply(gin)})

    task = {
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "program": PROGRAM,
        "concept": "tile_blueprint",
        "chain": ["tile_lattice", "novel_mask", "unique_translation", "complete_blueprint"],
        "difficulty": difficulty,
        "meta": {
            "version": VERSION,
            "difficulty": difficulty,
            "rule_hash": RULE_HASH,
            "n_train": n_train,
            "n_test": n_test,
            "lesson_plan": "unique-alignment-plus-mask-color-position-variation",
        },
    }
    errors = self_check_task(task)
    if errors:
        raise AssertionError(f"generated task failed self_check_task: {errors[:3]}")
    return task


def self_check_task(task):
    """Validate complete generic lessons without mutating the returned task."""
    if not isinstance(task, dict):
        return ["task must be a dictionary"]
    errors = []
    difficulty = task.get("difficulty")
    config = _BAND_CONFIG.get(difficulty)
    if config is None:
        errors.append("task difficulty must be easy, medium, or hard")
        config = {"train": -1, "test": -1}

    train = list(task.get("train") or [])
    test = list(task.get("test") or [])
    if len(train) != config["train"]:
        errors.append("train pair count disagrees with the difficulty profile")
    if len(test) != config["test"]:
        errors.append("test pair count disagrees with the difficulty profile")
    if task.get("program") != PROGRAM:
        errors.append("task program must equal the selected PROGRAM authority")
    if task.get("concept") != "tile_blueprint":
        errors.append("task concept must be tile_blueprint")
    if task.get("chain") != [
        "tile_lattice",
        "novel_mask",
        "unique_translation",
        "complete_blueprint",
    ]:
        errors.append("task chain must name lattice -> mask -> translation -> completion")

    meta = task.get("meta") or {}
    if meta.get("version") != VERSION:
        errors.append("meta.version does not match VERSION")
    if meta.get("difficulty") != difficulty:
        errors.append("meta.difficulty disagrees with task difficulty")
    if meta.get("rule_hash") != RULE_HASH:
        errors.append("meta.rule_hash does not match RULE_HASH")
    if meta.get("n_train") != config["train"] or meta.get("n_test") != config["test"]:
        errors.append("meta pair counts disagree with the difficulty profile")

    seen_inputs = set()
    train_masks = set()
    train_offsets = set()
    train_novels = set()
    for split_name, split in (("train", train), ("test", test)):
        for index, pair in enumerate(split):
            label = f"{split_name}[{index}]"
            if not isinstance(pair, dict):
                errors.append(f"{label} must be a pair dictionary")
                continue
            gin, gout = pair.get("input"), pair.get("output")
            if not _valid_grid(gin) or not _valid_grid(gout):
                errors.append(f"{label} has an invalid input or output grid")
                continue
            signature = repr(gin)
            if signature in seen_inputs:
                errors.append(f"{label} duplicates an earlier input grid")
            seen_inputs.add(signature)

            grammar = strict_canonical_like(gin)
            errors.extend(f"{label}: {reason}" for reason in grammar)
            scene, _ = _parse_scene(gin)
            if scene is None:
                continue
            if scene["band"] != difficulty:
                errors.append(f"{label}: observable difficulty profile disagrees with task difficulty")
            if len(gout) != len(gin) or len(gout[0]) != len(gin[0]):
                errors.append(f"{label}: output dimensions must exactly match input dimensions")
                continue
            expected = _apply(gin)
            if gout != expected:
                errors.append(f"{label}: output is not exact tile-blueprint completion")
                continue
            if gout == gin:
                errors.append(f"{label}: completion must add at least one anomalous tile")
            for name, witness in SEMANTIC_WITNESSES.items():
                if not witness(gin):
                    errors.append(f"{label}: missing semantic witness {name}")
            for name, rival in SEMANTIC_RIVALS.items():
                if rival(gin) == gout:
                    errors.append(f"{label}: named rival {name} still matches the answer")
            if split_name == "train":
                train_masks.add(tuple(scene["mask"]))
                train_offsets.add(scene["selected_offset"])
                train_novels.add(scene["novel"])

    if len(train_masks) < 2:
        errors.append("train split must vary the blueprint mask")
    if len(train_offsets) < 2:
        errors.append("train split must vary the blueprint translation")
    if len(train_novels) < 2:
        errors.append("train split must vary the novel motif color")
    for query_index, query in enumerate(test):
        for reason in lesson_identifiable(train, query):
            errors.append(f"test[{query_index}] lesson: {reason}")
    return sorted(set(errors))


if __name__ == "__main__":
    from puzzle_generators.generic.concepts.tile_blueprint import parity_check

    parity_check(generate_task, n=25, version_label=f"tile_blueprint gen1 v{VERSION}")
