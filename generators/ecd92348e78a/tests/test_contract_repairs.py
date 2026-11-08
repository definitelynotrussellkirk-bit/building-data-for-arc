from __future__ import annotations

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "ecd92348e78a"
ROOT = find_root(__file__)
GEN, _SOURCE, _SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
CANONICAL_PAIRS = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def _reasons(value):
    if value is True:
        return []
    if value is False:
        return ["predicate returned False"]
    return list(value)


def test_intentional_degenerate_modes_are_declared_lawful() -> None:
    assert set(GEN.LAWFUL_DEGENERATE_TEXTURES) == set(GEN.DEGENERATE_TEXTURES)


@pytest.mark.parametrize(
    ("seed", "sample_index", "difficulty", "overrides"),
    [
        (True, 0, None, {}),
        (0, "0", None, {}),
        (0, 0, 0, {}),
        (0, 0, None, {"grid_h": True}),
        (0, 0, None, {"palette_kind": 1}),
        (0, 0, None, {"position_bias": 0}),
        (0, 0, None, {"texture": 0}),
        (0, 0, None, {"__unknown_axis__": 1}),
    ],
)
def test_public_call_rejects_invalid_scalar_requests(
    seed, sample_index, difficulty, overrides
) -> None:
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(
            seed,
            sample_index,
            difficulty=difficulty,
            **overrides,
        )


def test_joint_override_conflicts_are_machine_readable() -> None:
    overrides = {
        "grid_h": 6,
        "n_colors": 5,
        "height_min": 6,
        "height_max": 10,
    }
    with pytest.raises(ValueError) as captured:
        GEN.generate(7, 11, difficulty="medium", **overrides)
    axes = set(getattr(captured.value, "incompatible_axes", ()))
    assert set(overrides) <= axes


def test_semantic_contract_accepts_canonical_and_refutes_named_rivals() -> None:
    pairs = CANONICAL_PAIRS
    assert GEN.SEMANTIC_WITNESSES
    assert GEN.SEMANTIC_RIVALS
    assert GEN.WITNESS_RIVALS

    for pair in pairs:
        grid = pair["input"]
        assert _reasons(GEN.strict_canonical_like(grid)) == []
        assert GEN.rule_mirror(grid) == pair["output"]

    for witness_name, rival_names in GEN.WITNESS_RIVALS.items():
        witness = GEN.SEMANTIC_WITNESSES[witness_name]
        assert any(
            witness(pair["input"])
            and any(
                GEN.SEMANTIC_RIVALS[rival](pair["input"]) != pair["output"]
                for rival in rival_names
            )
            for pair in pairs
        ), witness_name


def test_rule_mirror_uses_racket_grid_colors_order_for_tied_heights():
    module, _path, _sha = load_selected_generator(TASK_ID, root=find_root(__file__))
    grid = [
        [9, 0, 2],
        [9, 0, 2],
    ]

    assert module.rule_mirror(grid) == [
        [2, 9],
        [2, 9],
    ]
