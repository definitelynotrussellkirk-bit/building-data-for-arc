"""Current-source regressions for the selectively merged threshold family."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
from arc_repl.racket_bridge import RacketBridge
from reviewer_support import find_root, load_selected_generator

ROOT = find_root(__file__)
HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace/parametric"

def load_prototype():
    spec = importlib.util.spec_from_file_location("reconciled_panel_threshold", PARAMETRIC / "prototype.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_threshold_one_is_lawful_and_separates_all_three_exact_racket_programs():
    proto = load_prototype()
    gen, _, _ = load_selected_generator("a9c4475d7cda", root=ROOT)
    grid = gen.generate(1701, 19, grid_h=11, grid_w=11, count_profile="balanced")
    assert gen.self_check(grid) == []
    assert {1, 2, 3} <= {v for row in proto.panel_counts(grid) for v in row}
    assert proto.ALLOWED_MIN_PANEL_COUNTS == (1, 2, 3)
    with RacketBridge() as bridge:
        outputs = [proto.execute(bridge, proto.rule_text(t), grid) for t in (1, 2, 3)]
    assert len({json.dumps(out) for out in outputs}) == 3
    assert outputs == [proto.apply_python(grid, t) for t in (1, 2, 3)]
    assert proto.rule_text(2) == proto.canonical_program(ROOT)

def test_full_canonical_source_and_saved_programs_are_guarded(tmp_path, monkeypatch):
    proto = load_prototype()
    with pytest.raises(ValueError, match="canonical|source"):
        proto.render_program(proto.canonical_program(ROOT) + " ", 3)
    copy = tmp_path / "programs"
    copy.mkdir()
    for t in (1, 2, 3):
        (copy / f"threshold-{t}.rkt").write_text(proto.render_program(proto.canonical_program(ROOT), t))
    monkeypatch.setattr(proto, "PROGRAMS", copy)
    (copy / "threshold-1.rkt").write_text((copy / "threshold-1.rkt").read_text() + " ")
    with pytest.raises(ValueError, match="program|source"):
        proto.rule_text(1)

@pytest.mark.parametrize("threshold", [1, 2, 3])
def test_one_demo_identifies_all_declared_rivals_and_queries(threshold):
    proto = load_prototype()
    episode = proto.build_claimed_episode(2**63-1, min_panel_count=threshold, demos=1, queries=4)
    assert proto.surviving_thresholds(episode["train"]) == [threshold]
    assert {row["min_panel_count"] for row in episode["rivals"]} == {1, 2, 3} - {threshold}
    assert all(row["demo_differences"] == [0] and row["query_differences"] == [0, 1, 2, 3] for row in episode["rivals"])

def test_larger_independent_count_boundary_returns_32_distinct_lawful_inputs():
    proto = load_prototype()
    episode = proto.build_claimed_episode(99, min_panel_count=1, demos=16, queries=16)
    pairs = episode["train"] + episode["test"]
    assert len(episode["train"]) == len(episode["test"]) == 16
    assert len({json.dumps(pair["input"]) for pair in pairs}) == 32

def test_duplicate_preflight_and_physical_public_emission_order(tmp_path, monkeypatch):
    proto = load_prototype()
    episodes = [proto.build_claimed_episode(41, min_panel_count=t, demos=1, queries=1) for t in (3, 2, 1)]
    duplicate = tmp_path / "duplicate"
    with pytest.raises(ValueError, match="duplicate"):
        proto.write_episodes(duplicate, [episodes[0], deepcopy(episodes[0])])
    assert not duplicate.exists()
    writes = []
    original = Path.write_bytes
    def record(path, payload):
        if path.parent.name == "public":
            writes.append(path.name)
        return original(path, payload)
    monkeypatch.setattr(Path, "write_bytes", record)
    output = tmp_path / "ordered"
    proto.write_episodes(output, episodes)
    assert len(writes) == 3
    assert writes == sorted(writes)
    for path in (output / "public").iterdir():
        assert path.name == f"challenge-{hashlib.sha256(path.read_bytes()).hexdigest()}.json"

@pytest.mark.parametrize("bad", [True, 1.0, 9])
def test_writer_rejects_nonexact_or_wrong_private_labels(tmp_path, bad):
    proto = load_prototype()
    episode = proto.build_claimed_episode(17, min_panel_count=2, demos=1, queries=1)
    episode["test"][0]["output"][0][0] = bad
    with pytest.raises(ValueError, match="label|binary"):
        proto.write_episodes(tmp_path / "bad", [episode])
    assert not (tmp_path / "bad").exists()

@pytest.fixture(scope="module")
def exported(tmp_path_factory):
    proto = load_prototype()
    output = tmp_path_factory.mktemp("reconciled-threshold") / "export"
    proto.materialize(output, seed=17, demos=1, queries=4)
    return proto, output

def _rehash(output):
    path = output / "manifest.json"
    manifest = json.loads(path.read_text())
    for row in manifest["files"]:
        body = (output / row["path"]).read_bytes()
        row["sha256"] = hashlib.sha256(body).hexdigest()
        row["bytes"] = len(body)
    path.write_text(json.dumps(manifest))

def test_current_export_replays_source_programs_labels_and_public_bytes(exported):
    proto, output = exported
    result = proto.verify_evidence(output)
    assert result["status"] == "pass"
    assert result["episodes_checked"] == 3
    assert result["query_labels_checked"] == 12
    assert result["racket_labels_checked"] >= 15

@pytest.mark.parametrize("attack", ["program", "label", "bool_label", "source", "extra_file", "public", "certificate"])
def test_verifier_rejects_rehashed_source_program_label_and_export_tampering(exported, tmp_path, attack):
    import shutil
    proto, source = exported
    output = tmp_path / attack
    shutil.copytree(source, output)
    if attack == "program":
        path = output / "private/program-threshold-1.rkt"
        path.write_text(path.read_text() + " ")
    elif attack in ("label", "bool_label", "certificate"):
        path = output / "private/episode-threshold-2.json"
        episode = json.loads(path.read_text())
        if attack == "label":
            episode["test"][0]["output"][0][0] ^= 1
        elif attack == "bool_label":
            episode["test"][0]["output"][0][0] = bool(episode["test"][0]["output"][0][0])
        else:
            episode["query_identification"][0]["consistent_settings"] = [1, 2]
        path.write_text(json.dumps(episode))
    elif attack == "source":
        path = output / "report.json"
        report = json.loads(path.read_text())
        report["source_sha256"]["prototype.py"] = "0" * 64
        path.write_text(json.dumps(report))
    elif attack == "extra_file":
        (output / "private/extra-answer.json").write_text("{}")
    elif attack == "public":
        path = next((output / "public").iterdir())
        path.write_bytes(path.read_bytes() + b" ")
    _rehash(output)
    with pytest.raises(ValueError, match="program|label|binary|source|inventory|public|certificate|metadata"):
        proto.verify_evidence(output)


def test_one_demo_threshold_one_refutes_constant_masks_and_keeps_profile_coverage():
    proto = load_prototype()
    gen, _, _ = load_selected_generator("a9c4475d7cda", root=ROOT)
    episode = proto.build_claimed_episode(17, min_panel_count=1, demos=1, queries=4)
    assert {value for row in episode["train"][0]["output"] for value in row} == {0, 1}
    profiles = {gen.observe_overrides(pair["input"])["count_profile"] for pair in episode["train"] + episode["test"]}
    assert profiles == set(gen.COUNT_PROFILES)
