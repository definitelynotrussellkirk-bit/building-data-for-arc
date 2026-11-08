"""Focused tests for the proposed, unapproved nearest/farthest prototype."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import shutil
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, canonical_path, find_root

ROOT = find_root(__file__)
TASK_ID = "424c822d69f3"
PROTOTYPE_PATH = ROOT / f"generators/{TASK_ID}/workspace/parametric/prototype.py"
VERIFIER_PATH = ROOT / f"generators/{TASK_ID}/workspace/parametric/verify_evidence.py"
CANONICAL_SOURCE_SHA256 = "1379212df45efd44f4bb6d4cafca92b9588442bfc83807ed5d926d3048ccade5"


def _load_prototype():
    assert PROTOTYPE_PATH.is_file(), "parametric prototype has not been implemented"
    spec = importlib.util.spec_from_file_location("parametric_424c822d69f3", PROTOTYPE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_verifier():
    assert VERIFIER_PATH.is_file(), "retained evidence verifier has not been implemented"
    return _load_module(VERIFIER_PATH, "verify_parametric_424c822d69f3")


def _write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _refresh_manifest_hash(out: Path, relative: str) -> None:
    manifest_path = out / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    digest = hashlib.sha256((out / relative).read_bytes()).hexdigest()
    for row in manifest["files"]:
        if row["path"] == relative:
            row["sha256"] = digest
            break
    else:
        raise AssertionError(relative)
    _write_json(manifest_path, manifest)


def _canonical_source() -> str:
    sources = {
        row["program_solution"]
        for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines()
        if line.strip()
        if (row := json.loads(line)).get("task_id") == TASK_ID
    }
    assert len(sources) == 1
    source = sources.pop()
    assert hashlib.sha256(source.encode()).hexdigest() == CANONICAL_SOURCE_SHA256
    return source


def test_default_rule_is_exact_canonical_and_farthest_is_reversible():
    prototype = _load_prototype()
    canonical = _canonical_source()

    nearest = prototype.materialize_rule("nearest", root=ROOT)
    farthest = prototype.materialize_rule("farthest", root=ROOT)

    assert nearest == canonical
    assert hashlib.sha256(nearest.encode()).hexdigest() == CANONICAL_SOURCE_SHA256
    assert farthest != canonical
    assert prototype.restore_canonical(farthest) == canonical


@pytest.mark.parametrize("mode", [True, 1, "closest", None])
def test_invalid_selection_modes_are_rejected(mode):
    prototype = _load_prototype()
    with pytest.raises(ValueError):
        prototype.materialize_rule(mode, root=ROOT)


def test_materialization_rejects_source_drift():
    prototype = _load_prototype()
    canonical = _canonical_source()
    with pytest.raises(ValueError, match="canonical source SHA256"):
        prototype.materialize_rule("nearest", source=canonical + "\n")


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge() as runtime:
        yield runtime


def test_default_rule_reproduces_every_labeled_canonical_pair(bridge):
    prototype = _load_prototype()
    source = prototype.materialize_rule("nearest", root=ROOT)
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 4
    for pair in pairs:
        assert prototype.execute_rule(source, pair["input"], bridge=bridge) == pair["output"]


def _episode_inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_paired_episode_seeds_share_inputs_and_fix_one_mode_for_all_pairs(bridge):
    prototype = _load_prototype()
    nearest = prototype.make_episode(0, root=ROOT, bridge=bridge)
    farthest = prototype.make_episode(1, root=ROOT, bridge=bridge)

    assert nearest["parameters"] == {"selection_mode": "nearest"}
    assert farthest["parameters"] == {"selection_mode": "farthest"}
    assert nearest["input_seed"] == farthest["input_seed"] == 0
    assert nearest["counts"] == farthest["counts"] == {
        "demonstrations": 3,
        "queries": 4,
    }

    nearest_inputs = _episode_inputs(nearest)
    farthest_inputs = _episode_inputs(farthest)
    assert nearest_inputs == farthest_inputs
    assert len(nearest_inputs) == 7
    assert len({json.dumps(grid, separators=(",", ":")) for grid in nearest_inputs}) == 7

    for near_pair, far_pair in zip(
        nearest["train"] + nearest["test"],
        farthest["train"] + farthest["test"],
    ):
        assert near_pair["output"] != far_pair["output"]

    for episode in (nearest, farthest):
        assert episode["ambiguities"] == []
        matching = [
            row for row in episode["parameter_rivals"]
            if row["status"] == "matches_episode"
        ]
        refuted = [
            row for row in episode["parameter_rivals"]
            if row["status"] == "refuted_by_demonstrations"
        ]
        assert [row["selection_mode"] for row in matching] == [
            episode["parameters"]["selection_mode"]
        ]
        assert len(refuted) == 1
        assert refuted[0]["demonstration_mismatch_indices"] == [0, 1, 2]
        assert refuted[0]["query_mismatch_indices"] == [0, 1, 2, 3]
        assert len(episode["input_provenance"]) == 7
        assert all(row["nearest_unique"] for row in episode["input_provenance"])
        assert all(row["farthest_unique"] for row in episode["input_provenance"])


def test_every_episode_label_is_reexecuted_by_its_fixed_racket_rule(bridge):
    prototype = _load_prototype()
    for seed in (0, 1):
        episode = prototype.make_episode(seed, root=ROOT, bridge=bridge)
        source = prototype.materialize_rule(
            episode["parameters"]["selection_mode"], root=ROOT
        )
        for pair in episode["train"] + episode["test"]:
            assert prototype.execute_rule(source, pair["input"], bridge=bridge) == pair["output"]


def test_demo_and_query_counts_are_independent(bridge):
    prototype = _load_prototype()
    episode = prototype.make_episode(
        2,
        demo_count=2,
        query_count=5,
        root=ROOT,
        bridge=bridge,
    )
    assert len(episode["train"]) == 2
    assert len(episode["test"]) == 5
    assert episode["counts"] == {"demonstrations": 2, "queries": 5}
    assert len({json.dumps(grid) for grid in _episode_inputs(episode)}) == 7
    rival = next(
        row for row in episode["parameter_rivals"]
        if row["selection_mode"] != episode["parameters"]["selection_mode"]
    )
    assert rival["demonstration_mismatch_indices"] == [0, 1]
    assert rival["query_mismatch_indices"] == [0, 1, 2, 3, 4]


@pytest.mark.parametrize("seed", [True, -1, 1.0, "1", 2**63])
def test_invalid_episode_seeds_are_rejected(seed):
    prototype = _load_prototype()
    with pytest.raises(ValueError):
        prototype.make_episode(seed, root=ROOT)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"demo_count": 0},
        {"query_count": 0},
        {"demo_count": True},
        {"query_count": 1.0},
        {"demo_count": 9},
        {"query_count": 9},
    ],
)
def test_invalid_episode_counts_are_rejected(kwargs):
    prototype = _load_prototype()
    with pytest.raises(ValueError):
        prototype.make_episode(0, root=ROOT, **kwargs)


def test_sampler_stops_after_its_candidate_budget():
    prototype = _load_prototype()

    class AlwaysTiedGenerator:
        @staticmethod
        def generate(seed, sample_index):
            grid = [[0] * 7 for _ in range(7)]
            grid[0][1], grid[0][5] = 2, 8
            for row in (3, 4):
                for col in (2, 3, 4):
                    grid[row][col] = 5
            return grid

        @staticmethod
        def self_check(grid):
            return []

    with pytest.raises(RuntimeError, match="after 3 candidates"):
        prototype._collect_inputs(
            AlwaysTiedGenerator(),
            input_seed=0,
            count=1,
            max_attempts=3,
        )


def test_public_projection_hides_settings_programs_seeds_and_all_query_answers(bridge):
    prototype = _load_prototype()
    episode = prototype.make_episode(0, root=ROOT, bridge=bridge)
    public = prototype.public_challenge(episode)

    assert set(public) == {"train", "test"}
    assert len(public["train"]) == 3
    assert len(public["test"]) == 4
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    serialized = json.dumps(public, sort_keys=True)
    for forbidden in (
        "selection_mode",
        "parameters",
        "seed",
        "racket",
        "program",
        "input_provenance",
        "parameter_rivals",
    ):
        assert forbidden not in serialized


def test_public_id_depends_only_on_exact_visible_bytes(bridge):
    prototype = _load_prototype()
    episode = prototype.make_episode(0, root=ROOT, bridge=bridge)
    changed_private = copy.deepcopy(episode)
    for index, pair in enumerate(changed_private["test"]):
        pair["output"] = [[index]]
    changed_private["seed"] = 999
    changed_private["parameters"] = {"selection_mode": "private-only-change"}

    assert prototype.public_bytes(episode) == prototype.public_bytes(changed_private)
    assert prototype.public_id(episode) == prototype.public_id(changed_private)


def test_duplicate_visible_challenges_are_rejected(bridge):
    prototype = _load_prototype()
    episode = prototype.make_episode(0, root=ROOT, bridge=bridge)
    with pytest.raises(ValueError, match="duplicate visible challenge"):
        prototype._public_records([episode, copy.deepcopy(episode)])


def test_evidence_writer_retains_sorted_hash_valid_public_and_private_artifacts(tmp_path):
    prototype = _load_prototype()
    out = tmp_path / "nearest-farthest"
    report = prototype.write_evidence((0, 1), out=out, root=ROOT)

    assert report["status"] == "proposed_unapproved"
    assert report["counts"] == {
        "episodes": 2,
        "settings_exercised": 2,
        "demonstrations_per_episode": 3,
        "queries_per_episode": 4,
        "ambiguous_parameter_rivals": 0,
        "canonical_pairs_checked": 4,
        "canonical_pair_mismatches": 0,
    }
    assert [row["public_id"] for row in report["episodes"]] == sorted(
        row["public_id"] for row in report["episodes"]
    )
    assert {row["selection_mode"] for row in report["episodes"]} == {
        "nearest",
        "farthest",
    }
    assert len(report["rules"]) == 2

    for row in report["episodes"]:
        public_path = out / row["public_path"]
        private_path = out / row["private_path"]
        private = json.loads(private_path.read_text(encoding="utf-8"))
        assert public_path.name == f'{row["public_id"]}.json'
        assert public_path.read_bytes() == prototype.public_bytes(private)
        assert "output" not in json.loads(public_path.read_text())["test"][0]
        assert "output" in private["test"][0]

    for row in report["files"]:
        path = out / row["path"]
        assert path.is_file(), row["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"]

    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["prototype_version"] == prototype.VERSION
    for row in manifest["files"]:
        path = out / row["path"]
        assert path.is_file(), row["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"]


@pytest.mark.parametrize("seeds", [(), (0, 0), (True,), (-1,)])
def test_evidence_writer_rejects_empty_duplicate_or_invalid_seed_sets(tmp_path, seeds):
    prototype = _load_prototype()
    with pytest.raises(ValueError):
        prototype.write_evidence(seeds, out=tmp_path / "bad", root=ROOT)


def test_retained_evidence_verifier_reexecutes_every_label_and_canonical_pair(tmp_path):
    prototype = _load_prototype()
    verifier = _load_verifier()
    out = tmp_path / "evidence"
    prototype.write_evidence((0, 1), out=out, root=ROOT)

    result = verifier.verify_evidence(out, root=ROOT)

    assert result == {
        "status": "verified",
        "episodes": 2,
        "labels_reexecuted": 14,
        "canonical_pairs_reexecuted": 4,
        "manifest_files_verified": 13,
    }


def test_retained_evidence_verifier_rejects_a_hash_valid_but_changed_public_file(tmp_path):
    prototype = _load_prototype()
    verifier = _load_verifier()
    out = tmp_path / "evidence"
    report = prototype.write_evidence((0, 1), out=out, root=ROOT)
    public_path = out / report["episodes"][0]["public_path"]
    public = json.loads(public_path.read_text(encoding="utf-8"))
    public["test"][0]["input"][0][0] = (public["test"][0]["input"][0][0] + 1) % 10
    public_path.write_text(
        json.dumps(public, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    relative = public_path.relative_to(out).as_posix()
    report_path = out / "report.json"
    current_report = json.loads(report_path.read_text(encoding="utf-8"))
    public_digest = hashlib.sha256(public_path.read_bytes()).hexdigest()
    for row in current_report["files"]:
        if row["path"] == relative:
            row["sha256"] = public_digest
            break
    else:
        raise AssertionError(relative)
    _write_json(report_path, current_report)
    _refresh_manifest_hash(out, relative)
    _refresh_manifest_hash(out, "report.json")

    with pytest.raises(ValueError, match="public projection|public ID"):
        verifier.verify_evidence(out, root=ROOT)




def test_retained_evidence_verifier_rejects_same_version_prototype_source_drift(tmp_path):
    prototype = _load_prototype()
    out = tmp_path / "evidence"
    prototype.write_evidence((0, 1), out=out, root=ROOT)

    tool = tmp_path / "drifted-tool"
    tool.mkdir()
    shutil.copy2(PROTOTYPE_PATH, tool / "prototype.py")
    shutil.copy2(VERIFIER_PATH, tool / "verify_evidence.py")
    with (tool / "prototype.py").open("a", encoding="utf-8") as stream:
        stream.write("\n# same-version semantic drift\n")
    drifted = _load_module(tool / "verify_evidence.py", "drifted_parametric_verifier")

    with pytest.raises(ValueError, match="prototype source does not match retained snapshot"):
        drifted.verify_evidence(out, root=ROOT)


def test_retained_evidence_verifier_rejects_hash_valid_report_count_tamper(tmp_path):
    prototype = _load_prototype()
    verifier = _load_verifier()
    out = tmp_path / "evidence"
    prototype.write_evidence((0, 1), out=out, root=ROOT)
    report_path = out / "report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["counts"]["queries_per_episode"] += 1
    _write_json(report_path, report)
    _refresh_manifest_hash(out, "report.json")

    with pytest.raises(ValueError, match="query count"):
        verifier.verify_evidence(out, root=ROOT)


def test_retained_evidence_verifier_rejects_hash_valid_generator_binding_tamper(tmp_path):
    prototype = _load_prototype()
    verifier = _load_verifier()
    out = tmp_path / "evidence"
    report = prototype.write_evidence((0, 1), out=out, root=ROOT)
    private_relative = report["episodes"][0]["private_path"]
    private_path = out / private_relative
    private = json.loads(private_path.read_text(encoding="utf-8"))
    private["source_bindings"]["generator_sha256"] = "0" * 64
    _write_json(private_path, private)

    report_path = out / "report.json"
    current_report = json.loads(report_path.read_text(encoding="utf-8"))
    private_digest = hashlib.sha256(private_path.read_bytes()).hexdigest()
    for row in current_report["files"]:
        if row["path"] == private_relative:
            row["sha256"] = private_digest
            break
    else:
        raise AssertionError(private_relative)
    _write_json(report_path, current_report)
    _refresh_manifest_hash(out, private_relative)
    _refresh_manifest_hash(out, "report.json")

    with pytest.raises(ValueError, match="generator source binding"):
        verifier.verify_evidence(out, root=ROOT)


def test_retained_evidence_verifier_rejects_hash_valid_incomplete_report_file_index(tmp_path):
    prototype = _load_prototype()
    verifier = _load_verifier()
    out = tmp_path / "evidence"
    prototype.write_evidence((0, 1), out=out, root=ROOT)
    report_path = out / "report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["files"].pop()
    _write_json(report_path, report)
    _refresh_manifest_hash(out, "report.json")

    with pytest.raises(ValueError, match="report file inventory"):
        verifier.verify_evidence(out, root=ROOT)

def test_retained_evidence_verifier_rejects_an_untracked_nested_manifest_name(tmp_path):
    prototype = _load_prototype()
    verifier = _load_verifier()
    out = tmp_path / "evidence"
    prototype.write_evidence((0, 1), out=out, root=ROOT)
    nested = out / "private/untracked/manifest.json"
    nested.parent.mkdir(parents=True)
    nested.write_text('{"not":"declared"}\n', encoding="utf-8")

    with pytest.raises(ValueError, match="manifest inventory mismatch"):
        verifier.verify_evidence(out, root=ROOT)
