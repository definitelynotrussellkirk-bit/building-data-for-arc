"""Finite, executable shortcut rivals for the frame/crop alignment family.

Python predictions guard constructive sampling; qualification must execute the
separately materialized Racket rivals. Majority ties use the first wall color
encountered from top to bottom. This finite set is not an identifiability proof
against arbitrary programs.
"""
from __future__ import annotations

from collections import Counter

NAMES = (
    "always_direct", "always_mirror", "mirror_ties", "first_row",
    "edge_columns", "left_only", "right_only", "majority_walls",
    "last_wall_colors", "uniform_walls",
)


def _replace_once(program: str, old: str, new: str) -> str:
    count = program.count(old)
    if count != 1:
        raise ValueError(f"rival source guard expected one occurrence, found {count}: {old!r}")
    return program.replace(old, new, 1)


def _majority_expression(column: str) -> str:
    return (
        "(let ((vs (map (lambda (r) (at g r " + column + ")) "
        "(range (+ r0 1) r1)))) "
        "(let loop ((pending vs) (best (first vs)) (best-count -1)) "
        "(if (empty? pending) best "
        "(let* ((v (first pending)) "
        "(n (count-if (lambda (x) (= x v)) vs))) "
        "(if (> n best-count) (loop (rest pending) v n) "
        "(loop (rest pending) best best-count))))))"
    )


def programs(base_program: str) -> dict[str, str]:
    """Mutate one selected-setting program without changing its other logic."""
    finals = {op: f"(let ((flip? ({op} (score #t) (score #f))))" for op in (">", "<")}
    found = [op for op, text in finals.items() if text in base_program]
    if len(found) != 1:
        raise ValueError("expected exactly one match/contrast final comparison")
    op = found[0]
    final = finals[op]
    result = {
        "always_direct": _replace_once(base_program, final, "(let ((flip? #f))"),
        "always_mirror": _replace_once(base_program, final, "(let ((flip? #t))"),
        "mirror_ties": _replace_once(base_program, final, finals[op].replace(op + " (score", op + "= (score", 1)),
    }
    for name, predicate in (
        ("first_row", "(zero? (fst off))"),
        ("edge_columns", "(or (zero? (snd off)) (= (snd off) (- iw 1)))"),
    ):
        result[name] = _replace_once(
            base_program, "                           offsets))",
            "                           (filter (lambda (off) " + predicate + ") offsets)))",
        )
    result["left_only"] = _replace_once(
        base_program, "(and (>= dc (quotient (+ iw 1) 2)) (= v right))",
        "(and #f (>= dc (quotient (+ iw 1) 2)) (= v right))",
    )
    result["right_only"] = _replace_once(
        base_program, "(and (< dc (quotient iw 2)) (= v left))",
        "(and #f (< dc (quotient iw 2)) (= v left))",
    )
    for name in ("majority_walls", "last_wall_colors"):
        program = base_program
        for side, column in (("left", "cL"), ("right", "cR")):
            expression = _majority_expression(column) if name == "majority_walls" else f"(at g (- r1 1) {column})"
            program = _replace_once(program, f"({side} (at g (+ r0 1) {column}))", f"({side} {expression})")
        result[name] = program
    uniform = base_program
    for condition, side, column in (("(zero? c)", "left", "cL"), ("(= c (- ow 1))", "right", "cR")):
        uniform = _replace_once(
            uniform, f"({condition} (at g (+ r0 r) {column}))",
            f"({condition} (if (or (zero? r) (= r (- oh 1))) (at g (+ r0 r) {column}) {side}))",
        )
    result["uniform_walls"] = uniform
    assert tuple(result) == NAMES
    return result


def predict(facts: dict, name: str, alignment: str) -> list[list[int]]:
    """Predict one rival from recovered canonical geometry and input values."""
    if name not in NAMES:
        raise ValueError(f"unknown rival: {name!r}")
    if alignment not in ("match", "contrast"):
        raise ValueError(f"unknown alignment: {alignment!r}")
    crop = facts["crop"]
    ih, iw = len(crop), len(crop[0])
    left, right = facts["left_color"], facts["right_color"]
    left_wall, right_wall = facts["left_wall"], facts["right_wall"]
    if name == "majority_walls":
        left = Counter(left_wall[1:-1]).most_common(1)[0][0]
        right = Counter(right_wall[1:-1]).most_common(1)[0][0]
    elif name == "last_wall_colors":
        left, right = left_wall[-2], right_wall[-2]

    def score(flipped: bool) -> int:
        total = 0
        for r, row in enumerate(crop):
            for c in range(iw):
                if name == "first_row" and r != 0:
                    continue
                if name == "edge_columns" and c not in (0, iw - 1):
                    continue
                value = row[iw - 1 - c if flipped else c]
                total += bool(
                    (name != "right_only" and c < iw // 2 and value == left)
                    or (name != "left_only" and c >= (iw + 1) // 2 and value == right)
                )
        return total

    direct, reflected = score(False), score(True)
    flip = reflected > direct if alignment == "match" else reflected < direct
    if name == "always_direct":
        flip = False
    elif name == "always_mirror":
        flip = True
    elif name == "mirror_ties" and reflected == direct:
        flip = True
    output = [[0] * (iw + 2) for _ in range(ih + 2)]
    for r in range(ih + 2):
        output[r][0], output[r][-1] = left_wall[r], right_wall[r]
        if 0 < r < ih + 1:
            output[r][1:-1] = list(reversed(crop[r - 1])) if flip else list(crop[r - 1])
            if name == "uniform_walls":
                output[r][0], output[r][-1] = left, right
    return output
