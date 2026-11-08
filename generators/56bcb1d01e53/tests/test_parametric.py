"""Focused checks for the proposed square-closure parameter prototype."""
from __future__ import annotations

from functools import cache
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "56bcb1d01e53"
ROOT = find_root(__file__)
PROTOTYPE_PATH = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"


@cache
def prototype():
    assert PROTOTYPE_PATH.is_file(), "square-closure parametric prototype is not implemented"
    spec = importlib.util.spec_from_file_location("icon_symmetry_parametric", PROTOTYPE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_program_is_exact_canonical_and_modes_are_bounded():
    p = prototype()
    canonical = p.canonical_record(root=ROOT)["program_solution"]
    assert p.program_for("rotation", root=ROOT) == canonical
    assert p.program_for("dihedral", root=ROOT) != canonical
    assert p.MODES == ("rotation", "dihedral")
    assert p.DEFAULT_MODE == "rotation"
    for invalid in ("reflection", "", 0, True, None):
        with pytest.raises(ValueError, match="square_closure"):
            p.program_for(invalid, root=ROOT)


def test_programs_execute_with_racket_and_default_matches_all_canonical_pairs():
    p = prototype()
    from arc_repl.racket_bridge import RacketBridge

    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 5
    with RacketBridge() as bridge:
        for pair in pairs:
            assert p.execute(bridge, p.program_for("rotation", root=ROOT), pair["input"]) == pair["output"]
        witness = p.shared_witness(seed=0)
        rotation = p.execute(bridge, p.program_for("rotation", root=ROOT), witness)
        dihedral = p.execute(bridge, p.program_for("dihedral", root=ROOT), witness)
    assert rotation != dihedral


@pytest.mark.parametrize("seed,expected", [(0, "rotation"), (1, "dihedral"), (8, "rotation"), (9, "dihedral")])
def test_episode_selects_mode_once_and_demonstrations_identify_it(seed, expected):
    p = prototype()
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge(max_calls_before_restart=128) as bridge:
        public, private = p.generate_episode(seed, bridge, root=ROOT)
        public_again, private_again = p.generate_episode(seed, bridge, root=ROOT)
    assert public == public_again
    assert private == private_again
    assert private["parameter"] == {"square_closure": expected}
    assert len(public["train"]) == 2
    assert len(public["test"]) == 1
    assert set(public["test"][0]) == {"input"}
    assert private["rival_checks"][expected]["matches_all_demonstrations"]
    rival = "dihedral" if expected == "rotation" else "rotation"
    assert not private["rival_checks"][rival]["matches_all_demonstrations"]
    assert private["rival_checks"][rival]["distinguishing_demo_indices"] == [0, 1]
    assert len(private["query_answers"]) == 1


def test_materialized_evidence_keeps_hidden_mode_and_query_answers_private(tmp_path):
    p = prototype()
    manifest = p.write_evidence(tmp_path, seeds=[0, 1], root=ROOT)
    assert manifest["status"] == p.STATUS
    assert manifest["parameter"] == {
        "name": "square_closure",
        "allowed": ["rotation", "dihedral"],
        "default": "rotation",
    }
    assert manifest["canonical_default_unchanged"] is True
    assert set(manifest["program_sha256"]) == {"rotation", "dihedral"}
    for path in (tmp_path / "public").glob("episode-*.json"):
        data = json.loads(path.read_text())
        assert set(data) == {"train", "test"}
        assert set(data["test"][0]) == {"input"}
        text = path.read_text()
        assert "query_answers" not in text
        assert "square_closure" not in text
