from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

TASK_ID = "1b9d8370e28b"
GENERATOR_PATH = Path(__file__).resolve().parents[1] / "generator.py"
REPO_ROOT = Path(__file__).resolve().parents[3]


def _load_generator():
    name = f"generator_{TASK_ID}_{hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest()[:8]}"
    spec = importlib.util.spec_from_file_location(name, GENERATOR_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_row():
    with (REPO_ROOT / "shared/data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"canonical row {TASK_ID} not found")


def _layout(grid):
    h, w = len(grid), len(grid[0])
    candidates = []
    for split in range(1, h):
        for first in (1, 8):
            second = 1 if first == 8 else 8
            if all(v == 2 or v == (first if r < split else second)
                   for r, row in enumerate(grid) for v in row):
                candidates.append(("h", split, first))
    for split in range(1, w):
        for first in (1, 8):
            second = 1 if first == 8 else 8
            if all(v == 2 or v == (first if c < split else second)
                   for row in grid for c, v in enumerate(row)):
                candidates.append(("v", split, first))
    assert len(candidates) == 1, candidates
    return candidates[0]


def _intended(grid):
    axis, split, first = _layout(grid)
    h, w = len(grid), len(grid[0])
    second = 1 if first == 8 else 8
    out = [[first if (r < split if axis == "h" else c < split) else second
            for c in range(w)] for r in range(h)]
    for r in range(h):
        regions = [(0, w)] if axis == "h" else [(0, split), (split, w)]
        for c0, c1 in regions:
            bg = out[r][c0]
            count = sum(grid[r][c] == 2 for c in range(c0, c1))
            if bg == 8:
                for c in range(c0, c0 + count):
                    out[r][c] = 2
            else:
                for c in range(c1 - count, c1):
                    out[r][c] = 2
    return out


def _red_components(grid):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2}
    components = []
    while unseen:
        start = min(unseen)
        stack = [start]
        unseen.remove(start)
        component = {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                point = (r + dr, c + dc)
                if point in unseen:
                    unseen.remove(point)
                    component.add(point)
                    stack.append(point)
        components.append(component)
    return components


def test_metadata_and_unknown_override_contract():
    gen = _load_generator()
    assert gen.GENERATOR_ID == TASK_ID
    assert gen.TASK_ID == TASK_ID
    assert gen.RULE_HASH == "c5b820b4a73f"
    assert set(gen.AXES) == {"grid_h", "grid_w", "split_axis", "tl_color"}
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis=7)


@pytest.mark.parametrize(
    "options",
    [
        {"grid_h": 9, "grid_w": 9, "split_axis": "h", "tl_color": 8},
        {"grid_h": 15, "grid_w": 15, "split_axis": "h", "tl_color": 1},
        {"grid_h": 10, "grid_w": 11, "split_axis": "v", "tl_color": 8},
        {"grid_h": 12, "grid_w": 14, "split_axis": "v", "tl_color": 1},
    ],
)
def test_exact_overrides_round_trip(options):
    gen = _load_generator()
    grid = gen.generate(123, 17, difficulty="hard", **options)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == options
    assert grid == gen.generate(123, 17, difficulty="hard", **options)


def test_canonical_pairs_are_accepted_and_match_independent_oracle():
    gen = _load_generator()
    row = _canonical_row()
    for pair in row["train"] + row["test"]:
        assert gen.self_check(pair["input"]) == []
        assert gen.self_check(pair["output"]) == []
        assert _intended(pair["input"]) == pair["output"]


def test_rigid_component_shortcut_fits_canonical_but_generated_cases_refute_it():
    gen = _load_generator()
    row = _canonical_row()
    for pair in row["train"] + row["test"]:
        assert gen._rigid_components(pair["input"]) == pair["output"]

    witness_hits = 0
    inputs = set()
    component_counts = []
    for band in ("easy", "medium", "hard"):
        for i in range(40):
            grid = gen.generate(7000 + i, i, difficulty=band)
            assert gen.self_check(grid) == []
            assert _intended(grid) != grid
            components = _red_components(grid)
            component_counts.append(len(components))
            assert 3 <= len(components) <= 5
            inputs.add(json.dumps(grid, separators=(",", ":")))
            if gen.SEMANTIC_WITNESSES["ragged_component"](grid):
                witness_hits += 1
                assert gen._rigid_components(grid) != _intended(grid)

    assert witness_hits >= 90
    assert len(inputs) >= 110
    assert min(component_counts) >= 3 and max(component_counts) <= 5
    assert gen.WITNESS_RIVALS == {"ragged_component": ["rigid_components"]}
    assert set(gen.CANONICAL_SHORTCUTS) == {"rigid_components"}
    assert set(gen.LESSON_COMPETITORS) == {"rigid_components"}


def test_self_check_rejects_minimal_impostors():
    gen = _load_generator()
    background = [[8 if r < 4 else 1 for _ in range(9)] for r in range(9)]
    cases = []
    cases.append(background)

    singleton = [row[:] for row in background]
    singleton[1][4] = 2
    cases.append(singleton)

    one_region_only = [row[:] for row in background]
    one_region_only[1][3] = one_region_only[1][4] = 2
    one_region_only[2][3] = one_region_only[2][4] = 2
    cases.append(one_region_only)

    bad_palette = [row[:] for row in background]
    bad_palette[1][3] = 2
    bad_palette[6][5] = 2
    bad_palette[0][0] = 4
    cases.append(bad_palette)

    for grid in cases:
        assert gen.self_check(grid), grid

    assert gen.self_check([[8, 8], [1]])


def test_source_bound_rival_probe_smoke():
    probe_path = GENERATOR_PATH.parent / "workspace" / "rival_probe.py"
    name = f"rival_probe_{hashlib.sha256(probe_path.read_bytes()).hexdigest()[:8]}"
    spec = importlib.util.spec_from_file_location(name, probe_path)
    assert spec and spec.loader
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)

    report = probe.build_report(
        generator_path=GENERATOR_PATH,
        canonical_path=REPO_ROOT / "shared/data/canonical/puzzles.jsonl",
        lessons_per_band=2,
        base_seed=910_000,
    )
    assert report["generator_sha256"] == hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest()
    assert report["canonical"]["rigid_components"]["fits"] == report["canonical"]["pair_count"]
    for band in ("easy", "medium", "hard"):
        stats = report["per_band"][band]
        assert stats["lessons"] == 2
        assert stats["strict_rejections"] == 0
        assert stats["lesson_competitors"]["rigid_components"]["demo_refuted"] == 2
