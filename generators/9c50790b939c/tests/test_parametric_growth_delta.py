"""Focused tests for the proposed episode-level growth-delta prototype."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import shutil
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    find_root,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "9c50790b939c"
ROOT = find_root(__file__)
PROTOTYPE_PATH = (
    ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
)
GENERATOR_PATH = ROOT / "generators" / TASK_ID / "generator.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def prototype():
    return _load(PROTOTYPE_PATH, f"parametric_{TASK_ID}")


@pytest.fixture(scope="module")
def generator():
    return _load(GENERATOR_PATH, f"generator_{TASK_ID}_parametric_test")


def _canonical_row() -> dict:
    path = ROOT / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError("canonical row not found")


def test_default_rule_is_exact_pinned_canonical_source(prototype, generator):
    canonical = prototype.canonical_source(root=ROOT)
    assert prototype.DEFAULT_GROWTH_DELTA == 1
    assert prototype.materialize_rule(1, source=canonical) == canonical
    assert prototype.normalized_hash(canonical) == generator.RULE_HASH


def test_alternatives_change_only_the_output_growth_constant(prototype):
    canonical = prototype.canonical_source(root=ROOT)
    for delta in (0, 2):
        alternative = prototype.materialize_rule(delta, source=canonical)
        assert alternative != canonical
        replacement = prototype.block_length_form(delta)
        assert alternative.count(replacement) == 1
        assert (
            alternative.replace(
                replacement,
                prototype.block_length_form(prototype.DEFAULT_GROWTH_DELTA),
                1,
            )
            == canonical
        )


@pytest.mark.parametrize("bad", [None, True, -1, 3, 1.0, "1"])
def test_materialize_rule_rejects_undeclared_settings(prototype, bad):
    with pytest.raises((TypeError, ValueError), match="growth_delta"):
        prototype.materialize_rule(bad, root=ROOT)


def test_seed_choice_is_deterministic_and_covers_all_declared_values(prototype):
    first = [prototype.parameters_for_seed(seed) for seed in range(128)]
    second = [prototype.parameters_for_seed(seed) for seed in range(128)]
    assert first == second
    assert {row["growth_delta"] for row in first} == set(
        prototype.ALLOWED_GROWTH_DELTAS
    )


def test_all_racket_settings_execute_and_disagree_on_one_lawful_input(
    prototype, generator
):
    grid = generator.generate(20261022, 7, difficulty="medium")
    canonical = prototype.canonical_source(root=ROOT)
    sources = {
        delta: prototype.materialize_rule(delta, source=canonical)
        for delta in prototype.ALLOWED_GROWTH_DELTAS
    }
    with RacketBridge() as bridge:
        outputs = {
            delta: prototype.execute_rule(source, grid, bridge=bridge)
            for delta, source in sources.items()
        }
    assert len({repr(output) for output in outputs.values()}) == len(outputs)


def test_complete_episode_teaches_its_fixed_parameter_and_public_form_is_clean(
    prototype,
):
    with RacketBridge() as bridge:
        episodes = [
            prototype.make_episode(
                prototype.find_seed_for_growth_delta(delta),
                root=ROOT,
                bridge=bridge,
            )
            for delta in prototype.ALLOWED_GROWTH_DELTAS
        ]
    assert {episode["parameters"]["growth_delta"] for episode in episodes} == set(
        prototype.ALLOWED_GROWTH_DELTAS
    )
    for episode in episodes:
        chosen = episode["parameters"]["growth_delta"]
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 4
        assert len({pair["input_sha256"] for pair in episode["test"]}) == 4
        assert len(
            {pair["input_sha256"] for pair in (*episode["train"], *episode["test"])}
        ) == 7
        assert episode["status"] == "proposed_unapproved"
        assert episode["approved"] is False
        assert all(pair["growth_delta"] == chosen for pair in episode["train"])
        assert all(pair["growth_delta"] == chosen for pair in episode["test"])
        assert episode["ambiguities"] == []
        assert all(
            rival["status"] == "refuted_by_demonstrations"
            for rival in episode["parameter_rivals"]
        )

        public = prototype.public_challenge(copy.deepcopy(episode))
        assert set(public) == {"train", "test"}
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert all(set(pair) == {"input"} for pair in public["test"])
        serialized = repr(public)
        for forbidden in (
            "growth_delta",
            "parameters",
            "racket_source",
            "racket_sha256",
            "seed",
        ):
            assert forbidden not in serialized


def test_canonical_default_replays_all_labeled_canonical_pairs(prototype):
    source = prototype.materialize_rule(1, root=ROOT)
    row = _canonical_row()
    pairs = [*row["train"], *row["test"]]
    with RacketBridge() as bridge:
        for pair in pairs:
            assert prototype.execute_rule(source, pair["input"], bridge=bridge) == pair[
                "output"
            ]


def test_public_export_plan_uses_visible_ids_and_rejects_duplicate_payloads(
    prototype,
):
    with RacketBridge() as bridge:
        episodes = [
            prototype.make_episode(
                prototype.find_seed_for_growth_delta(delta),
                root=ROOT,
                bridge=bridge,
            )
            for delta in prototype.ALLOWED_GROWTH_DELTAS
        ]

    forward = prototype.public_export_plan(episodes)
    reverse = prototype.public_export_plan(list(reversed(episodes)))
    assert [row["public_id"] for row in forward] == [
        row["public_id"] for row in reverse
    ]
    assert [row["public_id"] for row in forward] == sorted(
        row["public_id"] for row in forward
    )
    for row in forward:
        assert row["public_id"] == public_challenge_id(row["episode"])
        assert row["public_bytes"] == public_challenge_bytes(row["episode"])

    changed_private = copy.deepcopy(episodes[0])
    changed_private["seed"] = 999999
    changed_private["parameters"] = {"growth_delta": 999}
    changed_private["racket_source"] = "private-change"
    changed_private["test"][0]["output"][0][0] = (
        changed_private["test"][0]["output"][0][0] + 1
    ) % 10
    assert public_challenge_id(changed_private) == public_challenge_id(episodes[0])

    changed_visible = copy.deepcopy(episodes[0])
    changed_visible["test"][0]["input"][0][0] = (
        changed_visible["test"][0]["input"][0][0] + 1
    ) % 10
    assert public_challenge_id(changed_visible) != public_challenge_id(episodes[0])

    with pytest.raises(ValueError, match="duplicate visible public payload"):
        prototype.public_export_plan([episodes[0], copy.deepcopy(episodes[0])])


def test_public_writer_uses_hash_filenames_and_removes_ordinal_stale_files(
    prototype, tmp_path
):
    with RacketBridge() as bridge:
        episodes = [
            prototype.make_episode(
                prototype.find_seed_for_growth_delta(delta),
                root=ROOT,
                bridge=bridge,
            )
            for delta in prototype.ALLOWED_GROWTH_DELTAS
        ]

    public_dir = tmp_path / "public"
    public_dir.mkdir()
    (public_dir / "episode-a.json").write_text("stale", encoding="utf-8")

    rows = prototype.write_public_challenges(
        episodes, public_dir.relative_to(tmp_path), root=tmp_path
    )
    expected_ids = sorted(public_challenge_id(episode) for episode in episodes)
    assert [row["public_id"] for row in rows] == expected_ids
    assert sorted(path.name for path in public_dir.glob("*.json")) == [
        f"{identifier}.json" for identifier in expected_ids
    ]
    assert not (public_dir / "episode-a.json").exists()

    episodes_by_id = {public_challenge_id(episode): episode for episode in episodes}
    for row in rows:
        public_path = tmp_path / row["public_path"]
        episode = episodes_by_id[row["public_id"]]
        assert public_path.read_bytes() == public_challenge_bytes(episode)
        assert row["sha256"] == row["public_id"]
        assert row["bytes"] == len(public_challenge_bytes(episode))
        visible = json.loads(public_path.read_text(encoding="utf-8"))
        assert visible == prototype.public_challenge(episode)
        assert all("output" not in pair for pair in visible["test"])
        serialized = public_path.read_text(encoding="utf-8")
        for forbidden in ("growth_delta", "parameters", "racket_source", "seed"):
            assert forbidden not in serialized

    assert prototype.public_export_files_match(episodes, rows, root=tmp_path) is True
    first_path = tmp_path / rows[0]["public_path"]
    first_path.write_text("{}\n", encoding="utf-8")
    assert prototype.public_export_files_match(episodes, rows, root=tmp_path) is False


def test_build_evidence_binds_source_files_to_the_explicit_root(prototype, tmp_path):
    relocated = tmp_path / "repo"
    relocated_task = relocated / "generators" / TASK_ID
    relocated_parametric = relocated_task / "workspace" / "parametric"
    relocated_rules = relocated_parametric / "rules"
    relocated_rules.mkdir(parents=True)
    shutil.copy2(GENERATOR_PATH, relocated_task / "generator.py")
    shutil.copy2(PROTOTYPE_PATH, relocated_parametric / "prototype.py")
    for rule in (PROTOTYPE_PATH.parent / "rules").glob("*.rkt"):
        shutil.copy2(rule, relocated_rules / rule.name)

    canonical_path = relocated / "shared" / "data" / "canonical" / "puzzles.jsonl"
    canonical_path.parent.mkdir(parents=True)
    canonical_path.write_text(json.dumps(_canonical_row()) + "\n", encoding="utf-8")

    report = prototype.build_evidence(root=relocated)
    bindings = report["source_bindings"]
    assert bindings["prototype"]["path"] == (
        f"generators/{TASK_ID}/workspace/parametric/prototype.py"
    )
    assert bindings["selected_generator"]["path"] == (
        f"generators/{TASK_ID}/generator.py"
    )
    assert bindings["canonical_data"]["path"] == (
        "shared/data/canonical/puzzles.jsonl"
    )
    for binding in bindings.values():
        path = relocated / binding["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == binding["sha256"]
    assert all(
        row["path"].startswith(f"generators/{TASK_ID}/workspace/parametric/rules/")
        for row in report["rules"].values()
    )


def test_evidence_exposes_separate_demo_query_counts_and_distinct_queries(prototype):
    report = prototype.build_evidence(root=ROOT)
    assert report["episode_shape"] == {
        "demonstration_count": 3,
        "query_count": 4,
        "demonstration_indices": [0, 1, 2],
        "query_indices": [3, 4, 5, 6],
    }
    assert report["checks"]["all_episode_pair_counts_match"] is True
    assert report["checks"]["all_query_inputs_distinct"] is True
    assert report["checks"]["all_queries_distinct_from_demonstrations"] is True
    assert any("seven-pair" in limit for limit in report["limitations"])
    assert all("four-pair" not in limit for limit in report["limitations"])
    assert report["checks"]["all_passed"] is True
