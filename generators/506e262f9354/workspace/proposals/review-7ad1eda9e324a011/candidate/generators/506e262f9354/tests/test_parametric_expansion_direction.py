"""Focused tests for the proposed expansion-direction prototype."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
import re
from pathlib import Path

import pytest

from reviewer_support import find_root

ROOT = find_root(__file__)
SOURCE = ROOT / "generators/506e262f9354/workspace/parametric/prototype.py"


@pytest.fixture(scope="module")
def prototype():
    assert SOURCE.is_file(), "the task-local parametric prototype must exist"
    spec = importlib.util.spec_from_file_location("parametric_506e262f9354", SOURCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def racket_bridge(prototype):
    """Reuse one protected runtime for the focused suite.

    Repeated bridge construction in one Python process can leave the pinned
    runtime's helper threads alive long enough to stall interpreter shutdown.
    The production prototype therefore accepts an injected bridge, and this
    fixture exercises that supported path.
    """
    with prototype.RacketBridge() as bridge:
        yield bridge


def test_direction_programs_preserve_exact_canonical_default(prototype):
    canonical = prototype.canonical_source(root=ROOT)
    assert hashlib.sha256(canonical.encode()).hexdigest() == (
        "7d00cd1a50d3b572eb7a50d096cb5d01f0e7af4d8f9bc403d42a3b905b20dc6f"
    )
    assert prototype.program_for("up", root=ROOT) == canonical

    down = prototype.program_for("down", root=ROOT)
    assert down != canonical
    assert "(rtop (min-of first sevens))" in down
    assert "(let ((d (- r rtop))" in down

    for value in ("left", "", 0, None, True):
        with pytest.raises(ValueError, match="expansion_direction"):
            prototype.program_for(value, root=ROOT)


def _direction_witness():
    return [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 7, 0, 0, 0],
        [0, 0, 0, 7, 0, 0, 0],
        [0, 0, 0, 7, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
    ]


def test_real_racket_expands_from_the_selected_endpoint(prototype, racket_bridge):
    grid = _direction_witness()
    expected_up = [
        [8, 7, 8, 7, 8, 7, 8],
        [0, 7, 8, 7, 8, 7, 0],
        [0, 0, 8, 7, 8, 0, 0],
        [0, 0, 0, 7, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
    ]
    expected_down = [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 7, 0, 0, 0],
        [0, 0, 8, 7, 8, 0, 0],
        [0, 7, 8, 7, 8, 7, 0],
        [8, 7, 8, 7, 8, 7, 8],
    ]

    before = [row[:] for row in grid]
    actual_up = prototype.execute_rule(
        prototype.program_for("up", root=ROOT), grid, bridge=racket_bridge
    )
    actual_down = prototype.execute_rule(
        prototype.program_for("down", root=ROOT), grid, bridge=racket_bridge
    )
    assert actual_up == expected_up
    assert actual_down == expected_down
    assert prototype.python_mirror(grid, expansion_direction="up") == expected_up
    assert prototype.python_mirror(grid, expansion_direction="down") == expected_down
    assert grid == before


def test_episode_fixes_one_direction_and_emits_four_distinct_queries(
    prototype, racket_bridge
):
    random_state = random.getstate()
    up = prototype.make_episode(
        17, expansion_direction="up", root=ROOT, bridge=racket_bridge
    )
    down = prototype.make_episode(
        17, expansion_direction="down", root=ROOT, bridge=racket_bridge
    )
    replay = prototype.make_episode(
        17, expansion_direction="up", root=ROOT, bridge=racket_bridge
    )

    assert up == replay
    assert up["parameters"] == {"expansion_direction": "up"}
    assert down["parameters"] == {"expansion_direction": "down"}
    assert len(up["train"]) == len(down["train"]) == 3
    assert len(up["test"]) == len(down["test"]) == 4

    up_pairs = up["train"] + up["test"]
    down_pairs = down["train"] + down["test"]
    assert [pair["input"] for pair in up_pairs] == [pair["input"] for pair in down_pairs]
    assert len({prototype.grid_sha256(pair["input"]) for pair in up_pairs}) == 7

    for direction, episode in (("up", up), ("down", down)):
        for pair in episode["train"] + episode["test"]:
            assert pair["output"] == prototype.python_mirror(
                pair["input"], expansion_direction=direction
            )
        rival, = episode["parameter_rivals"]
        assert rival["status"] == "refuted_by_demonstrations"
        assert rival["demonstration_mismatch_indices"] == [0, 1, 2]
        assert rival["query_mismatch_indices"] == [0, 1, 2, 3]
        assert not episode["ambiguities"]

    assert random.getstate() == random_state


def test_public_projection_hides_private_rule_and_query_answers(
    prototype, racket_bridge
):
    episode = prototype.make_episode(
        19, expansion_direction="down", root=ROOT, bridge=racket_bridge
    )
    public = prototype.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])

    public_id = prototype.public_id(episode)
    private_change = copy.deepcopy(episode)
    private_change["seed"] = 999_999
    private_change["program"] = "private replacement"
    private_change["parameters"]["expansion_direction"] = "up"
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
    out = tmp_path / "direction-evidence"
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
        "name": "expansion_direction",
        "allowed_values": ["up", "down"],
        "original_default": "up",
        "selection_scope": "once_per_episode",
        "input_constraints_depend_on_parameter": False,
    }
    assert report["counts"]["episodes"] == 2
    assert report["counts"]["train_pairs"] == 6
    assert report["counts"]["query_pairs"] == 8
    assert report["counts"]["distinct_input_grids"] == 7
    assert report["counts"]["canonical_pairs_checked"] >= 3
    assert report["counts"]["ambiguous_parameter_rivals"] == 0

    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["schema"] == "arcpuzzles-parametric-evidence-manifest-v1"
    for row in manifest["files"]:
        path = out / row["path"]
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"]

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
        assert len(private["train"]) == 3 and len(private["test"]) == 4
        assert all("output" not in pair for pair in public["test"])

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


def test_evidence_writer_preflights_then_writes_public_batch_by_identifier(
    prototype, racket_bridge, monkeypatch, tmp_path
):
    """Public artifacts are planned for the whole batch before any are written."""
    out = tmp_path / "ordered-public-evidence"
    payloads = {
        "up": b'{"visible":"up"}\n',
        "down": b'{"visible":"down"}\n',
    }
    identifiers = {
        key: hashlib.sha256(value).hexdigest() for key, value in payloads.items()
    }
    # Force the prototype's natural up/down iteration to be the reverse of the
    # required identifier order, so a write-as-you-go implementation fails.
    if identifiers["up"] < identifiers["down"]:
        payloads["up"], payloads["down"] = payloads["down"], payloads["up"]
        identifiers = {
            key: hashlib.sha256(value).hexdigest() for key, value in payloads.items()
        }
    assert identifiers["up"] > identifiers["down"]

    monkeypatch.setattr(
        prototype,
        "public_bytes",
        lambda episode: payloads[episode["parameters"]["expansion_direction"]],
    )
    monkeypatch.setattr(
        prototype,
        "public_id",
        lambda episode: identifiers[episode["parameters"]["expansion_direction"]],
    )

    writes = []
    original_write_bytes = Path.write_bytes

    def observe_write(path, payload):
        if path.parent.name == "public" and path.name.startswith("challenge-"):
            writes.append(path.name)
        return original_write_bytes(path, payload)

    monkeypatch.setattr(Path, "write_bytes", observe_write)
    prototype.write_evidence(seed=37, out=out, root=ROOT, bridge=racket_bridge)

    assert writes == [
        f"challenge-{identifiers['down']}.json",
        f"challenge-{identifiers['up']}.json",
    ]


def test_evidence_writer_rejects_duplicate_public_id_before_public_write(
    prototype, racket_bridge, monkeypatch, tmp_path
):
    out = tmp_path / "duplicate-public-evidence"
    payload = b'{"same-visible-payload":true}\n'
    identifier = hashlib.sha256(payload).hexdigest()
    monkeypatch.setattr(prototype, "public_bytes", lambda episode: payload)
    monkeypatch.setattr(prototype, "public_id", lambda episode: identifier)

    writes = []
    original_write_bytes = Path.write_bytes

    def observe_write(path, value):
        if path.parent.name == "public" and path.name.startswith("challenge-"):
            writes.append(path.name)
        return original_write_bytes(path, value)

    monkeypatch.setattr(Path, "write_bytes", observe_write)
    with pytest.raises(ValueError, match="duplicate visible public challenge"):
        prototype.write_evidence(seed=41, out=out, root=ROOT, bridge=racket_bridge)

    assert writes == []
    assert not out.exists()
