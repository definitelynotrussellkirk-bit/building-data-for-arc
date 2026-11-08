"""Focused tests for the proposed scan-order prototype, not canonical approval."""
from __future__ import annotations

from functools import lru_cache
import hashlib
import importlib.util
from pathlib import Path
import sys

import pytest

from reviewer_support import find_root


TASK_ID = "09d287bbfa0b"
ROOT = find_root(__file__)


@lru_cache(maxsize=1)
def prototype():
    path = ROOT / "generators" / TASK_ID / "workspace/parametric/prototype.py"
    assert path.is_file(), "the task-local scan-order prototype is not implemented"
    spec = importlib.util.spec_from_file_location("parametric_09d287bbfa0b", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_default_rule_is_exact_canonical_and_reverse_changes_only_scan_order():
    variant = prototype()
    assert variant.SCAN_ORDERS == ("row_major", "reverse_row_major")
    assert variant.DEFAULT_SCAN_ORDER == "row_major"
    canonical = variant.canonical_source(root=ROOT)
    assert hashlib.sha256(canonical.encode()).hexdigest() == variant.CANONICAL_PROGRAM_SHA256
    assert variant.materialize_rule(root=ROOT) == canonical
    assert variant.materialize_rule("row_major", root=ROOT) == canonical
    reverse = variant.materialize_rule("reverse_row_major", root=ROOT)
    assert reverse != canonical
    assert reverse.replace(variant.REVERSE_SCAN, variant.ROW_MAJOR_SCAN, 1) == canonical


@pytest.mark.parametrize("bad", [None, False, 1, "reverse", "ROW_MAJOR", "", []])
def test_rule_materialization_rejects_invalid_parameter_values(bad):
    variant = prototype()
    with pytest.raises(ValueError, match="scan_order"):
        variant.materialize_rule(bad, root=ROOT)


def test_exact_racket_default_replays_canonical_and_reverse_is_distinguishable():
    from arc_repl.racket_bridge import RacketBridge
    from reviewer_support import canonical_pairs, load_selected_generator

    variant = prototype()
    generator, _source, _digest = load_selected_generator(TASK_ID, root=ROOT)
    default_rule = variant.materialize_rule(root=ROOT)
    reverse_rule = variant.materialize_rule("reverse_row_major", root=ROOT)
    witness = generator.generate(
        719,
        1,
        difficulty="medium",
        texture="multi_quadrant",
        n_pixels=8,
    )
    with RacketBridge() as bridge:
        for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
            assert variant.execute_rule(default_rule, pair["input"], bridge=bridge) == pair["output"]
        default_output = variant.execute_rule(default_rule, witness, bridge=bridge)
        reverse_output = variant.execute_rule(reverse_rule, witness, bridge=bridge)
    assert default_output != reverse_output


def test_scan_order_choice_is_episode_scoped_deterministic_and_rng_isolated():
    import random

    variant = prototype()
    random.seed(46091)
    state = random.getstate()
    observed = {variant.choose_scan_order(seed) for seed in (0, 1)}
    assert observed == set(variant.SCAN_ORDERS)
    assert variant.choose_scan_order(0) == variant.choose_scan_order(0)
    assert random.getstate() == state


@pytest.mark.parametrize("bad", [None, False, -1, 2**63, 1.5, "0"])
def test_scan_order_choice_rejects_invalid_seed(bad):
    variant = prototype()
    with pytest.raises(ValueError, match="seed"):
        variant.choose_scan_order(bad)


def test_complete_episodes_are_identifiable_and_public_challenges_do_not_leak():
    import json
    from arc_repl.racket_bridge import RacketBridge

    variant = prototype()
    episodes = []
    with RacketBridge() as bridge:
        for seed in (0, 1):
            episode = variant.generate_episode(
                seed,
                root=ROOT,
                difficulty="medium",
                start=0,
                bridge=bridge,
            )
            episodes.append(episode)
            challenge = episode["challenge"]
            private = episode["private"]
            selected = private["parameters"]["scan_order"]
            assert selected == variant.choose_scan_order(seed)
            assert len(challenge["train"]) == 3
            assert challenge["test"] and set(challenge["test"][0]) == {"input"}
            public_text = json.dumps(challenge, sort_keys=True)
            for forbidden in (
                "scan_order",
                "reference_rule",
                "query_answers",
                "parameter_rivals",
                "reverse_row_major",
                "row_major",
            ):
                assert forbidden not in public_text
            assert private["identifiable_against_parameter_rivals"] is True
            assert private["parameter_rivals"][selected]["status"] == "selected"
            for order, rival in private["parameter_rivals"].items():
                if order != selected:
                    assert rival["status"] == "eliminated_by_demonstrations"
                    assert rival["demo_disagreements"] == [0, 1, 2]
                    assert rival["query_disagreements"] == [0]
            selected_rule = variant.materialize_rule(selected, root=ROOT)
            for pair in challenge["train"]:
                assert variant.execute_rule(selected_rule, pair["input"], bridge=bridge) == pair["output"]
            assert variant.execute_rule(
                selected_rule,
                challenge["test"][0]["input"],
                bridge=bridge,
            ) == private["query_answers"][0]["output"]
    assert {e["private"]["parameters"]["scan_order"] for e in episodes} == set(
        variant.SCAN_ORDERS
    )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"difficulty": None},
        {"difficulty": "MEDIUM"},
        {"start": -1},
        {"start": 1.5},
    ],
)
def test_episode_rejects_invalid_controls(kwargs):
    variant = prototype()
    with pytest.raises(ValueError):
        variant.generate_episode(0, root=ROOT, **kwargs)


