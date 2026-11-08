"""Focused tests for the native anchor-size-indexed component family."""
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import sys

import pytest

for ancestor in Path(__file__).resolve().parents:
    runtime = ancestor / "shared" / "runtime"
    if (runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(runtime))
        break

HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"
CANONICAL_PROGRAM = """(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((color (find-first (lambda (v) (!= v 0)) (grid-colors g)))
                  (n (count-color g color)))
             (encode-bar n n color)))))"""


def _load(name: str, path: Path):
    spec = spec_from_file_location(name, path)
    assert spec and spec.loader
    module = module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _components4(grid):
    colors = {value for row in grid for value in row if value != 0}
    assert len(colors) == 1
    color = next(iter(colors))
    height, width = len(grid), len(grid[0])
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    }
    components = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        cells = []
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    stack.append(nxt)
        components.append(tuple(sorted(cells)))
    return color, sorted(components, key=min)


def _oracle(grid, mode):
    color, components = _components4(grid)
    if mode == "all_cells":
        size = sum(map(len, components))
    else:
        anchor = components[0]
        candidates = components[1:]
        target = candidates[(len(anchor) - 1) % len(candidates)]
        size = len(target)
    return [[color] * size]


def test_adapter_preserves_exact_canonical_program_and_validates_settings():
    adapter = _load("anchor_indexed_adapter_contract", PARAMETRIC / "adapter.py")
    prototype = _load("anchor_indexed_prototype_contract", PARAMETRIC / "prototype.py")

    assert adapter.program({"count_mode": "all_cells"}) == CANONICAL_PROGRAM
    assert adapter.program({"count_mode": "anchor_indexed_component"}) == prototype.INDEXED_PROGRAM
    assert prototype.counterfactual_program() != prototype.INDEXED_PROGRAM

    for invalid in (
        None,
        {},
        {"count_mode": "unknown"},
        {"count_mode": "all_cells", "extra": 1},
    ):
        with pytest.raises(ValueError):
            adapter.program(invalid)


@pytest.mark.parametrize("seed", [0, 17, 991])
@pytest.mark.parametrize("demos", range(2, 7))
@pytest.mark.parametrize("queries", range(1, 5))
def test_counts_matched_inputs_prefix_stability_and_python_labels(seed, demos, queries):
    prototype = _load(
        f"anchor_indexed_proto_{seed}_{demos}_{queries}",
        PARAMETRIC / "prototype.py",
    )
    canonical = prototype.generate_episode(
        seed, count_mode="all_cells", demos=demos, queries=queries
    )
    indexed = prototype.generate_episode(
        seed, count_mode="anchor_indexed_component", demos=demos, queries=queries
    )

    assert len(canonical["train"]) == len(indexed["train"]) == demos
    assert len(canonical["test"]) == len(indexed["test"]) == queries
    assert [p["input"] for p in canonical["train"] + canonical["test"]] == [
        p["input"] for p in indexed["train"] + indexed["test"]
    ]

    maximum = prototype.generate_episode(
        seed, count_mode="anchor_indexed_component", demos=6, queries=4
    )
    assert indexed["train"] == maximum["train"][:demos]
    assert indexed["test"] == maximum["test"][:queries]

    pairs = canonical["train"] + canonical["test"]
    serialized = [json.dumps(pair["input"], separators=(",", ":")) for pair in pairs]
    assert len(serialized) == len(set(serialized))

    for mode, episode in (
        ("all_cells", canonical),
        ("anchor_indexed_component", indexed),
    ):
        for pair in episode["train"] + episode["test"]:
            color, components = _components4(pair["input"])
            assert 1 <= color <= 9
            assert len(components) >= 5
            assert pair["output"] == _oracle(pair["input"], mode)
            assert 1 <= len(pair["output"]) <= 30
            assert 1 <= len(pair["output"][0]) <= 30
            assert set(pair["output"][0]) == {color}

    for c_pair, i_pair in zip(canonical["train"], indexed["train"]):
        assert c_pair["output"] != i_pair["output"]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"seed": True, "count_mode": "all_cells", "demos": 3, "queries": 4},
        {"seed": -1, "count_mode": "all_cells", "demos": 3, "queries": 4},
        {"seed": 0, "count_mode": "unknown", "demos": 3, "queries": 4},
        {"seed": 0, "count_mode": "all_cells", "demos": 1, "queries": 4},
        {"seed": 0, "count_mode": "all_cells", "demos": 7, "queries": 4},
        {"seed": 0, "count_mode": "all_cells", "demos": 3, "queries": 0},
        {"seed": 0, "count_mode": "all_cells", "demos": 3, "queries": 5},
    ],
)
def test_invalid_episode_requests_reject(kwargs):
    prototype = _load("anchor_indexed_bad_requests", PARAMETRIC / "prototype.py")
    with pytest.raises(ValueError):
        prototype.generate_episode(**kwargs)


