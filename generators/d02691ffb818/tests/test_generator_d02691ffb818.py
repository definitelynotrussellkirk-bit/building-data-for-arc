"""Source-bound regression tests for d02691ffb818.

The Python stencil below is an independent test oracle.  The selected Racket
program remains the label authority and is exercised by the packet battery.
"""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from typing import Iterable

import pytest

HOME = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[3]
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))


def _load_generator():
    spec = importlib.util.spec_from_file_location("generator_d02691ffb818", GENERATOR_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _canonical_record() -> dict:
    candidates = (
        REPO / "shared/data/canonical/puzzles.jsonl",
        REPO / "data/canonical/puzzles.jsonl",
    )
    for path in candidates:
        if not path.exists():
            continue
        for line in path.read_text().splitlines():
            record = json.loads(line)
            if record.get("task_id") == "d02691ffb818":
                return record
    raise AssertionError("canonical task record not found")


def _pairs() -> list[dict]:
    task = _canonical_record()
    return list(task["train"]) + list(task["test"])


def stamp_x(grid: list[list[int]], *, ignore_border: bool = False,
            drop_clustered: bool = False) -> list[list[int]]:
    """Independent geometry oracle for the written/Racket rule."""
    h, w = len(grid), len(grid[0])
    markers = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
               if value == 1]
    out = [[0 for _ in range(w)] for _ in range(h)]
    for r, c in markers:
        if ignore_border and (r in (0, h - 1) or c in (0, w - 1)):
            continue
        if drop_clustered and any(
            (rr, cc) != (r, c) and max(abs(r - rr), abs(c - cc)) <= 2
            for rr, cc in markers
        ):
            continue
        for dr, dc in ((0, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)):
            rr, cc = r + dr, c + dc
            if 0 <= rr < h and 0 <= cc < w:
                out[rr][cc] = 7
    return out


def markers(grid: list[list[int]]) -> list[tuple[int, int]]:
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
            if value == 1]


def has_border_marker(grid: list[list[int]]) -> bool:
    h, w = len(grid), len(grid[0])
    return any(r in (0, h - 1) or c in (0, w - 1) for r, c in markers(grid))


def has_clustered_pair(grid: list[list[int]]) -> bool:
    points = markers(grid)
    return any(
        max(abs(r - rr), abs(c - cc)) <= 2
        for i, (r, c) in enumerate(points)
        for rr, cc in points[i + 1:]
    )


def test_python_oracle_matches_every_canonical_pair():
    for pair in _pairs():
        assert stamp_x(pair["input"]) == pair["output"]


def test_authority_pin_and_validator_accept_every_canonical_input():
    assert gen.RULE_HASH == "3eec1d7807b1"
    for pair in _pairs():
        assert gen.self_check(pair["input"]) == []


def test_validator_accepts_lawful_clipping_and_overlap_cases():
    edge = [[0] * 7 for _ in range(7)]
    edge[0][0] = 1
    edge[3][3] = 1
    close = [[0] * 7 for _ in range(7)]
    close[3][3] = 1
    close[3][5] = 1
    assert gen.self_check(edge) == []
    assert gen.self_check(close) == []
    assert stamp_x(edge)[0][0] == 7
    assert stamp_x(close) != close


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_public_overrides_are_exact_in_every_band_and_unknown_keys_reject(band):
    for count in (2, 14):
        grid = gen.generate(17, 5, difficulty=band, grid_h=5, grid_w=5, markers=count)
        assert (len(grid), len(grid[0]), len(markers(grid))) == (5, 5, count)
        assert gen.self_check(grid) == []
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, difficulty=band, grid_h=5, grid_w=5, markers=1)
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, difficulty=band, __override_contract_unknown_axis__=1)


def test_validator_rejects_minimal_non_teaching_impostors():
    singleton = [[0] * 7 for _ in range(7)]
    singleton[3][3] = 1

    short_line = [[0] * 7 for _ in range(7)]
    for c in range(4):
        short_line[3][c] = 1

    solid_2x2 = [[0] * 7 for _ in range(7)]
    for r in range(2):
        for c in range(2):
            solid_2x2[r][c] = 1

    assert gen.self_check(singleton)
    assert gen.self_check(short_line)
    assert gen.self_check(solid_2x2)


def test_clipped_border_witness_requires_output_relevant_border_contribution():
    # Regression from the 600-draw semantic census: the two border markers
    # are fully covered by nearby interior stamps, so deleting them leaves the
    # output unchanged.  Mere border presence is not a valid rival witness.
    grid = [
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 1, 0, 1],
        [0, 0, 0, 0, 0, 1, 1, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
    ]
    assert has_border_marker(grid)
    assert gen.CANONICAL_SHORTCUTS["ignore_border_markers"](grid) == stamp_x(grid)
    assert not gen.SEMANTIC_WITNESSES["clipped_border_x"](grid)


