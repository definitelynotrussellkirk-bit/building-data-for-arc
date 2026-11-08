from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_path, find_root

TASK = "7860069b4149"
ROOT = find_root(__file__)
PARAMETRIC = ROOT / "generators" / TASK / "workspace" / "parametric"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PROTOTYPE = _load("review_7860069b4149_prototype", PARAMETRIC / "prototype.py")
ADAPTER = _load("review_7860069b4149_adapter", PARAMETRIC / "adapter.py")



@pytest.fixture(scope="module")
def bridge():
    active = RacketBridge()
    try:
        yield active
    finally:
        active.shutdown()


def _canonical_program():
    rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines() if line.strip()]
    return next(row["program_solution"] for row in rows if row.get("task_id") == TASK)


def _episode_inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_default_program_is_exact_canonical_authority_and_alternate_is_distinct():
    canonical = _canonical_program()
    assert PROTOTYPE.program_for("continuous") == canonical
    alternate = PROTOTYPE.program_for("terminal_only")
    assert alternate != canonical
    assert alternate.startswith("(rule!")


@pytest.mark.parametrize("mode", PROTOTYPE.ALLOWED_TRAIL_MODES)
def test_racket_labels_match_independent_python_mirror(mode, bridge):
    episode = PROTOTYPE.make_episode(7, trail_mode=mode, train_count=2, query_count=2, bridge=bridge)
    assert episode["parameters"] == {"trail_mode": mode}
    for pair in episode["train"] + episode["test"]:
        assert pair["output"] == PROTOTYPE.python_output(pair["input"], trail_mode=mode)


def test_same_seed_and_counts_reuse_exact_inputs_across_settings_but_change_labels(bridge):
    continuous = PROTOTYPE.make_episode(11, trail_mode="continuous", train_count=3, query_count=4, bridge=bridge)
    terminal = PROTOTYPE.make_episode(11, trail_mode="terminal_only", train_count=3, query_count=4, bridge=bridge)
    assert _episode_inputs(continuous) == _episode_inputs(terminal)
    assert any(
        left["output"] != right["output"]
        for left, right in zip(continuous["train"], terminal["train"])
    )
    assert continuous["ambiguities"] == terminal["ambiguities"] == []
    assert all(
        rival["status"] == "refuted_by_demonstrations"
        for rival in continuous["parameter_rivals"] + terminal["parameter_rivals"]
    )


def test_demo_and_query_counts_are_independent_and_bounded(bridge):
    for demos, queries in ((2, 1), (3, 4), (6, 8)):
        episode = PROTOTYPE.make_episode(20 + demos + queries, train_count=demos, query_count=queries, bridge=bridge)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == queries
    for demos, queries in ((1, 4), (7, 4), (3, 0), (3, 9), (True, 4)):
        with pytest.raises((TypeError, ValueError)):
            PROTOTYPE.make_episode(1, train_count=demos, query_count=queries, bridge=bridge)


def test_four_query_episode_contains_distinct_substantive_30x30_stress(bridge):
    episode = PROTOTYPE.make_episode(29, trail_mode="continuous", train_count=3, query_count=4, bridge=bridge)
    inputs = _episode_inputs(episode)
    assert len({PROTOTYPE.grid_sha256(grid) for grid in inputs}) == 7
    stress = episode["test"][3]
    assert (len(stress["input"]), len(stress["input"][0])) == (30, 30)
    changed = sum(
        before != after
        for before_row, after_row in zip(stress["input"], stress["output"])
        for before, after in zip(before_row, after_row)
    )
    assert changed >= 40
    assert stress["output"] == PROTOTYPE.python_output(stress["input"], trail_mode="continuous")


def test_public_projection_hides_setting_program_and_query_answers(bridge):
    episode = PROTOTYPE.make_episode(31, trail_mode="terminal_only", train_count=3, query_count=4, bridge=bridge)
    public = PROTOTYPE.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    raw = PROTOTYPE.public_bytes(episode)
    assert b"terminal_only" not in raw
    assert episode["program"].encode() not in raw
    assert PROTOTYPE.public_id(episode) == PROTOTYPE.public_id(public)


def test_adapter_is_thin_strict_and_returns_promotion_shape():
    result = ADAPTER.generate(41, {"trail_mode": "continuous"}, demos=2, queries=4)
    assert len(result["train"]) == 2 and len(result["test"]) == 4
    assert result["program_solution"] == ADAPTER.program({"trail_mode": "continuous"})
    for bad in ({}, {"trail_mode": "unknown"}, {"trail_mode": "continuous", "extra": 1}, None):
        with pytest.raises(ValueError):
            ADAPTER.program(bad)


def test_evidence_writer_and_verifier_reject_public_tampering(
    evidence_template, tmp_path
):
    out = _copy_evidence(evidence_template, tmp_path)
    report = json.loads((out / "report.json").read_text())
    assert PROTOTYPE.verify_evidence(out)["valid"] is True
    assert report["settings_checked"] == list(PROTOTYPE.ALLOWED_TRAIL_MODES)

    public_path = next((out / "public").glob("*.json"))
    public = json.loads(public_path.read_text())
    public["test"][0]["output"] = [[0]]
    public_path.write_text(json.dumps(public) + "\n")
    relative = public_path.relative_to(out).as_posix()
    _rehash_manifest_entry(out, relative)
    with pytest.raises(ValueError):
        PROTOTYPE.verify_evidence(out)


