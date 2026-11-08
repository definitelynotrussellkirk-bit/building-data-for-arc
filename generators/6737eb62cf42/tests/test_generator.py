"""Portable regression tests for the 6737eb62cf42 crop curriculum."""
from __future__ import annotations

from collections import Counter, deque
from importlib.util import module_from_spec, spec_from_file_location
import json
import os
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "6737eb62cf42"
HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = spec_from_file_location(f"task_generator_{TASK_ID}", GENERATOR_PATH)
assert SPEC and SPEC.loader
GEN = module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)


def _pairs():
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def _crop_nonzero(grid):
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not cells:
        return [[0]]
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [list(row[c0 : c1 + 1]) for row in grid[r0 : r1 + 1]]


def _label(grid):
    return {"input": grid, "output": _crop_nonzero(grid)}


def _nonzero_components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells = set()
            while queue:
                current = queue.popleft()
                cells.add(current)
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = current[0] + dr, current[1] + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append((color, cells))
    return result


@pytest.mark.parametrize("pair", _pairs())
def test_canonical_pairs_are_lawful_and_match_independent_crop(pair):
    assert GEN.self_check(pair["input"]) == []
    assert GEN.strict_canonical_like(pair["input"]) == []
    assert _crop_nonzero(pair["input"]) == pair["output"]


def test_authority_and_schedule_contract_is_pinned():
    assert GEN.VERSION == "3.0.0"
    assert GEN.RULE_HASH == "debb1a8a129a"
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.LESSON_SCHEDULE_PERIOD == 20
    assert tuple(GEN.SCHEDULE_PROFILES) == tuple(GEN.PROFILE_DIMENSIONS)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("sample_index", range(20))
def test_schedule_profile_matches_the_declared_default_schedule(band, sample_index):
    assert GEN.schedule_profile(73, sample_index, band) == GEN.schedule_axes(
        73, sample_index, band
    )["scene_profile"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", [
    "canonical_8x9_crop4x6",
    "canonical_9x10_crop6x6",
    "canonical_10x10_crop4x6",
    "canonical_8x11_crop5x8",
    "canonical_9x10_crop5x7",
])
@pytest.mark.parametrize("placement", ["upper_left", "upper_right", "lower_left", "lower_right"])
@pytest.mark.parametrize("palette_size", [2, 3, 4])
@pytest.mark.parametrize("texture", ["paired_objects", "singleton_extreme"])
def test_complete_override_product_round_trips(
    band, profile, placement, palette_size, texture
):
    requested = {
        "scene_profile": profile,
        "placement": placement,
        "palette_size": palette_size,
        "texture": texture,
    }
    grid = GEN.generate(1701, 37, difficulty=band, **requested)
    assert GEN.self_check(grid, difficulty=band, meta={"overrides": requested}) == []
    assert GEN.observe_overrides(grid) == requested
    assert _crop_nonzero(grid) == GEN.rule_mirror(grid)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo_axis": 1},
        {"scene_profile": "not-a-profile"},
        {"scene_profile": None},
        {"placement": "center"},
        {"placement": 1},
        {"palette_size": 1},
        {"palette_size": 5},
        {"palette_size": True},
        {"palette_size": 3.0},
        {"texture": "no_cells"},
        {"texture": 1},
    ],
)
def test_invalid_and_retired_overrides_are_rejected(kwargs):
    with pytest.raises((KeyError, TypeError, ValueError)):
        GEN.generate(0, 0, **kwargs)


@pytest.mark.parametrize("difficulty", ["beginner", 1, False])
def test_unknown_difficulty_is_rejected(difficulty):
    with pytest.raises(ValueError):
        GEN.generate(0, 0, difficulty=difficulty)


@pytest.mark.parametrize("seed,sample_index", [(0, 0), (17, 3), (4400, 11)])
def test_difficulty_bands_are_pixel_observable_for_same_seed_and_slot(seed, sample_index):
    grids = [
        GEN.generate(seed, sample_index, difficulty=band)
        for band in ("easy", "medium", "hard")
    ]
    assert len({repr(grid) for grid in grids}) == 3


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_schedule_is_deterministic_and_covers_profiles_and_textures(band):
    observed = []
    for index in range(GEN.LESSON_SCHEDULE_PERIOD):
        grid = GEN.generate(4400, index, difficulty=band)
        assert grid == GEN.generate(4400, index, difficulty=band)
        assert GEN.self_check(grid) == []
        facts = GEN.observe_overrides(grid)
        assert facts == GEN.schedule_axes(4400, index, band)
        observed.append(facts)
    assert {item["scene_profile"] for item in observed} == set(GEN.SCHEDULE_PROFILES)
    assert {item["placement"] for item in observed} == set(GEN.PLACEMENTS)
    assert {item["texture"] for item in observed} == set(GEN.TEXTURES)
    assert {item["palette_size"] for item in observed} == {2, 3}
    assert sum(not GEN.strict_canonical_like(GEN.generate(4400, i, difficulty=band))
               for i in range(GEN.LESSON_SCHEDULE_PERIOD)) == 10


