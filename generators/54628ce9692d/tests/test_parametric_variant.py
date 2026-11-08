"""Focused tests for the unapproved docking-distance prototype."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil

import pytest

from reviewer_support import canonical_path, find_root


TASK_ID = "54628ce9692d"
ROOT = find_root(__file__)
PROTOTYPE_PATH = (
    Path(__file__).resolve().parents[1]
    / "workspace"
    / "parametric"
    / "prototype.py"
)


def _load_prototype():
    spec = importlib.util.spec_from_file_location(
        "review_54628ce9692d_parametric", PROTOTYPE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_source() -> str:
    sources = {
        row["program_solution"]
        for row in (
            json.loads(line)
            for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
        if row.get("task_id") == TASK_ID
    }
    assert len(sources) == 1
    return sources.pop()


def test_materialized_default_is_exact_canonical_and_alternative_is_guarded():
    prototype = _load_prototype()
    canonical = _canonical_source()
    default = prototype.materialize_rule(1, root=ROOT)
    alternative = prototype.materialize_rule(2, root=ROOT)

    assert prototype.ALLOWED_DOCKING_DISTANCES == (1, 2)
    assert prototype.DEFAULT_DOCKING_DISTANCE == 1
    assert default == canonical
    assert alternative != canonical
    assert alternative.count(prototype.ALTERNATIVE_ROW_STEP) == 1
    assert alternative.count(prototype.ALTERNATIVE_COL_STEP) == 1
    assert prototype.restore_canonical_rule(alternative) == canonical


def test_parameter_is_selected_once_and_known_seeds_cover_both_settings():
    prototype = _load_prototype()
    assert prototype.parameters_for_seed(0) == {"docking_distance": 2}
    assert prototype.parameters_for_seed(1) == {"docking_distance": 1}
    for bad in (True, -1, 1.5, "1", None):
        with pytest.raises(ValueError, match="seed"):
            prototype.parameters_for_seed(bad)


@pytest.mark.skipif(shutil.which("racket") is None, reason="bundled Racket not on PATH")
def test_racket_labeled_episodes_refute_the_other_distance_and_public_masks_it():
    prototype = _load_prototype()
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge() as bridge:
        episodes = [
            prototype.make_episode(seed, root=ROOT, bridge=bridge)
            for seed in (0, 1)
        ]

    assert {episode["parameters"]["docking_distance"] for episode in episodes} == {1, 2}
    for episode in episodes:
        assert episode["parameter_selected_once"] is True
        assert episode["ambiguities"] == []
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 1
        rival = episode["parameter_rivals"][0]
        assert rival["status"] == "refuted_by_every_demonstration"
        assert rival["demonstration_mismatch_indices"] == [0, 1, 2]
        assert rival["query_mismatch_indices"] == [0]

        public = prototype.public_challenge(episode)
        assert set(public) == {"train", "test"}
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert all(set(pair) == {"input"} for pair in public["test"])
        serialized = json.dumps(public, sort_keys=True)
        assert "docking_distance" not in serialized
        assert "racket" not in serialized.lower()
