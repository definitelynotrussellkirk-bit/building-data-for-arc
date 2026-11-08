"""Focused contract tests for the task-local tie-order parametric family."""
from __future__ import annotations

from copy import deepcopy
from importlib.util import module_from_spec, spec_from_file_location
import itertools
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_path, find_root

TASK_ID = "a55c1997c5e3"
TASK_HOME = Path(__file__).resolve().parents[1]
PARAMETRIC_HOME = TASK_HOME / "workspace/parametric"
PROTOTYPE_PATH = PARAMETRIC_HOME / "prototype.py"
ADAPTER_PATH = PARAMETRIC_HOME / "adapter.py"
PROMOTION_PATH = PARAMETRIC_HOME / "promotion.json"


def _load(path: Path, name: str):
    assert path.is_file(), f"missing implementation artifact: {path}"
    spec = spec_from_file_location(name, path)
    assert spec and spec.loader
    module = module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _prototype():
    return _load(PROTOTYPE_PATH, f"_parametric_{TASK_ID}")


def _adapter():
    return _load(ADAPTER_PATH, f"_adapter_{TASK_ID}")


def _canonical_source() -> str:
    with canonical_path(find_root(__file__)).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row["program_solution"]
    raise AssertionError(f"missing canonical program for {TASK_ID}")


def _inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def _assert_exact_grid(grid):
    assert type(grid) is list and 1 <= len(grid) <= 30
    assert type(grid[0]) is list and 1 <= len(grid[0]) <= 30
    width = len(grid[0])
    assert all(type(row) is list and len(row) == width for row in grid)
    assert all(type(cell) is int and 0 <= cell <= 9 for row in grid for cell in row)


def test_default_program_is_exact_canonical_and_alternate_changes_only_direction_order():
    proto = _prototype()
    canonical = _canonical_source()
    default = {"tie_order": "right_down_left_up"}
    alternate = {"tie_order": "up_left_down_right"}

    assert proto.ALLOWED_TIE_ORDERS == (
        "right_down_left_up",
        "up_left_down_right",
    )
    assert proto.DEFAULT_SETTINGS == default
    assert proto.rule_source(default) == canonical
    assert proto.rule_source(alternate) != canonical
    assert proto.restore_canonical_direction_block(proto.rule_source(alternate)) == canonical


def test_promotion_contract_and_adapter_expose_the_native_bounded_interface():
    proto = _prototype()
    adapter = _adapter()
    contract = json.loads(PROMOTION_PATH.read_text(encoding="utf-8"))
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"tie_order": list(proto.ALLOWED_TIE_ORDERS)},
        "default": proto.DEFAULT_SETTINGS,
        "limits": {"demos": [2, 6], "queries": [4, 4]},
    }
    settings = {"tie_order": "up_left_down_right"}
    assert adapter.program(settings) == proto.rule_source(settings)
    assert adapter.generate(17, settings, 3, 4) == proto.generate_episode(17, settings, 3, 4)


@pytest.mark.parametrize(
    "settings",
    [
        None,
        {},
        {"tie_order": "right_down_left_up", "extra": 1},
        {"tie_order": "left_right_down_up"},
        {"tie_order": True},
        {"tie_order": 0},
    ],
)
def test_settings_fail_closed(settings):
    proto = _prototype()
    with pytest.raises(ValueError, match="tie_order|settings"):
        proto.rule_source(settings)


@pytest.mark.parametrize(
    ("seed", "demos", "queries", "message"),
    [
        (True, 3, 4, "seed"),
        (-1, 3, 4, "seed"),
        (0, 1, 4, "demos"),
        (0, 7, 4, "demos"),
        (0, True, 4, "demos"),
        (0, 3, 3, "queries"),
        (0, 3, 5, "queries"),
        (0, 3, True, "queries"),
    ],
)
def test_episode_request_boundaries_fail_closed(seed, demos, queries, message):
    proto = _prototype()
    with pytest.raises(ValueError, match=message):
        proto.generate_episode(seed, proto.DEFAULT_SETTINGS, demos, queries)


