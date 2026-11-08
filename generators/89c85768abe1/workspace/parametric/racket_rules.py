"""Racket programs for rectangle completion followed by component selection.

The canonical program is owned separately in ``canonical.rkt``. These programs
operate on the same zero-background, disjoint same-color rectangle grammar;
rectangles may touch. Component selection ignores foreground color and retains
the original completed colors. Equal sizes choose the first row-major component.
"""
from __future__ import annotations


_HELPERS = """
    (define (complete-corners scene)
      (for/fold ([out scene]) ([color (in-list (grid-colors scene 0))])
        (define cells (find-color scene color))
        (if (>= (length cells) 2)
            (let ([bb (bbox-of-cells cells)])
              (paint-cells out
                (positions-in-rect (first bb) (second bb) (third bb) (fourth bb))
                color))
            out)))
    (define (first-largest groups)
      (for/fold ([best '()]) ([cells (in-list groups)])
        (if (> (length cells) (length best)) cells best)))
    (define (keep-component scene cells)
      (grid-from-fn (rows scene) (cols scene)
        (lambda (r c)
          (if (member (list r c) cells) (at scene r c) 0))))
"""


def _program(expression: str) -> str:
    return "(rule! (lambda (g)\n" + _HELPERS + expression + "))"


def variant_program() -> str:
    """Complete all rectangles, then retain the largest 4-connected component."""
    # This helper groups all nonzero colors with four-neighbor connectivity.
    # objects-multicolor instead uses eight neighbors in the native prelude.
    return _program("""
    (let ([completed (complete-corners g)])
      (keep-component completed
        (first-largest (components-any-nonzero completed))))
""")


def counterfactual_program(kind: str) -> str:
    """Return one executable declared shortcut, including deterministic ties.

    ``select_before_fill`` retains the largest component of the sparse input
    before filling the retained colors. A singleton color remains that cell,
    matching the canonical completion program's treatment of singletons.
    ``largest_rectangle`` ranks separate completed color bounding boxes by area.
    ``eight_connected`` changes only the completed-grid connectivity to eight.
    """
    if kind == "select_before_fill":
        return _program("""
    (complete-corners
      (keep-component g (first-largest (components-any-nonzero g))))
""")
    if kind == "largest_rectangle":
        return _program("""
    (let* ([completed (complete-corners g)]
           [rectangles
             (for/list ([color (in-list (grid-colors g 0))])
               (define bb (bbox-of-cells (find-color g color)))
               (positions-in-rect (first bb) (second bb) (third bb) (fourth bb)))]
           [ordered
             (sort rectangles
               (lambda (a b) (cell< (first a) (first b))))])
      (keep-component completed (first-largest ordered)))
""")
    if kind == "eight_connected":
        return _program("""
    (let ([completed (complete-corners g)])
      (keep-component completed
        (first-largest (map obj-cells (objects-multicolor completed 0)))))
""")
    raise ValueError(f"Unknown counterfactual kind: {kind!r}")
