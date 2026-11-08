"""Focused tests for the proposed completion-transform prototype."""
from __future__ import annotations

import copy
import hashlib
import json
import re
import random
import importlib
import importlib.util
import sys
from pathlib import Path

import pytest

from reviewer_support import find_root

ROOT = find_root(__file__)
SOURCE = ROOT / "generators/1674812130ff/workspace/parametric/prototype.py"


@pytest.fixture(scope="module")
def prototype():
    assert SOURCE.is_file(), "the task-local parametric prototype must exist"
    spec = importlib.util.spec_from_file_location("parametric_1674812130ff", SOURCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def racket_bridge(prototype):
    with prototype.RacketBridge() as bridge:
        yield bridge


def test_programs_preserve_exact_canonical_default(prototype):
    canonical = prototype.canonical_source(root=ROOT)
    assert canonical == "(rule! (grid-overlay-on (rotate-180 g) g 7))"
    assert hashlib.sha256(canonical.encode()).hexdigest() == (
        "b91db7bbbbf56e66fa4c8631114427f125bab0f01e93526e65f9c9436e554e0b"
    )
    assert prototype.program_for("rotate_180", root=ROOT) == canonical
    assert prototype.program_for("flip_lr", root=ROOT) == (
        "(rule! (grid-overlay-on (flip-lr g) g 7))"
    )

    for value in ("rotate-180", "flip-ud", "", 0, None, True):
        with pytest.raises(ValueError, match="completion_transform"):
            prototype.program_for(value, root=ROOT)


def _transform_witness():
    return [
        [7, 1, 4, 7, 7],
        [7, 2, 4, 7, 7],
        [8, 3, 8, 7, 8],
        [7, 5, 4, 7, 7],
        [7, 6, 4, 7, 7],
    ]


def test_real_racket_executes_each_completion_transform(prototype, racket_bridge):
    grid = _transform_witness()
    expected_rotate = [
        [7, 1, 4, 6, 7],
        [7, 2, 4, 5, 7],
        [8, 3, 8, 3, 8],
        [7, 5, 4, 2, 7],
        [7, 6, 4, 1, 7],
    ]
    expected_flip = [
        [7, 1, 4, 1, 7],
        [7, 2, 4, 2, 7],
        [8, 3, 8, 3, 8],
        [7, 5, 4, 5, 7],
        [7, 6, 4, 6, 7],
    ]

    before = [row[:] for row in grid]
    actual_rotate = prototype.execute_rule(
        prototype.program_for("rotate_180", root=ROOT), grid, bridge=racket_bridge
    )
    actual_flip = prototype.execute_rule(
        prototype.program_for("flip_lr", root=ROOT), grid, bridge=racket_bridge
    )
    assert actual_rotate == expected_rotate
    assert actual_flip == expected_flip
    assert prototype.python_complete(grid, completion_transform="rotate_180") == expected_rotate
    assert prototype.python_complete(grid, completion_transform="flip_lr") == expected_flip
    assert grid == before


def test_episode_fixes_one_transform_and_emits_four_distinct_queries(
    prototype, racket_bridge
):
    random_state = random.getstate()
    rotate = prototype.make_episode(
        17, completion_transform="rotate_180", root=ROOT, bridge=racket_bridge
    )
    flip = prototype.make_episode(
        17, completion_transform="flip_lr", root=ROOT, bridge=racket_bridge
    )
    replay = prototype.make_episode(
        17, completion_transform="rotate_180", root=ROOT, bridge=racket_bridge
    )

    assert rotate == replay
    assert rotate["parameters"] == {"completion_transform": "rotate_180"}
    assert flip["parameters"] == {"completion_transform": "flip_lr"}
    assert len(rotate["train"]) == len(flip["train"]) == 2
    assert len(rotate["test"]) == len(flip["test"]) == 4

    rotate_pairs = rotate["train"] + rotate["test"]
    flip_pairs = flip["train"] + flip["test"]
    assert [pair["input"] for pair in rotate_pairs] == [
        pair["input"] for pair in flip_pairs
    ]
    assert len({prototype.grid_sha256(pair["input"]) for pair in rotate_pairs}) == 6

    for transform, episode in (("rotate_180", rotate), ("flip_lr", flip)):
        for pair in episode["train"] + episode["test"]:
            assert pair["output"] == prototype.python_complete(
                pair["input"], completion_transform=transform
            )
        rival, = episode["parameter_rivals"]
        assert rival["status"] == "refuted_by_demonstrations"
        assert rival["demonstration_mismatch_indices"] == [0, 1]
        assert rival["query_mismatch_indices"] == [0, 1, 2, 3]
        assert not episode["ambiguities"]

    assert random.getstate() == random_state


def test_public_projection_hides_private_rule_and_query_answers(
    prototype, racket_bridge
):
    episode = prototype.make_episode(
        19, completion_transform="flip_lr", root=ROOT, bridge=racket_bridge
    )
    public = prototype.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])

    public_id = prototype.public_id(episode)
    private_change = copy.deepcopy(episode)
    private_change["seed"] = 999_999
    private_change["program"] = "private replacement"
    private_change["parameters"]["completion_transform"] = "rotate_180"
    private_change["test"][0]["output"][0][0] ^= 1
    assert prototype.public_id(private_change) == public_id

    visible_change = copy.deepcopy(episode)
    visible_change["train"][0]["output"][0][0] ^= 1
    assert prototype.public_id(visible_change) != public_id

    before = copy.deepcopy(episode)
    public["train"][0]["input"][0][0] = 9
    assert episode == before


