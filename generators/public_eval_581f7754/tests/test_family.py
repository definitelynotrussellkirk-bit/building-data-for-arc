"""Canonical and parametric regressions for public parent 581f7754."""
from __future__ import annotations
import copy
import importlib
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
    from reviewer_support import find_root
    runtime = (find_root(__file__) / "shared" / "runtime").resolve()
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
    spec = importlib.util.spec_from_file_location(f"_t581_{name}", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def official_pairs():
    from reviewer_support import find_root
    raw = find_root(__file__) / "shared" / "data" / "raw"
    task = json.loads((raw / "arc-agi_evaluation_challenges.json").read_text())["581f7754"]
    gold = json.loads((raw / "arc-agi_evaluation_solutions.json").read_text())["581f7754"]
    pairs = [("train", i, p["input"], p["output"]) for i, p in enumerate(task["train"])]
    pairs += [("test", i, p["input"], gold[i]) for i, p in enumerate(task["test"])]
    return pairs


def test_reference_exists_and_python_matches_all_official_labels():
    family = load("family")
    assert (HOME / "reference.rkt").is_file()
    for split, index, grid, expected in official_pairs():
        assert family.solve(grid, "matching_color") == expected, (split, index)


def test_reference_matches_all_official_labels_through_protected_racket():
    apply, identity, bridge = protected_evaluator()
    try:
        assert identity["backend"] == "racket" and identity["protected"]
        program = (HOME / "reference.rkt").read_text()
        for split, index, grid, expected in official_pairs():
            assert apply(program, grid) == expected, (split, index)
    finally:
        bridge.close()


def test_centered_full_three_block_gets_one_cell_toward_anchor_exception():
    family = load("family")
    bg = 8
    grid = [[bg] * 12 for _ in range(10)]
    grid[5][0] = 2
    for r in range(2, 5):
        for c in range(6, 9):
            grid[r][c] = 1
    grid[3][7] = 2
    out = family.solve(grid, "matching_color")
    assert out[5][6] == 2
    assert all(out[r][c] == 1 for r in range(4, 7) for c in range(5, 8) if (r, c) != (5, 6))
    assert all(out[r][8] == bg for r in range(4, 7))


def test_nearest_line_uses_geometry_instead_of_marker_color():
    family = load("family")
    grid = family.make_scene(5, "unit", 16, 18, orientation="rows", stress=False)
    matching = family.solve(grid, "matching_color")
    nearest = family.solve(grid, "nearest_line")
    assert matching != nearest
    a = family.intermediate(grid, "matching_color")
    b = family.intermediate(grid, "nearest_line")
    assert a["objects"] == b["objects"]
    assert a["assignments"] != b["assignments"]


@pytest.mark.parametrize("seed", [0, 17, 43])
def test_counts_matched_inputs_distinct_queries_and_30x30(seed):
    adapter = load("adapter")
    episodes = [adapter.generate(seed, {"assignment": setting}, 2, 4)
                for setting in ("matching_color", "nearest_line")]
    assert [[p["input"] for p in e["train"] + e["test"]] for e in episodes][0] == [
        p["input"] for p in episodes[1]["train"] + episodes[1]["test"]
    ]
    for episode in episodes:
        assert len(episode["train"]) == 2 and len(episode["test"]) == 4
        grids = [p["input"] for p in episode["train"] + episode["test"]]
        assert len({json.dumps(g, separators=(",", ":")) for g in grids}) == 6
        assert len(episode["test"][-1]["input"]) == 30
        assert len(episode["test"][-1]["input"][0]) == 30
        assert sum(v != family_bg(episode["test"][-1]["input"]) for row in episode["test"][-1]["input"] for v in row) >= 30
    assert any(a["output"] != b["output"] for a, b in zip(episodes[0]["train"], episodes[1]["train"]))


def family_bg(grid):
    from collections import Counter
    return Counter(v for row in grid for v in row).most_common(1)[0][0]


@pytest.mark.parametrize("bad", [True, -1, 1.5, "3", None])
def test_strict_seed_rejection(bad):
    with pytest.raises(ValueError):
        load("adapter").generate(bad, {"assignment": "matching_color"}, 2, 4)


@pytest.mark.parametrize("field,bad", [("demos", 1), ("demos", 7), ("demos", True),
                                         ("queries", 0), ("queries", 5), ("queries", 2.0)])
def test_strict_count_rejection(field, bad):
    kwargs = dict(seed=0, settings={"assignment": "matching_color"}, demos=2, queries=4)
    kwargs[field] = bad
    with pytest.raises(ValueError):
        load("adapter").generate(**kwargs)


@pytest.mark.parametrize("settings", [{}, {"assignment": "x"}, {"assignment": True},
                                         {"assignment": "matching_color", "x": 1}, None])
def test_strict_settings_rejection(settings):
    with pytest.raises(ValueError):
        load("adapter").program(settings)


def test_default_program_exact_and_sequential_public_projection_private_invariant():
    from reviewer_support import public_challenge_bytes, public_challenge_id
    adapter = load("adapter")
    assert adapter.program({"assignment": "matching_color"}) == (HOME / "reference.rkt").read_text()
    full = adapter.generate(17, {"assignment": "nearest_line"}, 2, 4)
    short = adapter.generate(17, {"assignment": "nearest_line"}, 2, 1)
    assert short["test"] == full["test"][:1]
    assert short["private_query_bank"] == full["test"]
    assert {adapter.presentation_order(i)[0] for i in range(24)} == {0, 1, 2, 3}
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
        for setting in ("matching_color", "nearest_line"):
            episode = adapter.generate(29, {"assignment": setting}, 2, 4)
            for pair in episode["train"] + episode["test"]:
                assert apply(adapter.program({"assignment": setting}), pair["input"]) == pair["output"]
    finally:
        bridge.close()


def test_finite_rivals_are_refuted_by_two_demonstrations():
    family = load("family")
    adapter = load("adapter")
    for seed in range(12):
        for setting in ("matching_color", "nearest_line"):
            episode = adapter.generate(seed, {"assignment": setting}, 2, 4)
            survivors = set(family.RIVALS)
            for pair in episode["train"]:
                survivors = {name for name in survivors
                             if family.solve_rival(pair["input"], setting, name) == pair["output"]}
            assert not survivors, (seed, setting, survivors)


def test_causal_counterfactual_changes_qualified_shape():
    adapter = load("adapter")
    pair = adapter.generate(17, {"assignment": "nearest_line"}, 2, 4)["test"][-1]
    apply, _, bridge = protected_evaluator()
    try:
        assert apply(adapter.program({"assignment": "nearest_line"}), pair["input"]) == pair["output"]
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
