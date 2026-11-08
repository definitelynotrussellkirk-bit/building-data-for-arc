"""Independent literal fixtures for the protected Racket reference.

Expected outputs are hand-authored. No sampler, family or Python rule is used.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
TASK = ROOT / "generators" / "public_eval_58f5dbd5"


def rows(*lines):
    return [[int(value) for value in line] for line in lines]


RECTANGULAR_DISCONNECTED = rows(
    "00000000000000",
    "02000000000000",
    "00002000000000",
    "00000002222220",
    "00000002222220",
    "05500002222220",
    "00550002222220",
    "00000000000000",
    "00000000000000",
)
RECTANGULAR_CARVE = rows(
    "00000000",
    "02222220",
    "02022220",
    "02222020",
    "02222220",
    "00000000",
)
RECTANGULAR_STAMP = rows(
    "00000000",
    "02222220",
    "02200020",
    "02000220",
    "02222220",
    "00000000",
)

ADJACENT_REVERSED_SOURCES = rows(
    "888888888888888888",
    "833888880000833338",
    "883888880000833338",
    "888888880000833338",
    "808888880000833338",
    "880888888888888888",
    "888888888888888888",
    "888888888888888888",
)
ADJACENT_CARVE = rows(
    "88888888888",
    "80000833338",
    "80800838838",
    "80080833838",
    "80000833338",
    "88888888888",
)

FULL_RECTANGLE_TEMPLATE = rows(
    "111111111111111",
    "166661111111111",
    "166661116666661",
    "166661116666661",
    "166661116666661",
    "111111116666661",
    "111111116666661",
    "111111116666661",
    "111111111111111",
    "111111111111111",
)
FULL_RECTANGLE_CARVE = rows(
    "11111111",
    "16666661",
    "16111161",
    "16111161",
    "16111161",
    "16111161",
    "16666661",
    "11111111",
)


@pytest.fixture(scope="module")
def execute():
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator

    runtime = ROOT / "shared" / "runtime"
    with _local_imports(runtime, TASK / "workspace" / "parametric"):
        apply_program, identity, bridge = _real_evaluator(runtime)
        assert identity["backend"] == "racket" and identity["protected"] is True
        try:
            yield apply_program
        finally:
            bridge.close()


def source():
    path = TASK / "reference.rkt"
    assert path.is_file(), "A complete task-local Racket reference is required"
    return path.read_text()


@pytest.mark.parametrize(
    "grid, expected",
    [
        (RECTANGULAR_DISCONNECTED, RECTANGULAR_CARVE),
        (ADJACENT_REVERSED_SOURCES, ADJACENT_CARVE),
        (FULL_RECTANGLE_TEMPLATE, FULL_RECTANGLE_CARVE),
    ],
    ids=[
        "rectangular-disconnected-and-unselected-decoy",
        "color-association-zero-foreground-and-one-cell-gutter",
        "large-filled-template-is-not-a-target",
    ],
)
def test_reference_hand_fixtures(execute, grid, expected):
    assert execute(source(), grid) == expected


def test_stamp_variant_keeps_positive_template_cells(execute):
    stamp = source().replace("(define ink-mode 'carve)", "(define ink-mode 'stamp)")
    assert execute(stamp, RECTANGULAR_DISCONNECTED) == RECTANGULAR_STAMP


def test_reading_order_rival_is_distinguished_by_color_association(execute):
    rival = source().replace(
        "(define association-mode 'color)",
        "(define association-mode 'reading-order)",
    )
    assert execute(rival, ADJACENT_REVERSED_SOURCES) != ADJACENT_CARVE


def test_every_original_training_and_test_label(execute):
    raw = ROOT / "shared" / "data" / "raw"
    task = json.loads((raw / "arc-agi_evaluation_challenges.json").read_text())["58f5dbd5"]
    gold = json.loads((raw / "arc-agi_evaluation_solutions.json").read_text())["58f5dbd5"]
    assert len(gold) == len(task["test"])
    pairs = task["train"] + [
        {"input": pair["input"], "output": expected}
        for pair, expected in zip(task["test"], gold)
    ]
    for index, pair in enumerate(pairs):
        assert execute(source(), pair["input"]) == pair["output"], index


def test_selected_canonical_is_byte_identical_to_reference():
    reference = source().encode()
    assert (TASK / "workspace" / "parametric" / "canonical.rkt").read_bytes() == reference
