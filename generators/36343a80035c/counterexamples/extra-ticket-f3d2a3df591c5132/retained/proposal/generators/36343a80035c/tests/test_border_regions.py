"""Regress the retained size-only shortcut; expected labels were run in Racket."""
from __future__ import annotations

from collections import deque
import importlib.util
import json
from pathlib import Path
import random

import pytest

HOME = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("border_test_generator", HOME / "generator.py")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
WITNESS = json.loads((HOME / "counterexamples/small-region-ordered-lesson.json").read_bytes())


def border_components(grid):
    """Independent border-first flood; never invokes the generator's helpers."""
    h, w = len(grid), len(grid[0])
    seen, regions = set(), []
    for start in ((r, c) for r in range(h) for c in range(w)
                  if r in (0, h - 1) or c in (0, w - 1)):
        if start in seen or grid[start[0]][start[1]] != 0:
            continue
        pending, region = deque([start]), {start}
        seen.add(start)
        while pending:
            r, c = pending.popleft()
            for nr, nc in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 0 and (nr, nc) not in seen:
                    seen.add((nr, nc))
                    region.add((nr, nc))
                    pending.append((nr, nc))
        regions.append(region)
    return regions


def independent_output(grid):
    outside = set().union(*border_components(grid))
    return [[8 if value == 0 and (r, c) not in outside else 0
             for c, value in enumerate(row)] for r, row in enumerate(grid)]


def test_seed17_hard_demos_refute_size_only_shortcut():
    # The retained v3.1.0 lesson's demos fit the size-only shortcut. Every
    # repaired demo must contain a small exterior-region discriminator.
    for index in range(3):
        grid = gen.generate(17, index, difficulty="hard")
        assert any(len(region) <= 4 for region in border_components(grid)), index


def test_lesson_gate_flags_retained_second_query_ambiguity():
    pairs = WITNESS["pairs"]
    reasons = gen.lesson_identifiable(pairs[:3], pairs[4])
    assert any("small_zero_regions" in reason for reason in reasons), reasons


def test_lesson_gate_flags_native_four_demo_first_query_ambiguity():
    # The native default supplies four demonstrations. The extra demo also
    # fits the rival, so the same sample-4 query is ambiguous in that context.
    pairs = WITNESS["pairs"]
    reasons = gen.lesson_identifiable(pairs[:4], pairs[4])
    assert any("small_zero_regions" in reason for reason in reasons), reasons


@pytest.mark.parametrize("index", range(7))
def test_decoy_keeps_frozen_racket_answer_and_preserves_existing_witness(index):
    pair = WITNESS["pairs"][index]
    before = pair["input"]
    grid = [row[:] for row in before]
    had_witness = any(len(region) <= 4 for region in border_components(before))
    colors = sorted({v for row in before for v in row if v})
    gen._ensure_small_border_region(grid, colors[0], random.Random(0))
    assert independent_output(grid) == pair["output"]
    assert any(len(region) <= 4 for region in border_components(grid))
    assert gen.observe_overrides(grid) == gen.observe_overrides(before)
    changed = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != before[r][c]]
    if had_witness:
        assert grid == before
    else:
        assert len(changed) == 2
        assert all(before[r][c] == 0 and grid[r][c] == colors[0] for r, c in changed)
        assert all(r in (0, len(grid)-1) or c in (0, len(grid[0])-1) for r, c in changed)


@pytest.mark.parametrize("height,width", [(9, 9), (9, 14), (14, 9), (14, 14)])
@pytest.mark.parametrize("profile", gen.SCENE_PROFILES)
@pytest.mark.parametrize("palette", gen.PALETTE_KINDS)
def test_exact_axes_keep_shapes_and_old_rival_discriminators(height, width, profile, palette):
    grid = gen.generate(17, 0, difficulty="hard", grid_h=height, grid_w=width,
                        scene_profile=profile, palette_kind=palette)
    assert (len(grid), len(grid[0])) == (height, width)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == {"scene_profile": profile, "palette_kind": palette}
    assert any(len(region) <= 4 for region in border_components(grid))
    answer = independent_output(grid)
    for name, rival in gen.SEMANTIC_RIVALS.items():
        if profile == "unit_plus_tall2" and name in gen.ANCHOR_COMPATIBLE_RIVALS:
            continue
        assert rival(grid) != answer, name


def test_new_draw_remains_reproducible_and_leaves_global_rng_alone():
    random.seed(923)
    state = random.getstate()
    first = gen.generate(17, 1, difficulty="hard")
    assert random.getstate() == state
    assert gen.generate(17, 1, difficulty="hard") == first


def test_broad_grammar_does_not_require_a_teaching_decoy():
    # A valid enclosure without this witness must remain a lawful input.
    assert gen.self_check(WITNESS["pairs"][0]["input"]) == []
