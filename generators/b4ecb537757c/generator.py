"""Keyed rotations into matching frames; labels stay with the Racket authority.

The sampler constructs complete scenes and checks the *rotated* insert extent.
Canonical inputs also contain ignored fragments from overwritten rectangles;
those are accepted by the operational validator, but are not generated here.
"""
from __future__ import annotations

from functools import partial
from itertools import product

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b4ecb537757c"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "1232696ab606"
SUMMARY = (
    "Match each intact monochrome frame to its external same-color insert. "
    "An isolated interior key selects identity (1), clockwise (2), half-turn "
    "(3), or counterclockwise (4). The unchanged reference clears the input, "
    "retains complete frames, and pastes transformed insert subgrids at each "
    "frame's interior top left. Generated transformed inserts fit completely. "
    "One-frame 7x12 three-color scenes alternate with varied multi-frame scenes."
)
INVARIANTS = [
    "rectangular integer grid with colors 0..9 and black background",
    "one to four distinct-color intact monochrome cardinal-connected frames with disjoint rectangles",
    "each surviving frame has one isolated key of color 1..4 and one matching insert",
    "matching inserts have no foreign cells in their bounding boxes",
    "the selected rotation fits inside its matching frame without overwriting a border",
    "normal draws use external inserts, separated frames, and independently varied roles",
]
AXES = {
    "grid_h": {"type": "int", "default": "7 in compact scenes; varied 7..22 otherwise", "valid": "7..22"},
    "grid_w": {"type": "int", "default": "12 in compact scenes; varied 12..24 otherwise", "valid": "12..24"},
    "n_frames": {"type": "int", "default": "1 in compact scenes; 2..4 when space permits", "valid": "1..4"},
}
# Geometry refusals identify the actual explicit axes on their ValueError.
# An empty list deliberately opts out of the checker's legacy blanket acceptance.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 7
LESSON_SCHEDULE_PERIOD = 8
SCHEDULE_PROFILES = tuple(f"{mode}/key{key}" for mode in ("compact", "varied") for key in range(1, 5))
MIN_STRICT_FRAC = 1.0


def schedule_profile(seed, sample_index, difficulty=None):
    return f"{'compact' if sample_index % 8 < 4 else 'varied'}/key{sample_index % 4 + 1}"


def _bbox(cells):
    return (min(r for r, _ in cells), min(c for _, c in cells),
            max(r for r, _ in cells), max(c for _, c in cells))


