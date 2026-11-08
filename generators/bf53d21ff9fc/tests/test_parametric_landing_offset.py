"""Focused tests for the task-local landing-offset prototype."""
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

import pytest

from reviewer_support import find_root


TASK = "bf53d21ff9fc"
ROOT = find_root(__file__)
PROTOTYPE = ROOT / f"generators/{TASK}/workspace/parametric/prototype.py"


def load_prototype():
    assert PROTOTYPE.is_file(), "The runnable task-local landing-offset prototype is missing"
    spec = importlib.util.spec_from_file_location(f"{TASK}_landing_offset", PROTOTYPE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_materialization_preserves_exact_default_and_changes_only_declared_offset():
    prototype = load_prototype()
    canonical = prototype.canonical_source(ROOT)
    default = prototype.materialize_program(canonical, 2)
    alternate = prototype.materialize_program(canonical, 3)
    assert default == canonical
    assert alternate != canonical
    assert canonical.count(prototype.LANDING_EXPRESSION) == 1
    assert alternate.count("(- (length trail) 3)") == 1
    for invalid in (True, 2.0, "2", 0, 1, 4, None):
        with pytest.raises(ValueError, match="landing_offset"):
            prototype.materialize_program(canonical, invalid)


def test_seeded_episodes_choose_once_cover_both_settings_and_keep_routes_long_enough():
    prototype = load_prototype()
    episodes = [prototype.episode_inputs(seed, root=ROOT) for seed in (0, 1)]
    assert {episode["parameters"]["landing_offset"] for episode in episodes} == {2, 3}
    for seed, episode in zip((0, 1), episodes):
        assert episode == prototype.episode_inputs(seed, root=ROOT)
        assert len(episode["inputs"]) == 4
        assert len({json.dumps(grid) for grid in episode["inputs"]}) == 4
        assert all(item["minimum_active_route_length"] >= 3 for item in episode["construction"])
        assert all(item["self_check"] == [] for item in episode["construction"])


def test_real_racket_evidence_preserves_canonical_parity_and_keeps_query_answers_private():
    prototype = load_prototype()
    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parametric-") as temp:
        evidence = Path(temp) / "landing-offset"
        report = prototype.write_evidence(evidence, seeds=(0, 1), root=ROOT)
        assert report["status"] == "prototype_passed"
        assert report["canonical_parity"] == {
            "passed": True,
            "labeled_pairs": 4,
            "path": "private/canonical-parity.json",
        }
        assert report["settings_covered"] == [2, 3]
        assert report["missing_episode_settings"] == []
        assert report["settings_witness"]["outputs_differ"] is True
        assert report["racket_evaluation_count"] == 26

        programs = {
            int(path.stem.rsplit("-", 1)[1]): path.read_text(encoding="utf-8")
            for path in (evidence / "private/programs").glob("landing-offset-*.rkt")
        }
        assert programs[2] == prototype.canonical_source(ROOT)
        assert programs[3] != programs[2]

        for row in report["episodes"]:
            public = json.loads((evidence / row["public_path"]).read_text())
            private = json.loads((evidence / row["private_path"]).read_text())
            assert set(public) == {"train", "test"}
            assert len(public["train"]) == 3 and len(public["test"]) == 1
            assert all(set(pair) == {"input", "output"} for pair in public["train"])
            assert all(set(pair) == {"input"} for pair in public["test"])
            assert "output" not in public["test"][0]
            chosen = private["parameters"]["landing_offset"]
            assert len(private["test_outputs"]) == 1
            assert private["rivals"][str(chosen)]["status"] == "survived_all"
            rival = 3 if chosen == 2 else 2
            assert private["rivals"][str(rival)]["status"] == "refuted_by_demonstrations"
            assert private["rivals"][str(rival)]["demonstration_mismatch_indices"] == [0, 1, 2]
            assert private["declared_parameter_ambiguity"] is False

        before = {path.relative_to(evidence): path.read_bytes()
                  for path in evidence.rglob("*") if path.is_file()}
        with pytest.raises(FileExistsError):
            prototype.write_evidence(evidence, seeds=(0, 1), root=ROOT)
        after = {path.relative_to(evidence): path.read_bytes()
                 for path in evidence.rglob("*") if path.is_file()}
        assert after == before
