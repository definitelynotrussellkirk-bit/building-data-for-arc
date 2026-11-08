"""Focused Racket-backed checks for the proposed positive-state prototype."""
from __future__ import annotations

from functools import lru_cache
import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root

TASK_ID = "784b131b3b93"
ROOT = find_root(__file__)
PROTOTYPE_PATH = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"


@lru_cache(maxsize=1)
def prototype():
    assert PROTOTYPE_PATH.is_file(), "positive-state parametric prototype is not implemented"
    spec = importlib.util.spec_from_file_location("arc784_positive_state_prototype", PROTOTYPE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge(max_calls_before_restart=128) as instance:
        yield instance


def test_default_program_is_exact_canonical_and_parameter_is_strict():
    p = prototype()
    canonical = p.canonical_program(root=ROOT)
    assert p.render_program("both_zero", root=ROOT) == canonical
    assert p.render_program("both_nonzero", root=ROOT) != canonical
    for invalid in (None, True, 0, "zero", "both-zero"):
        with pytest.raises(ValueError, match="positive_state"):
            p.render_program(invalid, root=ROOT)


def test_default_program_matches_every_canonical_label(bridge):
    p = prototype()
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 5
    source = p.render_program("both_zero", root=ROOT)
    for pair in pairs:
        assert p.execute(bridge, source, pair["input"]) == pair["output"]


def test_shared_lawful_witness_distinguishes_both_settings(bridge):
    p = prototype()
    witness = p.distinguishing_witness()
    zero_output = p.execute(bridge, p.render_program("both_zero", root=ROOT), witness)
    nonzero_output = p.execute(bridge, p.render_program("both_nonzero", root=ROOT), witness)
    assert zero_output != nonzero_output
    assert any(5 in row for row in zero_output)
    assert any(5 in row for row in nonzero_output)


@pytest.mark.parametrize("seed", [0, 1, 7, 19])
def test_episode_selects_parameter_once_and_demos_refute_the_rival(bridge, seed):
    p = prototype()
    public, private = p.generate_episode(seed, bridge=bridge, root=ROOT)
    public_again, private_again = p.generate_episode(seed, bridge=bridge, root=ROOT)
    assert public == public_again
    assert private == private_again
    assert private["parameters"]["positive_state"] in p.ALLOWED_STATES
    assert len(public["train"]) == 3
    assert len(public["test"]) == 1
    assert set(public["test"][0]) == {"input"}
    rival = private["parameter_rival"]
    assert rival["status"] == "refuted_on_demonstrations"
    assert rival["refuting_demonstration_indices"] == [0, 1, 2]
    assert rival["query_differs"] is True


def test_input_schedule_is_independent_of_selected_parameter(bridge):
    p = prototype()
    first_public, _ = p.generate_episode(37, bridge=bridge, root=ROOT, positive_state="both_zero")
    second_public, _ = p.generate_episode(37, bridge=bridge, root=ROOT, positive_state="both_nonzero")
    assert [pair["input"] for pair in first_public["train"]] == [
        pair["input"] for pair in second_public["train"]
    ]
    assert first_public["test"][0]["input"] == second_public["test"][0]["input"]
    assert [pair["output"] for pair in first_public["train"]] != [
        pair["output"] for pair in second_public["train"]
    ]


def test_materialized_evidence_separates_public_and_private_data(bridge, tmp_path):
    p = prototype()
    out = tmp_path / "evidence"
    report = p.write_evidence(out, seeds=[0, 2], bridge=bridge, root=ROOT)
    assert report["status"] == "proposed_prototype"
    assert report["counts"]["episodes"] == 2
    assert report["counts"]["canonical_labels_checked"] == 5
    assert report["counts"]["settings_exercised"] == 2
    assert report["counts"]["ambiguous_parameter_rivals"] == 0
    for path in (out / "public").glob("episode-*.json"):
        value = json.loads(path.read_text())
        assert set(value) == {"train", "test"}
        assert set(value["test"][0]) == {"input"}
        text = path.read_text()
        assert "positive_state" not in text
        assert '"output"' not in json.dumps(value["test"])
    for state in p.ALLOWED_STATES:
        rule_path = out / "private" / "rules" / f"positive-state-{state}.rkt"
        assert rule_path.read_text() == p.render_program(state, root=ROOT)
