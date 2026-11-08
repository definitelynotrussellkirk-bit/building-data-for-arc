from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys

import pytest

from reviewer_support import (
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)

REPO = find_root(__file__)
GEN, GENERATOR_PATH, GENERATOR_SHA256 = load_selected_generator("0ed4fa8c0b40", root=REPO)

PROTOTYPE_PATH = (
    REPO / "generators" / "0ed4fa8c0b40" / "workspace" / "parametric" / "prototype.py"
)
PROTOTYPE_SPEC = importlib.util.spec_from_file_location(
    "generator_0ed4fa8c0b40_parametric_prototype", PROTOTYPE_PATH
)
assert PROTOTYPE_SPEC and PROTOTYPE_SPEC.loader
PROTOTYPE = importlib.util.module_from_spec(PROTOTYPE_SPEC)
sys.modules[PROTOTYPE_SPEC.name] = PROTOTYPE
PROTOTYPE_SPEC.loader.exec_module(PROTOTYPE)


def test_declares_two_bounded_parameters_and_preserves_canonical_default():
    assert PROTOTYPE.ALLOWED_COPY_STYLES == ("mirror", "translate")
    assert PROTOTYPE.ALLOWED_GAPS == (0, 1)
    assert PROTOTYPE.DEFAULT_PARAMETERS == {"copy_style": "mirror", "gap": 0}
    assert set(PROTOTYPE.SETTINGS) == {
        ("mirror", 0),
        ("mirror", 1),
        ("translate", 0),
        ("translate", 1),
    }

    for grid in PROTOTYPE.episode_inputs(760):
        assert PROTOTYPE.python_transform(grid, "mirror", 0) == GEN.rule_mirror(grid)


def test_parameter_choice_is_once_per_episode_and_replayable():
    first = PROTOTYPE.parameters_for_seed(760)
    second = PROTOTYPE.parameters_for_seed(760)
    assert first == second
    assert tuple(first.values()) in PROTOTYPE.SETTINGS

    episode = PROTOTYPE.build_episode(seed=760)
    assert episode["parameter"] == first
    assert all("parameter" not in pair for pair in [*episode["train"], *episode["test"]])


@pytest.mark.parametrize(
    "copy_style,gap",
    (("mirror", -1), ("mirror", 2), ("rotate", 0), (True, 0), ("mirror", True)),
)
def test_invalid_parameter_values_fail_loudly(copy_style, gap):
    with pytest.raises((TypeError, ValueError)):
        PROTOTYPE.validate_parameters(copy_style, gap)


def test_every_setting_executes_exact_racket_and_demos_refute_all_parameter_rivals(tmp_path):
    report = PROTOTYPE.build_evidence(seed=760, output_root=tmp_path)
    assert report["status"] == "prototype"
    assert set(report["settings"]) == {
        "mirror-gap0",
        "mirror-gap1",
        "translate-gap0",
        "translate-gap1",
    }
    for setting in report["settings"].values():
        assert setting["all_pairs_match_exact_racket"] is True
        assert setting["all_pairs_match_python_assertion"] is True
        assert setting["demos_refute_all_other_parameter_settings"] is True
        assert len(setting["rival_demo_witnesses"]) == 3
        retained = tmp_path / setting["racket_relative_path"]
        assert retained.read_text() == setting["racket_text"]


def test_public_challenge_omits_hidden_rule_and_query_answer():
    episode = PROTOTYPE.build_episode(seed=761, parameters={"copy_style": "translate", "gap": 1})
    public = PROTOTYPE.public_challenge(episode)
    rendered = json.dumps(public, sort_keys=True)
    assert "copy_style" not in rendered
    assert '"gap"' not in rendered
    assert "racket" not in rendered.lower()
    assert all("output" in pair for pair in public["train"])
    assert all("output" not in pair for pair in public["test"])



def test_demo_and_query_counts_are_independent_and_four_queries_are_distinct():
    episode = PROTOTYPE.build_episode(
        seed=760,
        parameters={"copy_style": "mirror", "gap": 0},
        demo_count=2,
        query_count=4,
    )
    assert len(episode["train"]) == 2
    assert len(episode["test"]) == 4
    visible_inputs = [
        json.dumps(pair["input"], separators=(",", ":"))
        for pair in [*episode["train"], *episode["test"]]
    ]
    assert len(visible_inputs) == len(set(visible_inputs)) == 6
    source = PROTOTYPE.racket_source("mirror", 0)
    for pair in [*episode["train"], *episode["test"]]:
        assert pair["output"] == PROTOTYPE.execute_rule(source, pair["input"])


