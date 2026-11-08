"""Public exports must be opaque and depend only on visible challenge bytes."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import re
import sys

from reviewer_support import find_root, public_challenge_bytes, public_challenge_id

TASK_HOME = Path(__file__).resolve().parents[1]
SOURCE = TASK_HOME / "workspace" / "parametric" / "prototype.py"
ROOT = find_root(__file__)


def _load_prototype():
    assert SOURCE.is_file(), f"missing implementation: {SOURCE}"
    spec = importlib.util.spec_from_file_location(
        "orientation_scope_public_names_d09fae8197f6", SOURCE
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_public_projection_masks_private_rule_and_query_answers():
    """Catches hidden settings, source slots, programs, or labels leaking publicly."""
    proto = _load_prototype()
    episode = proto.generate_episode(
        271828,
        orientation_scope="rotations",
        root=ROOT,
        demo_count=3,
        query_count=4,
    )
    public = proto.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert len(public["train"]) == 3
    assert len(public["test"]) == 4
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    encoded = json.dumps(public, sort_keys=True)
    for hidden in (
        "orientation_scope",
        "program",
        "seed",
        "sample_index",
        "difficulty",
        "candidate_attempt",
    ):
        assert hidden not in encoded
    assert proto.public_filename(episode) == f"challenge-{public_challenge_id(public)}.json"
    assert public_challenge_bytes(public).endswith(b"\n")


def test_public_identifier_ignores_private_metadata_and_query_answers_only():
    """Catches filenames that encode the hidden setting, seed, or query labels."""
    proto = _load_prototype()
    episode = proto.generate_episode(
        161803,
        orientation_scope="dihedral",
        root=ROOT,
        demo_count=3,
        query_count=4,
    )
    original = proto.public_filename(episode)
    assert re.fullmatch(r"challenge-[0-9a-f]{64}\.json", original)

    private_change = deepcopy(episode)
    private_change["parameter"] = {"orientation_scope": "rotations"}
    private_change["seed"] = 999
    private_change["program"] = "private replacement"
    private_change["test"][0]["output"] = [[9]]
    assert proto.public_filename(private_change) == original

    demo_output_change = deepcopy(episode)
    demo_output_change["train"][0]["output"][0][0] = (
        demo_output_change["train"][0]["output"][0][0] + 1
    ) % 10
    assert proto.public_filename(demo_output_change) != original

    query_input_change = deepcopy(episode)
    query_input_change["test"][0]["input"][0][0] = (
        query_input_change["test"][0]["input"][0][0] + 1
    ) % 10
    assert proto.public_filename(query_input_change) != original
