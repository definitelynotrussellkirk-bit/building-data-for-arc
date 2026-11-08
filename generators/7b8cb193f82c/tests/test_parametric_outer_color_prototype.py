"""Focused tests for the separate outer-color rule prototype, not approval."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, canonical_path, find_root

TASK_ID = "7b8cb193f82c"
ROOT = find_root(__file__)
SOURCE = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"


def _load():
    assert SOURCE.is_file(), "outer-color prototype has not been implemented"
    spec = importlib.util.spec_from_file_location("outer_color_prototype", SOURCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def proto():
    return _load()


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge(timeout=15, startup_timeout=60) as value:
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
    assert proto.program_for(2, root=ROOT) == canonical
    assert hashlib.sha256(canonical.encode()).hexdigest() == proto.CANONICAL_TEXT_SHA256
    for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
        assert proto.execute_program(bridge, canonical, pair["input"]) == pair["output"]


def test_alternative_changes_only_the_outer_layer_colors_and_executes(proto, bridge):
    default = proto.program_for(2, root=ROOT)
    alternative = proto.program_for(3, root=ROOT)
    assert default.count("(if (odd? d) 2 3)") == 1
    assert alternative == default.replace("(if (odd? d) 2 3)", "(if (odd? d) 3 2)")
    grid = proto.episode_inputs(11)[0]
    assert proto.execute_program(bridge, default, grid) != proto.execute_program(bridge, alternative, grid)


def test_parameter_is_selected_once_and_both_settings_are_reachable(proto):
    selections = [proto.choose_outer_color(seed) for seed in range(32)]
    assert set(selections) == {2, 3}
    assert selections == [proto.choose_outer_color(seed) for seed in range(32)]
    with pytest.raises(ValueError):
        proto.choose_outer_color(True)
    with pytest.raises(ValueError):
        proto.choose_outer_color(-1)


@pytest.mark.parametrize("outer_color", [2, 3])
def test_complete_episode_has_racket_labels_and_demo_refutes_rival(proto, bridge, outer_color):
    episode = proto.build_episode(731, outer_color=outer_color, bridge=bridge, root=ROOT)
    assert episode["parameters"] == {"outer_color": outer_color}
    assert len(episode["train"]) == 3 and len(episode["test"]) == 1
    assert episode["rival"]["status"] == "refuted_by_demonstrations"
    assert episode["rival"]["differing_train_indices"]
    assert episode["rival"]["query_differs"] is True
    for pair in episode["train"] + episode["test"]:
        assert proto.execute_program(bridge, episode["program"], pair["input"]) == pair["output"]
    public = proto.public_challenge(episode)
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert "outer_color" not in json.dumps(public, sort_keys=True)


def test_materialization_retains_both_settings_and_hashes_files(proto, tmp_path):
    report = proto.materialize(tmp_path / "evidence", seed_start=731, root=ROOT)
    assert report["status"] == "passed"
    assert {item["parameters"]["outer_color"] for item in report["episodes"]} == {2, 3}
    manifest = json.loads((tmp_path / "evidence" / "manifest.json").read_text())
    for relative, expected in manifest["files"].items():
        actual = hashlib.sha256((tmp_path / "evidence" / relative).read_bytes()).hexdigest()
        assert actual == expected
    for item in report["episodes"]:
        public = json.loads((tmp_path / "evidence" / item["public_path"]).read_text())
        assert all(set(pair) == {"input"} for pair in public["test"])
