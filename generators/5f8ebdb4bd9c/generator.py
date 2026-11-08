"""Generator for transform-analogy task 5f8ebdb4bd9c.

Each input is a 3x11 strip containing three 3x3 panels separated by zero
columns: A, B, C.  B is A after one non-identity transform from
{rotate-cw, rotate-180, flip-lr, flip-ud}.  The answer is C after that same
transform.

The canonical examples do *not* require A itself to have five distinct images;
they require the A->B relation to determine the query answer.  Generated
lessons use a stronger teaching distribution: A identifies exactly one
non-identity transform, and C has distinct images under all five oracle
transforms.  Thus fixed-transform, copy-C, copy-A, and copy-B rivals are
observable and falsifiable rather than silently fitting the corpus.
"""
from __future__ import annotations

import copy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5f8ebdb4bd9c"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "bfccb7008cc6"
SUMMARY = (
    "A 3x11 strip contains three 3x3 sparse one-color panels A, B, and C at "
    "fixed columns, separated by zero columns. B is A after one non-identity "
    "rotation/reflection from {cw, 180, flip-lr, flip-ud}; infer that relation "
    "and apply it to C. Generated A panels identify exactly one relation, C "
    "panels distinguish every candidate transform, and four consecutive "
    "examples cover all four non-identity branches."
)

ORACLE_TCODES = (0, 1, 2, 4, 5)
TCODES = (1, 2, 4, 5)
SCHEDULE_PROFILES = TCODES
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "exactly three 3x3 panels occupy columns 0..2, 4..6, and 8..10",
    "columns 3 and 7 are uniform zero separators, and each panel is a sparse zero/nonzero mask",
    "A and B use one shared nonzero color; C uses one different nonzero color",
    "at least one oracle transform maps A to B, and all matching transforms give the same C answer",
    "ordinary generated lessons use one unique non-identity A->B transform and a transform-discriminative C",
    "every four consecutive ordinary samples cover cw, 180, flip-lr, and flip-ud exactly once",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

AXES = {
    "command": {
        "type": "int",
        "default": "four-sample cyclic schedule",
        "valid": "1|2|4|5",
        "doc": "non-identity transform mapping A to B and applied to C",
    },
    "a_active_count": {
        "type": "int",
        "default": "difficulty-banded schedule",
        "valid": "3..6",
        "doc": "number of nonzero cells in panel A (and B)",
    },
    "c_active_count": {
        "type": "int",
        "default": "difficulty-banded schedule",
        "valid": "3..6",
        "doc": "number of nonzero cells in panel C",
    },
}


def _flip_lr(grid: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in grid]


def _flip_ud(grid: list[list[int]]) -> list[list[int]]:
    return grid[::-1]


def _transpose(grid: list[list[int]]) -> list[list[int]]:
    return [list(column) for column in zip(*grid)]


def _rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return _flip_lr(_transpose(grid))


def _rotate_180(grid: list[list[int]]) -> list[list[int]]:
    return _flip_ud(_flip_lr(grid))


def _apply(grid: list[list[int]], command: int) -> list[list[int]]:
    if command == 0:
        return [row[:] for row in grid]
    if command == 1:
        return _rotate_cw(grid)
    if command == 2:
        return _rotate_180(grid)
    if command == 4:
        return _flip_lr(grid)
    if command == 5:
        return _flip_ud(grid)
    raise ValueError(f"unknown transform command: {command!r}")


