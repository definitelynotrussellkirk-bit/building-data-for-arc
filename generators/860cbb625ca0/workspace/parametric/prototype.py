#!/usr/bin/env python3
"""Episode-level exact/rotation/dihedral matching family for 860cbb625ca0.

The exact setting preserves the selected canonical Racket program byte-for-byte.
The two nearby settings expose the orientation policy already implemented by the
canonical source.  Inputs are shared across settings, but semantic stamp counts,
rows, orientations, palettes, wildcard fillings, decoys and boundaries vary by
seed so that fixed-row, mask-only and partial-orientation shortcuts are taught
away at the supported two-demonstration minimum.
"""
from __future__ import annotations

import argparse
from contextlib import nullcontext
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from typing import Any, Iterable

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    public_challenge_bytes as _public_challenge_bytes,
    public_challenge_id as _public_challenge_id,
)

TASK_ID = "860cbb625ca0"
ALLOWED_MODES = ("exact", "rotations", "dihedral")
MODE_NUMBER = {"exact": 0, "rotations": 1, "dihedral": 2}
DEFAULT_MODE = "exact"
DEFAULT_DEMOS = 3
DEFAULT_QUERIES = 4
PROTOTYPE_VERSION = "1.1.0"
ROOT = find_root(__file__)

SEQUENTIAL_DEPENDENCY = {
    "step_a": "Crop the input template and derive the episode-selected orientation variant set.",
    "intermediate": "The input-dependent ordered list of exact, rotational, or dihedral template grids.",
    "step_b": "Search the board with every grid in that list and count match starts by row.",
    "why_b_depends_on_a": (
        "The row histogram is computed from matches of the concrete variant grids; "
        "removing a derived orientation removes its board matches and changes the final strip."
    ),
}

# Symbolic templates use 0 as the canonical wildcard.  The first two samples of
# every episode are deliberately full-support then sparse, so the minimum lesson
# refutes both color-mask and zero-as-background rivals.
_TEMPLATE_BANK = (
    (
        (1, 2, 3),
        (4, 5, 6),
    ),
    (
        (1, 2, 0, 3),
        (4, 0, 5, 3),
        (4, 6, 6, 7),
    ),
    (
        (1, 2, 3),
        (4, 0, 2),
        (5, 6, 2),
        (5, 7, 7),
    ),
    (
        (1, 2, 3, 4),
        (5, 6, 3, 7),
        (5, 8, 8, 7),
    ),
)


def _validate_mode(match_mode: str) -> None:
    if type(match_mode) is not str or match_mode not in ALLOWED_MODES:
        raise ValueError(f"match_mode must be one of {ALLOWED_MODES}, got {match_mode!r}")


def _validate_seed(seed: int) -> None:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative exact integer")


def _validate_counts(demos: int, queries: int) -> None:
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be the exact integer 4")


def _validate_difficulty(difficulty: str) -> None:
    if difficulty not in {"easy", "medium", "hard"}:
        raise ValueError("difficulty must be 'easy', 'medium', or 'hard'")


def canonical_source(*, root: Path = ROOT) -> str:
    """Return the unique selected canonical Racket source for this task."""
    sources = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                source = row.get("program_solution")
                if not isinstance(source, str) or not source.strip():
                    raise ValueError(f"canonical record for {TASK_ID} has no program_solution")
                sources.append(source)
    if not sources:
        raise ValueError(f"no canonical record found for {TASK_ID}")
    unique = set(sources)
    if len(unique) != 1:
        raise ValueError(f"canonical variants for {TASK_ID} disagree on program_solution")
    return unique.pop()


def program_for(match_mode: str = DEFAULT_MODE, *, root: Path = ROOT) -> str:
    """Return exact Racket for one episode-level matching mode."""
    _validate_mode(match_mode)
    source = canonical_source(root=root)
    if match_mode == DEFAULT_MODE:
        return source
    needle = "(matches (find-matches board template 0))"
    if source.count(needle) != 1:
        raise ValueError("canonical source no longer matches the guarded mode template")
    return source.replace(
        needle,
        f"(matches (find-matches board template {MODE_NUMBER[match_mode]}))",
    )


def execute_rule(program: str, grid, *, bridge: RacketBridge | None = None):
    """Execute a complete rule through the protected Racket bridge."""
    owns_bridge = bridge is None
    active = RacketBridge() if owns_bridge else bridge
    try:
        active.define_grid("g", grid)
        return active.eval_text(f"({wrap_rule(program)} g)")
    finally:
        if owns_bridge:
            active.shutdown()


def rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def rotate_180(grid):
    return [row[::-1] for row in grid[::-1]]


def rotate_270(grid):
    return rotate_cw(rotate_180(grid))


def flip_lr(grid):
    return [row[::-1] for row in grid]


