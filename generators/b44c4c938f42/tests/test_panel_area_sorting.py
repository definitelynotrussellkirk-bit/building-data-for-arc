"""Regression for the panel-total-area shortcut, independent of contract helpers."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "b44c4c938f42"
gen, _, _ = load_selected_generator(TASK_ID, root=find_root(__file__))
probe_path = Path(__file__).resolve().parents[1] / "workspace" / "reference_probe.py"
spec = importlib.util.spec_from_file_location("panel_area_independent_probe", probe_path)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def total_area_output(grid):
    """Select the right objects but prioritize total panel area, then winner size."""
    panels = probe.split_panels(grid)
    records = []
    for panel in panels:
        objects = probe.components(panel)
        winner = max(objects, key=lambda obj: obj["size"])
        records.append((sum(obj["size"] for obj in objects), winner))
    records.sort(key=lambda item: (item[0], item[1]["size"]), reverse=True)
    height, width = len(grid), len(panels[0][0])
    occupied = {}
    for _, winner in records:
        for dr, dc in probe.SHIFTS:
            shifted = [(r + dr, c + dc) for r, c in winner["cells"]]
            if all(0 <= r < height and 0 <= c < width and (r, c) not in occupied
                   for r, c in shifted):
                for cell in shifted:
                    occupied[cell] = winner["color"]
                break
    return [[occupied.get((r, c), 8) for c in range(width)] for r in range(height)]


def strict_inversion(grid):
    sizes = probe.component_sizes_by_panel(grid)
    return any(a[0] > b[0] and sum(a) < sum(b) for a in sizes for b in sizes)


def test_total_area_rival_fits_every_labeled_canonical_pair():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)
    assert len(pairs) == 12
    for pair in pairs:
        assert total_area_output(pair["input"]) == pair["output"]


def test_public_racket_strict_inversion_counterexample():
    # Independently executed through `arcpuzzles apply`; retained with its hashes.
    grid = [[int(v) for v in row] for row in (
        "88881088888", "81888082288", "11188082288", "81888088888", "88888088222")]
    expected = [[int(v) for v in row] for row in (
        "88228", "81228", "11188", "81888", "88888")]
    assert gen.self_check(grid) == []
    assert strict_inversion(grid)
    assert probe.authority_output(grid) == expected
    assert total_area_output(grid) != expected


@pytest.mark.parametrize("difficulty", ("easy", "medium", "hard"))
def test_every_default_lesson_refutes_panel_total_area_under_every_holdout(difficulty):
    # This assertion fails when all panels receive one uniform distractor size.
    for seed in (40, 41, 173):
        for start in range(8):
            grids = [gen.generate(seed, start + offset, difficulty=difficulty)
                     for offset in range(4)]
            witnesses = [strict_inversion(grid) and
                         total_area_output(grid) != probe.authority_output(grid)
                         for grid in grids]
            for query_position in range(4):
                assert any(witness for index, witness in enumerate(witnesses)
                           if index != query_position), (seed, start, difficulty, query_position)


def test_mixed_default_profile_separates_rival_across_geometry_controls():
    for height in range(5, 9):
        for width in range(5, 8):
            for rotation in range(4):
                for order in ("ascending", "descending"):
                    grid = gen.generate(40, 1, difficulty="easy", grid_h=height,
                                        panel_w=width, panel_count=3,
                                        rotation=rotation, size_order=order)
                    assert strict_inversion(grid), (height, width, rotation, order)
                    assert total_area_output(grid) != probe.authority_output(grid)


@pytest.mark.parametrize("size", (1, 2))
def test_explicit_distractor_size_remains_uniform_and_exact(size):
    for difficulty in ("easy", "medium", "hard"):
        grid = gen.generate(40, 1, difficulty=difficulty, distractor_size=size)
        assert all(sizes[1] == size for sizes in probe.component_sizes_by_panel(grid))
        assert gen.observe_overrides(grid)["distractor_size"] == size


def test_canonical_shortcut_declaration_uses_real_callable():
    declared = getattr(gen, "CANONICAL_SHORTCUTS", {})
    rival = declared.get("sort_by_total_panel_area")
    assert callable(rival), "The measured canonical-fitting rival must remain executable."
    for pair in canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True):
        assert rival(pair["input"]) == pair["output"]
    assert gen.LESSON_COMPETITORS["sort_by_total_panel_area"] is rival
    assert gen.SEMANTIC_RIVALS.get("sort_by_total_panel_area") is rival
    claims = [name for name, rivals in gen.WITNESS_RIVALS.items()
              if "sort_by_total_panel_area" in rivals]
    assert claims, "The strict gate needs an executable generated-input witness."
    grid = gen.generate(40, 1, difficulty="easy")
    assert any(gen.SEMANTIC_WITNESSES[name](grid) for name in claims)
