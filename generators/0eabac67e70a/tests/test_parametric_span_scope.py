from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"
TASK_ID = "0eabac67e70a"


def _load(name: str, path: Path):
    assert path.is_file(), f"missing planned parametric source: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def modules():
    prototype = _load("pair_span_scope_test_prototype", PARAMETRIC / "prototype.py")
    adapter = _load("pair_span_scope_test_adapter", PARAMETRIC / "adapter.py")
    return prototype, adapter


def canonical_program() -> str:
    root = HOME.parents[1]
    path = root / "shared" / "data" / "canonical" / "puzzles.jsonl"
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rows.append(row)
    programs = {row["program_solution"] for row in rows}
    assert len(programs) == 1
    return next(iter(programs))


def test_adapter_exposes_exact_canonical_default_and_distinct_alternative():
    _prototype, adapter = modules()
    canonical = adapter.program({"span_scope": "all_pairs"})
    alternative = adapter.program({"span_scope": "junction_cluster"})
    assert canonical == canonical_program()
    assert alternative != canonical
    assert alternative.strip().startswith("(rule!")


@pytest.mark.parametrize(
    "settings",
    [
        {},
        {"span_scope": "all_pairs", "extra": 1},
        {"span_scope": "unknown"},
        {"span_scope": True},
        None,
    ],
)
def test_adapter_rejects_undeclared_settings(settings):
    _prototype, adapter = modules()
    with pytest.raises((TypeError, ValueError), match="span_scope|settings"):
        adapter.program(settings)


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"seed": True, "demos": 2, "queries": 4}, "seed"),
        ({"seed": -1, "demos": 2, "queries": 4}, "seed"),
        ({"seed": 0, "demos": 1, "queries": 4}, "demos"),
        ({"seed": 0, "demos": 7, "queries": 4}, "demos"),
        ({"seed": 0, "demos": 2, "queries": 1}, "queries"),
        ({"seed": 0, "demos": 2, "queries": 5}, "queries"),
    ],
)
def test_episode_count_and_seed_boundaries(kwargs, message):
    _prototype, adapter = modules()
    with pytest.raises((TypeError, ValueError), match=message):
        adapter.generate(settings={"span_scope": "all_pairs"}, **kwargs)


