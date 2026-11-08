"""Focused contract for the proposed reflection-extent rule prototype."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "66e63986855b"
ROOT = find_root(__file__)
PROTOTYPE_PATH = (
    ROOT
    / "generators"
    / TASK_ID
    / "workspace"
    / "parametric"
    / "prototype.py"
)

WITNESS_INPUT = [
    [8, 8, 8, 0, 0, 0],
    [8, 0, 0, 0, 0, 0],
    [8, 0, 0, 0, 0, 0],
    [8, 0, 0, 0, 0, 0],
    [8, 8, 8, 0, 0, 0],
    [0, 0, 0, 0, 0, 0],
]
EXTENT_ONE_EXPECTED = [
    [0, 0, 0, 0, 0, 0],
    [0, 8, 8, 0, 0, 0],
    [0, 8, 8, 0, 0, 0],
    [0, 8, 8, 0, 0, 0],
    [0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0],
]
EXTENT_TWO_EXPECTED = [
    [0, 0, 0, 0, 0, 0],
    [0, 8, 8, 8, 8, 0],
    [0, 8, 8, 8, 8, 0],
    [0, 8, 8, 8, 8, 0],
    [0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0],
]


@pytest.fixture(scope="module")
def proto():
    assert PROTOTYPE_PATH.is_file(), f"missing prototype: {PROTOTYPE_PATH}"
    spec = importlib.util.spec_from_file_location(
        "task_66e63986855b_parametric_reflection_extent",
        PROTOTYPE_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def bridge():
    runtime = RacketBridge(max_calls_before_restart=128)
    try:
        yield runtime
    finally:
        runtime.shutdown()


def test_default_program_is_exact_canonical_and_both_rules_execute_literal_witness(
    proto, bridge
) -> None:
    canonical = proto.canonical_program(ROOT)
    assert proto.program_for_extent(2, root=ROOT) == canonical

    assert proto.apply_python(WITNESS_INPUT, 1) == EXTENT_ONE_EXPECTED
    assert proto.apply_python(WITNESS_INPUT, 2) == EXTENT_TWO_EXPECTED
    assert proto.apply_racket(WITNESS_INPUT, 1, bridge=bridge) == EXTENT_ONE_EXPECTED
    assert proto.apply_racket(WITNESS_INPUT, 2, bridge=bridge) == EXTENT_TWO_EXPECTED


def test_parameter_is_chosen_once_and_invalid_scalars_fail_closed(proto, monkeypatch) -> None:
    assert proto.choose_parameters(0) == {"reflection_extent": 2}
    assert proto.choose_parameters(1) == {"reflection_extent": 1}
    assert proto.choose_parameters(0) == proto.choose_parameters(0)
    assert {
        proto.choose_parameters(seed)["reflection_extent"] for seed in range(8)
    } == {1, 2}

    for bad in (True, False, 0, 3, 1.0, "2", None):
        with pytest.raises(ValueError, match="reflection_extent"):
            proto.validate_extent(bad)
    for bad in (True, 0, -1, 9, 2.5, "3"):
        with pytest.raises(ValueError, match="demonstrations"):
            proto.validate_counts(bad, 4)
        with pytest.raises(ValueError, match="queries"):
            proto.validate_counts(3, bad)

    monkeypatch.setattr(
        proto,
        "canonical_program",
        lambda root=None: "(rule! (lambda (g) g))",
    )
    with pytest.raises(ValueError, match="substitution site"):
        proto.program_for_extent(1, root=ROOT)


def test_complete_episodes_are_lawful_racket_labeled_and_refute_the_other_setting(
    proto, bridge
) -> None:
    selected, _source, _sha = load_selected_generator(TASK_ID, root=ROOT)
    episodes = [
        proto.build_episode(seed, demos=3, queries=4, bridge=bridge)
        for seed in (0, 1)
    ]
    assert {
        episode["parameters"]["reflection_extent"] for episode in episodes
    } == {1, 2}

    for episode in episodes:
        assert episode["counts"] == {"demonstrations": 3, "queries": 4}
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 4
        assert len(episode["samples"]) == 7
        serialized_inputs = [
            json.dumps(pair["input"], separators=(",", ":"))
            for pair in [*episode["train"], *episode["test"]]
        ]
        assert len(set(serialized_inputs)) == 7
        assert episode["rival"] == {
            "reflection_extent": 3 - episode["parameters"]["reflection_extent"],
            "identified_by_demonstrations": True,
            "demo_differences": [0, 1, 2],
            "query_differences": [0, 1, 2, 3],
            "status": "distinguished",
        }
        assert proto.parameter_rival_findings(episode, bridge=bridge) == []
        for pair in [*episode["train"], *episode["test"]]:
            assert selected.self_check(pair["input"]) == []
            assert pair["output"] == proto.apply_python(
                pair["input"], episode["parameters"]["reflection_extent"]
            )


def test_public_projection_masks_private_semantics_and_uses_visible_bytes_only(
    proto, bridge
) -> None:
    episode = proto.build_episode(0, demos=2, queries=4, bridge=bridge)
    public = proto.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])

    serialized = json.dumps(public, sort_keys=True)
    for forbidden in (
        "reflection_extent",
        "parameters",
        "seed",
        "program",
        "rival",
        "samples",
    ):
        assert forbidden not in serialized

    changed_private = deepcopy(episode)
    changed_private["seed"] = 999999
    changed_private["parameters"]["reflection_extent"] = 1
    changed_private["test"][0]["output"] = [[9]]
    assert public_challenge_id(changed_private) == public_challenge_id(episode)
    assert public_challenge_bytes(changed_private) == public_challenge_bytes(episode)


def test_materializer_writes_hash_bound_private_and_masked_public_evidence(
    proto, bridge, tmp_path: Path
) -> None:
    out = tmp_path / "reflection-extent"
    report = proto.materialize(
        out,
        demos=3,
        queries=4,
        episode_seeds=(0, 1),
        bridge=bridge,
    )

    assert report["status"] == "proposed"
    assert report["parameter"] == {
        "name": "reflection_extent",
        "values": [1, 2],
        "default": 2,
        "selection": "once per episode; even seed -> 2, odd seed -> 1",
        "input_constraints": "unchanged selected-generator lawful domain",
    }
    assert report["counts"] == {"demonstrations": 3, "queries": 4}
    assert report["checks"]["all_passed"] is True
    assert report["checks"]["racket_python_parity"] is True
    assert report["checks"]["all_queries_distinguish_other_setting"] is True

    extent_two_path = out / "private" / "programs" / "reflection-extent-2.rkt"
    extent_one_path = out / "private" / "programs" / "reflection-extent-1.rkt"
    assert extent_two_path.read_text(encoding="utf-8") == proto.canonical_program(ROOT)
    assert extent_one_path.read_text(encoding="utf-8") == proto.program_for_extent(1)
    assert report["programs"]["2"]["sha256"] == hashlib.sha256(
        extent_two_path.read_bytes()
    ).hexdigest()

    episode_files = sorted((out / "private" / "episodes").glob("*.json"))
    public_files = sorted((out / "public").glob("*.json"))
    assert len(episode_files) == 2
    assert len(public_files) == 2
    assert (out / "private" / "witness.json").is_file()
    assert (out / "report.json").is_file()

    private_episodes = [
        json.loads(path.read_text(encoding="utf-8")) for path in episode_files
    ]
    by_id = {
        public_challenge_id(episode): episode for episode in private_episodes
    }
    assert set(by_id) == {path.stem for path in public_files}
    for path in public_files:
        payload = path.read_bytes()
        assert hashlib.sha256(payload).hexdigest() == path.stem
        assert payload == public_challenge_bytes(by_id[path.stem])
        public = json.loads(payload)
        assert len(public["train"]) == 3
        assert len(public["test"]) == 4
        assert all("output" not in pair for pair in public["test"])
        text = payload.decode("utf-8")
        for forbidden in (
            "reflection_extent",
            "seed",
            "program",
            "rival",
            "samples",
        ):
            assert forbidden not in text

    with pytest.raises(FileExistsError, match="already exists"):
        proto.materialize(out, bridge=bridge)
    duplicate_out = tmp_path / "duplicate"
    with pytest.raises(ValueError, match="duplicate public payload"):
        proto.materialize(
            duplicate_out,
            demos=1,
            queries=1,
            episode_seeds=(0, 0),
            bridge=bridge,
        )
    assert not duplicate_out.exists()


def test_cli_exposes_separate_demo_and_query_counts(tmp_path: Path) -> None:
    out = tmp_path / "cli-evidence"
    completed = subprocess.run(
        [
            sys.executable,
            str(PROTOTYPE_PATH),
            "--out",
            str(out),
            "--demos",
            "2",
            "--queries",
            "4",
            "--episode-seeds",
            "0",
            "1",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    report = json.loads((out / "report.json").read_text(encoding="utf-8"))
    assert report["counts"] == {"demonstrations": 2, "queries": 4}
    assert all(
        episode["counts"] == {"demonstrations": 2, "queries": 4}
        for episode in report["private_episodes"]
    )
