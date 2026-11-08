from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import os
import re
import subprocess
import sys

import pytest

from reviewer_support import canonical_path, find_root, load_selected_generator, public_challenge_id


TASK_ID = "3f26d45b9f51"
TASK_HOME = Path(__file__).resolve().parents[1]
PROTOTYPE_PATH = TASK_HOME / "workspace" / "parametric" / "prototype.py"


def _load_prototype():
    spec = importlib.util.spec_from_file_location(
        f"_test_parametric_{TASK_ID}", PROTOTYPE_PATH
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load prototype at {PROTOTYPE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


prototype = _load_prototype()


def _expand(coarse: list[list[int]], divider: int = 8) -> list[list[int]]:
    """Expand a hand-authored coarse lattice into the task's pixel representation."""
    side = 3 * len(coarse) - 1
    grid = [[0 for _ in range(side)] for _ in range(side)]
    for row in range(side):
        if row % 3 == 2:
            grid[row] = [divider for _ in range(side)]
    for col in range(side):
        if col % 3 == 2:
            for row in range(side):
                grid[row][col] = divider
    for cell_row, coarse_row in enumerate(coarse):
        for cell_col, color in enumerate(coarse_row):
            for dr in range(2):
                for dc in range(2):
                    grid[3 * cell_row + dr][3 * cell_col + dc] = color
    return grid


INPUT_COARSE = [
    [0, 0, 0, 0, 0, 0, 3],
    [0, 2, 0, 0, 2, 0, 0],
    [0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0],
    [0, 2, 0, 0, 0, 0, 0],
    [0, 0, 3, 3, 0, 3, 0],
]

BOTH_COARSE = [
    [0, 0, 0, 0, 0, 0, 3],
    [0, 2, 2, 2, 2, 0, 0],
    [0, 2, 0, 0, 0, 0, 0],
    [0, 2, 0, 0, 0, 0, 0],
    [0, 2, 0, 0, 0, 0, 0],
    [0, 2, 0, 0, 0, 0, 0],
    [0, 0, 3, 3, 3, 3, 0],
]

HORIZONTAL_COARSE = [
    [0, 0, 0, 0, 0, 0, 3],
    [0, 2, 2, 2, 2, 0, 0],
    [0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0],
    [0, 2, 0, 0, 0, 0, 0],
    [0, 0, 3, 3, 3, 3, 0],
]

VERTICAL_COARSE = [
    [0, 0, 0, 0, 0, 0, 3],
    [0, 2, 0, 0, 2, 0, 0],
    [0, 2, 0, 0, 0, 0, 0],
    [0, 2, 0, 0, 0, 0, 0],
    [0, 2, 0, 0, 0, 0, 0],
    [0, 2, 0, 0, 0, 0, 0],
    [0, 0, 3, 3, 0, 3, 0],
]


def _canonical_program() -> str:
    root = find_root(__file__)
    rows = [
        json.loads(line)
        for line in canonical_path(root).read_text(encoding="utf-8").splitlines()
    ]
    programs = {row["program_solution"] for row in rows if row.get("task_id") == TASK_ID}
    assert len(programs) == 1
    return programs.pop()


def test_axis_settings_are_strict_and_selected_once_from_seed():
    assert prototype.PARAMETER_NAME == "connection_axes"
    assert prototype.SETTINGS == ("both", "horizontal", "vertical")
    assert prototype.DEFAULT_SETTING == "both"
    assert [prototype.choose_setting(seed) for seed in range(6)] == [
        "both",
        "horizontal",
        "vertical",
        "both",
        "horizontal",
        "vertical",
    ]
    assert [prototype.episode_difficulty(seed) for seed in range(9)] == [
        "easy",
        "easy",
        "easy",
        "medium",
        "medium",
        "medium",
        "hard",
        "hard",
        "hard",
    ]
    for setting in prototype.SETTINGS:
        assert {
            prototype.episode_difficulty(seed)
            for seed in range(9)
            if prototype.choose_setting(seed) == setting
        } == {"easy", "medium", "hard"}
    assert prototype.choose_setting(99, "horizontal") == "horizontal"

    for bad in (None, True, 1, 1.0, "both ", "diagonal"):
        with pytest.raises((TypeError, ValueError)):
            prototype.validate_setting(bad)
    for bad_seed in (True, 1.5, "1", -1):
        with pytest.raises((TypeError, ValueError)):
            prototype.choose_setting(bad_seed)


def test_python_rule_matches_hand_checked_axis_outputs():
    grid = _expand(INPUT_COARSE)
    parent, _, _ = load_selected_generator(TASK_ID, root=find_root(__file__))
    assert parent.self_check(grid) == []
    assert parent.strict_canonical_like(grid) == []

    expected = {
        "both": _expand(BOTH_COARSE),
        "horizontal": _expand(HORIZONTAL_COARSE),
        "vertical": _expand(VERTICAL_COARSE),
    }
    actual = {
        setting: prototype.apply_python(grid, setting)
        for setting in prototype.SETTINGS
    }
    assert actual == expected
    assert len({json.dumps(value) for value in actual.values()}) == 3


def test_default_racket_program_is_exact_canonical_and_edits_fail_closed():
    canonical = _canonical_program()
    assert prototype.racket_program("both") == canonical
    alternatives = {
        setting: prototype.racket_program(setting)
        for setting in ("horizontal", "vertical")
    }
    assert all(source.startswith("(rule! (lambda (g)") for source in alternatives.values())
    assert all(source != canonical for source in alternatives.values())
    assert alternatives["horizontal"] != alternatives["vertical"]

    with pytest.raises(ValueError, match="edit point"):
        prototype._derive_alternative_program(
            canonical.replace("same-color marker", "same-colour marker", 1),
            "horizontal",
        )


def test_complete_episode_has_three_demos_four_distinct_queries_and_is_identifiable():
    episode = prototype.build_episode(
        17,
        connection_axes="vertical",
        demo_count=3,
        query_count=4,
    )
    assert episode["parameter"] == {
        "name": "connection_axes",
        "value": "vertical",
        "default": "both",
    }
    assert episode["seed"] == 17
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 4

    pairs = episode["train"] + episode["test"]
    inputs = [pair["input"] for pair in pairs]
    assert len({json.dumps(grid, separators=(",", ":")) for grid in inputs}) == 7

    parent, _, _ = load_selected_generator(TASK_ID, root=find_root(__file__))
    for pair in pairs:
        assert parent.self_check(pair["input"]) == []
        assert pair["output"] == prototype.apply_python(pair["input"], "vertical")
        outputs = {
            setting: prototype.apply_python(pair["input"], setting)
            for setting in prototype.SETTINGS
        }
        assert len({json.dumps(value) for value in outputs.values()}) == 3

    assert prototype.surviving_settings(episode["train"]) == ["vertical"]


def test_episode_count_validation_rejects_bool_zero_and_excessive_requests():
    for field, bad in (
        ("demo_count", True),
        ("demo_count", 0),
        ("demo_count", 17),
        ("query_count", False),
        ("query_count", 0),
        ("query_count", 17),
    ):
        kwargs = {"demo_count": 3, "query_count": 4, field: bad}
        with pytest.raises((TypeError, ValueError)):
            prototype.build_episode(0, **kwargs)


def test_public_projection_and_identifier_depend_only_on_visible_challenge_bytes():
    episode = prototype.build_episode(2, demo_count=3, query_count=4)
    public = prototype.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])

    encoded = json.dumps(public, sort_keys=True)
    for forbidden in ("connection_axes", "vertical", "prototype_version", "racket_program"):
        assert forbidden not in encoded

    identifier = prototype.public_identifier(episode)
    assert identifier == f"episode-{public_challenge_id(public)}.json"
    assert re.fullmatch(r"episode-[0-9a-f]{64}\.json", identifier)

    mutated_private = dict(episode)
    mutated_private["seed"] = 999999
    mutated_private["parameter"] = dict(episode["parameter"], value="horizontal")
    mutated_private["racket_program"] = "private mutation"
    assert prototype.public_identifier(mutated_private) == identifier



