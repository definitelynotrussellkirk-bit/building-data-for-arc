"""Semantic generator for ARC task c7a821733003.

Candidate L-frames use colors 5/6/7: 5 is the local origin, while the adjacent
6 and 7 cells define an ordered orthogonal basis.  Read nearby color-8 cells in
that local basis.  Exactly one candidate has a unique local signature; output a
1xN strip with 8 at that candidate's row-major index.

The 2/3/4 frame is deliberately non-authoritative.  Its motif is scheduled to
match the common candidate motif, the odd motif, or neither so training cannot
replace candidate-to-candidate comparison with a source-comparison shortcut.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "c7a821733003"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "7b53208520c4"

SUMMARY = (
    "Find every 5/6/7 L-frame, express nearby 8-cells in that frame's ordered "
    "local coordinates, and select the sole candidate whose signature occurs "
    "once. Return a 1xN strip with 8 at its row-major candidate index. The "
    "2/3/4 frame is a non-authoritative distractor whose motif varies "
    "independently across the curriculum."
)

INVARIANTS = [
    "one decorative 2/3/4 orthogonal L-frame and 3, 5, or 7 candidate 5/6/7 frames",
    "all but one candidate share one exact local color-8 signature",
    "the odd candidate has a different signature with the same cardinality",
    "candidate order is row-major by the color-5 origin",
]

# Each profile is exactly recoverable from the returned grid: dimensions,
# candidate count, odd index, and source/candidate signature relation.
_PROFILE_ROWS = (
    ("canonical_common_first", 13, 25, 3, 0, "common"),
    ("canonical_odd_middle", 13, 25, 3, 1, "odd"),
    ("canonical_unrelated_last", 13, 25, 3, 2, "unrelated"),
    ("canonical5_common_first", 13, 25, 5, 0, "common"),
    ("wide_odd_inner1", 20, 27, 5, 1, "odd"),
    ("wide_unrelated_middle", 20, 27, 5, 2, "unrelated"),
    ("wide_common_inner3", 20, 27, 5, 3, "common"),
    ("canonical5_odd_last", 13, 25, 5, 4, "odd"),
    ("large_unrelated_first", 21, 30, 7, 0, "unrelated"),
    ("wide7_common_inner1", 20, 27, 7, 1, "common"),
    ("large_odd_inner2", 21, 30, 7, 2, "odd"),
    ("wide7_unrelated_middle", 20, 27, 7, 3, "unrelated"),
    ("large_common_inner4", 21, 30, 7, 4, "common"),
    ("wide7_odd_inner5", 20, 27, 7, 5, "odd"),
    ("large_unrelated_last", 21, 30, 7, 6, "unrelated"),
)
SCENE_PROFILES = tuple(row[0] for row in _PROFILE_ROWS)
SCHEDULE_PROFILES = SCENE_PROFILES
_PROFILE_BY_NAME = {row[0]: row[1:] for row in _PROFILE_ROWS}
_PROFILE_BY_SIGNATURE = {row[1:]: row[0] for row in _PROFILE_ROWS}

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "deterministic six-profile curriculum",
        "valid": "canonical_common_first|canonical_odd_middle|canonical_unrelated_last|canonical5_common_first|wide_odd_inner1|wide_unrelated_middle|wide_common_inner3|canonical5_odd_last|large_unrelated_first|wide7_common_inner1|large_odd_inner2|wide7_unrelated_middle|large_common_inner4|wide7_odd_inner5|large_unrelated_last",
    }
}

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 4
EXPECTED_OUTPUT_CODOMAIN = 15

_CARD = ((-1, 0), (1, 0), (0, -1), (0, 1))
_BASES = tuple(
    (vx, vy)
    for vx in _CARD
    for vy in _CARD
    if vx[0] * vy[0] + vx[1] * vy[1] == 0
)
_FORBIDDEN = {(0, 0), (1, 0), (0, 1)}

# Asymmetric, three-cell signatures.  Equal size prevents a cell-count shortcut.
_MOTIFS = (
    ((-1, 2), (1, -1), (2, 1)),
    ((-1, 2), (2, -1), (2, 1)),
    ((-2, 1), (1, 2), (2, -1)),
    ((-2, 1), (1, -1), (1, 2)),
    ((-2, -1), (-1, 2), (2, 2)),
    ((-2, 2), (1, -2), (2, 1)),
    ((-1, -2), (2, -1), (2, 2)),
    ((-2, -2), (-1, 1), (2, -1)),
)
assert all(not (set(motif) & _FORBIDDEN) for motif in _MOTIFS)


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Any four consecutive examples cover all source relations and odd zones."""
    band_offset = {"easy": 0, "medium": 2, "hard": 4}[_band(difficulty)]
    offset = int(seed) % len(SCENE_PROFILES)
    return SCENE_PROFILES[(int(sample_index) + offset + band_offset) % len(SCENE_PROFILES)]


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not 7 <= len(grid) <= 30 or not 7 <= width <= 30:
        return [f"grid dimensions must be in 7..30, found {len(grid)}x{width}"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _find_frames(grid, colors: tuple[int, int, int]):
    """Mirror the selected Racket frame finder and its row-major sort order."""
    height, width = len(grid), len(grid[0])
    origin_color, x_color, y_color = colors
    frames = set()
    for row in range(height):
        for col in range(width):
            if grid[row][col] != origin_color:
                continue
            for vx, vy in _BASES:
                xr, xc = row + vx[0], col + vx[1]
                yr, yc = row + vy[0], col + vy[1]
                if not (0 <= xr < height and 0 <= xc < width):
                    continue
                if not (0 <= yr < height and 0 <= yc < width):
                    continue
                if grid[xr][xc] == x_color and grid[yr][yc] == y_color:
                    frames.add(((row, col), vx, vy))
    return sorted(frames)


def _local_signature(grid, frame) -> tuple[tuple[int, int], ...]:
    """The Racket rule clamps its requested radius 4 to local radius 3."""
    (origin_row, origin_col), vx, vy = frame
    signature = []
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 8:
                continue
            dr, dc = row - origin_row, col - origin_col
            u = dr * vx[0] + dc * vx[1]
            v = dr * vy[0] + dc * vy[1]
            if max(abs(u), abs(v)) <= 3:
                signature.append((u, v))
    return tuple(sorted(signature))


def _global_signature(grid, frame) -> tuple[tuple[int, int], ...]:
    """A deliberately wrong rival: ignore the 6/7-defined local basis."""
    (origin_row, origin_col), _vx, _vy = frame
    points = []
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value == 8 and max(abs(row - origin_row), abs(col - origin_col)) <= 3:
                points.append((row - origin_row, col - origin_col))
    return tuple(sorted(points))


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_errors(grid)
    if errors:
        return {"errors": errors}

    height, width = len(grid), len(grid[0])
    allowed = {0, 2, 3, 4, 5, 6, 7, 8}
    extra = sorted({value for row in grid for value in row if value not in allowed})
    if extra:
        errors.append(f"unexpected colors: {extra}")

    counts = Counter(value for row in grid for value in row)
    if (counts[2], counts[3], counts[4]) != (1, 1, 1):
        errors.append(
            "expected exactly one cell of each decorative frame color 2/3/4, "
            f"found {counts[2]}/{counts[3]}/{counts[4]}"
        )
    n_candidates = counts[5]
    if n_candidates < 3 or n_candidates > 7:
        errors.append(f"expected 3..7 candidate origins (color 5), found {n_candidates}")
    if counts[6] != n_candidates or counts[7] != n_candidates:
        errors.append(
            "candidate frame colors 5/6/7 must have equal counts, found "
            f"{counts[5]}/{counts[6]}/{counts[7]}"
        )

    sources = _find_frames(grid, (2, 3, 4))
    candidates = _find_frames(grid, (5, 6, 7))
    if len(sources) != 1:
        errors.append(f"expected exactly one valid 2/3/4 L-frame, found {len(sources)}")
    if len(candidates) != n_candidates:
        errors.append(
            f"expected one valid 5/6/7 L-frame per origin, found {len(candidates)} "
            f"for {n_candidates} origins"
        )

    source_signature = _local_signature(grid, sources[0]) if len(sources) == 1 else ()
    signatures = [_local_signature(grid, frame) for frame in candidates]
    if source_signature and not 2 <= len(source_signature) <= 5:
        errors.append(
            f"decorative source motif must contain 2..5 local color-8 cells, found {len(source_signature)}"
        )
    if signatures and any(not 2 <= len(signature) <= 5 for signature in signatures):
        errors.append("every candidate must expose 2..5 local color-8 motif cells")
    if signatures and len({len(signature) for signature in signatures}) != 1:
        errors.append("candidate motif cardinality must be equal; size may not reveal the odd candidate")

    signature_counts = Counter(signatures)
    odd_indices = [index for index, signature in enumerate(signatures) if signature_counts[signature] == 1]
    common_signatures = [signature for signature, count in signature_counts.items() if count == n_candidates - 1]
    if len(signature_counts) != 2 or len(odd_indices) != 1 or len(common_signatures) != 1:
        errors.append(
            "candidate signatures must form one common class of size N-1 and exactly one odd signature"
        )

    odd_index = odd_indices[0] if len(odd_indices) == 1 else None
    common_signature = common_signatures[0] if len(common_signatures) == 1 else None
    odd_signature = signatures[odd_index] if odd_index is not None else None
    source_relation = None
    if source_signature and common_signature is not None and odd_signature is not None:
        if source_signature == common_signature:
            source_relation = "common"
        elif source_signature == odd_signature:
            source_relation = "odd"
        else:
            source_relation = "unrelated"

    # Every color-8 cell must belong to exactly one visible source/candidate motif.
    covered: set[tuple[int, int]] = set()
    owners: Counter[tuple[int, int]] = Counter()
    for frame in sources + candidates:
        (origin_row, origin_col), vx, vy = frame
        for u, v in _local_signature(grid, frame):
            row = origin_row + u * vx[0] + v * vy[0]
            col = origin_col + u * vx[1] + v * vy[1]
            covered.add((row, col))
            owners[(row, col)] += 1
    actual_eights = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 8
    }
    if covered != actual_eights:
        errors.append("all color-8 cells must belong to a recognized local motif")
    if any(count != 1 for count in owners.values()):
        errors.append("local motif neighborhoods must not share color-8 cells")

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "sources": sources,
        "candidates": candidates,
        "source_signature": source_signature,
        "signatures": signatures,
        "common_signature": common_signature,
        "odd_signature": odd_signature,
        "odd_index": odd_index,
        "source_relation": source_relation,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, size-leaking, or cross-contaminated scenes."""
    del difficulty
    errors = list(_analysis(grid)["errors"])
    if meta and isinstance(meta, dict):
        requested = (meta.get("overrides") or {}).get("scene_profile")
        if requested is not None:
            observed = observe_overrides(grid).get("scene_profile")
            if observed != requested:
                errors.append(f"scene_profile override requested {requested!r}, observed {observed!r}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def rule_mirror(grid):
    analysis = _analysis(grid)
    if analysis["errors"] or analysis["odd_index"] is None:
        raise ValueError("input is outside c7a821733003's lawful grammar: " + "; ".join(analysis["errors"]))
    n_candidates = len(analysis["candidates"])
    return [[8 if index == analysis["odd_index"] else 0 for index in range(n_candidates)]]


def observe_overrides(grid) -> dict[str, str | None]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {"scene_profile": None}
    signature = (
        analysis["height"],
        analysis["width"],
        len(analysis["candidates"]),
        analysis["odd_index"],
        analysis["source_relation"],
    )
    return {"scene_profile": _PROFILE_BY_SIGNATURE.get(signature)}


def _profile(seed: int, sample_index: int, difficulty: Any, overrides: dict[str, Any]):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    band = _band(difficulty)
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in _PROFILE_BY_NAME:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    scheduled = requested or schedule_profile(seed, sample_index, band)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    options = SCENE_PROFILES if requested is not None else (scheduled,)
    selected = ctx.draw_choice("scene_profile", options)
    return ctx, selected, _PROFILE_BY_NAME[selected]


def _slots(height: int, width: int) -> list[tuple[int, int]]:
    rows = list(range(3, height - 2, 7))
    cols = list(range(3, width - 2, 7))
    return [(row, col) for row in rows for col in cols]


def _frame_cells(origin, vx, vy, motif):
    row, col = origin
    frame = [origin, (row + vx[0], col + vx[1]), (row + vy[0], col + vy[1])]
    motif_cells = [
        (row + u * vx[0] + v * vy[0], col + u * vx[1] + v * vy[1])
        for u, v in motif
    ]
    return frame, motif_cells


def _paint(grid, origin, basis, colors, motif) -> None:
    frame, motif_cells = _frame_cells(origin, basis[0], basis[1], motif)
    for (row, col), color in zip(frame, colors):
        grid[row][col] = color
    for row, col in motif_cells:
        grid[row][col] = 8


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx, profile_name, profile = _profile(seed, sample_index, difficulty, overrides)
    height, width, n_candidates, odd_index, source_relation = profile

    motif_rng = ctx.draw_rng("motifs")
    layout_rng = ctx.draw_rng("layout")
    basis_rng = ctx.draw_rng("bases")
    common, odd, unrelated = motif_rng.sample(list(_MOTIFS), 3)
    source_motif = {"common": common, "odd": odd, "unrelated": unrelated}[source_relation]

    available = _slots(height, width)
    if len(available) < n_candidates + 1:
        raise ValueError(
            f"profile {profile_name!r} has only {len(available)} safe slots for "
            f"{n_candidates + 1} frames"
        )

    # Retry only layout/basis spelling.  Semantic profile and motifs remain pinned.
    for attempt in range(80):
        chosen = layout_rng.sample(available, n_candidates + 1)
        source_origin = chosen[0]
        candidate_origins = sorted(chosen[1:])

        source_basis = basis_rng.choice(_BASES)
        candidate_bases = [basis_rng.choice(_BASES) for _ in range(n_candidates)]
        common_indices = [index for index in range(n_candidates) if index != odd_index]
        # Force at least two common candidates to realize the same local motif in
        # different global poses, which rebuts absolute-offset comparison.
        if len(common_indices) >= 2:
            candidate_bases[common_indices[0]] = _BASES[(attempt + 0) % len(_BASES)]
            candidate_bases[common_indices[1]] = _BASES[(attempt + 3) % len(_BASES)]

        grid = full_grid(height, width, 0)
        _paint(grid, source_origin, source_basis, (2, 3, 4), source_motif)
        for index, origin in enumerate(candidate_origins):
            motif = odd if index == odd_index else common
            _paint(grid, origin, candidate_bases[index], (5, 6, 7), motif)

        analysis = _analysis(grid)
        if analysis["errors"]:
            continue
        if observe_overrides(grid) != {"scene_profile": profile_name}:
            continue
        return grid

    raise RuntimeError(f"failed to realize lawful profile {profile_name!r} after 80 attempts")


# ---------------------------------------------------------------------------
# Named rival rules and lesson identifiability
# ---------------------------------------------------------------------------

def _strip(n_candidates: int, index: int) -> list[list[int]]:
    return [[8 if col == index else 0 for col in range(n_candidates)]]


def _rival_fixed(index_fn: Callable[[int], int]):
    def rival(grid):
        analysis = _analysis(grid)
        n_candidates = len(analysis.get("candidates", ()))
        if analysis["errors"] or not n_candidates:
            return []
        return _strip(n_candidates, index_fn(n_candidates))
    return rival


def _rival_source_mismatch(grid):
    """Canonical-fitting shortcut: pick the first candidate unlike the source."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return []
    source = analysis["source_signature"]
    index = next(
        (i for i, signature in enumerate(analysis["signatures"]) if signature != source),
        0,
    )
    return _strip(len(analysis["candidates"]), index)