@pytest.mark.parametrize("demos", [2, 3, 6])
@pytest.mark.parametrize("seed", [0, 17, 2**63 - 1])
def test_inputs_are_lawful_distinct_and_independent_of_private_setting(seed, demos):
    proto = _prototype()
    canonical = proto.generate_episode(
        seed, {"tie_order": "right_down_left_up"}, demos, 4
    )
    alternate = proto.generate_episode(
        seed, {"tie_order": "up_left_down_right"}, demos, 4
    )

    assert _inputs(canonical) == _inputs(alternate)
    serialized = [json.dumps(grid, separators=(",", ":")) for grid in _inputs(canonical)]
    assert len(serialized) == len(set(serialized)) == demos + 4

    task = proto.task_generator()
    for grid in _inputs(canonical):
        _assert_exact_grid(grid)
        assert task.strict_canonical_like(grid) == []

    large = canonical["test"][-1]["input"]
    assert (len(large), len(large[0])) == (30, 30)
    occupied = [(r, c) for r, row in enumerate(large) for c, value in enumerate(row) if value]
    assert min(r for r, _ in occupied) == 0
    assert max(r for r, _ in occupied) == 29
    assert min(c for _, c in occupied) == 0
    assert max(c for _, c in occupied) == 29


@pytest.mark.parametrize("seed", [0, 17, 20261024])
@pytest.mark.parametrize("tie_order", ["right_down_left_up", "up_left_down_right"])
def test_two_visible_demos_identify_setting_against_every_constant_direction_order(seed, tie_order):
    proto = _prototype()
    settings = {"tie_order": tie_order}
    episode = proto.generate_episode(seed, settings, 2, 4)
    assert proto.setting_survivors(episode) == [settings]

    chosen = proto.ORDER_DIRECTIONS[tie_order]
    for order in itertools.permutations((0, 1, 2, 3)):
        outputs = [proto.python_mirror_for_order(pair["input"], order) for pair in episode["train"]]
        matches = all(output == pair["output"] for output, pair in zip(outputs, episode["train"]))
        assert matches is (order == chosen), f"surviving direction order: {order}"

    assert any(
        left["output"] != right["output"]
        for left, right in zip(
            episode["test"],
            proto.generate_episode(
                seed,
                {"tie_order": "up_left_down_right" if tie_order == "right_down_left_up" else "right_down_left_up"},
                2,
                4,
            )["test"],
        )
    )


def test_public_projection_masks_settings_programs_and_all_query_answers():
    proto = _prototype()
    episode = proto.generate_episode(17, {"tie_order": "up_left_down_right"}, 3, 4)
    public = proto.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert len(public["train"]) == 3
    assert len(public["test"]) == 4
    assert all(set(pair) == {"input"} for pair in public["test"])

    visible_bytes = proto.public_bytes(episode)
    visible_id = proto.public_id(episode)
    changed_private = deepcopy(episode)
    changed_private["settings"] = {"tie_order": "redacted-change"}
    changed_private["program_solution"] = "private program changed"
    changed_private["test"][0]["output"] = [[9]]
    assert proto.public_bytes(changed_private) == visible_bytes
    assert proto.public_id(changed_private) == visible_id
    text = visible_bytes.decode("utf-8")
    assert "tie_order" not in text
    assert "program_solution" not in text


def test_python_labels_are_exact_and_nontrivial_for_each_setting():
    proto = _prototype()
    for settings in (
        {"tie_order": "right_down_left_up"},
        {"tie_order": "up_left_down_right"},
    ):
        episode = proto.generate_episode(29, settings, 3, 4)
        for split in ("train", "test"):
            for pair in episode[split]:
                assert pair["output"] == proto.python_mirror(pair["input"], settings)
                assert pair["output"] != pair["input"]
