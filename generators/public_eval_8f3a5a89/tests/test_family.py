"""Canonical and parametric regressions for public parent 8f3a5a89."""
from __future__ import annotations
import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import pytest

HOME = Path(__file__).resolve().parents[1]


def protected_evaluator():
    """Force the evaluator modules to come from this staged checkout.

    The packet test harness may preload an installed arc_repl pytest plugin
    before its checkout-local PYTHONPATH takes effect.  _real_evaluator
    deliberately rejects that mixed-source state.
    """
    from reviewer_support import find_root
    root = find_root(__file__)
    runtime = (root / "shared" / "runtime").resolve()
    for prefix in ("arc_repl", "puzzle_generators"):
        for name in list(sys.modules):
            if name == prefix or name.startswith(prefix + "."):
                module = sys.modules.get(name)
                source = getattr(module, "__file__", None)
                if source is None or not Path(source).resolve().is_relative_to(runtime):
                    del sys.modules[name]
    if str(runtime) not in sys.path:
        sys.path.insert(0, str(runtime))
    importlib.invalidate_caches()
    from arcpuzzles.parametric_worker import _real_evaluator
    return _real_evaluator(runtime)


def load(name: str):
    path = HOME / "workspace" / "parametric" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_t8f_{name}", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def official_pairs():
    from reviewer_support import find_root
    root = find_root(__file__)
    raw = root / "shared" / "data" / "raw"
    task = json.loads((raw / "arc-agi_evaluation_challenges.json").read_text())["8f3a5a89"]
    gold = json.loads((raw / "arc-agi_evaluation_solutions.json").read_text())["8f3a5a89"]
    pairs = [("train", i, p["input"], p["output"]) for i, p in enumerate(task["train"])]
    pairs += [("test", i, p["input"], gold[i]) for i, p in enumerate(task["test"])]
    return pairs


def test_reference_exists_and_python_matches_all_official_labels():
    family = load("family")
    assert (HOME / "reference.rkt").is_file()
    for split, index, grid, expected in official_pairs():
        assert family.solve(grid, "outer_only") == expected, (split, index)


def test_reference_matches_all_official_labels_through_protected_racket():
    apply, identity, bridge = protected_evaluator()
    try:
        assert identity["backend"] == "racket" and identity["protected"]
        program = (HOME / "reference.rkt").read_text()
        for split, index, grid, expected in official_pairs():
            assert apply(program, grid) == expected, (split, index)
    finally:
        bridge.close()


def test_hole_scope_changes_only_enclosed_hole_outline():
    family = load("family")
    grid = family.make_scene(5, "unit", 16, 18, orientation="vertical", stress=False)
    outer = family.solve(grid, "outer_only")
    holes = family.solve(grid, "include_holes")
    assert outer != holes
    info = family.analyze(grid)
    assert info["holes"]
    changed = {(r, c) for r in range(len(grid)) for c in range(len(grid[0])) if outer[r][c] != holes[r][c]}
    assert changed
    assert all((r, c) in info["region"] for r, c in changed)


@pytest.mark.parametrize("seed", [0, 17, 43])
def test_counts_matched_inputs_distinct_queries_and_30x30(seed):
    adapter = load("adapter")
    episodes = [adapter.generate(seed, {"contour": setting}, 2, 4)
                for setting in ("outer_only", "include_holes")]
    assert [[p["input"] for p in e["train"] + e["test"]] for e in episodes][0] == [
        p["input"] for p in episodes[1]["train"] + episodes[1]["test"]
    ]
    for episode in episodes:
        assert len(episode["train"]) == 2 and len(episode["test"]) == 4
        grids = [p["input"] for p in episode["train"] + episode["test"]]
        assert len({json.dumps(g, separators=(",", ":")) for g in grids}) == 6
        assert len(episode["test"][-1]["input"]) == 30
        assert len(episode["test"][-1]["input"][0]) == 30
        assert sum(v != 8 for row in episode["test"][-1]["input"] for v in row) >= 45
    assert any(a["output"] != b["output"] for a, b in zip(episodes[0]["train"], episodes[1]["train"]))


@pytest.mark.parametrize("bad", [True, -1, 1.5, "3", None])
def test_strict_seed_rejection(bad):
    with pytest.raises(ValueError):
        load("adapter").generate(bad, {"contour": "outer_only"}, 2, 4)


