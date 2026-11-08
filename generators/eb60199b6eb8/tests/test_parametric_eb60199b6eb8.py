from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"
CANONICAL_SHA256 = "7d5c5a67ac1a9f8170fdb3247fadbef891cc3402414982933e55e442b90ac8b7"
SETTINGS = (
    {"closure": "horizontal_only"},
    {"closure": "horizontal_then_vertical"},
)


def _load(name: str, filename: str):
    path = PARAMETRIC / filename
    assert path.is_file(), f"missing native parametric source: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _adapter():
    return _load("_test_eb60199b6eb8_adapter", "adapter.py")


def _prototype():
    return _load("_test_eb60199b6eb8_prototype", "prototype.py")


def _fingerprint(grid):
    return json.dumps(grid, separators=(",", ":"))


def _column_classes(grid):
    exact_same = 0
    exact_different = 0
    three_or_more_same = 0
    for c in range(len(grid[0])):
        values = [row[c] for row in grid if row[c] != 0]
        if len(values) == 2:
            if values[0] == values[1]:
                exact_same += 1
            else:
                exact_different += 1
        elif len(values) >= 3 and len(set(values)) == 1:
            three_or_more_same += 1
    return exact_same, exact_different, three_or_more_same


def test_contract_preserves_exact_canonical_default_and_declares_four_queries():
    adapter = _adapter()
    promotion = json.loads((PARAMETRIC / "promotion.json").read_text())
    canonical = adapter.program(SETTINGS[0])

    from arcpuzzles import Catalog

    selected = {
        row["program_solution"]
        for row in Catalog(HOME.parents[1])._variants()["eb60199b6eb8"]
    }
    assert selected == {canonical}
    assert hashlib.sha256(canonical.encode()).hexdigest() == CANONICAL_SHA256
    assert promotion == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/eb60199b6eb8/workspace/parametric/adapter.py",
        "parameters": {"closure": ["horizontal_only", "horizontal_then_vertical"]},
        "default": {"closure": "horizontal_only"},
        "limits": {"demos": [2, 6], "queries": [4, 4]},
        "qualification_demos": 3,
        "resources": [
            "generators/eb60199b6eb8/workspace/parametric/prototype.py",
            "generators/eb60199b6eb8/workspace/parametric/canonical.rkt",
        ],
    }
    assert adapter.program(SETTINGS[1]) != canonical


@pytest.mark.parametrize("demos", [2, 3, 6])
@pytest.mark.parametrize("settings", SETTINGS)
def test_generate_supports_demo_range_four_distinct_queries_and_racket_claim_shape(demos, settings):
    adapter = _adapter()
    prototype = _prototype()
    episode = adapter.generate(41, settings, demos, 4)

    assert len(episode["train"]) == demos
    assert len(episode["test"]) == 4
    assert episode["program_solution"] == adapter.program(settings)
    pairs = episode["train"] + episode["test"]
    assert len({_fingerprint(pair["input"]) for pair in pairs}) == len(pairs)

    for pair in pairs:
        grid = pair["input"]
        assert 1 <= len(grid) <= 30
        assert 1 <= len(grid[0]) <= 30
        expected = prototype.complete_horizontal(grid)
        if settings["closure"] == "horizontal_then_vertical":
            expected = prototype.complete_vertical(expected)
        assert pair["output"] == expected


@pytest.mark.parametrize("seed", [0, 17, 991])
def test_matched_inputs_teach_setting_in_every_demo(seed):
    adapter = _adapter()
    canonical = adapter.generate(seed, SETTINGS[0], 3, 4)
    composed = adapter.generate(seed, SETTINGS[1], 3, 4)

    assert [p["input"] for p in canonical["train"]] == [p["input"] for p in composed["train"]]
    assert [p["input"] for p in canonical["test"]] == [p["input"] for p in composed["test"]]
    assert all(a["output"] != b["output"] for a, b in zip(canonical["train"], composed["train"]))


@pytest.mark.parametrize("seed", [0, 17, 123456789])
def test_queries_are_independent_of_demo_count_and_first_turn_is_stable(seed):
    adapter = _adapter()
    short = adapter.generate(seed, SETTINGS[1], 2, 4)
    long = adapter.generate(seed, SETTINGS[1], 6, 4)

    assert short["test"] == long["test"]
    assert short["test"][0] == long["test"][0]


def test_each_lesson_contains_positive_color_mismatch_and_exact_three_vertical_cases():
    adapter = _adapter()
    prototype = _prototype()
    episode = adapter.generate(73, SETTINGS[1], 3, 4)

    for pair in episode["train"]:
        intermediate = prototype.complete_horizontal(pair["input"])
        exact_same, exact_different, three_or_more_same = _column_classes(intermediate)
        assert exact_same > 0
        assert exact_different > 0
        assert three_or_more_same > 0


def test_fourth_query_is_substantive_30x30_stress_not_padding():
    adapter = _adapter()
    canonical = adapter.generate(19, SETTINGS[0], 3, 4)["test"][3]
    composed = adapter.generate(19, SETTINGS[1], 3, 4)["test"][3]

    assert (len(composed["input"]), len(composed["input"][0])) == (30, 30)
    canonical_nonzero = sum(v != 0 for row in canonical["output"] for v in row)
    composed_nonzero = sum(v != 0 for row in composed["output"] for v in row)
    changed = sum(
        a != b
        for row_a, row_b in zip(canonical["output"], composed["output"])
        for a, b in zip(row_a, row_b)
    )
    assert canonical_nonzero >= 25
    assert composed_nonzero >= canonical_nonzero + 40
    assert changed >= 40
    assert any(composed["output"][0]) or any(composed["output"][-1])


def test_skip_a_counterfactual_changes_the_composed_result():
    adapter = _adapter()
    prototype = _prototype()
    grid = adapter.generate(29, SETTINGS[1], 3, 4)["test"][2]["input"]
    intermediate = prototype.complete_horizontal(grid)
    actual = prototype.complete_vertical(intermediate)
    skip_a = prototype.complete_vertical(grid)

    assert intermediate != grid
    assert actual != skip_a
    assert adapter.program(SETTINGS[1]) != prototype.skip_a_program()


def test_public_projection_omits_setting_program_and_future_query_answers():
    adapter = _adapter()
    episode = adapter.generate(5, SETTINGS[1], 3, 4)

    from reviewer_support import public_challenge_bytes, public_challenge_id

    public = json.loads(public_challenge_bytes(episode))
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert "program_solution" not in public
    original_id = public_challenge_id(episode)
    mutated = {**episode, "test": [{**pair, "output": [[9]]} for pair in episode["test"]]}
    assert public_challenge_id(mutated) == original_id


@pytest.mark.parametrize(
    "call",
    [
        lambda adapter: adapter.program({}),
        lambda adapter: adapter.program({"closure": "unknown"}),
        lambda adapter: adapter.program({"closure": True}),
        lambda adapter: adapter.generate(True, SETTINGS[0], 3, 4),
        lambda adapter: adapter.generate(-1, SETTINGS[0], 3, 4),
        lambda adapter: adapter.generate(0, SETTINGS[0], 1, 4),
        lambda adapter: adapter.generate(0, SETTINGS[0], 7, 4),
        lambda adapter: adapter.generate(0, SETTINGS[0], 3, 3),
        lambda adapter: adapter.generate(0, SETTINGS[0], 3, 5),
    ],
)
def test_invalid_settings_and_counts_are_rejected(call):
    adapter = _adapter()
    with pytest.raises(ValueError):
        call(adapter)
