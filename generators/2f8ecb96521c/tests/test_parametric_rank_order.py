"""Focused tests for the separate episode-level rank-order prototype."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root

TASK_ID = "2f8ecb96521c"
HOME = Path(__file__).resolve().parents[1]
PROTOTYPE_PATH = HOME / "workspace" / "parametric" / "prototype.py"


def _load_prototype():
    assert PROTOTYPE_PATH.is_file(), f"missing prototype: {PROTOTYPE_PATH}"
    spec = importlib.util.spec_from_file_location(
        "rank_order_parametric_prototype", PROTOTYPE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    root = find_root(__file__)
    rows = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rows.append(row)
    assert len(rows) == 1
    return rows[0]["program_solution"]


def test_program_materialization_preserves_default_and_reverses_only_rank_order():
    prototype = _load_prototype()
    canonical = _canonical_program()

    assert prototype.DEFAULT_RANK_ORDER == "small_to_large"
    assert tuple(prototype.RANK_ORDERS) == ("small_to_large", "large_to_small")
    assert prototype.program_for("small_to_large", root=find_root(__file__)) == canonical

    reverse = prototype.program_for("large_to_small", root=find_root(__file__))
    assert reverse != canonical
    assert "(reverse (sort-by (objects grid 0) obj-size))" in reverse
    assert reverse.replace("(reverse (sort-by (objects grid 0) obj-size))",
                           "(sort-by (objects grid 0) obj-size)") == canonical

    for invalid in (None, True, 1, "ascending", ""):
        with pytest.raises((TypeError, ValueError)):
            prototype.program_for(invalid, root=find_root(__file__))


def test_seed_selection_is_deterministic_and_covers_both_settings():
    prototype = _load_prototype()
    first = prototype.select_seeds(20261020, per_setting=1)
    second = prototype.select_seeds(20261020, per_setting=1)
    assert first == second
    assert set(first["seeds_by_setting"]) == set(prototype.RANK_ORDERS)
    assert all(len(seeds) == 1 for seeds in first["seeds_by_setting"].values())
    for setting, seeds in first["seeds_by_setting"].items():
        assert prototype.choose_rank_order(seeds[0]) == setting


def test_probe_uses_real_racket_and_emits_safe_distinguishing_episodes(tmp_path):
    prototype = _load_prototype()
    report = prototype.run_probe(
        base_seed=20261020,
        per_setting=1,
        difficulty="medium",
        out_dir=tmp_path,
        root=find_root(__file__),
    )

    assert report["status"] == "passed"
    assert report["prototype_status"] == "proposed"
    assert report["racket_verified"] is True
    assert report["python_parity_verified"] is True
    assert report["episode_count"] == 2
    assert report["racket_application_count"] == 20
    assert set(report["settings_observed"]) == set(prototype.RANK_ORDERS)
    assert (tmp_path / "report.json").is_file()
    assert (tmp_path / "private" / "cross-setting-witness.json").is_file()

    for episode in report["episodes"]:
        assert episode["demonstration_difference_indices"] == [0, 1, 2, 3]
        assert episode["query_difference_indices"] == [0]
        public = json.loads((tmp_path / episode["public_path"]).read_text())
        private = json.loads((tmp_path / episode["private_path"]).read_text())

        assert set(public) == {"schema", "task_id", "train", "test"}
        assert len(public["train"]) == prototype.N_TRAIN
        assert len(public["test"]) == prototype.N_TEST
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert all(set(pair) == {"input"} for pair in public["test"])
        public_text = json.dumps(public, sort_keys=True)
        assert episode["rank_order"] not in public_text
        assert "program" not in public_text.lower()

        assert private["rank_order"] == episode["rank_order"]
        assert private["racket_verified"] is True
        assert private["python_parity_verified"] is True
        assert len(private["train"]) == prototype.N_TRAIN
        assert len(private["test"]) == prototype.N_TEST
        assert all(pair["settings_disagree"] for pair in private["train"])
        assert all(pair["settings_disagree"] for pair in private["test"])
        assert all("output" in pair and "rival_output" in pair
                   for pair in private["test"])

    witness = json.loads(
        (tmp_path / "private" / "cross-setting-witness.json").read_text()
    )
    assert witness["outputs_disagree"] is True
    assert set(witness["outputs"]) == set(prototype.RANK_ORDERS)
    assert witness["outputs"]["small_to_large"] != witness["outputs"]["large_to_small"]
