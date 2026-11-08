"""Task-local prototype tests; these do not approve the canonical generator."""
from __future__ import annotations

import copy
import importlib.util
import json
import random
import shutil
import sys
from pathlib import Path

import pytest


TASK_HOME = Path(__file__).resolve().parents[1]
PROTOTYPE = TASK_HOME / "workspace/parametric/reflection.py"


@pytest.fixture(scope="module")
def module():
    assert PROTOTYPE.is_file(), "The requested parametric prototype is not implemented"
    spec = importlib.util.spec_from_file_location("reflection_prototype", PROTOTYPE)
    result = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = result
    spec.loader.exec_module(result)
    return result


def test_default_setting_preserves_canonical_operation(module):
    grid = [[0, 1, 2], [3, 4, 0]]
    assert module.DEFAULT == module.Settings("horizontal", "after")
    assert module.transform(grid) == [[0, 1, 2, 2, 1, 0], [3, 4, 0, 0, 4, 3]]
    assert module.program(module.DEFAULT) == module.CANONICAL_PROGRAM


@pytest.mark.parametrize(
    "axis, side, expected",
    [
        ("horizontal", "after", [[1, 2, 2, 1], [3, 4, 4, 3]]),
        ("horizontal", "before", [[2, 1, 1, 2], [4, 3, 3, 4]]),
        ("vertical", "after", [[1, 2], [3, 4], [3, 4], [1, 2]]),
        ("vertical", "before", [[3, 4], [1, 2], [1, 2], [3, 4]]),
    ],
)
def test_all_four_settings_have_explicit_distinct_semantics(module, axis, side, expected):
    original = [[1, 2], [3, 4]]
    before = copy.deepcopy(original)
    assert module.transform(original, module.Settings(axis, side)) == expected
    assert original == before


@pytest.mark.parametrize("axis, side", [("diagonal", "after"), ("horizontal", "left"), (None, "after"), (True, "before")])
def test_invalid_settings_fail_closed(module, axis, side):
    with pytest.raises(ValueError):
        module.Settings(axis, side)


@pytest.mark.parametrize("grid", [[], [[]], [[1, 2], [3]], [[True]], [[1.0]], [[-1]], [[10]]])
def test_malformed_grids_fail_closed(module, grid):
    with pytest.raises(ValueError):
        module.transform(grid)


def test_dimension_limits_depend_on_selected_axis(module):
    horizontal = module.Settings("horizontal", "after")
    vertical = module.Settings("vertical", "before")
    assert len(module.transform([[1] * 15 for _ in range(30)], horizontal)[0]) == 30
    assert len(module.transform([[1] * 30 for _ in range(15)], vertical)) == 30
    with pytest.raises(ValueError):
        module.transform([[1] * 16], horizontal)
    with pytest.raises(ValueError):
        module.transform([[1] for _ in range(16)], vertical)
    with pytest.raises(ValueError):
        module.transform([[1] for _ in range(31)], horizontal)
    with pytest.raises(ValueError):
        module.transform([[1] * 31], vertical)


def test_sampling_is_fresh_deterministic_and_independent_of_global_rng(module):
    random.seed(987654321)
    before = random.getstate()
    first = module.sample_inputs(42)
    assert random.getstate() == before
    second = module.sample_inputs(42)
    assert first == second
    assert first is not second and first[0] is not second[0]
    first[0][0][0] = (first[0][0][0] + 1) % 10
    assert module.sample_inputs(42) == second
    assert module.select_settings(42, axis="sample", side="sample") == module.select_settings(42, axis="sample", side="sample")


def test_every_demo_separates_all_settings_and_query_is_larger(module):
    for seed in range(32):
        inputs = module.sample_inputs(seed)
        assert len(inputs) == 4
        query = inputs[-1]
        assert len(query) > max(map(len, inputs[:3]))
        assert len(query[0]) > max(len(grid[0]) for grid in inputs[:3])
        assert len({module.digest(grid) for grid in inputs}) == 4
        for grid in inputs:
            outputs = [module.transform(grid, setting) for setting in module.ALL_SETTINGS]
            assert len({module.digest(output) for output in outputs}) == 4
            assert all(len(output) <= 30 and len(output[0]) <= 30 for output in outputs)


@pytest.mark.parametrize("seed", [True, -1, 1.5, "42", 2**63])
def test_invalid_seeds_fail_closed(module, seed):
    with pytest.raises(ValueError):
        module.sample_inputs(seed)


def test_existing_output_is_refused_before_runtime_use(module, tmp_path):
    output = tmp_path / "existing"
    output.mkdir()
    marker = output / "keep.txt"
    marker.write_text("untouched")
    with pytest.raises(FileExistsError):
        module.emit_bundle(output, seed=23, settings=[module.DEFAULT])
    assert marker.read_text() == "untouched"
    assert sorted(path.name for path in output.iterdir()) == ["keep.txt"]


@pytest.fixture(scope="module")
def executed_bundle(module, tmp_path_factory):
    output = tmp_path_factory.mktemp("reflection-evidence") / "bundle"
    evidence = module.emit_bundle(output, seed=1729, settings=list(module.ALL_SETTINGS))
    return output, evidence


