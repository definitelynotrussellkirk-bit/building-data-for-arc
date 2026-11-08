"""Focused review repairs for generator 54628ce9692d.

The inherited ``test_generator_54628ce9692d.py`` is a frozen fixture.  These
checks cover the review changes without editing that file.
"""
from __future__ import annotations

import copy

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "54628ce9692d"
ROOT = find_root(__file__)
GENERATOR, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, 1.75, "1", None])
def test_generate_rejects_nonliteral_integer_seed(bad_seed):
    with pytest.raises(TypeError, match="seed"):
        GENERATOR.generate(bad_seed, 0)


@pytest.mark.parametrize("bad_index", [True, False, 1.0, 1.75, "1", None])
def test_generate_rejects_nonliteral_integer_sample_index(bad_index):
    with pytest.raises(TypeError, match="sample_index"):
        GENERATOR.generate(1, bad_index)


def test_generate_rejects_negative_sample_index_but_accepts_integer_seed_domain():
    with pytest.raises(ValueError, match="non-negative"):
        GENERATOR.generate(1, -1)
    assert GENERATOR.self_check(GENERATOR.generate(-1, 0)) == []


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("n_pieces", True),
        ("n_pieces", 2.0),
        ("n_pieces", "2"),
        ("background_color", False),
        ("background_color", 2.0),
        ("background_color", "2"),
    ],
)
def test_generate_rejects_nonliteral_integer_overrides(name, value):
    with pytest.raises(TypeError, match=name):
        GENERATOR.generate(1, 0, **{name: value})


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("n_pieces", 1),
        ("n_pieces", 5),
        ("background_color", 1),
        ("background_color", 10),
    ],
)
def test_generate_rejects_out_of_range_overrides(name, value):
    with pytest.raises(ValueError, match=name):
        GENERATOR.generate(1, 0, **{name: value})


def _episode():
    settings = (
        (2, 2, "easy"),
        (3, 4, "medium"),
        (4, 7, "hard"),
        (3, 9, "hard"),
    )
    pairs = []
    for index, (n_pieces, background, band) in enumerate(settings):
        grid = GENERATOR.generate(
            91_000 + index,
            137 + index,
            difficulty=band,
            n_pieces=n_pieces,
            background_color=background,
        )
        pairs.append({"input": grid, "output": GENERATOR.rule_mirror(grid)})
    return pairs[:3], pairs[3]


def test_semantic_contract_is_explicit_executable_and_nonmutating():
    assert GENERATOR.EXAMPLES_NEEDED == 3
    assert GENERATOR.MIN_STRICT_FRAC == 1.0
    assert set(GENERATOR.SEMANTIC_RIVALS) == {
        "crop_scattered_pieces",
        "one_cell_gap_docking",
    }
    assert GENERATOR.LESSON_COMPETITORS == GENERATOR.SEMANTIC_RIVALS
    assert GENERATOR.CANONICAL_SHORTCUTS == {}
    assert set(GENERATOR.SEMANTIC_WITNESSES) == {
        "pieces_require_assembly",
        "paired_markers_touch",
    }
    assert GENERATOR.WITNESS_RIVALS == {
        "pieces_require_assembly": ["crop_scattered_pieces"],
        "paired_markers_touch": ["one_cell_gap_docking"],
    }

    for index, n_pieces in enumerate((2, 3, 4, 3, 2, 4)):
        grid = GENERATOR.generate(
            50_000 + index,
            700 + index,
            difficulty=("easy", "medium", "hard")[index % 3],
            n_pieces=n_pieces,
            background_color=2 + index,
        )
        original = copy.deepcopy(grid)
        expected = GENERATOR.rule_mirror(grid)
        assert GENERATOR.strict_canonical_like(grid) == []
        assert all(
            witness(grid) is True
            for witness in GENERATOR.SEMANTIC_WITNESSES.values()
        )
        assert all(
            rival(grid) != expected
            for rival in GENERATOR.SEMANTIC_RIVALS.values()
        )
        assert grid == original


def test_lesson_identifiability_accepts_valid_episode_and_rejects_bad_labels():
    demos, query = _episode()
    assert GENERATOR.lesson_identifiable(demos, query) == []
    assert GENERATOR.lesson_identifiable(demos[:2], query) == [
        "at least 3 demonstrations are required"
    ]

    corrupted = copy.deepcopy(demos)
    corrupted[0]["output"] = copy.deepcopy(corrupted[0]["input"])
    reasons = GENERATOR.lesson_identifiable(corrupted, query)
    assert any(
        "demo 0 output differs from the selected rule" in reason
        for reason in reasons
    )


def test_canonical_inputs_are_strict_and_refute_declared_rivals():
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert pairs
    for pair in pairs:
        grid = pair["input"]
        expected = pair["output"]
        assert GENERATOR.strict_canonical_like(grid) == []
        assert GENERATOR.rule_mirror(grid) == expected
        assert all(
            rival(grid) != expected
            for rival in GENERATOR.SEMANTIC_RIVALS.values()
        )
