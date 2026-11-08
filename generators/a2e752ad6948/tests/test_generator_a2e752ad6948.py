from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from collections import Counter
from pathlib import Path

import pytest


TASK_ID = "a2e752ad6948"
ROOT = Path(__file__).resolve().parents[1]
MODULE = importlib.import_module(
    "puzzle_generators.per_puzzle.a2e752ad6948.generator"
)


def _canonical_row() -> dict:
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"canonical task {TASK_ID} not found")


def _canonical_pairs() -> list[dict]:
    row = _canonical_row()
    test = row.get("test")
    tests = test if isinstance(test, list) else ([test] if test else [])
    return [*row.get("train", []), *tests]


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _source_authorities() -> list[str]:
    row = _canonical_row()
    base = json.loads(
        (
            ROOT
            / "data/base/solutions/banks/be1bc1d91387/M136__a2e752ad6948.json"
        ).read_text()
    )
    from puzzle_generators.runner import _load_rule

    loaded_rule, _ = _load_rule(TASK_ID)
    return [
        row["program_solution"],
        base["racket_target"]["raw_code"],
        base["racket_target"]["target_code"],
        loaded_rule,
    ]


def _expected_output(grid: list[list[int]]) -> list[list[int]]:
    """Independent test oracle for the written checker-frame semantics."""
    out = copy.deepcopy(grid)
    frames, extras = MODULE._analyze(grid)
    assert not extras
    for frame in frames:
        assert len(frame["markers"]) == 1
        marker_color = frame["markers"][0][2]
        for r in range(frame["r1"] + 1, frame["r2"]):
            for c in range(frame["c1"] + 1, frame["c2"]):
                local_parity = (
                    r - (frame["r1"] + 1) + c - (frame["c1"] + 1)
                ) % 2
                out[r][c] = marker_color if local_parity == 0 else frame["color"]
    return out


def _marker_anchored_shortcut(grid: list[list[int]]) -> list[list[int]]:
    """Tempting wrong rule: put marker color on the marker's checker phase."""
    out = copy.deepcopy(grid)
    frames, extras = MODULE._analyze(grid)
    assert not extras
    for frame in frames:
        assert len(frame["markers"]) == 1
        marker_r, marker_c, marker_color = frame["markers"][0]
        for r in range(frame["r1"] + 1, frame["r2"]):
            for c in range(frame["c1"] + 1, frame["c2"]):
                same_phase = (r + c - marker_r - marker_c) % 2 == 0
                out[r][c] = marker_color if same_phase else frame["color"]
    return out


def _frame_profile(frame: dict) -> str:
    if frame["h"] == frame["w"]:
        return "square"
    return "tall" if frame["h"] > frame["w"] else "wide"


def _fresh_color(grid: list[list[int]]) -> int:
    used = {value for row in grid for value in row}
    return next(color for color in range(1, 10) if color not in used)


def test_canonical_inventory_rule_pin_source_sync_and_acceptance() -> None:
    row = _canonical_row()
    pairs = _canonical_pairs()
    assert len(row["train"]) == 4
    assert len(pairs) == 5

    hashes = {_normalized_hash(source) for source in _source_authorities()}
    assert hashes == {"39fb0a2b12e8"}
    assert MODULE.RULE_HASH == hashes.pop()

    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        before = copy.deepcopy(source)
        assert MODULE.self_check(source) == []
        assert _expected_output(source) == pair["output"]
        assert source == before


def test_declared_axes_are_exact_observable_and_cover_boundaries() -> None:
    assert set(MODULE.AXES) == {
        "grid_h",
        "grid_w",
        "layout",
        "marker_phase",
        "texture",
    }
    assert set(MODULE.HELPFUL_TEXTURES) == set(MODULE.TEXTURES)
    assert MODULE.DEGENERATE_TEXTURES == ()

    draw = 0
    for band in ("easy", "medium", "hard"):
        for h, w in ((11, 12), (17, 20)):
            for layout in MODULE.LAYOUTS:
                for marker_phase in MODULE.MARKER_PHASES:
                    for texture in MODULE.TEXTURES:
                        draw += 1
                        overrides = {
                            "grid_h": h,
                            "grid_w": w,
                            "layout": layout,
                            "marker_phase": marker_phase,
                            "texture": texture,
                        }
                        grid = MODULE.generate(
                            17000 + draw,
                            19000 + draw,
                            difficulty=band,
                            **overrides,
                        )
                        assert MODULE.self_check(grid) == []
                        assert MODULE.observe_overrides(grid) == overrides


@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 10},
        {"grid_h": 18},
        {"grid_w": 11},
        {"grid_w": 21},
        {"layout": "stacked"},
        {"marker_phase": "even"},
        {"texture": "monochrome"},
        {"unknown_axis": 1},
    ],
)
def test_invalid_axis_values_reject_loudly(overrides: dict) -> None:
    with pytest.raises(ValueError):
        MODULE.generate(1, 2, difficulty="medium", **overrides)


