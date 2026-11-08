"""Racket-backed tests for the proposed shape-equivalence parameter."""
from __future__ import annotations

from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root

TASK_ID = "ae0a295c2271"
ROOT = find_root(__file__)
PROTOTYPE_PATH = (
    ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
)


@lru_cache(maxsize=1)
def prototype():
    assert PROTOTYPE_PATH.is_file(), "shape-equivalence prototype is not implemented"
    spec = importlib.util.spec_from_file_location(
        "ae0a295c2271_shape_equivalence_prototype", PROTOTYPE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge(max_calls_before_restart=128) as instance:
        yield instance


def test_default_program_is_exact_canonical_and_parameter_is_strict():
    p = prototype()
    assert p.PARAMETER_NAME == "shape_equivalence"
    assert p.ALLOWED_VALUES == ("exact", "d4")
    assert p.DEFAULT_VALUE == "exact"
    assert p.program_for("exact", root=ROOT) == p.canonical_program(root=ROOT)
    assert p.program_for("d4", root=ROOT) != p.canonical_program(root=ROOT)
    for invalid in (None, True, 0, 1.0, "rotation", "EXACT"):
        with pytest.raises(ValueError, match="shape_equivalence"):
            p.program_for(invalid, root=ROOT)


def test_default_program_matches_all_canonical_labels(bridge):
    p = prototype()
    program = p.program_for("exact", root=ROOT)
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) >= 3
    for pair in pairs:
        assert p.evaluate(bridge, program, pair["input"]) == pair["output"]


def test_one_lawful_input_distinguishes_executed_settings(bridge):
    p = prototype()
    grid = p.generate_inputs(27, root=ROOT)[0]
    exact = p.evaluate(bridge, p.program_for("exact", root=ROOT), grid)
    d4 = p.evaluate(bridge, p.program_for("d4", root=ROOT), grid)
    assert exact != d4
    assert exact == p.python_apply(grid, "exact", root=ROOT)
    assert d4 == p.python_apply(grid, "d4", root=ROOT)


@pytest.mark.parametrize("setting", ["exact", "d4"])
def test_episode_binds_one_setting_and_refutes_rival_for_every_query_rotation(
    bridge, setting
):
    p = prototype()
    episode = p.make_episode(bridge, seed=41, shape_equivalence=setting, root=ROOT)
    assert episode["parameters"] == {"shape_equivalence": setting}
    assert len(episode["pairs"]) == 4
    assert len({json.dumps(pair["input"]) for pair in episode["pairs"]}) == 4
    analysis = p.assess_episode(bridge, episode, root=ROOT)
    assert analysis["production"]["status"] == "refuted_by_demonstrations"
    assert [row["query_index"] for row in analysis["rotations"]] == [0, 1, 2, 3]
    for row in [analysis["production"], *analysis["rotations"]]:
        assert row["rival_fits_demonstrations"] is False
        assert row["rival_query_differs"] is True
        assert row["refuting_demonstration_indices"] == row["demonstration_indices"]


def test_public_projection_hides_parameter_program_and_query_answer(bridge):
    p = prototype()
    episode = p.make_episode(bridge, seed=8, shape_equivalence="exact", root=ROOT)
    public = p.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert len(public["train"]) == 3
    assert len(public["test"]) == 1
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert set(public["test"][0]) == {"input"}
    dumped = json.dumps(public).lower()
    assert "shape_equivalence" not in dumped
    assert "racket" not in dumped
    public["test"][0]["input"][0][0] = 99
    assert episode["pairs"][3]["input"][0][0] != 99


def test_materialized_tree_is_hash_bound_and_public_files_are_clean(bridge, tmp_path):
    p = prototype()
    out = tmp_path / "shape-equivalence"
    report = p.materialize(out, bridge=bridge, root=ROOT)
    assert report["status"] == "proposed_prototype"
    assert report["counts"] == {
        "canonical_labels_checked": len(canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)),
        "canonical_labels_passed": len(canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)),
        "settings": 2,
        "episodes": 2,
        "episode_labels": 8,
        "production_ambiguities": 0,
        "rotation_ambiguities": 0,
        "query_rotations": 8,
    }
    assert p.verify_tree(out, bridge=bridge, root=ROOT)["status"] == "pass"
    for record in report["settings"]:
        rule = out / record["rule_path"]
        private = out / record["private_path"]
        public = out / record["public_path"]
        assert hashlib.sha256(rule.read_bytes()).hexdigest() == record["rule_sha256"]
        assert hashlib.sha256(private.read_bytes()).hexdigest() == record["private_sha256"]
        assert hashlib.sha256(public.read_bytes()).hexdigest() == record["public_sha256"]
        challenge = json.loads(public.read_text())
        assert set(challenge["test"][0]) == {"input"}
        assert "shape_equivalence" not in public.read_text()
    with pytest.raises(FileExistsError):
        p.materialize(out, bridge=bridge, root=ROOT)
