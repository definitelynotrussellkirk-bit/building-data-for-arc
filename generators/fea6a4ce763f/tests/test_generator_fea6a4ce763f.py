"""Regression and semantic tests for the fea6a4ce763f curriculum."""
from __future__ import annotations

from collections import Counter
from importlib.util import module_from_spec, spec_from_file_location
import hashlib
import json
import os
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "fea6a4ce763f"
HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = spec_from_file_location(f"task_generator_{TASK_ID}", GENERATOR_PATH)
assert SPEC and SPEC.loader
GEN = module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)


def _pairs():
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for sr in range(h):
        for sc in range(w):
            color = grid[sr][sc]
            if color == 0 or (sr, sc) in seen:
                continue
            cells = set()
            stack = [(sr, sc)]
            seen.add((sr, sc))
            while stack:
                r, c = stack.pop()
                cells.add((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append((color, cells))
    return result


def _intended(grid):
    components = _components(grid)
    size = max(len(cells) for _, cells in components)
    winners = [cells for _, cells in components if len(cells) == size]
    assert len(winners) == 1
    cells = winners[0]
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    return [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]


def _pair(seed, sample_index, band="medium"):
    grid = GEN.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": _intended(grid)}


@pytest.mark.parametrize("pair", _pairs())
def test_canonical_inputs_are_owned_and_match_independent_oracle(pair):
    assert GEN.self_check(pair["input"]) == []
    assert GEN.strict_canonical_like(pair["input"]) == []
    assert _intended(pair["input"]) == pair["output"]


def test_rule_pin_and_public_surface_are_exact():
    assert GEN.RULE_HASH == "5f27f31fdbe8"
    assert set(GEN.AXES) == {"scene_profile"}
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == ()
    assert tuple(GEN.PROFILE_DIMENSIONS) == GEN.SCHEDULE_PROFILES
    assert GEN.LESSON_SCHEDULE_PERIOD == len(GEN.SCHEDULE_PROFILES) * 2


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", [
    "canonical_5x10_p4",
    "canonical_6x11_p4",
    "canonical_7x9_p4",
    "canonical_7x13_p4",
    "canonical_9x9_p5",
])
def test_every_profile_override_round_trips_in_every_band(profile, band):
    grid = GEN.generate(71, 3, difficulty=band, scene_profile=profile)
    h, w, palette = GEN.PROFILE_DIMENSIONS[profile]
    assert (len(grid), len(grid[0]), len({v for row in grid for v in row})) == (
        h,
        w,
        palette,
    )
    assert GEN.observe_overrides(grid) == {"scene_profile": profile}
    assert GEN.self_check(grid) == []
    assert GEN.strict_canonical_like(grid) == []


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo_axis": 1},
        {"grid_h": 6},
        {"scene_profile": None},
        {"scene_profile": 4},
        {"scene_profile": "not-a-profile"},
    ],
)
def test_invalid_or_retired_overrides_are_rejected(overrides):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **overrides)


def test_schedule_visits_every_profile_and_both_semantic_phases():
    period = GEN.LESSON_SCHEDULE_PERIOD
    observed = [GEN.schedule_profile(0, index, "hard") for index in range(period)]
    assert set(observed) == set(GEN.SCHEDULE_PROFILES)
    assert observed[: len(GEN.SCHEDULE_PROFILES)] == list(GEN.SCHEDULE_PROFILES)
    phases = [GEN.semantic_phase(0, index, "hard") for index in range(period)]
    assert set(phases) == {"split_distractor", "split_target"}
    assert all(a != b for a, b in zip(phases, phases[1:]))


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_ordinary_draws_are_deterministic_sparse_and_refute_the_scheduled_shortcut(band):
    hits = {name: 0 for name in GEN.SEMANTIC_WITNESSES}
    for index in range(20):
        grid = GEN.generate(4000 + index, index, difficulty=band)
        assert GEN.generate(4000 + index, index, difficulty=band) == grid
        assert GEN.self_check(grid) == []
        output = _intended(grid)
        nonzero = sum(value != 0 for row in output for value in row)
        assert nonzero < len(output) * len(output[0])
        fired = [name for name, witness in GEN.SEMANTIC_WITNESSES.items() if witness(grid)]
        assert fired == [GEN.semantic_phase(4000 + index, index, band)]
        hits[fired[0]] += 1
        for rival_name in GEN.WITNESS_RIVALS[fired[0]]:
            assert GEN.SEMANTIC_RIVALS[rival_name](grid) != output
    assert all(count > 0 for count in hits.values())


def test_declared_canonical_shortcuts_reproduce_all_canonical_labels():
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in _pairs()), name


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_cyclic_lesson_and_every_query_rotation_is_identifiable(band):
    period = GEN.LESSON_SCHEDULE_PERIOD
    for start in range(period):
        pairs = [_pair(9000 + start, start + offset, band) for offset in range(5)]
        for query_index in range(len(pairs)):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            query = pairs[query_index]
            assert GEN.lesson_identifiable(demos, query) == [], (
                band,
                start,
                query_index,
                GEN.lesson_identifiable(demos, query),
            )


def test_self_check_rejects_empty_singleton_and_tied_largest_domains():
    assert GEN.self_check([])
    assert GEN.self_check([[0, 0], [0, 1]])
    assert GEN.self_check([[1, 1, 0, 2, 2]])


def test_difficulty_knob_changes_realized_pixels_without_changing_public_profile():
    """Difficulty is public API and must not be byte-dead for equal seeds."""
    distinct_triples = 0
    for index in range(8):
        seed = 15000 + index
        grids = {
            band: GEN.generate(seed, index, difficulty=band)
            for band in ("easy", "medium", "hard")
        }
        profiles = {band: GEN.observe_overrides(grid) for band, grid in grids.items()}
        assert len({tuple(profile.items()) for profile in profiles.values()}) == 1
        signatures = {
            tuple(tuple(row) for row in grid)
            for grid in grids.values()
        }
        distinct_triples += len(signatures) == 3
    assert distinct_triples >= 6


def test_workspace_semantic_probe_reports_profiles_witnesses_and_rotations():
    probe_path = HOME / "workspace" / "semantic_probe.py"
    spec = spec_from_file_location("fea6a4ce763f_semantic_probe", probe_path)
    assert spec and spec.loader
    probe = module_from_spec(spec)
    sys.modules[spec.name] = probe
    spec.loader.exec_module(probe)

    report = probe.build_report(GEN, seeds_per_band=12)
    assert report["generator_id"] == TASK_ID
    assert report["profiles_seen"] == sorted(GEN.SCHEDULE_PROFILES)
    assert set(report["witness_hits"]) == set(GEN.SEMANTIC_WITNESSES)
    assert all(count > 0 for count in report["witness_hits"].values())
    assert report["rival_counterexample_failures"] == []
    assert report["rotation_failures"] == []


def test_retained_most_frequent_color_counterexample_matches_source():
    path = HOME / "counterexamples" / "most_frequent_color_split_distractor.json"
    data = json.loads(path.read_text())
    grid = data["input"]
    truth = data["racket_output"]
    rival_name = data["rival_name"]

    assert data["generator_sha256"] == hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest()
    assert data["rule_hash"] == GEN.RULE_HASH
    assert data["self_check_errors"] == GEN.self_check(grid) == []
    assert data["witness_fires"] is True
    assert GEN.SEMANTIC_WITNESSES["split_distractor"](grid)
    assert _intended(grid) == GEN.rule_mirror(grid) == truth
    assert GEN.CANONICAL_SHORTCUTS[rival_name](grid) == data["rival_output"]
    assert data["rival_output"] != truth
