"""Regression contract for the 155cf6b30713 curriculum repair.

These tests encode failures observed before the repair: canonical panels were
rejected after translation-normalizing their support, generated panels were far
denser than the source task, query colors never exercised pass-through behavior,
and declared overrides/semantic claims were not executable contracts.
"""
from __future__ import annotations

from copy import deepcopy

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator
from review_diagnostics import structural_signature

TASK_ID = "155cf6b30713"
ROOT = find_root(__file__)
GEN, _SOURCE, _DIGEST = load_selected_generator(TASK_ID, root=ROOT)
BANDS = (None, "easy", "medium", "hard")
CODES = ("r1", "r2", "r3", "fh", "fv", "tr", "atr")


def _canonical_pairs():
    return canonical_pairs(TASK_ID, root=ROOT)


def _panels(grid):
    p = len(grid)
    return [
        [row[start : start + p] for row in grid]
        for start in (0, p + 1, 2 * p + 2)
    ]


def _nonzero_colors(grid):
    return {value for row in grid for value in row if value != 0}


def _pair(grid):
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_authority_pin_and_truthful_public_contract():
    assert GEN.RULE_HASH == "c4019681eb48"
    assert GEN.VERSION == "2.0.0"
    assert GEN.EXAMPLES_NEEDED == 2
    assert GEN.AXES == {
        "transform": {
            "type": "enum",
            "default": "rng",
            "valid": "r1|r2|r3|fh|fv|tr|atr",
        },
        "panel_size": {
            "type": "int",
            "default": "rng 4..6",
            "valid": "4..6",
        },
    }
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert GEN.HELPFUL_TEXTURES == ()
    assert GEN.DEGENERATE_TEXTURES == ()


def test_canonical_pairs_are_accepted_and_match_python_mirror():
    pairs = _canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_canonical_examples_have_the_exact_authority_transform_not_normalized_ties():
    assert [GEN.observe_overrides(pair["input"])["transform"] for pair in _canonical_pairs()] == [
        "fh",
        "r1",
        "tr",
    ]


@pytest.mark.parametrize("difficulty", BANDS)
def test_generated_schedule_is_sparse_canonical_profile_and_teaches_both_color_branches(difficulty):
    profiles = set()
    panel_sizes = set()
    for sample_index in range(36):
        grid = GEN.generate(20261019, sample_index, difficulty=difficulty)
        assert grid == GEN.generate(20261019, sample_index, difficulty=difficulty)
        assert GEN.self_check(grid) == []
        p = len(grid)
        assert len(grid[0]) == 3 * p + 2
        panel_sizes.add(p)
        profiles.add((p, len(grid[0]), len({value for row in grid for value in row})))

        ex_in, ex_out, query = _panels(grid)
        assert [sum(value != 0 for row in panel for value in row) for panel in (ex_in, ex_out, query)] in (
            [4, 4, 4],
            [5, 5, 5],
        )
        code, mapping = GEN.infer_relation(grid)
        assert code in CODES
        query_colors = _nonzero_colors(query)
        assert query_colors & set(mapping), "query needs at least one recolored/mapped color"
        assert query_colors - set(mapping), "query needs at least one pass-through/unmapped color"

        expected = GEN.rule_mirror(grid)
        for name, rival in GEN.LESSON_COMPETITORS.items():
            assert rival(deepcopy(grid)) != expected, (difficulty, sample_index, name)
    assert {profile[2] for profile in profiles} == {5, 8}
    assert panel_sizes == {4, 5, 6}


