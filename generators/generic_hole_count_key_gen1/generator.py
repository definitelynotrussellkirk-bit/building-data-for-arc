"""gen1: legend of hole-pierced rectangle keys + gray blobs keyed by holes.

Scene: a 1-wide separator stripe (full row/col or corner L, color 1) walls
off a legend of 2-4 solid rectangle keys in distinct colors, key i pierced
by i single-cell holes. The field holds 4-8 gray blobs (nibbled rectangles)
with 0..max_key+1 enclosed holes each. Transform: recolor every gray blob
by the key whose hole-count matches its own; erase blobs with no matching
key; keys and stripe stay.
"""
from __future__ import annotations

from collections import Counter, defaultdict, deque
import hashlib

from puzzle_generators.base import gen_ctx

VERSION = "1.1.0"
TASK_ID = "generic_hole_count_key_gen1"
GENERATOR_ID = TASK_ID
SUMMARY = (
    "Read a legend of pierced rectangle keys as hole-count -> color, recolor "
    "each gray field blob by its enclosed-hole count, and erase unmatched blobs."
)
INVARIANTS = (
    "one full separator row or column divides legend from field",
    "legend keys are distinct-color filled rectangles with hole counts 0..k-1",
    "one key shares color 1 with the separator, so geometry—not color—identifies it",
    "legend spatial order is deliberately not hole-count order",
    "every pair contains gray blobs for every keyed count and at least one unmatched count",
    "two differently pierced gray blobs share one bbox size, refuting bbox-size proxies",
    "all non-gray cells remain fixed; matched gray cells recolor and unmatched gray cells erase",
)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

GRAY = 5
STRIPE = 1

PROGRAM = """(rule!
 ;; Legend keys are SOLID RECTANGLES (cells + enclosed holes fill their
 ;; bbox, both sides >= 2) in any non-gray color, each pierced by 0..n
 ;; single-cell holes: hole-count -> key color. Every GRAY (5) blob is
 ;; recolored by the key matching its own enclosed-hole count; blobs with
 ;; no matching key are erased. The separator stripe (1-wide / L-shaped,
 ;; never bbox-filling) and the keys themselves stay unchanged.
 (lambda (g)
   (let ()
     (define (hole-stats o)
       ;; (n-holes hole-area bbox-h bbox-w) via flood in the padded bbox
       (let* ((bb (obj-bbox o))
              (r1 (first bb)) (c1 (second bb))
              (r2 (nth bb 2)) (c2 (nth bb 3))
              (mask (paint-cells
                     (empty-grid (+ (- r2 r1) 3) (+ (- c2 c1) 3) 1)
                     (map (lambda (p) (list (+ (- (first p) r1) 1)
                                            (+ (- (second p) c1) 1)))
                          (obj-cells o))
                     0))
              (hole-objs (filter (lambda (q) (not (bordering? q mask)))
                                 (objects mask 0))))
         (list (length hole-objs)
               (reduce (lambda (n q) (+ n (obj-size q))) 0 hole-objs)
               (+ (- r2 r1) 1) (+ (- c2 c1) 1))))
     (define objs (objects g 0))
     (define keymap
       (flatmap (lambda (o)
                  (let ((s (hole-stats o)))
                    (if (and (!= (obj-color o) 5)
                             (>= (min (nth s 2) (nth s 3)) 2)
                             (= (+ (obj-size o) (second s))
                                (* (nth s 2) (nth s 3))))
                        (list (list (first s) (obj-color o)))
                        (list))))
                objs))
     (define (lookup k)
       (let ((hit (filter (lambda (e) (= (first e) k)) keymap)))
         (if (null? hit) 0 (second (first hit)))))
     (reduce (lambda (out o)
               (if (= (obj-color o) 5)
                   (recolor-cells out (obj-cells o)
                                  (lookup (first (hole-stats o))))
                   out))
             g objs))))"""


