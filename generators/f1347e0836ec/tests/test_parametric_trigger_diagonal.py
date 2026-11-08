"""Prototype-only tests for proposed trigger-diagonal rule variants."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

for ancestor in Path(__file__).resolve().parents:
    helper = ancestor / "shared" / "runtime"
    if (helper / "reviewer_support.py").is_file():
        sys.path.insert(0, str(helper))
        break
    if (ancestor / "reviewer_support.py").is_file():
        sys.path.insert(0, str(ancestor))
        break

from reviewer_support import find_root

TASK_ID = "f1347e0836ec"
ROOT = find_root(__file__)
PROTOTYPE = (
    ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
)


def load_prototype():
    assert PROTOTYPE.is_file(), "the runnable parametric prototype must exist"
    spec = importlib.util.spec_from_file_location("f1347_parametric_prototype", PROTOTYPE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def prototype():
    return load_prototype()


def test_parameter_choice_is_deterministic_and_covers_both_settings(prototype):
    assert prototype.choose_parameters(17) == prototype.choose_parameters(17)
    observed = {
        prototype.choose_parameters(seed)["trigger_diagonal"] for seed in range(64)
    }
    assert observed == {"main", "anti"}


@pytest.mark.parametrize("seed", [True, False, 1.0, "1"])
def test_parameter_choice_rejects_non_integer_seeds(prototype, seed):
    with pytest.raises(TypeError, match="episode seed must be an integer"):
        prototype.choose_parameters(seed)


@pytest.mark.parametrize(
    "value", [None, "diagonal", "MAIN", True, 1, 1.0]
)
def test_program_rejects_unsupported_parameter_values(prototype, value):
    with pytest.raises(ValueError, match="trigger_diagonal"):
        prototype.racket_program({"trigger_diagonal": value})


def test_executed_racket_programs_separate_main_and_anti_predicates(prototype):
    grid = [
        [5, 5, 5, 5, 5, 5],
        [5, 5, 5, 5, 6, 5],
        [5, 5, 5, 5, 5, 5],
        [5, 5, 5, 5, 5, 5],
        [5, 5, 5, 5, 5, 5],
        [5, 5, 5, 5, 5, 5],
    ]
    main_program = prototype.racket_program({"trigger_diagonal": "main"})
    anti_program = prototype.racket_program({"trigger_diagonal": "anti"})
    main_output = prototype.execute_program(main_program, [grid])[0]
    anti_output = prototype.execute_program(anti_program, [grid])[0]

    assert main_output == [
        [1, 1, 1, 1, 1, 5],
        [5, 5, 5, 5, 6, 5],
        [5, 5, 5, 5, 1, 5],
        [5, 5, 5, 5, 1, 5],
        [5, 5, 5, 5, 1, 5],
        [5, 5, 5, 5, 1, 1],
    ]
    assert anti_output == [
        [5, 5, 5, 5, 1, 1],
        [5, 5, 5, 5, 6, 5],
        [5, 5, 5, 5, 1, 5],
        [5, 5, 5, 5, 1, 5],
        [5, 5, 5, 5, 1, 5],
        [1, 1, 1, 1, 1, 5],
    ]
    assert main_output != anti_output


def test_default_executed_racket_matches_every_labeled_canonical_pair(prototype):
    from reviewer_support import canonical_pairs

    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    program = prototype.racket_program(
        {"trigger_diagonal": prototype.DEFAULT_TRIGGER_DIAGONAL}
    )
    actual = prototype.execute_program(program, [pair["input"] for pair in pairs])
    assert actual == [pair["output"] for pair in pairs]


@pytest.fixture(scope="module")
def selected_generator():
    from reviewer_support import load_selected_generator

    return load_selected_generator(TASK_ID, root=ROOT)


def test_episode_uses_one_rule_for_three_demos_and_one_query_and_replays(
    prototype, selected_generator
):
    first = prototype.make_episode(23, generator_bundle=selected_generator)
    second = prototype.make_episode(23, generator_bundle=selected_generator)

    assert first == second
    assert len(first["demos"]) == 3
    assert set(first["query"]) == {"input", "output"}
    assert first["parameters"] == prototype.choose_parameters(23)

    generator = selected_generator[0]
    all_pairs = [*first["demos"], first["query"]]
    assert all(
        generator.self_check(pair["input"], difficulty="medium") == []
        for pair in all_pairs
    )

    selected_program = prototype.racket_program(first["parameters"])
    replayed = prototype.execute_program(
        selected_program, [pair["input"] for pair in all_pairs]
    )
    assert replayed == [pair["output"] for pair in all_pairs]


def test_demo_outputs_identify_exactly_the_selected_setting(
    prototype, selected_generator
):
    episode = prototype.make_episode(23, generator_bundle=selected_generator)
    result = prototype.check_identifiability(episode["demos"])

    assert result["surviving_settings"] == [
        episode["parameters"][prototype.PARAMETER_NAME]
    ]
    assert result["unique"] is True
    assert result["demonstration_count"] == 3


def test_both_diagonals_only_is_deliberately_ambiguous(prototype):
    grid = [
        [7, 7, 7, 7, 7],
        [7, 7, 7, 7, 7],
        [7, 7, 8, 7, 7],
        [7, 7, 7, 7, 7],
        [7, 7, 7, 7, 7],
    ]
    program = prototype.racket_program({prototype.PARAMETER_NAME: "main"})
    output = prototype.execute_program(program, [grid])[0]
    result = prototype.check_identifiability([{"input": grid, "output": output}])

    assert result["surviving_settings"] == ["main", "anti"]
    assert result["unique"] is False
    assert result["demonstration_count"] == 1


def test_public_challenge_redacts_hidden_rule_and_query_answer(
    prototype, selected_generator
):
    episode = prototype.make_episode(23, generator_bundle=selected_generator)
    public = prototype.public_challenge(episode)

    assert set(public) == {"schema", "task_id", "demos", "query"}
    assert public["task_id"] == TASK_ID
    assert public["demos"] == episode["demos"]
    assert public["query"] == {"input": episode["query"]["input"]}
    serialized = repr(public).lower()
    for secret in ("seed", "parameter", "trigger_diagonal", "racket", "output':"):
        if secret == "output':":
            assert "'query': {'input':" in serialized
            assert "'query': {'input':" in serialized and "'query': {'output':" not in serialized
        else:
            assert secret not in serialized


def test_evidence_builder_covers_both_settings_and_refuses_overwrite(
    tmp_path, prototype
):
    import json
    import subprocess

    builder = PROTOTYPE.with_name("build_prototype.py")
    assert builder.is_file(), "the evidence builder must exist"
    out_dir = tmp_path / "parametric-evidence"
    completed = subprocess.run(
        [sys.executable, str(builder), "--out-dir", str(out_dir)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr

    summary = json.loads((out_dir / "summary.json").read_text(encoding="utf-8"))
    assert summary["passed"] is True
    assert summary["settings_covered"] == ["anti", "main"]
    assert summary["checks"] == {
        "ambiguity_diagnostic_keeps_both_settings": True,
        "canonical_default_exact_parity": True,
        "public_challenges_redacted": True,
        "separating_witness_differs": True,
        "unique_complete_episodes": True,
    }

    for setting in prototype.ALLOWED_TRIGGER_DIAGONALS:
        private_path = out_dir / f"episode-{setting}.json"
        public_path = out_dir / f"challenge-{setting}.json"
        program_path = out_dir / f"program-{setting}.rkt"
        assert private_path.is_file()
        assert public_path.is_file()
        assert program_path.is_file()
        public = json.loads(public_path.read_text(encoding="utf-8"))
        assert set(public) == {"schema", "task_id", "demos", "query"}
        assert set(public["query"]) == {"input"}
        public_text = public_path.read_text(encoding="utf-8").lower()
        for secret in ("seed", "trigger_diagonal", "racket_program", "parameters"):
            assert secret not in public_text

    assert (out_dir / "canonical-parity.json").is_file()
    assert (out_dir / "separating-witness.json").is_file()
    assert (out_dir / "ambiguity-diagnostic.json").is_file()
    assert (out_dir / "receipt.json").is_file()

    refused = subprocess.run(
        [sys.executable, str(builder), "--out-dir", str(out_dir)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    assert refused.returncode != 0
    assert "already exists" in (refused.stdout + refused.stderr)
