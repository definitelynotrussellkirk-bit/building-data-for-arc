"""Focused contract tests for the native largest-hole color-relay family."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import re

import pytest


HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"
ADAPTER_PATH = PARAMETRIC / "adapter.py"
CANONICAL = {"output_scope": "all_holes"}
RELAY = {"output_scope": "largest_hole_color_relay"}


def adapter():
    assert ADAPTER_PATH.is_file(), "native parametric adapter is missing"
    spec = importlib.util.spec_from_file_location(
        "test_629ec8fd452e_parametric_adapter", ADAPTER_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_default_program_is_exact_canonical_and_alternative_is_distinct():
    module = adapter()
    canonical = (PARAMETRIC / "canonical.rkt").read_text(encoding="utf-8")
    assert module.program(CANONICAL) == canonical
    assert module.program(RELAY) == (PARAMETRIC / "largest_hole_color_relay.rkt").read_text(
        encoding="utf-8"
    )
    assert module.program(RELAY) != canonical
    assert hashlib.sha256(canonical.encode()).hexdigest() == module.CANONICAL_SHA256


@pytest.mark.parametrize(
    "settings",
    [
        {},
        {"output_scope": True},
        {"output_scope": "largest_component_color"},
        {"output_scope": "all_holes", "extra": 1},
    ],
)
def test_undeclared_settings_fail_closed(settings):
    with pytest.raises(ValueError):
        adapter().program(settings)


@pytest.mark.parametrize(
    "seed,demos,queries",
    [
        (True, 3, 4),
        (-1, 3, 4),
        (0, 1, 4),
        (0, 7, 4),
        (0, True, 4),
        (0, 3, 0),
        (0, 3, 5),
        (0, 3, True),
    ],
)
def test_invalid_requests_fail_before_generation(seed, demos, queries):
    with pytest.raises(ValueError):
        adapter().generate(seed, CANONICAL, demos, queries)


@pytest.mark.parametrize("demos", [2, 3, 6])
@pytest.mark.parametrize("settings", [CANONICAL, RELAY])
def test_counts_distinctness_matched_inputs_and_prefix_queries(settings, demos):
    module = adapter()
    episode = module.generate(17, settings, demos, 4)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == 4
    assert episode["program_solution"] == module.program(settings)
    inputs = _inputs(episode)
    assert len({json.dumps(grid, separators=(",", ":")) for grid in inputs}) == demos + 4
    assert all(pair["output"] == module.transform(pair["input"], settings)
               for pair in episode["train"] + episode["test"])

    other_settings = RELAY if settings == CANONICAL else CANONICAL
    other = module.generate(17, other_settings, demos, 4)
    assert _inputs(other) == inputs

    one = module.generate(17, settings, demos, 1)
    assert one["train"] == episode["train"]
    assert one["test"][0] == episode["test"][0]
    assert module.teaching_check(episode)["ok"] is True


def test_relay_uses_largest_total_enclosed_area_not_largest_foreground_component():
    module = adapter()
    episode = module.generate(0, RELAY, 2, 4)
    first = episode["train"][0]
    analysis = module.explain(first["input"])
    assert analysis["largest_hole_color"] != analysis["largest_component_color"]
    assert analysis["largest_hole_color"] != analysis["first_hole_color"]
    relay_output = module.transform(first["input"], RELAY)
    skip_a_output = module.transform_skip_hole_analysis(first["input"])
    assert relay_output != skip_a_output
    assert any(
        component["color"] == analysis["largest_hole_color"] and not component["has_hole"]
        for component in analysis["components"]
    )


def test_fourth_query_is_substantive_30x30_boundary_stress():
    module = adapter()
    episode = module.generate(23, RELAY, 3, 4)
    grid = episode["test"][3]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    foreground = sum(value != 0 for row in grid for value in row)
    assert foreground >= 120
    assert any(grid[0][col] for col in range(30))
    assert any(grid[29][col] for col in range(30))
    analysis = module.explain(grid)
    assert len(analysis["hole_components"]) >= 3
    assert len({component["color"] for component in analysis["components"]}) >= 5


def test_public_projection_and_identifier_ignore_private_state_and_query_answers():
    module = adapter()
    episode = module.generate(5, RELAY, 3, 4)
    public = module.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    encoded = json.dumps(public, sort_keys=True)
    for forbidden in ("output_scope", "program_solution", "seed", "settings"):
        assert forbidden not in encoded

    name = module.public_filename(episode)
    assert re.fullmatch(r"[0-9a-f]{64}\.json", name)
    hidden = deepcopy(episode)
    hidden["settings"] = CANONICAL
    hidden["seed"] = 999
    hidden["program_solution"] = "private replacement"
    for pair in hidden["test"]:
        pair["output"] = [[9]]
    assert module.public_filename(hidden) == name

    visible = deepcopy(episode)
    visible["train"][0]["output"][0][0] = 9
    assert module.public_filename(visible) != name


def test_teaching_check_rejects_non_distinguishing_demonstrations():
    module = adapter()
    episode = module.generate(11, CANONICAL, 2, 4)
    ambiguous = deepcopy(episode)
    for pair in ambiguous["train"]:
        pair["output"] = module.transform(pair["input"], RELAY)
    ambiguous["program_solution"] = module.program(CANONICAL)
    assert module.teaching_check(ambiguous)["ok"] is False
