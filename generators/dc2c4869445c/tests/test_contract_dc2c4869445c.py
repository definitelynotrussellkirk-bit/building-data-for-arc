"""Selected canonical generator contract regressions; no prototype approval.

Run through the packet's review.py run wrapper so the real Racket runtime is
available. These tests bind to their own source/runtime tree, not cwd.
"""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import canonical_path, find_root, load_selected_generator


ROOT = find_root(__file__)
generator, SOURCE, SOURCE_SHA256 = load_selected_generator(
    "dc2c4869445c", root=ROOT
)


@pytest.fixture(scope="module")
def canonical_rule():
    programs = {
        row["program_solution"]
        for line in canonical_path(ROOT).read_text().splitlines()
        if (row := json.loads(line)).get("task_id") == generator.TASK_ID
    }
    assert len(programs) == 1, "selected canonical rule must be unambiguous"
    # This authority is an explicit lambda with its own h/w bindings and
    # ordinary Racket for/fold forms. Peel rule! without rewriting its body.
    program = strip_rule_wrapper(programs.pop())
    assert program.startswith("(lambda (g)")
    with RacketBridge() as bridge:
        bridge.eval_text(f"(define contract-rule {program})")

        def apply(grid):
            bridge.define_grid("contract-input", grid)
            return bridge.eval_text("(contract-rule contract-input)")

        yield apply


def _call(**changes):
    args = {
        "seed": 991, "sample_index": 0, "difficulty": "hard",
        "grid_h": 18, "grid_w": 20, "n_groups": 1, "seeds_per_group": 2,
    }
    args.update(changes)
    return generator.generate(**args)


@pytest.mark.parametrize("axis", ["seed", "sample_index"])
@pytest.mark.parametrize("value", [True, False, 1.0, 1.75, "1", None])
def test_integer_call_arguments_do_not_coerce(axis, value):
    with pytest.raises((TypeError, ValueError), match=axis):
        _call(**{axis: value})


def test_negative_sample_index_rejects_but_signed_integer_seed_is_supported():
    with pytest.raises(ValueError, match="sample_index"):
        _call(sample_index=-1)
    assert generator.self_check(_call(seed=-4)) == []


@pytest.mark.parametrize("value", [True, False, 0, 1.0, "", "bogus", [], {}])
def test_difficulty_requires_a_known_band_or_none(value):
    with pytest.raises((TypeError, ValueError), match="difficulty"):
        _call(difficulty=value)


@pytest.mark.parametrize("axis,control", [
    ("grid_h", 12), ("grid_w", 12), ("n_groups", 1),
    ("seeds_per_group", 2),
])
@pytest.mark.parametrize("kind", ["bool", "string", "integral_float", "float"])
def test_numeric_overrides_are_exact_integers(axis, control, kind):
    value = {"bool": True, "string": str(control),
             "integral_float": float(control), "float": control + 0.75}[kind]
    with pytest.raises((TypeError, ValueError), match=axis):
        _call(**{axis: value})


@pytest.mark.parametrize("axis,value", [
    ("grid_h", 11), ("grid_h", 31), ("grid_w", 11), ("grid_w", 31),
    ("n_groups", 0), ("n_groups", 4),
    ("seeds_per_group", 1), ("seeds_per_group", 4),
])
def test_numeric_override_ranges_are_enforced(axis, value):
    with pytest.raises(ValueError, match=axis):
        _call(**{axis: value})


@pytest.mark.parametrize("value", [False, 0, 1.0, [], {}])
def test_texture_does_not_accept_non_string_scalars(value):
    with pytest.raises((TypeError, ValueError), match="texture"):
        _call(texture=value)


def test_unknown_override_is_rejected_even_when_its_value_is_none():
    for value in (4, None):
        with pytest.raises((TypeError, ValueError), match="unknown.*override"):
            _call(grid_heigth=value)


def test_none_keeps_declared_optional_overrides_unpinned():
    grid = generator.generate(
        0, 0, difficulty=None, grid_h=None, grid_w=None,
        n_groups=None, seeds_per_group=None, texture=None,
    )
    assert generator.self_check(grid) == []


@pytest.mark.parametrize("texture,axis,value", [
    ("one_group", "n_groups", 1), ("one_group", "n_groups", 3),
    ("single_seed", "seeds_per_group", 2),
    ("single_seed", "seeds_per_group", 3),
])
def test_exclusive_texture_controls_are_declared_and_rejected(texture, axis, value):
    declarations = getattr(generator, "INCOMPATIBLE_OVERRIDE_COMBINATIONS", ())
    assert {"texture": texture, axis: None} in declarations
    with pytest.raises(ValueError, match=f"texture={texture}.*{axis}"):
        generator.generate(0, 0, texture=texture, **{axis: value})


@pytest.mark.parametrize("band,seed,groups,seeds", [
    (None, 9, 2, 3), ("medium", 9, 2, 3),
    ("hard", 8, 3, 3), ("hard", 9, 2, 3), ("hard", 12, 3, 3),
])
def test_previously_rejected_small_layouts_are_lawful_and_racket_matches(
    canonical_rule, band, seed, groups, seeds
):
    args = dict(difficulty=band, grid_h=12, grid_w=12)
    grid = generator.generate(seed, seed * 17 + 3, **args)
    assert generator.observe_overrides(grid) == {
        "n_groups": groups, "seeds_per_group": seeds,
    }
    assert generator.self_check(grid) == []
    assert canonical_rule(grid) == generator.rule_mirror(grid)
    assert generator.generate(seed, seed * 17 + 3, **args) == grid


