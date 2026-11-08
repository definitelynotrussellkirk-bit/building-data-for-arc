"""Privacy, replay, and publication regressions for the prototype evidence writer."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


PATH = Path(__file__).resolve().parents[1] / "workspace/parametric/build_evidence.py"


def load_evidence():
    assert PATH.is_file(), "The task-local evidence writer has not been implemented"
    spec = importlib.util.spec_from_file_location("rectangle_parametric_evidence", PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def episode():
    return {
        "task_id": "13507b4f7614",
        "seed": 0,
        "settings": {"join_axis": "none"},
        "program_solution": "chosen",
        "train": [{"input": [[0]], "output": [[1]]}],
        "test": [{"input": [[2]], "output": [[3]]}],
    }


def execute(program, grid):
    value = grid[0][0]
    if program == "chosen":
        return [[value + 1]]
    if program == "alternate":
        return [[0]]
    if program == "query_shortcut":
        return [[1 if value == 0 else 4]]
    if program == "broken":
        raise RuntimeError("invalid rival")
    raise AssertionError(program)


def test_public_bytes_and_names_ignore_private_answers_settings_and_programs():
    evidence = load_evidence()
    original = episode()
    expected = b'{"test":[{"input":[[2]]}],"train":[{"input":[[0]],"output":[[1]]}]}\n'
    assert evidence.public_bytes(original) == expected
    assert evidence.public_id(original) == hashlib.sha256(expected).hexdigest()
    changed = deepcopy(original)
    changed["test"][0]["output"] = [[8]]
    changed["settings"] = {"join_axis": "vertical"}
    changed["program_solution"] = "private replacement"
    changed["seed"] = 999
    assert evidence.public_bytes(changed) == expected
    assert evidence.public_id(changed) == evidence.public_id(original)
    changed["train"][0]["output"] = [[2]]
    assert evidence.public_id(changed) != evidence.public_id(original)


def test_single_query_observation_hides_future_inputs_and_total_count():
    evidence = load_evidence()
    first = episode()
    extended = deepcopy(first)
    extended["test"].append({"input": [[9]], "output": [[8]]})
    expected = {"train": [{"input": [[0]], "output": [[1]]}],
                "test": [{"input": [[2]]}]}
    assert evidence.observation(first, 0) == expected
    assert evidence.observation(extended, 0) == expected
    visible = evidence.observation(extended, 0)
    visible["train"][0]["input"][0][0] = 7
    assert extended["train"][0]["input"] == [[0]]
    for invalid in (-1, True, 2):
        with pytest.raises((ValueError, IndexError)):
            evidence.observation(extended, invalid)


def test_count_and_input_reuse_errors_fail_before_execution():
    evidence = load_evidence()
    with pytest.raises(ValueError, match="count"):
        evidence.check_episode(episode(), demos=2, queries=1,
            declared_programs={"none": "chosen", "horizontal": "alternate"},
            rivals={}, apply_program=execute)
    duplicate = episode()
    duplicate["test"][0]["input"] = [[0]]
    with pytest.raises(ValueError, match="distinct"):
        evidence.check_episode(duplicate, demos=1, queries=1,
            declared_programs={"none": "chosen", "horizontal": "alternate"},
            rivals={}, apply_program=execute)


def test_demo_surviving_rival_with_a_different_query_answer_fails():
    evidence = load_evidence()
    with pytest.raises(ValueError, match="query_shortcut"):
        evidence.check_episode(episode(), demos=1, queries=1,
            declared_programs={"none": "chosen", "horizontal": "alternate"},
            rivals={"query_shortcut": "query_shortcut"}, apply_program=execute)


def test_sample_equivalence_is_recorded_without_claiming_universal_elimination():
    evidence = load_evidence()
    result = evidence.check_episode(episode(), demos=1, queries=1,
        declared_programs={"none": "chosen", "horizontal": "alternate"},
        rivals={"skip_a": "chosen"}, apply_program=execute)
    assert result["declared_survivors"] == [{"join_axis": "none"}]
    assert result["rivals"]["skip_a"]["status"] == "agrees_on_sampled_queries"
    assert result["rivals"]["skip_a"]["demo_disagreements"] == []
    assert result["rivals"]["skip_a"]["query_disagreements"] == []


def test_runtime_errors_cannot_count_as_rival_rejection():
    evidence = load_evidence()
    with pytest.raises(ValueError, match="broken"):
        evidence.check_episode(episode(), demos=1, queries=1,
            declared_programs={"none": "chosen", "horizontal": "alternate"},
            rivals={"broken": "broken"}, apply_program=execute)


def test_claimed_labels_are_reexecuted_and_bool_cells_are_rejected():
    evidence = load_evidence()
    incorrect = episode()
    incorrect["test"][0]["output"] = [[4]]
    with pytest.raises(ValueError, match="label"):
        evidence.check_episode(incorrect, demos=1, queries=1,
            declared_programs={"none": "chosen", "horizontal": "alternate"},
            rivals={}, apply_program=execute)
    invalid = episode()
    invalid["train"][0]["input"] = [[True]]
    with pytest.raises(ValueError):
        evidence.public_bytes(invalid)


def test_bundle_verification_detects_private_tampering_and_refuses_overwrite(tmp_path):
    evidence = load_evidence()
    output = tmp_path / "new-evidence"
    manifest = evidence.write_bundle(output, [episode()], {"scope": "synthetic serialization test"})
    assert manifest["episodes"] == 1
    identifier = evidence.public_id(episode())
    assert (output / "public" / f"{identifier}.json").read_bytes() == evidence.public_bytes(episode())
    assert evidence.verify_bundle(output)["episodes"] == 1
    with pytest.raises(FileExistsError):
        evidence.write_bundle(output, [episode()], {})
    hidden = output / "private/episodes" / f"{identifier}.json"
    tampered = json.loads(hidden.read_bytes())
    tampered["test"][0]["output"] = [[9]]
    hidden.write_text(json.dumps(tampered))
    with pytest.raises(ValueError, match="hash"):
        evidence.verify_bundle(output)


def test_visible_duplicates_fail_without_creating_destination(tmp_path):
    evidence = load_evidence()
    original = episode()
    duplicate = deepcopy(original)
    duplicate["settings"] = {"join_axis": "vertical"}
    duplicate["test"][0]["output"] = [[8]]
    output = tmp_path / "duplicates"
    with pytest.raises(ValueError, match="duplicate"):
        evidence.write_bundle(output, [original, duplicate], {})
    assert not output.exists()


def test_witness_rejects_python_intermediate_that_disagrees_with_protected_racket():
    evidence = load_evidence()
    adapter = evidence._adapter()
    bad_mirror = SimpleNamespace(
        program=adapter.program,
        RULES=SimpleNamespace(
            counterfactual_program=adapter.RULES.counterfactual_program,
            joined_grid=lambda grid, axis: [[0]],
        ),
    )
    episodes = []
    programs = {}
    horizontal = [[4, 4, 0, 4, 4] for _ in range(3)]
    vertical = [list(row) for row in zip(*horizontal)]
    for axis, grid in (("horizontal", horizontal), ("vertical", vertical)):
        settings = {"join_axis": axis}
        program = adapter.program(settings)
        programs[json.dumps(settings, sort_keys=True, separators=(",", ":"))] = hashlib.sha256(program.encode()).hexdigest()
        episodes.append({"settings": settings, "train": [{"input": grid}], "test": []})
    qualification = {"schema": "arcpuzzles-parametric-qualification-v1",
                     "status": "qualified", "task_id": "13507b4f7614",
                     "source_binding": {"task_id": "13507b4f7614"}, "programs": programs}
    with evidence._local_imports(evidence.ROOT / "shared/runtime", evidence.HERE):
        apply, identity, bridge = evidence._real_evaluator(evidence.ROOT / "shared/runtime")
        try:
            with pytest.raises(ValueError, match="intermediate"):
                evidence.make_sequential_witness(episodes, qualification, bad_mirror, apply, identity)
            witness = evidence.make_sequential_witness(episodes, qualification, adapter, apply, identity)
            assert [case["intermediate_value"]["joined_grid"] for case in witness["cases"]] == [
                [[4, 4, 4, 4, 4]] * 3, [[4, 4, 4]] * 5]
            assert witness["racket"] == {"backend": "racket", "protected": True}
            assert witness["source_binding"] == qualification["source_binding"]
        finally:
            bridge.close()
