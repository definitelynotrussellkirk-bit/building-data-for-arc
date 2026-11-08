"""Regressions for concrete surviving shortcuts, not raw-grid diversity."""
from collections import Counter
from pathlib import Path
import random
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'workspace'))
from reference_probe import load_generator, object_stats, intended_output, racket_outputs
from topology_probe import ADDITIONAL_RIVALS, components, scene_signature, shape_signature

gen = load_generator()


@pytest.mark.parametrize('name', list(ADDITIONAL_RIVALS))
def test_four_demonstrations_refute_new_independent_rival(name):
    rival = ADDITIONAL_RIVALS[name]
    for start in range(4):
        grids = [gen.generate(8107, start+i) for i in range(4)]
        assert any(rival(g) != intended_output(g) for g in grids), name


def test_distribution_has_normalized_morphological_support():
    grids = [gen.generate(990+i, i) for i in range(128)]
    shapes = {shape_signature(o['cells']) for g in grids for o in components(g)}
    assert len(shapes) >= 40
    assert len({scene_signature(g) for g in grids}) >= 50


def test_extended_scenes_teach_four_five_and_six_holes():
    holes = {s['holes'] for s in object_stats(gen.generate(815, 0, profile='extended'))}
    assert {0, 1, 2, 3, 4, 5, 6} <= holes


def test_canvas_size_does_not_encode_profile():
    dimensions = []
    for profile in gen.PROFILES:
        grids = [gen.generate(100+i, i, profile=profile) for i in range(80)]
        dimensions.append({(len(g), len(g[0])) for g in grids})
    assert len(set.intersection(*dimensions)) >= 3


def test_repeated_hole_counts_and_all_canvas_borders_have_support():
    repeated = False
    edges = set()
    for i in range(128):
        g = gen.generate(600+i, i)
        repeated |= max(Counter(s['holes'] for s in object_stats(g)).values()) > 1
        for obj in components(g):
            r0, c0, r1, c1 = obj['bbox']
            if r0 == 0: edges.add('top')
            if c0 == 0: edges.add('left')
            if r1 == len(g)-1: edges.add('bottom')
            if c1 == len(g[0])-1: edges.add('right')
    assert repeated
    assert edges == {'top', 'left', 'bottom', 'right'}


def test_racket_parity_on_independently_sampled_masks_and_quarter_turns():
    rng = random.Random(41829)
    grids = []
    for i in range(70):
        h, w = rng.randint(6, 9), rng.randint(6, 9)
        g = [[7]*w for _ in range(h)]
        choices = [(r,c) for r in range(1,h-1,2) for c in range(1,w-1,2)]
        rng.shuffle(choices)
        for r,c in choices[:i % 7]: g[r][c] = 0
        for _ in range(i % 4): g = [list(row) for row in zip(*g[::-1])]
        grids.append(g)
    assert racket_outputs(grids) == [intended_output(g) for g in grids]