def test_verifier_builds_racket_backed_private_and_public_evidence(tmp_path):
    verifier = TASK_HOME / "workspace" / "parametric" / "verify.py"
    evidence = tmp_path / "evidence"
    env = dict(os.environ)
    command = [
        sys.executable,
        str(verifier),
        "--out",
        str(evidence),
        "--start-seed",
        "100",
        "--demo-count",
        "3",
        "--query-count",
        "4",
    ]

    completed = subprocess.run(
        command,
        cwd=TASK_HOME,
        env=env,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr

    report = json.loads((evidence / "report.json").read_text())
    assert report["status"] == "passed_bounded_prototype_evidence"
    assert report["prototype_status"] == "proposed_unapproved"
    assert report["parameter"] == {
        "name": "connection_axes",
        "default": "both",
        "allowed": ["both", "horizontal", "vertical"],
    }
    assert report["counts"] == {"demos_per_episode": 3, "queries_per_episode": 4}
    assert len(report["episodes"]) == 3
    identifiers = [row["public_identifier"] for row in report["episodes"]]
    assert identifiers == sorted(identifiers)
    assert len(set(identifiers)) == 3
    assert len({row["difficulty"] for row in report["episodes"]}) == 1

    canonical = prototype.canonical_program(root=find_root(__file__))
    assert (evidence / "private" / "rules" / "rule-both.rkt").read_text() == canonical

    for episode in report["episodes"]:
        assert episode["all_labels_executed_by_racket"] is True
        assert episode["surviving_settings"] == [episode["setting"]]
        assert set(episode["demo_disagreement_counts"]) == {
            setting for setting in prototype.SETTINGS if setting != episode["setting"]
        }
        assert all(count == 3 for count in episode["demo_disagreement_counts"].values())
        assert all(
            set(row["disagrees_with"]) == {
                setting for setting in prototype.SETTINGS if setting != episode["setting"]
            }
            for row in episode["queries"]
        )

    public_files = sorted((evidence / "public").glob("*.json"))
    assert len(public_files) == 3
    assert all(re.fullmatch(r"episode-[0-9a-f]{64}\.json", path.name) for path in public_files)
    for path in public_files:
        public = json.loads(path.read_text())
        assert set(public) == {"train", "test"}
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert all(set(pair) == {"input"} for pair in public["test"])
        encoded = path.read_text()
        assert "connection_axes" not in encoded
        assert "racket_program" not in encoded

    witness = json.loads((evidence / "private" / "same-input-disagreement.json").read_text())
    assert set(witness["outputs"]) == set(prototype.SETTINGS)
    assert len({json.dumps(value) for value in witness["outputs"].values()}) == 3

    manifest = json.loads((evidence / "manifest.json").read_text())
    listed = set(manifest["files"])
    assert "report.json" in listed
    assert "private/rules/rule-both.rkt" in listed
    assert {path.relative_to(evidence).as_posix() for path in public_files} <= listed

    before = (evidence / "report.json").read_bytes()
    repeated = subprocess.run(
        command,
        cwd=TASK_HOME,
        env=env,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert repeated.returncode != 0
    assert (evidence / "report.json").read_bytes() == before


def test_primary_writer_physically_emits_public_files_in_visible_id_order(tmp_path, monkeypatch):
    verifier_path = PROTOTYPE_PATH.with_name("verify.py")
    spec = importlib.util.spec_from_file_location("connection_axes_order_verifier", verifier_path)
    verifier = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "prototype", prototype)
    spec.loader.exec_module(verifier)
    writes = []
    original = Path.write_bytes
    def record(path, payload):
        if path.parent.name == "public":
            writes.append(path.name)
        return original(path, payload)
    monkeypatch.setattr(Path, "write_bytes", record)
    monkeypatch.setattr(prototype, "SETTINGS", tuple(reversed(prototype.SETTINGS)))
    verifier.build_evidence(tmp_path / "ordered", start_seed=31, demo_count=1, query_count=1)
    assert len(writes) == 3
    assert writes == sorted(writes)
