from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import re
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_ROOT = REPO_ROOT / "shared/runtime"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

PROTOTYPE_PATH = (
    REPO_ROOT
    / "generators/8eb9146172f8/workspace/parametric/prototype.py"
)


def test_prototype_file_exists():
    """Catches a missing deliverable rather than silently testing production only."""
    assert PROTOTYPE_PATH.is_file()


def _load_prototype():
    spec = importlib.util.spec_from_file_location(
        "parametric_deflection_distance_8eb9146172f8", PROTOTYPE_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def proto():
    return _load_prototype()


def _single_ray_input() -> list[list[int]]:
    grid = [[0] * 9 for _ in range(9)]
    grid[0][2] = 8
    grid[3][0] = 2
    grid[6][0] = 2
    return grid


def _expected_single_ray(distance: int) -> list[list[int]]:
    grid = _single_ray_input()
    columns = ([2, 2, 2, 3, 3, 3, 4, 4, 4]
               if distance == 1
               else [2, 2, 2, 4, 4, 4, 6, 6, 6])
    for row, col in enumerate(columns):
        grid[row][col] = 8
    return grid


def test_default_materialization_is_exact_canonical_source(proto):
    canonical = proto.canonical_rule()
    assert proto.materialize_rule() == canonical
    assert proto.materialize_rule(1) == canonical
    assert proto.normalized_rule_hash(canonical) == "5592536df499"


def test_materialization_rejects_nonliteral_and_unsupported_distances(proto):
    for bad in (True, 0, 3, 1.0, "1", None):
        with pytest.raises(ValueError, match="deflection_distance"):
            proto.materialize_rule(bad)


def test_real_racket_executes_both_hand_checked_distances(proto):
    source_grid = _single_ray_input()
    for distance in (1, 2):
        output = proto.execute_rule(
            proto.materialize_rule(distance), [source_grid]
        )[0]
        assert output == _expected_single_ray(distance)


@pytest.fixture(scope="module")
def evidence_bundle(proto, tmp_path_factory):
    out = tmp_path_factory.mktemp("deflection-distance") / "evidence"
    result = proto.write_evidence(
        out=out,
        seed=101,
        settings=(2, 1),
        demo_count=2,
        query_count=4,
        start=30,
        difficulty="medium",
    )
    manifest = json.loads((out / "manifest.json").read_text())
    episodes = {}
    for row in manifest["episodes"]:
        episode = json.loads((out / row["private_path"]).read_text())
        episodes[episode["parameters"]["deflection_distance"]] = episode
    return {"out": out, "result": result, "manifest": manifest, "episodes": episodes}


def test_episode_has_fixed_identifiable_setting_and_four_distinct_queries(evidence_bundle):
    episode = evidence_bundle["episodes"][2]
    assert episode["parameters"] == {"deflection_distance": 2}
    assert len(episode["train"]) == 2
    assert len(episode["test"]) == 4
    assert episode["rivals"]["consistent_settings"] == [2]
    assert episode["rivals"]["rival_demo_mismatches"] == [0, 1]
    assert episode["rivals"]["rival_query_mismatches"] == [0, 1, 2, 3]

    all_inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
    serialized = [json.dumps(grid, separators=(",", ":")) for grid in all_inputs]
    assert len(serialized) == len(set(serialized)) == 6
    assert all(pair["output"] for pair in episode["test"])


def test_demo_and_query_counts_are_independent(evidence_bundle):
    manifest = evidence_bundle["manifest"]
    assert manifest["demo_count"] == 2
    assert manifest["query_count"] == 4
    assert all(row["demo_count"] == 2 for row in manifest["episodes"])
    assert all(row["query_count"] == 4 for row in manifest["episodes"])


def test_public_identifier_uses_only_visible_bytes(proto, evidence_bundle):
    episode = evidence_bundle["episodes"][1]
    original_bytes = proto.public_bytes(episode)
    original_id = proto.public_id(episode)
    assert original_id == proto.digest(original_bytes)

    private_only = copy.deepcopy(episode)
    private_only["seed"] = 999999
    private_only["parameters"]["deflection_distance"] = 2
    private_only["test"][0]["output"][0][0] = (
        private_only["test"][0]["output"][0][0] + 1
    ) % 10
    assert proto.public_bytes(private_only) == original_bytes
    assert proto.public_id(private_only) == original_id

    visible_change = copy.deepcopy(episode)
    visible_change["train"][0]["output"][0][0] = (
        visible_change["train"][0]["output"][0][0] + 1
    ) % 10
    assert proto.public_id(visible_change) != original_id



def test_public_projection_does_not_alias_private_episode(proto, evidence_bundle):
    episode = evidence_bundle["episodes"][1]
    before = copy.deepcopy(episode)
    public = proto.public_challenge(episode)
    public["train"][0]["input"][0][0] = 9
    public["train"][0]["output"][0][0] = 9
    public["test"][0]["input"][0][0] = 9
    assert episode == before

def test_writer_keeps_public_files_opaque_and_private_answers_separate(evidence_bundle):
    out = evidence_bundle["out"]
    public_files = sorted((out / "public").glob("challenge-*.json"))
    assert len(public_files) == 2
    assert len({path.name for path in public_files}) == 2
    for path in public_files:
        assert re.fullmatch(r"challenge-[0-9a-f]{64}\.json", path.name)
        text = path.read_text()
        assert "deflection_distance" not in text
        assert '"output"' in text  # demonstrations remain labeled
        public = json.loads(text)
        assert all("output" not in pair for pair in public["test"])

    assert evidence_bundle["result"]["status"] == "ok"
    manifest = evidence_bundle["manifest"]
    assert len(manifest["episodes"]) == 2
    public_ids = [row["public_id"] for row in manifest["episodes"]]
    assert public_ids == sorted(public_ids)
    assert all(row["query_count"] == 4 for row in manifest["episodes"])


def test_independent_loop_mirror_matches_hand_witness_and_exact_racket(proto):
    from reviewer_support import load_selected_generator
    gen, _, _ = load_selected_generator("8eb9146172f8", root=REPO_ROOT)
    grids = [_single_ray_input()] + [gen.generate(31, i, difficulty="medium") for i in range(4)]
    for distance in (1, 2):
        expected = proto.execute_rule(proto.materialize_rule(distance), grids)
        assert [proto.apply_python(grid, distance) for grid in grids] == expected
        assert proto.apply_python(_single_ray_input(), distance) == _expected_single_ray(distance)
