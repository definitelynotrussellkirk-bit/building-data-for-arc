"""Focused semantic and distribution contract for 60a8a9d74a75."""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import importlib.util
from pathlib import Path
import random
import os
import subprocess
import sys

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "60a8a9d74a75"
HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", HOME / "generator.py")
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def zero_regions(grid):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 0}
    result = []
    while unseen:
        start = unseen.pop()
        cells = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (nr, nc) in unseen:
                    unseen.remove((nr, nc))
                    cells.add((nr, nc))
                    queue.append((nr, nc))
        colored_neighbors = []
        for r, c in cells:
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if 0 <= nr < h and 0 <= nc < w:
                    value = grid[nr][nc]
                    if value not in (0, 8):
                        colored_neighbors.append(((nr, nc), value))
        result.append({
            "cells": cells,
            "touches_edge": any(r in (0, h - 1) or c in (0, w - 1) for r, c in cells),
            "neighbor_cells": {point for point, _ in colored_neighbors},
            "colors": {value for _, value in colored_neighbors},
        })
    return result


def independent_rule(grid):
    out = deepcopy(grid)
    for region in zero_regions(grid):
        if len(region["colors"]) == 1:
            color = next(iter(region["colors"]))
            for r, c in region["cells"]:
                out[r][c] = color
    return out


def pair(grid):
    return {"input": grid, "output": independent_rule(grid)}


def test_rule_pin_and_honest_override_surface():
    assert GEN.RULE_HASH == "49411595dc9e"
    assert set(GEN.AXES) == {"profile"}
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.LESSON_SCHEDULE_PERIOD == 4
    assert tuple(GEN.SCHEDULE_PROFILES) == (
        "canonical_rows", "composite_open_left", "canonical_cols", "composite_open_top"
    )


def test_every_canonical_pair_is_accepted_and_matches_independent_rule():
    items = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(items) == 5
    for item in items:
        assert GEN.self_check(item["input"]) == []
        assert GEN.strict_canonical_like(item["input"]) == []
        assert GEN.rule_mirror(item["input"]) == independent_rule(item["input"]) == item["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", [
    "canonical_rows", "canonical_cols", "composite_open_left", "composite_open_top"
])
def test_profile_override_is_exact_observable_and_rule_lawful(band, profile):
    grid = GEN.generate(1701, 99, difficulty=band, profile=profile)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == {"profile": profile}
    assert GEN.rule_mirror(grid) == independent_rule(grid)


@pytest.mark.parametrize("kwargs", [
    {"profile": "unknown"}, {"profile": 3}, {"profile": None},
    {"unknown_axis": 1},
])
def test_invalid_overrides_fail_closed(kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 0, **kwargs)


@pytest.mark.parametrize("seed,sample_index", [(2, 37), (6, 105)])
@pytest.mark.parametrize("profile", ["composite_open_left", "composite_open_top"])
def test_composite_seed_placement_never_pinches_off_a_corner(seed, sample_index, profile):
    grid = GEN.generate(seed, sample_index, difficulty="hard", profile=profile)
    assert GEN.self_check(grid) == []
    assert len(zero_regions(grid)) == 4


def test_composite_profiles_cover_canonical_scale_regions():
    for profile in ("composite_open_left", "composite_open_top"):
        grid = GEN.generate(1701, 99, difficulty="hard", profile=profile)
        assert max(len(region["cells"]) for region in zero_regions(grid)) >= 50


def test_composite_profiles_exercise_all_semantic_branches():
    for profile in ("composite_open_left", "composite_open_top"):
        grid = GEN.generate(88, 1, difficulty="hard", profile=profile)
        regions = zero_regions(grid)
        assert len(regions) == 4
        assert any(len(x["colors"]) == 1 and len(x["neighbor_cells"]) == 2 for x in regions)
        assert any(len(x["colors"]) >= 2 for x in regions)
        assert any(x["touches_edge"] and len(x["colors"]) == 1 for x in regions)
        assert any(len(x["colors"]) == 1 and len(x["neighbor_cells"]) >= 12 for x in regions)
        truth = independent_rule(grid)
        for name, rival in GEN.SEMANTIC_RIVALS.items():
            assert rival(grid) != truth, name
        assert GEN.strict_canonical_like(grid)


def test_all_declared_canonical_shortcuts_really_fit_every_canonical_pair():
    items = canonical_pairs(TASK_ID, root=find_root(__file__))
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert all(rival(item["input"]) == item["output"] for item in items), name