def test_python_reference_outputs_match_hand_derived_fixture():
    prototype, _adapter = modules()
    grid = [
        [3, 0, 3, 0, 0, 0, 0],
        [0, 0, 0, 2, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 1, 0, 0, 0, 1, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 2, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
    ]
    all_pairs = [
        [8, 8, 8, 0, 0, 0, 0],
        [0, 0, 0, 8, 0, 0, 0],
        [0, 0, 0, 8, 0, 0, 0],
        [0, 8, 8, 8, 8, 8, 0],
        [0, 0, 0, 8, 0, 0, 0],
        [0, 0, 0, 8, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
    ]
    junction_cluster = [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 8, 0, 0, 0],
        [0, 0, 0, 8, 0, 0, 0],
        [0, 8, 8, 8, 8, 8, 0],
        [0, 0, 0, 8, 0, 0, 0],
        [0, 0, 0, 8, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
    ]
    assert prototype.validate_scene(grid) == []
    assert prototype.junction_of(grid) == (3, 3)
    assert prototype.output_for(grid, "all_pairs") == all_pairs
    assert prototype.output_for(grid, "junction_cluster") == junction_cluster


@pytest.mark.parametrize("seed", [0, 17, 2**31 + 9])
@pytest.mark.parametrize("demos", [2, 3, 6])
def test_generated_episodes_are_deterministic_distinct_and_setting_matched(seed, demos):
    prototype, adapter = modules()
    settings_a = {"span_scope": "all_pairs"}
    settings_b = {"span_scope": "junction_cluster"}
    first = adapter.generate(seed, settings_a, demos, 4)
    again = adapter.generate(seed, settings_a, demos, 4)
    alternative = adapter.generate(seed, settings_b, demos, 4)
    assert first == again
    inputs_a = [pair["input"] for split in ("train", "test") for pair in first[split]]
    inputs_b = [pair["input"] for split in ("train", "test") for pair in alternative[split]]
    assert inputs_a == inputs_b
    assert len({prototype.grid_digest(grid) for grid in inputs_a}) == demos + 4
    for pair_a, pair_b in zip(
        [pair for split in ("train", "test") for pair in first[split]],
        [pair for split in ("train", "test") for pair in alternative[split]],
    ):
        assert pair_a["output"] != pair_b["output"]
        assert prototype.validate_scene(pair_a["input"]) == []
        analysis = prototype.analyze_scene(pair_a["input"])
        assert len(analysis["junctions"]) == 1
        assert len(analysis["selected_colors"]) == 2


def test_query_schedule_covers_minimum_intermediate_large_and_30x30_stress():
    prototype, adapter = modules()
    episode = adapter.generate(23, {"span_scope": "junction_cluster"}, 2, 4)
    shapes = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert shapes == [(7, 7), (12, 16), (22, 26), (30, 30)]
    max_scene = prototype.analyze_scene(episode["test"][-1]["input"])
    assert len(max_scene["pairs"]) == 6
    assert sum(len(row) for row in max_scene["spans"]) >= 45
    assert len(max_scene["distractor_colors"]) == 4


def test_two_demo_teaching_core_refutes_declared_plausible_shortcuts():
    prototype, adapter = modules()
    for seed in range(12):
        episode = adapter.generate(seed, {"span_scope": "junction_cluster"}, 2, 4)
        audit = prototype.audit_teaching_set(episode["train"])
        assert audit["setting_survivors"] == ["junction_cluster"]
        assert set(audit["rivals"]) == {
            "fixed_first_demo_colors",
            "two_longest_spans",
            "two_shortest_spans",
            "two_center_nearest_spans",
        }
        assert all(row["refuted"] for row in audit["rivals"].values())


def test_promotion_contract_declares_two_settings_demo_range_and_four_queries():
    _prototype, _adapter = modules()
    contract = json.loads((PARAMETRIC / "promotion.json").read_text(encoding="utf-8"))
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/0eabac67e70a/workspace/parametric/adapter.py",
        "parameters": {"span_scope": ["all_pairs", "junction_cluster"]},
        "default": {"span_scope": "all_pairs"},
        "limits": {"demos": [2, 6], "queries": [4, 4]},
    }


def test_public_projection_hides_private_fields_and_reveals_only_requested_query():
    prototype, adapter = modules()
    verifier = _load("pair_span_scope_test_verify", PARAMETRIC / "verify.py")
    episode = adapter.generate(31, {"span_scope": "junction_cluster"}, 3, 4)
    episode["settings"] = {"span_scope": "junction_cluster"}
    episode["seed"] = 31
    projection = verifier.public_projection(episode, 2)
    assert set(projection) == {"train", "test"}
    assert len(projection["train"]) == 3
    assert len(projection["test"]) == 1
    assert projection["test"] == [{"input": episode["test"][2]["input"]}]
    assert projection["train"] == episode["train"]
    assert "output" not in projection["test"][0]
    serialized = json.dumps(projection, sort_keys=True)
    assert "program_solution" not in serialized
    assert "span_scope" not in serialized
    assert '"seed"' not in serialized
    assert prototype.grid_digest(projection["test"][0]["input"]) == prototype.grid_digest(
        episode["test"][2]["input"]
    )


def test_public_payload_and_id_are_invariant_to_private_metadata():
    _prototype, adapter = modules()
    verifier = _load("pair_span_scope_test_verify_invariance", PARAMETRIC / "verify.py")
    episode = adapter.generate(4, {"span_scope": "all_pairs"}, 2, 4)
    mutated = dict(episode)
    mutated["settings"] = {"span_scope": "private-change"}
    mutated["seed"] = 999999
    mutated["program_solution"] = "private replacement"
    assert verifier.public_payload(episode, 0) == verifier.public_payload(mutated, 0)
    assert verifier.public_id(episode, 0) == verifier.public_id(mutated, 0)


def test_public_batch_rejects_duplicate_visible_payload_before_creating_output(tmp_path):
    _prototype, adapter = modules()
    verifier = _load("pair_span_scope_test_verify_duplicates", PARAMETRIC / "verify.py")
    episode = adapter.generate(7, {"span_scope": "all_pairs"}, 3, 4)
    destination = tmp_path / "public"
    records = [
        {"seed": 7, "span_scope": "all_pairs", "episode": episode},
        {"seed": 7, "span_scope": "all_pairs", "episode": episode},
    ]
    with pytest.raises(ValueError, match="duplicate visible challenge"):
        verifier.write_public_projection_batch(records, destination)
    assert not destination.exists()


def test_evidence_builder_covers_settings_seeds_queries_and_teaching_core(tmp_path):
    _prototype, _adapter = modules()
    verifier = _load("pair_span_scope_test_verify_builder", PARAMETRIC / "verify.py")
    summary = verifier.build_evidence(tmp_path, seeds=(0, 17), demos=3)
    assert summary["status"] == "passed"
    assert summary["settings"] == ["all_pairs", "junction_cluster"]
    assert summary["seeds"] == [0, 17]
    assert summary["demonstrations"] == 3
    assert summary["queries_per_episode"] == 4
    assert summary["public_files"] == 16
    assert summary["teaching_audit"]["seeds_checked"] == 12
    assert summary["teaching_audit"]["demo_counts"] == [2, 3, 6]
    assert summary["teaching_audit"]["failures"] == []
    public_files = sorted((tmp_path / "public").glob("*.json"))
    assert len(public_files) == 16
    assert all(path.stem == verifier.sha256_bytes(path.read_bytes()) for path in public_files)
    index = json.loads((tmp_path / "projection-index.json").read_text(encoding="utf-8"))
    assert len(index["projections"]) == 16
    for row in index["projections"]:
        assert set(row) == {"public_id", "filename", "seed", "span_scope", "query_index"}
        assert 0 <= row["query_index"] < 4
