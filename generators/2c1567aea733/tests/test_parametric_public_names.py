"""Public names must bind exact visible bytes and ignore private fields."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import re
import sys

import pytest

SOURCE = Path(__file__).resolve().parents[1] / "workspace" / "parametric" / "prototype.py"


@pytest.fixture(scope="module")
def prototype():
    spec = importlib.util.spec_from_file_location("anchor_color_public_names", SOURCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_public_identifier_uses_exact_visible_bytes_only(prototype):
    episode = {
        "meta": {"anchor_color": 1, "episode_seed": 0},
        "train": [{"input": [[1, 0, 2]], "output": [[1, 2, 0]]}],
        "test": [{"input": [[4, 0, 1]], "output": [[4, 1, 0]]}],
    }
    name = prototype.public_filename(episode)
    assert re.fullmatch(r"challenge-[0-9a-f]{64}\.json", name)

    private_only = deepcopy(episode)
    private_only["meta"] = {"anchor_color": 4, "episode_seed": 999}
    private_only["test"][0]["output"] = [[0, 4, 1]]
    assert prototype.public_filename(private_only) == name

    visible_demo_label = deepcopy(episode)
    visible_demo_label["train"][0]["output"] = [[0, 1, 2]]
    assert prototype.public_filename(visible_demo_label) != name

    visible_query_input = deepcopy(episode)
    visible_query_input["test"][0]["input"] = [[1, 0, 4]]
    assert prototype.public_filename(visible_query_input) != name


def test_public_projection_never_leaks_parameter_program_seed_or_query_answer(prototype):
    episode = prototype.build_episode(11, anchor_color=4, demo_count=3, query_count=4)
    public = prototype.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    serialized = json.dumps(public, sort_keys=True)
    for forbidden in ("anchor_color", "episode_seed", "rule!", "program"):
        assert forbidden not in serialized
