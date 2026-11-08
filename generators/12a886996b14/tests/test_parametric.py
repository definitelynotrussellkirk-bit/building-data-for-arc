"""Native parametric contract for the translation-to-cue relay family."""
from __future__ import annotations

import importlib.util
import json
import random
from pathlib import Path
import sys

import pytest
from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "12a886996b14"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
PARAMETRIC = HOME / "workspace" / "parametric"
ADAPTER_PATH = PARAMETRIC / "adapter.py"
PROTOTYPE_PATH = PARAMETRIC / "prototype.py"
AUDIT_PATH = PARAMETRIC / "audit.py"
DIRECT = {"finish": "translate_only"}
RELAY = {"finish": "cue_payload"}
CUE_COLORS = {1, 5, 6}
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _load(path: Path, stem: str):
    assert path.is_file(), f"missing {path}"
    name = f"_{TASK_ID}_{stem}_{path.stat().st_mtime_ns}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _adapter():
    return _load(ADAPTER_PATH, "adapter")


def _prototype():
    return _load(PROTOTYPE_PATH, "prototype")


def _audit():
    return _load(AUDIT_PATH, "audit")


def _canonical_program() -> str:
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise AssertionError("canonical authority row is missing")


def _cells(grid, color):
    return {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}


def _bbox_anchor(cells):
    return min(r for r, _ in cells), min(c for _, c in cells)


def _neighbors(cells, h, w):
    return {
        (r + dr, c + dc)
        for r, c in cells
        for dr, dc in CARDINAL
        if 0 <= r + dr < h and 0 <= c + dc < w and (r + dr, c + dc) not in cells
    }


def _scene(grid):
    h, w = len(grid), len(grid[0])
    red = _cells(grid, 2)
    green = _cells(grid, 3)
    yellow = _cells(grid, 4)
    assert red and green and yellow
    rr, rc = _bbox_anchor(red)
    gr, gc = _bbox_anchor(green)
    delta = gr - rr, gc - rc
    assert delta != (0, 0)
    shifted = {(r + delta[0], c + delta[1]) for r, c in yellow}
    assert shifted and all(0 <= r < h and 0 <= c < w for r, c in shifted)

    def adjacent_colors(cells):
        return {
            grid[r][c]
            for r, c in _neighbors(cells, h, w)
            if grid[r][c] in CUE_COLORS
        }

    target = adjacent_colors(shifted)
    source = adjacent_colors(yellow)
    green_adjacent = adjacent_colors(green)
    assert len(target) == len(source) == len(green_adjacent) == 1
    target_color = next(iter(target))
    source_color = next(iter(source))
    green_color = next(iter(green_adjacent))
    assert len({target_color, source_color, green_color}) == 3
    return {
        "h": h,
        "w": w,
        "red": red,
        "green": green,
        "yellow": yellow,
        "shifted": shifted,
        "target_color": target_color,
        "source_color": source_color,
        "green_color": green_color,
    }


def _expected(grid, finish):
    scene = _scene(grid)
    out = [[0 for _ in row] for row in grid]
    for r, c in scene["shifted"]:
        out[r][c] = 4
    if finish == "cue_payload":
        for r, c in _cells(grid, scene["target_color"]):
            out[r][c] = 8
    return out


def test_adapter_contract_and_exact_canonical_default():
    adapter = _adapter()
    assert callable(adapter.program)
    assert callable(adapter.generate)
    assert adapter.program(DIRECT) == _canonical_program()
    assert adapter.program(RELAY) != adapter.program(DIRECT)


def test_inputs_are_matched_across_settings_and_counts_are_independent():
    adapter = _adapter()
    direct = adapter.generate(17, DIRECT, demos=3, queries=4)
    relay = adapter.generate(17, RELAY, demos=3, queries=4)
    assert len(direct["train"]) == len(relay["train"]) == 3
    assert len(direct["test"]) == len(relay["test"]) == 4
    direct_inputs = [p["input"] for p in direct["train"] + direct["test"]]
    relay_inputs = [p["input"] for p in relay["train"] + relay["test"]]
    assert direct_inputs == relay_inputs
    assert len({json.dumps(grid, separators=(",", ":")) for grid in direct_inputs}) == 7
    assert direct["program_solution"] == adapter.program(DIRECT)
    assert relay["program_solution"] == adapter.program(RELAY)


@pytest.mark.parametrize("seed", [0, 17, 97])
def test_each_scene_has_unique_destination_source_and_green_cues(seed):
    adapter = _adapter()
    direct = adapter.generate(seed, DIRECT, demos=3, queries=4)
    relay = adapter.generate(seed, RELAY, demos=3, queries=4)
    for direct_pair, relay_pair in zip(
        direct["train"] + direct["test"], relay["train"] + relay["test"], strict=True
    ):
        grid = direct_pair["input"]
        scene = _scene(grid)
        assert direct_pair["output"] == _expected(grid, "translate_only")
        assert relay_pair["output"] == _expected(grid, "cue_payload")
        assert direct_pair["output"] != relay_pair["output"]
        assert len(_cells(grid, scene["target_color"])) >= 3
        assert len(_cells(grid, scene["source_color"])) >= 3
        assert len(_cells(grid, scene["green_color"])) >= 3


