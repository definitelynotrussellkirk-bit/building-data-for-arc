"""Portable regression suite for ef03216cf2fa."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    canonical_counterclockwise_fit,
    canonical_pairs,
    counterclockwise_output,
    intended_output,
    load_generator,
    observed,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "train2", "test0"])
def test_accepts_and_reproduces_every_canonical_pair(pair):
    before = deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert intended_output(pair["input"]) == pair["output"]
    assert gen.rule_mirror(pair["input"]) == pair["output"]
    assert pair["input"] == before


def test_pins_rule_and_exposes_only_observable_axes():
    assert gen.RULE_HASH == "455db4f731f0"
    assert gen.EXAMPLES_NEEDED == 3
    assert set(gen.AXES) == {
        "grid_h",
        "grid_w",
        "n",
        "tall_count",
        "rank_layout",
        "palette_family",
    }
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("n,tall_count", [(3, 1), (3, 2), (4, 1), (4, 2)])
@pytest.mark.parametrize("rank_layout", ["ascending", "descending", "interleaved"])
@pytest.mark.parametrize("palette_family", ["low", "high", "mixed"])
def test_every_axis_cross_product_is_constructive_and_exact(
    band, n, tall_count, rank_layout, palette_family
):
    expected = {
        "grid_h": 10,
        "grid_w": 10,
        "n": n,
        "tall_count": tall_count,
        "rank_layout": rank_layout,
        "palette_family": palette_family,
    }
    grid = gen.generate(71, n * 100 + tall_count, difficulty=band, **expected)
    assert gen.self_check(grid) == []
    assert observed(grid) | {} == gen.observe_overrides(grid) | {
        "perimeters": observed(grid)["perimeters"],
        "colors": observed(grid)["colors"],
    }
    assert {key: observed(grid)[key] for key in expected} == expected
    assert gen.observe_overrides(grid) == expected
    assert gen.rule_mirror(grid) == intended_output(grid)


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo": 1},
        {"grid_h": 9},
        {"grid_h": 15},
        {"grid_w": 9},
        {"grid_w": 15},
        {"n": 2},
        {"n": 5},
        {"tall_count": 0},
        {"tall_count": 3},
        {"rank_layout": "random"},
        {"palette_family": "default"},
        {"grid_h": True},
        {"grid_w": 10.0},
        {"n": "3"},
        {"tall_count": 1.0},
        {"rank_layout": 7},
        {"palette_family": None},
    ],
)
def test_unknown_or_invalid_overrides_are_rejected(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **overrides)


@pytest.mark.parametrize("difficulty", ["trivial", 0.5, True])
def test_invalid_difficulty_is_rejected(difficulty):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, difficulty=difficulty)


def test_counterclockwise_rival_fits_all_canonical_pairs_but_exact_witness_disagrees():
    rival = gen.CANONICAL_SHORTCUTS["rotate_tall_counterclockwise"]
    assert canonical_counterclockwise_fit()
    assert all(rival(pair["input"]) == pair["output"] for pair in canonical_pairs())

    grid = gen.generate(
        20261008,
        17,
        grid_h=10,
        grid_w=10,
        n=3,
        tall_count=1,
        rank_layout="interleaved",
        palette_family="mixed",
    )
    assert gen.self_check(grid) == []
    assert gen.SEMANTIC_WITNESSES["clockwise_rotation_direction"](grid)
    assert intended_output(grid) != counterclockwise_output(grid)
    assert gen.rule_mirror(grid) == intended_output(grid)
    assert rival(grid) == counterclockwise_output(grid)


def test_lesson_hook_reports_surviving_counterclockwise_rival_and_accepts_generated_lesson():
    canonical = canonical_pairs()
    witness = gen.generate(
        991,
        4,
        n=4,
        tall_count=2,
        rank_layout="descending",
        palette_family="high",
    )
    query = {"input": witness, "output": intended_output(witness)}
    reasons = gen.lesson_identifiable(canonical[:3], query)
    assert any("rotate_tall_counterclockwise" in reason for reason in reasons)

    generated = []
    for index in range(4):
        grid = gen.generate(443, index, difficulty="medium")
        generated.append({"input": grid, "output": intended_output(grid)})
    assert gen.lesson_identifiable(generated[:3], generated[3]) == []


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_distribution_covers_every_declared_category_and_is_deterministic(band):
    seen_n = set()
    seen_tall = set()
    seen_layout = set()
    seen_palette = set()
    unique = set()
    for index in range(128):
        grid = gen.generate(5100 + index, index, difficulty=band)
        assert grid == gen.generate(5100 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert gen.rule_mirror(grid) == intended_output(grid)
        assert counterclockwise_output(grid) != intended_output(grid)
        stats = observed(grid)
        seen_n.add(stats["n"])
        seen_tall.add(stats["tall_count"])
        seen_layout.add(stats["rank_layout"])
        seen_palette.add(stats["palette_family"])
        unique.add(repr(grid))
    assert seen_n == {3, 4}
    assert seen_tall == {1, 2}
    assert seen_layout == {"ascending", "descending", "interleaved"}
    assert seen_palette == {"low", "high", "mixed"}
    assert len(unique) >= 120


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True, 0], [0, 0]],
        [[0, 0], [0, 0]],
        [[1, 1], [1, 1]],
    ],
)
def test_malformed_or_out_of_domain_grids_return_diagnostics(grid):
    assert gen.self_check(grid)


@pytest.mark.parametrize("mutation", ["remove_object", "reuse_color", "touch_objects", "too_many_objects"])
def test_self_check_rejects_destructive_mutations(mutation):
    grid = gen.generate(
        808,
        3,
        grid_h=10,
        grid_w=10,
        n=3,
        tall_count=1,
        rank_layout="ascending",
        palette_family="mixed",
    )
    changed = deepcopy(grid)
    objects = []
    seen = set()
    for r, row in enumerate(changed):
        for c, value in enumerate(row):
            if value and (r, c) not in seen:
                stack = [(r, c)]
                seen.add((r, c))
                cells = []
                while stack:
                    cr, cc = stack.pop()
                    cells.append((cr, cc))
                    for dr, dc in ((-1, 0), (0, -1), (0, 1), (1, 0)):
                        nr, nc = cr + dr, cc + dc
                        if (
                            0 <= nr < len(changed)
                            and 0 <= nc < len(changed[0])
                            and (nr, nc) not in seen
                            and changed[nr][nc] == value
                        ):
                            seen.add((nr, nc))
                            stack.append((nr, nc))
                objects.append((value, cells))
    if mutation == "remove_object":
        for r, c in objects[-1][1]:
            changed[r][c] = 0
    elif mutation == "reuse_color":
        old, cells = objects[-1]
        replacement = objects[0][0]
        assert old != replacement
        for r, c in cells:
            changed[r][c] = replacement
    elif mutation == "touch_objects":
        # Add a bridge of the first object's color to another occupied region.
        color, cells = objects[0]
        r, c = cells[0]
        target_r, target_c = objects[1][1][0]
        while c != target_c:
            c += 1 if target_c > c else -1
            changed[r][c] = color
        while r != target_r:
            r += 1 if target_r > r else -1
            changed[r][c] = color
    else:
        changed[5][5] = 9 if 9 not in {obj[0] for obj in objects} else 5
    assert gen.self_check(changed)


def test_canonical_perimeter_ties_remain_legal():
    pair = canonical_pairs()[1]
    assert len(set(observed(pair["input"])["perimeters"])) < observed(pair["input"])["n"]
    assert gen.self_check(pair["input"]) == []


def test_axes_metadata_is_statically_literal_for_repository_linter():
    import ast

    tree = ast.parse((HOME / "generator.py").read_text())
    assignment = next(
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "AXES" for target in node.targets)
    )
    assert not any(isinstance(node, (ast.Call, ast.Name)) for node in ast.walk(assignment.value))


def test_difficulty_bands_change_hidden_layout_without_narrowing_override_domains():
    common = {
        "grid_h": 10,
        "grid_w": 10,
        "n": 4,
        "tall_count": 2,
        "rank_layout": "interleaved",
        "palette_family": "mixed",
    }
    grids = [gen.generate(717, 11, difficulty=band, **common) for band in ("easy", "medium", "hard")]
    assert len({repr(grid) for grid in grids}) == 3
    assert all(gen.observe_overrides(grid) == common for grid in grids)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_pinned_profile_floor_has_an_exact_canonical_profile_in_every_band(band):
    import hashlib

    canonical_profiles = {(10, 10, 4), (10, 12, 4), (11, 11, 5), (12, 12, 5)}
    hits = 0
    for index in range(20):
        digest = hashlib.sha256(
            f"profile-floor:v1:{gen.TASK_ID}:{band}:{index}".encode()
        ).hexdigest()
        seed = int(digest[:12], 16)
        grid = gen.generate(seed, seed % 7919 + index, difficulty=band)
        profile = (len(grid), len(grid[0]), len({value for row in grid for value in row}))
        hits += profile in canonical_profiles
    assert hits >= 1


def test_retained_counterexample_is_reproducible_and_source_bound():
    import hashlib
    import json

    witness_dir = HOME / "counterexamples" / "review-d5c9325712268b53-counterclockwise"
    input_grid = json.loads((witness_dir / "input.json").read_text())
    rival_output = json.loads((witness_dir / "rival.json").read_text())
    probe = json.loads((witness_dir / "python_probe.json").read_text())
    racket = json.loads((witness_dir / "racket.json").read_text())

    source_sha = hashlib.sha256((HOME / "generator.py").read_bytes()).hexdigest()
    regenerated = gen.generate(
        probe["seed"],
        probe["sample_index"],
        difficulty=probe["difficulty"],
        **probe["overrides"],
    )

    assert source_sha == probe["generator_sha256"] == racket["generator_sha256"]
    assert gen.RULE_HASH == probe["rule_hash"] == racket["executed_rule_hash"]
    assert regenerated == input_grid == probe["input"] == racket["results"][0]["input"]
    assert gen.self_check(input_grid) == probe["self_check_findings"] == []
    assert gen.observe_overrides(input_grid) == probe["observed_axes"] == probe["overrides"]

    intended = intended_output(input_grid)
    rival = counterclockwise_output(input_grid)
    assert intended == gen.rule_mirror(input_grid)
    assert intended == probe["intended_python_oracle"] == racket["results"][0]["output"]
    assert rival == probe["counterclockwise_rival_output"] == rival_output
    assert probe["disagrees"] is True
    assert intended != rival