@pytest.mark.parametrize(
    "name,value",
    (("demo_count", 0), ("demo_count", True), ("query_count", 0), ("query_count", 9)),
)
def test_invalid_episode_counts_fail_loudly(name, value):
    kwargs = {"seed": 760, "demo_count": 3, "query_count": 4}
    kwargs[name] = value
    with pytest.raises((TypeError, ValueError)):
        PROTOTYPE.build_episode(**kwargs)


def test_public_identifier_is_exact_visible_bytes_and_ignores_private_fields_and_query_answers():
    episode = PROTOTYPE.build_episode(
        seed=761,
        parameters={"copy_style": "translate", "gap": 1},
        demo_count=3,
        query_count=4,
    )
    expected_bytes = public_challenge_bytes(episode)
    expected_id = public_challenge_id(episode)
    assert PROTOTYPE.public_identifier(episode) == expected_id
    assert hashlib.sha256(expected_bytes).hexdigest() == expected_id

    changed = copy.deepcopy(episode)
    changed["seed"] = -999
    changed["parameter"] = {"copy_style": "mirror", "gap": 0}
    changed["racket_sha256"] = "private replacement"
    changed["test"][0]["output"] = [[9]]
    changed["private_note"] = {"setting_ordinal": 999}
    assert PROTOTYPE.public_identifier(changed) == expected_id
    assert public_challenge_bytes(changed) == expected_bytes

    changed["test"][0]["input"][0][0] = (changed["test"][0]["input"][0][0] + 1) % 10
    assert PROTOTYPE.public_identifier(changed) != expected_id


def test_racket_backed_public_batch_is_content_named_sorted_and_private_invariant(tmp_path):
    report = PROTOTYPE.build_evidence(
        seed=760,
        output_root=tmp_path / "rules",
        demo_count=3,
        query_count=4,
    )
    episodes = [setting["episode"] for setting in report["settings"].values()]
    forward = tmp_path / "forward"
    reverse = tmp_path / "reverse"
    forward_rows = PROTOTYPE.write_public_challenges(episodes, forward)
    reverse_rows = PROTOTYPE.write_public_challenges(list(reversed(episodes)), reverse)

    assert forward_rows == reverse_rows
    assert [row["public_id"] for row in forward_rows] == sorted(row["public_id"] for row in forward_rows)
    assert len(forward_rows) == 4
    for row in forward_rows:
        public_path = forward / row["filename"]
        assert public_path.stem == hashlib.sha256(public_path.read_bytes()).hexdigest()
        assert public_path.read_bytes() == public_challenge_bytes(
            next(episode for episode in episodes if public_challenge_id(episode) == row["public_id"])
        )
        public = json.loads(public_path.read_text())
        assert len(public["train"]) == 3
        assert len(public["test"]) == 4
        assert all(set(pair) == {"input"} for pair in public["test"])

    private_changed = copy.deepcopy(episodes[0])
    private_changed["parameter"] = {"copy_style": "mirror", "gap": 1}
    private_changed["seed"] = -1
    private_changed["test"][0]["output"] = [[9]]
    with pytest.raises(ValueError, match="duplicate public"):
        PROTOTYPE.write_public_challenges([episodes[0], private_changed], tmp_path / "duplicate")
    assert not (tmp_path / "duplicate").exists()

    for setting in report["settings"].values():
        assert len(setting["query_checks"]) == 4
        assert all(check["identified_from_demonstrations"] for check in setting["query_checks"])


def test_checked_in_current_examples_use_exact_content_ids():
    current = PROTOTYPE_PATH.parent / "examples" / "current"
    paths = sorted(current.glob("*.json"))
    assert len(paths) == 4
    for path in paths:
        raw = path.read_bytes()
        assert path.stem == hashlib.sha256(raw).hexdigest()
        public = json.loads(raw)
        assert len(public["train"]) == 3
        assert len(public["test"]) == 4
        assert all(set(pair) == {"input"} for pair in public["test"])