def test_first_two_demos_constructively_refute_fixed_target_shortcuts():
    prototype = _load("anchor_indexed_teaching", PARAMETRIC / "prototype.py")
    audit = _load("anchor_indexed_audit", PARAMETRIC / "audit.py")

    for seed in (0, 17):
        episode = prototype.generate_episode(
            seed, count_mode="anchor_indexed_component", demos=2, queries=4
        )
        anchor_sizes = []
        selected_sizes = []
        for pair in episode["train"]:
            _, components = _components4(pair["input"])
            anchor_sizes.append(len(components[0]))
            selected_sizes.append(
                len(components[1:][(len(components[0]) - 1) % (len(components) - 1)])
            )
        assert anchor_sizes == [1, 3]
        assert selected_sizes == [2, 5]

    report = audit.python_audit(seeds=(0, 17), demo_counts=range(2, 7))
    assert report["ambiguities"] == []
    assert report["episodes"] == 20
    assert report["stress_30x30"] == 20
    assert {
        "all_cells",
        "anchor_size",
        "all_candidates",
        "fixed_candidate_0",
        "fixed_candidate_1",
        "fixed_candidate_2",
        "fixed_candidate_3",
        "largest_candidate",
        "smallest_candidate",
        "wrong_plus_one_selector",
        "reverse_selector",
    } <= set(report["rivals"])


def test_fourth_query_is_substantive_30x30_with_boundary_spread():
    prototype = _load("anchor_indexed_stress", PARAMETRIC / "prototype.py")
    episode = prototype.generate_episode(
        17, count_mode="anchor_indexed_component", demos=3, queries=4
    )
    grid = episode["test"][3]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    nonzero = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    assert len(nonzero) == 30
    assert {0, 29} <= {r for r, _ in nonzero}
    assert {0, 29} <= {c for _, c in nonzero}
    _, components = _components4(grid)
    assert len(components) >= 8


def test_public_turn_hides_private_fields_and_matches_one_query_request():
    prototype = _load("anchor_indexed_public", PARAMETRIC / "prototype.py")
    full = prototype.generate_episode(
        23, count_mode="anchor_indexed_component", demos=3, queries=4
    )
    single = prototype.generate_episode(
        23, count_mode="anchor_indexed_component", demos=3, queries=1
    )
    first = prototype.public_turn(full, 0)
    assert first == prototype.public_turn(single, 0)
    assert set(first) == {"train", "test"}
    assert len(first["test"]) == 1
    assert set(first["test"][0]) == {"input"}
    text = json.dumps(first, sort_keys=True)
    for forbidden in ("count_mode", "program", "seed"):
        assert forbidden not in text


def test_racket_programs_match_python_on_constructive_cases():
    prototype = _load("anchor_indexed_racket", PARAMETRIC / "prototype.py")
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    episode = prototype.generate_episode(
        0, count_mode="anchor_indexed_component", demos=2, queries=1
    )
    programs = {
        mode: prototype.rule_text(mode)
        for mode in ("all_cells", "anchor_indexed_component")
    }
    with RacketBridge(timeout=10, startup_timeout=60) as bridge:
        for mode, program in programs.items():
            wrapped = wrap_rule(program)
            for pair in episode["train"] + episode["test"]:
                literal = "'(" + " ".join(
                    "(" + " ".join(map(str, row)) + ")" for row in pair["input"]
                ) + ")"
                actual = bridge.eval_text(f"({wrapped} {literal})")
                assert actual == _oracle(pair["input"], mode)


def test_causal_case_wrong_intermediate_changes_final_output():
    prototype = _load("anchor_indexed_causal", PARAMETRIC / "prototype.py")
    case = prototype.causal_case(seed=0)
    assert case["settings"] == {"count_mode": "anchor_indexed_component"}
    assert case["intermediate_value"]["anchor_size"] == 2
    assert case["output"] != case["counterfactual_output"]
    assert case["ablation"] == "wrong_intermediate"
