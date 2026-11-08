from __future__ import annotations

import importlib

import pytest

TASK = "edb34dd65185"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")


def _packed_height(grid: list[list[int]]) -> int:
    heights = []
    for _color, cells in GEN._components(grid):
        rows = [r for r, _ in cells]
        heights.append(max(rows) - min(rows) + 1)
    return sum(heights) + max(0, len(heights) - 1)


def _overflow_fixture() -> list[list[int]]:
    grid = [[0] * 19 for _ in range(16)]
    # Three lawful, distinct-hole objects with crop heights 3, 5 and 7.
    placements = [
        (1, 1, GEN._solid(3, 3), 8),
        (1, 8, GEN._ring(5, 5), 3),
        (8, 7, GEN._double_ring(7, 5), 7),
    ]
    for r0, c0, cells, color in placements:
        for r, c in cells:
            grid[r0 + r][c0 + c] = color
    return grid


def test_self_check_rejects_vertical_pack_overflow():
    grid = _overflow_fixture()
    assert _packed_height(grid) == 17 > len(grid)
    assert any("pack" in error.lower() for error in GEN.self_check(grid))


def test_retained_hard_seed_and_bounded_census_are_packable():
    retained = GEN.generate(2, 10, difficulty="hard")
    assert GEN.self_check(retained) == []
    assert _packed_height(retained) <= len(retained)

    for seed in range(80):
        grid = GEN.generate(seed, seed * 7 + 3, difficulty="hard")
        assert GEN.self_check(grid) == []
        assert _packed_height(grid) <= len(grid)

import importlib.util
from reviewer_support import find_root

HOME = find_root(__file__) / "generators" / TASK


def _load_prototype():
    path = HOME / "workspace/parametric/prototype.py"
    assert path.is_file(), "parametric prototype is not implemented"
    spec = importlib.util.spec_from_file_location("_edb_parametric_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


def test_parametric_default_is_exact_canonical_program():
    prototype = _load_prototype()
    canonical = (HOME / "workspace/parametric/canonical.rkt").read_text(encoding="utf-8")
    assert prototype.program({"order": "ascending"}) == canonical
    assert prototype.program({"order": "descending"}) != canonical


@pytest.mark.parametrize("demos", [2, 3, 6])
@pytest.mark.parametrize("order", ["ascending", "descending"])
def test_parametric_episode_counts_labels_uniqueness_and_30x30(order, demos):
    prototype = _load_prototype()
    settings = {"order": order}
    episode = prototype.generate(17, settings, demos, 4)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == 4
    inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
    assert len({_frozen(grid) for grid in inputs}) == demos + 4
    assert (len(inputs[-1]), len(inputs[-1][0])) == (30, 30)
    assert sum(cell != 0 for row in inputs[-1] for cell in row) >= 45
    for pair in episode["train"] + episode["test"]:
        assert pair["output"] == prototype.transform(pair["input"], settings)
        assert GEN.self_check(pair["input"]) == []
        assert _packed_height(pair["input"]) <= len(pair["input"])


def test_parametric_inputs_match_across_settings_and_demos_identify_order():
    prototype = _load_prototype()
    episodes = {
        order: prototype.generate(29, {"order": order}, 2, 4)
        for order in ("ascending", "descending")
    }
    for split in ("train", "test"):
        assert [p["input"] for p in episodes["ascending"][split]] == [
            p["input"] for p in episodes["descending"][split]
        ]
    for chosen, episode in episodes.items():
        survivors = []
        for candidate in ("ascending", "descending"):
            if all(
                prototype.transform(pair["input"], {"order": candidate}) == pair["output"]
                for pair in episode["train"]
            ):
                survivors.append(candidate)
        assert survivors == [chosen]
    assert episodes["ascending"]["test"][0]["output"] != episodes["descending"]["test"][0]["output"]


def test_parametric_count_prefixes_are_stable():
    prototype = _load_prototype()
    short = prototype.generate(41, {"order": "descending"}, 2, 1)
    long = prototype.generate(41, {"order": "descending"}, 6, 4)
    assert short["train"] == long["train"][:2]
    assert short["test"] == long["test"][:1]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"seed": True},
        {"seed": -1},
        {"settings": {}},
        {"settings": {"order": "sideways"}},
        {"demos": 1},
        {"demos": 7},
        {"queries": 0},
        {"queries": 5},
    ],
)
def test_parametric_invalid_requests_fail_closed(kwargs):
    prototype = _load_prototype()
    args = {"seed": 0, "settings": {"order": "ascending"}, "demos": 2, "queries": 4}
    args.update(kwargs)
    with pytest.raises(ValueError):
        prototype.generate(**args)


def _rival_pack(prototype, grid, rival):
    entries = []
    for _color, cells in prototype._components(grid):
        crop = prototype._crop(grid, cells)
        entries.append(
            {
                "holes": prototype._crop_holes(crop),
                "area": sum(value != 0 for row in crop for value in row),
                "color": min(value for row in crop for value in row if value != 0),
                "crop": crop,
            }
        )
    if rival == "scan_order":
        ordered = entries
    elif rival == "reverse_scan":
        ordered = list(reversed(entries))
    elif rival == "area_ascending":
        ordered = sorted(entries, key=lambda entry: (entry["area"], entry["color"]))
    elif rival == "area_descending":
        ordered = sorted(entries, key=lambda entry: (-entry["area"], entry["color"]))
    elif rival == "color_ascending":
        ordered = sorted(entries, key=lambda entry: entry["color"])
    elif rival == "color_descending":
        ordered = sorted(entries, key=lambda entry: -entry["color"])
    else:
        raise AssertionError(rival)
    output = [[0 for _ in row] for row in grid]
    top = 0
    for entry in ordered:
        crop = entry["crop"]
        for r, row in enumerate(crop):
            for c, value in enumerate(row):
                if value != 0:
                    output[top + r][c] = value
        top += len(crop) + 1
    return output


def test_two_demos_reject_plausible_fixed_shortcuts():
    prototype = _load_prototype()
    rivals = (
        "scan_order",
        "reverse_scan",
        "area_ascending",
        "area_descending",
        "color_ascending",
        "color_descending",
    )
    for seed in range(16):
        for order in ("ascending", "descending"):
            episode = prototype.generate(seed, {"order": order}, 2, 4)
            survivors = [
                rival
                for rival in rivals
                if all(
                    _rival_pack(prototype, pair["input"], rival) == pair["output"]
                    for pair in episode["train"]
                )
            ]
            assert survivors == [], (seed, order, survivors)
