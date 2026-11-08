"""Regression tests for the generator request-scalar contract."""
from __future__ import annotations

import importlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve()
_PORTABLE_ROOT = _HERE.parents[1]
if (_PORTABLE_ROOT / "data/canonical/puzzles.jsonl").is_file():
    sys.path.insert(0, str(_PORTABLE_ROOT))
    CANON_PATH = _PORTABLE_ROOT / "data/canonical/puzzles.jsonl"
    GEN = importlib.import_module("puzzle_generators.per_puzzle.5d6fcce80b6a.generator")
else:
    REPO_ROOT = _HERE.parents[3]
    CANON_PATH = REPO_ROOT / "shared/data/canonical/puzzles.jsonl"
    sys.path.insert(0, str(REPO_ROOT / "shared/runtime"))
    spec = importlib.util.spec_from_file_location(
        "generator_5d6fcce80b6a_request_contract_tests",
        REPO_ROOT / "generators/5d6fcce80b6a/generator.py",
    )
    assert spec is not None and spec.loader is not None
    GEN = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = GEN
    spec.loader.exec_module(GEN)


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, 1.75, "1", None])
def test_generate_rejects_non_integer_seed_without_coercion(bad_seed) -> None:
    with pytest.raises(TypeError, match="seed must be an integer"):
        GEN.generate(bad_seed, 0, difficulty="medium")


@pytest.mark.parametrize("bad_index", [True, False, 1.0, 1.75, "1", None])
def test_generate_rejects_non_integer_sample_index_without_coercion(bad_index) -> None:
    with pytest.raises(TypeError, match="sample_index must be a nonnegative integer"):
        GEN.generate(1, bad_index, difficulty="medium")


def test_generate_rejects_negative_sample_index() -> None:
    with pytest.raises(ValueError, match="sample_index must be a nonnegative integer"):
        GEN.generate(1, -1, difficulty="medium")


def test_declared_canonical_shortcuts_fit_every_labeled_canonical_pair() -> None:
    row = next(
        json.loads(line)
        for line in CANON_PATH.read_text().splitlines()
        if json.loads(line).get("task_id") == GEN.TASK_ID
    )
    pairs = [*row["train"], *row["test"]]
    for name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in pairs), name

    noncanonical_lesson_rivals = {
        "green_every_blank_row",
        "copy_input_to_all_four_quadrants",
    }
    assert noncanonical_lesson_rivals <= set(GEN.LESSON_COMPETITORS)
    assert noncanonical_lesson_rivals.isdisjoint(GEN.CANONICAL_SHORTCUTS)
