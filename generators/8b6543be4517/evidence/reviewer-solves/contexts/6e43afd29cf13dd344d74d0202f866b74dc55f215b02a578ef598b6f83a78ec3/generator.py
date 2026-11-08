"""Semantic generator for ARC task ``8b6543be4517``.

A full line of color 8 is the mirror axis.  The output is the symmetric
closure of the color-7 pattern across that line: every 7 keeps its original
cell and its in-bounds reflection becomes 7, including an occupied target.
Other colors are distractors and are preserved outside reflection targets.

Every draw contains unmatched 7s on both sides and an untouched asymmetric
non-7 distractor. Counts and completed pairs vary. Every consecutive four-demo
window covers both orientations, a centered axis, clipped sources, occupied
and clean targets, and both two-addition and more-than-three-addition cases.
Labels always come from the unchanged canonical Racket authority.
"""
from __future__ import annotations

from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8b6543be4517"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "4b5d3dcd179a"

SUMMARY = (
    "Find the unique full row or column of color 8.  For every color-7 cell, "
    "paint its reflection across that line color 7 while preserving the "
    "original 7 and the divider. Reflection targets become 7 even when occupied; "
    "all other cells, including distractors, stay unchanged. Out-of-bounds "
    "reflections are skipped without deleting their sources."
)
INVARIANTS = [
    "exactly one full color-8 row or column is the mirror divider",
    "all 7 cells lie off the divider; in-bounds reflections are copied and out-of-bounds reflections are skipped",
    "ordinary draws contain unmatched 7s on both sides; completed-pair and marker counts vary",
    "ordinary draws contain an asymmetric non-target distractor that stays unchanged",
    "four consecutive ordinary demos cover centered/clipped and occupied/clean target branches",
]
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

# A single exact categorical axis keeps the override contract honest.  Each
# profile is recoverable from visible scene features (shape, divider, and
# distractor color/count); no hidden metadata is needed.
_PROFILE_ROWS = (
    # name, h, w, orientation, divider index, distractor color, distractor cells
    ("e_col_4", 9, 12, "col", 5, 4, 4),
    ("e_row_6", 10, 13, "row", 4, 6, 3),
    ("e_col_5", 8, 11, "col", 6, 5, 3),
    ("e_row_9", 9, 12, "row", 5, 9, 2),
    ("m_col_6", 10, 13, "col", 5, 6, 2),
    ("m_row_4", 9, 12, "row", 5, 4, 3),
    ("m_col_9", 8, 11, "col", 4, 9, 4),
    ("m_row_5", 10, 13, "row", 5, 5, 2),
    ("h_col_4", 10, 13, "col", 7, 4, 2),
    ("h_row_6", 8, 11, "row", 3, 6, 4),
    ("h_col_5", 9, 12, "col", 5, 5, 2),
    ("h_row_9", 10, 13, "row", 4, 9, 4),
    # Keep legacy signatures intact; add visibly centered row/column profiles.
    ("center_col_4", 10, 13, "col", 6, 4, 4),
    ("center_row_6", 9, 12, "row", 4, 6, 3),
)
SCENE_PROFILES = tuple(row[0] for row in _PROFILE_ROWS)
_PROFILE_BY_NAME = {
    name: {
        "h": h,
        "w": w,
        "orientation": orientation,
        "mid": mid,
        "distractor": distractor,
        "distractor_cells": distractor_cells,
    }
    for name, h, w, orientation, mid, distractor, distractor_cells in _PROFILE_ROWS
}
_PROFILES_BY_BAND = {
    "easy": ("e_col_4", "e_row_6", "center_col_4", "e_row_9", "e_col_5", "center_row_6"),
    "medium": ("m_col_6", "m_row_4", "center_col_4", "m_row_5", "m_col_9", "center_row_6"),
    "hard": ("h_col_4", "h_row_6", "center_col_4", "h_row_9", "h_col_5", "center_row_6"),
}
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "six-profile deterministic curriculum per difficulty band",
        "valid": "e_col_4|e_row_6|e_col_5|e_row_9|m_col_6|m_row_4|m_col_9|m_row_5|h_col_4|h_row_6|h_col_5|h_row_9|center_col_4|center_row_6",
    }
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
_CANONICAL_DIMS = {(8, 11), (9, 12), (10, 13)}
_DISTRACTOR_COLORS = {4, 5, 6, 9}


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    del seed
    profiles = _PROFILES_BY_BAND[_band(difficulty)]
    return profiles[int(sample_index) % len(profiles)]


