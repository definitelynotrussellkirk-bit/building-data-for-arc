"""gen3: take the LEFT HALF of a fully-colored grid (a SHRINK transform).

The input is a dense field made from two independently tiled halves that share
exactly the same visible palette.  The output is the left half, so the task
cannot be solved by color selection, constant fill, right-half crop, centered
crop, or mirroring.  Pair dimensions vary inside every lesson so a fixed-width
prefix crop does not survive the demonstrations either.
"""
from __future__ import annotations

from collections import Counter
import hashlib

from puzzle_generators.base import gen_ctx
from puzzle_generators.generic.concepts.dense_field import (
    parity_check,
    measure,
    make_dense_partition,
)

VERSION = "2.0.0"
TASK_ID = "generic_dense_field_gen3"
GENERATOR_ID = TASK_ID
SUMMARY = "Crop a fully colored dense field to exactly its left half."
INVARIANTS = (
    "input is a nonempty rectangular ARC grid with no background cells",
    "input width is even and output keeps all rows but exactly half the columns",
    "left and right halves expose the same visible palette but different layouts",
    "the left half is multicolor and horizontally asymmetric",
    "the centered half-width crop differs from the left-half answer",
    "every lesson varies input/output width, refuting a fixed-width prefix crop",
)
AXES = {"difficulty": ("easy", "medium", "hard")}
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0

PROGRAM = "(rule! (lambda (g) (left-half g)))"


RULE_HASH = hashlib.sha256(" ".join(PROGRAM.split()).encode("utf-8")).hexdigest()[:12]

# Deliberately disjoint dimension profiles make the one declared semantic axis
# (difficulty) observable directly from every returned input grid.  Each cycle
# has no same-height or same-width teaching adjacency, so every two-demo window varies.
_BAND_CONFIG = {
    "easy": {
        "dims": ((10, 16), (12, 10), (14, 12), (16, 14)),
        "palette": 3,
        "train": 3,
        "test": 1,
    },
    "medium": {
        "dims": ((18, 24), (20, 18), (22, 20), (24, 22)),
        "palette": 4,
        "train": 3,
        "test": 1,
    },
    "hard": {
        "dims": ((24, 30), (26, 24), (28, 26), (30, 28), (24, 26), (26, 28)),
        "palette": 4,
        "train": 4,
        "test": 2,
    },
}


def _valid_grid(g) -> bool:
    return bool(
        isinstance(g, list)
        and g
        and all(isinstance(row, list) and row for row in g)
        and len({len(row) for row in g}) == 1
        and all(
            isinstance(value, int)
            and not isinstance(value, bool)
            and 0 <= value <= 9
            for row in g
            for value in row
        )
    )


def _apply(g):
    """Python mirror of ``PROGRAM``: columns ``0 .. width/2-1``."""
    half = len(g[0]) // 2
    return [row[:half] for row in g]


def _right_half(g):
    half = len(g[0]) // 2
    return [row[half:] for row in g]


def _center_half(g):
    width = len(g[0])
    half = width // 2
    start = (width - half) // 2
    return [row[start:start + half] for row in g]


def _colors(g):
    return {value for row in g for value in row}


def _is_lr_symmetric(g):
    return all(row == row[::-1] for row in g)


def _rival_right_half(g):
    return _right_half(g)


def _rival_center_half(g):
    return _center_half(g)


def _rival_mirror_left(g):
    return [row[::-1] for row in _apply(g)]


def _rival_modal_fill(g):
    left = _apply(g)
    mode = Counter(value for row in g for value in row).most_common(1)[0][0]
    return [[mode] * len(left[0]) for _ in range(len(left))]


def _same_palette_both_halves(g) -> bool:
    return _colors(_apply(g)) == _colors(_right_half(g))


def _left_is_multicolor(g) -> bool:
    return len(_colors(_apply(g))) >= 3


def _left_right_disagree(g) -> bool:
    return _apply(g) != _right_half(g)


def _center_disagrees(g) -> bool:
    return _apply(g) != _center_half(g)


def _left_asymmetric(g) -> bool:
    return not _is_lr_symmetric(_apply(g))


