"""Focused regressions for the rotation-code mosaic generator review.

Labels are produced by the unchanged Racket authority.  ``rule_mirror`` is an
independent review oracle used only for tests, semantic rivals, and evidence.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "76b6aec98a7c"
RULE_HASH = "266efcdf916c"
ROOT = find_root(__file__)
GENERATOR_PATH = ROOT / "generators" / TASK_ID / "generator.py"
if not GENERATOR_PATH.is_file():
    GENERATOR_PATH = ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
SPEC = importlib.util.spec_from_file_location("rotation_mosaic_under_review", GENERATOR_PATH)
gen = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(gen)


def _rotate(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _bbox(cells):
    rows, cols = zip(*cells)
    return min(rows), min(cols), max(rows) + 1, max(cols) + 1


def _parts(grid):
    ones = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1}
    frame_box = _bbox(ones)
    r0, c0, r1, c1 = frame_box
    motif = [list(row[c0 + 1:c1 - 1]) for row in grid[r0 + 1:r1 - 1]]
    frame_rect = {(r, c) for r in range(r0, r1) for c in range(c0, c1)}
    code_cells = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
                  if value in (2, 3, 4, 5) and (r, c) not in frame_rect}
    code_box = _bbox(code_cells)
    cr0, cc0, cr1, cc1 = code_box
    codes = [list(row[cc0:cc1]) for row in grid[cr0:cr1]]
    return frame_box, motif, code_box, codes


def _rotation_orbit(pattern):
    frozen = set()
    current = pattern
    for _ in range(4):
        frozen.add(tuple(tuple(row) for row in current))
        current = _rotate(current)
    return frozen


def test_rule_hash_is_pinned_to_the_unchanged_authority():
    assert gen.RULE_HASH == RULE_HASH


@pytest.mark.parametrize("controls", [
    {"grid_h": 10, "grid_w": 10, "motif_size": 2, "code_h": 2, "code_w": 2,
     "source_color": 6, "layout": "frame_left"},
    {"grid_h": 20, "grid_w": 22, "motif_size": 4, "code_h": 3, "code_w": 3,
     "source_color": 9, "layout": "frame_above"},
    {"grid_h": 13, "grid_w": 17, "motif_size": 3, "code_h": 2, "code_w": 3,
     "source_color": 7, "layout": "frame_right"},
    {"grid_h": 12, "grid_w": 14, "motif_size": 4, "code_h": 3, "code_w": 2,
     "source_color": 8, "layout": "frame_below"},
])
def test_every_advertised_exact_control_is_observable_and_honored(controls):
    grid = gen.generate(37, 11, difficulty="hard", **controls)
    assert gen.observe_overrides(grid) == controls
    assert gen.self_check(grid, meta={"overrides": controls}) == []


@pytest.mark.parametrize("overrides", [
    {"grid_h": 9}, {"grid_w": 23}, {"motif_size": 1}, {"motif_size": 5},
    {"code_h": 1}, {"code_w": 4}, {"source_color": 5}, {"source_color": 10},
    {"layout": "diagonal"}, {"grid_h": True}, {"source_color": "7"},
    {"code_h": 2.5}, {"motif_szie": 3}, {"texture": "no_frame"},
])
def test_invalid_or_legacy_controls_fail_explicitly(overrides):
    with pytest.raises(ValueError):
        gen.generate(3, 5, **overrides)


def test_defaults_cover_geometry_color_layout_and_motif_variation():
    observed = [gen.observe_overrides(gen.generate(101, index, difficulty="medium"))
                for index in range(24)]
    assert {row["motif_size"] for row in observed} == {2, 3, 4}
    assert {row["source_color"] for row in observed} == {6, 7, 8, 9}
    assert {row["layout"] for row in observed} == {
        "frame_left", "frame_right", "frame_above", "frame_below"
    }
    assert {row["code_h"] for row in observed} == {2, 3}
    assert {row["code_w"] for row in observed} == {2, 3}
    assert len({(row["grid_h"], row["grid_w"]) for row in observed}) >= 8


def test_every_default_instance_contains_all_rotation_codes_and_an_asymmetric_motif():
    for index in range(24):
        grid = gen.generate(211, index, difficulty="medium")
        _, motif, _, codes = _parts(grid)
        assert {value for row in codes for value in row} == {2, 3, 4, 5}
        assert len(_rotation_orbit(motif)) == 4
        assert gen.self_check(grid) == []


def test_canonical_pairs_are_in_domain_and_match_the_python_oracle():
    for pair in canonical_pairs(TASK_ID, root=ROOT):
        assert gen.self_check(pair["input"]) == [], pair["variant"]
        assert gen.rule_mirror(pair["input"]) == pair["output"], pair["variant"]


def test_generated_inputs_match_the_unchanged_racket_authority():
    from arcpuzzles import Catalog

    inputs = [gen.generate(307, index, difficulty=band)
              for band in ("easy", "medium", "hard") for index in range(4)]
    receipt = Catalog(ROOT).apply(TASK_ID, inputs, timeout=120)
    assert receipt["rule_hash_matches_catalog"]
    assert all(result["valid_output"] for result in receipt["results"])
    assert [result["output"] for result in receipt["results"]] == [
        gen.rule_mirror(grid) for grid in inputs
    ]


def test_fixed_color_six_is_a_real_canonical_shortcut_and_is_refuted_by_defaults():
    rival = gen.CANONICAL_SHORTCUTS["fixed_color_six"]
    for pair in canonical_pairs(TASK_ID, root=ROOT):
        assert rival(pair["input"]) == pair["output"]

    witness = gen.generate(
        19, 1, grid_h=13, grid_w=15, motif_size=3, code_h=2, code_w=3,
        source_color=7, layout="frame_left",
    )
    assert rival(witness) != gen.rule_mirror(witness)


def test_four_consecutive_pairs_remain_identifiable_under_every_query_rotation():
    for start in range(8):
        pairs = []
        for index in range(start, start + 4):
            grid = gen.generate(401, index, difficulty="medium")
            pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
        for query_index, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert gen.lesson_identifiable(demos, query) == [], (start, query_index)


def test_self_check_rejects_code_holes_symmetric_motifs_and_rogue_cells():
    good = gen.generate(
        23, 7, grid_h=14, grid_w=16, motif_size=3, code_h=3, code_w=3,
        source_color=8, layout="frame_right",
    )
    frame_box, _, code_box, _ = _parts(good)

    code_hole = deepcopy(good)
    cr0, cc0, _, _ = code_box
    code_hole[cr0][cc0] = 0
    assert gen.self_check(code_hole)

    symmetric = deepcopy(good)
    r0, c0, r1, c1 = frame_box
    for r in range(r0 + 1, r1 - 1):
        for c in range(c0 + 1, c1 - 1):
            symmetric[r][c] = 8
    assert gen.self_check(symmetric)

    rogue = deepcopy(good)
    for r, row in enumerate(rogue):
        for c, value in enumerate(row):
            if value == 0:
                rogue[r][c] = 9
                assert gen.self_check(rogue)
                return
    pytest.fail("fixture unexpectedly had no background cell")


def test_default_schedule_anchors_an_exact_canonical_profile_in_every_band():
    """Mirror the repository's pinned 20-draw profile-floor census."""
    import hashlib

    canonical_profiles = {(10, 16, 7), (11, 17, 7), (11, 18, 7)}
    total_hits = 0
    for band in ("easy", "medium", "hard"):
        hits = []
        for index in range(20):
            digest = hashlib.sha256(
                f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
            ).hexdigest()
            seed = int(digest[:12], 16)
            sample_index = seed % 7919 + index
            grid = gen.generate(seed, sample_index, difficulty=band)
            profile = (len(grid), len(grid[0]), len({v for row in grid for v in row}))
            if profile in canonical_profiles:
                hits.append((index, profile))
        assert hits, band
        total_hits += len(hits)
    assert total_hits >= 15, total_hits  # clean 25% floor over 60 pinned draws


def test_task_local_distribution_probe_reports_reusable_evidence():
    probe_path = GENERATOR_PATH.parent / "workspace" / "probe_distribution.py"
    probe_spec = importlib.util.spec_from_file_location("rotation_mosaic_probe", probe_path)
    probe = importlib.util.module_from_spec(probe_spec)
    assert probe_spec.loader is not None
    probe_spec.loader.exec_module(probe)

    report = probe.audit(root=ROOT, per_band=4, window_starts=2, racket_samples=0)
    assert report["status"] == "pass"
    assert report["summary"]["sampled"] == 12
    assert report["summary"]["self_check_failures"] == 0
    assert report["summary"]["lesson_rotations_checked"] == 8
    assert report["axis_coverage"]["source_color"] == [6, 7, 8, 9]
    assert report["axis_coverage"]["layout"] == [
        "frame_above", "frame_below", "frame_left", "frame_right"
    ]
