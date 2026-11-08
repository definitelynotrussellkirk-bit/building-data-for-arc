"""Regression for the retained marker-free morphology shortcut."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import find_root


TASK_ID = "b38ab8be5f4c"
_PRIORITY = ("ring8", "stair5", "p5", "c5", "tee4")


def _load_generator():
    root = Path(find_root(__file__))
    path = root / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location(f"review_{TASK_ID}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _shape_priority_rival(grid: list[list[int]]) -> list[list[int]]:
    """Ignore the guide marker and crop the highest-priority body morphology."""
    facts = gen._analyze(grid)
    assert not facts["errors"]
    ranked = [
        (_PRIORITY.index(obj["shape"]), obj["color"])
        for obj in facts["body_objects"].values()
        if obj["shape"] in _PRIORITY
    ]
    assert ranked
    _, color = min(ranked)
    return gen._crop_for_color(grid, color)


def test_every_four_demo_window_refutes_shape_priority_shortcut() -> None:
    # The structural role schedule has period 60 (target 20, zone 3, lesson 4).
    for band in ("easy", "medium", "hard"):
        for start in range(60):
            demos = [
                gen.generate(20261012, start + offset, difficulty=band)
                for offset in range(4)
            ]
            assert any(
                _shape_priority_rival(grid) != gen.rule_mirror(grid)
                for grid in demos
            ), (band, start)


def test_shape_priority_shortcut_is_declared_for_semantic_checks() -> None:
    rival = gen.LESSON_COMPETITORS.get("shape_priority_morphology")
    assert callable(rival)
    for index in range(4):
        grid = gen.generate(77, index, difficulty="medium")
        assert rival(grid) == _shape_priority_rival(grid)


def test_role_swapped_sample_declares_shape_priority_witness() -> None:
    witness = gen.SEMANTIC_WITNESSES.get("target_not_shape_priority")
    assert callable(witness)
    grid = gen.generate(77, 2, difficulty="medium")
    assert witness(grid) is True
    assert gen.WITNESS_RIVALS["target_not_shape_priority"] == [
        "shape_priority_morphology"
    ]


def test_shape_priority_is_tracked_as_a_canonical_shortcut() -> None:
    shortcut = gen.CANONICAL_SHORTCUTS.get("shape_priority_morphology")
    assert callable(shortcut)
    grid = gen.generate(91, 0, difficulty="easy")
    assert shortcut(grid) == _shape_priority_rival(grid)


def test_retained_role_swap_counterexample() -> None:
    root = Path(find_root(__file__))
    fixture_path = (
        root
        / "generators"
        / TASK_ID
        / "counterexamples"
        / "shape-priority-role-swap.json"
    )
    fixture = json.loads(fixture_path.read_text())
    grid = fixture["input"]
    assert gen.self_check(grid) == []
    assert gen.rule_mirror(grid) == fixture["authority_output"]
    assert _shape_priority_rival(grid) == fixture["rival_output"]
    assert fixture["authority_output"] != fixture["rival_output"]
    assert gen.SEMANTIC_WITNESSES["target_not_shape_priority"](grid) is True


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"seed": True}, "seed"),
        ({"seed": 1.0}, "seed"),
        ({"seed": "1"}, "seed"),
        ({"sample_index": True}, "sample_index"),
        ({"sample_index": 1.0}, "sample_index"),
        ({"sample_index": -1}, "sample_index"),
        ({"difficulty": True}, "difficulty"),
        ({"difficulty": 0}, "difficulty"),
        ({"difficulty": "__invalid_difficulty__"}, "difficulty"),
    ],
)
def test_generate_rejects_nonliteral_call_scalars(kwargs, message: str) -> None:
    call = {"seed": 991, "sample_index": 0, "difficulty": "easy"}
    call.update(kwargs)
    with pytest.raises((TypeError, ValueError), match=message):
        gen.generate(**call)


@pytest.mark.parametrize(
    ("axis", "value"),
    [
        ("grid_h", 8.0),
        ("grid_w", 10.0),
        ("marker_col", True),
        ("marker_col", 0.0),
        ("guide", True),
        ("guide", 1.0),
        ("target_shape", 1),
        ("target_zone", 1),
        ("bbox_intruder", 1),
    ],
)
def test_generate_rejects_nonliteral_override_scalars(axis: str, value) -> None:
    with pytest.raises((TypeError, ValueError), match=axis):
        gen.generate(991, 0, difficulty="easy", **{axis: value})
