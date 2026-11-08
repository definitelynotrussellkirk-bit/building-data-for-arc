from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

TASK_DIR = Path(__file__).resolve().parents[1]
PARAM_DIR = TASK_DIR / "workspace" / "parametric"
REPO = TASK_DIR.parents[1]


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    programs = set()
    ledger = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in ledger.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == "c792bb147617":
            programs.add(row["program_solution"])
    assert len(programs) == 1
    return programs.pop()


def test_promotion_contract_declares_four_palette_rotations() -> None:
    promotion = PARAM_DIR / "promotion.json"
    adapter = PARAM_DIR / "adapter.py"
    prototype = PARAM_DIR / "prototype.py"

    assert prototype.is_file(), "prototype.py must define the proposed rule family"
    assert adapter.is_file(), "adapter.py must expose the promotion interface"
    assert promotion.is_file(), "promotion.json must bind the finite settings"

    contract = json.loads(promotion.read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/c792bb147617/workspace/parametric/adapter.py",
        "parameters": {
            "orientation": ["canonical", "rotate_cw", "rotate_180", "rotate_ccw"]
        },
        "default": {"orientation": "canonical"},
        "limits": {"demos": [2, 8], "queries": [1, 8]},
    }


def test_program_materialization_preserves_canonical_and_rotates_only_palette() -> None:
    prototype = _load(PARAM_DIR / "prototype.py", "test_palette_rotation_prototype_program")

    expected_maps = {
        "canonical": {"up": 2, "left": 7, "right": 6, "down": 8},
        "rotate_cw": {"up": 7, "left": 8, "right": 2, "down": 6},
        "rotate_180": {"up": 8, "left": 6, "right": 7, "down": 2},
        "rotate_ccw": {"up": 6, "left": 2, "right": 8, "down": 7},
    }
    programs = {name: prototype.program_for(name) for name in expected_maps}

    assert prototype.ORIENTATIONS == tuple(expected_maps)
    assert prototype.DIRECTION_COLORS == expected_maps
    assert programs["canonical"] == _canonical_program()
    assert len(set(programs.values())) == 4
    for name, mapping in expected_maps.items():
        program = programs[name]
        assert f"(hash-set! result (list (- r 1) c) {mapping['up']})" in program
        assert f"(hash-set! result (list r (- c 1)) {mapping['left']})" in program
        assert f"(hash-set! result (list r (+ c 1)) {mapping['right']})" in program
        assert f"(hash-set! result (list (+ r 1) c) {mapping['down']})" in program


def test_transform_rotates_palette_clips_boundaries_and_preserves_input() -> None:
    prototype = _load(PARAM_DIR / "prototype.py", "test_palette_rotation_prototype_transform")
    source = [[0 for _ in range(6)] for _ in range(6)]
    source[2][2] = 1
    source[0][5] = 1
    original = copy.deepcopy(source)

    for orientation, mapping in prototype.DIRECTION_COLORS.items():
        expected = copy.deepcopy(source)
        expected[1][2] = mapping["up"]
        expected[2][1] = mapping["left"]
        expected[2][3] = mapping["right"]
        expected[3][2] = mapping["down"]
        expected[0][4] = mapping["left"]
        expected[1][5] = mapping["down"]
        assert prototype.transform(source, orientation) == expected

    assert source == original


def test_episode_generation_is_deterministic_setting_neutral_unique_and_labeled() -> None:
    prototype = _load(PARAM_DIR / "prototype.py", "test_palette_rotation_prototype_episode")
    episodes = {
        orientation: prototype.generate_episode(17, orientation, demos=3, queries=4)
        for orientation in prototype.ORIENTATIONS
    }

    canonical_inputs = [
        pair["input"]
        for split in ("train", "test")
        for pair in episodes["canonical"][split]
    ]
    assert len(canonical_inputs) == 7
    assert len({json.dumps(grid, separators=(",", ":")) for grid in canonical_inputs}) == 7

    for orientation, episode in episodes.items():
        assert episode == prototype.generate_episode(17, orientation, demos=3, queries=4)
        assert episode["program_solution"] == prototype.program_for(orientation)
        inputs = [pair["input"] for split in ("train", "test") for pair in episode[split]]
        assert inputs == canonical_inputs
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 4
        for split in ("train", "test"):
            for pair in episode[split]:
                assert pair["output"] == prototype.transform(pair["input"], orientation)


def test_adapter_is_thin_exact_and_uses_requested_counts() -> None:
    prototype = _load(PARAM_DIR / "prototype.py", "test_palette_rotation_prototype_adapter_expected")
    adapter = _load(PARAM_DIR / "adapter.py", "test_palette_rotation_adapter")
    settings = {"orientation": "rotate_180"}

    assert adapter.program(settings) == prototype.program_for("rotate_180")
    assert adapter.generate(23, settings, 2, 4) == prototype.generate_episode(
        23, "rotate_180", demos=2, queries=4
    )


def test_two_demonstrations_identify_each_orientation_as_sole_survivor() -> None:
    prototype = _load(PARAM_DIR / "prototype.py", "test_palette_rotation_prototype_survivors")
    for orientation in prototype.ORIENTATIONS:
        episode = prototype.generate_episode(31, orientation, demos=2, queries=4)
        assert prototype.surviving_orientations(episode["train"]) == (orientation,)


@pytest.mark.parametrize(
    "settings",
    [
        {},
        {"orientation": "canonical", "extra": 1},
        {"orientation": "unknown"},
        {"orientation": 0},
    ],
)
def test_adapter_rejects_settings_outside_the_exact_contract(settings) -> None:
    adapter = _load(PARAM_DIR / "adapter.py", "test_palette_rotation_adapter_invalid")
    with pytest.raises((TypeError, ValueError)):
        adapter.program(settings)


def test_supported_max_counts_are_distinct_and_bounds_fail_loudly() -> None:
    prototype = _load(PARAM_DIR / "prototype.py", "test_palette_rotation_prototype_limits")
    episode = prototype.generate_episode(2**63 - 1, "canonical", demos=8, queries=8)
    pairs = episode["train"] + episode["test"]
    assert len(pairs) == 16
    assert len({json.dumps(pair["input"], separators=(",", ":")) for pair in pairs}) == 16

    invalid_calls = [
        (True, "canonical", 3, 4),
        (0, "unknown", 3, 4),
        (0, "canonical", 1, 4),
        (0, "canonical", 9, 4),
        (0, "canonical", 3, 0),
        (0, "canonical", 3, 9),
    ]
    for seed, orientation, demos, queries in invalid_calls:
        with pytest.raises(ValueError):
            prototype.generate_episode(seed, orientation, demos=demos, queries=queries)


def test_shared_neighbor_writes_follow_canonical_row_major_order() -> None:
    prototype = _load(PARAM_DIR / "prototype.py", "test_palette_rotation_prototype_overlap")
    source = [[0 for _ in range(6)] for _ in range(6)]
    source[2][1] = 1
    source[2][3] = 1
    source[1][5] = 1
    source[3][5] = 1

    for orientation, colors in prototype.DIRECTION_COLORS.items():
        output = prototype.transform(source, orientation)
        assert output[2][2] == colors["left"]
        assert output[2][5] == colors["up"]
