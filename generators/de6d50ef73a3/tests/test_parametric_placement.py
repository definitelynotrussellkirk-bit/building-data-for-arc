"""Racket-backed regressions for the top-left / marker-corner family."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import random
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace/parametric"


def load(name):
    path = PARAMETRIC / f"{name}.py"
    assert path.is_file(), f"missing parametric {name}.py"
    spec = importlib.util.spec_from_file_location(f"_test_de6d_{name}", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def prototype():
    return load("prototype")


@pytest.fixture(scope="module")
def engine(prototype):
    with prototype.RacketEngine() as runtime:
        yield runtime


def _paste(height, width, crop, top, left):
    output = [[0 for _ in range(width)] for _ in range(height)]
    for r, row in enumerate(crop):
        for c, value in enumerate(row):
            if value:
                output[top + r][left + c] = value
    return output


FIXTURE_CROP = [
    [1, 1, 1, 9],
    [1, 0, 2, 2],
    [1, 2, 2, 0],
]
FIXTURE = _paste(7, 9, FIXTURE_CROP, 2, 2)


def test_default_program_is_exact_canonical_bytes(prototype):
    from reviewer_support import canonical_path, find_root

    root = find_root(HOME)
    rows = [json.loads(line) for line in canonical_path(root).read_text().splitlines()]
    sources = {row["program_solution"] for row in rows if row["task_id"] == prototype.TASK_ID}
    assert sources == {prototype.program({"placement": "top_left"})}


def test_programs_execute_hand_derived_labels(prototype, engine):
    assert prototype.marker_info(FIXTURE)["corner"] == "top_right"
    canonical = _paste(7, 9, FIXTURE_CROP, 0, 0)
    marker = _paste(7, 9, FIXTURE_CROP, 0, 9 - 4)
    assert engine.apply(prototype.program({"placement": "top_left"}), FIXTURE) == canonical
    assert engine.apply(prototype.program({"placement": "marker_corner"}), FIXTURE) == marker
    assert prototype.python_oracle(FIXTURE, {"placement": "top_left"}) == canonical
    assert prototype.python_oracle(FIXTURE, {"placement": "marker_corner"}) == marker


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_counts_matched_inputs_teaching_and_four_queries(prototype, engine, demos):
    episodes = [
        prototype.generate(17, {"placement": placement}, demos, 4, engine=engine)
        for placement in prototype.PLACEMENTS
    ]
    for episode in episodes:
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
        assert len({json.dumps(grid) for grid in inputs}) == demos + 4
        assert [len(inputs[-1]), len(inputs[-1][0])] == [30, 30]
        assert sum(bool(v) for row in inputs[-1] for v in row) >= 150
        corners = [prototype.marker_info(pair["input"])["corner"] for pair in episode["test"]]
        assert corners == ["top_right", "bottom_left", "bottom_right", "top_left"]
        certificate = prototype.verify_episode(episode, engine=engine)
        assert certificate["survivors"] == [episode["settings"]["placement"]]
        assert certificate["fit_scope"] == "demonstrations_only"
        assert all(row["label_matches"] for row in certificate["queries"])
    for split in ("train", "test"):
        assert [p["input"] for p in episodes[0][split]] == [p["input"] for p in episodes[1][split]]
    assert episodes[0]["test"][0]["output"] != episodes[1]["test"][0]["output"]


def test_two_demonstrations_eliminate_fixed_corner_rivals(prototype, engine):
    for placement in prototype.PLACEMENTS:
        episode = prototype.generate(31, {"placement": placement}, 2, 1, engine=engine)
        certificate = prototype.check_teaching(episode["train"], episode["settings"], engine=engine)
        assert certificate["survivors"] == [placement]
        assert set(certificate["declared_rivals"]) >= {
            "top_left", "marker_corner", "fixed_top_right",
            "fixed_bottom_left", "fixed_bottom_right", "identity",
        }


@pytest.mark.parametrize(
    "field,value",
    [
        ("demos", 1), ("demos", 7), ("demos", True), ("demos", 3.0),
        ("queries", 0), ("queries", 5), ("queries", "4"),
        ("seed", -1), ("seed", True),
    ],
)
def test_invalid_requests_fail_before_generation(prototype, field, value):
    args = dict(seed=0, settings={"placement": "top_left"}, demos=3, queries=4)
    args[field] = value
    with pytest.raises(ValueError):
        prototype.generate(**args)


@pytest.mark.parametrize(
    "settings",
    [{}, {"placement": "center"}, {"placement": "top_left", "extra": 1}, {"placement": True}],
)
def test_settings_are_exact(prototype, settings):
    with pytest.raises(ValueError):
        prototype.program(settings)


def test_marker_grammar_rejects_malformed_ambiguous_and_disconnected(prototype):
    valid = deepcopy(FIXTURE)
    assert prototype.marker_info(valid)["marker_color"] == 9
    cases = []
    ragged = deepcopy(valid); ragged[0].pop(); cases.append(ragged)
    boolean = deepcopy(valid); boolean[0][0] = True; cases.append(boolean)
    ambiguous = deepcopy(valid); ambiguous[3][2] = 8; cases.append(ambiguous)
    interior_marker = deepcopy(valid); interior_marker[2][5] = 1; interior_marker[3][3] = 9; cases.append(interior_marker)
    disconnected = deepcopy(valid); disconnected[2][4] = 0; disconnected[3][5] = 0; cases.append(disconnected)
    for grid in cases:
        with pytest.raises(ValueError):
            prototype.marker_info(grid)


def test_sampler_is_deterministic_setting_independent_and_rng_isolated(prototype):
    random.seed(987654)
    state = random.getstate()
    first = prototype.sample_input(101, "query", 3, prototype.QUERY_PROFILES[3])
    assert random.getstate() == state
    second = prototype.sample_input(101, "query", 3, prototype.QUERY_PROFILES[3])
    assert first == second and first is not second
    assert all(a is not b for a, b in zip(first, second))
    info = prototype.marker_info(first)
    assert info["corner"] == "top_left"
    assert len(info["colors"]) >= 3


def test_first_query_input_is_stable_when_query_count_changes(prototype, engine):
    one = prototype.generate(55, {"placement": "marker_corner"}, 3, 1, engine=engine)
    four = prototype.generate(55, {"placement": "marker_corner"}, 3, 4, engine=engine)
    assert one["train"] == four["train"]
    assert one["test"][0] == four["test"][0]


def test_verifier_rejects_tampering_duplicates_and_private_claims(prototype, engine):
    episode = prototype.generate(7, {"placement": "marker_corner"}, 2, 4, engine=engine)
    mutations = []
    bad = deepcopy(episode); bad["test"][0]["output"][0][0] = (bad["test"][0]["output"][0][0] + 1) % 10; mutations.append(bad)
    bad = deepcopy(episode); bad["test"][0] = deepcopy(bad["train"][0]); mutations.append(bad)
    bad = deepcopy(episode); bad["settings"] = {"placement": "top_left"}; mutations.append(bad)
    bad = deepcopy(episode); bad["program_solution"] = "(rule! g)"; mutations.append(bad)
    bad = deepcopy(episode); bad["training_admitted"] = True; mutations.append(bad)
    for bad in mutations:
        with pytest.raises(ValueError):
            prototype.verify_episode(bad, engine=engine)


def test_adapter_and_promotion_contract_are_thin_and_exact(prototype, engine):
    adapter = load("adapter")
    contract = json.loads((PARAMETRIC / "promotion.json").read_text())
    assert contract["default"] == {"placement": "top_left"}
    assert contract["parameters"] == {"placement": ["top_left", "marker_corner"]}
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    assert adapter.program({"placement": "top_left"}) == prototype.program({"placement": "top_left"})
    episode = adapter.generate(3, {"placement": "marker_corner"}, 2, 1)
    assert prototype.verify_episode(episode, engine=engine)["survivors"] == ["marker_corner"]