def test_declared_canonical_shortcuts_fit_every_canonical_label():
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in _pairs()), name


@pytest.mark.parametrize("index", range(1, 20, 2))
def test_singleton_schedule_cases_refute_canonical_shortcuts(index):
    grid = GEN.generate(8000 + index, index, difficulty="medium")
    assert GEN.observe_overrides(grid)["texture"] == "singleton_extreme"
    intended = _crop_nonzero(grid)
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert rival(grid) != intended, name


@pytest.mark.parametrize("index", range(20))
def test_every_default_case_refutes_largest_component_shortcut(index):
    grid = GEN.generate(9100 + index, index, difficulty="hard")
    intended = _crop_nonzero(grid)
    assert GEN.SEMANTIC_RIVALS["largest_monochrome_component"](grid) != intended
    components = _nonzero_components(grid)
    assert max(len(cells) for _, cells in components) == 4


@pytest.mark.parametrize("start", range(20))
def test_every_schedule_window_and_query_rotation_is_declared_rival_identifiable(start):
    grids = [GEN.generate(12000 + start, start + offset) for offset in range(4)]
    labelled = [_label(grid) for grid in grids]
    for query_index in range(4):
        query = labelled[query_index]
        demos = [pair for i, pair in enumerate(labelled) if i != query_index]
        assert GEN.lesson_identifiable(demos, query) == []
        for name, rival in GEN.LESSON_COMPETITORS.items():
            assert not (
                all(rival(pair["input"]) == pair["output"] for pair in demos)
                and rival(query["input"]) != query["output"]
            ), (start, query_index, name)


def test_semantic_witnesses_are_real_counterexamples():
    paired = GEN.generate(
        51,
        0,
        scene_profile="canonical_8x9_crop4x6",
        placement="upper_left",
        palette_size=2,
        texture="paired_objects",
    )
    singleton = GEN.generate(
        52,
        1,
        scene_profile="canonical_9x10_crop5x7",
        placement="lower_right",
        palette_size=3,
        texture="singleton_extreme",
    )
    cases = {"all_objects_define_crop": paired, "singleton_color_matters": singleton,
             "third_color_matters": singleton}
    for witness, grid in cases.items():
        assert GEN.SEMANTIC_WITNESSES[witness](grid), witness
        for rival_name in GEN.WITNESS_RIVALS[witness]:
            assert GEN.SEMANTIC_RIVALS[rival_name](grid) != _crop_nonzero(grid)


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True for _ in range(8)] for _ in range(8)],
        [[0 for _ in range(8)] for _ in range(8)],
        [[0, 0, 0, 0, 0], [0, 4, 4, 4, 0], [0, 0, 0, 0, 0]],
        [[1 for _ in range(8)] for _ in range(8)],
    ],
)
def test_self_check_rejects_malformed_empty_identity_and_minimal_impostors(grid):
    assert GEN.self_check(grid)


def test_self_check_rejects_unpadded_or_tiny_active_boxes():
    unpadded = [[0] * 8 for _ in range(8)]
    unpadded[0][1] = 2
    unpadded[3][4] = 3
    tiny = [[0] * 8 for _ in range(8)]
    tiny[2][2] = 2
    tiny[2][3] = 3
    assert GEN.self_check(unpadded)
    assert GEN.self_check(tiny)


def test_observe_overrides_rejects_a_non_profile_grid():
    grid = [[0] * 12 for _ in range(12)]
    grid[2][2] = 2
    grid[2][3] = 2
    grid[7][8] = 3
    grid[8][8] = 3
    assert GEN.self_check(grid) == []
    with pytest.raises(ValueError):
        GEN.observe_overrides(grid)


def test_retained_singleton_boundary_counterexample_matches_generator_and_rivals():
    path = HOME / "counterexamples" / "singleton-boundary.json"
    payload = json.loads(path.read_text())
    generation = payload["generation"]
    grid = GEN.generate(
        generation["seed"],
        generation["sample_index"],
        difficulty=generation["difficulty"],
        **generation["overrides"],
    )
    assert grid == payload["input"]
    assert GEN.self_check(grid) == []
    assert payload["racket_output"] == _crop_nonzero(grid)
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert payload["rival_outputs"][name] == rival(grid)
        assert payload["rival_outputs"][name] != payload["racket_output"]