def test_supported_count_boundaries_and_substantive_30x30_query():
    adapter = _adapter()
    for demos, queries in ((2, 1), (2, 4), (6, 1), (6, 4)):
        episode = adapter.generate(23, RELAY, demos=demos, queries=queries)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == queries
        for pair in episode["train"] + episode["test"]:
            h, w = len(pair["input"]), len(pair["input"][0])
            assert 1 <= h <= 30 and 1 <= w <= 30
            assert all(type(cell) is int and 0 <= cell <= 9 for row in pair["input"] for cell in row)
    episode = adapter.generate(23, RELAY, demos=3, queries=4)
    largest = episode["test"][-1]["input"]
    assert (len(largest), len(largest[0])) == (30, 30)
    nonzero = sum(cell != 0 for row in largest for cell in row)
    assert nonzero >= 28
    scene = _scene(largest)
    assert any(r in (0, 29) or c in (0, 29) for r, c in scene["shifted"])


@pytest.mark.parametrize(
    "seed,settings,demos,queries",
    [
        (-1, DIRECT, 3, 4),
        (True, DIRECT, 3, 4),
        (1, {}, 3, 4),
        (1, {"finish": "unknown"}, 3, 4),
        (1, {"finish": "translate_only", "extra": 1}, 3, 4),
        (1, DIRECT, 1, 4),
        (1, DIRECT, 7, 4),
        (1, DIRECT, 3, 0),
        (1, DIRECT, 3, 5),
        (1, DIRECT, True, 4),
    ],
)
def test_invalid_requests_fail_closed(seed, settings, demos, queries):
    adapter = _adapter()
    with pytest.raises(ValueError):
        adapter.generate(seed, settings, demos=demos, queries=queries)


def test_generation_is_deterministic_and_does_not_touch_global_rng():
    adapter = _adapter()
    random.seed(20261024)
    state = random.getstate()
    first = adapter.generate(88, RELAY, demos=3, queries=4)
    after = random.getstate()
    second = adapter.generate(88, RELAY, demos=3, queries=4)
    assert state == after
    assert first == second
    assert first is not second


@pytest.mark.parametrize("seed", [0, 17, 97])
@pytest.mark.parametrize("demos", [2, 3, 6])
@pytest.mark.parametrize("settings", [DIRECT, RELAY])
def test_visible_demonstrations_identify_setting_and_refute_finite_rivals(seed, demos, settings):
    adapter = _adapter()
    prototype = _prototype()
    episode = adapter.generate(seed, settings, demos=demos, queries=4)
    check = prototype.teaching_check(episode, settings)
    assert check["declared_survivors"] == [settings["finish"]]
    assert check["harmful_survivors"] == []
    assert set(check["tested_rivals"]) >= {
        "translate_only",
        "cue_payload",
        "source_cue_payload",
        "green_cue_payload",
        "lowest_color_payload",
        "largest_payload",
        "local_cue_only",
        "payload_only",
    }


def test_wrong_order_is_a_real_causal_ablation():
    adapter = _adapter()
    prototype = _prototype()
    episode = adapter.generate(17, RELAY, demos=3, queries=4)
    for pair in episode["train"] + episode["test"]:
        correct = pair["output"]
        wrong = prototype.wrong_order_transform(pair["input"])
        scene = prototype.intermediate(pair["input"])
        assert scene["destination_cue_color"] != scene["source_cue_color"]
        assert correct != wrong


def test_public_turn_hides_private_data_and_future_queries():
    adapter = _adapter()
    prototype = _prototype()
    episode = adapter.generate(17, RELAY, demos=3, queries=4)
    episode["settings"] = RELAY
    episode["seed"] = 17
    visible = prototype.public_turn(episode, 0)
    payload = public_challenge_bytes(visible)
    parsed = json.loads(payload)
    assert len(parsed["test"]) == 1
    assert set(parsed["test"][0]) == {"input"}
    assert b"cue_payload" not in payload
    assert b"program_solution" not in payload
    assert public_challenge_id(visible) == public_challenge_id({
        "train": episode["train"],
        "test": [{"input": episode["test"][0]["input"]}],
    })


def test_sequential_witness_matches_owner_admission_schema():
    audit = _audit()
    source_binding = {
        "task_id": TASK_ID,
        "files": [{"path": "example.py", "sha256": "0" * 64}],
    }
    raw_case = {
        "settings": RELAY,
        "intermediate_value": {
            "translated_yellow": [[3, 4], [3, 5]],
            "destination_cue_color": 5,
        },
        "input": [[2, 3, 4]],
        "output": [[0, 4, 8]],
        "counterfactual_output": [[0, 4, 0]],
        "ablation": "wrong_order",
        "program": "(lambda (g) g)",
        "counterfactual_program": "(lambda (g) (reverse g))",
        "differing_cells": 1,
    }

    witness = audit.build_sequential_witness(source_binding, raw_case)

    assert witness["schema"] == "arcpuzzles-sequential-dependency-witness-v1"
    assert witness["task_id"] == TASK_ID
    assert witness["source_binding"] == source_binding
    assert witness["source_binding"] is not source_binding
    assert witness["racket"] == {"backend": "racket", "protected": True}
    assert witness["step_a"] == (
        "Infer the input-derived red-to-green displacement and translate the yellow object by that vector."
    )
    assert witness["intermediate"] == (
        "The translated yellow footprint and the unique cue color orthogonally adjacent to that destination footprint."
    )
    assert witness["step_b"] == (
        "Select the remote payload having that cue color, recolor the payload cyan, and retain the translated yellow object."
    )
    assert witness["why_b_depends_on_a"] == (
        "The scene also contains source-footprint and green-marker cue decoys; the correct cue and payload "
        "cannot be selected until Step A determines the translated destination footprint."
    )
    assert witness["cases"] == [raw_case]
    assert witness["cases"][0] is not raw_case
