from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import json
from unittest.mock import patch
import sys

import pytest

from scripts import build_kimi_generator_assignment as assignment


TASK_ID = "64592477ccc8"
ROOT = Path(__file__).resolve().parents[1]


def test_validate_record_does_not_rebuild_assignment_queue(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = tmp_path / "record.json"
    record.write_text(json.dumps({"task_id": "cheap-gate"}), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["builder", "--validate-record", str(record)])

    with patch.object(assignment, "build_rows") as build_rows, patch.object(
        assignment, "_review_contract_errors", return_value=[]
    ), patch.object(assignment, "_queued_training_caps", return_value={}):
        assert assignment.main() == 0

    build_rows.assert_not_called()


def test_queued_training_caps_streams_valid_rows(tmp_path: Path) -> None:
    queue = tmp_path / "queue.jsonl"
    queue.write_text(
        json.dumps(
            {
                "task_id": "abc",
                "machine_ratings": {
                    "training_suitability_cap": {"tier": 3}
                },
            }
        )
        + "\nnot-json\n",
        encoding="utf-8",
    )

    assert assignment._queued_training_caps(queue) == {"abc": 3}


@pytest.mark.parametrize(
    ("sources", "expected_class"),
    [
        (["(rule! g)", "(rule! g)"], "stale_exact"),
        (["(rule!\n g)", "(rule! g)"], "whitespace_only"),
        (["(rule! g) ; note", "(rule! g)"], "comment_only"),
        (["(rule! g)", "(rule! (rotate-cw g))"], "semantic_text"),
    ],
)
def test_authority_divergence_classification(
    sources: list[str],
    expected_class: str,
) -> None:
    result = assignment._classify_authority_sources(sources)

    assert result["divergence_class"] == expected_class
    assert result["authority_count"] == 2


def test_archival_raw_does_not_compete_with_selected_rule(tmp_path: Path) -> None:
    task_id = "0123456789ab"
    canonical_path = tmp_path / "puzzles.jsonl"
    canonical_rule = "(rule! (lambda (g) g))"
    canonical_path.write_text(
        json.dumps({"task_id": task_id, "program_solution": canonical_rule})
        + "\n",
        encoding="utf-8",
    )
    base_dir = tmp_path / "base"
    base_dir.mkdir()
    (base_dir / "task.json").write_text(
        json.dumps(
            {
                "task_id": task_id,
                "racket_target": {
                    "target_code": canonical_rule,
                    "target_code_role": "selected_task_rule",
                    "raw_code": "(rule! (lambda (g) (rotate-cw g)))",
                    "raw_code_role": "archival_executable_source",
                },
            }
        ),
        encoding="utf-8",
    )

    assignment._authority_divergence_profiles.cache_clear()
    try:
        with patch.object(assignment, "CANONICAL", canonical_path), patch.object(
            assignment, "BASE_SOLUTIONS", base_dir
        ):
            profile = assignment._authority_divergence_profiles()[task_id]
    finally:
        assignment._authority_divergence_profiles.cache_clear()

    assert profile["divergence_class"] == "stale_exact"
    assert profile["selected_authority_count"] == 2
    assert profile["archival_source_count"] == 1
    assert profile["archival_differs_from_selected"] is True


def test_legacy_raw_is_selected_only_when_no_selected_rule_exists(
    tmp_path: Path,
) -> None:
    task_id = "abcdef012345"
    canonical_path = tmp_path / "puzzles.jsonl"
    canonical_path.write_text("", encoding="utf-8")
    base_dir = tmp_path / "base"
    base_dir.mkdir()
    for index, source in enumerate(("(rule! g)", "(rule! (rotate-cw g))")):
        (base_dir / f"{index}.json").write_text(
            json.dumps(
                {
                    "task_id": task_id,
                    "racket_target": {"raw_code": source},
                }
            ),
            encoding="utf-8",
        )

    assignment._authority_divergence_profiles.cache_clear()
    try:
        with patch.object(assignment, "CANONICAL", canonical_path), patch.object(
            assignment, "BASE_SOLUTIONS", base_dir
        ):
            profile = assignment._authority_divergence_profiles()[task_id]
    finally:
        assignment._authority_divergence_profiles.cache_clear()

    assert profile["divergence_class"] == "stale_exact"
    assert profile["selected_authority_count"] == 1
    assert profile["archival_source_count"] == 1


def test_canonical_selfcheck_preflight_flags_two_corner_baseline(
    tmp_path: Path,
) -> None:
    baseline = tmp_path / "generator_before.py"
    baseline.write_text(
        """
def self_check(grid, *, difficulty=None, meta=None):
    by_color = {}
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value:
                by_color.setdefault(value, []).append((row, col))
    errors = []
    for color, points in by_color.items():
        if len(points) != 2:
            errors.append(
                f"color {color} occurs {len(points)} times, expected 2"
            )
    return errors
""".lstrip(),
        encoding="utf-8",
    )

    result = assignment._canonical_selfcheck_probe(TASK_ID, baseline)

    assert result["status"] == "ok"
    assert result["canonical_selfcheck_total"] == 5
    assert result["canonical_selfcheck_rejection_count"] == 5
    assert result["canonical_selfcheck_error_count"] == 0


def test_canonical_selfcheck_preflight_accepts_repaired_generator() -> None:
    generator = (
        ROOT
        / "puzzle_generators"
        / "per_puzzle"
        / TASK_ID
        / "generator.py"
    )

    result = assignment._canonical_selfcheck_probe(TASK_ID, generator)

    assert result["status"] == "ok"
    assert result["canonical_selfcheck_total"] == 5
    assert result["canonical_selfcheck_rejection_count"] == 0
    assert result["canonical_selfcheck_error_count"] == 0


def test_preflight_freshness_labels_changed_generator_hash_as_historical() -> None:
    preflight = {"generator_sha256": "a" * 64, "findings": ["graylisted"]}

    assert assignment._preflight_freshness(preflight, "b" * 64) == (
        "stale_generator_sha"
    )
    assert assignment._preflight_freshness(preflight, "a" * 64) == "current"
    assert assignment._preflight_freshness({}, "a" * 64) == "absent"


def test_cheap_override_preflight_flags_accepted_unconsumed_axis() -> None:
    def generate(seed, sample_index, *, difficulty=None, **overrides):
        del seed, sample_index, difficulty, overrides
        return [[0]]

    module = SimpleNamespace(
        AXES={"texture": {"type": "str", "valid": "warm|cool"}},
        generate=generate,
    )

    result = assignment._cheap_override_preflight(module)

    assert result["override_axes_probed"] == 1
    assert result["override_accepted_unconsumed_count"] == 1
    assert result["override_observation_failure_count"] == 1
    assert result["override_unknown_key_accepted_count"] == 1
    assert "unknown_key_accepted" in result["override_root_cause_categories"]


def test_cheap_override_preflight_accepts_consumed_observable_axis() -> None:
    from puzzle_generators.base import gen_ctx

    def generate(seed, sample_index, *, difficulty=None, **overrides):
        ctx = gen_ctx(
            seed=seed,
            sample_index=sample_index,
            version="fixture",
            task_id="fixture",
            difficulty=difficulty,
            overrides=overrides,
        )
        value = ctx.draw_choice("texture", ("warm", "cool"))
        return [[1 if value == "warm" else 2]]

    module = SimpleNamespace(
        AXES={"texture": {"type": "str", "valid": "warm|cool"}},
        generate=generate,
        observe_overrides=lambda grid: {
            "texture": "warm" if grid == [[1]] else "cool"
        },
    )

    result = assignment._cheap_override_preflight(module)

    assert result["override_axes_probed"] == 1
    assert result["override_accepted_unconsumed_count"] == 0
    assert result["override_observation_failure_count"] == 0
    assert result["override_unknown_key_verdict"] == "accepted"


def test_cheap_override_preflight_runs_selfcheck_on_accepted_boundary() -> None:
    from puzzle_generators.base import gen_ctx

    def generate(seed, sample_index, *, difficulty=None, **overrides):
        ctx = gen_ctx(
            seed=seed,
            sample_index=sample_index,
            version="fixture",
            task_id="fixture",
            difficulty=difficulty,
            overrides=overrides,
        )
        value = ctx.draw_choice("texture", ("warm", "cool"))
        return [[1 if value == "warm" else 2]]

    module = SimpleNamespace(
        AXES={"texture": {"type": "str", "valid": "warm|cool"}},
        generate=generate,
        observe_overrides=lambda grid: {
            "texture": "warm" if grid == [[1]] else "cool"
        },
        self_check=lambda grid, *, difficulty=None, meta=None: [
            "boundary rejected"
        ],
    )

    result = assignment._cheap_override_preflight(module)

    assert result["override_accepted_selfcheck_rejection_count"] == 1
    assert (
        "accepted_boundary_selfcheck_rejected"
        in result["override_root_cause_categories"]
    )
