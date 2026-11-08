"""Focused tests for the separate projection-polarity rule prototype."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, canonical_path, find_root

TASK_ID = "e937c5b85cdd"
ROOT = find_root(__file__)
SOURCE = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"


def _load_prototype():
    assert SOURCE.is_file(), "projection-polarity prototype has not been implemented"
    spec = importlib.util.spec_from_file_location("projection_polarity_prototype", SOURCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def proto():
    return _load_prototype()


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge(timeout=30, startup_timeout=60, max_calls_before_restart=128) as value:
        yield value


def _canonical_text() -> str:
    sources = set()
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                sources.add(row["program_solution"])
    assert len(sources) == 1
    return sources.pop()


def test_default_program_is_exact_canonical_and_executes_labels(proto, bridge):
    canonical = _canonical_text()
    assert proto.program_for("opposite", root=ROOT) == canonical
    assert hashlib.sha256(canonical.encode()).hexdigest() == proto.CANONICAL_TEXT_SHA256
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    outputs = proto.execute_outputs(bridge, canonical, [pair["input"] for pair in pairs])
    assert outputs == [pair["output"] for pair in pairs]


def test_alternative_changes_only_the_projection_polarity(proto, bridge):
    canonical = proto.program_for("opposite", root=ROOT)
    facing = proto.program_for("facing", root=ROOT)
    assert canonical.count(proto._CANONICAL_ACTIONS) == 1
    assert facing == canonical.replace(proto._CANONICAL_ACTIONS, proto._FACING_ACTIONS)
    witness = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)[0]["input"]
    opposite_output = proto.execute_outputs(bridge, canonical, [witness])[0]
    facing_output = proto.execute_outputs(bridge, facing, [witness])[0]
    assert opposite_output != facing_output


def test_parameter_is_selected_once_and_both_settings_are_reachable(proto):
    choices = [proto.choose_projection_polarity(seed) for seed in range(32)]
    assert set(choices) == {"opposite", "facing"}
    assert choices == [proto.choose_projection_polarity(seed) for seed in range(32)]
    for invalid in (True, -1, 1.5, "1", None):
        with pytest.raises(ValueError, match="seed"):
            proto.choose_projection_polarity(invalid)


@pytest.mark.parametrize("projection_polarity", ["opposite", "facing"])
def test_complete_episode_has_racket_labels_and_demo_refutes_rival(
    proto, bridge, projection_polarity
):
    episode = proto.build_episode(
        731,
        projection_polarity=projection_polarity,
        bridge=bridge,
        root=ROOT,
    )
    assert episode["parameters"] == {"projection_polarity": projection_polarity}
    assert len(episode["train"]) == 3 and len(episode["test"]) == 1
    assert episode["rival"]["status"] == "refuted_by_demonstrations"
    assert episode["rival"]["differing_train_indices"]
    assert episode["rival"]["query_differs"] is True
    outputs = proto.execute_outputs(
        bridge,
        episode["program"],
        [pair["input"] for pair in episode["train"] + episode["test"]],
    )
    assert outputs == [pair["output"] for pair in episode["train"] + episode["test"]]
    public = proto.public_challenge(episode)
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    public_text = json.dumps(public, sort_keys=True)
    assert "projection_polarity" not in public_text
    assert "program" not in public_text
    assert "seed" not in public_text


def test_materialization_retains_both_settings_and_hashes_files(proto, tmp_path):
    report = proto.materialize(tmp_path / "evidence", seed_start=731, root=ROOT)
    assert report["status"] == "passed"
    assert {
        item["parameters"]["projection_polarity"] for item in report["episodes"]
    } == {"opposite", "facing"}
    manifest = json.loads((tmp_path / "evidence" / "manifest.json").read_text())
    for relative, expected in manifest["files"].items():
        actual = hashlib.sha256((tmp_path / "evidence" / relative).read_bytes()).hexdigest()
        assert actual == expected
    for item in report["episodes"]:
        public = json.loads((tmp_path / "evidence" / item["public_path"]).read_text())
        assert all(set(pair) == {"input"} for pair in public["test"])
