"""Task-local prototype tests; separate from canonical-generator repair coverage."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import subprocess
import sys

import pytest

from reviewer_support import canonical_path, find_root

ROOT = find_root(__file__)
SOURCE = Path(__file__).resolve().parents[1] / "workspace/parametric/prototype.py"
SETTINGS = [
    {"scan_order": "row_major", "pick": "last"},
    {"scan_order": "row_major", "pick": "first"},
    {"scan_order": "column_major", "pick": "last"},
    {"scan_order": "column_major", "pick": "first"},
]
# Eight occupied zones; distinct first/last values on every edge strip.
WITNESS = [
    [9, 6, 0, 0, 0, 5, 8],
    [5, 0, 0, 1, 0, 0, 4],
    [7, 2, 0, 0, 0, 3, 6],
    [6, 0, 0, 4, 0, 0, 2],
    [5, 2, 0, 0, 0, 8, 0],
]


def load_prototype():
    assert SOURCE.is_file(), "the requested runnable parametric prototype is missing"
    spec = importlib.util.spec_from_file_location("zone_parametric_prototype", SOURCE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def prototype():
    return load_prototype()


@pytest.fixture(scope="module")
def oracle(prototype):
    with prototype.RacketOracle() as runner:
        yield runner


def input_key(grid):
    return tuple(tuple(row) for row in grid)


def public_tree(root):
    return {
        str(p.relative_to(root)): p.read_bytes()
        for p in root.rglob("*") if p.is_file()
    }


def test_canonical_default_exact_source_and_all_six_pairs():
    prototype = load_prototype()
    row = next(
        json.loads(line)
        for line in canonical_path(ROOT).read_text().splitlines()
        if json.loads(line)["task_id"] == "9df67b512dad"
    )
    assert prototype.program() == row["program_solution"]
    pairs = row["train"] + row["test"]
    assert len(pairs) == 6
    with prototype.RacketOracle() as oracle:
        for pair in pairs:
            before = copy.deepcopy(pair["input"])
            assert oracle.label(pair["input"]) == pair["output"]
            assert pair["input"] == before
        assert oracle.runtime_identity["protected"] is True


@pytest.mark.parametrize("settings,center", list(zip(SETTINGS, (4, 1, 3, 2))))
def test_real_racket_reduction_selects_hand_checked_witness(prototype, oracle, settings, center):
    if settings["pick"] == "first":
        expected = [[9, 6, 8], [5, center, 4], [5, 2, 0]]
    else:
        expected = [[9, 5, 8], [6, center, 2], [5, 8, 0]]
    assert oracle.label(WITNESS, settings) == expected


def test_paired_inputs_four_fixed_rules_and_every_label_replayed(prototype, oracle):
    episodes = [
        prototype.generate_episode(31 + index, settings=settings, input_seed=509, oracle=oracle)
        for index, settings in enumerate(SETTINGS)
    ]
    inputs = [[p["input"] for p in e["train"] + e["test"]] for e in episodes]
    assert inputs[1:] == [inputs[0]] * 3
    assert len({prototype.program(setting) for setting in SETTINGS}) == 4
    for settings, episode in zip(SETTINGS, episodes):
        assert len(episode["train"]) == 2
        assert len(episode["test"]) == 4
        private = episode["_private"]
        assert private["settings"] == settings
        assert private["program_sha256"] == hashlib.sha256(prototype.program(settings).encode()).hexdigest()
        assert private["demonstration_certificate"]["survivors"] == [settings]
        assert private["demonstration_certificate"]["global_occupancy_survives"] is False
        assert len({input_key(p["input"]) for p in episode["train"] + episode["test"]}) == 6
        for pair in episode["train"] + episode["test"]:
            prototype.validate_input(pair["input"])
            assert pair["output"] == oracle.label(pair["input"], settings)
    for pair_index in range(6):
        assert len({
            (e["train"] + e["test"])[pair_index]["output"][1][1]
            for e in episodes
        }) == 4


def test_determinism_fresh_grids_and_no_global_random_state_mutation(prototype, oracle):
    random.seed(901)
    before = random.getstate()
    first = prototype.generate_episode(77, oracle=oracle)
    second = prototype.generate_episode(77, oracle=oracle)
    assert first == second
    assert random.getstate() == before
    assert first is not second
    assert first["train"][0]["input"] is not second["train"][0]["input"]
    first["train"][0]["input"][0][0] = 0 if second["train"][0]["input"][0][0] else 1
    assert first != second
    other = prototype.generate_episode(78, oracle=oracle)
    assert [p["input"] for p in other["test"]] != [p["input"] for p in second["test"]]


@pytest.mark.parametrize("demos,queries", [(1, 8), (8, 1), (8, 8)])
def test_separate_count_boundaries_and_distinctness(prototype, oracle, demos, queries):
    episode = prototype.generate_episode(97, demos=demos, queries=queries, oracle=oracle)
    assert (len(episode["train"]), len(episode["test"])) == (demos, queries)
    assert len({input_key(p["input"]) for p in episode["train"] + episode["test"]}) == demos + queries


@pytest.mark.parametrize("kwargs", [
    {"seed": True}, {"seed": 1.0}, {"seed": "1"}, {"seed": -1}, {"seed": 2**63},
    {"input_seed": False}, {"input_seed": -1}, {"input_seed": 2.5},
    {"demos": True}, {"demos": 0}, {"demos": 9}, {"demos": 2.0}, {"demos": "2"},
    {"queries": False}, {"queries": 0}, {"queries": 9}, {"queries": 4.0}, {"queries": "4"},
    {"settings": {"scan_order": "diagonal", "pick": "last"}},
    {"settings": {"scan_order": "row_major", "pick": "middle"}},
    {"settings": {"scan_order": "row_major"}},
    {"settings": {"scan_order": "row_major", "pick": "last", "extra": 1}},
    {"settings": ["row_major", "last"]},
])
def test_strict_literal_arguments(prototype, kwargs):
    args = {"seed": 1, **kwargs}
    with pytest.raises(ValueError):
        prototype.generate_episode(**args)


@pytest.mark.parametrize("kind", ["bool", "float", "string", "ragged", "tuple", "empty", "small", "large", "color"])
def test_rejects_nonliteral_or_out_of_domain_grids(prototype, oracle, kind):
    grid = copy.deepcopy(WITNESS)
    if kind == "bool":
        grid[0][0] = True
    elif kind == "float":
        grid[0][0] = 1.0
    elif kind == "string":
        grid[0][0] = "1"
    elif kind == "ragged":
        grid[1].pop()
    elif kind == "tuple":
        grid[1] = tuple(grid[1])
    elif kind == "empty":
        grid = []
    elif kind == "small":
        grid = [[0] * 6 for _ in range(4)]
    elif kind == "large":
        grid = [[0] * 17 for _ in range(15)]
    else:
        grid[0][0] = 10
    with pytest.raises(ValueError):
        oracle.label(grid)


def test_demo_only_inference_rejects_monochrome_counterexample(prototype, oracle):
    mono = [[3 if value else 0 for value in row] for row in WITNESS]
    demos = [{"input": mono, "output": [[3, 3, 3], [3, 3, 3], [3, 3, 0]]}]
    certificate = prototype.infer_from_demonstrations(demos, oracle=oracle)
    assert certificate["survivors"] == SETTINGS
    assert certificate["global_occupancy_survives"] is True
    with pytest.raises(ValueError, match="underidentified"):
        prototype.require_identifiable(demos, SETTINGS[0], oracle=oracle)
    for settings in SETTINGS:
        identified = [{"input": WITNESS, "output": oracle.label(WITNESS, settings)}]
        certificate = prototype.require_identifiable(identified, settings, oracle=oracle)
        assert certificate["survivors"] == [settings]
        assert certificate["global_occupancy_survives"] is False


def test_writer_uses_visible_hash_bytes_and_order_independent_public_index(prototype, oracle, tmp_path):
    episodes = [prototype.generate_episode(13, settings=s, input_seed=44, oracle=oracle) for s in SETTINGS]
    first, second = tmp_path / "first", tmp_path / "second"
    prototype.write_export(episodes, first, oracle=oracle)
    altered = copy.deepcopy(episodes)
    for episode in altered:
        episode["_private"]["seed"] = 999
        episode["_private"]["reviewer_note"] = "private metadata must not name public files"
    prototype.write_export(list(reversed(altered)), second, oracle=oracle)
    assert public_tree(first / "public") == public_tree(second / "public")
    index = json.loads((first / "public/index.json").read_text())
    assert index == sorted(index)
    assert len(index) == 4
    for episode in episodes:
        public_id = prototype.public_challenge_id(episode)
        path = first / "public" / f"{public_id}.json"
        visible_bytes = path.read_bytes()
        assert visible_bytes == prototype.public_challenge_bytes(episode)
        assert hashlib.sha256(visible_bytes).hexdigest() == public_id
        visible = json.loads(visible_bytes)
        assert set(visible) == {"train", "test"}
        assert all(set(pair) == {"input", "output"} for pair in visible["train"])
        assert all(set(pair) == {"input"} for pair in visible["test"])
        private = json.loads((first / "private/episodes" / f"{public_id}.json").read_text())
        source = private["_private"]["program_solution"]
        rule_path = first / "private/rules" / f"{private['_private']['program_sha256']}.rkt"
        assert rule_path.read_text() == source
        assert private["test"] == episode["test"]
        mutated = copy.deepcopy(episode)
        mutated["_private"] = {"settings": "altered", "seed": 123, "program_solution": "wrong"}
        mutated["test"][0]["output"] = [[0]]
        assert prototype.public_challenge_bytes(mutated) == visible_bytes
        assert prototype.public_challenge_id(mutated) == public_id


def test_writer_rejects_duplicate_visible_payload_before_creating_destination(prototype, oracle, tmp_path):
    episode = prototype.generate_episode(14, oracle=oracle)
    duplicate = copy.deepcopy(episode)
    duplicate["_private"]["seed"] = 999
    out = tmp_path / "duplicates"
    with pytest.raises(ValueError, match="duplicate visible"):
        prototype.write_export([episode, duplicate], out, oracle=oracle)
    assert not out.exists()


def test_writer_checks_demo_identifiability_before_query_labels(prototype, oracle, tmp_path):
    episode = prototype.generate_episode(15, oracle=oracle)
    mono = [[3 if value else 0 for value in row] for row in WITNESS]
    episode["train"] = [{"input": mono, "output": [[3, 3, 3], [3, 3, 3], [3, 3, 0]]}]
    # Deliberately invalid query label: the demo-only failure must win first.
    episode["test"][0]["output"] = [["not a color"]]
    with pytest.raises(ValueError, match="underidentified"):
        prototype.write_export([episode], tmp_path / "ambiguous", oracle=oracle)
    assert not (tmp_path / "ambiguous").exists()


def test_writer_replays_query_labels_and_refuses_existing_destination(prototype, oracle, tmp_path):
    episode = prototype.generate_episode(16, oracle=oracle)
    changed = copy.deepcopy(episode)
    changed["test"][0]["output"][1][1] = 0
    with pytest.raises(ValueError, match="query.*Racket"):
        prototype.write_export([changed], tmp_path / "bad-label", oracle=oracle)
    assert not (tmp_path / "bad-label").exists()
    valid = tmp_path / "valid"
    prototype.write_export([episode], valid, oracle=oracle)
    before = public_tree(valid)
    with pytest.raises(FileExistsError):
        prototype.write_export([episode], valid, oracle=oracle)
    assert public_tree(valid) == before


def test_cli_exports_four_complete_episodes(prototype, tmp_path):
    out = tmp_path / "cli"
    completed = subprocess.run([
        sys.executable, str(SOURCE), "--all-settings", "--seed", "23",
        "--input-seed", "91", "--demos", "2", "--queries", "4", "--out", str(out),
    ], cwd=tmp_path, capture_output=True, text=True, timeout=60)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    result = json.loads(completed.stdout)
    assert result["episodes"] == 4
    assert result["demonstrations"] == 8
    assert result["queries"] == 16
    manifest = json.loads((out / "private/manifest.json").read_text())
    assert len(manifest["episodes"]) == 4
    assert len(manifest["programs"]) == 4
    assert manifest["status"] == "prototype"
    assert len(manifest["source_sha256"]) >= 1


@pytest.mark.parametrize("field,value", [
    ("seed", "missing"), ("input_seed", "missing"),
    ("seed", None), ("seed", True), ("seed", 1.5), ("seed", "23"),
    ("seed", -1), ("seed", 2**63),
    ("input_seed", None), ("input_seed", False), ("input_seed", 1.5),
    ("input_seed", "91"), ("input_seed", -1), ("input_seed", 2**63),
    ("settings", None), ("settings", "missing"),
])
def test_writer_rejects_malformed_private_provenance_before_creation(
        prototype, oracle, tmp_path, field, value):
    episode = prototype.generate_episode(4381, demos=1, queries=1, oracle=oracle)
    if value == "missing":
        del episode["_private"][field]
    else:
        episode["_private"][field] = value
    out = tmp_path / "malformed-private"
    with pytest.raises(ValueError):
        prototype.write_export([episode], out, oracle=oracle)
    assert not out.exists()


def test_writer_refreshes_source_provenance_after_racket_replay(prototype, oracle, tmp_path):
    episode = prototype.generate_episode(19, demos=1, queries=1, oracle=oracle)
    episode["_private"]["source_sha256"] = {"forged-source.py": "0" * 64}
    out = tmp_path / "refreshed-provenance"
    prototype.write_export([episode], out, oracle=oracle)
    manifest = json.loads((out / "private/manifest.json").read_text())
    exported = json.loads(next((out / "private/episodes").glob("*.json")).read_text())
    assert exported["_private"]["source_sha256"] == manifest["source_sha256"]
    assert exported["_private"]["source_sha256"][str(SOURCE.relative_to(ROOT))] == hashlib.sha256(SOURCE.read_bytes()).hexdigest()