def test_evidence_writer_executes_both_settings_and_binds_public_files(
    prototype, racket_bridge, monkeypatch, tmp_path
):
    out = tmp_path / "completion-evidence"
    monkeypatch.setattr(
        prototype,
        "RacketBridge",
        lambda: pytest.fail("write_evidence ignored its supplied bridge"),
    )
    report = prototype.write_evidence(
        seed=23, out=out, root=ROOT, bridge=racket_bridge
    )

    assert report["status"] == "proposed_unapproved"
    assert report["approved"] is False
    assert report["parameter"] == {
        "name": "completion_transform",
        "allowed_values": ["rotate_180", "flip_lr"],
        "original_default": "rotate_180",
        "selection_scope": "once_per_episode",
        "input_constraints_depend_on_parameter": False,
    }
    assert report["counts"] == {
        "episodes": 2,
        "train_pairs": 4,
        "query_pairs": 8,
        "distinct_input_grids": 6,
        "settings_exercised": 2,
        "canonical_pairs_checked": 4,
        "ambiguous_parameter_rivals": 0,
    }
    assert report["canonical_default"]["all_match"] is True

    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["schema"] == "arcpuzzles-parametric-evidence-manifest-v1"
    for row in manifest["files"]:
        path = out / row["path"]
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"]

    visible_ids = set()
    for row in report["episodes"]:
        public_path = out / row["public_path"]
        private_path = out / row["private_path"]
        rule_path = out / row["racket_path"]
        assert re.fullmatch(r"challenge-[0-9a-f]{64}\.json", public_path.name)
        private = json.loads(private_path.read_text())
        public = json.loads(public_path.read_text())
        assert public == prototype.public_challenge(private)
        assert public_path.name == f"challenge-{prototype.public_id(private)}.json"
        assert hashlib.sha256(rule_path.read_bytes()).hexdigest() == private["program_sha256"]
        assert len(private["train"]) == 2 and len(private["test"]) == 4
        assert all("output" not in pair for pair in public["test"])
        visible_ids.add(row["public_id"])
    assert len(visible_ids) == 2

    with pytest.raises(FileExistsError):
        prototype.write_evidence(
            seed=23, out=out, root=ROOT, bridge=racket_bridge
        )


