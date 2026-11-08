#!/usr/bin/env python3
"""Task-local proposed rule variants for stacked occupancy (ARC 31d5ba1a).

The selected canonical generator and its Racket authority remain separate.
All labels here are evaluated by the included public Racket bridge.
"""
from __future__ import annotations

from dataclasses import dataclass

from arc_repl.racket_bridge import RacketBridge


@dataclass(frozen=True)
class Parameters:
    operation: str = "xor"
    output_color: int = 6

    def __post_init__(self):
        if type(self.operation) is not str or self.operation not in ("xor", "and", "or"):
            raise ValueError("operation must be xor, and, or or")
        if type(self.output_color) is not int or not 1 <= self.output_color <= 9:
            raise ValueError("output_color must be an integer in 1..9, not bool")

    def as_dict(self):
        return {"operation": self.operation, "output_color": self.output_color}


DEFAULT = Parameters()
SETTINGS = tuple(Parameters(operation, color)
                 for operation in ("xor", "and", "or") for color in range(1, 10))


def emit_program(parameters=DEFAULT):
    """Return the exact callable Racket expression used for every label."""
    if not isinstance(parameters, Parameters):
        raise ValueError("parameters must be a Parameters instance")
    predicate = {"xor": "(not (equal? upper lower))",
                 "and": "(and upper lower)", "or": "(or upper lower)"}[parameters.operation]
    return f"""(lambda (g)
  (let* ((half-h (quotient (rows g) 2))
         (width (cols g)))
    (build-grid half-h width (r c)
      (let ((upper (not (zero? (at g r c))))
            (lower (not (zero? (at g (+ r half-h) c)))))
        (if {predicate} {parameters.output_color} 0)))))
"""


def _racket_list(value):
    if isinstance(value, list):
        return "(" + " ".join(_racket_list(item) for item in value) + ")"
    if type(value) is not int or not 0 <= value <= 9:
        raise ValueError("grids must contain integer ARC colors 0..9, not bool")
    return str(value)


def execute_program(program, grids, *, bridge=None):
    """Apply an exact callable program to grids in real Racket, never Python."""
    if bridge is None:
        with RacketBridge() as owned_bridge:
            return execute_program(program, grids, bridge=owned_bridge)
    return bridge.eval_text("(map " + program + " '" + _racket_list(grids) + ")")
