"""Focused behavioral checks for the unselected parametric workspace prototype."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, public_challenge_bytes, public_challenge_id


TASK = "581bb11ff645"
TASK_HOME = Path(__file__).resolve().parents[1]
REPO = TASK_HOME.parents[1]
PROTOTYPE = TASK_HOME / "workspace/parametric/prototype.py"
SETTINGS = (
    {"count_mode": "cells", "direction": "ascending"},
    {"count_mode": "cells", "direction": "descending"},
    {"count_mode": "components", "direction": "ascending"},
    {"count_mode": "components", "direction": "descending"},
)

# Hand-counted scores: cells A/B/C/D = 4/3/2/3; four-neighbor
# components = 1/3/1/2. B's zeros touch only diagonally. A and C's
# zeros touch the group boundary, so counting may not flood the separators.
BLOCKS = {
    "A": ("222", "002", "002", "222", "222"),
    "B": ("222", "022", "202", "220", "222"),
    "C": ("222", "022", "022", "222", "222"),
    "D": ("222", "002", "222", "220", "222"),
}
EXPECTED_ORDERS = {
    "cells/ascending": "CBDA",
    "cells/descending": "ABDC",
    "components/ascending": "ACDB",
    "components/descending": "BDAC",
    "components8/ascending": "ABCD",
    "components8/descending": "DABC",
    "identity": "ABCD",
    "reverse_groups": "DCBA",
}


def _groups(order):
    """Assemble a literal fixture; deliberately contains no ranking logic."""
    return [[int(cell) for cell in "0".join(BLOCKS[name][row] for name in order)]
            for row in range(5)]


def _load_prototype():
    spec = importlib.util.spec_from_file_location("parametric_581bb11ff645", PROTOTYPE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def prototype():
    return _load_prototype()


@pytest.fixture(scope="module")
def racket():
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge() as bridge:
        yield bridge


def _execute(bridge, program, grid):
    # These authorities are self-contained lambdas. The generic wrap_rule
    # pipeline also needs scripts.comment_solutions, absent from this packet.
    from puzzle_generators.rule_wrap import strip_line_comments, strip_rule_wrapper

    body = strip_rule_wrapper(strip_line_comments(program))
    assert body.lstrip().startswith("(lambda")
    bridge.eval_text(f"(define __parametric_test_rule {body})")
    bridge.define_grid("__parametric_test_input", grid)
    return bridge.eval_text("(__parametric_test_rule __parametric_test_input)")


@pytest.fixture(scope="module")
def episodes(prototype, racket):
    return [prototype.generate_episode(4100 + index, bridge=racket, **setting)
            for index, setting in enumerate(SETTINGS)]


def test_parametric_api_is_available():
    assert PROTOTYPE.is_file(), "The isolated parametric prototype has not been implemented"
    module = _load_prototype()
    for name in ("canonical_program", "materialize_program", "transform",
                 "generate_episode", "lesson_certificate", "write_batch", "verify_batch"):
        assert callable(getattr(module, name, None)), f"Missing parametric API: {name}"


def test_parameter_domain_is_exactly_the_four_supported_rules(prototype):
    assert len(prototype.SETTINGS) == 4
    assert {tuple(sorted(setting.items())) for setting in prototype.SETTINGS} == {
        tuple(sorted(setting.items())) for setting in SETTINGS
    }


def test_default_program_preserves_exact_canonical_authority(prototype):
    ledger = REPO / "shared/data/canonical/puzzles.jsonl"
    programs = {row["program_solution"] for line in ledger.read_text().splitlines()
                if (row := json.loads(line))["task_id"] == TASK}
    assert len(programs) == 1
    authoritative = programs.pop()
    assert prototype.canonical_program() == authoritative
    assert prototype.materialize_program() == authoritative
    assert prototype.materialize_program(count_mode="cells", direction="ascending") == authoritative


def test_default_rule_replays_all_eight_normalized_canonical_pairs(prototype, racket):
    pairs = canonical_pairs(TASK, root=REPO, labeled_only=True)
    assert len(pairs) == 8
    for pair in pairs:
        assert prototype.transform(pair["input"]) == pair["output"]
        assert _execute(racket, prototype.canonical_program(), pair["input"]) == pair["output"]


@pytest.mark.parametrize("setting", SETTINGS)
def test_literal_pattern_order_four_connectivity_and_stable_ties(prototype, racket, setting):
    grid = _groups("ABCD")
    before = copy.deepcopy(grid)
    rival = f"{setting['count_mode']}/{setting['direction']}"
    expected = _groups(EXPECTED_ORDERS[rival])
    actual = prototype.transform(grid, **setting)
    assert actual == expected
    assert grid == before
    assert actual is not grid and all(a is not b for a, b in zip(actual, grid))
    assert _execute(racket, prototype.materialize_program(**setting), grid) == expected


@pytest.mark.parametrize("setting", SETTINGS)
def test_one_discriminating_demo_identifies_the_rule_from_visible_pairs(prototype, setting):
    rival = f"{setting['count_mode']}/{setting['direction']}"
    challenge = {
        "train": [{"input": _groups("ABCD"), "output": _groups(EXPECTED_ORDERS[rival])}],
        "test": [{"input": _groups("ABCD")}],
    }
    certificate = prototype.lesson_certificate(challenge)
    assert certificate["survivors"] == [rival]
    assert certificate["identifiable"] is True
    assert len(certificate["queries"]) == 1
    assert certificate["queries"][0]["identifiable"] is True
    assert certificate["queries"][0]["survivor_predictions"] == [
        {"rival": rival, "output": _groups(EXPECTED_ORDERS[rival])}
    ]


def _ambiguous_challenge():
    return {
        "train": [{"input": _groups("AAA"), "output": _groups("AAA")}],
        "test": [{"input": _groups("ABCD")}],
    }


def test_ambiguous_demos_keep_every_rival_and_expose_query_disagreement(prototype):
    certificate = prototype.lesson_certificate(_ambiguous_challenge())
    assert set(certificate["survivors"]) == set(EXPECTED_ORDERS)
    assert certificate["identifiable"] is False
    query = certificate["queries"][0]
    assert query["identifiable"] is False
    predictions = {row["rival"]: row["output"] for row in query["survivor_predictions"]}
    assert predictions == {name: _groups(order) for name, order in EXPECTED_ORDERS.items()}


def test_certificate_ignores_missing_changed_and_malformed_private_query_labels(prototype):
    challenge = _ambiguous_challenge()
    baseline = prototype.lesson_certificate(challenge)
    for private_label in (_groups("CBDA"), _groups("BDAC"), None, "not a grid", {"answer": 7}):
        changed = copy.deepcopy(challenge)
        changed["test"][0]["output"] = private_label
        changed.update({
            "parameters": {"count_mode": "untrusted", "direction": "untrusted"},
            "seed": "private seed must not affect inference",
            "program": "private program must not affect inference",
            "program_sha256": "untrusted",
            "certificate": {"identifiable": True, "survivors": ["cells/ascending"]},
        })
        assert prototype.lesson_certificate(changed) == baseline


def test_survivors_may_agree_on_a_query_without_identifying_one_parameter(prototype):
    challenge = _ambiguous_challenge()
    challenge["test"] = [{"input": _groups("AAA")}]
    certificate = prototype.lesson_certificate(challenge)
    assert set(certificate["survivors"]) == set(EXPECTED_ORDERS)
    assert certificate["identifiable"] is True
    assert certificate["queries"][0]["identifiable"] is True
    assert all(row["output"] == _groups("AAA")
               for row in certificate["queries"][0]["survivor_predictions"])


def test_inconsistent_demo_cannot_pass_identifiability_vacuously(prototype):
    challenge = {
        "train": [{"input": _groups("ABCD"), "output": _groups("AAAA")}],
        "test": [{"input": _groups("ABCD")}],
    }
    certificate = prototype.lesson_certificate(challenge)
    assert certificate["survivors"] == []
    assert certificate["identifiable"] is False
    assert certificate["queries"][0]["identifiable"] is False
    assert certificate["queries"][0]["survivor_predictions"] == []


@pytest.mark.parametrize("index", range(4))
def test_generated_default_episodes_keep_four_distinct_queries_and_real_labels(
    prototype, racket, episodes, index
):
    episode = episodes[index]
    setting = SETTINGS[index]
    assert episode["parameters"] == setting
    assert episode["seed"] == 4100 + index
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 4
    assert episode["program"] == prototype.materialize_program(**setting)
    assert episode["program_sha256"] == hashlib.sha256(episode["program"].encode()).hexdigest()
    all_pairs = episode["train"] + episode["test"]
    assert len({json.dumps(pair["input"]) for pair in all_pairs}) == len(all_pairs)
    for pair in all_pairs:
        assert pair["output"] == _execute(racket, episode["program"], pair["input"])
        assert pair["output"] == prototype.transform(pair["input"], **setting)
    public = json.loads(public_challenge_bytes(episode))
    assert episode["certificate"] == prototype.lesson_certificate(public)
    assert episode["certificate"]["identifiable"] is True
    assert all(query["identifiable"] for query in episode["certificate"]["queries"])


def test_generation_is_deterministic_fresh_and_does_not_change_global_rng(prototype, racket):
    random.seed(810734)
    state = random.getstate()
    first = prototype.generate_episode(91, bridge=racket, count_mode="components", direction="descending")
    assert random.getstate() == state
    expected = copy.deepcopy(first)
    second = prototype.generate_episode(91, bridge=racket, count_mode="components", direction="descending")
    assert second == expected
    first["train"][0]["input"][0][0] = 9
    first["test"][0]["output"][0][0] = 9
    first["parameters"]["direction"] = "tampered"
    assert second == expected
    assert prototype.generate_episode(91, bridge=racket, count_mode="components", direction="descending") == expected
    assert random.getstate() == state


@pytest.mark.parametrize("seed,n_demo,n_query", [(0, 1, 1), (2**63 - 1, 16, 16)])
def test_supported_generation_boundaries_are_real_episodes(prototype, racket, seed, n_demo, n_query):
    episode = prototype.generate_episode(seed, n_demo=n_demo, n_query=n_query, bridge=racket)
    assert len(episode["train"]) == n_demo
    assert len(episode["test"]) == n_query
    assert episode["certificate"]["identifiable"] is True
    assert len({json.dumps(pair["input"]) for pair in episode["train"] + episode["test"]}) == n_demo + n_query


@pytest.mark.parametrize("name,value", [
    ("count_mode", "pixels"), ("count_mode", ""), ("count_mode", None),
    ("count_mode", True), ("count_mode", ["cells"]),
    ("direction", "reverse"), ("direction", ""), ("direction", None),
    ("direction", True), ("direction", {"ascending": True}),
])
def test_unknown_or_nonstring_parameters_fail_closed_everywhere(prototype, name, value):
    kwargs = {name: value}
    with pytest.raises(ValueError):
        prototype.materialize_program(**kwargs)
    with pytest.raises(ValueError):
        prototype.transform(_groups("ABCD"), **kwargs)
    with pytest.raises(ValueError):
        prototype.generate_episode(1, **kwargs)


@pytest.mark.parametrize("name,value", [
    ("seed", -1), ("seed", 2**63), ("seed", True), ("seed", 1.0), ("seed", "1"), ("seed", None),
    ("n_demo", 0), ("n_demo", 17), ("n_demo", True), ("n_demo", 1.0), ("n_demo", "3"), ("n_demo", None),
    ("n_query", 0), ("n_query", 17), ("n_query", True), ("n_query", 1.0), ("n_query", "4"), ("n_query", None),
])
def test_invalid_seed_and_pair_counts_fail_closed(prototype, name, value):
    kwargs = {"seed": 1, name: value}
    with pytest.raises(ValueError):
        prototype.generate_episode(**kwargs)


BAD_GRIDS = [
    None, (), [], [[]], ["22202220222"],
    [[0] * 15 for _ in range(5)],
    [[2] * 15 for _ in range(5)],
    _groups("AB"), _groups("ABCDAB"),
    [tuple(row) for row in _groups("ABCD")],
    _groups("ABCD")[:-1] + [_groups("ABCD")[-1][:-1]],
    [[False if cell == 0 else cell for cell in row] for row in _groups("ABCD")],
    [[2.0 if cell == 2 else cell for cell in row] for row in _groups("ABCD")],
    [[1 if cell == 2 else cell for cell in row] for row in _groups("ABCD")],
    [_groups("ABCD")[0] for _ in range(31)],
    [[2] * 7 + [0] + [2] * 7 + [0] + [2] * 7 + [0] + [2] * 7 for _ in range(5)],
    [[0] + row for row in _groups("ABCD")],
    [row + [0] for row in _groups("ABCD")],
    [row[:4] + [0] + row[4:] for row in _groups("ABCD")],
    [row[:2] + row[3:] for row in _groups("ABCD")],
]


@pytest.mark.parametrize("grid", BAD_GRIDS)
def test_malformed_grids_fail_closed(prototype, grid):
    with pytest.raises(ValueError):
        prototype.transform(grid)


@pytest.mark.parametrize("challenge", [
    None, {}, {"train": [], "test": [{"input": _groups("ABCD")}]},
    {"train": [{"input": _groups("ABCD"), "output": _groups("CBDA")}], "test": []},
    {"train": [{"input": _groups("ABCD")}], "test": [{"input": _groups("ABCD")}]},
    {"train": [{"input": _groups("ABCD"), "output": [[True]]}], "test": [{"input": _groups("ABCD")}]},
    {"train": [{"input": _groups("ABCD"), "output": _groups("CBDA")}], "test": [{"input": []}]},
])
def test_malformed_visible_lessons_fail_closed(prototype, challenge):
    with pytest.raises(ValueError):
        prototype.lesson_certificate(challenge)


def test_batch_public_files_are_exact_shared_bytes_with_hash_names(prototype, episodes, tmp_path):
    out = tmp_path / "batch"
    result = prototype.write_batch(list(reversed(episodes)), out)
    expected_ids = sorted(public_challenge_id(episode) for episode in episodes)
    assert result["public_ids"] == expected_ids
    assert json.loads((out / "index.json").read_bytes())["public_ids"] == expected_ids
    assert sorted(path.stem for path in (out / "public").glob("*.json")) == expected_ids
    assert sorted(path.stem for path in (out / "private").glob("*.json")) == expected_ids
    for episode in episodes:
        identifier = public_challenge_id(episode)
        payload = (out / "public" / f"{identifier}.json").read_bytes()
        assert payload == public_challenge_bytes(episode)
        assert hashlib.sha256(payload).hexdigest() == identifier
        public = json.loads(payload)
        assert set(public) == {"train", "test"}
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert all(set(pair) == {"input"} for pair in public["test"])
        private = json.loads((out / "private" / f"{identifier}.json").read_bytes())
        for key in ("train", "test", "parameters", "seed", "program", "program_sha256", "certificate"):
            assert private[key] == episode[key]


def _change_private_fields(episode):
    changed = copy.deepcopy(episode)
    changed["seed"] += 1
    changed["parameters"] = {"count_mode": "components", "direction": "descending"}
    changed["program"] = "(rule! g)"
    changed["program_sha256"] = hashlib.sha256(changed["program"].encode()).hexdigest()
    changed["certificate"] = {"identifiable": False, "survivors": []}
    for pair in changed["test"]:
        pair["output"] = [[9 for _ in row] for row in pair["input"]]
    return changed


def test_batch_identity_ignores_all_private_fields_but_changes_for_visible_demo(prototype, episodes, tmp_path):
    episode = episodes[0]
    private_change = _change_private_fields(episode)
    first = prototype.write_batch([episode], tmp_path / "first")
    second = prototype.write_batch([private_change], tmp_path / "private_change")
    assert first["public_ids"] == second["public_ids"] == [public_challenge_id(episode)]
    identifier = first["public_ids"][0]
    assert (tmp_path / "first/public" / f"{identifier}.json").read_bytes() == (
        tmp_path / "private_change/public" / f"{identifier}.json").read_bytes()
    visible_change = copy.deepcopy(episode)
    visible_change["train"][0]["output"][0][0] = 9
    third = prototype.write_batch([visible_change], tmp_path / "visible_change")
    assert third["public_ids"] != first["public_ids"]


def test_duplicate_visible_payload_is_rejected_before_creating_any_output(prototype, episodes, tmp_path):
    out = tmp_path / "must_not_exist"
    with pytest.raises(ValueError, match="(?i)duplicate"):
        prototype.write_batch([episodes[0], _change_private_fields(episodes[0])], out)
    assert not out.exists()


def test_batch_refuses_existing_output_without_altering_it(prototype, episodes, tmp_path):
    out = tmp_path / "existing"
    out.mkdir()
    sentinel = out / "keep.txt"
    sentinel.write_bytes(b"existing user content\n")
    with pytest.raises((ValueError, FileExistsError)):
        prototype.write_batch([episodes[0]], out)
    assert list(out.iterdir()) == [sentinel]
    assert sentinel.read_bytes() == b"existing user content\n"


def test_serialized_batch_verifier_replays_every_parameter_on_every_pair(prototype, racket, episodes, tmp_path):
    out = tmp_path / "replay"
    prototype.write_batch(episodes, out)
    report = prototype.verify_batch(out, bridge=racket)
    assert report["status"] == "passed"
    assert report["episodes"] == 4
    assert report["labeled_pairs"] == 28
    assert report["queries"] == 16
    assert report["racket_parameter_replays"] == 112
    assert report["training_admitted"] is False
    assert sorted(row["public_id"] for row in report["rows"]) == sorted(
        public_challenge_id(episode) for episode in episodes
    )


@pytest.mark.parametrize("corruption", ["query_label", "program", "certificate", "public_bytes"])
def test_serialized_batch_verifier_rejects_corrupted_content(prototype, racket, episodes, tmp_path, corruption):
    out = tmp_path / corruption
    index = prototype.write_batch([episodes[0]], out)
    identifier = index["public_ids"][0]
    public_path = out / "public" / f"{identifier}.json"
    private_path = out / "private" / f"{identifier}.json"
    if corruption == "public_bytes":
        # Valid JSON with unchanged visible values still has the wrong exact ID.
        public_path.write_bytes(public_path.read_bytes() + b"\n")
    else:
        private = json.loads(private_path.read_bytes())
        if corruption == "query_label":
            cell = private["test"][0]["output"][0][0]
            private["test"][0]["output"][0][0] = 2 if cell == 0 else 0
        elif corruption == "program":
            private["program"] = "(rule! (lambda (g) g))"
            private["program_sha256"] = hashlib.sha256(private["program"].encode()).hexdigest()
        elif corruption == "certificate":
            private["certificate"]["identifiable"] = False
        private_path.write_text(json.dumps(private))
        assert public_path.read_bytes() == public_challenge_bytes(private)
        assert hashlib.sha256(public_path.read_bytes()).hexdigest() == identifier
    with pytest.raises(ValueError):
        prototype.verify_batch(out, bridge=racket)


@pytest.mark.parametrize("corruption", [
    "label_zero_to_false", "label_integer_to_float",
    "certificate_index_to_false", "certificate_boolean_to_integer",
])
def test_serialized_verifier_rejects_numeric_type_aliases(prototype, racket, episodes, tmp_path, corruption):
    out = tmp_path / corruption
    index = prototype.write_batch([episodes[0]], out)
    identifier = index["public_ids"][0]
    private_path = out / "private" / f"{identifier}.json"
    private = json.loads(private_path.read_bytes())
    if corruption == "label_zero_to_false":
        output = private["test"][0]["output"]
        r, c = next((r, c) for r, row in enumerate(output)
                    for c, cell in enumerate(row) if cell == 0)
        output[r][c] = False
    elif corruption == "label_integer_to_float":
        output = private["test"][0]["output"]
        output[0][0] = float(output[0][0])
    elif corruption == "certificate_index_to_false":
        private["certificate"]["queries"][0]["query_index"] = False
    elif corruption == "certificate_boolean_to_integer":
        private["certificate"]["queries"][0]["identifiable"] = 1
    private_path.write_text(json.dumps(private))
    assert (out / "public" / f"{identifier}.json").read_bytes() == public_challenge_bytes(private)
    with pytest.raises(ValueError):
        prototype.verify_batch(out, bridge=racket)