def _validate_grid(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    w = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["grid must be rectangular"]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return [f"cell ({r},{c}) must be an ARC integer color 0..9"]
    return []


def _divider(grid: Sequence[Sequence[int]]) -> tuple[str, int] | None:
    h, w = len(grid), len(grid[0])
    rows = [r for r in range(h) if all(grid[r][c] == 8 for c in range(w))]
    cols = [c for c in range(w) if all(grid[r][c] == 8 for r in range(h))]
    if len(rows) + len(cols) != 1:
        return None
    return ("row", rows[0]) if rows else ("col", cols[0])


def _reflect(pos: tuple[int, int], orientation: str, mid: int) -> tuple[int, int]:
    r, c = pos
    return (2 * mid - r, c) if orientation == "row" else (r, 2 * mid - c)


def _side(pos: tuple[int, int], orientation: str, mid: int) -> int:
    value = pos[0] if orientation == "row" else pos[1]
    return -1 if value < mid else (1 if value > mid else 0)


def _analysis(grid: Sequence[Sequence[int]]) -> dict[str, Any]:
    if _validate_grid(grid):
        return {"divider": None}
    div = _divider(grid)
    if div is None:
        return {"divider": None}
    orientation, mid = div
    h, w = len(grid), len(grid[0])
    sevens = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 7}
    paired = set()
    unmatched = {-1: set(), 1: set()}
    out_of_bounds = set()
    on_divider = set()
    for pos in sevens:
        side = _side(pos, orientation, mid)
        if side == 0:
            on_divider.add(pos)
            continue
        rr, cc = _reflect(pos, orientation, mid)
        if not (0 <= rr < h and 0 <= cc < w):
            out_of_bounds.add(pos)
        elif (rr, cc) in sevens:
            paired.add(pos)
        else:
            unmatched[side].add(pos)
    other_eights = [
        (r, c) for r in range(h) for c in range(w)
        if grid[r][c] == 8 and ((orientation == "row" and r != mid) or (orientation == "col" and c != mid))
    ]
    distractors = [
        (r, c, grid[r][c]) for r in range(h) for c in range(w)
        if grid[r][c] not in (0, 7, 8)
    ]
    collision_targets = set()
    for pos in unmatched[-1] | unmatched[1]:
        q = _reflect(pos, orientation, mid)
        if grid[q[0]][q[1]] not in (0, 7, 8):
            collision_targets.add(q)
    preserved_asymmetric = set()
    for r, c, _color in distractors:
        q = _reflect((r, c), orientation, mid)
        if ((r, c) not in collision_targets and 0 <= q[0] < h and 0 <= q[1] < w
                and grid[q[0]][q[1]] == 0):
            preserved_asymmetric.add((r, c))
    return {
        "divider": div,
        "centered": 2 * mid == (h if orientation == "row" else w) - 1,
        "collision_targets": collision_targets,
        "preserved_asymmetric_distractors": preserved_asymmetric,
        "sevens": sevens,
        "paired": paired,
        "unmatched_neg": unmatched[-1],
        "unmatched_pos": unmatched[1],
        "out_of_bounds": out_of_bounds,
        "on_divider": on_divider,
        "other_eights": other_eights,
        "distractors": distractors,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task's structural input grammar (including all canonicals)."""
    del difficulty, meta
    errors = _validate_grid(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    info = _analysis(grid)
    if info.get("divider") is None:
        errors.append("expected exactly one full color-8 row or column divider")
        return errors
    if info["other_eights"]:
        errors.append("color 8 may appear only on the full divider")
    if not info["sevens"]:
        errors.append("at least one off-divider color-7 marker is required")
    if info["on_divider"]:
        errors.append("color-7 markers may not overwrite the divider")
    # The ARC task uses zero as background; without any zero there is no scene
    # around the divider/pattern and destructive solid-grid impostors pass.
    if not any(value == 0 for row in grid for value in row):
        errors.append("background color 0 must be present")
    if h < 5 or w < 5:
        errors.append("grid is too small to express divider/reflection structure")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Accept the canonical manifold while checking its visible envelope."""
    errors = self_check(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    colors = {value for row in grid for value in row}
    if (h, w) not in _CANONICAL_DIMS:
        errors.append(f"dimensions {h}x{w} are outside canonical profiles")
    if len(colors) != 4 or not {0, 7, 8}.issubset(colors):
        errors.append(f"canonical-like input must use 0/7/8 plus one distractor color, found {sorted(colors)}")
    distractor_colors = colors - {0, 7, 8}
    if len(distractor_colors) != 1 or not distractor_colors.issubset(_DISTRACTOR_COLORS):
        errors.append(f"distractor color must be one of {sorted(_DISTRACTOR_COLORS)}")
    return errors


def _profile_signature(grid: Sequence[Sequence[int]]) -> tuple[Any, ...] | None:
    info = _analysis(grid)
    if info.get("divider") is None:
        return None
    orientation, mid = info["divider"]
    distractor_colors = sorted({color for _, _, color in info["distractors"]})
    if len(distractor_colors) != 1:
        return None
    return (
        len(grid), len(grid[0]), orientation, mid,
        distractor_colors[0], len(info["distractors"]),
    )


_PROFILE_BY_SIGNATURE = {
    (p["h"], p["w"], p["orientation"], p["mid"], p["distractor"], p["distractor_cells"]): name
    for name, p in _PROFILE_BY_NAME.items()
}
if len(_PROFILE_BY_SIGNATURE) != len(_PROFILE_BY_NAME):
    raise RuntimeError("scene profile signatures must be unique")


def observe_overrides(grid) -> dict[str, str | None]:
    if _validate_grid(grid):
        return {"scene_profile": None}
    return {"scene_profile": _PROFILE_BY_SIGNATURE.get(_profile_signature(grid))}


def _candidate_pairs(h: int, w: int, orientation: str, mid: int):
    """Return unique reflection pairs wholly inside the grid, away from axis."""
    seen = set()
    pairs = []
    for r in range(h):
        for c in range(w):
            pos = (r, c)
            if _side(pos, orientation, mid) == 0:
                continue
            q = _reflect(pos, orientation, mid)
            if not (0 <= q[0] < h and 0 <= q[1] < w) or q == pos:
                continue
            key = tuple(sorted((pos, q)))
            if key not in seen:
                seen.add(key)
                pairs.append(key)
    return pairs


def _draw_profile(profile: dict[str, Any], rng, *, cadence: int) -> list[list[int]]:
    """Construct pixels; reject a layout instead of weakening branch witnesses.

    The four-step cadence is independent of the six-step visible profile cycle.
    0/1 have occupied targets; 2/3 have clean targets. Steps 0/1/2 request
    clipped sources when geometry permits. A four-demo window has three such
    requests but at most two centered slots, so at least one request can fire.
    Step 0 adds >3 sevens and step 3 adds exactly two. Counts otherwise vary.
    """
    h, w = profile["h"], profile["w"]
    orientation, mid = profile["orientation"], profile["mid"]
    for _attempt in range(200):
        g = full_grid(h, w, 0)
        if orientation == "row":
            for c in range(w):
                g[mid][c] = 8
        else:
            for r in range(h):
                g[r][mid] = 8

        pairs = _candidate_pairs(h, w, orientation, mid)
        rng.shuffle(pairs)
        if len(pairs) < 5:
            continue

        # Completed pairs are optional, as in the canonical examples. Paired
        # and unpaired orbits are chosen without replacement, so count variation
        # cannot accidentally turn a required one-sided orbit into a full pair.
        for _ in range(rng.choice((0, 0, 1, 1, 2))):
            for r, c in pairs.pop():
                g[r][c] = 7
        n_unmatched = rng.randint(4, 5) if cadence == 0 else (
            2 if cadence == 3 else rng.randint(2, 5))
        sides = [-1, 1] + [rng.choice((-1, 1)) for _ in range(n_unmatched - 2)]
        for desired_side in sides:
            candidates = [(idx, next(p for p in pair if _side(p, orientation, mid) == desired_side))
                          for idx, pair in enumerate(pairs)]
            # Prefer some adjacent cells rather than emitting only isolated
            # pixels. Orbit ownership still prevents accidental complete pairs.
            touching = [(idx, p) for idx, p in candidates
                        if any(0 <= rr < h and 0 <= cc < w and g[rr][cc] == 7
                               for rr, cc in ((p[0]-1,p[1]), (p[0]+1,p[1]),
                                              (p[0],p[1]-1), (p[0],p[1]+1)))]
            idx, pos = rng.choice(touching if touching and rng.random() < 0.7 else candidates)
            pairs.pop(idx)
            g[pos[0]][pos[1]] = 7

        oob_candidates = []
        for r in range(h):
            for c in range(w):
                if g[r][c] != 0 or _side((r, c), orientation, mid) == 0:
                    continue
                rr, cc = _reflect((r, c), orientation, mid)
                if not (0 <= rr < h and 0 <= cc < w):
                    oob_candidates.append((r, c))
        if cadence in (0, 1, 2) and oob_candidates:
            rng.shuffle(oob_candidates)
            count = rng.randint(1, min(3, len(oob_candidates)))
            for r, c in oob_candidates[:count]:
                g[r][c] = 7

        # Place a preserved distractor object asymmetrically, avoiding all 7s
        # and their reflection cells so the mirror-everything rival is visible.
        color = profile["distractor"]
        need = profile["distractor_cells"]
        empties = []
        for r in range(h):
            for c in range(w):
                if g[r][c] != 0:
                    continue
                q = _reflect((r, c), orientation, mid)
                if not (0 <= q[0] < h and 0 <= q[1] < w):
                    continue
                if g[q[0]][q[1]] == 0:
                    empties.append((r, c))
        rng.shuffle(empties)
        placed = []
        if empties:
            first = empties[0]
            placed.append(first)
            frontier = [first]
            while len(placed) < need and frontier:
                r, c = frontier.pop(0)
                nbrs = [(r-1,c),(r+1,c),(r,c-1),(r,c+1)]
                rng.shuffle(nbrs)
                for p in nbrs:
                    if p in empties and p not in placed and g[p[0]][p[1]] == 0:
                        # keep the reflected location empty
                        q = _reflect(p, orientation, mid)
                        if g[q[0]][q[1]] == 0 and q not in placed:
                            placed.append(p)
                            frontier.append(p)
                            if len(placed) >= need:
                                break
        if len(placed) != need:
            continue
        for r, c in placed:
            g[r][c] = color
        if cadence in (0, 1):
            # The canonical Racket writes 7 at every reflected target, not only
            # zeros. Add sources opposite part of the distractor object while
            # leaving at least one asymmetric non-target distractor untouched.
            targets = list(placed)
            rng.shuffle(targets)
            count = rng.randint(1, len(targets) - 1)
            for pos in targets[:count]:
                rr, cc = _reflect(pos, orientation, mid)
                g[rr][cc] = 7
        info = _analysis(g)
        curriculum_ok = (
            not strict_canonical_like(g)
            and bool(info["unmatched_neg"])
            and bool(info["unmatched_pos"])
            and bool(info["preserved_asymmetric_distractors"])
            and bool(info["collision_targets"]) == (cadence in (0, 1))
        )
        if curriculum_ok and observe_overrides(g)["scene_profile"] is not None:
            return g
    raise RuntimeError("failed to construct a lawful mirror scene")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    band = _band(difficulty)
    requested = overrides.get("scene_profile")
    if requested is not None and (not isinstance(requested, str) or requested not in _PROFILE_BY_NAME):
        raise ValueError(f"unknown scene_profile: {requested!r}")
    selected = requested or schedule_profile(seed, sample_index, band)
    ctx = gen_ctx(
        seed=seed, sample_index=sample_index, version=VERSION,
        task_id=TASK_ID, difficulty=band, overrides=overrides,
    )
    profile_name = ctx.draw_choice("scene_profile", [selected])
    return _draw_profile(_PROFILE_BY_NAME[profile_name], ctx.draw_rng("layout"),
                         cadence=int(sample_index) % 4)


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Independent Python mirror for semantic discrimination/tests only."""
    out = [list(row) for row in grid]
    div = _divider(grid)
    if div is None:
        return out
    orientation, mid = div
    h, w = len(grid), len(grid[0])
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 7:
                continue
            rr, cc = _reflect((r, c), orientation, mid)
            if 0 <= rr < h and 0 <= cc < w:
                out[rr][cc] = 7
    return out


def _rival_negative_to_positive_only(grid):
    out = [list(row) for row in grid]
    div = _divider(grid)
    if div is None:
        return out
    orientation, mid = div
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 7 and _side((r, c), orientation, mid) < 0:
                rr, cc = _reflect((r, c), orientation, mid)
                if 0 <= rr < len(grid) and 0 <= cc < len(grid[0]):
                    out[rr][cc] = 7
    return out


def _rival_positive_to_negative_only(grid):
    out = [list(row) for row in grid]
    div = _divider(grid)
    if div is None:
        return out
    orientation, mid = div
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 7 and _side((r, c), orientation, mid) > 0:
                rr, cc = _reflect((r, c), orientation, mid)
                if 0 <= rr < len(grid) and 0 <= cc < len(grid[0]):
                    out[rr][cc] = 7
    return out


def _rival_mirror_all_nonzero(grid):
    out = [list(row) for row in grid]
    div = _divider(grid)
    if div is None:
        return out
    orientation, mid = div
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value not in (0, 8):
                rr, cc = _reflect((r, c), orientation, mid)
                if 0 <= rr < len(grid) and 0 <= cc < len(grid[0]):
                    out[rr][cc] = value
    return out


def _rival_row_dividers_only(grid):
    div = _divider(grid)
    if div is None or div[0] != "row":
        return [list(row) for row in grid]
    return rule_mirror(grid)


def _rival_column_dividers_only(grid):
    div = _divider(grid)
    if div is None or div[0] != "col":
        return [list(row) for row in grid]
    return rule_mirror(grid)


def _rival_drop_unreflectable_sevens(grid):
    """Wrongly delete source 7s whose reflection would leave the grid."""
    out = rule_mirror(grid)
    info = _analysis(grid)
    for r, c in info.get("out_of_bounds", ()):
        out[r][c] = 0
    return out


def _rival_move_sevens(grid):
    out = [list(row) for row in grid]
    div = _divider(grid)
    if div is None:
        return out
    orientation, mid = div
    original = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 7]
    for r, c in original:
        out[r][c] = 0
    for pos in original:
        rr, cc = _reflect(pos, orientation, mid)
        if 0 <= rr < len(grid) and 0 <= cc < len(grid[0]):
            out[rr][cc] = 7
    return out


def _rival_paint_background_only(grid):
    """Plausible but wrong: refuse to overwrite a nonzero reflection target."""
    out = [list(row) for row in grid]
    div = _divider(grid)
    if div is None:
        return out
    orientation, mid = div
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 7:
                rr, cc = _reflect((r, c), orientation, mid)
                if 0 <= rr < len(grid) and 0 <= cc < len(row) and grid[rr][cc] == 0:
                    out[rr][cc] = 7
    return out


def _rival_add_at_most_three(grid):
    """The old sampler always changed exactly three cells."""
    target = rule_mirror(grid)
    out = [list(row) for row in grid]
    added = 0
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if target[r][c] != value and added < 3:
                out[r][c] = target[r][c]
                added += 1
    return out


def _rival_offcenter_only(grid):
    if _analysis(grid).get("centered"):
        return [list(row) for row in grid]
    return rule_mirror(grid)


SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "copy_negative_side_only": _rival_negative_to_positive_only,
    "copy_positive_side_only": _rival_positive_to_negative_only,
    "mirror_every_nonzero_color": _rival_mirror_all_nonzero,
    "move_sevens_instead_of_copy": _rival_move_sevens,
    "row_dividers_only": _rival_row_dividers_only,
    "column_dividers_only": _rival_column_dividers_only,
    "drop_unreflectable_sevens": _rival_drop_unreflectable_sevens,
    "paint_background_only": _rival_paint_background_only,
    "add_at_most_three": _rival_add_at_most_three,
    "offcenter_dividers_only": _rival_offcenter_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)

