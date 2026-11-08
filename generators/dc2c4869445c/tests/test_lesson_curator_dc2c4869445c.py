"""Opt-in canonical lesson repair against two declared semantic rivals."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import find_root, load_selected_generator


ROOT = find_root(__file__)
TASK = ROOT / "generators/dc2c4869445c"
CURATOR = TASK / "workspace/lesson_curator.py"
FIXTURES = TASK / "counterexamples/review-7d25a1f0d766d596"
CASES = (
    ("production-ambiguity", 1776932124, "easy", 29),
    ("rotation-ambiguity", 632428106, "easy", 96),
    ("medium-rotation-ambiguity", 2201692212, "medium", 89),
)


def saved(name="production-ambiguity"):
    return json.loads((FIXTURES / f"{name}.lesson.json").read_text())


def independent_refutations(lesson):
    generator = load_selected_generator("dc2c4869445c", root=ROOT)[0]
    pairs = lesson["train"] + lesson["test"]
    return {name: [fn(deepcopy(pair["input"])) != pair["output"] for pair in pairs]
            for name, fn in generator.SEMANTIC_RIVALS.items()}


def assert_all_holdouts(lesson):
    assert len(lesson["train"]) == 3 and len(lesson["test"]) == 1
    differences = independent_refutations(lesson)
    assert set(differences) == {"translate_copies", "globally_unique_seeds"}
    for held_out in range(4):
        for name, flags in differences.items():
            assert any(flag for i, flag in enumerate(flags) if i != held_out), (name, held_out)


def test_saved_witness_is_a_real_production_ambiguity():
    lesson = saved()
    flags = independent_refutations(lesson)
    assert flags["globally_unique_seeds"] == [False, False, False, True]
    assert any(flags["translate_copies"][:3])


def test_curator_entrypoint_exists():
    assert CURATOR.is_file(), "The requested fixed-query lesson curator is missing"


@pytest.fixture(scope="module")
def curator():
    assert CURATOR.is_file(), "The requested fixed-query lesson curator is missing"
    spec = importlib.util.spec_from_file_location("dc2c4869445c_lesson_curator_test", CURATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def executor(curator):
    with curator.RuleExecutor() as live:
        yield live


@pytest.mark.parametrize("name,seed,band,start", CASES)
def test_repair_measured_failure_preserves_query_and_refutes_every_holdout(
        curator, executor, name, seed, band, start):
    lesson = saved(name)
    before = deepcopy(lesson)
    original_flags = independent_refutations(lesson)["globally_unique_seeds"]
    assert original_flags == [False, False, False, True]
    calls = executor.calls
    result = curator.curate_lesson(lesson, seed=seed, difficulty=band,
                                    start_index=start, max_attempts=128, executor=executor)
    assert lesson == before
    assert result["private"]["test"] == before["test"]
    assert result["report"]["actual_racket_label_calls"] == executor.calls - calls
    assert result["report"]["actual_racket_label_calls"] >= 5
    assert_all_holdouts(result["private"])
    # An independent execution checks every exported label, including retained
    # pairs and the query. No Python mirror supplies these labels.
    for pair in result["private"]["train"] + result["private"]["test"]:
        assert executor.apply(pair["input"], 0) == pair["output"]
    assert result["report"]["after"]["production"]["strict_demo_elimination"]
    assert len(result["report"]["after"]["holdouts"]) == 4
    assert all(row["strict_demo_elimination"] for row in result["report"]["after"]["holdouts"])
    public = result["public"]
    assert set(public) == {"train", "test"}
    assert public["train"] == result["private"]["train"]
    assert public["test"] == [{"input": before["test"][0]["input"]}]
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert set(public["test"][0]) == {"input"}
    replay = curator.curate_lesson(before, seed=seed, difficulty=band,
                                    start_index=start, max_attempts=128, executor=executor)
    assert replay == result


def test_already_strict_lesson_is_unchanged_and_needs_no_candidate_draws(curator, executor):
    repaired = curator.curate_lesson(saved(), seed=1776932124, difficulty="easy",
                                      start_index=29, max_attempts=128, executor=executor)
    result = curator.curate_lesson(repaired["private"], seed=1, difficulty="hard",
                                    start_index=0, max_attempts=0, executor=executor)
    assert result["private"] == repaired["private"]
    assert result["report"]["attempts"] == 0
    assert result["report"]["accepted_indices"] == []
    assert result["report"]["actual_racket_label_calls"] == 4


@pytest.mark.parametrize("duplicate_index", (25, 28))
def test_one_duplicate_draw_exhausts_bound_without_changing_query(curator, executor, duplicate_index):
    lesson = saved()
    before = deepcopy(lesson)
    # Draw25 is the first demonstration; draw28 is the frozen query itself.
    with pytest.raises(curator.CuratorError, match="exhausted") as caught:
        curator.curate_lesson(lesson, seed=1776932124, difficulty="easy",
                             start_index=duplicate_index, max_attempts=1, executor=executor)
    detail = caught.value.details
    assert detail["attempts"] == 1
    assert detail["attempted_indices"] == [duplicate_index]
    assert detail["rejections"][0]["reason"] == "duplicate_input"
    assert detail["source_identity"]["generator_sha256"]
    assert detail["actual_racket_label_calls"] == 4
    assert lesson == before


def test_original_demo_equal_to_query_cannot_export_a_leaked_challenge(curator, executor):
    lesson = saved()
    lesson["train"][0] = deepcopy(lesson["test"][0])
    with pytest.raises(curator.CuratorError, match="duplicate"):
        curator.curate_lesson(lesson, seed=1776932124, difficulty="easy",
                             start_index=29, max_attempts=128, executor=executor)


def test_answer_equivalent_rival_still_requires_refuting_demonstrations(curator, executor):
    lesson = saved()
    # Four actual labeled fixture pairs, all answer-equivalent for the global
    # singleton rival. Strict export still needs two refuting pairs for holdouts.
    lesson["test"] = [saved("rotation-ambiguity")["train"][0]]
    assert independent_refutations(lesson)["globally_unique_seeds"] == [False] * 4
    result = curator.curate_lesson(lesson, seed=1776932124, difficulty="easy",
                                    start_index=29, max_attempts=128, executor=executor)
    assert result["private"]["test"] == lesson["test"]
    assert_all_holdouts(result["private"])
    assert len(result["report"]["accepted_indices"]) >= 2


def test_a_wrong_saved_label_is_rejected_instead_of_silently_relabelled(curator, executor):
    lesson = saved()
    lesson["test"][0]["output"][0][0] = (lesson["test"][0]["output"][0][0] + 1) % 10
    before = deepcopy(lesson)
    with pytest.raises(curator.CuratorError, match="label mismatch"):
        curator.curate_lesson(lesson, seed=1776932124, difficulty="easy",
                             start_index=29, max_attempts=128, executor=executor)
    assert lesson == before


def test_rival_error_cannot_be_treated_as_refutation(curator, monkeypatch):
    generator = curator.selected_generator()[0]
    def broken(grid):
        raise RuntimeError("deliberate rival scoring failure")
    monkeypatch.setitem(generator.SEMANTIC_RIVALS, "globally_unique_seeds", broken)
    with pytest.raises(curator.CuratorError, match="rival"):
        curator.score_lesson(saved())


def test_missing_declared_rival_cannot_vacuously_pass(curator, monkeypatch):
    generator = curator.selected_generator()[0]
    monkeypatch.delitem(generator.SEMANTIC_RIVALS, "globally_unique_seeds")
    with pytest.raises(curator.CuratorError, match="rival"):
        curator.score_lesson(saved())


def test_mutating_rival_is_rejected(curator, monkeypatch):
    generator = curator.selected_generator()[0]
    original = generator.SEMANTIC_RIVALS["globally_unique_seeds"]
    def mutating(grid):
        prediction = original(deepcopy(grid))
        grid[0][0] = (grid[0][0] + 1) % 10
        return prediction
    monkeypatch.setitem(generator.SEMANTIC_RIVALS, "globally_unique_seeds", mutating)
    with pytest.raises(curator.CuratorError, match="rival"):
        curator.score_lesson(saved())


def test_nondeterministic_rival_is_rejected(curator, monkeypatch):
    generator = curator.selected_generator()[0]
    original = generator.SEMANTIC_RIVALS["globally_unique_seeds"]
    calls = 0
    def changing(grid):
        nonlocal calls
        calls += 1
        result = original(grid)
        if calls % 2 == 0:
            result[0][0] = (result[0][0] + 1) % 10
        return result
    monkeypatch.setitem(generator.SEMANTIC_RIVALS, "globally_unique_seeds", changing)
    with pytest.raises(curator.CuratorError, match="nondeterministic"):
        curator.score_lesson(saved())


def test_writer_emits_clean_artifacts_and_real_identity(curator, tmp_path):
    out = tmp_path / "complete"
    report = curator.write_evidence(out, lesson_path=FIXTURES / "production-ambiguity.lesson.json",
                                    seed=1776932124, difficulty="easy", start_index=29,
                                    max_attempts=128)
    public = json.loads((out / "public.json").read_text())
    private = json.loads((out / "private.json").read_text())
    assert public == {"train": private["train"], "test": [{"input": private["test"][0]["input"]}]}
    assert private["test"] == saved()["test"]
    assert_all_holdouts(private)
    assert report == json.loads((out / "report.json").read_text())
    assert report["runtime_identity"]
    assert report["actual_racket_label_calls"] >= 5
    assert report["source_identity"]["generator_sha256"] == hashlib.sha256(
        curator.selected_generator()[1].read_bytes()).hexdigest()
    assert report["source_identity"]["files"]["curator"]["sha256"] == hashlib.sha256(
        CURATOR.read_bytes()).hexdigest()
    for relative, digest in report["artifacts"].items():
        assert hashlib.sha256((out / relative).read_bytes()).hexdigest() == digest
    for key in ("raw_rule", "callable", "bridge_definition"):
        record = report["source_identity"]["programs"][key]
        assert hashlib.sha256((out / record["path"]).read_bytes()).hexdigest() == record["sha256"]
    assert not (out / "failure.json").exists()


def test_failed_writer_has_source_bound_receipt_and_no_public_challenge(curator, tmp_path):
    out = tmp_path / "failed"
    with pytest.raises(curator.CuratorError, match="exhausted"):
        curator.write_evidence(out, lesson_path=FIXTURES / "production-ambiguity.lesson.json",
                               seed=1776932124, difficulty="easy", start_index=25,
                               max_attempts=1)
    receipt = json.loads((out / "failure.json").read_text())
    assert receipt["status"] == "failed_no_export"
    assert receipt["source_identity"]["generator_sha256"]
    assert receipt["input_lesson_sha256"] == hashlib.sha256(
        (FIXTURES / "production-ambiguity.lesson.json").read_bytes()).hexdigest()
    assert receipt["details"]["attempts"] == 1
    assert not (out / "public.json").exists()
    assert not (out / "private.json").exists()


def test_late_writer_failure_removes_every_challenge_artifact(curator, tmp_path, monkeypatch):
    out = tmp_path / "late-failure"
    original_write = curator._write
    failed = False
    def fail_report_once(path, value):
        nonlocal failed
        if path.name == "report.json" and not failed:
            failed = True
            raise OSError("deliberate report write failure")
        return original_write(path, value)
    monkeypatch.setattr(curator, "_write", fail_report_once)
    with pytest.raises(OSError, match="deliberate report write failure"):
        curator.write_evidence(out, lesson_path=FIXTURES / "production-ambiguity.lesson.json",
                               seed=1776932124, difficulty="easy", start_index=29,
                               max_attempts=128)
    assert failed
    receipt = json.loads((out / "failure.json").read_text())
    assert receipt["status"] == "failed_no_export"
    for name in ("public.json", "private.json", "report.json"):
        assert not (out / name).exists(), name


def test_unreadable_lesson_still_records_source_bound_failure(curator, tmp_path):
    out = tmp_path / "missing-input"
    with pytest.raises(FileNotFoundError):
        curator.write_evidence(out, lesson_path=tmp_path / "does-not-exist.json",
                               seed=1776932124, difficulty="easy", start_index=29,
                               max_attempts=128)
    receipt = json.loads((out / "failure.json").read_text())
    assert receipt["status"] == "failed_no_export"
    assert receipt["input_lesson_sha256"] is None
    assert receipt["source_identity"]["generator_sha256"]
    assert not (out / "public.json").exists()


@pytest.mark.parametrize("changed", ({"max_attempts": -1}, {"max_attempts": True},
                                   {"difficulty": "automatic"}, {"start_index": -1}))
def test_invalid_sampling_requests_are_rejected(curator, executor, changed):
    request = dict(seed=1, difficulty="easy", start_index=0, max_attempts=1, executor=executor)
    request.update(changed)
    with pytest.raises(ValueError):
        curator.curate_lesson(saved(), **request)