def _frozen(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _mask(panel: list[list[int]]) -> list[list[int]]:
    return [[int(value != 0) for value in row] for row in panel]


def _distinct_transform_images(panel: list[list[int]]) -> bool:
    return len({_frozen(_apply(panel, command)) for command in ORACLE_TCODES}) == len(
        ORACLE_TCODES
    )


def _same_transform_orbit(left: list[list[int]], right: list[list[int]]) -> bool:
    right_frozen = _frozen(right)
    return any(_frozen(_apply(left, command)) == right_frozen for command in ORACLE_TCODES)


def _normalize_band(difficulty: Any) -> str:
    if difficulty in (None, "default", "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> int:
    del seed, difficulty
    return TCODES[sample_index % len(TCODES)]


def _scheduled_count(label: str, ctx, sample_index: int, band: str, overrides: dict[str, Any]) -> int:
    if label in overrides:
        return ctx.draw_int(label, 3, 6)
    if label == "a_active_count":
        scheduled = {"easy": 3, "medium": 4 + (sample_index % 2), "hard": 6}[band]
    else:
        scheduled = {
            "easy": 3 + (sample_index % 2),
            "medium": 4 + ((sample_index + 1) % 2),
            "hard": 5 + (sample_index % 2),
        }[band]
    return ctx.draw_choice(label, [scheduled])


def _sample_panel(rng, color: int, active_count: int, *, forbidden_orbit=None) -> list[list[int]]:
    cells = [(row, col) for row in range(3) for col in range(3)]
    for _ in range(512):
        panel = full_grid(3, 3, 0)
        for row, col in rng.sample(cells, active_count):
            panel[row][col] = color
        if not _distinct_transform_images(panel):
            continue
        if forbidden_orbit is not None and _same_transform_orbit(forbidden_orbit, _mask(panel)):
            continue
        return panel
    raise ValueError(
        f"could not sample a transform-discriminative 3x3 panel with {active_count} active cells"
    )


def _assemble(a: list[list[int]], b: list[list[int]], c: list[list[int]]) -> list[list[int]]:
    grid = full_grid(3, 11, 0)
    for row in range(3):
        grid[row][0:3] = a[row][:]
        grid[row][4:7] = b[row][:]
        grid[row][8:11] = c[row][:]
    return grid


def _validate_grid(grid: Any) -> tuple[list[str], list[list[int]] | None]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or len(grid) != 3:
        return ["expected a 3x11 grid with three fixed 3x3 panels"], None
    normalized: list[list[int]] = []
    for row in grid:
        if not isinstance(row, (list, tuple)) or len(row) != 11:
            return ["expected a 3x11 grid with three fixed 3x3 panels"], None
        clean_row: list[int] = []
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append("grid colors must be integers in 0..9")
                break
            clean_row.append(value)
        normalized.append(clean_row)
    if errors:
        return errors, None
    return [], normalized


def _single_nonzero_color(panel: list[list[int]], name: str, errors: list[str]) -> int | None:
    colors = {value for row in panel for value in row if value != 0}
    if len(colors) != 1:
        errors.append(f"{name} must use exactly one nonzero motif color, found {sorted(colors)}")
        return None
    if not any(value == 0 for row in panel for value in row):
        errors.append(f"{name} must contain zero cells as part of its sparse mask")
    return next(iter(colors))


def _analyze(grid: Any) -> dict[str, Any]:
    errors, normalized = _validate_grid(grid)
    result: dict[str, Any] = {"errors": errors, "facts": {}}
    if errors or normalized is None:
        return result

    separator_values = {
        normalized[row][column]
        for row in range(3)
        for column in (3, 7)
    }
    if separator_values != {0}:
        errors.append(f"separator columns 3 and 7 must be zero, found {sorted(separator_values)}")

    a = [row[0:3] for row in normalized]
    b = [row[4:7] for row in normalized]
    c = [row[8:11] for row in normalized]
    a_color = _single_nonzero_color(a, "panel A", errors)
    b_color = _single_nonzero_color(b, "panel B", errors)
    c_color = _single_nonzero_color(c, "panel C", errors)
    if a_color is not None and b_color is not None and a_color != b_color:
        errors.append(f"panels A and B must share one motif color, got {a_color} and {b_color}")
    if a_color is not None and c_color is not None and a_color == c_color:
        errors.append("panel C must use a different motif color from panels A/B")

    matches = tuple(command for command in ORACLE_TCODES if _apply(a, command) == b)
    if not matches:
        errors.append("panel B matches no allowed transform of panel A")
    candidate_answers = tuple(_apply(c, command) for command in matches)
    answer_keys = {_frozen(answer) for answer in candidate_answers}
    if len(answer_keys) > 1:
        errors.append(
            f"A->B is answer-ambiguous: matching transforms {list(matches)} disagree on C"
        )
    if 0 in matches:
        errors.append("identity A->B is a rule-hiding no-op and is excluded from the teaching distribution")
    if a_color is not None and c_color is not None and _same_transform_orbit(_mask(a), _mask(c)):
        errors.append("panel C must not reuse panel A's transform orbit")

    facts = {
        "grid": normalized,
        "a": a,
        "b": b,
        "c": c,
        "a_color": a_color,
        "b_color": b_color,
        "c_color": c_color,
        "matches": matches,
        "command": matches[0] if len(matches) == 1 else None,
        "answer": candidate_answers[0] if candidate_answers and len(answer_keys) == 1 else None,
        "a_active_count": sum(value != 0 for row in a for value in row),
        "c_active_count": sum(value != 0 for row in c for value in row),
        "a_transform_discriminative": _distinct_transform_images(a),
        "c_transform_discriminative": _distinct_transform_images(c),
    }
    result["facts"] = facts
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    overrides = (meta or {}).get("overrides", {}) if isinstance(meta, dict) else {}
    if overrides:
        unknown = set(overrides) - set(AXES)
        if unknown:
            errors.append(f"unknown override(s): {sorted(unknown)}")
        if not errors:
            facts = analysis["facts"]
            for name in AXES:
                if name in overrides and facts[name] != int(overrides[name]):
                    errors.append(
                        f"requested {name} {int(overrides[name])}, observed {facts[name]}"
                    )
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    facts = analysis["facts"]
    if facts["command"] is None:
        raise ValueError(f"command is not uniquely observable: {facts['matches']!r}")
    return {name: int(facts[name]) for name in AXES}


def rule_mirror(grid) -> list[list[int]]:
    """Input-pure Python mirror for focused tests; Racket remains authoritative."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return copy.deepcopy(analysis["facts"]["answer"])


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    band = _normalize_band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    command = (
        ctx.draw_choice("command", TCODES)
        if "command" in overrides
        else ctx.draw_choice("command", [schedule_profile(seed, sample_index, band)])
    )
    a_active_count = _scheduled_count(
        "a_active_count", ctx, sample_index, band, overrides
    )
    c_active_count = _scheduled_count(
        "c_active_count", ctx, sample_index, band, overrides
    )

    color_rng = ctx.draw_rng("motif_colors")
    a_color, c_color = color_rng.sample(range(1, 10), 2)
    a = _sample_panel(ctx.draw_rng("panel_a"), a_color, a_active_count)
    b = _apply(a, command)
    c = _sample_panel(
        ctx.draw_rng("panel_c"),
        c_color,
        c_active_count,
        forbidden_orbit=_mask(a),
    )
    grid = _assemble(a, b, c)

    expected = {
        "command": command,
        "a_active_count": a_active_count,
        "c_active_count": c_active_count,
    }
    errors = self_check(grid)
    if errors:
        raise RuntimeError("internal construction error: " + "; ".join(errors))
    observed = observe_overrides(grid)
    if observed != expected:
        raise RuntimeError(f"internal construction mismatch: expected {expected}, observed {observed}")
    return [row[:] for row in grid]


def _fixed_transform(command: int) -> Callable[[list[list[int]]], list[list[int]]]:
    def rival(grid):
        analysis = _analyze(grid)
        if analysis["errors"]:
            raise ValueError("; ".join(analysis["errors"]))
        return _apply(analysis["facts"]["c"], command)

    return rival


def _copy_panel(name: str):
    def rival(grid):
        analysis = _analyze(grid)
        if analysis["errors"]:
            raise ValueError("; ".join(analysis["errors"]))
        return copy.deepcopy(analysis["facts"][name])

    return rival


SEMANTIC_RIVALS = {
    "copy_c_identity": _fixed_transform(0),
    "always_rotate_cw": _fixed_transform(1),
    "always_rotate_180": _fixed_transform(2),
    "always_flip_lr": _fixed_transform(4),
    "always_flip_ud": _fixed_transform(5),
    "copy_panel_a": _copy_panel("a"),
    "copy_panel_b": _copy_panel("b"),
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _command_witness(command: int):
    def witness(grid):
        analysis = _analyze(grid)
        return (
            not analysis["errors"]
            and analysis["facts"]["command"] == command
            and analysis["facts"]["c_transform_discriminative"]
        )

    return witness


SEMANTIC_WITNESSES = {
    "rotate_cw_branch": _command_witness(1),
    "rotate_180_branch": _command_witness(2),
    "flip_lr_branch": _command_witness(4),
    "flip_ud_branch": _command_witness(5),
}
WITNESS_RIVALS = {
    "rotate_cw_branch": [
        "copy_c_identity",
        "always_rotate_180",
        "always_flip_lr",
        "always_flip_ud",
        "copy_panel_a",
        "copy_panel_b",
    ],
    "rotate_180_branch": [
        "copy_c_identity",
        "always_rotate_cw",
        "always_flip_lr",
        "always_flip_ud",
        "copy_panel_a",
        "copy_panel_b",
    ],
    "flip_lr_branch": [
        "copy_c_identity",
        "always_rotate_cw",
        "always_rotate_180",
        "always_flip_ud",
        "copy_panel_a",
        "copy_panel_b",
    ],
    "flip_ud_branch": [
        "copy_c_identity",
        "always_rotate_cw",
        "always_rotate_180",
        "always_flip_lr",
        "copy_panel_a",
        "copy_panel_b",
    ],
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(f"need at least {EXAMPLES_NEEDED} demonstrations")
    commands: set[int] = set()
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        analysis = _analyze(pair["input"])
        if analysis["errors"]:
            reasons.append(f"demo {index} malformed: {analysis['errors'][0]}")
            continue
        command = analysis["facts"]["command"]
        if command is None:
            reasons.append(f"demo {index} does not identify one transform")
            continue
        commands.add(command)
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"demo {index} output disagrees with the transform analogy rule")
    if len(demos) >= EXAMPLES_NEEDED and commands != set(TCODES):
        reasons.append(f"demonstrations do not cover all four non-identity transforms: {sorted(commands)}")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not an input/output pair")
    else:
        analysis = _analyze(query["input"])
        if analysis["errors"]:
            reasons.append(f"query malformed: {analysis['errors'][0]}")
        elif "output" in query and query["output"] != rule_mirror(query["input"]):
            reasons.append("query output disagrees with the transform analogy rule")
    return reasons


def mutation_fixtures():
    base = generate(73, 0, difficulty="medium", command=1, a_active_count=4, c_active_count=5)
    analysis = _analyze(base)
    a, c = analysis["facts"]["a"], analysis["facts"]["c"]
    a_color, c_color = analysis["facts"]["a_color"], analysis["facts"]["c_color"]

    bad_separator = copy.deepcopy(base)
    bad_separator[1][3] = 9

    identity_ab = copy.deepcopy(base)
    for row in range(3):
        identity_ab[row][4:7] = a[row][:]

    wrong_relation = copy.deepcopy(base)
    wrong_relation[0][4] = c_color

    reused_orbit = copy.deepcopy(base)
    for row in range(3):
        for col in range(3):
            reused_orbit[row][8 + col] = c_color if a[row][col] else 0

    mixed_c_colors = copy.deepcopy(base)
    for row in range(3):
        for col in range(3):
            if c[row][col] != 0:
                mixed_c_colors[row][8 + col] = a_color
                break
        else:
            continue
        break

    blank = full_grid(3, 11, 0)
    return [
        ("nonzero_separator", bad_separator),
        ("identity_a_to_b", identity_ab),
        ("b_not_a_transform", wrong_relation),
        ("c_reuses_a_transform_orbit", reused_orbit),
        ("c_uses_mixed_role_colors", mixed_c_colors),
        ("blank_rule_hiding_strip", blank),
    ]
