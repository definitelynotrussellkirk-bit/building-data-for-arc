"""Portable regressions for the 2026-10-22 review repair.

The inherited ``test_generator_e07bbcbe6ba4.py`` is a frozen fixture and is
intentionally not edited here.  These tests use the public reviewer helpers so
that they run in both the repository and staged portable runtimes.
"""
from __future__ import annotations

import json
import hashlib
from pathlib import Path

import pytest

from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
)


ROOT = find_root(__file__)
GEN, GENERATOR_SOURCE, GENERATOR_SHA256 = load_selected_generator(
    "e07bbcbe6ba4", root=ROOT
)


def _canonical_pairs() -> list[dict]:
    return canonical_pairs(GEN.TASK_ID, root=ROOT, labeled_only=True)


def _canonical_source() -> str:
    sources: set[str] = set()
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == GEN.TASK_ID:
                source = row.get("program_solution")
                if isinstance(source, str):
                    sources.add(source)
    assert len(sources) == 1
    return sources.pop()


@pytest.mark.parametrize(
    "seed,sample_index,difficulty,overrides",
    [
        (True, 0, None, {}),
        (1.0, 0, None, {}),
        ("1", 0, None, {}),
        (0, True, None, {}),
        (0, 1.0, None, {}),
        (0, -1, None, {}),
        (0, 0, False, {}),
        (0, 0, 0, {}),
        (0, 0, "bogus", {}),
        (0, 0, None, {"__typo_axis__": 1}),
        (0, 0, None, {"grid_h": True}),
        (0, 0, None, {"grid_h": 15.0}),
        (0, 0, None, {"grid_h": "15"}),
        (0, 0, None, {"frame_w": False}),
    ],
)
def test_generate_rejects_permissive_scalar_coercions_and_unknown_axes(
    seed, sample_index, difficulty, overrides
):
    """Changing ``int(value)`` coercion or the override allow-list breaks this."""
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(
            seed,
            sample_index,
            difficulty=difficulty,
            **overrides,
        )


def test_expanded_geometry_supports_a_longer_ring_without_changing_the_rule():
    """Shrinking the repaired frame/canvas domains makes this lawful case fail."""
    grid = GEN.generate(
        20261022,
        17,
        difficulty="hard",
        grid_h=30,
        grid_w=30,
        frame_h=24,
        frame_w=24,
        marker_edge=False,
    )
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == {
        "frame_h": 24,
        "frame_w": 24,
        "marker_edge": False,
    }
    assert GEN.rule_mirror(grid) != grid


def test_pinned_profile_floor_has_at_least_twenty_five_percent_support():
    """The public 20-per-band census must retain >=15 canonical envelopes."""
    per_band = {}
    for band in ("easy", "medium", "hard"):
        hits = 0
        for index in range(20):
            digest = hashlib.sha256(
                f"profile-floor:v1:{GEN.TASK_ID}:{band}:{index}".encode()
            ).hexdigest()
            seed = int(digest[:12], 16)
            sample_index = seed % 7919 + index
            grid = GEN.generate(seed, sample_index, difficulty=band)
            profile = (
                len(grid),
                len(grid[0]),
                len({value for row in grid for value in row}),
            )
            hits += profile == (15, 15, 2)
        per_band[band] = hits
    assert all(hits >= 1 for hits in per_band.values()), per_band
    assert sum(per_band.values()) >= 15, per_band


def test_selected_racket_authorities_match_the_exact_canonical_program():
    """Whitespace-only target drift must not recur; raw archival text is retained."""
    canonical = _canonical_source()
    paths = (
        ROOT / "shared/data/base/solutions/training/b7fb29bc__e07bbcbe6ba4.json",
        ROOT / "shared/data/base/solutions/augmented/b7fb29bc__d5ad22a70742.json",
    )
    for path in paths:
        record = json.loads(path.read_text(encoding="utf-8"))
        target = record["racket_target"]
        assert target["target_code"] == canonical
        assert isinstance(target.get("raw_code"), str)
        assert target["raw_code"]


def test_declared_fixed_bbox_shortcut_fits_every_canonical_pair():
    """The declared rival is honest: canonical demonstrations cannot refute it."""
    rival = GEN.CANONICAL_SHORTCUTS["fixed_canonical_bbox"]
    pairs = _canonical_pairs()
    assert len(pairs) == 8
    assert all(rival(pair["input"]) == pair["output"] for pair in pairs)


def test_variable_geometry_witness_refutes_the_fixed_bbox_shortcut():
    """Removing geometry variation or the witness/rival link breaks this test."""
    grid = GEN.generate(
        9,
        3,
        grid_h=9,
        grid_w=9,
        frame_h=7,
        frame_w=7,
        marker_edge=True,
    )
    intended = GEN.rule_mirror(grid)
    rival = GEN.CANONICAL_SHORTCUTS["fixed_canonical_bbox"]
    assert GEN.self_check(grid) == []
    assert GEN.SEMANTIC_WITNESSES["variable_geometry_refutes_fixed_bbox"](grid)
    assert "fixed_canonical_bbox" in GEN.WITNESS_RIVALS[
        "variable_geometry_refutes_fixed_bbox"
    ]
    assert rival(grid) != intended


def test_lesson_hook_reports_then_refutes_the_canonical_shortcut():
    """A generated counterexample must make the declared shortcut teachable."""
    canonical = [
        {"input": pair["input"], "output": pair["output"]}
        for pair in _canonical_pairs()[:3]
    ]
    query_grid = GEN.generate(
        91,
        4,
        grid_h=9,
        grid_w=10,
        frame_h=7,
        frame_w=8,
        marker_edge=False,
    )
    reasons = GEN.lesson_identifiable(canonical, {"input": query_grid})
    assert any("fixed_canonical_bbox" in reason for reason in reasons)

    counterexample = {
        "input": query_grid,
        "output": GEN.rule_mirror(query_grid),
    }
    another_query = GEN.generate(
        92,
        5,
        grid_h=12,
        grid_w=13,
        frame_h=8,
        frame_w=9,
        marker_edge=True,
    )
    assert GEN.lesson_identifiable(
        canonical[:2] + [counterexample],
        {"input": another_query},
    ) == []
