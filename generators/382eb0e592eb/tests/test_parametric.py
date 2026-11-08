"""Prototype-only tests; these do not alter the selected canonical rule."""
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

MODULE_PATH = Path(__file__).resolve().parents[1] / "workspace" / "parametric" / "direction.py"
SPEC = spec_from_file_location("direction_prototype_382eb0e592eb", MODULE_PATH)
assert SPEC and SPEC.loader
PROTO = module_from_spec(SPEC)
sys.modules[SPEC.name] = PROTO
SPEC.loader.exec_module(PROTO)


def test_default_materialization_is_the_selected_rule_and_variant_is_distinct():
    down = PROTO.materialize_rule("down")
    up = PROTO.materialize_rule("up")
    assert PROTO.ALLOWED_DIRECTIONS == ("down", "up")
    assert PROTO.DEFAULT_DIRECTION == "down"
    assert PROTO.normalized_hash(down) == "03fbcf596117"
    assert up != down
    assert PROTO.normalized_hash(up) != PROTO.normalized_hash(down)


def test_each_fixture_distinguishes_both_direction_settings():
    fixtures = PROTO.fixtures()
    assert len(fixtures) >= 4
    for fixture in fixtures:
        grid = fixture["input"]
        down = PROTO.python_mirror(grid, "down")
        up = PROTO.python_mirror(grid, "up")
        assert down != up
        assert down != grid
        assert up != grid


def test_episode_parameter_is_deterministic_and_public_view_hides_it():
    for seed in range(16):
        assert PROTO.choose_direction(seed) == PROTO.choose_direction(seed)
        assert PROTO.choose_direction(seed) in PROTO.ALLOWED_DIRECTIONS
    episode = {
        "task_id": PROTO.TASK_ID,
        "parameter": {"direction": "up"},
        "racket": {"source": "secret"},
        "demonstrations": [{"input": [[0]], "output": [[0]]}],
        "query": {"input": [[0]], "output": [[0]]},
        "rival_predictions": {"down": [[[0]]]},
    }
    public = PROTO.public_challenge(episode)
    assert public == {
        "schema": "382eb0e592eb-direction-public-challenge-v1",
        "task_id": PROTO.TASK_ID,
        "train": [{"input": [[0]], "output": [[0]]}],
        "test": [{"input": [[0]]}],
    }
