"""Native promotion checks for the eefadafb2b7b connectivity family."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random

import pytest

from reviewer_support import (
    canonical_path,
    find_root,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "eefadafb2b7b"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
PARAMETRIC = HOME / "workspace" / "parametric"


def _load(name: str):
    path = PARAMETRIC / name
    assert path.is_file(), f"missing required parametric source: {path}"
    spec = importlib.util.spec_from_file_location(
        f"_eefadafb2b7b_{name.replace('.', '_')}", path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    programs = set()
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.add(row["program_solution"])
    assert len(programs) == 1
    return next(iter(programs))


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


def _racket_grid(grid):
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


@pytest.fixture(scope="module")
def racket_apply():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    with RacketBridge() as bridge:
        identity = bridge.runtime_identity
        assert identity["backend"] == "racket"
        assert identity["protected"] is True

        def apply(program: str, grid):
            return bridge.eval_text(f"({wrap_rule(program)} {_racket_grid(grid)})")

        yield apply


def test_native_files_and_contract_are_complete():
    for name in ("adapter.py", "prototype.py", "promotion.json", "canonical.rkt"):
        assert (PARAMETRIC / name).is_file()
    contract = json.loads((PARAMETRIC / "promotion.json").read_text(encoding="utf-8"))
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/eefadafb2b7b/workspace/parametric/adapter.py",
        "parameters": {"connectivity": [8, 4]},
        "default": {"connectivity": 8},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "resources": [
            "generators/eefadafb2b7b/workspace/parametric/prototype.py",
            "generators/eefadafb2b7b/workspace/parametric/canonical.rkt",
        ],
    }


def test_default_program_is_exact_canonical_and_alternate_is_only_connectivity_change():
    prototype = _load("prototype.py")
    canonical = _canonical_program()
    assert prototype.program({"connectivity": 8}) == canonical
    alternate = prototype.program({"connectivity": 4})
    assert alternate != canonical
    assert canonical.count("(objects-8 cyan-mask 0)") == 1
    assert alternate.count("(objects cyan-mask 0)") == 1
    assert "(objects-8 cyan-mask 0)" not in alternate


def test_settings_share_inputs_and_three_demos_identify_the_selected_rule():
    prototype = _load("prototype.py")
    eight = prototype.generate(17, {"connectivity": 8}, demos=3, queries=4)
    four = prototype.generate(17, {"connectivity": 4}, demos=3, queries=4)
    assert _inputs(eight) == _inputs(four)
    assert prototype.fit_settings(eight["train"]) == [{"connectivity": 8}]
    assert prototype.fit_settings(four["train"]) == [{"connectivity": 4}]
    assert any(a["output"] != b["output"] for a, b in zip(eight["test"], four["test"]))


def test_counts_are_independent_prefix_stable_and_query_four_is_substantive_30x30():
    prototype = _load("prototype.py")
    short = prototype.generate(23, {"connectivity": 4}, demos=2, queries=1)
    medium = prototype.generate(23, {"connectivity": 4}, demos=2, queries=4)
    long = prototype.generate(23, {"connectivity": 4}, demos=6, queries=4)
    assert short["train"] == medium["train"] == long["train"][:2]
    assert short["test"] == medium["test"][:1]
    assert medium["test"] == long["test"]
    assert [(len(p["input"]), len(p["input"][0])) for p in long["test"]] == [
        (12, 15),
        (18, 20),
        (24, 27),
        (30, 30),
    ]
    pairs = long["train"] + long["test"]
    assert len({_freeze(pair["input"]) for pair in pairs}) == len(pairs)
    stress = long["test"][-1]["input"]
    occupied_rows = {r for r, row in enumerate(stress) if any(row)}
    occupied_cols = {c for c in range(30) if any(stress[r][c] for r in range(30))}
    assert {0, 29} <= occupied_rows
    assert {0, 29} <= occupied_cols
    assert sum(cell != 0 for row in stress for cell in row) >= 90


def test_public_projection_hashes_only_visible_bytes():
    prototype = _load("prototype.py")
    episode = prototype.generate(31, {"connectivity": 4}, demos=3, queries=4)
    visible = public_challenge_bytes(episode)
    identity = public_challenge_id(episode)
    mutated = copy.deepcopy(episode)
    mutated["settings"] = {"private": "changed"}
    mutated["seed"] = 999
    mutated["program_solution"] = "private changed program"
    mutated["test"][0]["output"] = [[9]]
    assert public_challenge_bytes(mutated) == visible
    assert public_challenge_id(mutated) == identity
    assert hashlib.sha256(visible).hexdigest() == identity
    public = json.loads(visible)
    assert all(set(pair) == {"input"} for pair in public["test"])


def test_three_demos_eliminate_every_declared_finite_shortcut():
    prototype = _load("prototype.py")
    for connectivity in (8, 4):
        report = prototype.self_review(
            prototype.generate(41, {"connectivity": connectivity}, demos=3, queries=4)
        )
        intended = f"connectivity_{connectivity}"
        assert report["selected"] == {"connectivity": connectivity}
        assert report["survivors"] == [intended]
        assert report["harmful_survivors"] == []
        assert report["intended_survivors"] == [intended]


def test_native_adapter_enforces_types_and_racket_executes_all_labels(racket_apply):
    adapter = _load("adapter.py")
    prototype = _load("prototype.py")
    before = random.getstate()
    for connectivity in (8, 4):
        settings = {"connectivity": connectivity}
        episode = adapter.generate(7, settings, 2, 4)
        assert set(episode) == {"train", "test", "program_solution"}
        assert episode["program_solution"] == adapter.program(settings)
        for pair in episode["train"] + episode["test"]:
            assert pair["output"] == prototype.solve(pair["input"], settings)
            assert racket_apply(episode["program_solution"], pair["input"]) == pair["output"]
    assert random.getstate() == before

    bad = [
        (-1, {"connectivity": 8}, 2, 4),
        (True, {"connectivity": 8}, 2, 4),
        (0, {"connectivity": 8}, 1, 4),
        (0, {"connectivity": 8}, 7, 4),
        (0, {"connectivity": 8}, 2, 0),
        (0, {"connectivity": 8}, 2, 5),
        (0, {"connectivity": 6}, 2, 4),
        (0, {"connectivity": True}, 2, 4),
        (0, {"connectivity": 8, "extra": 1}, 2, 4),
    ]
    for args in bad:
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(*args)
