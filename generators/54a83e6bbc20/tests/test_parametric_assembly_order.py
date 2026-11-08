"""Independent checks of the isolated jigsaw assembly-order prototype.

Real Racket labels are required. These tests do not extend production approval
to either setting of the prototype or modify the selected generator's rule.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_path,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "54a83e6bbc20"
ROOT = find_root(__file__)
PROTOTYPE_PATH = Path(__file__).resolve().parents[1] / "workspace/parametric/prototype.py"
ORDERS = ("top_to_bottom", "bottom_to_top")
CANONICAL_CLAUSE = "(r0 (obj-r1 left))"
REVERSED_CLAUSE = "(r0 (- h 1 (obj-r2 left)))"
MATCHING_RIVALS = {
    "pair_by_input_row", "pair_by_sorted_color", "pair_by_area_only",
    "ignore_row_0", "ignore_row_1", "ignore_row_2",
}


@pytest.fixture(scope="module")
def prototype():
    assert PROTOTYPE_PATH.is_file(), "assembly-order prototype has not been implemented"
    spec = importlib.util.spec_from_file_location("jigsaw_assembly_prototype", PROTOTYPE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def canonical():
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError("selected canonical task missing")


@pytest.fixture(scope="module")
def selected():
    return load_selected_generator(TASK_ID, root=ROOT)


@pytest.fixture(scope="module")
def episodes(prototype):
    return {
        "top": prototype.build_episode(root=ROOT, seed=18),
        "bottom": prototype.build_episode(root=ROOT, seed=19),
        "custom": prototype.build_episode(root=ROOT, seed=18, n_train=5, n_test=2),
    }


def _pairs(episode):
    return [*episode["train"], *episode["test"]]


def _key(grid):
    return json.dumps(grid, separators=(",", ":"))


def _reverse_bands(grid):
    """Move complete three-row bands while preserving row order within each."""
    output = copy.deepcopy(grid)
    starts = list(range(1, len(grid) - 1, 4))
    for destination, origin in zip(starts, reversed(starts)):
        output[destination:destination + 3] = copy.deepcopy(grid[origin:origin + 3])
    return output


def _literal(value):
    if isinstance(value, list):
        return "(" + " ".join(_literal(item) for item in value) + ")"
    assert type(value) is int and 0 <= value <= 9
    return str(value)


@pytest.fixture(scope="module")
def oracle(canonical, episodes):
    """Run the canonical source and one exact clause mutation independently."""
    top_source = canonical["program_solution"]
    assert top_source.count(CANONICAL_CLAUSE) == 1
    sources = (top_source, top_source.replace(CANONICAL_CLAUSE, REVERSED_CLAUSE))
    grids = [pair["input"] for pair in canonical["train"] + canonical["test"]]
    grids += [pair["input"] for episode in episodes.values() for pair in _pairs(episode)]
    by_grid = {}
    with RacketBridge() as bridge:
        for order, source in zip(ORDERS, sources):
            stripped = source.strip()
            assert stripped.startswith("(rule! ") and stripped.endswith(")")
            body = stripped[len("(rule! "):-1].strip()
            bridge.eval_text(f"(define independent-test-rule {body})")
            outputs = bridge.eval_text(
                "(map independent-test-rule '" + _literal(grids) + ")"
            )
            assert isinstance(outputs, list) and len(outputs) == len(grids)
            by_grid[order] = {_key(grid): output for grid, output in zip(grids, outputs)}
    return by_grid


def test_parameter_contract_and_exact_integer_seed_parity(prototype):
    assert prototype.ALLOWED_ASSEMBLY_ORDERS == ORDERS
    assert prototype.DEFAULT_ASSEMBLY_ORDER == "top_to_bottom"
    for seed in (-2, 0, 18, 100):
        assert prototype.choose_assembly_order(seed) == ORDERS[0]
    for seed in (-1, 1, 19, 101):
        assert prototype.choose_assembly_order(seed) == ORDERS[1]
    class IntegerSubclass(int):
        pass
    for seed in (True, False, 1.0, "1", None, IntegerSubclass(1)):
        with pytest.raises(TypeError, match="seed"):
            prototype.choose_assembly_order(seed)


def test_only_declared_orders_are_accepted(prototype, canonical):
    grid = canonical["train"][0]["input"]
    for invalid in (None, True, "", "reverse", "TOP_TO_BOTTOM"):
        with pytest.raises(ValueError, match="assembly_order"):
            prototype.racket_source(invalid, root=ROOT)
        with pytest.raises(ValueError, match="assembly_order"):
            prototype.python_transform(grid, invalid, root=ROOT)


def test_exact_default_authority_and_single_clause_alternative(prototype, canonical):
    source = canonical["program_solution"]
    assert prototype.racket_source(ORDERS[0], root=ROOT) == source
    assert prototype.racket_source(ORDERS[1], root=ROOT) == source.replace(
        CANONICAL_CLAUSE, REVERSED_CLAUSE
    )
    assert hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12] == "82f172ba82d3"


def test_rule_materialization_preserves_exact_sources(prototype, tmp_path):
    destination = tmp_path / "racket"
    prototype.materialize_rules(root=ROOT, out=destination)
    assert {path.name for path in destination.iterdir()} == {
        f"{order}.rkt" for order in ORDERS
    }
    for order in ORDERS:
        assert (destination / f"{order}.rkt").read_bytes() == prototype.racket_source(
            order, root=ROOT
        ).encode("utf-8")


def test_prototype_keeps_selected_production_authority_isolated(
    prototype, selected, tmp_path
):
    generator, path, source_sha = selected
    before = path.read_bytes()
    prototype.materialize_rules(root=ROOT, out=tmp_path / "isolated-rules")
    assert generator.RULE_HASH == "82f172ba82d3"
    assert path.read_bytes() == before
    assert hashlib.sha256(before).hexdigest() == source_sha
    assert PROTOTYPE_PATH != path


def test_canonical_fixtures_retain_exact_top_order_outputs(prototype, canonical, oracle):
    pairs = canonical["train"] + canonical["test"]
    assert len(pairs) == 4
    for pair in pairs:
        assert prototype.python_transform(pair["input"], ORDERS[0], root=ROOT) == pair["output"]
        assert oracle[ORDERS[0]][_key(pair["input"])] == pair["output"]


def test_bottom_order_moves_bands_without_flipping_their_rows(
    prototype, canonical, oracle
):
    examples = canonical["train"] + canonical["test"]
    distinguishes_whole_flip = False
    for pair in examples:
        expected = _reverse_bands(pair["output"])
        distinguishes_whole_flip |= expected != list(reversed(pair["output"]))
        assert prototype.python_transform(pair["input"], ORDERS[1], root=ROOT) == expected
        assert oracle[ORDERS[1]][_key(pair["input"])] == expected
    assert distinguishes_whole_flip, "fixtures must distinguish band order from row reflection"


def test_default_episode_counts_are_three_and_four(episodes):
    for name in ("top", "bottom"):
        assert len(episodes[name]["train"]) == 3
        assert len(episodes[name]["test"]) == 4


def test_demonstration_and_query_counts_are_independent(episodes):
    assert len(episodes["custom"]["train"]) == 5
    assert len(episodes["custom"]["test"]) == 2


def test_all_episode_inputs_are_globally_distinct_and_lawful(episodes, selected):
    generator, _, _ = selected
    for episode in episodes.values():
        pairs = _pairs(episode)
        assert len({_key(pair["input"]) for pair in pairs}) == len(pairs)
        assert all(generator.strict_canonical_like(pair["input"]) == [] for pair in pairs)


def test_episode_is_deterministic_for_same_seed_and_counts(prototype, episodes):
    assert prototype.build_episode(root=ROOT, seed=18) == episodes["top"]


def test_every_pair_uses_the_frozen_setting_and_real_racket_label(
    prototype, episodes, oracle
):
    for name, episode in episodes.items():
        order = ORDERS[1] if name == "bottom" else ORDERS[0]
        assert episode["seed"] == (19 if name == "bottom" else 18)
        assert episode["parameters"]["assembly_order"] == order
        for pair in _pairs(episode):
            assert pair["output"] == oracle[order][_key(pair["input"])]
            assert pair["output"] == prototype.python_transform(pair["input"], order, root=ROOT)
            other = ORDERS[1] if order == ORDERS[0] else ORDERS[0]
            assert pair["output"] != oracle[other][_key(pair["input"])]


def test_reference_execution_failure_cannot_fall_back_to_python(prototype, monkeypatch):
    def fail_reference(*args, **kwargs):
        raise RuntimeError("sentinel Racket execution failure")
    monkeypatch.setattr(prototype, "_racket_outputs", fail_reference)
    with pytest.raises(RuntimeError, match="sentinel Racket execution failure"):
        prototype.build_episode(root=ROOT, seed=18)


def test_duplicate_exhaustion_is_bounded_and_never_labels_a_partial_episode(
    prototype, selected, canonical, monkeypatch
):
    generator, source_path, source_sha = selected
    fixed_grid = copy.deepcopy(canonical["train"][0]["input"])
    assert generator.strict_canonical_like(fixed_grid) == []
    calls = []

    def repeated_input(*args, **kwargs):
        calls.append((args, kwargs))
        return copy.deepcopy(fixed_grid)

    def unexpected_labels(*args, **kwargs):
        pytest.fail("exhausted distinct-input sampling must not label a partial episode")

    monkeypatch.setattr(
        prototype, "load_selected_generator",
        lambda *args, **kwargs: (generator, source_path, source_sha),
    )
    monkeypatch.setattr(generator, "generate", repeated_input)
    monkeypatch.setattr(prototype, "_racket_outputs", unexpected_labels)
    with pytest.raises(RuntimeError, match="distinct inputs"):
        prototype.build_episode(root=ROOT, seed=18)
    assert prototype.ATTEMPTS_PER_PAIR == 32
    assert len(calls) == prototype.ATTEMPTS_PER_PAIR * 3 == 96


def test_invalid_counts_are_rejected_before_label_execution(prototype, monkeypatch):
    def unexpected_execution(*args, **kwargs):
        pytest.fail("invalid counts reached Racket")
    monkeypatch.setattr(prototype, "_racket_outputs", unexpected_execution)
    for name, invalids in {"n_train": [-1, 0, 1, 2, 33], "n_test": [0, -1, 33]}.items():
        for value in invalids:
            with pytest.raises(ValueError, match=name):
                prototype.build_episode(root=ROOT, seed=18, **{name: value})
    class IntegerSubclass(int):
        pass
    for name in ("n_train", "n_test"):
        for value in (True, False, 3.0, "3", None, IntegerSubclass(3)):
            with pytest.raises(TypeError, match=name):
                prototype.build_episode(root=ROOT, seed=18, **{name: value})


def test_rival_registry_contains_both_orders_and_all_lifted_matching_rivals(
    prototype, episodes
):
    analysis = prototype.analyze_rivals(episodes["top"], root=ROOT)
    names = set(analysis["rival_names"])
    assert set(ORDERS) <= names
    assert {f"{name}@{order}" for name in MATCHING_RIVALS for order in ORDERS} <= names
    assert {"flip_rows", "flip_columns", "rotate_180"} <= names


def test_rival_survivors_are_filtered_only_by_demonstrations(prototype, episodes):
    original = prototype.analyze_rivals(episodes["top"], root=ROOT)
    changed = copy.deepcopy(episodes["top"])
    for pair in changed["test"]:
        pair["output"] = [[9]]
    after = prototype.analyze_rivals(changed, root=ROOT)
    assert after["demo_survivors"] == original["demo_survivors"]


def test_demonstrations_identify_order_and_every_query_against_declared_rivals(
    prototype, episodes
):
    for name in ("top", "bottom"):
        episode = episodes[name]
        analysis = prototype.analyze_rivals(episode, root=ROOT)
        intended = episode["parameters"]["assembly_order"]
        alternative = ORDERS[1] if intended == ORDERS[0] else ORDERS[0]
        assert intended in analysis["demo_survivors"]
        assert alternative not in analysis["demo_survivors"]
        assert len(analysis["queries"]) == len(episode["test"])
        assert all(query["disagreeing_survivors"] == [] for query in analysis["queries"])


def test_writer_exports_exact_shared_visible_bytes_in_content_id_order(
    prototype, episodes, tmp_path
):
    inputs = [episodes["bottom"], episodes["top"]]
    before = copy.deepcopy(inputs)
    destination = tmp_path / "public"
    rows = prototype.write_public_challenges(iter(inputs), out=destination)
    expected = sorted(
        [{"public_id": public_challenge_id(episode),
          "filename": f"{public_challenge_id(episode)}.json"} for episode in inputs],
        key=lambda row: row["public_id"],
    )
    assert rows == expected
    assert {path.name for path in destination.iterdir()} == {row["filename"] for row in rows}
    for episode in inputs:
        payload = (destination / f"{public_challenge_id(episode)}.json").read_bytes()
        assert payload == public_challenge_bytes(episode)
        assert hashlib.sha256(payload).hexdigest() == public_challenge_id(episode)
        visible = json.loads(payload)
        assert set(visible) == {"train", "test"}
        assert all(set(pair) == {"input", "output"} for pair in visible["train"])
        assert all(set(pair) == {"input"} for pair in visible["test"])
    assert inputs == before


def test_public_identity_ignores_private_fields_and_query_answers(
    prototype, episodes, tmp_path
):
    original = episodes["top"]
    changed = copy.deepcopy(original)
    changed.update({"seed": 998877, "parameters": {"assembly_order": "private-mode"},
                    "program": "private reference code", "evidence": "private evidence"})
    for pair in changed["test"]:
        pair["output"] = [[9]]
    first = prototype.write_public_challenges([original], out=tmp_path / "one")
    second = prototype.write_public_challenges([changed], out=tmp_path / "two")
    assert first == second
    filename = first[0]["filename"]
    assert (tmp_path / "one" / filename).read_bytes() == (tmp_path / "two" / filename).read_bytes()


def test_writer_rejects_duplicate_visible_payloads_before_writing(
    prototype, episodes, tmp_path
):
    duplicate = copy.deepcopy(episodes["top"])
    duplicate["seed"] = -999
    duplicate["test"][0]["output"] = [[9]]
    destination = tmp_path / "public"
    with pytest.raises(ValueError, match="(?i)duplicate"):
        prototype.write_public_challenges([episodes["top"], duplicate], out=destination)
    assert not destination.exists() or not list(destination.iterdir())


def test_writer_preflights_existing_targets_without_partial_exports(
    prototype, episodes, tmp_path
):
    inputs = sorted([episodes["top"], episodes["bottom"]], key=public_challenge_id)
    destination = tmp_path / "public"
    destination.mkdir()
    existing = destination / f"{public_challenge_id(inputs[-1])}.json"
    existing.write_bytes(b"existing public destination must survive\n")
    with pytest.raises(FileExistsError):
        prototype.write_public_challenges(inputs, out=destination)
    assert existing.read_bytes() == b"existing public destination must survive\n"
    assert list(destination.iterdir()) == [existing]