def test_edge_profile_guarantees_an_output_relevant_clipped_border_stamp():
    # Regression from the 1,000-lessons-per-band census.  The old edge layout
    # produced markers at (0, 0) and (1, 1), so the interior stamp covered every
    # cell contributed by the border marker and ignore_border_markers survived.
    seed = 6121770150353974458
    sample_index = 3016
    grid = gen.generate(seed, sample_index, difficulty="easy")
    assert gen.schedule_profile(seed, sample_index, "easy") == "edge"
    assert gen.SEMANTIC_WITNESSES["clipped_border_x"](grid)
    assert gen.CANONICAL_SHORTCUTS["ignore_border_markers"](grid) != stamp_x(grid)


def test_default_schedule_covers_canonical_edge_and_cluster_profiles():
    assert tuple(gen.SCHEDULE_PROFILES) == ("canonical", "edge", "clustered")
    grids = [gen.generate(41, index, difficulty="medium") for index in range(3)]
    assert [gen.schedule_profile(41, index, "medium") for index in range(3)] == list(gen.SCHEDULE_PROFILES)
    assert gen.strict_canonical_like(grids[0]) == []
    assert has_border_marker(grids[1])
    assert has_clustered_pair(grids[2])
    assert gen.SEMANTIC_WITNESSES["clipped_border_x"](grids[1])
    assert gen.SEMANTIC_WITNESSES["overlapping_x_union"](grids[2])


def test_each_band_has_canonical_profile_support_in_twenty_draws():
    canonical_profiles = {
        (len(pair["input"]), len(pair["input"][0]), len(set(sum(pair["input"], []))))
        for pair in _pairs()
    }
    # The shared profile gate uses dimensions plus number of input colors.
    for band in ("easy", "medium", "hard"):
        observed = set()
        for index in range(20):
            grid = gen.generate(1234 + index, index, difficulty=band)
            observed.add((len(grid), len(grid[0]), len(set(sum(grid, [])))))
        assert observed & canonical_profiles, (band, observed, canonical_profiles)


def test_canonical_shortcuts_fit_canonical_and_generated_profiles_refute_them():
    assert {"ignore_border_markers", "drop_clustered_markers"} <= set(gen.CANONICAL_SHORTCUTS)
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in _pairs()), name

    edge = gen.generate(7, 1, difficulty="easy")
    cluster = gen.generate(7, 2, difficulty="easy")
    assert gen.CANONICAL_SHORTCUTS["ignore_border_markers"](edge) != stamp_x(edge)
    assert gen.CANONICAL_SHORTCUTS["drop_clustered_markers"](cluster) != stamp_x(cluster)


def test_every_three_example_window_refutes_all_declared_competitors():
    assert gen.EXAMPLES_NEEDED == 3
    assert set(gen.LESSON_COMPETITORS) >= {
        "ignore_border_markers",
        "drop_clustered_markers",
        "center_only",
        "cardinal_cross",
        "preserve_blue_center",
    }
    for band in ("easy", "medium", "hard"):
        for start in range(9):
            demos = []
            for offset in range(gen.EXAMPLES_NEEDED):
                grid = gen.generate(900 + start, start + offset, difficulty=band)
                demos.append({"input": grid, "output": stamp_x(grid)})
            query_grid = gen.generate(1900 + start, start + gen.EXAMPLES_NEEDED, difficulty=band)
            query = {"input": query_grid, "output": stamp_x(query_grid)}
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(demo["input"]) != demo["output"] for demo in demos), (band, start, name)


def test_default_draws_are_deterministic_valid_and_nontrivial():
    for band in ("easy", "medium", "hard"):
        for index in range(30):
            grid = gen.generate(500 + index, index, difficulty=band)
            assert grid == gen.generate(500 + index, index, difficulty=band)
            assert gen.self_check(grid) == []
            assert stamp_x(grid) != grid


def test_source_bound_review_probe_covers_declared_rivals_and_cyclic_starts():
    probe_path = HOME / "workspace" / "review_probe.py"
    assert probe_path.is_file(), "source-bound review probe is missing"
    spec = importlib.util.spec_from_file_location("review_probe_d02691ffb818", probe_path)
    assert spec and spec.loader
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)

    report = probe.run_probe(lessons_per_band=3)
    assert report["status"] == "pass", report["failures"]
    assert report["totals"]["lessons"] == 9
    assert report["totals"]["demo_draws"] == 27
    assert all(row["canonical_pairs_matched"] == row["canonical_pairs_total"]
               for row in report["canonical_shortcuts"].values())
    assert all(row["lessons_survived"] == 0
               for row in report["lesson_competitors"].values())
    assert set(report["cyclic_starts"]) == {"0", "1", "2"}
    assert all(row["lessons"] > 0 and row["unidentifiable"] == 0
               for row in report["cyclic_starts"].values())