def test_retained_evidence_is_replayable_hash_bound_and_public_private_split(tmp_path):
    import json

    variant = prototype()
    out = tmp_path / "evidence"
    report = variant.retain_evidence(
        [0, 1],
        out,
        root=ROOT,
        difficulty="medium",
        start=0,
    )
    assert report["status"] == "bounded_checks_passed"
    assert report["settings_observed"] == sorted(variant.SCAN_ORDERS)
    assert report["canonical_replay"]["failed"] == 0
    assert report["canonical_replay"]["pairs"] >= 1
    assert report["distinguishing_witness"]["outputs_differ"] is True
    assert (out / "private/report.json").is_file()
    assert (out / "private/canonical_replay.json").is_file()
    assert (out / "private/distinguishing_witness.json").is_file()
    for order in variant.SCAN_ORDERS:
        rule_path = out / "private/rules" / f"scan-{order}.rkt"
        assert rule_path.read_text(encoding="utf-8") == variant.materialize_rule(order, root=ROOT)
    for index in range(2):
        public_path = out / "public" / f"episode-{index:03d}.json"
        private_path = out / "private" / f"episode-{index:03d}.json"
        public = json.loads(public_path.read_text(encoding="utf-8"))
        private = json.loads(private_path.read_text(encoding="utf-8"))
        assert set(public) == {"train", "test"}
        assert set(public["test"][0]) == {"input"}
        public_text = public_path.read_text(encoding="utf-8")
        assert private["parameters"]["scan_order"] not in public_text
        assert "query_answers" not in public_text
        assert private["public_file_sha256"] == variant.sha256(public_path.read_bytes())
        assert private["identifiable_against_parameter_rivals"] is True
    for name in (
        "prototype.py",
        "generator.py",
        "test_parametric_scan_order.py",
        "README.md",
    ):
        assert (out / "private/source_snapshot" / name).is_file()

    occupied = tmp_path / "occupied"
    occupied.mkdir()
    (occupied / "keep.txt").write_text("do not mix\n", encoding="utf-8")
    with pytest.raises(ValueError, match="new or empty"):
        variant.retain_evidence([0, 1], occupied, root=ROOT)