def test_cli_exposes_demo_and_query_counts_separately(
    prototype, racket_bridge, tmp_path
):
    out = tmp_path / "cli-evidence"
    assert prototype.main([
        "--seed", "31",
        "--difficulty", "hard",
        "--train", "3",
        "--test", "4",
        "--out", str(out),
    ], bridge=racket_bridge) == 0
    report = json.loads((out / "report.json").read_text())
    assert report["counts"]["train_pairs"] == 6
    assert report["counts"]["query_pairs"] == 8


def test_promotion_adapter_is_thin_and_declares_bounded_settings(
    prototype, monkeypatch
):
    adapter_path = SOURCE.parent / "adapter.py"
    promotion_path = SOURCE.parent / "promotion.json"
    assert adapter_path.is_file()
    assert promotion_path.is_file()
    contract = json.loads(promotion_path.read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/1674812130ff/workspace/parametric/adapter.py",
        "parameters": {
            "completion_transform": ["rotate_180", "flip_lr"]
        },
        "default": {"completion_transform": "rotate_180"},
        "limits": {"demos": [1, 8], "queries": [1, 8]},
    }

    monkeypatch.syspath_prepend(str(SOURCE.parent))
    sys.modules.pop("adapter", None)
    sys.modules["prototype"] = prototype
    adapter = importlib.import_module("adapter")
    assert adapter.program({"completion_transform": "rotate_180"}) == (
        "(rule! (grid-overlay-on (rotate-180 g) g 7))"
    )
    episode = adapter.generate(7, {"completion_transform": "flip_lr"}, 1, 1)
    assert len(episode["train"]) == 1
    assert len(episode["test"]) == 1
    assert episode["program_solution"] == prototype.program_for("flip_lr")


def test_strict_seed_count_and_difficulty_validation(prototype, racket_bridge):
    for seed in (-1, 1.5, True, "7"):
        with pytest.raises(ValueError, match="seed"):
            prototype.make_episode(seed, bridge=racket_bridge)

    for train_count, query_count, message in (
        (0, 4, "train_count"),
        (9, 4, "train_count"),
        (True, 4, "train_count"),
        (2, 0, "query_count"),
        (2, 9, "query_count"),
        (2, True, "query_count"),
    ):
        with pytest.raises(ValueError, match=message):
            prototype.make_episode(
                1,
                train_count=train_count,
                query_count=query_count,
                bridge=racket_bridge,
            )

    with pytest.raises(ValueError, match="difficulty"):
        prototype.make_episode(1, difficulty="extreme", bridge=racket_bridge)


def test_adversarial_probe_covers_boundary_counts_privacy_and_numeric_types(
    prototype, racket_bridge, monkeypatch
):
    probe_path = SOURCE.parent / "adversarial_probe.py"
    assert probe_path.is_file(), "the reusable bounded adversarial probe must exist"
    monkeypatch.syspath_prepend(str(SOURCE.parent))
    sys.modules["prototype"] = prototype
    spec = importlib.util.spec_from_file_location(
        "parametric_1674812130ff_adversarial_probe", probe_path
    )
    assert spec is not None and spec.loader is not None
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)

    report = probe.run_probe(
        seeds=[0, 17],
        difficulties=["easy", "hard"],
        root=ROOT,
        bridge=racket_bridge,
    )
    assert report["schema"] == "arcpuzzles-parametric-adversarial-probe-v1"
    assert report["status"] == "bounded_no_findings"
    assert report["findings"] == []
    assert report["surfaces"] == [
        "sampler_boundaries_and_parameter_racket_parity",
        "public_private_export_and_numeric_types",
    ]
    assert report["counts"] == {
        "seed_difficulty_cases": 4,
        "episodes": 8,
        "racket_labeled_pairs": 72,
        "distinct_inputs_checked": 36,
        "public_ids_checked": 8,
    }