def _components(grid):
    """Same-color four-neighbor components, in row-major discovery order."""
    h, w = len(grid), len(grid[0])
    seen, components = set(), []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if not color or (r, c) in seen:
                continue
            pending, cells = [(r, c)], []
            seen.add((r, c))
            while pending:
                rr, cc = pending.pop()
                cells.append((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        pending.append((nr, nc))
            components.append({"color": color, "cells": cells, "bbox": _bbox(cells)})
    return components


def _is_frame(obj):
    r0, c0, r1, c1 = obj["bbox"]
    if r1 - r0 < 2 or c1 - c0 < 2:
        return False
    border = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
              if r in (r0, r1) or c in (c0, c1)}
    return set(obj["cells"]) == border


def _inside(r, c, bbox):
    r0, c0, r1, c1 = bbox
    return r0 < r < r1 and c0 < c < c1


def _subgrid(grid, bbox):
    r0, c0, r1, c1 = bbox
    return [list(row[c0:c1 + 1]) for row in grid[r0:r1 + 1]]


def _turn(shape, key):
    out = [list(row) for row in shape]
    for _ in range(key - 1):
        out = [list(row) for row in zip(*out[::-1])]
    return out


def _scene(grid):
    components = _components(grid)
    frames = [obj for obj in components if _is_frame(obj)]
    inserts = [obj for obj in components if len(obj["cells"]) > 1 and not _is_frame(obj)]
    singles = [obj for obj in components if len(obj["cells"]) == 1 and obj["color"] in (1, 2, 3, 4)]
    errors, scene = [], []
    if not 1 <= len(frames) <= 4:
        errors.append(f"expected 1..4 complete frames; found {len(frames)}")
    if len({obj["color"] for obj in frames}) != len(frames):
        errors.append("complete frame colors must be distinct")
    for i, first in enumerate(frames):
        r0, c0, r1, c1 = first["bbox"]
        for second in frames[i + 1:]:
            s0, t0, s1, t1 = second["bbox"]
            if max(r0, s0) <= min(r1, s1) and max(c0, t0) <= min(c1, t1):
                errors.append("complete frame rectangles must be disjoint; nested frames can overwrite each other")
    for frame in frames:
        color = frame["color"]
        candidates = [obj for obj in inserts if obj["color"] == color]
        keys = [obj for obj in singles if _inside(*obj["cells"][0], frame["bbox"])]
        if len(candidates) != 1:
            errors.append(f"frame color {color}: expected one matching insert, found {len(candidates)}")
        if len(keys) != 1:
            errors.append(f"frame color {color}: expected one isolated key, found {len(keys)}")
        if len(candidates) != 1 or len(keys) != 1:
            continue
        insert, key = candidates[0], keys[0]["color"]
        raw = _subgrid(grid, insert["bbox"])
        if any(v not in (0, color) for row in raw for v in row):
            errors.append(f"frame color {color}: insert bounding box contains foreign cells")
        if any(_inside(r, c, fr["bbox"]) for r, c in insert["cells"] for fr in frames):
            errors.append(f"frame color {color}: matching insert must be outside complete frames")
        ih, iw = frame["bbox"][2] - frame["bbox"][0] - 1, frame["bbox"][3] - frame["bbox"][1] - 1
        sh, sw = len(raw), len(raw[0])
        th, tw = (sw, sh) if key in (2, 4) else (sh, sw)
        if th > ih or tw > iw:
            errors.append(f"frame color {color}: key {key} transforms {sh}x{sw} to {th}x{tw}, outside {ih}x{iw} interior")
        scene.append({"frame": frame, "insert": insert, "key": key, "shape": raw})
    # Isolated non-key noise has no role; canonical orphan keys and multi-cell
    # overwritten-frame fragments remain legal and are ignored by the authority.
    if any(len(obj["cells"]) == 1 and obj["color"] not in (1, 2, 3, 4) for obj in components):
        errors.append("unexplained singleton outside the key palette")
    return scene, errors


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"]
    if any(not isinstance(row, (list, tuple)) or not row for row in grid):
        return ["rows must be nonempty sequences"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    if len(grid) > 30 or len(grid[0]) > 30:
        return ["grid dimensions exceed 30"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["cells must be integer colors 0..9; booleans are not colors"]
    if not any(v == 0 for row in grid for v in row):
        return ["black background is required"]
    return _scene(grid)[1]


def strict_canonical_like(grid):
    """Operational task domain, including the canonical ignored fragments."""
    return self_check(grid)


def observe_overrides(grid):
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "n_frames": sum(_is_frame(obj) for obj in _components(grid))}


def _capacity(h, w):
    # Each pocket has a 5x5 frame and a separate 3x3 insert region. One blank
    # row/column separates pockets; whole-canvas reflections vary their side.
    return min(4, ((h + 1) // 6) * ((w + 1) // 10))


def _incompatible(overrides):
    exc = ValueError("incompatible grid_h/grid_w/n_frames: canvas cannot fit the declared separated pockets")
    exc.incompatible_axes = tuple(name for name, value in overrides.items() if value is not None)
    raise exc


# Nonrectangular, connected shapes with four distinct orientations. This keeps
# every scheduled key informative; symmetric canonical motifs remain accepted.
_MOTIFS = (
    ((0, 0), (1, 0), (1, 1)),
    ((0, 0), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 1)),
    ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (2, 0), (2, 1)),
)


def _motif_options(key, fh, fw):
    options = []
    for cells in _MOTIFS:
        h, w = max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1
        raw = full_grid(h, w, 0)
        for r, c in cells:
            raw[r][c] = 1
        for initial_key in (1, 2, 3, 4):
            shape = _turn(raw, initial_key)
            transformed = _turn(shape, key)
            if len(transformed) <= fh - 2 and len(transformed[0]) <= fw - 2:
                options.append(shape)
    return options


def _draw_frame(g, r0, c0, fh, fw, color):
    for r in range(r0, r0 + fh):
        for c in range(c0, c0 + fw):
            if r in (r0, r0 + fh - 1) or c in (c0, c0 + fw - 1):
                g[r][c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise ValueError("seed must be an integer; booleans and coercions are invalid")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty is not None and (type(difficulty) is not str or difficulty not in ("easy", "medium", "hard")):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        lo, hi = {"grid_h": (7, 22), "grid_w": (12, 24), "n_frames": (1, 4)}[name]
        if value is not None and (type(value) is not int or not lo <= value <= hi):
            raise ValueError(f"{name} must be an integer in [{lo}, {hi}]")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    compact = sample_index % 8 < 4
    eh, ew = overrides.get("grid_h"), overrides.get("grid_w")
    counts = [n for n in range(1, 5) if _capacity(eh or 22, ew or 24) >= n]
    if not counts or (overrides.get("n_frames") is not None and overrides["n_frames"] not in counts):
        _incompatible(overrides)
    default_counts = [1] if compact else [n for n in counts if n >= 2] or [1]
    n = ctx.draw_choice("n_frames", counts if overrides.get("n_frames") is not None else default_counts)
    heights = [h for h in range(7, 23) if _capacity(h, ew or 24) >= n]
    if eh is not None and eh not in heights:
        _incompatible(overrides)
    if compact and n == 1 and eh is None:
        h_options = [7]
    else:
        preferred = (range(11, 16) if difficulty == "easy" else
                     range(17, 23) if difficulty == "hard" else range(13, 20))
        h_options = heights + [h for h in heights if h in preferred] * 3
    h = ctx.draw_choice("grid_h", heights if eh is not None else h_options)
    widths = [w for w in range(12, 25) if _capacity(h, w) >= n]
    if ew is not None and ew not in widths:
        _incompatible(overrides)
    w_options = [12] if compact and n == 1 and ew is None else widths
    w = ctx.draw_choice("grid_w", widths if ew is not None else w_options)
    rng = ctx.draw_rng("layout")
    # Select separated pockets before drawing: no capped random packing and no
    # fixed fallback that silently changes requested dimensions/counts.
    slots = [(6 * r, 10 * c) for r in range((h + 1) // 6) for c in range((w + 1) // 10)]
    selected = sorted(rng.sample(slots, n))
    max_r, max_c = max(r for r, _ in selected) + 5, max(c for _, c in selected) + 9
    dr, dc = rng.randint(0, h - max_r), rng.randint(0, w - max_c)
    selected = [(r + dr, c + dc) for r, c in selected]
    first = sample_index % 4 + 1
    keys = [first] + [rng.choice((1, 2, 3, 4)) for _ in range(n - 1)]
    # Two varied-scene anchors per eight draws distinguish reading every key
    # from inferring keys from spatial rank. Any single holdout leaves one.
    # Opposite pairs, or nonuniform tuples with repetitions, refute uniform
    # keys and either +/-1 progression under every ordering/reflection.
    # The other varied residues retain independently sampled key tuples.
    if n > 1 and sample_index % 8 in (4, 6):
        choices = []
        for tail in product((1, 2, 3, 4), repeat=n - 1):
            candidate = (first,) + tail
            if ((n == 2 and (candidate[1] - first) % 4 == 2) or
                    (n > 2 and 1 < len(set(candidate)) < n)):
                choices.append(candidate)
        keys = list(rng.choice(choices))
    # A random bijection between roles and colors; keys retain their fixed code.
    available, colors = list(range(1, 10)), []
    for key in keys:
        color = rng.choice([c for c in available if c != key])
        colors.append(color)
        available.remove(color)
    g, shapes = full_grid(h, w, 0), []
    transformed_seen = set()
    for (r0, c0), key, color in zip(selected, keys, colors):
        fh, fw = rng.choice((4, 5)), rng.choice((4, 5))
        # The pocket leaves enough space for either orientation and random slack.
        fr, fc = r0 + rng.randint(0, 5 - fh), c0 + rng.randint(0, 5 - fw)
        _draw_frame(g, fr, fc, fh, fw, color)
        g[rng.randint(fr + 1, fr + fh - 2)][rng.randint(fc + 1, fc + fw - 2)] = key
        options = _motif_options(key, fh, fw)
        novel = [s for s in options if tuple(map(tuple, _turn(s, key))) not in transformed_seen]
        shape = rng.choice(novel or options)
        transformed_seen.add(tuple(map(tuple, _turn(shape, key))))
        shapes.append(shape)
    # A nonzero cyclic offset always breaks the pocket/color correspondence for
    # multi-frame scenes. Color matching, rather than nearest-row association,
    # is needed; jitter and whole-grid reflections vary absolute placement.
    shift = rng.randint(1, n - 1) if n > 1 else 0
    for i, (shape, color) in enumerate(zip(shapes, colors)):
        r0, c0 = selected[(i + shift) % n]
        ir, ic = r0 + rng.randint(0, 5 - len(shape)), c0 + 6 + rng.randint(0, 3 - len(shape[0]))
        for r, row in enumerate(shape):
            for c, value in enumerate(row):
                if value:
                    g[ir + r][ic + c] = color
    if rng.choice((False, True)):
        g.reverse()
    if rng.choice((False, True)):
        g = [row[::-1] for row in g]
    return g


def _rival(grid, *, key_mapping=None, color_keys=False, first_key=False, rank_match=False, rank_key_step=None):
    """Diagnostic predictions only; never used as training labels."""
    scene, errors = _scene(grid)
    if errors:
        raise ValueError("rival outside declared domain: " + "; ".join(errors))
    out = full_grid(len(grid), len(grid[0]), 0)
    for item in scene:
        frame = item["frame"]
        for r, c in frame["cells"]:
            out[r][c] = frame["color"]
    by_rank = sorted(scene, key=lambda item: item["insert"]["bbox"][:2])
    lookup = {3: 4, 4: 1, 6: 3, 7: 3, 8: 2}
    for index, item in enumerate(scene):
        frame, key = item["frame"], item["key"]
        if color_keys:
            key = lookup.get(frame["color"], 1)
        elif first_key:
            key = scene[0]["key"]
        elif rank_key_step is not None:
            key = (scene[0]["key"] - 1 + rank_key_step * index) % 4 + 1
        elif key_mapping is not None:
            key = key_mapping[key - 1]
        shape = _turn(by_rank[index]["shape"] if rank_match else item["shape"], key)
        r0, c0 = frame["bbox"][:2]
        for r, row in enumerate(shape):
            for c, value in enumerate(row):
                rr, cc = r0 + 1 + r, c0 + 1 + c
                if value and 0 <= rr < len(out) and 0 <= cc < len(out[0]):
                    out[rr][cc] = frame["color"] if rank_match else value
    return out


def _has_key(grid, key):
    scene, errors = _scene(grid)
    return not errors and any(item["key"] == key and
        len({tuple(map(tuple, _turn(item["shape"], k))) for k in (1, 2, 3, 4)}) == 4
        for item in scene)


def _rival_disagrees(grid, rival):
    return rival(grid) != _rival(grid)


SEMANTIC_RIVALS = {}
SEMANTIC_WITNESSES = {}
WITNESS_RIVALS = {}
for _key in (1, 2, 3, 4):
    _names = []
    for _wrong in (1, 2, 3, 4):
        if _key == _wrong:
            continue
        _mapping = [1, 2, 3, 4]
        _mapping[_key - 1] = _wrong
        _name = f"key{_key}_as{_wrong}"
        SEMANTIC_RIVALS[_name] = partial(_rival, key_mapping=tuple(_mapping))
        _names.append(_name)
    SEMANTIC_WITNESSES[f"key{_key}_asymmetric"] = partial(_has_key, key=_key)
    WITNESS_RIVALS[f"key{_key}_asymmetric"] = _names
SEMANTIC_RIVALS.update({
    "frame_color_lookup": partial(_rival, color_keys=True),
    "first_key_for_all": partial(_rival, first_key=True),
    "rank_match": partial(_rival, rank_match=True),
    "rank_key_decrement": partial(_rival, rank_key_step=-1),
    "rank_key_increment": partial(_rival, rank_key_step=1),
})
for _name in ("frame_color_lookup", "first_key_for_all", "rank_match", "rank_key_decrement", "rank_key_increment"):
    SEMANTIC_WITNESSES[f"refute_{_name}"] = partial(_rival_disagrees, rival=SEMANTIC_RIVALS[_name])
    WITNESS_RIVALS[f"refute_{_name}"] = [_name]
CANONICAL_SHORTCUTS = {name: SEMANTIC_RIVALS[name] for name in ("frame_color_lookup", "rank_key_decrement")}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Require visible asymmetric support for every queried key and named rivals.

    Seven demos plus one query contain every key twice in the default eight-draw
    schedule. Arbitrary holdout of those eight leaves at least one witness per
    key. Two varied-scene anchors refute uniform and cyclic spatial key rules;
    any holdout leaves one anchor. Named rival scoring additionally checks
    accidental layout correlations.
    This is finite declared-hypothesis coverage, not universal uniqueness.
    """
    if any(self_check(pair["input"]) for pair in demos) or self_check(query["input"]):
        return ["lesson contains an input outside the operational domain"]
    keys = {item["key"] for item in _scene(query["input"])[0]}
    errors = [f"query key {key} lacks an asymmetric demonstration"
              for key in sorted(keys) if not any(_has_key(pair["input"], key) for pair in demos)]
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos) and rival(query["input"]) != query["output"]:
            errors.append(f"unrefuted query-diverging rival: {name}")
    return errors
