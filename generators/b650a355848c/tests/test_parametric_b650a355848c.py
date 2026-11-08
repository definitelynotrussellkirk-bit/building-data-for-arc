"""Focused contract tests for the proposed marker-assignment family.

Protected Racket qualification is the authority for retained labels; these tests
pin deterministic sampling, exact-source binding, teaching, and public projection.
"""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, canonical_path, public_challenge_bytes

TASK_ID = "b650a355848c"
HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"
POLICIES = ("independent_nearest", "minimum_bijection")


def _load(filename: str):
    path = PARAMETRIC / filename
    assert path.is_file(), f"missing parametric source: {path}"
    name = "_b650_parametric_" + filename.replace(".", "_")
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    programs = {
        row["program_solution"]
        for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines()
        if line.strip()
        and (row := json.loads(line)).get("task_id") == TASK_ID
    }
    assert len(programs) == 1
    return next(iter(programs))


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


def _inputs(episode, split):
    return [pair["input"] for pair in episode[split]]


def test_required_native_files_and_contract():
    for filename in ("adapter.py", "prototype.py", "promotion.json", "README.md", "canonical.rkt"):
        assert (PARAMETRIC / filename).is_file()
    contract = json.loads((PARAMETRIC / "promotion.json").read_text(encoding="utf-8"))
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/b650a355848c/workspace/parametric/adapter.py",
        "parameters": {"assignment_policy": list(POLICIES)},
        "default": {"assignment_policy": "independent_nearest"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "resources": [
            "generators/b650a355848c/workspace/parametric/prototype.py",
            "generators/b650a355848c/workspace/parametric/canonical.rkt",
        ],
    }


def test_default_program_is_exact_canonical_and_alternate_is_distinct():
    adapter = _load("adapter.py")
    assert adapter.program({"assignment_policy": "independent_nearest"}) == _canonical_program()
    assert adapter.program({"assignment_policy": "minimum_bijection"}) != _canonical_program()


def test_python_default_matches_every_canonical_pair():
    prototype = _load("prototype.py")
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) >= 4
    for pair in pairs:
        assert prototype.solve(pair["input"], {"assignment_policy": "independent_nearest"}) == pair["output"]


def test_independent_counts_distinct_inputs_and_literal_labels():
    adapter = _load("adapter.py")
    prototype = _load("prototype.py")
    for policy in POLICIES:
        settings = {"assignment_policy": policy}
        for demos in range(2, 7):
            for queries in range(1, 5):
                episode = adapter.generate(19, settings, demos, queries)
                assert (len(episode["train"]), len(episode["test"])) == (demos, queries)
                assert episode["program_solution"] == adapter.program(settings)
                pairs = episode["train"] + episode["test"]
                assert len({_frozen(pair["input"]) for pair in pairs}) == demos + queries
                for pair in pairs:
                    assert pair["output"] == prototype.solve(pair["input"], settings)
                    for grid in (pair["input"], pair["output"]):
                        assert type(grid) is list and 1 <= len(grid) <= 30
                        assert type(grid[0]) is list and 1 <= len(grid[0]) <= 30
                        assert all(type(row) is list and len(row) == len(grid[0]) for row in grid)
                        assert all(type(cell) is int and 0 <= cell <= 9 for row in grid for cell in row)
        assert settings == {"assignment_policy": policy}


def test_matched_inputs_determinism_and_split_prefixes():
    adapter = _load("adapter.py")
    episodes = [adapter.generate(7, {"assignment_policy": policy}, 3, 4) for policy in POLICIES]
    for split in ("train", "test"):
        assert _inputs(episodes[0], split) == _inputs(episodes[1], split)
    base = copy.deepcopy(episodes[0])
    assert adapter.generate(7, {"assignment_policy": POLICIES[0]}, 3, 4) == base
    assert _inputs(adapter.generate(7, {"assignment_policy": POLICIES[0]}, 2, 4), "test") == _inputs(base, "test")
    assert _inputs(adapter.generate(7, {"assignment_policy": POLICIES[0]}, 6, 4), "test") == _inputs(base, "test")
    assert adapter.generate(7, {"assignment_policy": POLICIES[0]}, 3, 1)["test"] == base["test"][:1]
    episodes[0]["train"][0]["input"][0][0] = 9
    assert adapter.generate(7, {"assignment_policy": POLICIES[0]}, 3, 4) == base