@pytest.mark.parametrize("seeds,texture", [
    (1, "none"), (2, "none"), (3, "none"),
    (2, "solid_main"), (3, "solid_main"),
])
def test_three_groups_fit_minimum_canvas_with_exact_seed_count(
    canonical_rule, seeds, texture
):
    overrides = {"grid_h": 12, "grid_w": 12, "n_groups": 3}
    if seeds == 1:
        overrides["texture"] = "single_seed"
    else:
        overrides.update(seeds_per_group=seeds, texture=texture)
    grid = generator.generate(8, 139, difficulty="hard", **overrides)
    assert generator.observe_overrides(grid) == {
        "n_groups": 3, "seeds_per_group": seeds,
    }
    assert generator.self_check(grid) == []
    assert canonical_rule(grid) == generator.rule_mirror(grid)


@pytest.mark.parametrize("texture", ["one_group", "single_seed", "solid_main"])
def test_declared_lawful_textures_execute_the_canonical_rule(canonical_rule, texture):
    assert texture in getattr(generator, "LAWFUL_DEGENERATE_TEXTURES", ())
    grid = generator.generate(17, 2, difficulty="medium", texture=texture)
    assert generator.self_check(grid) == []
    observed = generator.observe_overrides(grid)
    if texture == "one_group":
        assert observed["n_groups"] == 1
    elif texture == "single_seed":
        assert observed["seeds_per_group"] == 1
    else:
        for group in generator.profile_features(grid)["groups"]:
            h, w = group["main_bbox"]
            assert group["main_cells"] == h * w
    expected = canonical_rule(grid)
    assert expected == generator.rule_mirror(grid)
    assert expected != grid


def _semantic_input(*, two_groups=True, solid=False, clipped=False):
    grid = [[0] * 20 for _ in range(12)]
    rel = ([(r, c) for r in range(3) for c in range(2)] if solid
           else [(0, 0), (1, 0), (2, 0), (2, 1)])
    anchors = [(1, 1, 1, (2, 3, 4))] if clipped else [(4, 4, 1, (2, 3, 4))]
    if two_groups:
        anchors.append((4, 12, 2, (5, 6, 7)))
    for r0, c0, main, colors in anchors:
        for r, c in rel:
            grid[r0 + r][c0 + c] = main
        for (r, c), color in zip(
            [(r0 - 1, c0 - 1), (r0 - 1, c0), (r0, c0 - 1)], colors
        ):
            grid[r][c] = color
    return grid


@pytest.mark.parametrize("bad", ["x", None, [], True, 1.5, -1, 10])
def test_self_check_reports_bad_cells_without_entering_geometry(bad):
    grid = _semantic_input(two_groups=False)
    grid[4][4] = bad
    reasons = generator.self_check(grid)
    assert any("color" in reason for reason in reasons)


@pytest.mark.parametrize("witness,rival", [
    ("reflection_not_translation", "translate_copies"),
    ("local_seed_color_roles", "globally_unique_seeds"),
])
def test_semantic_witnesses_refute_named_rivals_with_racket(canonical_rule, witness, rival):
    predicates = getattr(generator, "SEMANTIC_WITNESSES", {})
    rivals = getattr(generator, "SEMANTIC_RIVALS", {})
    claims = getattr(generator, "WITNESS_RIVALS", {})
    assert witness in predicates, "finite task-domain witness must be declared"
    assert rival in rivals
    assert claims[witness] == [rival]
    grid = _semantic_input()
    before = deepcopy(grid)
    assert generator.self_check(grid) == []
    assert predicates[witness](grid) is True
    assert rivals[rival](grid) != canonical_rule(grid)
    assert grid == before, "witnesses and counterfactual rules must be pure"


def test_semantic_witnesses_do_not_claim_symmetric_or_clipped_evidence():
    predicates = getattr(generator, "SEMANTIC_WITNESSES", {})
    assert "reflection_not_translation" in predicates
    assert "local_seed_color_roles" in predicates
    symmetric = _semantic_input(two_groups=False, solid=True)
    assert generator.self_check(symmetric) == []
    assert predicates["reflection_not_translation"](symmetric) is False
    assert predicates["local_seed_color_roles"](symmetric) is False
    clipped = _semantic_input(clipped=True)
    assert "reflection block clips the grid edge" in generator.self_check(clipped)
    assert all(predicate(clipped) is False for predicate in predicates.values())


@pytest.mark.parametrize("band,expected", [
    (None, "f23822399218d02b7c94d43d76273c49719962081ae4e784785fd08766ddf388"),
    ("easy", "46e452f805dd30ab265be180d9a70f4af3564e980dbfdfe227a69621b9faa467"),
    ("medium", "f23822399218d02b7c94d43d76273c49719962081ae4e784785fd08766ddf388"),
    ("hard", "0fd47ae316dc3d562835127aac329f580ffd58ed70f955a2eed6b6e76d52d081"),
])
def test_successful_default_seed_stream_is_preserved(band, expected):
    grid = generator.generate(0, 3, difficulty=band)
    digest = hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()
    assert digest == expected
    assert generator.generate(0, 3, difficulty=band, texture="none") == grid
