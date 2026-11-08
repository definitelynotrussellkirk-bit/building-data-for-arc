from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_path, find_root

TASK_ID = "99601629ab88"
HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"
ADAPTER = PARAMETRIC / "adapter.py"
CANONICAL_SETTINGS = {"matrix_orientation": "mirror_left_right"}
ALTERNATIVE_SETTINGS = {"matrix_orientation": "largest_block_to_top_left"}


def load_adapter():
    assert ADAPTER.is_file(), "native adapter has not been implemented"
    name = "_test_99601629ab88_adapter"
    sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location(name, ADAPTER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def canonical_source() -> str:
    ledger = canonical_path(find_root(__file__))
    programs = {
        row["program_solution"]
        for line in ledger.read_text(encoding="utf-8").splitlines()
        if (row := json.loads(line)).get("task_id") == TASK_ID
    }
    assert len(programs) == 1
    return next(iter(programs))


def all_inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_adapter_contract_exists():
    assert ADAPTER.is_file(), "native adapter has not been implemented"
    assert (PARAMETRIC / "promotion.json").is_file()
    assert (PARAMETRIC / "canonical.rkt").is_file()


def test_canonical_program_is_exact_selected_source():
    adapter = load_adapter()
    assert adapter.program(CANONICAL_SETTINGS) == canonical_source()
    assert (PARAMETRIC / "canonical.rkt").read_text(encoding="utf-8") == canonical_source()
    assert adapter.program(ALTERNATIVE_SETTINGS).startswith("(rule! (lambda (g)")
    assert adapter.program(ALTERNATIVE_SETTINGS) != canonical_source()


@pytest.mark.parametrize("seed", [0, 17, 41])
def test_counts_prefix_stability_and_matched_inputs(seed):
    adapter = load_adapter()
    short = adapter.generate(seed, CANONICAL_SETTINGS, 2, 1)
    long = adapter.generate(seed, CANONICAL_SETTINGS, 6, 4)
    alternate = adapter.generate(seed, ALTERNATIVE_SETTINGS, 6, 4)

    assert short["train"] == long["train"][:2]
    assert short["test"] == long["test"][:1]
    assert [p["input"] for p in long["train"]] == [p["input"] for p in alternate["train"]]
    assert [p["input"] for p in long["test"]] == [p["input"] for p in alternate["test"]]
    assert len({json.dumps(grid) for grid in all_inputs(long)}) == 10
    assert any(a["output"] != b["output"] for a, b in zip(long["train"], alternate["train"]))
    assert any(a["output"] != b["output"] for a, b in zip(long["test"], alternate["test"]))


@pytest.mark.parametrize("settings", [CANONICAL_SETTINGS, ALTERNATIVE_SETTINGS])
@pytest.mark.parametrize("seed", [0, 17])
def test_python_claims_and_minimum_lesson_certificate(settings, seed):
    adapter = load_adapter()
    episode = adapter.generate(seed, settings, 2, 4)
    for pair in episode["train"] + episode["test"]:
        assert pair["output"] == adapter.transform(pair["input"], settings["matrix_orientation"])
        analysis = adapter.analyze(pair["input"])
        assert analysis["largest_corner"] in {"top_left", "top_right", "bottom_left", "bottom_right"}
    certificate = adapter.lesson_certificate(
        episode["train"], [pair["input"] for pair in episode["test"]]
    )
    assert certificate["surviving_settings"] == [settings]
    assert certificate["ambiguous_rivals"] == []
    assert certificate["query_count"] == 4


def test_corner_schedule_and_30x30_stress_are_substantive():
    adapter = load_adapter()
    episode = adapter.generate(17, ALTERNATIVE_SETTINGS, 6, 4)
    demo_corners = [adapter.analyze(pair["input"])["largest_corner"] for pair in episode["train"]]
    query_corners = [adapter.analyze(pair["input"])["largest_corner"] for pair in episode["test"]]
    assert demo_corners[:2] == ["top_left", "bottom_right"]
    assert set(query_corners) == {"top_left", "top_right", "bottom_left", "bottom_right"}

    stress = episode["test"][3]["input"]
    analysis = adapter.analyze(stress)
    assert (len(stress), len(stress[0])) == (30, 30)
    assert (len(analysis["matrix"]), len(analysis["matrix"][0])) == (4, 4)
    assert len({cell for row in stress for cell in row}) >= 5
    assert sum(cell != 0 for row in stress for cell in row) >= 700
    assert analysis["largest_corner"] == "top_left"
    transforms = {
        adapter.apply_corner(analysis["matrix"], corner)
        for corner in ("top_left", "top_right", "bottom_left", "bottom_right")
    }
    assert len(transforms) == 4


def test_public_turn_hides_private_fields_and_first_turn_is_count_invariant():
    adapter = load_adapter()
    one = adapter.generate(5, ALTERNATIVE_SETTINGS, 3, 1)
    four = adapter.generate(5, ALTERNATIVE_SETTINGS, 3, 4)
    first_one = adapter.public_turn(one, 0)
    first_four = adapter.public_turn(four, 0)
    assert first_one == first_four
    assert set(first_one) == {"train", "test"}
    assert len(first_one["test"]) == 1
    assert "output" not in first_one["test"][0]
    encoded = json.dumps(first_one, sort_keys=True)
    for private_name in ("settings", "program_solution", "certificate", "seed", "sampling"):
        assert private_name not in encoded


@pytest.mark.parametrize(
    "args",
    [
        (True, CANONICAL_SETTINGS, 3, 4),
        (-1, CANONICAL_SETTINGS, 3, 4),
        (0, {"matrix_orientation": "unknown"}, 3, 4),
        (0, {"matrix_orientation": "mirror_left_right", "extra": 1}, 3, 4),
        (0, CANONICAL_SETTINGS, 1, 4),
        (0, CANONICAL_SETTINGS, 7, 4),
        (0, CANONICAL_SETTINGS, 3, 0),
        (0, CANONICAL_SETTINGS, 3, 5),
    ],
)
def test_invalid_requests_are_rejected(args):
    adapter = load_adapter()
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(*args)
