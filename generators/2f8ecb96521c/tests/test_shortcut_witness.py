"""Regression for the canonical-fitting row-projection shortcut witness."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

from reviewer_support import find_root

TASK_ID = "2f8ecb96521c"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    canonical_pairs,
    row_projection_rival,
    rule_output,
)

WITNESS_PATH = HOME / "counterexamples" / "row_projection_canonical_fit.json"


def _load_generator():
    path = HOME / "generator.py"
    spec = importlib.util.spec_from_file_location("shortcut_witness_generator", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_retained_row_projection_witness_is_canonical_fitting_and_generated():
    assert WITNESS_PATH.is_file(), f"missing retained witness: {WITNESS_PATH}"
    witness = json.loads(WITNESS_PATH.read_text(encoding="utf-8"))
    generator = _load_generator()

    training = [pair for pair in canonical_pairs() if pair["split"] == "train"]
    assert len(training) == 2
    assert all(row_projection_rival(pair["input"]) == pair["output"] for pair in training)
    assert witness["canonical_training_fit"] == [True, True]

    generated = generator.generate(
        witness["generation"]["seed"],
        witness["generation"]["sample_index"],
        difficulty=witness["generation"]["difficulty"],
    )
    assert generated == witness["input"]
    assert generator.self_check(generated) == []
    assert generator.observe_overrides(generated)["layout"] == "side_by_side"

    intended = rule_output(generated)
    rival = row_projection_rival(generated)
    assert intended == witness["selected_racket_output"]
    assert rival == witness["row_projection_output"]
    assert rival != intended
    assert witness["generator_emits_witness"] is True