@pytest.mark.parametrize("field,bad", [("demos", 1), ("demos", 7), ("demos", True),
                                         ("queries", 0), ("queries", 5), ("queries", 2.0)])
def test_strict_count_rejection(field, bad):
    kwargs = dict(seed=0, settings={"contour": "outer_only"}, demos=2, queries=4)
    kwargs[field] = bad
    with pytest.raises(ValueError):
        load("adapter").generate(**kwargs)


@pytest.mark.parametrize("settings", [{}, {"contour": "x"}, {"contour": True},
                                         {"contour": "outer_only", "x": 1}, None])
def test_strict_settings_rejection(settings):
    with pytest.raises(ValueError):
        load("adapter").program(settings)


def test_default_program_exact_and_sequential_public_projection_private_invariant():
    from reviewer_support import public_challenge_bytes, public_challenge_id
    adapter = load("adapter")
    assert adapter.program({"contour": "outer_only"}) == (HOME / "reference.rkt").read_text()
    full = adapter.generate(17, {"contour": "include_holes"}, 2, 4)
    short = adapter.generate(17, {"contour": "include_holes"}, 2, 1)
    assert short["test"] == full["test"][:1]
    assert short["private_query_bank"] == full["test"]
    firsts = {adapter.presentation_order(i)[0] for i in range(24)}
    assert firsts == {0, 1, 2, 3}
    for seed in range(8):
        idx = adapter.presentation_order(seed)[0]
        view = adapter.public_view(full, idx)
        assert set(view) == {"train", "test"}
        assert len(view["test"]) == 1 and set(view["test"][0]) == {"input"}
        hidden = copy.deepcopy(full)
        hidden["settings"] = {"secret": True}
        hidden["program_solution"] = "different"
        hidden["seed"] = 999
        for pair in hidden["test"]:
            pair["output"] = [[9]]
        assert adapter.public_view(hidden, idx) == view
        assert len(public_challenge_id(view)) == 64
        assert public_challenge_bytes(view) == public_challenge_bytes(adapter.public_view(full, idx))


def test_generated_programs_match_python_for_both_settings():
    adapter = load("adapter")
    apply, _, bridge = protected_evaluator()
    try:
        for setting in ("outer_only", "include_holes"):
            episode = adapter.generate(29, {"contour": setting}, 2, 4)
            for pair in episode["train"] + episode["test"]:
                assert apply(adapter.program({"contour": setting}), pair["input"]) == pair["output"]
    finally:
        bridge.close()


def test_finite_rivals_are_refuted_by_two_demonstrations():
    family = load("family")
    for seed in range(12):
        for setting in ("outer_only", "include_holes"):
            episode = load("adapter").generate(seed, {"contour": setting}, 2, 4)
            survivors = set(family.RIVALS)
            for pair in episode["train"]:
                survivors = {name for name in survivors
                             if family.solve_rival(pair["input"], setting, name) == pair["output"]}
            assert not survivors, (seed, setting, survivors)


def test_causal_counterfactual_changes_qualified_shape():
    adapter = load("adapter")
    pair = adapter.generate(17, {"contour": "include_holes"}, 2, 4)["test"][-1]
    apply, _, bridge = protected_evaluator()
    try:
        assert apply(adapter.program({"contour": "include_holes"}), pair["input"]) == pair["output"]
        assert apply(adapter.counterfactual_program(), pair["input"]) != pair["output"]
    finally:
        bridge.close()


def test_generator_is_self_contained_when_relocated(tmp_path):
    from reviewer_support import find_root
    shutil.copy2(HOME / "generator.py", tmp_path / "generator.py")
    code = """import json, generator
g=generator.generate(29,3,difficulty='hard')
assert len(g)==30 and len(g[0])==30
assert not generator.self_check(g)
print(json.dumps(generator.rule_mirror(g)))
"""
    env = dict(os.environ, PYTHONPATH=str(find_root(__file__) / "shared" / "runtime"), PYTHONDONTWRITEBYTECODE="1")
    proc = subprocess.run([sys.executable, "-c", code], cwd=tmp_path, env=env,
                          text=True, capture_output=True, timeout=30)
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout)
