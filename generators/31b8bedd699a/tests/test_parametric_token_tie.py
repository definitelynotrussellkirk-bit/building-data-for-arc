"""Focused contract tests for the task-local token-size/tie-policy prototype."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

import pytest


for _ancestor in Path(__file__).resolve().parents:
    _runtime = _ancestor / "shared" / "runtime"
    if (_ancestor / "reviewer_support.py").is_file():
        sys.path.insert(0, str(_ancestor))
        break
    if (_runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(_runtime))
        break
else:
    raise ImportError("The test's tree does not contain reviewer_support.py")

from reviewer_support import find_root, load_selected_generator


TASK_ID = "31b8bedd699a"
ROOT = find_root(__file__)
PROTOTYPE = (
    ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
)


def _load_prototype():
    assert PROTOTYPE.is_file(), f"missing proposed parametric prototype: {PROTOTYPE}"
    spec = importlib.util.spec_from_file_location(
        "parametric_token_tie_31b8bedd699a", PROTOTYPE
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _tie_grid():
    """Two 3x3 outlines whose top-left row/column ranges are both four."""
    return [
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 2, 2, 2, 0, 0, 0, 0, 0],
        [0, 2, 0, 2, 0, 0, 0, 0, 0],
        [0, 2, 2, 2, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 3, 3, 3, 0],
        [0, 0, 0, 0, 0, 3, 0, 3, 0],
        [0, 0, 0, 0, 0, 3, 3, 3, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]


def test_declares_two_bounded_episode_parameters_and_exact_canonical_default():
    proto = _load_prototype()
    assert proto.TOKEN_SIZES == (3, 4, 5)
    assert proto.TIE_POLICIES == ("horizontal", "vertical")
    assert proto.DEFAULT_TOKEN_SIZE == 4
    assert proto.DEFAULT_TIE_POLICY == "horizontal"
    assert proto.PARAMETERS == {
        "token_size": {
            "allowed": (3, 4, 5),
            "default": 4,
            "selected_once_per_episode": True,
        },
        "tie_policy": {
            "allowed": ("horizontal", "vertical"),
            "default": "horizontal",
            "selected_once_per_episode": True,
        },
    }
    canonical = proto.canonical_record(root=ROOT)["program_solution"]
    assert proto.racket_program(4, "horizontal", root=ROOT) == canonical
    assert proto.racket_program(3, "horizontal", root=ROOT) != canonical
    assert proto.racket_program(4, "vertical", root=ROOT) != canonical


def test_python_mirror_has_hand_derived_size_and_tie_outputs():
    proto = _load_prototype()
    grid = _tie_grid()
    assert proto.apply_python(grid, 3, "horizontal") == [
        [2, 2, 2, 3, 3, 3],
        [2, 0, 2, 3, 0, 3],
        [2, 2, 2, 3, 3, 3],
    ]
    assert proto.apply_python(grid, 3, "vertical") == [
        [2, 2, 2],
        [2, 0, 2],
        [2, 2, 2],
        [3, 3, 3],
        [3, 0, 3],
        [3, 3, 3],
    ]


@pytest.mark.parametrize("invalid", [None, True, False, 2, 6, 4.0, "4"])
def test_token_size_rejects_non_exact_or_out_of_range_values(invalid):
    proto = _load_prototype()
    with pytest.raises(ValueError):
        proto.racket_program(invalid, "horizontal", root=ROOT)


@pytest.mark.parametrize("invalid", [None, True, 0, "both", "Horizontal"])
def test_tie_policy_rejects_unknown_or_non_string_values(invalid):
    proto = _load_prototype()
    with pytest.raises(ValueError):
        proto.racket_program(4, invalid, root=ROOT)


@pytest.mark.parametrize("field", ["demo_count", "query_count"])
@pytest.mark.parametrize("invalid", [True, 0, 65, 1.5, "4"])
def test_episode_counts_are_independent_strict_bounds(field, invalid):
    proto = _load_prototype()
    kwargs = {"demo_count": 3, "query_count": 4, field: invalid}
    with pytest.raises(ValueError):
        proto.generate_episode(17, token_size=4, tie_policy="horizontal", root=ROOT, **kwargs)


def test_all_settings_build_identifiable_three_demo_four_query_episodes():
    proto = _load_prototype()
    generator, _, _ = load_selected_generator(TASK_ID, root=ROOT)
    settings = [
        (token_size, tie_policy)
        for token_size in proto.TOKEN_SIZES
        for tie_policy in proto.TIE_POLICIES
    ]
    input_fingerprints = None
    for token_size, tie_policy in settings:
        episode = proto.generate_episode(
            20261023,
            token_size=token_size,
            tie_policy=tie_policy,
            demo_count=3,
            query_count=4,
            root=ROOT,
        )
        assert episode["parameter_draw_count"] == 1
        assert episode["parameter"] == {
            "token_size": token_size,
            "tie_policy": tie_policy,
        }
        assert episode["program"] == proto.racket_program(
            token_size, tie_policy, root=ROOT
        )
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 4
        assert [pair["profile"] for pair in episode["train"]] == [
            "tie",
            "vertical",
            "horizontal",
        ]
        assert [pair["profile"] for pair in episode["test"]] == [
            "vertical",
            "horizontal",
            "tie",
            "vertical",
        ]
        assert proto.episode_errors(episode, root=ROOT) == []

        pairs = [*episode["train"], *episode["test"]]
        fingerprints = [
            json.dumps(pair["input"], separators=(",", ":")) for pair in pairs
        ]
        assert len(set(fingerprints)) == 7
        if input_fingerprints is None:
            input_fingerprints = fingerprints
        else:
            assert fingerprints == input_fingerprints
        assert all(generator.self_check(pair["input"]) == [] for pair in pairs)
        assert all(
            pair["output"]
            == proto.apply_python(pair["input"], token_size, tie_policy)
            for pair in pairs
        )
        assert any(
            proto.known_distribution_shortcut(pair["input"], token_size)
            != pair["output"]
            for pair in episode["test"]
        )

        public = proto.public_challenge(episode)
        assert set(public) == {"train", "test"}
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert all(set(pair) == {"input"} for pair in public["test"])
        assert "program" not in json.dumps(public)
        assert "tie_policy" not in json.dumps(public)

        if (token_size, tie_policy) == (4, "horizontal"):
            assert all(
                pair["output"] == generator.rule_mirror(pair["input"])
                for pair in pairs
            )


def test_seed_selection_replay_and_public_identifier_boundary():
    proto = _load_prototype()
    first = proto.generate_episode(29, demo_count=2, query_count=4, root=ROOT)
    second = proto.generate_episode(29, demo_count=2, query_count=4, root=ROOT)
    assert first == second
    assert first["parameter"] == proto.select_parameters(29)

    base_name = proto.public_filename(first)
    changed_private = deepcopy(first)
    changed_private["seed"] += 1
    changed_private["parameter"] = {"token_size": 5, "tie_policy": "vertical"}
    changed_private["program"] = "private"
    changed_private["test"][0]["output"] = [[9]]
    assert proto.public_filename(changed_private) == base_name

    changed_visible = deepcopy(first)
    changed_visible["train"][0]["output"][0][0] = (
        changed_visible["train"][0]["output"][0][0] + 1
    ) % 10
    assert proto.public_filename(changed_visible) != base_name
