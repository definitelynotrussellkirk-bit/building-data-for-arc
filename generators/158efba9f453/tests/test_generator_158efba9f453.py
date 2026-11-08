from __future__ import annotations

import copy
import random

import pytest
from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "158efba9f453"
ROOT = find_root(__file__)
GEN, _SOURCE_PATH, _SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def _canonical_pairs():
    return canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def test_canonical_inputs_are_accepted_and_mirror_exactly():
    pairs = _canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize(
    "overrides",
    [
        {
            "grid_h": 7,
            "grid_w": 9,
            "n_motifs": 1,
            "source_side": "left",
            "axis_zone": "left",
            "axis_overlap": False,
            "marker_profile": "outer",
        },
        {
            "grid_h": 12,
            "grid_w": 15,
            "n_motifs": 3,
            "source_side": "right",
            "axis_zone": "right",
            "axis_overlap": True,
            "marker_profile": "inset",
        },
        {
            "grid_h": 9,
            "grid_w": 13,
            "n_motifs": 2,
            "source_side": "left",
            "axis_zone": "center",
            "axis_overlap": True,
            "marker_profile": "mixed",
        },
    ],
)
def test_exact_override_boundaries_are_observable(overrides):
    grid = GEN.generate(20260724, 17, difficulty="hard", **overrides)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == overrides
    assert GEN.rule_mirror(grid) != grid


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(918273)
    before = random.getstate()
    first = GEN.generate(41, 9, difficulty="medium")
    after = random.getstate()
    second = GEN.generate(41, 9, difficulty="medium")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert GEN.generate(41, 9, difficulty="medium") == second


@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1"])
def test_generate_rejects_non_integer_seed(seed):
    with pytest.raises(TypeError, match="seed"):
        GEN.generate(seed, 0)


@pytest.mark.parametrize("sample_index", [True, False, 1.0, 1.75, "1"])
def test_generate_rejects_non_integer_sample_index(sample_index):
    with pytest.raises(TypeError, match="sample_index"):
        GEN.generate(991, sample_index)


def test_generate_rejects_negative_sample_index():
    with pytest.raises(ValueError, match="sample_index"):
        GEN.generate(991, -1)


@pytest.mark.parametrize(
    ("axis", "value"),
    [
        ("grid_h", "7"),
        ("grid_h", 7.0),
        ("grid_w", "9"),
        ("grid_w", 9.0),
        ("n_motifs", True),
        ("n_motifs", "2"),
        ("n_motifs", 2.0),
        ("axis_overlap", 0),
        ("axis_overlap", 1),
    ],
)
def test_generate_rejects_wrong_scalar_types_for_overrides(axis, value):
    with pytest.raises(TypeError, match=axis):
        GEN.generate(991, 0, **{axis: value})


def test_self_check_rejects_targeted_structural_impostors():
    base = GEN.generate(
        71,
        12,
        difficulty="medium",
        grid_h=9,
        grid_w=13,
        n_motifs=2,
        source_side="left",
        axis_zone="center",
        axis_overlap=False,
        marker_profile="outer",
    )
    markers = [(r, c) for r, row in enumerate(base) for c, value in enumerate(row) if value == 5]
    axis = markers[0][1]
    motif_cells = [(r, c) for r, row in enumerate(base) for c, value in enumerate(row) if value not in (0, 5)]

    one_marker = copy.deepcopy(base)
    one_marker[markers[0][0]][markers[0][1]] = 0

    split_axis = copy.deepcopy(base)
    r, c = markers[0]
    split_axis[r][c] = 0
    split_axis[r][c - 1] = 5

    both_sides = copy.deepcopy(base)
    r, c = motif_cells[0]
    both_sides[r][2 * axis - c] = both_sides[r][c]

    axis_only = [[0 for _ in row] for row in base]
    for r, c in markers:
        axis_only[r][c] = 5
    axis_only[len(base) // 2][axis] = 4

    disconnected_color = copy.deepcopy(base)
    color = disconnected_color[motif_cells[0][0]][motif_cells[0][1]]
    disconnected_color[len(base) // 2][axis - 1] = color

    impostors = {
        "one_marker": one_marker,
        "split_axis": split_axis,
        "already_mirrored": both_sides,
        "axis_only_identity": axis_only,
        "disconnected_color": disconnected_color,
    }
    for name, grid in impostors.items():
        assert GEN.self_check(grid), name


def test_three_consecutive_demos_eliminate_declared_shortcuts():
    for start in range(12):
        demos = []
        for sample_index in range(start, start + GEN.EXAMPLES_NEEDED):
            inp = GEN.generate(991, sample_index)
            demos.append({"input": inp, "output": GEN.rule_mirror(inp)})
        query_input = GEN.generate(991, start + GEN.EXAMPLES_NEEDED)
        query = {"input": query_input, "output": GEN.rule_mirror(query_input)}
        assert GEN.lesson_identifiable(demos, query) == []


def test_left_source_only_is_a_canonical_fitting_shortcut_with_generated_counterexample():
    rival = GEN.CANONICAL_SHORTCUTS["left_source_only"]
    assert all(rival(pair["input"]) == pair["output"] for pair in _canonical_pairs())

    witness = GEN.generate(
        20261013,
        5,
        difficulty="hard",
        grid_h=9,
        grid_w=13,
        n_motifs=2,
        source_side="right",
        axis_zone="center",
        axis_overlap=True,
        marker_profile="mixed",
    )
    assert GEN.observe_overrides(witness)["source_side"] == "right"
    assert rival(witness) == witness
    assert rival(witness) != GEN.rule_mirror(witness)


def test_lesson_identifiable_reports_left_source_only_survivor():
    demos = []
    for sample_index in range(3):
        inp = GEN.generate(
            4242,
            sample_index,
            source_side="left",
            n_motifs=2,
            axis_overlap=bool(sample_index % 2),
        )
        demos.append({"input": inp, "output": GEN.rule_mirror(inp)})
    query_input = GEN.generate(4242, 3, source_side="right", n_motifs=2)
    query = {"input": query_input, "output": GEN.rule_mirror(query_input)}

    reasons = GEN.lesson_identifiable(demos, query)
    assert any("left_source_only" in reason for reason in reasons)

def test_semantic_contract_binds_every_witness_to_an_executable_rival():
    assert set(GEN.SEMANTIC_WITNESSES) == set(GEN.WITNESS_RIVALS)
    for witness_name, rival_names in GEN.WITNESS_RIVALS.items():
        assert rival_names, witness_name
        assert all(name in GEN.SEMANTIC_RIVALS for name in rival_names)

    witness = GEN.generate(
        20261013,
        5,
        difficulty="hard",
        grid_h=9,
        grid_w=13,
        n_motifs=2,
        source_side="right",
        axis_zone="center",
        axis_overlap=True,
        marker_profile="mixed",
    )
    assert GEN.SEMANTIC_WITNESSES["source_right"](witness)
    assert GEN.SEMANTIC_RIVALS["left_source_only"](witness) != GEN.rule_mirror(witness)