def _rival_output(prototype, grid, name):
    _height, _width, vertical, shapes, markers = prototype._scene_parts(grid)
    matrix = prototype._distance_matrix(shapes, markers)
    count = len(shapes)
    if name == "greedy_unique":
        remaining = set(range(count))
        assignment = []
        for distances in matrix:
            chosen = min(remaining, key=lambda index: (distances[index], index))
            assignment.append(chosen)
            remaining.remove(chosen)
    elif name == "spatial_pairing":
        assignment = sorted(
            range(count),
            key=lambda index: (
                markers[index][0] if vertical else markers[index][1],
                markers[index][1], markers[index][0], index,
            ),
        )
    elif name == "nearest_shape_cell":
        assignment = []
        for shape in shapes:
            distances = [
                min(abs(marker[0] - row) + abs(marker[1] - col)
                    for row, col in shape["cells"])
                for marker in markers
            ]
            assignment.append(min(range(count), key=lambda index: distances[index]))
    elif name == "color_order":
        assignment = sorted(range(count), key=lambda index: markers[index][2])
    else:  # pragma: no cover - test helper guard
        raise ValueError(name)
    output_height = 4 * count if vertical else 4
    output_width = 4 if vertical else 4 * count
    output = [[0] * output_width for _ in range(output_height)]
    for slot, (shape, marker_index) in enumerate(zip(shapes, assignment, strict=True)):
        top, left, _bottom, _right = shape["bbox"]
        base_row = 4 * slot if vertical else 0
        base_col = 0 if vertical else 4 * slot
        for row, col in shape["cells"]:
            output[base_row + row - top][base_col + col - left] = markers[marker_index][2]
    return output


def test_first_two_demos_reject_bounded_harmful_shortcuts():
    adapter = _load("adapter.py")
    prototype = _load("prototype.py")
    rivals = {
        "independent_nearest": ("nearest_shape_cell",),
        "minimum_bijection": ("greedy_unique", "spatial_pairing", "color_order"),
    }
    for seed in range(64):
        for policy, names in rivals.items():
            episode = adapter.generate(seed, {"assignment_policy": policy}, 2, 4)
            for name in names:
                assert any(
                    _rival_output(prototype, pair["input"], name) != pair["output"]
                    for pair in episode["train"]
                ), (seed, policy, name)


def test_two_demos_teach_policy_and_exercise_global_assignment():
    adapter = _load("adapter.py")
    prototype = _load("prototype.py")
    episodes = {
        policy: adapter.generate(31, {"assignment_policy": policy}, 2, 4)
        for policy in POLICIES
    }
    for selected in POLICIES:
        rival = POLICIES[1 - POLICIES.index(selected)]
        assert any(
            prototype.solve(pair["input"], {"assignment_policy": rival}) != pair["output"]
            for pair in episodes[selected]["train"]
        )
        for pair in episodes[selected]["train"]:
            facts = prototype.observables(pair["input"])
            assert len(set(facts["independent_marker_indices"])) < facts["shape_count"]
            assert len(set(facts["minimum_bijection_marker_indices"])) == facts["shape_count"]
            assert facts["minimum_bijection_unique"] is True
            assert all(len(row["nearest_marker_indices"]) == 1 for row in facts["distance_rows"])