def _normalized_rule_text(source):
    """Comment/whitespace-normalized authority text for evidence invalidation."""
    code = "\n".join(line.split(";", 1)[0] for line in source.splitlines())
    return " ".join(code.split())


RULE_HASH = hashlib.sha256(_normalized_rule_text(PROGRAM).encode("utf-8")).hexdigest()


def _components(g):
    h, w = len(g), len(g[0])
    seen = [[False] * w for _ in range(h)]
    out = []
    for r in range(h):
        for c in range(w):
            if g[r][c] != 0 and not seen[r][c]:
                col = g[r][c]
                comp = []
                q = deque([(r, c)])
                seen[r][c] = True
                while q:
                    x, y = q.popleft()
                    comp.append((x, y))
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < h and 0 <= ny < w and not seen[nx][ny] \
                                and g[nx][ny] == col:
                            seen[nx][ny] = True
                            q.append((nx, ny))
                out.append((col, comp))
    return out


def _hole_stats(comp):
    """(n_holes, hole_area, bbox_h, bbox_w) — mirror of the Racket flood."""
    cells = set(comp)
    r1 = min(r for r, _ in comp) - 1
    c1 = min(c for _, c in comp) - 1
    r2 = max(r for r, _ in comp) + 1
    c2 = max(c for _, c in comp) + 1
    hh, ww = r2 - r1 + 1, c2 - c1 + 1
    seen = [[False] * ww for _ in range(hh)]
    n = area = 0
    for i in range(hh):
        for j in range(ww):
            if not seen[i][j] and (i + r1, j + c1) not in cells:
                q = deque([(i, j)])
                seen[i][j] = True
                size = 1
                border = False
                while q:
                    x, y = q.popleft()
                    if x in (0, hh - 1) or y in (0, ww - 1):
                        border = True
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < hh and 0 <= ny < ww and not seen[nx][ny] \
                                and (nx + r1, ny + c1) not in cells:
                            seen[nx][ny] = True
                            size += 1
                            q.append((nx, ny))
                if not border:
                    n += 1
                    area += size
    return n, area, hh - 2, ww - 2


def _apply(g):
    """Python mirror of PROGRAM."""
    comps = _components(g)
    keymap = {}
    for col, comp in comps:
        n, area, bh, bw = _hole_stats(comp)
        if col != GRAY and min(bh, bw) >= 2 and len(comp) + area == bh * bw \
                and n not in keymap:
            keymap[n] = col
    out = [row[:] for row in g]
    for col, comp in comps:
        if col == GRAY:
            n, _, _, _ = _hole_stats(comp)
            newc = keymap.get(n, 0)
            for r, c in comp:
                out[r][c] = newc
    return out


def _bbox(comp):
    rs = [r for r, _ in comp]
    cs = [c for _, c in comp]
    return min(rs), min(cs), max(rs), max(cs)


def _descriptor(col, comp):
    n, area, bh, bw = _hole_stats(comp)
    return {
        "color": col,
        "cells": list(comp),
        "holes": n,
        "hole_area": area,
        "bbox_h": bh,
        "bbox_w": bw,
        "bbox": _bbox(comp),
        "size": len(comp),
    }


def _is_separator(desc, h, w):
    cells = desc["cells"]
    if desc["color"] != STRIPE:
        return False
    rows = {r for r, _ in cells}
    cols = {c for _, c in cells}
    return (len(rows) == 1 and len(cells) == w) or (
        len(cols) == 1 and len(cells) == h
    )


def _is_key(desc):
    return (
        desc["color"] != GRAY
        and min(desc["bbox_h"], desc["bbox_w"]) >= 2
        and desc["size"] + desc["hole_area"]
        == desc["bbox_h"] * desc["bbox_w"]
    )


