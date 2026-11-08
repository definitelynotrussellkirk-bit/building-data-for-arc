"""Regression tests for the retained metric rules and v2 episode writer."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import racket_runtime_status
from reviewer_support import find_root


ROOT = find_root(__file__)
PROTOTYPE_PATH = (
    ROOT
    / "generators/e07bbcbe6ba4/workspace/parametric/prototype.py"
)


def _load_prototype():
    assert PROTOTYPE_PATH.exists(), "distance-metric prototype has not been built"
    spec = importlib.util.spec_from_file_location(
        "e07bbcbe6ba4_parametric_prototype", PROTOTYPE_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _require_racket():
    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])


def test_default_rule_is_exact_canonical_and_alternative_is_one_guarded_edit():
    prototype = _load_prototype()
    canonical = prototype.canonical_source(root=ROOT)
    assert hashlib.sha256(canonical.encode()).hexdigest() == prototype.CANONICAL_SHA256
    assert prototype.materialize_rule("chebyshev", root=ROOT) == canonical
    manhattan = prototype.materialize_rule("manhattan", root=ROOT)
    assert manhattan != canonical
    assert prototype.CHEBYSHEV_SITE not in manhattan
    assert manhattan.count(prototype.MANHATTAN_SITE) == 1
    assert prototype.materialize_rule("chebyshev", source=canonical) == canonical


def test_actual_racket_rules_disagree_on_an_authored_lawful_input():
    _require_racket()
    prototype = _load_prototype()
    grid = prototype.fixtures()[0]["input"]
    chebyshev = prototype.execute_rule(
        prototype.materialize_rule("chebyshev", root=ROOT), grid
    )
    manhattan = prototype.execute_rule(
        prototype.materialize_rule("manhattan", root=ROOT), grid
    )
    assert chebyshev != manhattan


@pytest.mark.parametrize("metric", ["chebyshev", "manhattan"])
def test_one_seed_level_parameter_is_shared_and_identified_by_demonstrations(metric):
    _require_racket()
    prototype = _load_prototype()
    seed = prototype.first_seed_for_metric(metric)
    episode = prototype.make_episode(seed, root=ROOT)
    assert episode["parameters"] == {"distance_metric": metric, "origin_mode": "marker"}
    assert episode["selected_rule_sha256"] == hashlib.sha256(
        prototype.materialize_rule(metric, root=ROOT).encode()).hexdigest()
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 4
    assert episode["identifiability"]["passed"] is True
    assert episode["identifiability"]["distinguishing_demo_indices"]
    other = ({"chebyshev", "manhattan"} - {metric}).pop()
    assert episode["identifiability"]["rivals"]["setting:" + other + "-marker"]["refuted_by_demo"] is True
    assert all(pair["distance_metric"] == metric for pair in episode["private_pairs"])


def test_public_challenge_omits_hidden_rule_and_query_answer():
    _require_racket()
    prototype = _load_prototype()
    episode = prototype.make_episode(
        prototype.first_seed_for_metric("manhattan"), root=ROOT
    )
    public = prototype.public_challenge(episode)
    payload = json.dumps(public, sort_keys=True)
    assert "distance_metric" not in payload
    assert "rule" not in payload.lower()
    assert all("output" in pair for pair in public["train"])
    assert "output" not in public["test"][0]


def test_evidence_writer_records_four_settings_and_opaque_single_query_files(tmp_path):
    _require_racket()
    prototype = _load_prototype()
    out = tmp_path / "distance-metric"
    report = prototype.write_evidence(out=out, root=ROOT)
    assert report["status"] == "prototype"
    assert {row["distance_metric"] for row in report["episodes"]} == {
        "chebyshev",
        "manhattan",
    }
    hashes = {row["racket_sha256"] for row in report["episodes"]}
    assert len(report["episodes"]) == len(hashes) == 4
    assert report["canonical_default"]["all_labeled_pairs_match"] is True
    assert report["distinguishing_witness"]["outputs_differ"] is True
    for row in report["files"]:
        path = out / row["path"]
        assert path.exists()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"]
        if row["path"].startswith("public/"):
            assert path.stem == row["sha256"]
            visible = json.loads(path.read_bytes())
            assert set(visible) == {"train", "test"}
            assert len(visible["train"]) == 3 and len(visible["test"]) == 1
            assert set(visible["test"][0]) == {"input"}
    assert len(list((out / "public").glob("*.json"))) == 16
    assert report["bounded_yield"]["succeeded"] == report["bounded_yield"]["attempted"] == 12
    with pytest.raises(FileExistsError):
        prototype.write_evidence(out=out, root=ROOT)
