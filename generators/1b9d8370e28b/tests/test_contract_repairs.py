"""Focused regressions for strict call contracts and selected rule authority."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "1b9d8370e28b"
ROOT = find_root(__file__)
HOME = Path(__file__).resolve().parents[1]


def _load_generator():
    candidate = os.environ.get("GENERATOR_UNDER_TEST")
    path = Path(candidate) if candidate else HOME / "generator.py"
    name = f"generator_{TASK_ID}_{hashlib.sha256(path.read_bytes()).hexdigest()[:12]}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    programs = {
        pair["program_solution"]
        for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
        if isinstance(pair.get("program_solution"), str)
    }
    if not programs:
        # canonical_pairs intentionally returns pair rows, so read the bound
        # canonical ledger when program text is not duplicated into each pair.
        ledger = ROOT / "shared/data/canonical/puzzles.jsonl"
        with ledger.open(encoding="utf-8") as handle:
            programs = {
                row["program_solution"]
                for row in map(json.loads, handle)
                if row.get("task_id") == TASK_ID
                and isinstance(row.get("program_solution"), str)
            }
    assert len(programs) == 1
    return programs.pop()


@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1"])
def test_generate_rejects_noninteger_seed_scalars(seed):
    with pytest.raises((TypeError, ValueError), match="seed"):
        _load_generator().generate(seed, 0)


@pytest.mark.parametrize("sample_index", [True, False, 1.0, 1.75, "1", -1])
def test_generate_rejects_invalid_sample_index_scalars(sample_index):
    with pytest.raises((TypeError, ValueError), match="sample_index"):
        _load_generator().generate(20261023, sample_index)


@pytest.mark.parametrize("difficulty", [True, False, 0, 1.0, "__invalid_difficulty__"])
def test_generate_rejects_unsupported_difficulty_scalars(difficulty):
    with pytest.raises((TypeError, ValueError), match="difficulty"):
        _load_generator().generate(20261023, 0, difficulty=difficulty)


@pytest.mark.parametrize(
    ("axis", "value"),
    [
        ("grid_h", True),
        ("grid_h", "9"),
        ("grid_h", 9.0),
        ("grid_h", 8),
        ("grid_h", 16),
        ("grid_w", False),
        ("grid_w", "15"),
        ("grid_w", 15.0),
        ("grid_w", 8),
        ("grid_w", 16),
        ("split_axis", True),
        ("split_axis", 1),
        ("split_axis", "horizontal"),
        ("tl_color", True),
        ("tl_color", 1.0),
        ("tl_color", "8"),
        ("tl_color", 2),
    ],
)
def test_generate_rejects_invalid_declared_override_scalars(axis, value):
    with pytest.raises((TypeError, ValueError), match=axis):
        _load_generator().generate(20261023, 0, **{axis: value})


def test_none_overrides_remain_equivalent_to_omission():
    generator = _load_generator()
    expected = generator.generate(20261023, 3, difficulty="medium")
    actual = generator.generate(
        20261023,
        3,
        difficulty="medium",
        grid_h=None,
        grid_w=None,
        split_axis=None,
        tl_color=None,
    )
    assert actual == expected


def test_selected_target_authorities_match_canonical_and_preserve_archival_raw():
    canonical = _canonical_program()
    archival_sha256 = "2a341050fb24c1c96e87cbd385e218052904360727db710e04e3b627124fbe96"
    paths = (
        ROOT / "shared/data/base/solutions/augmented/9b4c17c4__f8ebaa2af9de.json",
        ROOT / "shared/data/base/solutions/training/9b4c17c4__1b9d8370e28b.json",
    )
    for path in paths:
        target = json.loads(path.read_text(encoding="utf-8"))["racket_target"]
        assert target["target_code"] == canonical
        assert hashlib.sha256(target["raw_code"].encode()).hexdigest() == archival_sha256
        assert target["raw_code"] != target["target_code"]
        assert target["canonicalization_status"] == (
            "selected_canonical_with_preserved_archival_raw"
        )
        assert target["target_status"] == (
            "selected_exact_canonical; archival_raw_execution_parity_required"
        )