def _scene_parts(grid):
    h, w = len(grid), len(grid[0])
    scene = {"stripes": [], "keys": [], "blobs": [], "others": []}
    for col, comp in _components(grid):
        desc = _descriptor(col, comp)
        if _is_separator(desc, h, w):
            scene["stripes"].append(desc)
        elif col == GRAY:
            scene["blobs"].append(desc)
        elif _is_key(desc):
            scene["keys"].append(desc)
        else:
            scene["others"].append(desc)
    for name in ("stripes", "keys", "blobs", "others"):
        scene[name].sort(key=lambda x: (x["bbox"][0], x["bbox"][1]))
    scene["layout"] = _scene_layout(scene, h, w)
    return scene


def _scene_layout(scene, h, w):
    if len(scene["stripes"]) != 1:
        return None
    stripe = scene["stripes"][0]
    rows = {r for r, _ in stripe["cells"]}
    cols = {c for _, c in stripe["cells"]}
    if len(rows) == 1 and len(stripe["cells"]) == w:
        split = next(iter(rows))
        if all(k["bbox"][2] < split for k in scene["keys"]) and all(
            b["bbox"][0] > split for b in scene["blobs"]
        ):
            return "top"
    if len(cols) == 1 and len(stripe["cells"]) == h:
        split = next(iter(cols))
        if all(k["bbox"][3] < split for k in scene["keys"]) and all(
            b["bbox"][1] > split for b in scene["blobs"]
        ):
            return "left"
    return None


def _keymap(scene):
    out = {}
    for key in scene["keys"]:
        out.setdefault(key["holes"], key["color"])
    return out


def _paint_blob_colors(grid, scene, colors):
    out = [row[:] for row in grid]
    for blob, color in zip(scene["blobs"], colors):
        for r, c in blob["cells"]:
            out[r][c] = color
    return out


def _rival_legend_position(grid):
    """Wrong: hole count k means the k-th spatial legend key."""
    scene = _scene_parts(grid)
    keys = scene["keys"]
    return _paint_blob_colors(
        grid,
        scene,
        [keys[b["holes"]]["color"] if b["holes"] < len(keys) else 0
         for b in scene["blobs"]],
    )


def _rival_keep_unmatched_gray(grid):
    """Wrong: recolor matched blobs but leave unmatched blobs gray."""
    scene = _scene_parts(grid)
    keymap = _keymap(scene)
    return _paint_blob_colors(
        grid, scene, [keymap.get(b["holes"], GRAY) for b in scene["blobs"]]
    )


def _rival_all_gray_first_key(grid):
    """Wrong modal-color echo: every gray blob gets one legend color."""
    scene = _scene_parts(grid)
    color = scene["keys"][0]["color"] if scene["keys"] else 0
    return _paint_blob_colors(grid, scene, [color] * len(scene["blobs"]))


def _rival_bbox_area_rank(grid):
    """Wrong fixed-size proxy: rank gray bbox area instead of counting holes."""
    scene = _scene_parts(grid)
    keymap = _keymap(scene)
    areas = sorted({b["bbox_h"] * b["bbox_w"] for b in scene["blobs"]})
    rank = {area: i for i, area in enumerate(areas)}
    return _paint_blob_colors(
        grid,
        scene,
        [keymap.get(rank[b["bbox_h"] * b["bbox_w"]], 0)
         for b in scene["blobs"]],
    )


def _rival_blob_position(grid):
    """Wrong fixed-position proxy: map row-major blob index to key count."""
    scene = _scene_parts(grid)
    keymap = _keymap(scene)
    return _paint_blob_colors(
        grid, scene, [keymap.get(i, 0) for i, _ in enumerate(scene["blobs"])]
    )


def _rival_key_size_rank(grid):
    """Wrong texture proxy: infer count from filled key-cell rank."""
    scene = _scene_parts(grid)
    keys = sorted(scene["keys"], key=lambda k: (-k["size"], k["bbox"]))
    return _paint_blob_colors(
        grid,
        scene,
        [keys[b["holes"]]["color"] if b["holes"] < len(keys) else 0
         for b in scene["blobs"]],
    )


