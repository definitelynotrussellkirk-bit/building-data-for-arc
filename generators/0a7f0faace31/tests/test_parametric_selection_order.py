"""Contract tests for the isolated first/last selection-order prototype."""
import importlib.util
from pathlib import Path

import pytest

from reviewer_support import find_root


TASK_ID = "0a7f0faace31"
ROOT = find_root(__file__)
PROTOTYPE = (
    ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
)
if not PROTOTYPE.is_file():
    PROTOTYPE = (
        ROOT
        / "puzzle_generators"
        / "per_puzzle"
        / TASK_ID
        / "workspace"
        / "parametric"
        / "prototype.py"
    )
SPEC = importlib.util.spec_from_file_location("selection_order_prototype", PROTOTYPE)
prototype = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(prototype)


def test_default_setting_is_exact_canonical_program():
    assert prototype.DEFAULT_SELECTION_ORDER == "first"
    assert prototype.instantiate_rule("first", root=ROOT) == prototype.canonical_rule(root=ROOT)


def test_last_setting_changes_only_selection_direction():
    first = prototype.instantiate_rule("first", root=ROOT)
    last = prototype.instantiate_rule("last", root=ROOT)
    assert last != first
    assert "(reverse glyphs)" in last
    assert last.replace("(reverse glyphs)", "glyphs") == first


@pytest.mark.parametrize("bad", [True, False, 1.0, "1"])
def test_episode_seed_is_exact_integer(bad):
    with pytest.raises((TypeError, ValueError)):
        prototype.choose_selection_order(bad)


@pytest.mark.parametrize("order", prototype.SELECTION_ORDERS)
def test_every_prototype_episode_teaches_the_other_order(order):
    episode = prototype.build_episode(17, selection_order=order, root=ROOT)
    rival = next(value for value in prototype.SELECTION_ORDERS if value != order)
    assert len(episode["pairs"]) == 4
    for pair in episode["pairs"]:
        assert pair["output"] == prototype.apply_python(pair["input"], order)
        assert prototype.apply_python(pair["input"], rival) != pair["output"]
    for query_index in range(4):
        demo_indices = [index for index in range(4) if index != query_index]
        assert any(
            prototype.apply_python(episode["pairs"][index]["input"], rival)
            != episode["pairs"][index]["output"]
            for index in demo_indices
        )