def _rival_global_coordinates(grid):
    """Ignore the 6/7 basis and compare absolute offsets from each 5 origin."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return []
    signatures = [_global_signature(grid, frame) for frame in analysis["candidates"]]
    counts = Counter(signatures)
    index = next((i for i, signature in enumerate(signatures) if counts[signature] == 1), 0)
    return _strip(len(signatures), index)


def _rival_motif_size_only(grid):
    """Pick a unique motif cardinality; fall back to the first candidate."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return []
    sizes = [len(signature) for signature in analysis["signatures"]]
    counts = Counter(sizes)
    index = next((i for i, size in enumerate(sizes) if counts[size] == 1), 0)
    return _strip(len(sizes), index)


SEMANTIC_RIVALS = {
    "source_mismatch": _rival_source_mismatch,
    "absolute_global_offsets": _rival_global_coordinates,
    "motif_size_only": _rival_motif_size_only,
    "always_first": _rival_fixed(lambda _n: 0),
    "always_middle": _rival_fixed(lambda n: (n - 1) // 2),
    "always_last": _rival_fixed(lambda n: n - 1),
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"source_mismatch": _rival_source_mismatch}


def _valid_and_differs(grid, rival_name: str) -> bool:
    return not self_check(grid) and SEMANTIC_RIVALS[rival_name](grid) != rule_mirror(grid)


def _source_relation_breaks_source_mismatch(grid) -> bool:
    analysis = _analysis(grid)
    return (
        not analysis["errors"]
        and analysis["source_relation"] in {"odd", "unrelated"}
        and _valid_and_differs(grid, "source_mismatch")
    )


def _common_local_motif_changes_global_pose(grid) -> bool:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return False
    common = analysis["common_signature"]
    frames = [
        frame
        for frame, signature in zip(analysis["candidates"], analysis["signatures"])
        if signature == common
    ]
    return len({_global_signature(grid, frame) for frame in frames}) >= 2 and _valid_and_differs(
        grid, "absolute_global_offsets"
    )


def _equal_cardinality_kills_size_rival(grid) -> bool:
    analysis = _analysis(grid)
    return (
        not analysis["errors"]
        and len({len(signature) for signature in analysis["signatures"]}) == 1
        and _valid_and_differs(grid, "motif_size_only")
    )


SEMANTIC_WITNESSES = {
    "source_relation_breaks_source_mismatch": _source_relation_breaks_source_mismatch,
    "common_motif_multiple_global_poses": _common_local_motif_changes_global_pose,
    "equal_motif_cardinality_odd_not_first": _equal_cardinality_kills_size_rival,
    "odd_not_first": lambda grid: _valid_and_differs(grid, "always_first"),
    "odd_not_middle": lambda grid: _valid_and_differs(grid, "always_middle"),
    "odd_not_last": lambda grid: _valid_and_differs(grid, "always_last"),
}
WITNESS_RIVALS = {
    "source_relation_breaks_source_mismatch": ["source_mismatch"],
    "common_motif_multiple_global_poses": ["absolute_global_offsets"],
    "equal_motif_cardinality_odd_not_first": ["motif_size_only"],
    "odd_not_first": ["always_first"],
    "odd_not_middle": ["always_middle"],
    "odd_not_last": ["always_last"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named rival survives demos but changes the query."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    errors: list[str] = []
    survivors = set(LESSON_COMPETITORS)
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            errors.append(f"demo {index} must contain input and output grids")
            continue
        grid = demo["input"]
        if self_check(grid):
            errors.append(f"demo {index} input is outside the teaching grammar")
            continue
        authoritative = rule_mirror(grid)
        if demo["output"] != authoritative:
            errors.append(f"demo {index} output disagrees with the selected rule")
            continue
        for name, competitor in LESSON_COMPETITORS.items():
            if competitor(grid) != authoritative:
                survivors.discard(name)

    query_grid = query["input"]
    if self_check(query_grid):
        errors.append("query input is outside the teaching grammar")
        return errors
    authoritative_query = rule_mirror(query_grid)
    if "output" in query and query["output"] != authoritative_query:
        errors.append("query output disagrees with the selected rule")
    dangerous = [
        name
        for name in sorted(survivors)
        if LESSON_COMPETITORS[name](query_grid) != authoritative_query
    ]
    if dangerous:
        errors.append("demonstrations leave query-changing rival(s) alive: " + ", ".join(dangerous))
    return errors
