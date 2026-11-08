"""Regression contract for the hollow-object hole-extraction sampler.

The canonical Racket rule remains the label authority.  This file deliberately
uses an independent Python oracle so sampler and tests cannot share the same
implementation mistake.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import random

import pytest

from reviewer_support import canonical_pairs, find_root

TASK = "2db2974cdb04"
HOME = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location("reviewed_2db2974cdb04", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _regions(grid, *, zero: bool):
    h, w = len(grid), len(grid[0])
    unseen = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if (grid[r][c] == 0) is zero
    }
    result = []
    while unseen:
        start = unseen.pop()
        color = grid[start[0]][start[1]]
        todo = [start]
        cells = {start}
        while todo:
            r, c = todo.pop()
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                point = (nr, nc)
                if point in unseen and (zero or grid[nr][nc] == color):
                    unseen.remove(point)
                    cells.add(point)
                    todo.append(point)
        result.append((color, cells))
    return result


def oracle(grid):
    """Paint only global 0-regions wholly strict-inside each colored bbox."""
    out = [[0 for _ in row] for row in grid]
    zero_regions = [cells for _, cells in _regions(grid, zero=True)]
    for color, cells in _regions(grid, zero=False):
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        r1, r2, c1, c2 = min(rs), max(rs), min(cs), max(cs)
        for region in zero_regions:
            if region and all(r1 < r < r2 and c1 < c < c2 for r, c in region):
                for r, c in region:
                    out[r][c] = color
    return out


def profile(grid):
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


@pytest.mark.parametrize(
    "pair",
    canonical_pairs(TASK, root=ROOT),
    ids=lambda p: f"v{p['variant']}-{p['split']}{p['pair_index']}",
)
def test_canonical_inputs_are_owned_and_independent_oracle_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert oracle(pair["input"]) == pair["output"]


def test_rule_hash_is_pinned_to_selected_authority():
    assert gen.RULE_HASH == "c621ef85bf9e"


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        dict(layout_profile="canonical_9x9", n_objects=2,
             shape_profile="rectangular", border_profile="interior",
             contact_profile="separated"),
        dict(layout_profile="canonical_10x12", n_objects=2,
             shape_profile="stemmed", border_profile="edge",
             contact_profile="touching"),
        dict(layout_profile="canonical_10x10", n_objects=1,
             shape_profile="stemmed", border_profile="edge",
             contact_profile="separated"),
        dict(layout_profile="expanded_12x14", n_objects=2,
             shape_profile="rectangular", border_profile="edge",
             contact_profile="touching"),
    ],
)
def test_every_advertised_override_is_exact_and_observable(band, options):
    grid = gen.generate(317, 29, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == options
    assert oracle(grid) != grid


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo": 1},
        {"layout_profile": "tiny"},
        {"n_objects": True},
        {"n_objects": 0},
        {"n_objects": 3},
        {"shape_profile": "solid"},
        {"border_profile": "sometimes"},
        {"contact_profile": "overlap"},
        {"n_objects": 1, "contact_profile": "touching"},
    ],
)
def test_invalid_or_incompatible_overrides_fail_loudly(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **overrides)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_distribution_is_deterministic_lawful_and_canonically_anchored(band):
    observed = {name: set() for name in gen.AXES}
    canonical_profiles = {
        profile(pair["input"]) for pair in canonical_pairs(TASK, root=ROOT)
    }
    exact_hits = 0
    inputs = set()
    outputs = set()
    for index in range(90):
        seed = 10_000 + index
        grid = gen.generate(seed, index, difficulty=band)
        assert grid == gen.generate(seed, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        intended = oracle(grid)
        assert intended != grid
        exact_hits += profile(grid) in canonical_profiles
        inputs.add(tuple(map(tuple, grid)))
        outputs.add(tuple(map(tuple, intended)))
        values = gen.observe_overrides(grid)
        for name in observed:
            observed[name].add(values[name])
    assert exact_hits >= 20
    assert len(inputs) >= 70
    assert len(outputs) >= 60
    assert observed["n_objects"] == {1, 2}
    assert observed["shape_profile"] == {"rectangular", "stemmed"}
    assert observed["border_profile"] == {"interior", "edge"}
    assert observed["contact_profile"] == {"separated", "touching"}
    assert len(observed["layout_profile"]) >= 4


def test_named_rivals_have_constructive_counterexamples():
    stem_pair = gen.generate(
        71, 1, layout_profile="canonical_10x12", n_objects=2,
        shape_profile="stemmed", border_profile="edge",
        contact_profile="touching",
    )
    intended = oracle(stem_pair)
    assert gen.SEMANTIC_WITNESSES["stemmed_bbox_counterexample"](stem_pair)
    assert gen.SEMANTIC_WITNESSES["multiple_objects"](stem_pair)
    assert gen.SEMANTIC_WITNESSES["border_removed"](stem_pair)
    for name, rival in gen.SEMANTIC_RIVALS.items():
        assert rival(deepcopy(stem_pair)) != intended, name

    rectangle = gen.generate(
        72, 1, layout_profile="canonical_9x11", n_objects=2,
        shape_profile="rectangular", border_profile="interior",
        contact_profile="separated",
    )
    # The bbox shortcut is intentionally canonical-compatible on pure rectangles;
    # only the stemmed branch supplies its counterexample.
    assert gen.SEMANTIC_RIVALS["bbox_interior"](rectangle) == oracle(rectangle)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_three_consecutive_schedule_profiles_identify_the_rule(band):
    assert len(gen.SCHEDULE_PROFILES) == gen.EXAMPLES_NEEDED == 3
    for start in range(9):
        pairs = []
        profiles = []
        for offset in range(4):
            index = start + offset
            grid = gen.generate(80_000 + start, index, difficulty=band)
            pairs.append({"input": grid, "output": oracle(grid)})
            profiles.append(gen.schedule_profile(80_000 + start, index, band))
        assert set(profiles[:3]) == set(gen.SCHEDULE_PROFILES)
        assert gen.lesson_identifiable(pairs[:3], pairs[3]) == []
        for query_index in range(4):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert gen.lesson_identifiable(demos, pairs[query_index]) == []


def test_self_check_rejects_open_solid_malformed_and_identity_scenes():
    valid = gen.generate(88, 4)

    opened = deepcopy(valid)
    color = next(value for row in opened for value in row if value)
    point = next(
        (r, c) for r, row in enumerate(opened) for c, value in enumerate(row)
        if value == color
    )
    opened[point[0]][point[1]] = 0
    assert gen.self_check(opened)

    solid = [[0] * 7 for _ in range(7)]
    for r in range(2, 5):
        for c in range(2, 5):
            solid[r][c] = 4
    assert gen.self_check(solid)

    for malformed in (None, [], [[]], [[0], [0, 1]], [[True, 0]], [[0, 10]]):
        assert gen.self_check(malformed)


def test_generation_does_not_mutate_global_random_state():
    random.seed(418)
    before = random.getstate()
    gen.generate(77, 12, difficulty="hard")
    assert random.getstate() == before


def test_workspace_audit_replays_core_contract():
    path = HOME / "workspace" / "hole_extraction_audit.py"
    spec = importlib.util.spec_from_file_location("hole_extraction_audit", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    report = module.run_audit(per_band=12)
    assert report["canonical_pairs"] == 5
    assert report["canonical_failures"] == []
    assert report["errors"] == []
    for stats in report["bands"].values():
        assert stats["invalid"] == 0
        assert stats["oracle_mismatches"] == 0
        assert stats["exact_canonical_profiles"] > 0


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_default_stemmed_scene_refutes_bbox_interior_shortcut(band):
    for index in range(120):
        grid = gen.generate(610_000 + index, index, difficulty=band)
        if gen.observe_overrides(grid)["shape_profile"] == "stemmed":
            assert gen.SEMANTIC_RIVALS["bbox_interior"](grid) != oracle(grid)
            assert gen.SEMANTIC_WITNESSES["stemmed_bbox_counterexample"](grid)


def test_retained_bbox_counterexample_is_source_bound_and_authoritative():
    home = HOME / "counterexamples" / "bbox-interior-shortcut"
    metadata = json.loads((home / "metadata.json").read_text())
    grid = json.loads((home / "input.json").read_text())
    rival = json.loads((home / "bbox-rival.json").read_text())
    racket = json.loads((home / "racket.json").read_text())
    assert metadata["generator_sha256"] == hashlib.sha256((HOME / "generator.py").read_bytes()).hexdigest()
    assert metadata["rule_hash"] == gen.RULE_HASH == racket["executed_rule_hash"]
    assert gen.self_check(grid) == []
    expected = oracle(grid)
    assert racket["results"][0]["output"] == expected
    assert rival != expected
    assert metadata["difference_cells"]
