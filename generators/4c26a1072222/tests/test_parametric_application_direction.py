from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import (
    canonical_path,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "4c26a1072222"
ROOT = find_root(__file__)
PROTOTYPE_PATH = (
    ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
)
VERIFY_PATH = PROTOTYPE_PATH.with_name("verify.py")

_PROTOTYPE = None
_VERIFIER = None
_GENERATOR = None


def _prototype():
    global _PROTOTYPE
    assert PROTOTYPE_PATH.is_file(), "parametric prototype has not been implemented"
    if _PROTOTYPE is None:
        name = "_test_parametric_application_direction_prototype"
        spec = importlib.util.spec_from_file_location(name, PROTOTYPE_PATH)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        _PROTOTYPE = module
    return _PROTOTYPE



def _verifier():
    global _VERIFIER
    assert VERIFY_PATH.is_file(), "parametric verifier has not been implemented"
    if _VERIFIER is None:
        name = "_test_parametric_application_direction_verifier"
        spec = importlib.util.spec_from_file_location(name, VERIFY_PATH)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        parameter_dir = str(VERIFY_PATH.parent)
        sys.path.insert(0, parameter_dir)
        try:
            spec.loader.exec_module(module)
        finally:
            sys.path.remove(parameter_dir)
        _VERIFIER = module
    return _VERIFIER


def _generator():
    global _GENERATOR
    if _GENERATOR is None:
        _GENERATOR, _source, _digest = load_selected_generator(TASK_ID, root=ROOT)
    return _GENERATOR


def _canonical_program() -> str:
    programs = {
        row["program_solution"]
        for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines()
        if (row := json.loads(line)).get("task_id") == TASK_ID
    }
    assert len(programs) == 1
    return programs.pop()


def _pairs(episode):
    return [pair for split in ("train", "test") for pair in episode[split]]


def _serialized_inputs(episode):
    return [
        json.dumps(pair["input"], separators=(",", ":"))
        for pair in _pairs(episode)
    ]


def test_default_program_is_exact_canonical_and_inverse_is_one_checked_edit():
    """Catches canonical drift or an inverse rule that mutates unrelated logic."""
    prototype = _prototype()
    canonical = _canonical_program()
    old = "(v (c-val gr t lr c))"
    new = "(v (c-val gr (cond ((= t 4) 5) ((= t 5) 4) (else t)) lr c))"

    assert prototype.DEFAULT_SETTING == "forward"
    assert prototype.SETTINGS == ("forward", "inverse")
    assert prototype.program_for("forward") == canonical
    assert canonical.count(old) == 1
    assert prototype.program_for("inverse") == canonical.replace(old, new, 1)

    with pytest.raises(TypeError):
        prototype.program_for(None)
    with pytest.raises(ValueError):
        prototype.program_for("reverse-colors")


def test_inverse_application_swaps_only_quarter_turns_per_band():
    """Catches a wrong D4 inverse table or using the inverse to relearn the map."""
    prototype = _prototype()
    generator = _generator()
    inverse_transform = {0: 0, 1: 1, 2: 2, 3: 3, 4: 5, 5: 4, 6: 6, 7: 7}

    for sample_index, first_transform in enumerate(generator.TRANSFORM_NAMES):
        grid = generator.generate(
            7300 + sample_index,
            sample_index,
            n_bands=4,
            first_transform=first_transform,
        )
        info, errors = generator._analyze(grid)
        assert errors == []
        forward = prototype.apply_setting(grid, "forward")
        inverse = prototype.apply_setting(grid, "inverse")

        assert forward == generator.rule_mirror(grid)
        for band in info["bands"]:
            expected_transform = inverse_transform[band["transform"]]
            transformed = generator._transform(band["c"], expected_transform)
            expected = [
                [band["mapping"].get(value, value) for value in row]
                for row in transformed
            ]
            row0 = band["row0"]
            actual = [inverse[row0], inverse[row0 + 1]]
            forward_block = [forward[row0], forward[row0 + 1]]
            assert actual == expected
            if band["transform"] in (4, 5):
                assert actual != forward_block
            else:
                assert actual == forward_block


def test_episode_has_one_fixed_identifiable_setting_and_four_unique_queries():
    """Catches per-pair setting resampling, duplicate queries, or weak demos."""
    prototype = _prototype()
    episode = prototype.build_episode(
        20261023,
        application_direction="inverse",
        n_train=4,
        n_test=4,
    )

    assert episode["parameters"] == {"application_direction": "inverse"}
    assert episode["program"] == prototype.program_for("inverse")
    assert len(episode["train"]) == 4
    assert len(episode["test"]) == 4
    assert prototype.setting_survivors(episode["train"]) == ["inverse"]
    assert prototype.episode_errors(episode) == []

    serialized = _serialized_inputs(episode)
    assert len(serialized) == len(set(serialized)) == 8
    query_serialized = [
        json.dumps(pair["input"], separators=(",", ":"))
        for pair in episode["test"]
    ]
    assert len(query_serialized) == len(set(query_serialized)) == 4

    for pair in _pairs(episode):
        assert prototype.apply_setting(pair["input"], "forward") != prototype.apply_setting(
            pair["input"], "inverse"
        )
        assert pair["output"] == prototype.apply_setting(pair["input"], "inverse")


def test_input_schedule_is_independent_of_selected_setting():
    """Catches rule-dependent sampling that confounds the paired comparison."""
    prototype = _prototype()
    forward = prototype.build_episode(91, application_direction="forward")
    inverse = prototype.build_episode(91, application_direction="inverse")

    assert [pair["input"] for pair in _pairs(forward)] == [
        pair["input"] for pair in _pairs(inverse)
    ]
    assert [pair["sampling"] for pair in _pairs(forward)] == [
        pair["sampling"] for pair in _pairs(inverse)
    ]
    assert all(
        left["output"] != right["output"]
        for left, right in zip(_pairs(forward), _pairs(inverse), strict=True)
    )


def test_public_projection_masks_hidden_rule_and_query_answers():
    """Catches seed, setting, program, query labels, or private metadata leaks."""
    prototype = _prototype()
    episode = prototype.build_episode(41, application_direction="inverse")
    public = prototype.public_projection(episode)
    payload = json.dumps(public, sort_keys=True)

    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert "parameters" not in payload
    assert "program" not in payload
    assert "seed" not in payload
    assert "sampling" not in payload
    assert prototype.public_identifier(episode) == public_challenge_id(public)

    hidden_only_mutation = deepcopy(episode)
    hidden_only_mutation["seed"] = 123456789
    hidden_only_mutation["parameters"] = {"application_direction": "forward"}
    hidden_only_mutation["program"] = "private replacement"
    hidden_only_mutation["generator_sha256"] = "0" * 64
    for pair in hidden_only_mutation["test"]:
        pair["output"] = [[9]]
        pair["sampling"] = {"private": "replacement"}
    assert prototype.public_identifier(hidden_only_mutation) == prototype.public_identifier(
        episode
    )


def test_invalid_seed_setting_and_episode_counts_fail_closed():
    """Catches permissive APIs that emit undersized or ill-typed episodes."""
    prototype = _prototype()

    assert prototype.choose_setting(17) in prototype.SETTINGS
    assert prototype.choose_setting(17) == prototype.choose_setting(17)
    with pytest.raises(TypeError):
        prototype.choose_setting(True)
    with pytest.raises(TypeError):
        prototype.apply_setting([[1]], 1)
    with pytest.raises(ValueError):
        prototype.apply_setting([[1]], "sideways")
    with pytest.raises(TypeError):
        prototype.build_episode(True)
    with pytest.raises(ValueError):
        prototype.build_episode(1, application_direction="sideways")
    with pytest.raises(ValueError):
        prototype.build_episode(1, n_train=3, n_test=4)
    with pytest.raises(ValueError):
        prototype.build_episode(1, n_train=4, n_test=3)


def test_verifier_writes_exact_canonical_public_bytes(tmp_path):
    """Catches public IDs that do not hash the exact visible public file."""
    prototype = _prototype()
    verifier = _verifier()
    episode = prototype.build_episode(20261023, application_direction="inverse")
    public = prototype.public_projection(episode)
    path = tmp_path / "public.json"

    emitted = verifier._write_public(path, public)
    canonical = public_challenge_bytes(public)

    assert emitted == canonical
    assert path.read_bytes() == canonical
    assert hashlib.sha256(path.read_bytes()).hexdigest() == prototype.public_identifier(
        episode
    )


def test_verifier_sorts_batch_entries_by_opaque_public_id():
    """Catches batch manifests whose ordering leaks setting iteration order."""
    verifier = _verifier()
    entries = [
        {"public_id": "f" * 64, "setting": "forward"},
        {"public_id": "2" * 64, "setting": "inverse"},
    ]

    ordered = verifier._sort_manifest_entries(entries)

    assert [row["public_id"] for row in ordered] == ["2" * 64, "f" * 64]
    assert [row["setting"] for row in entries] == ["forward", "inverse"]