SEMANTIC_WITNESSES = {
    "row_divider": lambda g: (_analysis(g).get("divider") or (None,))[0] == "row",
    "column_divider": lambda g: (_analysis(g).get("divider") or (None,))[0] == "col",
    "preexisting_mirrored_pair": lambda g: bool(_analysis(g).get("paired")),
    "unmatched_negative_side": lambda g: bool(_analysis(g).get("unmatched_neg")),
    "unmatched_positive_side": lambda g: bool(_analysis(g).get("unmatched_pos")),
    "preserved_non7_distractor": lambda g: bool(_analysis(g).get("preserved_asymmetric_distractors")),
    "out_of_bounds_reflection_skipped": lambda g: bool(_analysis(g).get("out_of_bounds")),
    "occupied_target_overwritten": lambda g: bool(_analysis(g).get("collision_targets")),
    "centered_divider": lambda g: bool(_analysis(g).get("centered")),
    "more_than_three_additions": lambda g: (
        len(_analysis(g).get("unmatched_neg", ())) + len(_analysis(g).get("unmatched_pos", ())) > 3),
}
WITNESS_RIVALS = {
    "row_divider": ["column_dividers_only"],
    "column_divider": ["row_dividers_only"],
    "out_of_bounds_reflection_skipped": ["drop_unreflectable_sevens"],
    "unmatched_negative_side": ["copy_positive_side_only"],
    "unmatched_positive_side": ["copy_negative_side_only"],
    "preserved_non7_distractor": ["mirror_every_nonzero_color"],
    "preexisting_mirrored_pair": ["move_sevens_instead_of_copy"],
    "occupied_target_overwritten": ["paint_background_only"],
    "centered_divider": ["offcenter_dividers_only"],
    "more_than_three_additions": ["add_at_most_three"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require official outputs and kill every named shortcut before query."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output"]
    errors: list[str] = []
    for i, pair in enumerate([*demos, query]):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            errors.append(f"pair {i} must contain input and output")
            continue
        if self_check(pair["input"]):
            errors.append(f"pair {i} is outside the lawful input grammar")
            continue
        if _validate_grid(pair["output"]):
            errors.append(f"pair {i} has a malformed output grid")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            errors.append(f"pair {i} disagrees with the mirror-closure rule")
    if errors:
        return errors
    for name, rival in SEMANTIC_RIVALS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                errors.append(f"demonstrations still admit rival {name}")
    return errors