SEMANTIC_WITNESSES = {
    "same_palette_both_halves": _same_palette_both_halves,
    "left_multicolor": _left_is_multicolor,
    "right_half_disagrees": _left_right_disagree,
    "center_crop_disagrees": _center_disagrees,
    "left_half_asymmetric": _left_asymmetric,
}
SEMANTIC_RIVALS = {
    "take_right_half": _rival_right_half,
    "take_center_half": _rival_center_half,
    "mirror_left_half": _rival_mirror_left,
    "emit_modal_color_block": _rival_modal_fill,
}
WITNESS_RIVALS = {
    "same_palette_both_halves": ["take_right_half"],
    "left_multicolor": ["emit_modal_color_block"],
    "right_half_disagrees": ["take_right_half"],
    "center_crop_disagrees": ["take_center_half"],
    "left_half_asymmetric": ["mirror_left_half"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _profile_band(h: int, w: int):
    matches = [
        band
        for band, config in _BAND_CONFIG.items()
        if (h, w) in config["dims"]
    ]
    return matches[0] if len(matches) == 1 else None


def strict_canonical_like(grid):
    """Return reasons when an input falls outside the left-half lesson grammar."""
    if not _valid_grid(grid):
        return ["grid must be a nonempty rectangular ARC color grid"]

    reasons = []
    h, w = len(grid), len(grid[0])
    band = _profile_band(h, w)
    if band is None:
        reasons.append("dimensions must match exactly one declared difficulty profile")
    if w % 2:
        reasons.append("input width must be even")
    if any(value == 0 for row in grid for value in row):
        reasons.append("dense-field input must not contain background 0")

    if w % 2 == 0:
        left = _apply(grid)
        right = _right_half(grid)
        left_colors = _colors(left)
        right_colors = _colors(right)
        expected_palette = _BAND_CONFIG[band]["palette"] if band else None
        if expected_palette is not None and len(left_colors) != expected_palette:
            reasons.append(
                f"left half must expose exactly {expected_palette} palette colors"
            )
        if left_colors != right_colors:
            reasons.append("left and right halves must expose the same palette")
        if len(left_colors) < 3:
            reasons.append("left-half answer must expose at least three colors")
        if left == right:
            reasons.append("right-half crop must disagree with the left-half answer")
        if _center_half(grid) == left:
            reasons.append("centered half-width crop must disagree with the answer")
        if _is_lr_symmetric(left):
            reasons.append("left-half answer must be horizontally asymmetric")
        if _rival_modal_fill(grid) == left:
            reasons.append("modal-color block rival must disagree with the answer")
    return sorted(set(reasons))


def lesson_identifiable(demos, query):
    """Require demonstrations to rule out named crops and fixed-width prefixes."""
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
            reasons.append(f"pair {index} output is not exact left-half crop")

    if reasons:
        return sorted(set(reasons))

    output_widths = {len(pair["output"][0]) for pair in demos}
    input_heights = {len(pair["input"]) for pair in demos}
    if len(output_widths) < 2:
        reasons.append("demonstrations must vary left-half output width")
    if len(input_heights) < 2:
        reasons.append("demonstrations must vary input height")

    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            suffix = (
                "and also matches the query"
                if rival(query["input"]) == query["output"]
                else "but disagrees on the query"
            )
            reasons.append(f"competitor {name} fits every demonstration {suffix}")
    return sorted(set(reasons))


def _dense_half(rng, gh, half_w, palette):
    """Dense coarse partition that exposes every palette color and is asymmetric."""
    want = set(palette)
    for _ in range(96):
        half = make_dense_partition(rng, gh, half_w, palette)
        if _colors(half) == want and not _is_lr_symmetric(half):
            return half

    # Deterministic coarse fallback: every color occupies a full rectangular
    # band, avoiding one-pixel cue artifacts while guaranteeing palette support.
    n = len(palette)
    order = list(palette)
    rng.shuffle(order)
    bounds = [round(i * gh / n) for i in range(n + 1)]
    half = [[order[-1]] * half_w for _ in range(gh)]
    for i, color in enumerate(order):
        for r in range(bounds[i], bounds[i + 1]):
            half[r] = [color] * half_w
    # Break horizontal symmetry using a full-height coarse side band.
    alt = order[1] if len(order) > 1 else order[0]
    band_w = max(1, half_w // 3)
    for r in range(gh):
        for c in range(band_w):
            half[r][c] = alt
    return half


def _make_strict_input(rng, gh, gw, palette):
    """Build a dense input that kills every named per-pair shortcut."""
    half_w = gw // 2
    for _ in range(96):
        left = _dense_half(rng, gh, half_w, palette)
        right = _dense_half(rng, gh, half_w, palette)
        grid = [left[r] + right[r] for r in range(gh)]
        if not strict_canonical_like(grid):
            return grid
    raise ValueError("could not build a shortcut-refuting dense left-half scene")


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

    palette = list(
        ctx.draw_distinct_colors(
            "palette", n=config["palette"], exclude=[0]
        )
    )
    offset = ctx.draw_int("dimension_offset", 0, len(config["dims"]) - 1)

    total_pairs = config["train"] + config["test"]
    pairs = []
    for index in range(total_pairs):
        gh, gw = config["dims"][(offset + index) % len(config["dims"])]
        rng = ctx.draw_rng(f"input_{index}")
        gin = _make_strict_input(rng, gh, gw, palette)
        pairs.append({"input": gin, "output": _apply(gin)})

    task = {
        "train": pairs[: config["train"]],
        "test": pairs[config["train"] :],
        "program": PROGRAM,
        "chain": ["left_half"],
        "difficulty": difficulty,
        "meta": {
            "difficulty": difficulty,
            "palette": palette,
            "n_train": config["train"],
            "n_test": config["test"],
            "version": VERSION,
            "rule_hash": RULE_HASH,
            "lesson_plan": "vary-dimensions-and-kill-crop-shortcuts",
        },
    }
    findings = self_check_task(task)
    if findings:
        raise AssertionError(f"generated task failed self_check_task: {findings[:3]}")
    return task


def self_check_task(task) -> list[str]:
    """Structural, semantic, lesson-level, and source-pinning checks."""
    if not isinstance(task, dict):
        return ["task must be a dictionary"]

    errors: list[str] = []
    difficulty = task.get("difficulty")
    config = _BAND_CONFIG.get(difficulty)
    if config is None:
        errors.append("task difficulty must be easy, medium, or hard")
        config = {"train": -1, "test": -1, "palette": -1, "dims": ()}

    train = list(task.get("train") or [])
    test = list(task.get("test") or [])
    if len(train) != config["train"]:
        errors.append("train pair count disagrees with the difficulty profile")
    if len(test) != config["test"]:
        errors.append("test pair count disagrees with the difficulty profile")
    if task.get("program") != PROGRAM:
        errors.append("task program must equal the selected PROGRAM authority")
    if task.get("chain") != ["left_half"]:
        errors.append("task chain must name the left_half transform")

    meta = task.get("meta") or {}
    if meta.get("version") != VERSION:
        errors.append("meta.version does not match VERSION")
    if meta.get("difficulty") != difficulty:
        errors.append("meta.difficulty disagrees with task difficulty")
    if meta.get("rule_hash") != RULE_HASH:
        errors.append("meta.rule_hash does not match RULE_HASH")
    if meta.get("n_train") != config["train"] or meta.get("n_test") != config["test"]:
        errors.append("meta pair counts disagree with the difficulty profile")
    palette = meta.get("palette")
    if not isinstance(palette, list) or len(palette) != config["palette"]:
        errors.append("meta.palette has the wrong size for the difficulty profile")
        palette = []
    elif (
        len(set(palette)) != len(palette)
        or 0 in palette
        or any(not isinstance(c, int) or isinstance(c, bool) or not 1 <= c <= 9 for c in palette)
    ):
        errors.append("meta.palette must contain distinct nonzero ARC colors")

    seen_inputs = set()
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
            if palette and _colors(gin) != set(palette):
                errors.append(f"{label}: visible colors disagree with meta.palette")

            h, w = len(gin), len(gin[0])
            if len(gout) != h or any(len(row) != w // 2 for row in gout):
                errors.append(f"{label}: output must be h x input_width/2")
                continue
            expected = _apply(gin)
            if gout != expected:
                errors.append(f"{label}: output is not exact left-half crop")
                continue
            if gout == gin:
                errors.append(f"{label}: left-half transform must shrink the grid")

            for name, witness in SEMANTIC_WITNESSES.items():
                if not witness(gin):
                    errors.append(f"{label}: missing semantic witness {name}")
            for name, rival in SEMANTIC_RIVALS.items():
                if rival(gin) == gout:
                    errors.append(f"{label}: named rival {name} still matches the answer")

    if train and test:
        for query_index, query in enumerate(test):
            for reason in lesson_identifiable(train, query):
                errors.append(f"test[{query_index}] lesson: {reason}")
    return sorted(set(errors))


if __name__ == "__main__":
    parity_check(generate_task, n=25, version_label=VERSION)
    measure(generate_task, n=25)
