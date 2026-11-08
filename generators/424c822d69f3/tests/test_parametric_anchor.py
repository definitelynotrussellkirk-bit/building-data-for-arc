"""Focused tests for the task-local rectangle-anchor parametric prototype."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root

TASK_DIR = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)
ROOT_PARAMETRIC = TASK_DIR / "workspace" / "parametric"
PARAMETRIC = ROOT_PARAMETRIC / "bbox_anchor"
PROTOTYPE_PATH = PARAMETRIC / "prototype.py"
ORACLE_PATH = PARAMETRIC / "oracle.py"


def _load(name: str, path: Path):
    if not path.is_file():
        pytest.fail(f"missing implementation file: {path.relative_to(ROOT)}")
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    ledger = canonical_path(ROOT)
    rows = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()]
    matches = [row["program_solution"] for row in rows if row.get("task_id") == "424c822d69f3"]
    assert len(matches) == 1
    return matches[0]


def _grid(markers: dict[int, int], c0: int, c1: int, *, width: int = 10):
    grid = [[0] * width for _ in range(5)]
    for col, color in markers.items():
        grid[0][col] = color
    for row in (2, 3):
        for col in range(c0, c1 + 1):
            grid[row][col] = 5
    return grid


def test_rule_materialization_preserves_exact_canonical_default_and_changes_only_anchor():
    prototype = _load("anchor_prototype_rules", PROTOTYPE_PATH)
    canonical = _canonical_program()
    old = "(center (/ (+ (second bb) (fourth bb)) 2))"

    assert prototype.rule_text("midpoint") == canonical
    assert prototype.rule_text("left_edge") == canonical.replace(old, "(center (second bb))")
    assert prototype.rule_text("right_edge") == canonical.replace(old, "(center (fourth bb))")
    assert canonical.count(old) == 1


@pytest.mark.parametrize("value", [None, "center", "left", 0, True])
def test_invalid_anchor_values_fail_loudly(value):
    prototype = _load("anchor_prototype_invalid", PROTOTYPE_PATH)
    with pytest.raises((TypeError, ValueError)):
        prototype.rule_text(value)


def test_prototype_domain_rejects_tie_under_any_declared_anchor():
    prototype = _load("anchor_prototype_domain", PROTOTYPE_PATH)
    # Midpoint/left are uniquely nearest to col 0; right edge at col 2 ties cols 0 and 4.
    grid = _grid({0: 1, 4: 2}, 1, 2, width=5)
    errors = prototype.prototype_domain_errors(grid)
    assert any("right_edge" in reason and "tie" in reason.lower() for reason in errors)


def test_independent_oracle_exposes_both_parameter_witness_types_without_mutation():
    oracle = _load("anchor_independent_oracle", ORACLE_PATH)

    # Left edge chooses marker 0, while midpoint and right edge choose marker 6.
    left_witness = _grid({0: 1, 6: 2, 9: 3}, 2, 6)
    original = deepcopy(left_witness)
    left_outputs = {anchor: oracle.independent_output(left_witness, anchor)
                    for anchor in ("midpoint", "left_edge", "right_edge")}
    assert left_outputs["midpoint"] == left_outputs["right_edge"]
    assert left_outputs["left_edge"] != left_outputs["midpoint"]
    assert left_witness == original

    # Right edge chooses marker 9, while midpoint and left edge choose marker 3.
    right_witness = _grid({0: 1, 3: 2, 9: 3}, 4, 7)
    right_outputs = {anchor: oracle.independent_output(right_witness, anchor)
                     for anchor in ("midpoint", "left_edge", "right_edge")}
    assert right_outputs["midpoint"] == right_outputs["left_edge"]
    assert right_outputs["right_edge"] != right_outputs["midpoint"]


@pytest.fixture(scope="module")
def parametric_module():
    return _load("anchor_parametric_full", PROTOTYPE_PATH)


@pytest.fixture(scope="module")
def three_setting_episodes(parametric_module):
    with parametric_module.RuleEngine() as engine:
        episodes = [
            parametric_module.generate_episode(
                17, anchor=anchor, demos=3, queries=4, max_attempts=512, engine=engine
            )
            for anchor in parametric_module.ANCHORS
        ]
    return episodes


def test_input_selection_is_deterministic_identifying_and_query_rich(parametric_module):
    first = parametric_module.select_inputs(17, demos=3, queries=4, max_attempts=512)
    second = parametric_module.select_inputs(17, demos=3, queries=4, max_attempts=512)
    assert first == second
    assert len(first["train"]) == 3
    assert len(first["test"]) == 4
    assert {row["witness_kind"] for row in first["train"]} >= {
        "left_edge_witness", "right_edge_witness"
    }
    assert all(row["witness_kind"] in {"left_edge_witness", "right_edge_witness"}
               for row in first["test"])
    assert {row["witness_kind"] for row in first["test"]} == {
        "left_edge_witness", "right_edge_witness"
    }
    identifiers = [parametric_module.digest(row["input"])
                   for row in first["train"] + first["test"]]
    assert len(identifiers) == len(set(identifiers)) == 7


def test_three_setting_episodes_share_inputs_and_have_racket_checked_identifiable_labels(
    parametric_module, three_setting_episodes
):
    sample_indices = [episode["accepted_sample_indices"] for episode in three_setting_episodes]
    assert sample_indices[0] == sample_indices[1] == sample_indices[2]
    assert [episode["anchor"] for episode in three_setting_episodes] == list(parametric_module.ANCHORS)

    public_ids = set()
    for episode in three_setting_episodes:
        assert episode["schema"] == "rectangle-anchor-parametric-prototype-v1"
        assert episode["status"] == "proposed"
        assert episode["demo_count"] == 3
        assert episode["query_count"] == 4
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 4
        assert len(episode["label_checks"]) == 7
        assert all(row["independent_oracle_match"] for row in episode["label_checks"])
        assert all(row["racket_executed"] for row in episode["label_checks"])
        assert all(report["status"] == "identified_within_declared_anchors"
                   for report in episode["query_identification"])
        assert all(report["consistent_anchors"] == [episode["anchor"]]
                   for report in episode["query_identification"])
        assert all(report["query_answer_used_for_demo_fit"] is False
                   for report in episode["query_identification"])
        public_ids.add(parametric_module.public_id(episode))
    assert len(public_ids) == 3


@pytest.mark.parametrize(
    "kwargs",
    [
        {"seed": True}, {"seed": -1}, {"demos": True}, {"demos": 1},
        {"queries": 0}, {"queries": 3}, {"queries": 5}, {"queries": 1.0}, {"max_attempts": False},
        {"max_attempts": 0}, {"anchor": "center"},
    ],
)
def test_episode_api_rejects_invalid_numeric_and_setting_boundaries(parametric_module, kwargs):
    call = {"seed": 0, "anchor": "midpoint", "demos": 2, "queries": 4, "max_attempts": 64}
    call.update(kwargs)
    with pytest.raises((TypeError, ValueError)):
        parametric_module.generate_episode(**call)


def test_sampling_budget_exhaustion_is_explicit(parametric_module):
    with pytest.raises(RuntimeError, match="sampling budget exhausted"):
        parametric_module.select_inputs(17, demos=3, queries=4, max_attempts=1)


def test_empty_demonstrations_remain_ambiguous_without_hidden_setting(parametric_module):
    selection = parametric_module.select_inputs(17, demos=2, queries=4, max_attempts=512)
    with parametric_module.RuleEngine() as engine:
        report = parametric_module.identify_query([], selection["test"][0]["input"], engine=engine)
    assert report["status"] == "ambiguous_within_declared_anchors"
    assert report["consistent_anchors"] == list(parametric_module.ANCHORS)
    assert report["query_answer_used_for_demo_fit"] is False


def test_public_projection_hides_private_semantics_and_ignores_query_answers(
    parametric_module, three_setting_episodes
):
    episode = deepcopy(three_setting_episodes[0])
    visible = parametric_module.public_payload(episode)
    serialized = json.dumps(visible, sort_keys=True)
    assert episode["anchor"] not in serialized
    assert episode["program_solution"] not in serialized
    assert all(set(pair) == {"input"} for pair in visible["test"])

    original_id = parametric_module.public_id(episode)
    episode["seed"] = 999999
    episode["anchor"] = "left_edge"
    episode["test"][0]["output"][0][0] = (episode["test"][0]["output"][0][0] + 1) % 10
    assert parametric_module.public_id(episode) == original_id


def test_writer_uses_visible_hash_names_and_rejects_duplicate_or_mutated_labels_before_write(
    parametric_module, three_setting_episodes, tmp_path
):
    episode = three_setting_episodes[1]
    destination = tmp_path / "valid"
    saved = parametric_module.write_episodes(destination, [episode])
    assert len(saved) == 1
    public_path = Path(saved[0]["public_path"])
    assert public_path.name == parametric_module.public_id(episode) + ".json"
    assert json.loads(public_path.read_text(encoding="utf-8")) == parametric_module.public_payload(episode)
    assert episode["anchor"] not in public_path.name

    duplicate_destination = tmp_path / "duplicate"
    with pytest.raises(ValueError, match="duplicate visible payload"):
        parametric_module.write_episodes(duplicate_destination, [episode, deepcopy(episode)])
    assert not duplicate_destination.exists()

    mutated = deepcopy(episode)
    mutated["test"][0]["output"][2][2] = (mutated["test"][0]["output"][2][2] + 1) % 10
    rejected_destination = tmp_path / "mutated"
    with pytest.raises(ValueError, match="label mismatch"):
        parametric_module.write_episodes(rejected_destination, [mutated])
    assert not rejected_destination.exists()


def test_promotion_adapter_declares_bounded_anchor_family(parametric_module):
    adapter_path = PARAMETRIC / "adapter.py"
    promotion_path = PARAMETRIC / "promotion.json"
    adapter = _load("anchor_promotion_adapter", adapter_path)
    promotion = json.loads(promotion_path.read_text(encoding="utf-8"))

    assert promotion == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/424c822d69f3/workspace/parametric/bbox_anchor/adapter.py",
        "parameters": {"anchor": ["midpoint", "left_edge", "right_edge"]},
        "default": {"anchor": "midpoint"},
        "limits": {"demos": [2, 6], "queries": [4, 4]},
    }
    assert adapter.program({"anchor": "midpoint"}) == _canonical_program()
    generated = adapter.generate(23, {"anchor": "right_edge"}, 2, 4)
    assert generated["anchor"] == "right_edge"
    assert len(generated["train"]) == 2
    assert len(generated["test"]) == 4


def test_canonical_exact_source_guard_rejects_whitespace_drift(monkeypatch):
    prototype = _load("anchor_exact_drift", PROTOTYPE_PATH)
    canonical = _canonical_program()
    monkeypatch.setattr(prototype, "canonical_rows", lambda: ({"program_solution": canonical + "\n"},))
    prototype.canonical_program.cache_clear()
    with pytest.raises(ValueError, match="exact|SHA"):
        prototype.canonical_program()


def test_writer_rejects_empty_batches_before_creating_destination(tmp_path):
    prototype = _load("anchor_empty_writer", PROTOTYPE_PATH)
    destination = tmp_path / "empty"
    with pytest.raises(ValueError, match="empty"):
        prototype.write_episodes(destination, [])
    assert not destination.exists()


def test_anchor_exports_use_shared_visible_bytes_and_refuse_existing_destination(
    parametric_module, three_setting_episodes, tmp_path,
):
    from reviewer_support import public_challenge_bytes

    episode = three_setting_episodes[0]
    destination = tmp_path / "canonical-bytes"
    saved = parametric_module.write_episodes(destination, [episode])
    public_path = Path(saved[0]["public_path"])
    assert public_path.read_bytes() == public_challenge_bytes(parametric_module.public_payload(episode))
    with pytest.raises(FileExistsError):
        parametric_module.write_episodes(destination, [episode])


def test_anchor_adapter_rejects_unknown_or_missing_setting_keys():
    adapter = _load("anchor_strict_adapter", PARAMETRIC / "adapter.py")
    for settings in ({}, {"anchor": "midpoint", "extra": 1}, None):
        with pytest.raises(ValueError, match="exactly anchor"):
            adapter.program(settings)


def test_native_root_promotion_contract_is_narrow_and_preserves_canonical_default():
    adapter = _load("anchor_native_root_adapter", ROOT_PARAMETRIC / "adapter.py")
    promotion = json.loads((ROOT_PARAMETRIC / "promotion.json").read_text(encoding="utf-8"))
    assert promotion == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/424c822d69f3/workspace/parametric/adapter.py",
        "parameters": {"anchor": ["midpoint", "left_edge", "right_edge"]},
        "default": {"anchor": "midpoint"},
        "limits": {"demos": [2, 6], "queries": [4, 4]},
    }
    assert adapter.program({"anchor": "midpoint"}) == _canonical_program()
    episode = adapter.generate(23, {"anchor": "right_edge"}, 2, 4)
    assert len(episode["train"]) == 2
    assert len(episode["test"]) == 4
    assert episode["program_solution"] == adapter.program({"anchor": "right_edge"})


def test_native_root_adapter_rejects_non_four_query_requests():
    adapter = _load("anchor_native_root_adapter_counts", ROOT_PARAMETRIC / "adapter.py")
    for queries in (1, 3, 5):
        with pytest.raises((TypeError, ValueError), match="queries"):
            adapter.generate(0, {"anchor": "midpoint"}, 3, queries)


@pytest.mark.parametrize("demos", range(2, 7))
def test_selection_supports_every_native_demo_count_and_exactly_four_queries(parametric_module, demos):
    selected = parametric_module.select_inputs(71 + demos, demos=demos, queries=4, max_attempts=512)
    assert len(selected["train"]) == demos
    assert len(selected["test"]) == 4
    assert len({parametric_module.digest(row["input"]) for row in selected["train"] + selected["test"]}) == demos + 4


def test_every_episode_reserves_a_substantive_30x30_boundary_query(parametric_module):
    selected = parametric_module.select_inputs(17, demos=3, queries=4, max_attempts=512)
    stress = [row for row in selected["test"] if len(row["input"]) == 30 and len(row["input"][0]) == 30]
    assert len(stress) == 1
    grid = stress[0]["input"]
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 5]
    assert len(cells) >= 120
    assert any(c == 0 for _r, c in cells)
    assert any(c == 29 for _r, c in cells)
    assert any(r == 29 for r, _c in cells)
    assert parametric_module.prototype_domain_errors(grid) == []
    assert stress[0]["witness_kind"] in {"left_edge_witness", "right_edge_witness"}
