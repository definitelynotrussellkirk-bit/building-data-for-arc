"""Unit contract for the task-local parametric Racket verifier."""
from __future__ import annotations

import importlib.util
from pathlib import Path

from reviewer_support import find_root

TASK_ID = "df3c6021b715"
ROOT = find_root(__file__)
PARAMETRIC = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
PROTOTYPE_PATH = PARAMETRIC / "prototype.py"
VERIFIER_PATH = PARAMETRIC / "verify.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_racket_callable_preserves_explicit_lambda_rule_body():
    proto = _load(PROTOTYPE_PATH, "df3_parametric_proto_for_verifier_test")
    verifier = _load(VERIFIER_PATH, "df3_parametric_verifier")
    callable_source = verifier.racket_callable(proto.program_for("horizontal"))
    assert callable_source.lstrip().startswith("(lambda (g)")
    assert "(rule!" not in callable_source


def test_racket_application_contains_grid_literal_and_one_callable():
    proto = _load(PROTOTYPE_PATH, "df3_parametric_proto_for_application_test")
    verifier = _load(VERIFIER_PATH, "df3_parametric_verifier_application")
    grid = [[0, 1], [2, 0]]
    expression = verifier.racket_application(proto.program_for("vertical"), grid)
    assert expression.count("(lambda (g)") == 1
    assert "'((0 1) (2 0))" in expression
