"""Executable finite shortcut rivals for the projection-depth family.

Each returned value is a complete Racket rule derived from the independently
qualified dot-offset program.  The Python oracle for each name lives in
``prototype.shortcut_output``; the bounded audit executes both and requires
exact agreement before using the rival as evidence.
"""
from __future__ import annotations

NAMES = (
    "fixed_two",
    "no_exterior_bar",
    "bar_only",
    "opposite_edge_distance",
    "interior_height",
    "nearest_edge_distance",
)

_DEPTH = """(depth (if top-open
                                             (- (fst dot) fr1)
                                             (- fr2 (fst dot))))"""

_INTERIOR_FILL = """((and
                                           (> r fr1)
                                           (< r fr2)
                                           (> kc fc1)
                                           (< kc fc2)
                                           (zero? (at acc r kc))) dc)"""
_TOP_NOTCH_FILL = """((and
                                           top-open
                                           (= r fr1)
                                           (> kc fc1)
                                           (< kc fc2)
                                           (zero? v)) dc)"""
_BOTTOM_NOTCH_FILL = """((and
                                           (not top-open)
                                           (= r fr2)
                                           (> kc fc1)
                                           (< kc fc2)
                                           (zero? v)) dc)"""


def _replace_once(program: str, old: str, new: str) -> str:
    count = program.count(old)
    if count != 1:
        raise ValueError(
            f"rival source guard expected one occurrence, found {count}: {old!r}"
        )
    return program.replace(old, new, 1)


def _depth(program: str, expression: str) -> str:
    return _replace_once(program, _DEPTH, f"(depth {expression})")


def _bar_only(program: str) -> str:
    # Preserve frame detection and projection, but replace each fill branch by
    # the accumulator value it would otherwise overwrite.
    result = _replace_once(
        program,
        _INTERIOR_FILL,
        _INTERIOR_FILL[:-3] + " (at acc r kc))",
    )
    result = _replace_once(
        result,
        _TOP_NOTCH_FILL,
        _TOP_NOTCH_FILL[:-3] + " (at acc r kc))",
    )
    return _replace_once(
        result,
        _BOTTOM_NOTCH_FILL,
        _BOTTOM_NOTCH_FILL[:-3] + " (at acc r kc))",
    )


def programs(dot_offset_program: str) -> dict[str, str]:
    """Materialize guarded Racket implementations of six plausible shortcuts."""
    if type(dot_offset_program) is not str or not dot_offset_program.strip():
        raise ValueError("dot_offset_program must be nonempty Racket source")
    result = {
        "fixed_two": _depth(dot_offset_program, "2"),
        "no_exterior_bar": _depth(dot_offset_program, "0"),
        "bar_only": _bar_only(dot_offset_program),
        "opposite_edge_distance": _depth(
            dot_offset_program,
            "(if top-open\n                                             (- fr2 (fst dot))\n                                             (- (fst dot) fr1))",
        ),
        "interior_height": _depth(dot_offset_program, "(- fr2 fr1 1)"),
        "nearest_edge_distance": _depth(
            dot_offset_program,
            "(min (- (fst dot) fr1)\n                                                  (- fr2 (fst dot)))",
        ),
    }
    if set(result) != set(NAMES) or len(set(result.values())) != len(result):
        raise AssertionError("rival construction did not produce six distinct programs")
    return result
