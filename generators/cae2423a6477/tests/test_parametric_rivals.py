"""Independent semantic regressions for selected-barrier enclosure."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

sys.dont_write_bytecode = True
HOME = Path(__file__).resolve().parents[1] / "workspace" / "parametric"


def load_local(name):
    path = HOME / (name + ".py")
    assert path.is_file(), f"missing assigned semantic implementation: {path.name}"
    spec = importlib.util.spec_from_file_location("cae2423a6477_test_" + name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def canvas(height, width, shapes):
    result = [[0] * width for _ in range(height)]
    for cells in shapes:
        for row, col in cells:
            result[row][col] = 3
    return result


def frame(top, left, height, width):
    return {(r, c) for r in range(top, top + height)
            for c in range(left, left + width)
            if r in (top, top + height - 1) or c in (left, left + width - 1)}


def test_joint_cage_fills_the_pocket_outside_every_selected_rectangle():
    oracle = load_local("rivals")
    source = canvas(9, 9, [frame(r, c, 3, 3)
                          for r, c in ((0, 3), (3, 0), (3, 6), (6, 3))])
    border = oracle.intended(source, "border")
    enclosed = oracle.intended(source, "enclosed")
    assert border[4][4] == 0
    assert enclosed[4][4] == 2
    assert sum(value == 7 for row in enclosed for value in row) == 32
    assert sum(value == 2 for row in enclosed for value in row) == 13
    assert oracle.bank("enclosed")["bbox_interiors"](source)[4][4] == 0
    assert oracle.bank("enclosed")["eight_neighbor_exterior"](source)[4][4] == 0


@pytest.mark.parametrize("height,width", [(1, 1), (1, 8), (8, 1), (2, 4), (4, 2), (2, 2)])
def test_degenerate_solid_borders_are_not_selected(height, width):
    oracle = load_local("rivals")
    source = [[3] * width for _ in range(height)]
    assert oracle.intended(source, "border") == source
    assert oracle.intended(source, "enclosed") == source


def test_unselected_green_contents_are_passable_but_never_painted():
    oracle = load_local("rivals")
    source = canvas(11, 11, [frame(0, 0, 11, 11), {(4, 4), (4, 5), (5, 4)}])
    result = oracle.intended(source, "enclosed")
    assert result[4][4] == result[4][5] == result[5][4] == 3
    assert result[5][5] == result[1][1] == 2
    assert all(result[r][c] == 7 for r, c in frame(0, 0, 11, 11))


def test_nonframes_do_not_become_enclosure_walls():
    oracle = load_local("rivals")
    nub = frame(2, 2, 5, 5) | {(1, 4)}
    source = canvas(9, 9, [nub])
    assert oracle.intended(source, "border") == source
    assert oracle.intended(source, "enclosed") == source


def test_each_named_rival_has_an_executable_reference_and_separating_fixture():
    oracle = load_local("rivals")
    for mode in ("border", "enclosed"):
        samples = oracle.fixtures()
        for name, predict in oracle.bank(mode).items():
            assert oracle.racket(mode, name).startswith("(rule!")
            assert any(predict(grid) != oracle.intended(grid, mode)
                       for grid in samples.values()), name


def test_semantic_screen_keeps_a_demo_survivor_even_when_its_query_is_wrong():
    audit = load_local("audit")
    episode = {"train": [{"input": [[0]], "output": [[0]]}],
               "test": [{"input": [[3, 3, 3], [3, 0, 3], [3, 3, 3]],
                         "output": [[7, 7, 7], [7, 0, 7], [7, 7, 7]]}]}
    result = audit.screen_episode(episode, "border", {"identity": lambda grid: [row[:] for row in grid]})
    assert result["survivors"] == ["identity"]
    assert result["query_disagreements"] == {"identity": [0]}
    assert result["refutations"] == {}


def test_nested_frames_preserve_the_inner_frame_and_green_contents():
    oracle = load_local("rivals")
    result = oracle.intended(oracle.fixtures()["nested_with_contents"], "enclosed")
    counts = {color: sum(row.count(color) for row in result) for color in (0, 2, 3, 7)}
    assert counts == {0: 0, 2: 190, 3: 3, 7: 96}


@pytest.mark.parametrize("grid", [[], [[]], [[True]], [[2]], [[3.0]], [["3"]], [[0], [0, 0]], [[0] * 31]])
def test_oracle_rejects_values_outside_the_admitted_grammar(grid):
    oracle = load_local("rivals")
    with pytest.raises(ValueError):
        oracle.intended(grid, "enclosed")


def test_alias_controls_do_not_inflate_observed_mechanism_count():
    oracle = load_local("rivals")
    groups = oracle.signature_groups("enclosed", oracle.fixtures().values())
    assert [group for group in groups if len(group) > 1] == [["bbox_interiors", "eight_neighbor_exterior"]]
    assert len(groups) < len(oracle.bank("enclosed"))


@pytest.fixture(scope="module")
def protected_apply():
    # A staged task-test tree may contain both flattened execution modules and
    # repository-shaped mirrors.  Choose the runtime that actually exists and
    # clear cached arc_repl/puzzle_generators modules before provenance checks.
    for ancestor in Path(__file__).resolve().parents:
        candidates = (ancestor / "shared" / "runtime", ancestor)
        found = next((path for path in candidates if (path / "reviewer_support.py").is_file()), None)
        if found is not None:
            sys.path.insert(0, str(found))
            break
    from reviewer_support import find_root
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator
    root = find_root(__file__)
    nested = root / "shared" / "runtime"
    runtime = nested if (nested / "arc_repl" / "racket_bridge.py").is_file() else root
    with _local_imports(runtime, HOME):
        apply, identity, bridge = _real_evaluator(runtime)
        assert identity["backend"] == "racket" and identity["protected"] is True
        try:
            yield apply
        finally:
            bridge.close()


@pytest.mark.parametrize("mode", ["border", "enclosed"])
def test_independent_reference_matches_handcrafted_semantic_controls(protected_apply, mode):
    oracle = load_local("rivals")
    for name, grid in oracle.fixtures().items():
        assert protected_apply(oracle.racket(mode), grid) == oracle.intended(grid, mode), name


def test_exact_canonical_reference_checks_degeneracy_and_component_geometry(protected_apply):
    oracle = load_local("rivals")
    canonical = (HOME / "canonical.rkt").read_text(encoding="utf-8")
    for name, grid in oracle.fixtures().items():
        assert protected_apply(canonical, grid) == oracle.intended(grid, "border"), name


@pytest.mark.parametrize("mode", ["border", "enclosed"])
def test_every_rival_executes_on_a_separating_input_and_empty_input(protected_apply, mode):
    oracle = load_local("rivals")
    examples = oracle.fixtures()
    for name, predict in oracle.bank(mode).items():
        witness = next(grid for grid in examples.values() if predict(grid) != oracle.intended(grid, mode))
        for grid in (witness, [[0]]):
            assert protected_apply(oracle.racket(mode, name), grid) == predict(grid), name