def test_four_queries_include_movable_substantive_30x30_stress():
    adapter = _load("adapter.py")
    positions = set()
    for seed in range(8):
        episode = adapter.generate(seed, {"assignment_policy": POLICIES[0]}, 3, 4)
        shapes = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
        assert set(shapes) == {(11, 17), (17, 12), (24, 27), (30, 30)}
        positions.add(shapes.index((30, 30)))
        stress = episode["test"][shapes.index((30, 30))]["input"]
        nonzero = [(r, c) for r, row in enumerate(stress) for c, value in enumerate(row) if value]
        assert len(nonzero) >= 40
        assert min(r for r, _ in nonzero) == 0 or min(c for _, c in nonzero) == 0
        assert max(r for r, _ in nonzero) == 29 or max(c for _, c in nonzero) == 29
        facts = _load("prototype.py").observables(stress)
        assert facts["shape_count"] == facts["marker_count"] == 5
    assert len(positions) >= 3


def test_sampler_constructively_supports_bounded_seed_census():
    adapter = _load("adapter.py")
    settings = {"assignment_policy": POLICIES[0]}
    for seed in range(64):
        episode = adapter.generate(seed, settings, 6, 4)
        assert len(episode["train"]) == 6
        assert len(episode["test"]) == 4


def test_first_turn_public_projection_hides_private_and_future_data():
    adapter = _load("adapter.py")
    prototype = _load("prototype.py")
    episode = adapter.generate(5, {"assignment_policy": POLICIES[1]}, 3, 4)
    visible = prototype.public_challenge(episode, query_index=0)
    identity = prototype.public_id(episode, query_index=0)
    assert set(visible) == {"train", "test"}
    assert visible["train"] == episode["train"]
    assert visible["test"] == [{"input": episode["test"][0]["input"]}]
    assert identity == __import__("hashlib").sha256(public_challenge_bytes(visible)).hexdigest()
    changed = copy.deepcopy(episode)
    changed.update(settings={"assignment_policy": POLICIES[0]}, seed=999, program_solution="private")
    for pair in changed["test"]:
        pair["output"] = [[9]]
    for pair in changed["test"][1:]:
        pair["input"] = [[8]]
    assert prototype.public_challenge(changed, query_index=0) == visible
    assert prototype.public_id(changed, query_index=0) == identity
    changed["test"][0]["input"][0][0] = (changed["test"][0]["input"][0][0] + 1) % 10
    assert prototype.public_id(changed, query_index=0) != identity


def test_malformed_settings_and_request_boundaries_reject():
    adapter = _load("adapter.py")
    for settings in (None, {}, {"assignment_policy": "typo"}, {"assignment_policy": True},
                     {"assignment_policy": POLICIES[0], "extra": 1}):
        with pytest.raises((TypeError, ValueError)):
            adapter.program(settings)
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(0, settings, 3, 4)
    valid = {"assignment_policy": POLICIES[0]}
    for seed in (-1, 2**63, True, 0.0, "0"):
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(seed, valid, 3, 4)
    for demos, queries in ((1, 4), (7, 4), (True, 4), (3.0, 4),
                           (3, 0), (3, 5), (3, True), (3, 4.0)):
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(0, valid, demos, queries)
    assert len(adapter.generate(2**63 - 1, valid, 2, 1)["test"]) == 1


def test_bounded_rival_audit_tool_has_explicit_finite_inventory():
    rivals = _load("rivals.py")
    audit = _load("audit.py")
    assert rivals.NAMES == (
        "greedy_unique",
        "spatial_pairing",
        "reverse_spatial_pairing",
        "nearest_shape_cell",
        "independent_farthest",
        "first_marker_all",
        "color_order",
        "center_nearest",
    )
    programs = rivals.programs()
    assert set(programs) == set(rivals.NAMES)
    assert len(set(programs.values())) == len(programs)
    assert all(type(program) is str and program.startswith("(rule!") for program in programs.values())
    report = audit.run_bounded(
        sampler_seeds=range(8),
        execution_seeds=(),
        demo_counts=(2, 3, 6),
        queries=4,
        execute_racket=False,
    )
    assert report["status"] == "passed"
    assert report["harmful_survivors"] == []
    assert report["sampler_requests"] == 8 * len(POLICIES) * 3
