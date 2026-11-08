from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import find_root

TASK_ROOT = Path(__file__).resolve().parents[1]
PARAMETRIC_ROOT = TASK_ROOT / "workspace" / "parametric"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PROTOTYPE = _load("parametric_9ce2dcf587b8", PARAMETRIC_ROOT / "prototype.py")
PROBE = _load("reference_probe_9ce2dcf587b8_parametric", TASK_ROOT / "workspace" / "reference_probe.py")
sys.path.insert(0, str(PARAMETRIC_ROOT))
VERIFY = _load("parametric_verify_9ce2dcf587b8", PARAMETRIC_ROOT / "verify.py")


def test_parameter_contract_and_episode_choice_are_bounded_and_deterministic():
    assert PROTOTYPE.PARAMETER_NAME == "diagonal_axes"
    assert PROTOTYPE.ALLOWED_SETTINGS == ("both", "main_only")
    assert PROTOTYPE.DEFAULT_SETTING == "both"
    for seed in (0, 1, 2, 19, 20261020):
        first = PROTOTYPE.choose_setting(seed)
        assert first in PROTOTYPE.ALLOWED_SETTINGS
        assert PROTOTYPE.choose_setting(seed) == first


@pytest.mark.parametrize("bad", [None, True, 1.5, "1"])
def test_parameter_seed_validation_is_strict(bad):
    with pytest.raises(TypeError):
        PROTOTYPE.choose_setting(bad)


@pytest.mark.parametrize("bad", [None, True, 1, "anti_only", ""])
def test_parameter_setting_validation_is_strict(bad):
    with pytest.raises((TypeError, ValueError)):
        PROTOTYPE.program_for(bad)


def test_default_program_is_exact_canonical_and_variant_changes_only_directions():
    canonical = PROBE.authority_sources(find_root(__file__))["canonical"]
    assert PROTOTYPE.program_for("both") == canonical
    assert canonical.count("diagonal-deltas") == 1
    assert PROTOTYPE.program_for("main_only") == canonical.replace(
        "diagonal-deltas",
        "'((-1 -1) (1 1))",
        1,
    )


def test_verifier_builds_a_bare_bridge_callable_without_authoring_only_scripts():
    callable_text = VERIFY._callable_text(PROTOTYPE.program_for("both"))
    assert callable_text.startswith("(lambda (g) (let* ((h (rows g)) (w (cols g)))")
    assert "(lambda (g)" in callable_text


@pytest.mark.parametrize("setting", ["both", "main_only"])
def test_episode_uses_one_setting_and_every_pair_distinguishes_the_rival(setting):
    episode = PROTOTYPE.build_episode(20261020, setting=setting)
    assert episode["meta"][PROTOTYPE.PARAMETER_NAME] == setting
    assert episode["meta"]["default_setting"] == "both"
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 1

    rival = next(value for value in PROTOTYPE.ALLOWED_SETTINGS if value != setting)
    for pair in episode["train"] + episode["test"]:
        selected = PROTOTYPE.apply_python(pair["input"], setting)
        alternate = PROTOTYPE.apply_python(pair["input"], rival)
        assert pair["output"] == selected
        assert selected != alternate


def test_public_challenge_omits_parameter_program_and_query_answer():
    episode = PROTOTYPE.build_episode(20261020, setting="main_only")
    challenge = PROTOTYPE.public_challenge(episode)
    serialized = json.dumps(challenge, sort_keys=True)
    assert PROTOTYPE.PARAMETER_NAME not in serialized
    assert "main_only" not in serialized
    assert "rule!" not in serialized
    assert all("output" in pair for pair in challenge["train"])
    assert all("output" not in pair for pair in challenge["test"])
