"""Generator for 4b:m23 — connect aligned pairs.

Rule: for each nonzero color that occurs exactly twice, fill the inclusive
straight segment between the two cells when they share a row or a column.
Colors that are singletons, diagonal pairs, or triples stay unchanged.

The ordinary curriculum makes every returned board non-trivial and keeps
connectable spans disjoint.  A four-sample schedule covers horizontal,
vertical, mixed-orientation, short-span, long-span, edge-anchored, and
interior-only examples while randomized placement preserves high variation.
Unchanged distractors rebut count-only, connect-every-duplicate, and
marker-as-answer shortcuts.
"""
from __future__ import annotations

from collections import defaultdict
from functools import lru_cache

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "17c625cd9cdd"
TASK_ID = "17c625cd9cdd"
VERSION = "2.0.0"
RULE_HASH = "f01970251592"
SUMMARY = (
    "Fill the straight segment for every color occurring exactly twice on "
    "one row or one column; leave singleton, diagonal-pair, and triple "
    "distractor colors unchanged."
)
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0 and strictly more cells are background than nonzero",
    "1..4 connectable colors each occur exactly twice, are row/column aligned, "
    "and have at least one blank cell between their endpoints",
    "connectable spans are pairwise disjoint and contain no foreign marker",
    "0..3 distractor colors are singletons, diagonal pairs, or triples and "
    "therefore remain unchanged under the Racket oracle",
    "ordinary sample_index blocks of four cover both orientations and both "
    "short/long span classes",
]

ORIENTATIONS = ("horizontal", "vertical", "mixed")
SPAN_CLASSES = ("short", "long", "mixed")
PALETTE_KINDS = ("lower", "upper", "spread")
AXES = {
    "grid_h": {"type": "int", "default": "band schedule/rng", "valid": "6..14"},
    "grid_w": {"type": "int", "default": "band schedule/rng", "valid": "6..14"},
    "n_pairs": {"type": "int", "default": "2..4 by band/sample", "valid": "1..4"},
    "n_distractors": {"type": "int", "default": "0..3 by band/sample", "valid": "0..3"},
    "orientation": {"type": "str", "default": "four-sample schedule", "valid": "|".join(ORIENTATIONS)},
    "span_class": {"type": "str", "default": "four-sample schedule", "valid": "|".join(SPAN_CLASSES)},
    "palette_kind": {"type": "str", "default": "four-sample schedule", "valid": "|".join(PALETTE_KINDS)},
    "edge_anchor": {"type": "bool", "default": "alternates by sample", "valid": "true|false"},
}

_VALID_H = (6, 14)
_VALID_W = (6, 14)
_DISTRACTOR_KINDS = ("singleton", "diagonal_pair", "triple")


def _positions_by_color(grid):
    pos = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                pos[value].append((r, c))
    return dict(pos)


def _target_info(grid):
    """Return connectable colors as (color, orientation, span_len, cells, segment)."""
    out = []
    for color, cells in sorted(_positions_by_color(grid).items()):
        if len(cells) != 2:
            continue
        a, b = cells
        if a[0] == b[0]:
            span_len = abs(a[1] - b[1]) + 1
            if span_len < 3:
                continue
            segment = frozenset((a[0], c) for c in range(min(a[1], b[1]), max(a[1], b[1]) + 1))
            out.append((color, "horizontal", span_len, tuple(cells), segment))
        elif a[1] == b[1]:
            span_len = abs(a[0] - b[0]) + 1
            if span_len < 3:
                continue
            segment = frozenset((r, a[1]) for r in range(min(a[0], b[0]), max(a[0], b[0]) + 1))
            out.append((color, "vertical", span_len, tuple(cells), segment))
    return out


def _mirror(grid):
    """Python mirror of the canonical rule, used only for structural tests."""
    out = [row[:] for row in grid]
    for color, cells in sorted(_positions_by_color(grid).items()):
        if len(cells) != 2:
            continue
        a, b = cells
        if a[0] == b[0]:
            for c in range(min(a[1], b[1]), max(a[1], b[1]) + 1):
                out[a[0]][c] = color
        elif a[1] == b[1]:
            for r in range(min(a[0], b[0]), max(a[0], b[0]) + 1):
                out[r][a[1]] = color
    return out