def test_racket_labels_rivals_witness_and_canonical_parity(module, executed_bundle):
    output, evidence = executed_bundle
    assert evidence["status"] == "pass"
    assert evidence["runtime"]["backend"] == "racket"
    assert evidence["runtime"]["protected"] is True
    assert evidence["counts"]["episodes"] == 4
    assert evidence["counts"]["labelled_pairs"] == 16
    assert evidence["counts"]["alternate_rival_checks"] == 12
    assert evidence["counts"]["ambiguous_episodes"] == 0
    assert evidence["canonical_parity"]["passed"] is True
    assert evidence["canonical_parity"]["receipt"]["rule_hash_matches_catalog"] is True
    assert len({item["output_sha256"] for item in evidence["distinct_setting_witness"]["results"]}) == 4
    for episode in evidence["episodes"]:
        settings = module.Settings(**episode["parameters"])
        assert episode["program"] == module.program(settings)
        assert episode["program_sha256"] == module.text_digest(episode["program"])
        for pair in episode["pairs"]:
            assert pair["output"] == module.transform(pair["input"], settings)
        assert len(episode["rivals"]) == 3
        assert all(rival["status"] == "refuted_by_demonstrations" for rival in episode["rivals"])
        assert all(rival["demo_matches"] == [False, False, False] for rival in episode["rivals"])
        assert (output / episode["public_path"]).is_file()


def test_public_challenges_expose_only_demonstrations_and_query_inputs(executed_bundle):
    output, evidence = executed_bundle
    for episode in evidence["episodes"]:
        public = json.loads((output / episode["public_path"]).read_text())
        assert set(public) == {"train", "test"}
        assert len(public["train"]) == 3 and len(public["test"]) == 1
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert set(public["test"][0]) == {"input"}


def test_saved_bundle_can_be_reexecuted(module, executed_bundle):
    output, _ = executed_bundle
    verified = module.verify_bundle(output)
    assert verified["status"] == "pass"
    assert verified["counts"]["episodes"] == 4
    assert verified["counts"]["labelled_pairs"] == 16
    assert verified["counts"]["alternate_rival_checks"] == 12
    assert verified["canonical_parity"]["passed"] is True


def test_verify_rejects_public_query_answer_leak(module, executed_bundle, tmp_path):
    original, evidence = executed_bundle
    output = tmp_path / "leaked"
    shutil.copytree(original, output)
    challenge = output / evidence["episodes"][0]["public_path"]
    public = json.loads(challenge.read_text())
    public["test"][0]["output"] = [[1]]
    challenge.write_text(json.dumps(public))
    with pytest.raises(ValueError, match="public"):
        module.verify_bundle(output)


def test_verify_rejects_tampered_private_program(module, executed_bundle, tmp_path):
    original, _ = executed_bundle
    output = tmp_path / "tampered"
    shutil.copytree(original, output)
    path = output / "private/evidence.json"
    evidence = json.loads(path.read_text())
    evidence["episodes"][0]["program"] = "(rule! (lambda (g) g))"
    path.write_text(json.dumps(evidence))
    with pytest.raises(ValueError, match="program"):
        module.verify_bundle(output)


@pytest.mark.parametrize("replacement", [False, 0.0])
def test_verify_rejects_equal_valued_noninteger_cells(module, executed_bundle, tmp_path, replacement):
    original, evidence = executed_bundle
    output = tmp_path / "numeric-tamper"
    shutil.copytree(original, output)
    challenge = output / evidence["episodes"][0]["public_path"]
    public = json.loads(challenge.read_text())
    grid = public["train"][0]["input"]
    row, col = len(grid) // 2, len(grid[0]) // 2
    assert grid[row][col] == 0
    grid[row][col] = replacement
    challenge.write_text(json.dumps(public))
    with pytest.raises(ValueError, match="public"):
        module.verify_bundle(output)


def test_verify_rejects_unlisted_public_files(module, executed_bundle, tmp_path):
    original, evidence = executed_bundle
    output = tmp_path / "extra-public"
    shutil.copytree(original, output)
    (output / "public/answers.json").write_text(json.dumps(evidence["episodes"][0]["pairs"][-1]))
    with pytest.raises(ValueError, match="public"):
        module.verify_bundle(output)


def test_verify_rejects_changed_semantic_provenance(module, executed_bundle, tmp_path):
    original, _ = executed_bundle
    output = tmp_path / "provenance-tamper"
    shutil.copytree(original, output)
    path = output / "private/evidence.json"
    evidence = json.loads(path.read_text())
    evidence["task_id"] = "another-task"
    evidence["family"] = "evaluation:another"
    evidence["default"] = {"axis": "vertical", "side": "before"}
    path.write_text(json.dumps(evidence))
    with pytest.raises(ValueError, match="task_id|family|default"):
        module.verify_bundle(output)


def test_cli_cannot_write_private_receipt_into_public(module, tmp_path, monkeypatch):
    bundle = tmp_path / "bundle"
    (bundle / "public").mkdir(parents=True)
    output = bundle / "public/verification.json"
    calls = []

    def verified_receipt(path):
        calls.append(path)
        return {"status": "pass", "counts": {}, "private_query_label": [[1]]}

    monkeypatch.setattr(module, "verify_bundle", verified_receipt)
    assert module.main(["verify", str(bundle), "--out", str(output)]) == 1
    assert not output.exists()
    assert not calls