def _rival_skip_zero_hole(grid):
    """Wrong branch omission: erase unpierced gray blobs."""
    scene = _scene_parts(grid)
    keymap = _keymap(scene)
    return _paint_blob_colors(
        grid,
        scene,
        [0 if b["holes"] == 0 else keymap.get(b["holes"], 0)
         for b in scene["blobs"]],
    )


def _has_scrambled_key_order(grid):
    scene = _scene_parts(grid)
    holes = [k["holes"] for k in scene["keys"]]
    return len(holes) >= 2 and holes != sorted(holes)


def _has_unmatched_blob(grid):
    scene = _scene_parts(grid)
    keymap = _keymap(scene)
    return any(b["holes"] not in keymap for b in scene["blobs"])


def _all_key_counts_present(grid):
    scene = _scene_parts(grid)
    blob_counts = {b["holes"] for b in scene["blobs"]}
    return bool(scene["keys"]) and all(
        k["holes"] in blob_counts for k in scene["keys"]
    )


def _stripe_shares_key_color(grid):
    scene = _scene_parts(grid)
    return bool(
        len(scene["stripes"]) == 1
        and any(k["color"] == scene["stripes"][0]["color"]
                for k in scene["keys"])
    )


def _same_bbox_different_holes(grid):
    scene = _scene_parts(grid)
    groups = defaultdict(set)
    for blob in scene["blobs"]:
        groups[(blob["bbox_h"], blob["bbox_w"])].add(blob["holes"])
    return any(len(counts) >= 2 for counts in groups.values())


def _blob_order_refutes_position(grid):
    try:
        return _rival_blob_position(grid) != _apply(grid)
    except Exception:
        return False


def _key_size_proxy_refuted(grid):
    try:
        return _rival_key_size_rank(grid) != _apply(grid)
    except Exception:
        return False


def _has_zero_hole_blob(grid):
    return any(b["holes"] == 0 for b in _scene_parts(grid)["blobs"])