@pytest.mark.parametrize("difficulty", BANDS)
@pytest.mark.parametrize("panel_size", [4, 5, 6])
@pytest.mark.parametrize("transform", CODES)
def test_every_exact_override_is_honored_in_every_band(difficulty, panel_size, transform):
    requested = {"panel_size": panel_size, "transform": transform}
    grid = GEN.generate(187, 11, difficulty=difficulty, **requested)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    "args,kwargs",
    [
        ((True, 0), {}),
        ((0.0, 0), {}),
        (("0", 0), {}),
        ((0, True), {}),
        ((0, 0.0), {}),
        ((0, "0"), {}),
        ((0, -1), {}),
        ((0, 0), {"difficulty": "impossible"}),
        ((0, 0), {"typo": 1}),
        ((0, 0), {"panel_size": 3}),
        ((0, 0), {"panel_size": 7}),
        ((0, 0), {"panel_size": True}),
        ((0, 0), {"panel_size": 4.0}),
        ((0, 0), {"panel_size": "4"}),
        ((0, 0), {"transform": "id"}),
        ((0, 0), {"transform": 1}),
    ],
)
def test_invalid_scalars_unknown_axes_and_out_of_range_values_are_rejected(args, kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(*args, **kwargs)


def test_generated_structural_signatures_overlap_canonical_training_support():
    seen_five = seen_eight = False
    for sample_index in range(24):
        grid = GEN.generate(31337, sample_index, difficulty="medium")
        signature = structural_signature({"input": grid, "output": GEN.rule_mirror(grid)})
        n_colors = len({value for row in grid for value in row})
        if n_colors == 5:
            seen_five = True
            assert signature["object_count"] == 8
            assert signature["marker_count"] == 0
        elif n_colors == 8:
            seen_eight = True
            assert signature["palette_roles"] == {
                "preserved": 2,
                "introduced": 0,
                "removed": 5,
            }
        else:
            pytest.fail(f"unexpected profile with {n_colors} colors")
    assert seen_five and seen_eight


def test_declared_semantic_witnesses_and_rivals_are_executable():
    expected_rivals = {
        "identity_query",
        "transform_only",
        "recolor_only",
        "drop_unmapped",
        "unmixed_query_only",
    }
    assert set(GEN.SEMANTIC_RIVALS) == expected_rivals
    assert set(GEN.CANONICAL_SHORTCUTS) == {"unmixed_query_only"}
    assert set(GEN.LESSON_COMPETITORS) == expected_rivals

    grid = GEN.generate(23, 5, panel_size=5, transform="atr")
    expected = GEN.rule_mirror(grid)
    for witness_name, witness in GEN.SEMANTIC_WITNESSES.items():
        if not witness(grid):
            continue
        rival_names = GEN.WITNESS_RIVALS[witness_name]
        assert rival_names
        assert any(GEN.SEMANTIC_RIVALS[name](deepcopy(grid)) != expected for name in rival_names)


def test_unmixed_query_shortcut_fits_canonical_but_every_generated_pair_refutes_it():
    shortcut = GEN.CANONICAL_SHORTCUTS["unmixed_query_only"]
    assert all(shortcut(pair["input"]) == pair["output"] for pair in _canonical_pairs())
    for panel_size in (4, 5, 6):
        for sample_index in range(4):
            grid = GEN.generate(47, sample_index, panel_size=panel_size)
            assert shortcut(grid) != GEN.rule_mirror(grid)


@pytest.mark.parametrize("difficulty", BANDS)
@pytest.mark.parametrize("start", range(8))
def test_every_three_pair_window_survives_every_query_rotation(difficulty, start):
    pairs = [_pair(GEN.generate(991, start + offset, difficulty=difficulty)) for offset in range(3)]
    for query_index in range(3):
        query = pairs[query_index]
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        assert GEN.lesson_identifiable(demos, query) == []
        for name, rival in GEN.LESSON_COMPETITORS.items():
            assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                difficulty,
                start,
                query_index,
                name,
            )


@pytest.mark.parametrize(
    "bad",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 14 for _ in range(4)],
        [[10] * 14 for _ in range(4)],
        [[0] * 14 for _ in range(4)],
    ],
)
def test_malformed_grids_return_diagnostics(bad):
    errors = GEN.self_check(bad)
    assert isinstance(errors, list) and errors


def test_oracles_rivals_and_observer_do_not_mutate_inputs():
    grid = GEN.generate(22, 1)
    original = deepcopy(grid)
    GEN.rule_mirror(grid)
    GEN.observe_overrides(grid)
    for rival in GEN.SEMANTIC_RIVALS.values():
        rival(grid)
    assert grid == original


def _load_workspace_inspector():
    import importlib.util

    path = ROOT / "generators" / TASK_ID / "workspace" / "inspect_lesson.py"
    spec = importlib.util.spec_from_file_location("inspect_155cf6b30713", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_workspace_lesson_inspector_reports_replayable_branch_and_rival_evidence():
    inspector = _load_workspace_inspector()
    report = inspector.inspect_lesson(
        seed=991,
        sample_index=7,
        difficulty="hard",
        panel_size=5,
        transform="atr",
        root=ROOT,
    )
    assert report["task_id"] == TASK_ID
    assert report["generator_sha256"] == _DIGEST
    assert report["request"] == {
        "seed": 991,
        "sample_index": 7,
        "difficulty": "hard",
        "overrides": {"panel_size": 5, "transform": "atr"},
    }
    assert report["self_check_errors"] == []
    assert report["observed_overrides"] == {"panel_size": 5, "transform": "atr"}
    assert report["query_roles"]["mapped"]
    assert report["query_roles"]["unmapped"]
    assert report["query_roles"]["mixed"] is True
    assert set(report["rivals"]) == set(GEN.LESSON_COMPETITORS)
    assert all(item["refuted"] for item in report["rivals"].values())
    assert all(item["differing_cells"] > 0 for item in report["rivals"].values())


def test_retained_pre_repair_counterexamples_remain_reproducible():
    import json

    path = (
        ROOT
        / "generators"
        / TASK_ID
        / "counterexamples"
        / "review-45912c0c7cb6659e.json"
    )
    payload = json.loads(path.read_text(encoding="utf-8"))

    canonical = payload["canonical_false_rejection"]
    assert GEN.self_check(canonical["input"]) == []
    assert GEN.rule_mirror(canonical["input"]) == canonical["output"]

    mapped_only = payload["mapped_only_query"]
    _code, mapping = GEN.infer_relation(mapped_only["input"])
    query = _panels(mapped_only["input"])[2]
    query_colors = _nonzero_colors(query)
    assert query_colors
    assert query_colors <= set(mapping)
    assert not (query_colors - set(mapping))