def _grid_key(grid) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def variants_for(template, match_mode: str):
    """Mirror canonical variant ordering and mode-2 de-duplication."""
    _validate_mode(match_mode)
    rotations = [
        [row[:] for row in template],
        rotate_cw(template),
        rotate_180(template),
        rotate_270(template),
    ]
    if match_mode == "exact":
        return rotations[:1]
    if match_mode == "rotations":
        return rotations
    reflected = flip_lr(template)
    candidates = rotations + [
        reflected,
        rotate_cw(reflected),
        rotate_180(reflected),
        rotate_270(reflected),
    ]
    seen = set()
    unique = []
    for candidate in candidates:
        key = _grid_key(candidate)
        if key not in seen:
            seen.add(key)
            unique.append(candidate)
    return unique


def paste_grid(target, stamp, row: int, col: int) -> None:
    """Paste a rectangular stamp in place, rejecting out-of-bounds anchors."""
    if type(row) is not int or type(col) is not int:
        raise ValueError("paste anchor must use exact integers")
    if not target or not target[0] or not stamp or not stamp[0]:
        raise ValueError("target and stamp must be nonempty")
    if any(len(line) != len(stamp[0]) for line in stamp):
        raise ValueError("stamp must be rectangular")
    if row < 0 or col < 0 or row + len(stamp) > len(target):
        raise ValueError("stamp does not fit target")
    if col + len(stamp[0]) > len(target[0]):
        raise ValueError("stamp does not fit target")
    for dr, line in enumerate(stamp):
        for dc, value in enumerate(line):
            target[row + dr][col + dc] = value


def _validate_grid(grid, *, name: str = "grid") -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError(f"{name} must be a nonempty rectangular list of rows")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError(f"{name} must be rectangular with exact integer colors 0..9")
    if len(grid) > 30 or width > 30:
        raise ValueError(f"{name} must fit within 30x30")
    return len(grid), width


def compose_input(template, board):
    """Place template and board around one full-height color-9 divider."""
    th, tw = _validate_grid(template, name="template")
    bh, bw = _validate_grid(board, name="board")
    if th > bh:
        raise ValueError("template must not be taller than board")
    if any(9 in row for row in template) or any(9 in row for row in board):
        raise ValueError("template and board must reserve color 9 for the divider")
    if tw + 1 + bw > 30:
        raise ValueError("composite input must fit within 30 columns")
    left = [[0 for _ in range(tw)] for _ in range(bh)]
    paste_grid(left, template, 0, 0)
    return [left[r] + [9] + list(board[r]) for r in range(bh)]


def _crop_nonzero(grid):
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 9)
    ]
    if not cells:
        return [[0]]
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]


def split_input(grid):
    """Split one composite input exactly as the canonical program does."""
    h, w = _validate_grid(grid, name="input")
    divider = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if len(divider) != 1:
        raise ValueError("input must contain exactly one full-height color-9 divider")
    c = divider[0]
    if c == 0 or c == w - 1:
        raise ValueError("divider must leave nonempty template and board panels")
    left = [row[:c] for row in grid]
    board = [row[c + 1 :] for row in grid]
    return _crop_nonzero(left), board


def _matches_at(board, template, row: int, col: int) -> bool:
    return all(
        value == 0 or board[row + dr][col + dc] == value
        for dr, line in enumerate(template)
        for dc, value in enumerate(line)
    )


def _strict_matches_at(board, template, row: int, col: int) -> bool:
    return all(
        board[row + dr][col + dc] == value
        for dr, line in enumerate(template)
        for dc, value in enumerate(line)
    )


def _mask_matches_at(board, template, row: int, col: int) -> bool:
    return all(
        value == 0 or board[row + dr][col + dc] != 0
        for dr, line in enumerate(template)
        for dc, value in enumerate(line)
    )


def _mirror_from_variants(grid, variants, matcher=_matches_at):
    _, board = split_input(grid)
    counts = [0 for _ in range(len(board))]
    for variant in variants:
        vh, vw = len(variant), len(variant[0])
        if vh > len(board) or vw > len(board[0]):
            continue
        for r in range(len(board) - vh + 1):
            for c in range(len(board[0]) - vw + 1):
                if matcher(board, variant, r, c):
                    counts[r] += 1
    if any(value > 9 for value in counts):
        raise ValueError("match count exceeds ARC color range")
    return [counts]


def python_mirror(grid, *, match_mode: str = DEFAULT_MODE):
    """Independent mirror of the canonical matcher; Racket remains authority."""
    _validate_mode(match_mode)
    template, _ = split_input(grid)
    return _mirror_from_variants(grid, variants_for(template, match_mode))


def match_records(grid, *, match_mode: str = DEFAULT_MODE):
    """Return the concrete input-dependent orientation/anchor intermediate."""
    _validate_mode(match_mode)
    template, board = split_input(grid)
    rows = []
    for variant_index, variant in enumerate(variants_for(template, match_mode)):
        vh, vw = len(variant), len(variant[0])
        if vh > len(board) or vw > len(board[0]):
            continue
        for r in range(len(board) - vh + 1):
            for c in range(len(board[0]) - vw + 1):
                if _matches_at(board, variant, r, c):
                    rows.append(
                        {
                            "variant_index": variant_index,
                            "row": r,
                            "col": c,
                            "shape": [vh, vw],
                        }
                    )
    return rows


