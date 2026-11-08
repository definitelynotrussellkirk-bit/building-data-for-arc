"""Focused tests for the task-local anchor-color parametric prototype."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import sys

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, canonical_path, find_root

TASK_HOME = Path(__file__).resolve().parents[1]
PROTOTYPE_PATH = TASK_HOME / "workspace" / "parametric" / "prototype.py"
ROOT = find_root(__file__)


def _load_prototype():
    spec = importlib.util.spec_from_file_location(
        "task_2c1567aea733_parametric_anchor_color", PROTOTYPE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def prototype():
    return _load_prototype()


def _canonical_program() -> str:
    matches = []
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == "2c1567aea733":
            matches.append(row["program_solution"])
    assert len(matches) == 1
    return matches[0]


def test_prototype_module_exists():
    assert PROTOTYPE_PATH.is_file()


def test_parameter_contract_is_strict_and_selected_once(prototype):
    assert prototype.PARAMETER_NAME == "anchor_color"
    assert prototype.ALLOWED_ANCHORS == (1, 2, 4)
    assert prototype.DEFAULT_ANCHOR == 1
    assert [prototype.choose_anchor(seed) for seed in range(3)] == [1, 2, 4]
    assert prototype.choose_anchor(17) == prototype.choose_anchor(17)

    for value in (True, 1.0, "1", None):
        with pytest.raises(TypeError):
            prototype.choose_anchor(value)
    for value in (0, 3, 5, 9):
        with pytest.raises(ValueError):
            prototype.program_for(value)
    with pytest.raises(TypeError):
        prototype.program_for(True)


def test_program_sources_preserve_exact_default_and_only_change_anchor_lookup(prototype):
    canonical = _canonical_program()
    needle = "(find-color g 1)"
    assert canonical.count(needle) == 1
    assert prototype.program_for(1) == canonical
    for anchor in (2, 4):
        alternative = prototype.program_for(anchor)
        assert alternative == canonical.replace(needle, f"(find-color g {anchor})")
        assert alternative != canonical


def test_default_python_reference_matches_every_canonical_label(prototype):
    for pair in canonical_pairs(prototype.TASK_ID, root=ROOT, labeled_only=True):
        original = deepcopy(pair["input"])
        assert prototype.apply_python(pair["input"], 1) == pair["output"]
        assert pair["input"] == original


def test_default_complete_program_executes_a_canonical_label(prototype):
    pair = canonical_pairs(prototype.TASK_ID, root=ROOT, labeled_only=True)[0]
    with RacketBridge() as bridge:
        actual = prototype.execute_racket(
            bridge, prototype.program_for(1), pair["input"]
        )
    assert actual == pair["output"]


def test_all_anchor_settings_diverge_without_clipping_on_sampled_inputs(prototype):
    grids = prototype.sample_inputs(20261023, pair_count=12)
    assert len(grids) == len({prototype.grid_sha256(grid) for grid in grids}) == 12

    parent, _path, _sha = prototype.load_parent(root=ROOT)
    for grid in grids:
        assert parent.self_check(grid) == []
        assert parent.observe_overrides(grid)["scene_profile"] in {
            "copied_rectangles",
            "copied_irregular",
        }
        nonzero = sum(value != 0 for row in grid for value in row)
        outputs = {anchor: prototype.apply_python(grid, anchor) for anchor in (1, 2, 4)}
        assert len({prototype.grid_sha256(value) for value in outputs.values()}) == 3
        for output in outputs.values():
            assert sum(value != 0 for row in output for value in row) == nonzero
            assert sorted(value for row in output for value in row if value) == sorted(
                value for row in grid for value in row if value
            )


def test_episode_counts_inputs_are_setting_independent_and_all_queries_are_taught(prototype):
    seed = 99173
    inputs_by_anchor = []
    for anchor in prototype.ALLOWED_ANCHORS:
        episode = prototype.build_episode(
            seed,
            anchor_color=anchor,
            demo_count=3,
            query_count=4,
            root=ROOT,
        )
        assert episode["meta"][prototype.PARAMETER_NAME] == anchor
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 4
        all_pairs = episode["train"] + episode["test"]
        inputs_by_anchor.append([pair["input"] for pair in all_pairs])
        assert len({prototype.grid_sha256(pair["input"]) for pair in all_pairs}) == 7
        assert all(
            pair["output"] == prototype.apply_python(pair["input"], anchor)
            for pair in all_pairs
        )

        score = prototype.score_episode(episode)
        assert score["status"] == "identifiable"
        assert len(score["query_checks"]) == 4
        for query in score["query_checks"]:
            assert query["status"] == "identifiable"
            assert {row["anchor_color"] for row in query["rivals"]} == (
                set(prototype.ALLOWED_ANCHORS) - {anchor}
            )
            assert all(row["status"] == "refuted_by_demonstrations" for row in query["rivals"])
            assert all(row["demonstration_mismatches"] == [0, 1, 2] for row in query["rivals"])
            assert all(row["query_disagrees"] is True for row in query["rivals"])

    assert inputs_by_anchor[0] == inputs_by_anchor[1] == inputs_by_anchor[2]


def test_invalid_counts_and_non_total_inputs_fail_loudly(prototype):
    for kwargs in (
        {"demo_count": True},
        {"demo_count": 0},
        {"demo_count": 9},
        {"query_count": 0},
        {"query_count": 9},
        {"demo_count": 8, "query_count": 8},
    ):
        with pytest.raises((TypeError, ValueError)):
            prototype.build_episode(1, **kwargs)

    malformed = [
        [],
        [[0], [0, 1]],
        [[0, 1], [2, 3]],
        [[0, 1, 2], [4, 0, 0]],
    ]
    for grid in malformed:
        with pytest.raises(ValueError):
            prototype.apply_python(grid, 1)

    # Unequal-height objects can clip under an alternate low anchor. The
    # prototype must reject that unsupported input instead of silently dropping cells.
    clipping = [
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [1, 0, 0, 0, 2, 0, 0, 0, 0, 0],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 4, 0],
    ]
    with pytest.raises(ValueError, match="clip"):
        prototype.apply_python(clipping, 4)


def test_legacy_evidence_writer_fails_closed_before_duplicate_native_qualification(prototype, tmp_path):
    """The retained writer is legacy; native qualification owns full Racket replay."""
    racket_path = os.environ.get("RACKET_PATH")
    assert racket_path, "RACKET_PATH must be supplied by the packet wrapper"

    out = tmp_path / "incomplete-evidence"
    report = prototype.write_evidence(
        out,
        seeds=(0,),
        demo_count=2,
        query_count=1,
        root=ROOT,
        racket_path=racket_path,
    )
    assert report["status"] == "error"
    assert report["error"] == {
        "type": "ValueError",
        "message": "retained seeds must cover anchor colors 1, 2, and 4",
    }
    assert json.loads((out / "report.json").read_text())["status"] == "error"
    assert json.loads((out / "manifest.json").read_text())["status"] == "error"
    with pytest.raises(FileExistsError):
        prototype.write_evidence(out, racket_path=racket_path)