def test_every_cyclic_lesson_and_query_rotation_refutes_all_rivals():
    assert set(GEN.SEMANTIC_RIVALS) == set(GEN.LESSON_COMPETITORS)
    for band in ("easy", "medium", "hard"):
        for start in range(8):
            lesson = [pair(GEN.generate(5000 + start, start + offset, difficulty=band))
                      for offset in range(4)]
            assert {GEN.schedule_profile(0, start + i, band) for i in range(4)} == set(GEN.SCHEDULE_PROFILES)
            for query_index, query in enumerate(lesson):
                demos = [item for i, item in enumerate(lesson) if i != query_index]
                assert GEN.lesson_identifiable(demos, query) == []
                for name, rival in GEN.LESSON_COMPETITORS.items():
                    assert any(rival(item["input"]) != item["output"] for item in demos), name


def test_schedule_has_canonical_profile_support_in_every_band():
    for band in ("easy", "medium", "hard"):
        grids = [GEN.generate(7000 + i, i, difficulty=band) for i in range(20)]
        profiles = [GEN.observe_overrides(grid)["profile"] for grid in grids]
        assert profiles.count("canonical_rows") == 5
        assert profiles.count("canonical_cols") == 5
        assert sum(not GEN.strict_canonical_like(grid) for grid in grids) == 10
        assert any((len(grid), len(grid[0]), len({v for row in grid for v in row})) == (10, 10, 4)
                   for grid in grids)
        assert any((len(grid), len(grid[0]), len({v for row in grid for v in row})) == (9, 11, 4)
                   for grid in grids)


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(20261008)
    state = random.getstate()
    first = GEN.generate(77, 5, difficulty="medium")
    assert random.getstate() == state
    second = GEN.generate(77, 5, difficulty="medium")
    assert first == second and first is not second
    assert all(a is not b for a, b in zip(first, second))
    saved = deepcopy(second)
    first[0][0] = 0 if first[0][0] else 8
    assert second == saved


@pytest.mark.parametrize("bad", [None, [], [[]], [[8, 8], [8]], [[True, 8], [8, 8]], [[8, 8], [8, 7]]])
def test_malformed_or_rule_hiding_inputs_are_diagnostic(bad):
    assert GEN.self_check(bad)


def test_validator_rejects_destructive_composite_mutations():
    grid = GEN.generate(3, 1, profile="composite_open_left")
    assert GEN.self_check(grid) == []
    mutants = []
    erased_wall = deepcopy(grid); erased_wall[8][4] = 0; mutants.append(erased_wall)
    bad_palette = deepcopy(grid); bad_palette[0][0] = 10; mutants.append(bad_palette)
    closed_open_region = deepcopy(grid)
    for r in range(len(closed_open_region)):
        if closed_open_region[r][0] == 0:
            closed_open_region[r][0] = 8
    mutants.append(closed_open_region)
    for mutant in mutants:
        assert GEN.self_check(mutant)


def test_reference_probe_independently_reports_regions_truth_and_rivals():
    probe_path = HOME / "workspace" / "reference_probe.py"
    spec = importlib.util.spec_from_file_location(f"probe_{TASK_ID}", probe_path)
    assert spec and spec.loader
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)

    grid = GEN.generate(901, 1, difficulty="hard", profile="composite_open_left")
    report = probe.analyze_grid(grid, rivals=GEN.LESSON_COMPETITORS)
    assert report["reference_output"] == independent_rule(grid)
    assert report["region_count"] == 4
    assert set(report["rivals"]) == set(GEN.LESSON_COMPETITORS)
    assert all(item["disagrees"] for item in report["rivals"].values())


def test_reference_probe_cli_bootstraps_repository_runtime(tmp_path):
    probe_path = HOME / "workspace" / "reference_probe.py"
    out = tmp_path / "probe.json"
    env = dict(os.environ)
    env["PYTHONPATH"] = ""
    completed = subprocess.run(
        [
            sys.executable, str(probe_path),
            "--seed", "901", "--sample-index", "1",
            "--difficulty", "hard",
            "--profile", "composite_open_left",
            "--out", str(out),
        ],
        cwd=find_root(__file__),
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    payload = __import__("json").loads(out.read_text())
    assert payload["task_id"] == TASK_ID
    assert payload["region_count"] == 4


def test_retained_shortcut_counterexample_refutes_single_seed_chambers():
    import json

    path = HOME / "counterexamples" / "single_seed_8_chambers.json"
    payload = json.loads(path.read_text())
    grid = payload["input"]
    assert GEN.self_check(grid) == []
    assert GEN.rule_mirror(grid) == payload["authority_output"]
    assert GEN.SEMANTIC_RIVALS[payload["rival_name"]](grid) == payload["rival_output"]
    assert payload["rival_output"] != payload["authority_output"]
