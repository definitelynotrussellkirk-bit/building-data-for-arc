"""Review regressions; runnable directly in the library or a staged runtime."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

TASK_ID = "c2b9484357c1"
HERE = Path(__file__).resolve()
REPO = next((p for p in HERE.parents if (p / "shared/runtime").is_dir()), None)
if REPO is not None:
    sys.path.insert(0, str(REPO / "shared/runtime"))
    SOURCE = REPO / "generators" / TASK_ID / "generator.py"
else:
    ROOT = next(p for p in HERE.parents if (p / "puzzle_generators").is_dir())
    sys.path.insert(0, str(ROOT))
    SOURCE = ROOT / "puzzle_generators/per_puzzle" / TASK_ID / "generator.py"
spec = importlib.util.spec_from_file_location("c2b9484357c1_review_subject", SOURCE)
assert spec is not None and spec.loader is not None
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def shape_key(grid):
    """Forget color, canvas, placement and each component's D4 orientation."""
    def key(cells):
        variants = []
        for swap in (False, True):
            for sr in (-1, 1):
                for sc in (-1, 1):
                    points = [(sr * (c if swap else r), sc * (r if swap else c))
                              for r, c in cells]
                    r0 = min(r for r, _ in points)
                    c0 = min(c for _, c in points)
                    variants.append(tuple(sorted((r-r0, c-c0) for r, c in points)))
        return min(variants)
    return tuple(sorted(key(obj["cells"]) for obj in gen._scene(grid)))


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_lesson_requires_filling_multiple_holes(band):
    for seed in (0, 17, 4901):
        grids = [gen.generate(seed, i, difficulty=band)
                 for i in range(gen.EXAMPLES_NEEDED)]
        assert any(len(gen._largest_hollow(gen._scene(g))["holes"]) == 2
                   for g in grids), (band, seed, "no multi-hole winner")


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_bbox_conflict_requires_cell_count_not_outer_perimeter(band):
    grid = gen.generate(17, 3, difficulty=band, scene_profile="bbox_area_conflict",
                        grid_h=8, grid_w=9, solid_decoy=True)
    scene = gen._scene(grid)
    target = gen._largest_hollow(scene)
    rival = next(o for o in gen._hollows(scene) if o is not target)
    def outline(o):
        r0, c0, r1, c1 = o["bbox"]
        return 2 * (r1-r0+1 + c1-c0+1) - 4
    assert target["size"] > rival["size"]
    assert target["bbox_area"] < rival["bbox_area"]
    assert outline(target) < outline(rival), "outer-perimeter shortcut still wins"
    assert len(target["holes"]) == 2
    out = gen._true_output(grid)
    assert all(out[r][c] == target["color"] for hole in target["holes"] for r, c in hole)
    assert all(out[r][c] == grid[r][c] for r in range(len(grid))
               for c in range(len(grid[0])) if (r, c) not in target["hole_cells"])


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_noncosmetic_geometry_diversity(band):
    keys = {shape_key(gen.generate(seed, i, difficulty=band))
            for seed in range(16) for i in range(gen.EXAMPLES_NEEDED)}
    assert len(keys) >= 8, (band, len(keys), "only cosmetic template variation")


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("height", [8, 12])
@pytest.mark.parametrize("width", [9, 14])
@pytest.mark.parametrize("profile", gen.SCENE_PROFILES)
@pytest.mark.parametrize("solid", [False, True])
@pytest.mark.parametrize("palette", gen.PALETTE_KINDS)
def test_full_boundary_override_cross_product(band, height, width, profile, solid, palette):
    grid = gen.generate(29, 9, difficulty=band, grid_h=height, grid_w=width,
                        scene_profile=profile, solid_decoy=solid, palette_kind=palette)
    assert (len(grid), len(grid[0])) == (height, width)
    assert gen.observe_overrides(grid) == {
        'scene_profile': profile, 'solid_decoy': solid, 'palette_kind': palette}
    assert gen.self_check(grid) == []
    # Preserve the positive comparison witness after every stretch/override.
    scene = gen._scene(grid)
    target = gen._largest_hollow(scene)
    if solid:
        assert max(o['size'] for o in scene if not o['hollow']) > target['size']
    if profile == 'bbox_area_conflict':
        assert gen._witness_outer_perimeter_conflict(grid)
        assert gen._witness_multi_hole_target(grid)


@pytest.mark.parametrize("profile", gen.SCENE_PROFILES)
def test_reference_mirror_equivariance_and_palette_renaming(profile):
    grid = gen.generate(211, 3, difficulty='hard', scene_profile=profile, solid_decoy=True)
    output = gen._true_output(grid)
    transforms = [lambda g: [row[:] for row in g],
                  lambda g: [row[::-1] for row in g],
                  lambda g: [row[:] for row in g[::-1]],
                  lambda g: [list(row) for row in zip(*g)]]
    # The oracle's unique colored-cell maximum is invariant under D4.
    for first in transforms:
        for second in transforms:
            transformed = first(second(grid))
            assert gen.self_check(transformed) == []
            assert gen._true_output(transformed) == first(second(output))
    palette = {0: 0, **{c: 10-c for c in range(1, 10)}}
    renamed = [[palette[c] for c in row] for row in grid]
    assert gen.self_check(renamed) == []
    assert gen._true_output(renamed) == [[palette[c] for c in row] for row in output]