def test_sequential_query_projection_hides_future_inputs_and_preserves_single_query_first_turn(bridge):
    full = PROTOTYPE.make_episode(
        67, trail_mode="terminal_only", train_count=3, query_count=4, bridge=bridge
    )
    single = PROTOTYPE.make_episode(
        67, trail_mode="terminal_only", train_count=3, query_count=1, bridge=bridge
    )
    turns = PROTOTYPE.public_query_turns(full)
    assert len(turns) == 4
    assert all(set(turn) == {"train", "test"} and len(turn["test"]) == 1 for turn in turns)
    assert [turn["test"][0]["input"] for turn in turns] == [
        pair["input"] for pair in full["test"]
    ]
    assert turns[0] == PROTOTYPE.public_challenge(single)
    for turn in turns:
        raw = json.dumps(turn, sort_keys=True).encode()
        assert b"terminal_only" not in raw
        assert full["program"].encode() not in raw
        assert all("output" not in pair for pair in turn["test"])


@pytest.fixture(scope="module")
def evidence_template(tmp_path_factory, bridge):
    out = tmp_path_factory.mktemp("parametric-evidence") / "current"
    PROTOTYPE.write_evidence(seed=79, out=out, train_count=3, query_count=4, bridge=bridge)
    assert PROTOTYPE.verify_evidence(out)["valid"] is True
    return out


def _copy_evidence(template, tmp_path):
    out = tmp_path / "evidence"
    shutil.copytree(template, out)
    return out


def _rehash_manifest_entry(root, relative):
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["files"][relative] = hashlib.sha256((root / relative).read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def test_evidence_verifier_rejects_stale_generator_binding_even_when_manifest_is_rehashed(
    evidence_template, tmp_path
):
    out = _copy_evidence(evidence_template, tmp_path)
    report_path = out / "report.json"
    report = json.loads(report_path.read_text())
    report["generator_sha256"] = "0" * 64
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    _rehash_manifest_entry(out, "report.json")
    with pytest.raises(ValueError, match="generator"):
        PROTOTYPE.verify_evidence(out)


def test_evidence_verifier_rejects_missing_setting_row_even_when_manifest_is_rehashed(
    evidence_template, tmp_path
):
    out = _copy_evidence(evidence_template, tmp_path)
    report_path = out / "report.json"
    report = json.loads(report_path.read_text())
    report["episodes"] = report["episodes"][:1]
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    _rehash_manifest_entry(out, "report.json")
    with pytest.raises(ValueError, match="settings"):
        PROTOTYPE.verify_evidence(out)


def test_evidence_verifier_rejects_manifest_path_escape(evidence_template, tmp_path):
    out = _copy_evidence(evidence_template, tmp_path)
    outside = tmp_path / "outside.txt"
    outside.write_text("not evidence\n")
    manifest_path = out / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["files"]["../outside.txt"] = hashlib.sha256(outside.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    with pytest.raises(ValueError):
        PROTOTYPE.verify_evidence(out)



def test_evidence_verifier_rejects_self_consistent_program_replacement(
    evidence_template, tmp_path
):
    out = _copy_evidence(evidence_template, tmp_path)
    report = json.loads((out / "report.json").read_text())
    row = report["episodes"][0]
    private_path = out / row["private_path"]
    rule_path = out / row["rule_path"]
    private = json.loads(private_path.read_text())
    fake_program = "(rule! g)"
    private["program"] = fake_program
    private["program_sha256"] = hashlib.sha256(fake_program.encode()).hexdigest()
    private["normalized_program_sha256"] = PROTOTYPE.normalized_program_sha256(fake_program)
    private_path.write_text(json.dumps(private, indent=2, sort_keys=True) + "\n")
    rule_path.write_text(fake_program)
    _rehash_manifest_entry(out, row["private_path"])
    _rehash_manifest_entry(out, row["rule_path"])
    with pytest.raises(ValueError, match="program"):
        PROTOTYPE.verify_evidence(out)


def test_evidence_verifier_rejects_report_count_mismatch(
    evidence_template, tmp_path
):
    out = _copy_evidence(evidence_template, tmp_path)
    report_path = out / "report.json"
    report = json.loads(report_path.read_text())
    report["train_count"] = 2
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    _rehash_manifest_entry(out, "report.json")
    with pytest.raises(ValueError, match="count"):
        PROTOTYPE.verify_evidence(out)


def test_evidence_verifier_rejects_unlisted_extra_file(evidence_template, tmp_path):
    out = _copy_evidence(evidence_template, tmp_path)
    (out / "unlisted.txt").write_text("unbound bytes\n")
    with pytest.raises(ValueError, match="inventory"):
        PROTOTYPE.verify_evidence(out)
