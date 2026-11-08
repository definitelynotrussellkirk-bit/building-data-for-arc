"""The export gate must evaluate the actual demos against every query."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

from test_review_c2b9484357c1 import gen


@pytest.fixture
def gate():
    path = Path(__file__).resolve().parents[1] / "workspace/validate_lessons.py"
    assert path.is_file(), "the emitted-lesson gate is missing"
    spec = importlib.util.spec_from_file_location("lesson_gate", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def episode(n_train=4, query_indices=(4,)):
    def pair(i):
        g = gen.generate(17, i, difficulty="medium")
        return {"input": g, "output": gen._true_output(g)}
    return {"task_id": gen.TASK_ID, "seed": 17,
            "train": [pair(i) for i in range(n_train)],
            "test": [pair(i) for i in query_indices],
            "provenance": {"generator_sha256": "test-hash", "rule_hash": gen.RULE_HASH}}


def test_actual_three_demo_export_is_rejected(gate):
    result = gate.assess_episode(episode(3, (3,)), gen, "test-hash")
    assert result["status"] == "fail"
    assert any("fits every demo" in s for s in result["findings"])


def test_four_demo_export_passes_without_mutation(gate):
    item = episode()
    original = copy.deepcopy(item)
    assert gate.assess_episode(item, gen, "test-hash")["status"] == "pass"
    assert item == original


def test_second_query_is_not_silently_ignored(gate):
    result = gate.assess_episode(episode(3, (0, 3)), gen, "test-hash")
    assert result["status"] == "fail"
    assert any("query 1" in s for s in result["findings"])


@pytest.mark.parametrize("digest", [None, "stale-hash"])
def test_missing_or_stale_provenance_fails_closed(gate, digest):
    item = episode()
    item["provenance"]["generator_sha256"] = digest
    result = gate.assess_episode(item, gen, "test-hash")
    assert result["status"] == "fail"
    assert any("generator_sha256" in s for s in result["findings"])


def test_mutating_hook_fails_without_changing_caller(gate):
    def bad(demos, query):
        demos[0]["input"][0][0] = 99
        return []
    subject = SimpleNamespace(TASK_ID=gen.TASK_ID, RULE_HASH=gen.RULE_HASH,
                              lesson_identifiable=bad, EXAMPLES_NEEDED=4)
    item = episode()
    original = copy.deepcopy(item)
    result = gate.assess_episode(item, subject, "test-hash")
    assert result["status"] == "fail"
    assert any("mutated" in s for s in result["findings"])
    assert item == original


def test_no_contract_is_not_a_pass(gate):
    subject = SimpleNamespace(TASK_ID=gen.TASK_ID, RULE_HASH=gen.RULE_HASH)
    result = gate.assess_episode(episode(), subject, "test-hash")
    assert result["status"] == "no_contract"


def test_malformed_query_is_retained_as_failure(gate):
    item = episode()
    item["test"][0]["output"] = [[False]]
    result = gate.assess_episode(item, gen, "test-hash")
    assert result["status"] == "fail"
    assert any("grid" in s for s in result["findings"])


@pytest.mark.parametrize("foreign_part", ["runtime", "generator"])
def test_loader_rejects_modules_from_another_library(gate, tmp_path, monkeypatch, foreign_part):
    library = tmp_path / "library"
    source = library / "generators/isolated_subject/generator.py"
    source.parent.mkdir(parents=True)
    source.write_text("TASK_ID = 'isolated_subject'\n")
    runtime = library / "shared/runtime/puzzle_generators"
    package = SimpleNamespace(__path__=[str(runtime / "per_puzzle")],
                              __file__=str(runtime / "per_puzzle/__init__.py"))
    root = SimpleNamespace(__file__=str(runtime / "__init__.py"))
    subject = SimpleNamespace(__file__=str(source))
    if foreign_part == "runtime":
        package.__file__ = str(tmp_path / "other/per_puzzle/__init__.py")
    else:
        subject.__file__ = str(tmp_path / "other/generator.py")
    modules = {"puzzle_generators": root,
               "puzzle_generators.per_puzzle": package,
               "puzzle_generators.per_puzzle.isolated_subject.generator": subject}
    monkeypatch.setattr(gate.importlib, "import_module", lambda name: modules[name])
    with pytest.raises(ValueError, match="another|outside"):
        gate.load_generator(library, "isolated_subject")
