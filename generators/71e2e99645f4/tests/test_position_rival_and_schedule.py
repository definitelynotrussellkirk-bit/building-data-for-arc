"""Regressions for the canonical position-memorization shortcut."""
from __future__ import annotations

import importlib.util
import os
from itertools import combinations
from pathlib import Path

from reviewer_support import canonical_pairs, find_root

TASK_ID = "71e2e99645f4"
HOME = Path(__file__).resolve().parents[1]


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location(f"position_rival_{TASK_ID}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()
PAIRS = canonical_pairs(TASK_ID, root=find_root(__file__))

# A learner can memorize only the pattern/color pairs observed at each section
# position.  The three absent combinations all occur together in the query.
POSITION_TABLE = (
    {"no_hole": 2, "center_hole": 8, "edge_hole": 3},
    {"no_hole": 2, "center_hole": 8, "bottom_hole": 4},
    {"no_hole": 2, "bottom_hole": 4, "edge_hole": 3},
)


def position_lookup_rival(grid):
    patterns = GEN.observe_overrides(grid)["hole_patterns"]
    return [[POSITION_TABLE[index].get(pattern, 2)] * 3 for index, pattern in enumerate(patterns)]


def test_registered_position_lookup_fits_canonical_demos_and_fails_query() -> None:
    rival = GEN.LESSON_COMPETITORS["canonical_position_lookup"]
    for pair in PAIRS[:4]:
        assert rival(pair["input"]) == pair["output"]

    query = PAIRS[4]
    assert GEN.observe_overrides(query["input"])["hole_patterns"] == [
        "bottom_hole",
        "edge_hole",
        "center_hole",
    ]
    assert rival(query["input"]) == [[2, 2, 2], [2, 2, 2], [2, 2, 2]]
    assert rival(query["input"]) != query["output"]


def test_eighteen_case_schedule_keeps_full_codomain_and_refutes_rival_in_every_rotation() -> None:
    for band in ("easy", "medium", "hard"):
        for seed in (0, 1, 421, 8123):
            signatures = {
                tuple(GEN.observe_overrides(GEN.generate(seed, index, difficulty=band))["hole_patterns"])
                for index in range(18)
            }
            assert len(signatures) == GEN.EXPECTED_OUTPUT_CODOMAIN == 18

            for start in range(24):
                lesson = [
                    GEN.generate(seed, start + offset, difficulty=band)
                    for offset in range(4)
                ]
                refutes = [
                    position_lookup_rival(grid) != GEN.rule_mirror(grid)
                    for grid in lesson
                ]
                # Any three of the four must retain at least one refutation.
                assert sum(refutes) >= 2
                for demo_indices in combinations(range(4), 3):
                    assert any(refutes[index] for index in demo_indices)


def test_position_shortcut_probe_reports_the_canonical_gap_and_repaired_windows() -> None:
    probe_path = HOME / "workspace" / "probe_position_shortcut.py"
    spec = importlib.util.spec_from_file_location(f"position_probe_{TASK_ID}", probe_path)
    assert spec and spec.loader
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)

    report = probe.build_report(
        draws_per_band=12,
        window_starts=12,
        seeds=(0, 1),
        root=find_root(__file__),
    )
    assert report["canonical"]["demonstrations_all_fit"] is True
    assert report["canonical"]["query_disagrees"] is True
    assert report["canonical"]["query_rival_output"] == [[2, 2, 2]] * 3
    assert report["ordinary_draws"]["rival_disagreements"] > 0
    assert report["lesson_windows"]["surviving_three_demo_rotations"] == 0