SEMANTIC_WITNESSES = {
    "scrambled_key_order": _has_scrambled_key_order,
    "unmatched_blob_erases": _has_unmatched_blob,
    "all_key_counts_present": _all_key_counts_present,
    "stripe_color_alias": _stripe_shares_key_color,
    "same_bbox_different_holes": _same_bbox_different_holes,
    "blob_order_scrambled": _blob_order_refutes_position,
    "key_size_proxy_refuted": _key_size_proxy_refuted,
    "zero_hole_branch": _has_zero_hole_blob,
}
SEMANTIC_RIVALS = {
    "legend_position": _rival_legend_position,
    "keep_unmatched_gray": _rival_keep_unmatched_gray,
    "all_gray_first_key": _rival_all_gray_first_key,
    "bbox_area_rank": _rival_bbox_area_rank,
    "blob_position": _rival_blob_position,
    "key_size_rank": _rival_key_size_rank,
    "skip_zero_hole": _rival_skip_zero_hole,
}
WITNESS_RIVALS = {
    "scrambled_key_order": ["legend_position"],
    "unmatched_blob_erases": ["keep_unmatched_gray"],
    "all_key_counts_present": ["all_gray_first_key"],
    "same_bbox_different_holes": ["bbox_area_rank"],
    "blob_order_scrambled": ["blob_position"],
    "key_size_proxy_refuted": ["key_size_rank"],
    "zero_hole_branch": ["skip_zero_hole"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _valid_grid(grid):
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


def strict_canonical_like(grid):
    """Return reasons when an input falls outside the teaching grammar."""
    if not _valid_grid(grid):
        return ["grid must be a nonempty rectangular ARC color grid"]
    h, w = len(grid), len(grid[0])
    reasons = []
    if not (26 <= h <= 30 and 26 <= w <= 30):
        reasons.append("grid dimensions must each be in 26..30")

    scene = _scene_parts(grid)
    if len(scene["stripes"]) != 1:
        reasons.append("input must contain exactly one full color-1 separator")
    if scene["others"]:
        reasons.append("input contains a non-key/non-blob object")
    if scene["layout"] not in ("top", "left"):
        reasons.append("separator must put every key on one side and every blob on the other")

    keys = scene["keys"]
    blobs = scene["blobs"]
    if not (2 <= len(keys) <= 4):
        reasons.append("legend must contain 2..4 rectangle keys")
    else:
        key_holes = [k["holes"] for k in keys]
        key_colors = [k["color"] for k in keys]
        if sorted(key_holes) != list(range(len(keys))):
            reasons.append("legend hole counts must be exactly 0..key_count-1")
        if len(set(key_holes)) != len(keys):
            reasons.append("legend hole counts must be unique")
        if len(set(key_colors)) != len(keys):
            reasons.append("legend key colors must be distinct")
        if STRIPE not in key_colors:
            reasons.append("one key must share color 1 with the separator")
        if key_holes == sorted(key_holes):
            reasons.append("legend spatial order must not equal hole-count order")
        if any(not (4 <= k["bbox_h"] <= 5 and 4 <= k["bbox_w"] <= 5)
               for k in keys):
            reasons.append("key bbox dimensions must each be 4..5")

        if not (len(keys) + 2 <= len(blobs) <= len(keys) + 3):
            reasons.append("field must contain key_count+2..key_count+3 gray blobs")
        blob_counts = Counter(b["holes"] for b in blobs)
        if any(n < 0 or n > len(keys) for n in blob_counts):
            reasons.append("gray blob hole counts must lie in 0..key_count")
        for n in range(len(keys) + 1):
            if blob_counts[n] == 0:
                reasons.append(f"field is missing gray hole-count branch {n}")
        if any(b["size"] + b["hole_area"]
               == b["bbox_h"] * b["bbox_w"] for b in blobs):
            reasons.append("gray blobs must be nibbled, not key-like solid rectangles")
        if any(not (5 <= b["bbox_h"] <= 6 and 5 <= b["bbox_w"] <= 6)
               for b in blobs):
            reasons.append("gray blob bbox dimensions must each be 5..6")

    if keys and blobs:
        if not _same_bbox_different_holes(grid):
            reasons.append("missing same-bbox/different-hole texture discriminator")
        if not _blob_order_refutes_position(grid):
            reasons.append("row-major blob-position rival still matches the answer")
        if not _key_size_proxy_refuted(grid):
            reasons.append("filled-key-size rival still matches the answer")
        if not _stripe_shares_key_color(grid):
            reasons.append("separator color does not alias any key color")
        canonical = _apply(grid)
        for name, rival in SEMANTIC_RIVALS.items():
            try:
                if rival(grid) == canonical:
                    reasons.append(f"named rival {name} still matches the answer")
            except Exception as exc:
                reasons.append(f"named rival {name} raised {type(exc).__name__}")
    return sorted(set(reasons))


def _mapping_signature(grid):
    scene = _scene_parts(grid)
    return tuple(sorted((k["holes"], k["color"]) for k in scene["keys"]))


def _key_order_signature(grid):
    return tuple(k["holes"] for k in _scene_parts(grid)["keys"])


def lesson_identifiable(demos, query):
    """Reject lessons compatible with any named fixed-order/size shortcut."""
    reasons = []
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"lesson needs at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict):
        return ["query must be an input/output pair"]

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
            reasons.append(f"pair {index} output is not the hole-count-key result")
    if reasons:
        return reasons

    layouts = {_scene_parts(pair["input"])["layout"] for pair in demos}
    if layouts != {"top", "left"}:
        reasons.append("training lesson must demonstrate both separator orientations")
    if len({_mapping_signature(pair["input"]) for pair in demos}) < 2:
        reasons.append("training lesson must vary the hole-count-to-color mapping")
    if len({_key_order_signature(pair["input"]) for pair in demos}) < 2:
        reasons.append("training lesson must vary the scrambled legend order")

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


def _make_key(rng, n_holes):
    """A 4..5 rectangle with exactly n non-adjacent single-cell holes."""
    for _ in range(120):
        kh = rng.randint(4, 5)
        kw = rng.randint(4, 5)
        interior = [(i, j) for i in range(1, kh - 1) for j in range(1, kw - 1)]
        rng.shuffle(interior)
        holes = []
        for cell in interior:
            if len(holes) == n_holes:
                break
            if all(abs(cell[0] - a) + abs(cell[1] - b) >= 2 for a, b in holes):
                holes.append(cell)
        if len(holes) != n_holes:
            continue
        rect = [[1] * kw for _ in range(kh)]
        for i, j in holes:
            rect[i][j] = 0
        return rect
    raise ValueError(f"cannot fit {n_holes} holes in a key")


def _make_blob(rng, n_holes, *, dims=None):
    """A connected nibbled 5..6 rectangle with exactly n enclosed holes."""
    for _ in range(180):
        bh, bw = dims or (rng.randint(5, 6), rng.randint(5, 6))
        mask = [[1] * bw for _ in range(bh)]
        boundary = sorted(set(
            [(0, j) for j in range(bw)]
            + [(bh - 1, j) for j in range(bw)]
            + [(i, 0) for i in range(bh)]
            + [(i, bw - 1) for i in range(bh)]
        ))
        rng.shuffle(boundary)
        for i, j in boundary[:rng.randint(2, 5)]:
            mask[i][j] = 0
        if not all(any(mask[0][j] for j in range(bw)) for _ in [0]):
            continue
        if not any(mask[bh - 1][j] for j in range(bw)):
            continue
        if not any(mask[i][0] for i in range(bh)):
            continue
        if not any(mask[i][bw - 1] for i in range(bh)):
            continue

        interior = [
            (i, j)
            for i in range(1, bh - 1)
            for j in range(1, bw - 1)
            if all(mask[i + di][j + dj] for di, dj in
                   ((1, 0), (-1, 0), (0, 1), (0, -1), (0, 0)))
        ]
        rng.shuffle(interior)
        holes = []
        for cell in interior:
            if len(holes) == n_holes:
                break
            if all(abs(cell[0] - a) + abs(cell[1] - b) >= 2 for a, b in holes):
                holes.append(cell)
        if len(holes) != n_holes:
            continue
        for i, j in holes:
            mask[i][j] = 0

        cells = [(i, j) for i in range(bh) for j in range(bw) if mask[i][j]]
        if not cells:
            continue
        cellset = set(cells)
        reached = {cells[0]}
        q = deque([cells[0]])
        while q:
            x, y = q.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nb = (x + dx, y + dy)
                if nb in cellset and nb not in reached:
                    reached.add(nb)
                    q.append(nb)
        if len(reached) != len(cells):
            continue
        n, area, ch, cw = _hole_stats(cells)
        if n != n_holes or (ch, cw) != (bh, bw):
            continue
        if len(cells) + area == ch * cw:
            continue
        return [[GRAY if mask[i][j] else 0 for j in range(bw)]
                for i in range(bh)]
    raise ValueError(f"cannot build a blob with {n_holes} holes")


def _stamp(g, sub, r0, c0):
    for i, row in enumerate(sub):
        for j, value in enumerate(row):
            if value:
                g[r0 + i][c0 + j] = value


def _fits(g, sub, r0, c0):
    """Require one-cell clearance against every existing non-zero cell."""
    h, w = len(g), len(g[0])
    if r0 < 0 or c0 < 0 or r0 + len(sub) > h or c0 + len(sub[0]) > w:
        return False
    for i in range(-1, len(sub) + 1):
        for j in range(-1, len(sub[0]) + 1):
            r, c = r0 + i, c0 + j
            if 0 <= r < h and 0 <= c < w and g[r][c] != 0:
                return False
    return True


def _place_in_field(g, sub, field, rng):
    fr, fc, fh, fw = field
    candidates = [
        (r, c)
        for r in range(fr, fh - len(sub) + 1)
        for c in range(fc, fw - len(sub[0]) + 1)
    ]
    rng.shuffle(candidates)
    for r0, c0 in candidates:
        if _fits(g, sub, r0, c0):
            _stamp(g, sub, r0, c0)
            return True
    return False


def _grid_bounds(difficulty, rng):
    if difficulty == "easy":
        return rng.randint(26, 28), rng.randint(26, 28)
    if difficulty == "medium":
        return rng.randint(28, 30), rng.randint(28, 30)
    return 30, 30


def _build_pair(rng, difficulty, *, layout, n_keys, variant):
    for _scene_attempt in range(180):
        h, w = _grid_bounds(difficulty, rng)
        g = [[0] * w for _ in range(h)]

        colors = rng.sample([2, 3, 4, 6, 7, 8, 9], n_keys - 1)
        rng.shuffle(colors)
        colors.insert(variant % n_keys, STRIPE)
        key_specs = [(holes, colors[holes], _make_key(rng, holes))
                     for holes in range(n_keys)]
        order_templates = [
            list(reversed(range(n_keys))),
            list(range(1, n_keys)) + [0],
        ]
        spatial_order = order_templates[variant % len(order_templates)]
        ordered = [key_specs[i] for i in spatial_order]

        if layout == "top":
            total = sum(len(key[2][0]) for key in ordered) + 2 * (n_keys - 1)
            if total > w - 2:
                continue
            slack = w - total
            c0 = rng.randint(1, max(1, slack - 1))
            for _, color, key in ordered:
                _stamp(g, [[color if value else 0 for value in row] for row in key], 1, c0)
                c0 += len(key[0]) + 2
            separator = max(len(key[2]) for key in ordered) + 2
            for c in range(w):
                g[separator][c] = STRIPE
            field = (separator + 2, 0, h, w)
        else:
            total = sum(len(key[2]) for key in ordered) + 2 * (n_keys - 1)
            if total > h - 2:
                continue
            slack = h - total
            r0 = rng.randint(1, max(1, slack - 1))
            for _, color, key in ordered:
                _stamp(g, [[color if value else 0 for value in row] for row in key], r0, 1)
                r0 += len(key) + 2
            separator = max(len(key[2][0]) for key in ordered) + 2
            for r in range(h):
                g[r][separator] = STRIPE
            field = (0, separator + 2, h, w)

        counts = list(range(n_keys + 1))
        counts += [rng.randint(0, n_keys) for _ in range(rng.randint(1, 2))]
        rng.shuffle(counts)
        forced = {0: False, 1: False}
        blobs = []
        try:
            for count in counts:
                dims = None
                if count in forced and not forced[count]:
                    dims = (6, 6)
                    forced[count] = True
                blobs.append((count, _make_blob(rng, count, dims=dims)))
        except ValueError:
            continue
        rng.shuffle(blobs)
        if any(not _place_in_field(g, blob, field, rng) for _, blob in blobs):
            continue

        if strict_canonical_like(g):
            continue
        return g, _apply(g)
    raise ValueError("could not build a shortcut-refuting hole-count-key pair")


def _n_keys_for(difficulty, offset, index):
    if difficulty == "easy":
        return 2 + ((offset + index) % 2)
    if difficulty == "medium":
        return 3 + ((offset + index) % 2)
    return 4


def generate_task(seed, *, difficulty="medium"):
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty: {difficulty!r}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=0,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
    )
    n_train = ctx.draw_int("n_train", 3, 4)
    n_test = ctx.draw_int("n_test", 1, 2)
    plan_rng = ctx.draw_rng("lesson_plan")
    key_offset = plan_rng.randint(0, 1)
    layouts = ["top", "left"]
    layouts += [plan_rng.choice(("top", "left"))
                for _ in range(n_train + n_test - 2)]

    pairs = []
    for index in range(n_train + n_test):
        rng = ctx.draw_rng(f"pair_{index}")
        n_keys = _n_keys_for(difficulty, key_offset, index)
        gin, gout = _build_pair(
            rng, difficulty, layout=layouts[index], n_keys=n_keys,
            variant=index,
        )
        pairs.append({"input": gin, "output": gout})

    task = {
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "program": PROGRAM,
        "concept": "hole_count_key",
        "difficulty": difficulty,
        "meta": {
            "version": VERSION,
            "difficulty": difficulty,
            "rule_hash": RULE_HASH,
            "lesson_plan": "both-layouts-plus-named-rival-counterexamples",
        },
    }
    errors = self_check_task(task)
    if errors:
        raise AssertionError(f"generated task failed self_check_task: {errors[:3]}")
    return task


def self_check_task(task):
    """Structural, semantic, lesson, and mutation-sensitive whole-task checks."""
    if not isinstance(task, dict):
        return ["task must be a dictionary"]
    errors = []
    difficulty = task.get("difficulty")
    if difficulty not in ("easy", "medium", "hard"):
        errors.append("task difficulty must be easy, medium, or hard")
    train = list(task.get("train") or [])
    test = list(task.get("test") or [])
    if not (3 <= len(train) <= 4):
        errors.append("task must contain 3..4 training pairs")
    if not (1 <= len(test) <= 2):
        errors.append("task must contain 1..2 test pairs")
    if task.get("program") != PROGRAM:
        errors.append("task program is not the selected hole-count-key authority")
    if task.get("concept") != "hole_count_key":
        errors.append("task concept must be hole_count_key")
    meta = task.get("meta") or {}
    if meta.get("version") != VERSION:
        errors.append("meta.version is stale")
    if meta.get("difficulty") != difficulty:
        errors.append("meta.difficulty disagrees with task difficulty")
    if meta.get("rule_hash") != RULE_HASH:
        errors.append("meta.rule_hash does not match normalized PROGRAM")

    seen_inputs = set()
    for split_name, pairs in (("train", train), ("test", test)):
        for index, pair in enumerate(pairs):
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
            for reason in strict_canonical_like(gin):
                errors.append(f"{label}: {reason}")
            expected = _apply(gin)
            if expected != gout:
                errors.append(f"{label}: output is not exact hole-count-key recoloring")
                continue
            if any(
                gin[r][c] != GRAY and gout[r][c] != gin[r][c]
                for r in range(len(gin))
                for c in range(len(gin[0]))
            ):
                errors.append(f"{label}: non-gray legend/stripe/background changed")
            if any(value == GRAY for row in gout for value in row):
                errors.append(f"{label}: output leaves gray blob cells unresolved")
            scene = _scene_parts(gin)
            out_colors = {value for row in gout for value in row}
            for key in scene["keys"]:
                if key["color"] not in out_colors:
                    errors.append(f"{label}: key color {key['color']} is not exercised")

    if train:
        layouts = {_scene_parts(pair["input"])["layout"] for pair in train
                   if isinstance(pair, dict) and _valid_grid(pair.get("input"))}
        if layouts != {"top", "left"}:
            errors.append("train split must demonstrate both top and left legends")
        mappings = {_mapping_signature(pair["input"]) for pair in train
                    if isinstance(pair, dict) and _valid_grid(pair.get("input"))}
        if len(mappings) < 2:
            errors.append("train split must vary the hole-count-to-color mapping")
        orders = {_key_order_signature(pair["input"]) for pair in train
                  if isinstance(pair, dict) and _valid_grid(pair.get("input"))}
        if len(orders) < 2:
            errors.append("train split must vary the scrambled key order")
    for index, query in enumerate(test):
        for reason in lesson_identifiable(train, query):
            errors.append(f"test[{index}] lesson not identifiable: {reason}")
    return sorted(set(errors))


if __name__ == "__main__":
    from puzzle_generators.generic.concepts.hole_count_key import parity_check

    parity_check(generate_task, n=25,
                 version_label=f"hole_count_key gen1 v{VERSION}")