def observe_overrides(grid) -> dict:
    """Recover every exact semantic axis from the returned grid."""
    h, w = len(grid), len(grid[0])
    positions = _positions_by_color(grid)
    targets = _target_info(grid)
    target_colors = {item[0] for item in targets}
    orientations = {item[1] for item in targets}
    lengths = {"short" if item[2] <= 4 else "long" for item in targets}
    colors = set(positions)
    if 1 in colors and 9 in colors:
        palette_kind = "spread"
    elif 1 in colors:
        palette_kind = "lower"
    elif 9 in colors:
        palette_kind = "upper"
    else:
        palette_kind = "unmarked"
    return {
        "n_pairs": len(targets),
        "n_distractors": len(set(positions) - target_colors),
        "orientation": (
            "mixed" if orientations == {"horizontal", "vertical"}
            else next(iter(orientations)) if len(orientations) == 1
            else "none"
        ),
        "span_class": (
            "mixed" if lengths == {"short", "long"}
            else next(iter(lengths)) if len(lengths) == 1
            else "none"
        ),
        "palette_kind": palette_kind,
        "edge_anchor": any(
            r in (0, h - 1) or c in (0, w - 1)
            for _, _, _, cells, _ in targets
            for r, c in cells
        ),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or rule-hiding lessons; accept every canonical input."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    h = len(grid)
    errors = []
    if not (_VALID_H[0] <= h <= _VALID_H[1] and _VALID_W[0] <= w <= _VALID_W[1]):
        errors.append(f"dims {h}x{w} outside 6..14 x 6..14")
    if any(
        not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        errors.append("colors must be integer ARC colors 0..9")
        return errors

    positions = _positions_by_color(grid)
    targets = _target_info(grid)
    target_colors = {item[0] for item in targets}
    if not (1 <= len(targets) <= 4):
        errors.append(f"expected 1..4 connectable colors, found {len(targets)}")

    nonzero_count = sum(value != 0 for row in grid for value in row)
    if nonzero_count >= h * w - nonzero_count:
        errors.append("background 0 is not strictly modal")

    target_segments = [item[4] for item in targets]
    for i, first in enumerate(target_segments):
        for second in target_segments[:i]:
            if first & second:
                errors.append("connectable spans overlap")
                break

    occupied = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0}
    for color, _, _, cells, segment in targets:
        foreign = (set(segment) - set(cells)) & occupied
        if foreign:
            errors.append(f"color {color} span contains foreign marker(s): {sorted(foreign)}")

    distractor_count = 0
    for color, cells in sorted(positions.items()):
        if color in target_colors:
            continue
        distractor_count += 1
        if len(cells) == 1 or len(cells) == 3:
            continue
        if len(cells) == 2:
            a, b = cells
            if a[0] != b[0] and a[1] != b[1]:
                continue
            errors.append(f"color {color} is an adjacent/aligned pair with no meaningful interior")
        else:
            errors.append(f"color {color} appears {len(cells)} times; allowed distractors have 1, 2 diagonal, or 3 cells")
    if distractor_count > 3:
        errors.append(f"{distractor_count} distractor colors (> 3)")

    if _mirror(grid) == grid:
        errors.append("oracle is identity: no meaningful aligned pair fires")
    return errors


def _pair_specs(n_pairs, orientation, span_class):
    if n_pairs == 1 and orientation == "mixed":
        raise ValueError("orientation=mixed requires n_pairs>=2")
    if n_pairs == 1 and span_class == "mixed":
        raise ValueError("span_class=mixed requires n_pairs>=2")
    if orientation == "mixed":
        orientations = ["horizontal", "vertical"] + ["horizontal" if i % 2 == 0 else "vertical" for i in range(n_pairs - 2)]
    else:
        orientations = [orientation] * n_pairs
    if span_class == "mixed":
        spans = ["short", "long"] + ["short" if i % 2 == 0 else "long" for i in range(n_pairs - 2)]
    else:
        spans = [span_class] * n_pairs
    return list(zip(orientations, spans))


@lru_cache(maxsize=None)
def _segment_candidates(h, w, orientation, span_class, anchor_mode):
    candidates = []
    if orientation == "horizontal":
        lengths = range(3, min(4, w) + 1) if span_class == "short" else range(5, w + 1)
        for length in lengths:
            for r in range(h):
                for c0 in range(w - length + 1):
                    ends = ((r, c0), (r, c0 + length - 1))
                    anchored = any(rr in (0, h - 1) or cc in (0, w - 1) for rr, cc in ends)
                    if anchor_mode == "required" and not anchored:
                        continue
                    if anchor_mode == "forbidden" and anchored:
                        continue
                    segment = frozenset((r, c) for c in range(c0, c0 + length))
                    candidates.append((ends, segment))
    else:
        lengths = range(3, min(4, h) + 1) if span_class == "short" else range(5, h + 1)
        for length in lengths:
            for c in range(w):
                for r0 in range(h - length + 1):
                    ends = ((r0, c), (r0 + length - 1, c))
                    anchored = any(rr in (0, h - 1) or cc in (0, w - 1) for rr, cc in ends)
                    if anchor_mode == "required" and not anchored:
                        continue
                    if anchor_mode == "forbidden" and anchored:
                        continue
                    segment = frozenset((r, c) for r in range(r0, r0 + length))
                    candidates.append((ends, segment))
    return candidates


def _place_pairs(rng, h, w, specs, edge_anchor):
    entries = []
    for index, (orientation, span_class) in enumerate(specs):
        mode = "required" if edge_anchor and index == 0 else "forbidden" if not edge_anchor else "optional"
        candidates = list(_segment_candidates(h, w, orientation, span_class, mode))
        rng.shuffle(candidates)
        if not candidates:
            return None
        entries.append((index, candidates))
    entries.sort(key=lambda item: len(item[1]))
    chosen = {}

    def search(depth, used):
        if depth == len(entries):
            return True
        index, candidates = entries[depth]
        for ends, segment in candidates:
            if segment & used:
                continue
            chosen[index] = (ends, segment)
            if search(depth + 1, used | set(segment)):
                return True
            chosen.pop(index, None)
        return False

    if not search(0, set()):
        return None
    return [chosen[i] for i in range(len(specs))]


def _palette(rng, kind, total):
    if total < 1 or total > 8:
        raise ValueError(f"need 1..8 distinct nonzero colors, got {total}")
    middle = list(range(2, 9))
    if kind == "lower":
        colors = [1] + rng.sample(middle, total - 1)
    elif kind == "upper":
        colors = [9] + rng.sample(middle, total - 1)
    else:
        if total < 2:
            raise ValueError("palette_kind=spread requires at least two colors")
        colors = [1, 9] + rng.sample(middle, total - 2)
    rng.shuffle(colors)
    return colors


def _place_distractors(rng, h, w, kinds, forbidden):
    """Fast randomized placement outside every target segment.

    The grid is sparse and there are at most three groups, so bounded retries
    are both faster and easier to audit than enumerating O((hw)^2) pair sets.
    """
    all_cells = [(r, c) for r in range(h) for c in range(w)]
    for _attempt in range(80):
        used = set(forbidden)
        chosen = []
        ok = True
        for kind in kinds:
            free = [cell for cell in all_cells if cell not in used]
            cells = None
            if kind == "singleton" and free:
                cells = frozenset((rng.choice(free),))
            elif kind == "diagonal_pair" and len(free) >= 2:
                for _ in range(80):
                    a, b = rng.sample(free, 2)
                    if a[0] != b[0] and a[1] != b[1]:
                        cells = frozenset((a, b))
                        break
            elif kind == "triple":
                candidates = []
                for r in range(h - 1):
                    for c in range(w - 1):
                        square = ((r, c), (r + 1, c), (r, c + 1), (r + 1, c + 1))
                        for missing in range(4):
                            shape = frozenset(cell for i, cell in enumerate(square) if i != missing)
                            if not shape & used:
                                candidates.append(shape)
                if candidates:
                    cells = rng.choice(candidates)
            if cells is None:
                ok = False
                break
            chosen.append(cells)
            used.update(cells)
        if ok:
            return chosen
    return None


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)

    band = difficulty if difficulty in ("easy", "medium", "hard") else "medium"
    phase = sample_index % 4
    override_mode = any(value is not None for value in overrides.values())
    schedules = {
        "easy": {
            "n_pairs": (2, 2, 3, 2), "n_distractors": (0, 1, 1, 2),
            "grid_h": (7, 8), "grid_w": (7, 9),
        },
        "medium": {
            "n_pairs": (2, 3, 4, 3), "n_distractors": (1, 2, 3, 2),
            "grid_h": (8, 11), "grid_w": (8, 12),
        },
        "hard": {
            "n_pairs": (3, 4, 4, 3), "n_distractors": (2, 3, 3, 1),
            "grid_h": (10, 14), "grid_w": (10, 14),
        },
    }[band]

    if overrides.get("grid_h") is not None:
        h = ctx.draw_int("grid_h", *_VALID_H)
    elif override_mode:
        h = ctx.draw_int("grid_h", 10, 10)
    else:
        h = ctx.draw_int("grid_h", *schedules["grid_h"])
    if overrides.get("grid_w") is not None:
        w = ctx.draw_int("grid_w", *_VALID_W)
    elif override_mode:
        w = ctx.draw_int("grid_w", 10, 10)
    else:
        w = ctx.draw_int("grid_w", *schedules["grid_w"])

    if overrides.get("n_pairs") is not None:
        n_pairs = ctx.draw_int("n_pairs", 1, 4)
    elif override_mode:
        n_pairs = ctx.draw_int("n_pairs", 2, 2)
    else:
        scheduled = schedules["n_pairs"][phase]
        n_pairs = ctx.draw_int("n_pairs", scheduled, scheduled)

    orientation_schedule = ("horizontal", "vertical", "mixed", "mixed")
    requested_orientation = overrides.get("orientation")
    if requested_orientation is not None:
        orientation = ctx.draw_choice("orientation", ORIENTATIONS)
    else:
        if override_mode:
            scheduled = "vertical" if w == _VALID_W[0] and h > w else "horizontal"
        else:
            scheduled = orientation_schedule[phase]
            if n_pairs == 1 and scheduled == "mixed":
                scheduled = "horizontal" if phase % 2 == 0 else "vertical"
        orientation = ctx.draw_choice("orientation", (scheduled,))

    span_schedule = ("short", "long", "mixed", "long")
    if overrides.get("span_class") is not None:
        span_class = ctx.draw_choice("span_class", SPAN_CLASSES)
    else:
        scheduled = "short" if override_mode else span_schedule[phase]
        if n_pairs == 1 and scheduled == "mixed":
            scheduled = "short"
        span_class = ctx.draw_choice("span_class", (scheduled,))

    if overrides.get("n_distractors") is not None:
        n_distractors = ctx.draw_int("n_distractors", 0, 3)
    else:
        scheduled = 1 if override_mode else schedules["n_distractors"][phase]
        if overrides.get("palette_kind") == "spread" and n_pairs + scheduled < 2:
            scheduled = 1
        n_distractors = ctx.draw_int("n_distractors", scheduled, scheduled)

    palette_schedule = ("lower", "upper", "spread", "spread")
    if overrides.get("palette_kind") is not None:
        palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    else:
        palette_kind = ctx.draw_choice("palette_kind", (("lower" if override_mode else palette_schedule[phase]),))

    if overrides.get("edge_anchor") is not None:
        edge_anchor = ctx.draw_choice("edge_anchor", (False, True))
    else:
        edge_anchor = ctx.draw_choice("edge_anchor", ((True if override_mode else (False, True, False, True)[phase]),))

    specs = _pair_specs(n_pairs, orientation, span_class)
    total_colors = n_pairs + n_distractors
    if palette_kind == "spread" and total_colors < 2:
        raise ValueError("palette_kind=spread requires n_pairs+n_distractors>=2")

    rng = ctx.draw_rng("layout")
    placed_pairs = _place_pairs(rng, h, w, specs, edge_anchor)
    if placed_pairs is None:
        raise ValueError(
            f"cannot place n_pairs={n_pairs}, orientation={orientation}, "
            f"span_class={span_class}, edge_anchor={edge_anchor} on {h}x{w}"
        )

    forbidden = set().union(*(segment for _, segment in placed_pairs))
    start = (seed + sample_index) % len(_DISTRACTOR_KINDS)
    kinds = [_DISTRACTOR_KINDS[(start + i) % len(_DISTRACTOR_KINDS)] for i in range(n_distractors)]
    distractors = _place_distractors(rng, h, w, kinds, forbidden)
    if distractors is None:
        raise ValueError(f"cannot place {n_distractors} distractors outside target spans on {h}x{w}")

    colors = _palette(rng, palette_kind, total_colors)
    grid = full_grid(h, w, 0)
    for color, (ends, _) in zip(colors[:n_pairs], placed_pairs):
        for r, c in ends:
            grid[r][c] = color
    for color, cells in zip(colors[n_pairs:], distractors):
        for r, c in cells:
            grid[r][c] = color

    errors = self_check(grid, difficulty=difficulty, meta={"texture": "standard"})
    if errors:
        raise ValueError("constructed invalid lesson: " + "; ".join(errors))
    return grid
