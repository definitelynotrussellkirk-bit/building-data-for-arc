"""Behavioral tests for the proposed outline/filled rectangle family."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

from arcpuzzles.parametric_worker import evaluate_contract
from reviewer_support import canonical_path, find_root, public_challenge_bytes


HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"
PROTOTYPE = PARAMETRIC / "prototype.py"
EPISODE_IO = PARAMETRIC / "episode_io.py"
CONTRACT = PARAMETRIC / "promotion.json"
TASK_ID = "a452b4b4f04a"


def _load(path: Path, name: str):
    assert path.is_file(), f"missing runnable artifact: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def p():
    return _load(PROTOTYPE, "a452_parametric_subject")


@pytest.fixture(scope="module")
def episode_io():
    return _load(EPISODE_IO, "a452_episode_io_subject")


def _inputs(episode):
    return [[pair["input"] for pair in episode[split]] for split in ("train", "test")]


def test_default_program_is_the_exact_selected_canonical_program(p):
    root = find_root(__file__)
    rows = [json.loads(line) for line in canonical_path(root).read_text().splitlines()]
    programs = {row["program_solution"] for row in rows if row.get("task_id") == TASK_ID}
    assert programs == {p.program({"render": "outline"})}


def test_settings_share_inputs_and_every_labeled_pair_distinguishes_render_mode(p):
    outline = p.generate(17, {"render": "outline"}, demos=2, queries=4)
    filled = p.generate(17, {"render": "filled"}, demos=2, queries=4)
    assert _inputs(outline) == _inputs(filled)
    assert len(outline["train"]) == 2 and len(outline["test"]) == 4
    for split in ("train", "test"):
        assert all(a["output"] != b["output"] for a, b in zip(outline[split], filled[split]))


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_demo_and_query_counts_are_independent_and_inputs_stay_distinct(p, demos):
    episode = p.generate(23, {"render": "outline"}, demos=demos, queries=4)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == 4
    encoded = [json.dumps(pair["input"], separators=(",", ":"))
               for split in ("train", "test") for pair in episode[split]]
    assert len(encoded) == len(set(encoded))


def test_first_public_turn_is_identical_for_one_and_four_query_requests(p):
    full = p.generate(29, {"render": "filled"}, demos=3, queries=4)
    one = p.generate(29, {"render": "filled"}, demos=3, queries=1)
    full_first = {"train": full["train"], "test": [{"input": full["test"][0]["input"]}]}
    assert public_challenge_bytes(full_first) == public_challenge_bytes(one)


def test_minimum_and_30_square_profiles_contain_real_rectangle_content(p):
    minimum = p.sample_input(5, "test", 0)
    large = p.sample_input(5, "test", 3)
    assert (len(minimum), len(minimum[0])) == (6, 6)
    assert (len(large), len(large[0])) == (30, 30)
    assert sum(cell != 0 for row in minimum for cell in row) >= 2
    # The large profile must distribute marker objects across the canvas, not pad one corner.
    quadrants = [
        sum(large[r][c] != 0 for r in rr for c in cc)
        for rr in (range(0, 15), range(15, 30))
        for cc in (range(0, 15), range(15, 30))
    ]
    assert all(count > 0 for count in quadrants)


def test_native_worker_executes_protected_racket_and_identifies_each_setting():
    root = find_root(__file__)
    contract = json.loads(CONTRACT.read_text())
    jobs = [
        {"seed": seed, "settings": {"render": render}, "demos": 2, "queries": 4}
        for seed in (0, 17) for render in ("outline", "filled")
    ]
    result = evaluate_contract(root, TASK_ID, contract, jobs)
    assert result["racket"]["backend"] == "racket"
    assert result["racket"]["protected"] is True
    assert result["racket_evaluations"] >= sum(job["demos"] + job["queries"] for job in jobs)
    assert [row["survivors"] for row in result["checks"]] == [[job["settings"]] for job in jobs]
    assert any(len(pair["input"]) == 30 and len(pair["input"][0]) == 30
               for episode in result["episodes"] for pair in episode["test"])


def test_probe_cli_creates_parent_and_writes_verified_report(tmp_path):
    root = find_root(__file__)
    output = tmp_path / "missing-parent" / "current"
    completed = subprocess.run(
        [sys.executable, str(PARAMETRIC / "probe.py"), "--out", str(output)],
        cwd=root,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0, completed.stderr
    report = json.loads((output / "report.json").read_text())
    assert report["bundle_verified"] is True
    assert [6, 6] in report["query_shapes"]
    assert [30, 30] in report["query_shapes"]
    assert report["racket"]["protected"] is True


@pytest.mark.parametrize("kwargs", [
    {"seed": True}, {"demos": 1}, {"demos": 7}, {"demos": 2.0},
    {"queries": 0}, {"queries": 5}, {"queries": True},
    {"settings": {"render": "border"}},
    {"settings": {"render": "outline", "extra": 1}},
])
def test_invalid_requests_are_rejected(p, kwargs):
    request = {"seed": 0, "settings": {"render": "outline"}, "demos": 3, "queries": 4}
    request.update(kwargs)
    with pytest.raises(ValueError):
        p.generate(**request)


def test_bundle_writer_hides_private_fields_and_verifier_detects_corruption(
    p, episode_io, tmp_path
):
    outline = p.generate(3, {"render": "outline"}, demos=2, queries=4)
    filled = p.generate(3, {"render": "filled"}, demos=2, queries=4)

    duplicate = tmp_path / "duplicate"
    with pytest.raises(ValueError, match="duplicate visible"):
        episode_io.write_bundle([outline, deepcopy(outline)], duplicate)
    assert not duplicate.exists()

    destination = tmp_path / "bundle"
    receipt = episode_io.write_bundle([outline, filled], destination)
    assert receipt["episodes"] == 2 and receipt["public_challenges"] == 8
    verified = episode_io.verify_bundle(destination)
    assert verified == receipt

    for path in sorted((destination / "public").glob("*.json")):
        raw = path.read_text()
        assert "outline" not in raw and "filled" not in raw and "program" not in raw
        value = json.loads(raw)
        assert set(value) == {"train", "test"}
        assert len(value["test"]) == 1
        assert set(value["test"][0]) == {"input"}

    private_rows = [json.loads(line) for line in (destination / "private.jsonl").read_text().splitlines()]
    assert {row["settings"]["render"] for row in private_rows} == {"outline", "filled"}
    assert all("answer" in row and "program" in row for row in private_rows)

    corrupt = sorted((destination / "public").glob("*.json"))[0]
    corrupt.write_text(corrupt.read_text() + " ")
    with pytest.raises(ValueError, match="hash"):
        episode_io.verify_bundle(destination)