def grid_sha256(grid) -> str:
    return hashlib.sha256(
        json.dumps(grid, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def normalized_program_sha256(program: str) -> str:
    return hashlib.sha256(" ".join(program.split()).encode()).hexdigest()


def select_setting(seed: int) -> str:
    _validate_seed(seed)
    digest = hashlib.sha256(f"{TASK_ID}:match-mode:{seed}".encode()).digest()
    return ALLOWED_MODES[digest[0] % len(ALLOWED_MODES)]


def _palette_template(seed: int, sample_index: int):
    symbolic = _TEMPLATE_BANK[sample_index % len(_TEMPLATE_BANK)]
    symbols = sorted({value for row in symbolic for value in row if value})
    colors = list(range(1, 9))
    digest = hashlib.sha256(
        f"{TASK_ID}:template-palette:{seed}:{sample_index}".encode()
    ).digest()
    for i in range(len(colors) - 1, 0, -1):
        j = digest[len(colors) - 1 - i] % (i + 1)
        colors[i], colors[j] = colors[j], colors[i]
    mapping = dict(zip(symbols, colors[: len(symbols)]))
    template = [[mapping.get(value, 0) for value in row] for row in symbolic]
    if len(variants_for(template, "dihedral")) != 8:
        raise AssertionError("sample template must have eight distinct dihedral variants")
    return template


def _dimensions(sample_index: int, total: int, difficulty: str) -> tuple[int, int]:
    if sample_index == total - 1:
        return 30, 30
    if difficulty == "easy":
        return 10 + 2 * (sample_index % 3), 18 + 2 * (sample_index % 4)
    if difficulty == "hard":
        return 18 + 2 * (sample_index % 5), 24 + (sample_index % 5)
    return 12 + 2 * (sample_index % 5), 20 + (sample_index % 7)


def _rect_clear(rect, placed, *, gap: int = 1) -> bool:
    r, c, h, w = rect
    for rr, cc, hh, ww in placed:
        if not (
            r + h + gap <= rr
            or rr + hh + gap <= r
            or c + w + gap <= cc
            or cc + ww + gap <= c
        ):
            return False
    return True


def _candidate_anchors(h: int, w: int, sh: int, sw: int, salt: bytes):
    anchors = [(r, c) for r in range(h - sh + 1) for c in range(w - sw + 1)]
    anchors.sort(
        key=lambda rc: hashlib.sha256(
            salt + f":{sh}:{sw}:{rc[0]}:{rc[1]}".encode()
        ).digest()
    )
    return anchors


def _boundary_preference(h: int, w: int, sh: int, sw: int, side: str, salt: bytes):
    digest = hashlib.sha256(salt + side.encode()).digest()
    if side == "top":
        return 0, int.from_bytes(digest[:4], "big") % (w - sw + 1)
    if side == "bottom":
        return h - sh, int.from_bytes(digest[:4], "big") % (w - sw + 1)
    if side == "left":
        return int.from_bytes(digest[:4], "big") % (h - sh + 1), 0
    if side == "right":
        return int.from_bytes(digest[:4], "big") % (h - sh + 1), w - sw
    raise ValueError(side)


def _place_variant(board, stamp, preferred, placed, salt: bytes):
    h, w = len(board), len(board[0])
    sh, sw = len(stamp), len(stamp[0])
    candidates = []
    for r, c in preferred:
        if 0 <= r <= h - sh and 0 <= c <= w - sw and (r, c) not in candidates:
            candidates.append((r, c))
    candidates.extend(
        anchor
        for anchor in _candidate_anchors(h, w, sh, sw, salt)
        if anchor not in candidates
    )
    for r, c in candidates:
        rect = (r, c, sh, sw)
        if _rect_clear(rect, placed):
            placed.append(rect)
            return r, c
    raise RuntimeError(f"could not place {sh}x{sw} variant on {h}x{w} board")


def _fill_color(template) -> int:
    used = {value for row in template for value in row if value}
    for color in range(1, 9):
        if color not in used:
            return color
    return 8


def _paint_semantic(board, stamp, row: int, col: int, wildcard_fill: int) -> None:
    for dr, line in enumerate(stamp):
        for dc, value in enumerate(line):
            board[row + dr][col + dc] = value if value else wildcard_fill


def _paint_near_miss(board, stamp, row: int, col: int, wildcard_fill: int, wrong_color: int) -> None:
    changed = False
    for dr, line in enumerate(stamp):
        for dc, value in enumerate(line):
            if value and not changed:
                # Full-support templates use all eight non-divider ARC colors, so
                # ``wrong_color`` can equal the first required cell.  Rotate to a
                # different nonzero color in that case; leaving the mask intact is
                # what makes this a useful color-aware near miss.
                replacement = wrong_color
                if replacement == value:
                    replacement = 1 + (value % 8)
                board[row + dr][col + dc] = replacement
                changed = True
            else:
                board[row + dr][col + dc] = value if value else wildcard_fill
    if not changed:
        raise AssertionError("near miss needs a required cell")


def _semantic_specs(seed: int, sample_index: int, stress: bool):
    digest = hashlib.sha256(f"{TASK_ID}:semantic-counts:{seed}:{sample_index}".encode()).digest()
    exact_count = 3 if stress else 1 + digest[0] % 2
    rotation_count = 4 if stress else 2 + digest[1] % 2
    reflection_count = 4 if stress else 2 + digest[2] % 2
    specs = []
    for index in range(exact_count):
        specs.append(("exact", 0))
    rotation_indices = (1, 2, 3)
    for index in range(rotation_count):
        specs.append(("rotation_only", rotation_indices[index % len(rotation_indices)]))
    reflection_indices = (4, 5, 6, 7)
    for index in range(reflection_count):
        specs.append(("reflection_only", reflection_indices[index % len(reflection_indices)]))
    specs.sort(
        key=lambda row: hashlib.sha256(
            f"{TASK_ID}:semantic-order:{seed}:{sample_index}:{row[0]}:{row[1]}:{specs.count(row)}".encode()
        ).digest()
    )
    # The sort key above deliberately avoids global RNG; equal duplicate specs are
    # still semantically interchangeable.
    return specs


def _build_input_attempt(seed: int, sample_index: int, total: int, difficulty: str, attempt: int):
    h, total_w = _dimensions(sample_index, total, difficulty)
    template = _palette_template(seed, sample_index)
    board_w = total_w - len(template[0]) - 1
    board = [[0 for _ in range(board_w)] for _ in range(h)]
    all_variants = variants_for(template, "dihedral")
    stress = (h, total_w) == (30, 30)
    specs = _semantic_specs(seed + 1009 * attempt, sample_index, stress)
    placed = []
    placements = []
    wildcard_fill = _fill_color(template)
    sides = ("top", "bottom", "left", "right") if stress else ()

    for index, (category, variant_index) in enumerate(specs):
        stamp = all_variants[variant_index]
        salt = hashlib.sha256(
            f"{TASK_ID}:place:{seed}:{sample_index}:{attempt}:{index}:{category}:{variant_index}".encode()
        ).digest()
        preferred = []
        if index < len(sides):
            preferred.append(
                _boundary_preference(
                    h, board_w, len(stamp), len(stamp[0]), sides[index], salt
                )
            )
        row, col = _place_variant(board, stamp, preferred, placed, salt)
        _paint_semantic(board, stamp, row, col, wildcard_fill)
        placements.append(
            {
                "category": category,
                "variant_index": variant_index,
                "row": row,
                "col": col,
                "shape": [len(stamp), len(stamp[0])],
            }
        )

    near_misses = []
    miss_count = 3 if stress else 1
    # Reuse the wildcard fill as the wrong required-cell color.  It is
    # guaranteed absent from the template, while sparse seven-color templates
    # leave no second unused ARC color.
    wrong_color = wildcard_fill
    for index in range(miss_count):
        variant_index = (2 + index * 3) % 8
        stamp = all_variants[variant_index]
        salt = hashlib.sha256(
            f"{TASK_ID}:near-miss:{seed}:{sample_index}:{attempt}:{index}".encode()
        ).digest()
        row, col = _place_variant(board, stamp, [], placed, salt)
        _paint_near_miss(board, stamp, row, col, wildcard_fill, wrong_color)
        near_misses.append(
            {
                "variant_index": variant_index,
                "row": row,
                "col": col,
                "shape": [len(stamp), len(stamp[0])],
            }
        )

    # Isolated nuisance cells challenge component/frequency shortcuts without
    # creating a full semantic window.  Failed exact-record checks below reject
    # any accidental match.
    salt = hashlib.sha256(f"{TASK_ID}:clutter:{seed}:{sample_index}:{attempt}".encode()).digest()
    clutter_target = 10 if stress else 2 + sample_index % 4
    clutter = 0
    for r, c in _candidate_anchors(h, board_w, 1, 1, salt):
        if board[r][c] != 0:
            continue
        if any(
            0 <= r + dr < h
            and 0 <= c + dc < board_w
            and board[r + dr][c + dc] != 0
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
        ):
            continue
        board[r][c] = wildcard_fill
        clutter += 1
        if clutter == clutter_target:
            break

    composite = compose_input(template, board)
    expected_by_mode = {
        "exact": {(p["variant_index"], p["row"], p["col"]) for p in placements if p["variant_index"] == 0},
        "rotations": {(p["variant_index"], p["row"], p["col"]) for p in placements if p["variant_index"] <= 3},
        "dihedral": {(p["variant_index"], p["row"], p["col"]) for p in placements},
    }
    records_by_mode = {}
    row_histograms = {}
    for mode in ALLOWED_MODES:
        records = match_records(composite, match_mode=mode)
        actual = {(r["variant_index"], r["row"], r["col"]) for r in records}
        if actual != expected_by_mode[mode]:
            raise AssertionError(f"unexpected {mode} matches: expected={expected_by_mode[mode]}, actual={actual}")
        records_by_mode[mode] = records
        row_histograms[mode] = python_mirror(composite, match_mode=mode)[0]
        if python_mirror(composite, match_mode=mode) == fixed_row_shortcut(composite, match_mode=mode):
            raise AssertionError(f"retained fixed-row shortcut for {mode}")

    if len({_grid_key([row_histograms[mode]]) for mode in ALLOWED_MODES}) != len(ALLOWED_MODES):
        raise AssertionError("constructed input does not distinguish all match modes")
    if stress:
        occupied = [(r, c) for r, row in enumerate(board) for c, value in enumerate(row) if value]
        rows = {r for r, _ in occupied}
        cols = {c for _, c in occupied}
        if not (
            len(occupied) >= 70
            and min(rows) == 0
            and max(rows) == h - 1
            and min(cols) == 0
            and max(cols) == board_w - 1
            and len(rows) >= 12
            and len(cols) >= 12
        ):
            raise AssertionError("30x30 stress content did not span the board substantively")

    return {
        "grid": composite,
        "input_sha256": grid_sha256(composite),
        "sample_index": sample_index,
        "shape": [len(composite), len(composite[0])],
        "stamp_anchors": [[p["row"], p["col"]] for p in placements],
        "semantic_placements": placements,
        "near_misses": near_misses,
        "row_histograms": row_histograms,
        "match_records": records_by_mode,
    }


def _build_input(seed: int, sample_index: int, total: int, difficulty: str):
    for attempt in range(64):
        try:
            return _build_input_attempt(seed, sample_index, total, difficulty, attempt)
        except (AssertionError, RuntimeError, StopIteration):
            continue
    raise RuntimeError(
        f"could not construct a shortcut-resistant input for seed={seed} sample={sample_index}"
    )


def _sample_inputs(seed: int, total: int, difficulty: str):
    samples = [_build_input(seed, index, total, difficulty) for index in range(total)]
    hashes = [row["input_sha256"] for row in samples]
    if len(set(hashes)) != len(hashes):
        raise AssertionError("parametric sampler emitted duplicate visible inputs")
    return samples


def fixed_row_shortcut(grid, *, match_mode: str):
    """The fixed-corner shortcut admitted by prototype 1.0.0."""
    _validate_mode(match_mode)
    template, board = split_input(grid)
    counts = [0 for _ in range(len(board))]
    counts[0] = 1 if match_mode == "exact" else 2
    if match_mode == "dihedral":
        counts[len(board) - len(template)] += 1
    return [counts]


def _mask_only(grid, match_mode: str):
    template, _ = split_input(grid)
    return _mirror_from_variants(
        grid, variants_for(template, match_mode), matcher=_mask_matches_at
    )


def _zero_is_background(grid, match_mode: str):
    template, _ = split_input(grid)
    return _mirror_from_variants(
        grid, variants_for(template, match_mode), matcher=_strict_matches_at
    )


def _partial_intermediate(grid, match_mode: str):
    template, _ = split_input(grid)
    variants = variants_for(template, match_mode)
    if match_mode == "rotations":
        variants = variants[:2]
    elif match_mode == "dihedral":
        variants = variants[:5]
    return _mirror_from_variants(grid, variants)


def rival_diagnostics(episode: dict[str, Any]):
    """Score plausible shortcuts on one private episode; all must miss a demo."""
    if type(episode) is not dict or type(episode.get("parameters")) is not dict:
        raise ValueError("episode must contain private parameters")
    mode = episode["parameters"].get("match_mode")
    _validate_mode(mode)
    solvers = {
        "fixed_row": lambda grid: fixed_row_shortcut(grid, match_mode=mode),
        "mask_only": lambda grid: _mask_only(grid, mode),
        "zero_is_background": lambda grid: _zero_is_background(grid, mode),
    }
    if mode != "exact":
        solvers["partial_intermediate"] = lambda grid: _partial_intermediate(grid, mode)
    def score_pairs(pairs, solve):
        mismatches = []
        errors = []
        for index, pair in enumerate(pairs):
            try:
                predicted = solve(pair["input"])
            except (AssertionError, RuntimeError, ValueError) as exc:
                # A shortcut that cannot emit a legal ARC grid on a visible
                # example is refuted just as decisively as one that emits the
                # wrong grid.  Preserve the failure for the evidence report.
                mismatches.append(index)
                errors.append({
                    "index": index,
                    "type": type(exc).__name__,
                    "message": str(exc),
                })
            else:
                if predicted != pair["output"]:
                    mismatches.append(index)
        return mismatches, errors

    rows = []
    for name, solve in solvers.items():
        demo_mismatches, demo_errors = score_pairs(episode["train"], solve)
        query_mismatches, query_errors = score_pairs(episode["test"], solve)
        rows.append(
            {
                "name": name,
                "demonstration_mismatch_indices": demo_mismatches,
                "query_mismatch_indices": query_mismatches,
                "demonstration_error_records": demo_errors,
                "query_error_records": query_errors,
                "status": "refuted_by_demonstrations" if demo_mismatches else "survived_demonstrations",
            }
        )
    return rows


def recolor_input(grid, *, salt: int):
    """Apply a deterministic bijection to every visible nonzero/non-divider color."""
    if type(salt) is not int:
        raise ValueError("salt must be an exact integer")
    _validate_grid(grid, name="input")
    used = sorted({value for row in grid for value in row if value not in (0, 9)})
    if not used:
        raise ValueError("input has no recolorable colors")
    ranked = sorted(
        range(1, 9),
        key=lambda color: hashlib.sha256(f"{TASK_ID}:recolor:{salt}:{color}".encode()).digest(),
    )
    chosen = ranked[: len(used)]
    if chosen == used:
        chosen = chosen[1:] + chosen[:1]
    mapping = dict(zip(used, chosen))
    return [
        [mapping.get(value, value) for value in row]
        for row in grid
    ]


def _generator_identity(root: Path) -> dict[str, str]:
    path = Path(root) / "generators" / TASK_ID / "generator.py"
    if not path.is_file():
        manifest = Path(root) / "RUNTIME_MANIFEST.json"
        if not manifest.is_file():
            raise FileNotFoundError(path)
        rows = json.loads(manifest.read_text()).get("files", [])
        matches = [
            row
            for row in rows
            if row.get("library_path") == f"generators/{TASK_ID}/generator.py"
        ]
        selected = [row for row in matches if row.get("runtime_path") != row.get("library_path")]
        matches = selected or matches
        if len(matches) != 1:
            raise ValueError("could not resolve one selected generator source")
        path = Path(root) / matches[0]["runtime_path"]
    body = path.read_bytes()
    return {
        "generator_path": str(path.relative_to(root)),
        "generator_sha256": hashlib.sha256(body).hexdigest(),
    }


def generate_claims(
    seed: int,
    *,
    match_mode: str,
    difficulty: str = "medium",
    demos: int = DEFAULT_DEMOS,
    queries: int = DEFAULT_QUERIES,
    root: Path = ROOT,
) -> dict[str, Any]:
    """Build deterministic Python claims for independent protected replay."""
    _validate_seed(seed)
    _validate_mode(match_mode)
    _validate_counts(demos, queries)
    _validate_difficulty(difficulty)
    samples = _sample_inputs(seed, demos + queries, difficulty)
    pairs = [
        {
            "input": row["grid"],
            "output": python_mirror(row["grid"], match_mode=match_mode),
        }
        for row in samples
    ]
    return {
        "train": pairs[:demos],
        "test": pairs[demos:],
        "program_solution": program_for(match_mode, root=root),
    }


def make_episode_family(
    seed: int,
    *,
    difficulty: str = "medium",
    demos: int = DEFAULT_DEMOS,
    queries: int = DEFAULT_QUERIES,
    root: Path = ROOT,
    bridge: RacketBridge | None = None,
) -> dict[str, dict[str, Any]]:
    """Build all three private episodes while replaying each input only once."""
    _validate_seed(seed)
    _validate_counts(demos, queries)
    _validate_difficulty(difficulty)
    samples = _sample_inputs(seed, demos + queries, difficulty)
    programs = {mode: program_for(mode, root=root) for mode in ALLOWED_MODES}
    outputs = {mode: [] for mode in ALLOWED_MODES}

    owns_bridge = bridge is None
    active = RacketBridge() if owns_bridge else bridge
    try:
        for row in samples:
            for mode in ALLOWED_MODES:
                output = execute_rule(programs[mode], row["grid"], bridge=active)
                mirror = python_mirror(row["grid"], match_mode=mode)
                if output != mirror:
                    raise AssertionError(f"Racket/Python parity failed for match_mode={mode}")
                outputs[mode].append(output)
    finally:
        if owns_bridge:
            active.shutdown()

    source = _generator_identity(root)
    family = {}
    for mode in ALLOWED_MODES:
        pairs = [
            {"input": row["grid"], "output": outputs[mode][index]}
            for index, row in enumerate(samples)
        ]
        rivals = []
        ambiguities = []
        for rival in ALLOWED_MODES:
            if rival == mode:
                continue
            demo_mismatches = [
                index
                for index in range(demos)
                if outputs[mode][index] != outputs[rival][index]
            ]
            query_mismatches = [
                index
                for index in range(queries)
                if outputs[mode][demos + index] != outputs[rival][demos + index]
            ]
            status = "refuted_by_demonstrations" if demo_mismatches else "ambiguous_query"
            rivals.append(
                {
                    "match_mode": rival,
                    "status": status,
                    "demonstration_mismatch_indices": demo_mismatches,
                    "query_mismatch_indices": query_mismatches,
                }
            )
            if not demo_mismatches:
                ambiguities.append({"match_mode": rival, "reason": status})
        program = programs[mode]
        family[mode] = {
            "schema": "arcpuzzles-proposed-parametric-episode-v1",
            "status": "proposed_unapproved",
            "approved": False,
            "task_id": TASK_ID,
            "prototype_version": PROTOTYPE_VERSION,
            "parameters": {"match_mode": mode},
            "seed": seed,
            "difficulty": difficulty,
            "train": pairs[:demos],
            "test": pairs[demos:],
            "program": program,
            "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
            "normalized_program_sha256": normalized_program_sha256(program),
            "selection_scope": "once_per_episode",
            "sampling": [
                {
                    key: row[key]
                    for key in (
                        "input_sha256",
                        "sample_index",
                        "shape",
                        "stamp_anchors",
                        "semantic_placements",
                        "near_misses",
                        "row_histograms",
                        "match_records",
                    )
                }
                for row in samples
            ],
            "parameter_rivals": rivals,
            "ambiguities": ambiguities,
            "source": source,
        }
        family[mode]["shortcut_rivals"] = rival_diagnostics(family[mode])
        survivors = [
            row["name"]
            for row in family[mode]["shortcut_rivals"]
            if row["status"] != "refuted_by_demonstrations"
        ]
        if survivors:
            raise AssertionError(
                f"shortcut rivals survived the demonstrations for {mode}: {survivors}"
            )
    return family


def make_episode(
    seed: int,
    *,
    match_mode: str | None = None,
    difficulty: str = "medium",
    demos: int = DEFAULT_DEMOS,
    queries: int = DEFAULT_QUERIES,
    root: Path = ROOT,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    selected = select_setting(seed) if match_mode is None else match_mode
    _validate_mode(selected)
    return make_episode_family(
        seed,
        difficulty=difficulty,
        demos=demos,
        queries=queries,
        root=root,
        bridge=bridge,
    )[selected]


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    return json.loads(_public_challenge_bytes(episode))


def public_bytes(episode: dict[str, Any]) -> bytes:
    return _public_challenge_bytes(episode)


def public_id(episode: dict[str, Any]) -> str:
    return _public_challenge_id(episode)


def first_turn_bytes(episode: dict[str, Any]) -> bytes:
    """Visible bytes before any query answer: demos plus only query 0."""
    if not isinstance(episode, dict) or type(episode.get("test")) is not list or not episode["test"]:
        raise ValueError("episode must contain at least one query")
    return _public_challenge_bytes(
        {"train": episode.get("train"), "test": [episode["test"][0]]}
    )


def first_turn_id(episode: dict[str, Any]) -> str:
    return hashlib.sha256(first_turn_bytes(episode)).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_evidence(
    *,
    seed: int,
    out: Path,
    root: Path = ROOT,
    difficulty: str = "medium",
    demos: int = DEFAULT_DEMOS,
    queries: int = DEFAULT_QUERIES,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Atomically write source-bound public/private evidence for all modes."""
    _validate_seed(seed)
    _validate_counts(demos, queries)
    _validate_difficulty(difficulty)
    out = Path(out)
    if out.exists():
        raise FileExistsError(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=f".{out.name}.tmp-", dir=out.parent))
    try:
        bridge_context = RacketBridge() if bridge is None else nullcontext(bridge)
        with bridge_context as active:
            runtime_identity = active.runtime_identity
            canonical_program = program_for(DEFAULT_MODE, root=root)
            canonical_rows = []
            for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
                actual = execute_rule(canonical_program, pair["input"], bridge=active)
                canonical_rows.append(
                    {
                        "variant": pair["variant"],
                        "split": pair["split"],
                        "pair_index": pair["pair_index"],
                        "input_sha256": grid_sha256(pair["input"]),
                        "expected_output_sha256": grid_sha256(pair["output"]),
                        "actual_output_sha256": grid_sha256(actual),
                        "matches": actual == pair["output"],
                    }
                )
            if not canonical_rows or not all(row["matches"] for row in canonical_rows):
                raise AssertionError("canonical exact program failed a labelled canonical pair")

            family = make_episode_family(
                seed,
                difficulty=difficulty,
                demos=demos,
                queries=queries,
                root=root,
                bridge=active,
            )

        pending_public = []
        episode_rows = []
        distinct_inputs = set()
        for mode in ALLOWED_MODES:
            episode = family[mode]
            rule_rel = Path("private/rules") / f"match-{mode}.rkt"
            private_rel = Path("private") / f"episode-{mode}.json"
            rule_path = temp / rule_rel
            rule_path.parent.mkdir(parents=True, exist_ok=True)
            rule_path.write_text(episode["program"], encoding="utf-8")
            private = dict(episode)
            private["racket_path"] = rule_rel.as_posix()
            private["racket_sha256"] = _file_sha256(rule_path)
            _write_json(temp / private_rel, private)

            visible_bytes = public_bytes(private)
            visible_id = public_id(private)
            pending_public.append(
                {
                    "mode": mode,
                    "id": visible_id,
                    "bytes": visible_bytes,
                    "private": private,
                    "private_rel": private_rel,
                    "rule_rel": rule_rel,
                }
            )
            distinct_inputs.update(
                grid_sha256(pair["input"])
                for pair in private["train"] + private["test"]
            )

        public_ids = [row["id"] for row in pending_public]
        if len(set(public_ids)) != len(public_ids):
            raise ValueError("duplicate public challenge id")
        for row in pending_public:
            if row["id"] != hashlib.sha256(row["bytes"]).hexdigest():
                raise ValueError("public identifier does not hash the exact visible bytes")

        for row in sorted(pending_public, key=lambda item: item["id"]):
            public_rel = Path("public") / f"challenge-{row['id']}.json"
            public_path = temp / public_rel
            public_path.parent.mkdir(parents=True, exist_ok=True)
            public_path.write_bytes(row["bytes"])
            private = row["private"]
            episode_rows.append(
                {
                    "match_mode": row["mode"],
                    "public_id": row["id"],
                    "public_path": public_rel.as_posix(),
                    "private_path": row["private_rel"].as_posix(),
                    "racket_path": row["rule_rel"].as_posix(),
                    "first_turn_id": first_turn_id(private),
                    "program_sha256": private["program_sha256"],
                    "ambiguous_parameter_rivals": len(private["ambiguities"]),
                    "shortcut_rivals_refuted": sum(
                        row["status"] == "refuted_by_demonstrations"
                        for row in private["shortcut_rivals"]
                    ),
                    "shortcut_rivals_survived": sum(
                        row["status"] != "refuted_by_demonstrations"
                        for row in private["shortcut_rivals"]
                    ),
                }
            )

        shortcut_rows = [
            row
            for mode in ALLOWED_MODES
            for row in family[mode]["shortcut_rivals"]
        ]
        canonical_sampling = family[DEFAULT_MODE]["sampling"]
        report = {
            "schema": "arcpuzzles-parametric-evidence-report-v1",
            "status": "proposed_unapproved",
            "approved": False,
            "task_id": TASK_ID,
            "prototype_version": PROTOTYPE_VERSION,
            "parameter": {
                "name": "match_mode",
                "allowed_values": list(ALLOWED_MODES),
                "original_default": DEFAULT_MODE,
                "selection_scope": "once_per_episode",
                "input_constraints_depend_on_parameter": False,
            },
            "seed": seed,
            "difficulty": difficulty,
            "runtime_identity": runtime_identity,
            "canonical_replay": canonical_rows,
            "episodes": sorted(episode_rows, key=lambda row: row["match_mode"]),
            "counts": {
                "episodes": len(ALLOWED_MODES),
                "train_pairs": demos * len(ALLOWED_MODES),
                "query_pairs": queries * len(ALLOWED_MODES),
                "distinct_input_grids": len(distinct_inputs),
                "canonical_pairs_checked": len(canonical_rows),
                "ambiguous_parameter_rivals": sum(
                    len(family[mode]["ambiguities"]) for mode in ALLOWED_MODES
                ),
                "shortcut_rivals_checked": len(shortcut_rows),
                "shortcut_rivals_refuted": sum(
                    row["status"] == "refuted_by_demonstrations"
                    for row in shortcut_rows
                ),
                "semantic_placements": sum(
                    len(row["semantic_placements"]) for row in canonical_sampling
                ),
                "near_misses": sum(
                    len(row["near_misses"]) for row in canonical_sampling
                ),
            },
        }
        _write_json(temp / "report.json", report)

        manifest_rows = []
        for path in sorted(temp.rglob("*")):
            if path.is_file():
                manifest_rows.append(
                    {
                        "path": path.relative_to(temp).as_posix(),
                        "sha256": _file_sha256(path),
                        "bytes": path.stat().st_size,
                    }
                )
        _write_json(
            temp / "manifest.json",
            {
                "schema": "arcpuzzles-parametric-evidence-manifest-v1",
                "task_id": TASK_ID,
                "files": manifest_rows,
            },
        )
        temp.replace(out)
        return report
    except BaseException:
        shutil.rmtree(temp, ignore_errors=True)
        raise


def main(argv: Iterable[str] | None = None, *, bridge: RacketBridge | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"), default="medium")
    parser.add_argument("--demos", type=int, default=DEFAULT_DEMOS)
    parser.add_argument("--queries", type=int, default=DEFAULT_QUERIES)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(list(argv) if argv is not None else None)
    write_evidence(
        seed=args.seed,
        out=args.out,
        difficulty=args.difficulty,
        demos=args.demos,
        queries=args.queries,
        bridge=bridge,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
