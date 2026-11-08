"""Focused tests for the proposed, unapproved selection-metric prototype."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

ROOT = find_root(__file__)
PROTOTYPE_PATH = ROOT / "generators/e521d16d403e/workspace/parametric/prototype.py"


def _load_prototype():
    spec = importlib.util.spec_from_file_location("parametric_e521d16d403e", PROTOTYPE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_source() -> str:
    import json
    sources = {
        row["program_solution"]
        for line in canonical_path(ROOT).read_text().splitlines()
        if line.strip()
        if (row := json.loads(line)).get("task_id") == "e521d16d403e"
    }
    assert len(sources) == 1
    return sources.pop()


def test_default_materialization_is_exact_canonical_and_alternative_is_guarded():
    prototype = _load_prototype()
    canonical = _canonical_source()
    materialize = getattr(prototype, "materialize_rule", None)
    assert callable(materialize), "prototype must expose materialize_rule"
    assert materialize("occupied_cells", root=ROOT) == canonical
    alternative = materialize("bbox_area", root=ROOT)
    assert alternative != canonical
    assert prototype.restore_canonical(alternative) == canonical
    assert hashlib.sha256(canonical.encode()).hexdigest() == prototype.CANONICAL_SOURCE_SHA256


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge() as runtime:
        yield runtime


def test_default_setting_reproduces_every_labeled_canonical_pair(bridge):
    prototype = _load_prototype()
    execute = getattr(prototype, "execute_rule", None)
    assert callable(execute), "prototype must execute exact Racket"
    source = prototype.materialize_rule("occupied_cells", root=ROOT)
    pairs = canonical_pairs(prototype.TASK_ID, root=ROOT, labeled_only=True)
    assert pairs
    for pair in pairs:
        assert execute(source, pair["input"], bridge=bridge) == pair["output"]


def test_authored_inputs_distinguish_occupied_cells_from_bbox_area(bridge):
    prototype = _load_prototype()
    fixtures = getattr(prototype, "fixtures", None)
    assert callable(fixtures), "prototype must expose lawful authored fixtures"
    occupied = prototype.materialize_rule("occupied_cells", root=ROOT)
    area = prototype.materialize_rule("bbox_area", root=ROOT)
    rows = fixtures()
    assert len(rows) == 4
    for row in rows:
        generator, _source, _digest = load_selected_generator("e521d16d403e", root=ROOT)
        assert generator.self_check(row["input"]) == [], row["fixture_id"]
        occupied_output = prototype.execute_rule(occupied, row["input"], bridge=bridge)
        area_output = prototype.execute_rule(area, row["input"], bridge=bridge)
        assert occupied_output != area_output, row["fixture_id"]


@pytest.mark.parametrize("value", [True, 1, "size", None])
def test_invalid_selection_metric_is_rejected(value):
    prototype = _load_prototype()
    with pytest.raises(ValueError):
        prototype.materialize_rule(value, root=ROOT)


def test_episode_selects_parameter_once_and_refutes_the_other_setting(bridge):
    prototype = _load_prototype()
    make_episode = getattr(prototype, "make_episode", None)
    assert callable(make_episode), "prototype must build complete episodes"
    area_episode = make_episode(0, root=ROOT, bridge=bridge)
    occupied_episode = make_episode(1, root=ROOT, bridge=bridge)
    assert area_episode["parameters"] == {"selection_metric": "bbox_area"}
    assert occupied_episode["parameters"] == {"selection_metric": "occupied_cells"}
    for episode in (area_episode, occupied_episode):
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 1
        assert episode["ambiguities"] == []
        matching = [row for row in episode["parameter_rivals"] if row["status"] == "matches_episode"]
        refuted = [row for row in episode["parameter_rivals"] if row["status"] == "refuted_by_demonstrations"]
        assert [row["selection_metric"] for row in matching] == [episode["parameters"]["selection_metric"]]
        assert len(refuted) == 1
        assert refuted[0]["demonstration_mismatch_indices"] == [0, 1, 2]
        assert refuted[0]["query_mismatch_indices"] == [0]


def test_public_challenge_omits_hidden_setting_source_and_query_answer(bridge):
    prototype = _load_prototype()
    episode = prototype.make_episode(0, root=ROOT, bridge=bridge)
    public = prototype.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    serialized = json.dumps(public)
    for forbidden in ("selection_metric", "racket", "seed", "parameter"):
        assert forbidden not in serialized


def test_evidence_writer_materializes_both_settings_and_hashes_files(tmp_path):
    prototype = _load_prototype()
    write_evidence = getattr(prototype, "write_evidence", None)
    assert callable(write_evidence), "prototype must retain executable evidence"
    out = tmp_path / "selection-metric"
    report = write_evidence((0, 1), out=out, root=ROOT)
    assert report["status"] == "proposed_unapproved"
    assert report["counts"]["episodes"] == 2
    assert report["counts"]["settings_exercised"] == 2
    assert report["counts"]["ambiguous_parameter_rivals"] == 0
    for episode in report["episodes"]:
        public = json.loads((out / episode["public_path"]).read_text())
        private = json.loads((out / episode["private_path"]).read_text())
        assert public == prototype.public_challenge(private)
        assert "output" not in public["test"][0]
        assert "output" in private["test"][0]
    for row in report["files"]:
        assert hashlib.sha256((out / row["path"]).read_bytes()).hexdigest() == row["sha256"]
