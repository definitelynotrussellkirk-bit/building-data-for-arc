"""Focused tests for the proposed stack-side extension; execute through Racket."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
PROTOTYPE = HOME / "workspace/parametric/prototype.py"


def _load():
    assert PROTOTYPE.is_file(), "The requested runnable parametric prototype is absent"
    spec = importlib.util.spec_from_file_location("block_stack_parametric_test", PROTOTYPE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def proto():
    return _load()


@pytest.fixture(scope="module")
def engine(proto):
    with proto.RuleEngine() as runtime:
        yield runtime


def _canonical_pairs(proto):
    unique = {}
    for row in proto.canonical_rows():
        for split in ("train", "test"):
            for pair in row[split]:
                unique.setdefault(json.dumps(pair["input"]), pair)
    return list(unique.values())


def _short_axis_reflect(grid):
    if len(grid) == 7:
        return [list(reversed(row)) for row in grid]
    return list(reversed(grid))


def _public_bytes_by_name(destination):
    public = Path(destination) / "public"
    return {path.name: path.read_bytes() for path in public.iterdir()}


def test_canonical_setting_executes_unchanged_authority_on_all_canonical_pairs(proto, engine):
    pairs = _canonical_pairs(proto)
    assert len(pairs) == 4
    for pair in pairs:
        assert engine.apply(pair["input"], "toward_main") == pair["output"]


def test_alternate_reflects_short_axis_without_reordering_long_axis(proto, engine):
    for pair in _canonical_pairs(proto):
        expected = _short_axis_reflect(pair["output"])
        assert expected != pair["output"]
        assert engine.apply(pair["input"], "toward_small") == expected
        assert proto.independent_output(pair["input"], "toward_small") == expected


@pytest.mark.parametrize("side", ("toward_main", "toward_small"))
def test_complete_four_query_episode_uses_fixed_setting_and_racket_labels(proto, engine, side):
    episode = proto.generate_episode(17, stack_side=side, demos=3, queries=4, engine=engine)
    assert episode["stack_side"] == side
    assert len(episode["train"]) == 3 and len(episode["test"]) == 4
    pairs = episode["train"] + episode["test"]
    assert len({json.dumps(p["input"]) for p in pairs}) == 7
    for pair in pairs:
        canonical = engine.apply(pair["input"], "toward_main")
        expected = canonical if side == "toward_main" else _short_axis_reflect(canonical)
        assert pair["output"] == expected
        assert pair["output"] == proto.independent_output(pair["input"], side)
    for query in episode["query_identification"]:
        assert query["consistent_settings"] == [side]
        assert query["status"] == "identified_within_declared_rivals"
        assert query["query_answer_used_for_demo_fit"] is False
        assert any(item["mismatching_demo_indices"] for item in query["rivals"])
    assert len(episode["label_checks"]) == 7


def test_rule_choice_and_inputs_are_deterministic_and_counts_are_independent(proto, engine):
    first = proto.generate_episode(29, demos=2, queries=4, engine=engine)
    same = proto.generate_episode(29, demos=2, queries=4, engine=engine)
    assert first == same
    changed = proto.generate_episode(29, demos=4, queries=1, engine=engine)
    assert changed["stack_side"] == first["stack_side"]
    assert (len(changed["train"]), len(changed["test"])) == (4, 1)
    assert first["train"] == changed["train"][:2]


@pytest.mark.parametrize("name,value,error", [
    ("demos", 0, ValueError), ("queries", 0, ValueError),
    ("demos", -1, ValueError), ("queries", 33, ValueError),
    ("demos", True, TypeError), ("queries", False, TypeError),
    ("demos", 3.0, TypeError), ("queries", "4", TypeError),
    ("seed", True, TypeError), ("seed", -1, ValueError),
    ("stack_side", "left", ValueError), ("max_attempts", 0, ValueError),
])
def test_invalid_controls_fail_before_execution(proto, name, value, error):
    arguments = {"seed": 17, "demos": 3, "queries": 4}
    arguments[name] = value
    with pytest.raises(error):
        proto.generate_episode(**arguments)


def test_sampling_budget_exhaustion_never_silently_reduces_query_count(proto):
    with pytest.raises(RuntimeError, match="sampling budget exhausted"):
        proto.generate_episode(17, demos=3, queries=4, max_attempts=2)


def test_demo_fit_never_reads_any_query_answer(proto, engine):
    episode = proto.generate_episode(17, stack_side="toward_small", engine=engine)
    query = episode["test"][0]["input"]
    before = copy.deepcopy(episode["train"])
    report = proto.identify_query(episode["train"], query, engine=engine)
    assert report["consistent_settings"] == ["toward_small"]
    assert episode["train"] == before
    # No answer is supplied by this API. With no demonstrations, both settings
    # remain feasible and their different query predictions expose ambiguity.
    ambiguous = proto.identify_query([], query, engine=engine)
    assert set(ambiguous["consistent_settings"]) == set(proto.STACK_SIDES)
    assert ambiguous["status"] == "ambiguous_within_declared_rivals"


def test_racket_backed_public_writer_omits_hidden_fields_and_query_labels(proto, engine, tmp_path):
    episode = proto.generate_episode(17, stack_side="toward_small", engine=engine)
    paths = proto.write_episode(tmp_path, episode, engine=engine)
    public_path = Path(paths["public_path"])
    public = json.loads(public_path.read_text())
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    expected = hashlib.sha256(json.dumps(public, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    assert public_path.name == expected + ".json"
    assert public_path.parent == tmp_path / "public"
    private = json.loads(Path(paths["private_path"]).read_text())
    assert len(private["test"]) == 4
    assert private["stack_side"] == "toward_small"
    assert len(private["label_checks"]) == 7
    for pair in private["train"] + private["test"]:
        assert pair["output"] == engine.apply(pair["input"], private["stack_side"])


def test_public_identity_and_export_are_invariant_to_every_hidden_field(proto, engine, tmp_path):
    episode = proto.generate_episode(17, stack_side="toward_main", engine=engine)
    first = proto.write_public_challenge(tmp_path, episode)
    original = first.read_bytes()
    changed = copy.deepcopy(episode)
    changed["seed"] = 987654321
    changed["stack_side"] = "toward_small"
    changed["program_solution"] = "PRIVATE RULE CANARY"
    changed["setting_ordinal"] = 999
    changed["private_canary"] = {"note": "PRIVATE METADATA CANARY"}
    for pair in changed["test"]:
        pair["output"] = [[9]]
    second = proto.write_public_challenge(tmp_path, changed)
    assert second == first and second.read_bytes() == original
    assert proto.public_id(changed) == proto.public_id(episode)
    visible_change = copy.deepcopy(episode)
    visible_change["train"][0]["output"][0][0] = 9
    assert proto.public_id(visible_change) != proto.public_id(episode)


def test_full_writer_rejects_query_label_corruption_before_export(proto, engine, tmp_path):
    episode = proto.generate_episode(17, stack_side="toward_main", engine=engine)
    episode["test"][2]["output"] = [[9]]
    with pytest.raises(ValueError, match="label mismatch"):
        proto.write_episode(tmp_path, episode, engine=engine)
    assert not (tmp_path / "public").exists()


def test_independent_oracle_counts_rings_not_color_area(proto, engine):
    for index in range(8):
        grid = proto.generator().generate(41, index)
        for side in proto.STACK_SIDES:
            output = engine.apply(grid, side)
            assert output == proto.independent_output(grid, side)
            assert len(output) == 7 or len(output[0]) == 7

def test_batch_writer_sorts_public_writes_by_visible_id_independent_of_input_order_and_private_metadata(
        proto, engine, tmp_path):
    toward_main = proto.generate_episode(17, stack_side="toward_main", engine=engine)
    toward_small = proto.generate_episode(17, stack_side="toward_small", engine=engine)
    expected_ids = sorted((proto.public_id(toward_main), proto.public_id(toward_small)))

    first_root = tmp_path / "first"
    first = proto.write_episodes(first_root, [toward_small, toward_main], engine=engine)

    changed_main = copy.deepcopy(toward_main)
    changed_main["seed"] = 987654321
    changed_main["setting_ordinal"] = 99
    changed_main["private_canary"] = {"setting": "main"}
    changed_small = copy.deepcopy(toward_small)
    changed_small["seed"] = 123456789
    changed_small["setting_ordinal"] = -4
    changed_small["private_canary"] = {"setting": "small"}
    second_root = tmp_path / "second"
    second = proto.write_episodes(second_root, [changed_main, changed_small], engine=engine)

    assert [row["public_id"] for row in first] == expected_ids
    assert [row["public_id"] for row in second] == expected_ids
    assert [Path(row["public_path"]).name for row in first] == [value + ".json" for value in expected_ids]
    assert [Path(row["public_path"]).name for row in second] == [value + ".json" for value in expected_ids]
    assert _public_bytes_by_name(first_root) == _public_bytes_by_name(second_root)


def test_batch_writer_rejects_duplicate_visible_payloads_before_any_write(proto, engine, tmp_path):
    episode = proto.generate_episode(17, stack_side="toward_main", engine=engine)
    duplicate = copy.deepcopy(episode)
    duplicate["seed"] = 19
    duplicate["private_canary"] = "different private metadata"

    with pytest.raises(ValueError, match="duplicate visible payload"):
        proto.write_episodes(tmp_path, [episode, duplicate], engine=engine)

    assert not (tmp_path / "public").exists()
    assert not (tmp_path / "private").exists()