def test_default_census_guarantees_two_local_frames_and_blocks_shortcuts() -> None:
    for band_index, band in enumerate(("easy", "medium", "hard")):
        layouts = Counter()
        phases = Counter()
        textures = Counter()
        profiles = Counter()
        inputs = set()
        outputs = set()
        for seed in range(120):
            grid = MODULE.generate(
                21000 + band_index * 1000 + seed,
                31 * seed + 7,
                difficulty=band,
            )
            assert MODULE.self_check(grid) == []
            observed = MODULE.observe_overrides(grid)
            layouts[observed["layout"]] += 1
            phases[observed["marker_phase"]] += 1
            textures[observed["texture"]] += 1

            frames, extras = MODULE._analyze(grid)
            assert len(frames) == 2
            assert extras == []
            assert all(4 <= frame["h"] <= 6 for frame in frames)
            assert all(4 <= frame["w"] <= 6 for frame in frames)
            assert all(len(frame["markers"]) == 1 for frame in frames)
            assert len(
                {
                    frames[0]["color"],
                    frames[0]["markers"][0][2],
                    frames[1]["color"],
                    frames[1]["markers"][0][2],
                }
            ) == 4
            profiles.update(_frame_profile(frame) for frame in frames)

            output = _expected_output(grid)
            assert output != grid
            assert _marker_anchored_shortcut(grid) != output
            inputs.add(tuple(map(tuple, grid)))
            outputs.add(tuple(map(tuple, output)))

        assert set(layouts) == set(MODULE.LAYOUTS)
        assert set(phases) == set(MODULE.MARKER_PHASES)
        assert set(textures) == set(MODULE.TEXTURES)
        assert set(profiles) == {"square", "wide", "tall"}
        assert len(inputs) >= 118
        assert len(outputs) >= 118


def test_determinism_fresh_returns_and_global_rng_purity() -> None:
    random.seed(20260723)
    state = random.getstate()
    first = MODULE.generate(97, 103, difficulty="hard")
    assert random.getstate() == state
    second = MODULE.generate(97, 103, difficulty="hard")
    assert random.getstate() == state

    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second


def test_self_check_rejects_structural_impostors_and_recombinations() -> None:
    base = MODULE.generate(
        451,
        919,
        difficulty="hard",
        grid_h=17,
        grid_w=20,
        layout="diagonal_down",
        marker_phase="mixed",
        texture="default",
    )
    frames, _ = MODULE._analyze(base)

    all_zero = [[0] * 12 for _ in range(11)]
    singleton = [[0] * 12 for _ in range(11)]
    singleton[5][5] = 1
    solid_2x2 = [[0] * 12 for _ in range(11)]
    for r in (4, 5):
        for c in (5, 6):
            solid_2x2[r][c] = 2

    broken_corner = copy.deepcopy(base)
    broken_corner[frames[0]["r1"]][frames[0]["c1"]] = 0

    missing_marker = copy.deepcopy(base)
    marker_r, marker_c, _ = frames[0]["markers"][0]
    missing_marker[marker_r][marker_c] = 0

    fresh_color_extra = copy.deepcopy(base)
    fresh_color_extra[0][0] = _fresh_color(base)

    border_color_interior = copy.deepcopy(base)
    first = frames[0]
    border_color_interior[first["r1"] + 1][first["c1"] + 1] = first["color"]

    reused_role_color = copy.deepcopy(base)
    second_marker_r, second_marker_c, _ = frames[1]["markers"][0]
    reused_role_color[second_marker_r][second_marker_c] = frames[0]["color"]

    oversized = [[0] * 18 for _ in range(12)]
    for r in range(1, 8):
        for c in range(1, 8):
            if r in (1, 7) or c in (1, 7):
                oversized[r][c] = 2
    oversized[3][3] = 4
    for r in range(2, 6):
        for c in range(11, 15):
            if r in (2, 5) or c in (11, 14):
                oversized[r][c] = 6
    oversized[3][12] = 8

    touching = [[0] * 15 for _ in range(10)]
    for r in range(2, 6):
        for c in range(1, 5):
            if r in (2, 5) or c in (1, 4):
                touching[r][c] = 1
    touching[3][2] = 2
    for r in range(2, 6):
        for c in range(5, 9):
            if r in (2, 5) or c in (5, 8):
                touching[r][c] = 3
    touching[3][6] = 4

    for name, mutation in {
        "all_zero": all_zero,
        "singleton": singleton,
        "solid_2x2": solid_2x2,
        "broken_corner": broken_corner,
        "missing_marker": missing_marker,
        "fresh_color_extra": fresh_color_extra,
        "border_color_interior": border_color_interior,
        "reused_role_color": reused_role_color,
        "oversized": oversized,
        "touching": touching,
    }.items():
        assert MODULE.self_check(mutation), name


def test_generated_output_is_local_and_input_remains_unchanged() -> None:
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for seed in range(40):
            grid = MODULE.generate(
                31000 + band_index * 1000 + seed,
                37 * seed + 11,
                difficulty=band,
            )
            before = copy.deepcopy(grid)
            output = _expected_output(grid)
            assert grid == before
            frames, _ = MODULE._analyze(grid)
            for frame in frames:
                marker_color = frame["markers"][0][2]
                allowed = {frame["color"], marker_color}
                interior = {
                    output[r][c]
                    for r in range(frame["r1"] + 1, frame["r2"])
                    for c in range(frame["c1"] + 1, frame["c2"])
                }
                assert interior == allowed
