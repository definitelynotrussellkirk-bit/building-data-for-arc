"""Prototype-only semantics; canonical generator coverage lives separately.

PARAMETRIC_CANONICAL_BASELINE=1 intentionally runs the variant expectations
against the unchanged canonical rule, retaining a behavioral red-phase probe.
"""
from __future__ import annotations

from itertools import product
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

TASK_HOME = Path(__file__).resolve().parents[1]
REPO = TASK_HOME.parents[1]
RUNTIME_ROOT = REPO if (REPO / "RUNTIME_MANIFEST.json").is_file() else REPO / "shared/runtime"
sys.path.insert(0, str(RUNTIME_ROOT))
sys.path.insert(0, str(TASK_HOME / "workspace/parametric"))

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_line_comments, strip_rule_wrapper

VALUES = ("both", "low", "high")
SETTINGS = tuple(product(VALUES, repeat=2))


@lru_cache(maxsize=1)
def canonical_program():
    programs = {
        row["program_solution"]
        for line in (REPO / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
        if (row := json.loads(line)).get("task_id") == "77e3acd21c5d"
    }
    assert len(programs) == 1
    return programs.pop()


def witness_grid(*, canvas=(8, 8), markers=((2, 3),)):
    """Explicit lawful three-object scene, independent of the input sampler."""
    source_h, source_w = 5, 7
    height = max(12, canvas[0] + 2)
    width = source_w + 3 + canvas[1] + 1
    grid = [[0] * width for _ in range(height)]
    for r in range(1, 6):
        for c in range(1, 8):
            grid[r][c] = 2
    for r, c in markers:
        grid[1 + r][1 + c] = 3
    for r in range(1, 1 + canvas[0]):
        for c in range(10, 10 + canvas[1]):
            grid[r][c] = 5
    for r in range(8, 11):
        for c in range(1, 6):
            grid[r][c] = 6
    grid[9][2] = 3
    return grid


@pytest.fixture(scope="module")
def bridge():
    value = RacketBridge()
    yield value
    value.close()


def execute(bridge, grid, row_ties, column_ties):
    if os.environ.get("PARAMETRIC_CANONICAL_BASELINE") == "1":
        program = canonical_program()
    else:
        from prototype import Parameters, materialize_rule

        program = materialize_rule(Parameters(row_ties, column_ties))
    # This task is a complete native Racket lambda: no DSL shorthand, dict
    # literals, or free h/w bindings. Reuse the shared comment/wrapper peel.
    callable_text = strip_rule_wrapper(strip_line_comments(program))
    bridge.eval_text(f"(define __tie_test {callable_text})")
    bridge.define_grid("__tie_input", grid)
    return bridge.eval_text("(__tie_test __tie_input)")


@pytest.mark.parametrize("row_ties,column_ties", SETTINGS)
def test_exact_tie_settings_change_real_racket_output(bridge, row_ties, column_ties):
    # The tied source marker is (2,3) in a 5x7 source. An 8x8 canvas
    # gives top/bottom landings 2/5 and left/right landings 3/4.
    expected = [[5] * 8 for _ in range(8)]
    rows = {"both": (2, 5), "low": (2,), "high": (5,)}[row_ties]
    columns = {"both": (3, 4), "low": (3,), "high": (4,)}[column_ties]
    for r, c in product(rows, columns):
        expected[r][c] = 3
    assert execute(bridge, witness_grid(), row_ties, column_ties) == expected


@pytest.mark.parametrize("row_ties,column_ties", SETTINGS)
def test_ordinary_anchors_and_clipping_do_not_change(bridge, row_ties, column_ties):
    expected = [[5] * 8 for _ in range(8)]
    for r, c in ((0, 0), (7, 7), (1, 6)):
        expected[r][c] = 3
    grid = witness_grid(markers=((0, 0), (4, 6), (1, 5)))
    assert execute(bridge, grid, row_ties, column_ties) == expected
    clipped = witness_grid(canvas=(2, 2), markers=((0, 0), (2, 3), (4, 6)))
    assert execute(bridge, clipped, row_ties, column_ties) == [[3, 5], [5, 3]]


def test_default_program_is_exact_canonical_and_variants_have_unique_hashes():
    from prototype import ALL_PARAMETERS, DEFAULT, materialize_rule

    assert materialize_rule(DEFAULT) == canonical_program()
    hashes = {hashlib.sha256(materialize_rule(p).encode()).hexdigest() for p in ALL_PARAMETERS}
    assert len(hashes) == 9


def test_widest_source_is_not_replaced_by_first_multicolor_component(bridge):
    grid = [[0] * 18 for _ in range(17)]
    for r in range(1, 9):
        for c in range(1, 9):
            grid[r][c] = 5
    for r in range(1, 4):
        for c in range(11, 16):
            grid[r][c] = 6
    grid[1][11] = 3
    for r in range(11, 16):
        for c in range(1, 8):
            grid[r][c] = 2
    grid[13][4] = 3
    expected = [[5] * 8 for _ in range(8)]
    expected[5][4] = 3
    assert execute(bridge, grid, "high", "high") == expected


def test_equal_source_and_canvas_dimensions_can_leave_settings_indistinguishable(bridge):
    outputs = [execute(bridge, witness_grid(canvas=(5, 7)), r, c) for r, c in SETTINGS]
    assert all(output == outputs[0] for output in outputs)


@pytest.fixture(scope="module")
def rules():
    from prototype import RacketRules

    with RacketRules() as value:
        yield value


def test_default_matches_all_canonical_labels(rules):
    from prototype import DEFAULT
    from reviewer_support import canonical_pairs

    pairs = canonical_pairs("77e3acd21c5d", root=REPO, labeled_only=True)
    outputs = rules.outputs(DEFAULT, [pair["input"] for pair in pairs])
    assert len(pairs) == 8
    assert outputs == [pair["output"] for pair in pairs]


def test_seed_selects_rule_once_and_covers_bounded_parameter_space():
    from prototype import ALL_PARAMETERS, choose_parameters

    first = [choose_parameters(seed) for seed in range(200)]
    assert first == [choose_parameters(seed) for seed in range(200)]
    assert set(first) == set(ALL_PARAMETERS)


@pytest.mark.parametrize("bad", [True, 1.0, "low", None, -1])
def test_episode_seed_validation_is_strict(bad):
    from prototype import choose_parameters

    with pytest.raises((TypeError, ValueError)):
        choose_parameters(bad)


@pytest.mark.parametrize("bad", [True, 1, "left", "LOW", None])
def test_parameter_values_are_strict(bad):
    from prototype import Parameters

    with pytest.raises((TypeError, ValueError)):
        Parameters(bad, "both")
    with pytest.raises((TypeError, ValueError)):
        Parameters("both", bad)


@pytest.mark.parametrize("row_ties,column_ties", SETTINGS)
def test_complete_episode_labels_and_declared_rival_elimination(rules, row_ties, column_ties):
    from prototype import Parameters, generate_episode, object_sha256

    parameters = Parameters(row_ties, column_ties)
    episode = generate_episode(417, parameters=parameters, rules=rules)
    public, private = episode["public"], episode["private"]
    assert set(public) == {"train", "test"}
    assert len(public["train"]) == 5 and len(public["test"]) == 1
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert private["parameters"] == parameters.as_dict()
    assert private["seed"] == 417
    assert private["public_sha256"] == object_sha256(public)
    pairs = private["train"] + private["test"]
    labels = rules.outputs(parameters, [pair["input"] for pair in pairs])
    assert labels == [pair["output"] for pair in pairs]
    assert private["label_backend"] == "racket"
    assert private["rivals"][parameters.key]["status"] == "selected"
    alternatives = [row for key, row in private["rivals"].items() if key != parameters.key]
    assert len(alternatives) == 8
    assert all(row["status"] == "eliminated" for row in alternatives)
    assert all(0 <= row["first_refuting_demo"] < 5 for row in alternatives)


def test_seeded_episode_replay_is_exact_and_public_is_a_separate_copy(rules):
    from prototype import generate_episode

    first = generate_episode(67, rules=rules)
    second = generate_episode(67, rules=rules)
    assert first == second
    old = first["private"]["train"][0]["input"][0][0]
    first["public"]["train"][0]["input"][0][0] = (old + 1) % 10
    assert first["private"]["train"][0]["input"][0][0] == old


def test_untaught_rule_distinction_is_reported_as_ambiguity(rules):
    from prototype import DEFAULT, score_rivals

    grids = [witness_grid(markers=((0, 0),)), witness_grid()]
    scored = score_rivals(rules.matrix(grids), DEFAULT, n_train=1)
    alternatives = [row for key, row in scored.items() if key != DEFAULT.key]
    assert len(alternatives) == 8
    assert all(row["status"] == "ambiguous" for row in alternatives)


def test_episode_inputs_do_not_encode_parameter_choice(rules):
    from prototype import Parameters, generate_episode

    first = generate_episode(721, parameters=Parameters("low", "high"), rules=rules)
    second = generate_episode(721, parameters=Parameters("high", "low"), rules=rules)
    first_inputs = [p["input"] for p in first["private"]["train"] + first["private"]["test"]]
    second_inputs = [p["input"] for p in second["private"]["train"] + second["private"]["test"]]
    assert first_inputs == second_inputs
    assert first["public"] != second["public"]


def test_cli_replays_across_processes_and_hash_seeds(tmp_path):
    script = TASK_HOME / "workspace/parametric/probe.py"
    records = []
    for hash_seed in ("2", "71"):
        out = tmp_path / f"episode-{hash_seed}"
        env = dict(os.environ, PYTHONHASHSEED=hash_seed)
        run = subprocess.run(
            [sys.executable, str(script), "episode", "--seed", "85", "--out", str(out)],
            cwd=REPO, env=env, text=True, capture_output=True, timeout=120,
        )
        assert run.returncode == 0, run.stdout + run.stderr
        public = json.loads((out / "challenge.json").read_text())
        private = json.loads((out / "private.json").read_text())
        assert set(public) == {"train", "test"}
        assert all(set(pair) == {"input"} for pair in public["test"])
        assert (out / "rule.rkt").read_text() == private["program"]
        assert hashlib.sha256(private["program"].encode()).hexdigest() == private["program_sha256"]
        records.append((public, private))
    assert records[0] == records[1]
