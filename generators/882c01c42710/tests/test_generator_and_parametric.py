from __future__ import annotations

import importlib.util
from pathlib import Path


HOME = Path(__file__).resolve().parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _axes(grid):
    h, w = len(grid), len(grid[0])
    row_counts = [sum(v != 0 for v in row) for row in grid]
    col_counts = [sum(grid[r][c] != 0 for r in range(h)) for c in range(w)]
    return row_counts.index(max(row_counts)), col_counts.index(max(col_counts)), row_counts, col_counts


def test_self_check_accepts_a_valid_occupied_crossing():
    gen = _load("generator_882", HOME / "generator.py")
    grid = [[0] * 7 for _ in range(7)]
    grid[3][2:5] = [1, 2, 3]
    grid[1][3] = 4
    grid[2][3] = 1
    grid[4][3] = 3
    assert gen.self_check(grid) == []


def test_length_and_size_overrides_change_the_actual_seed_sequences():
    gen = _load("generator_882_overrides", HOME / "generator.py")
    grid = gen.generate(91, 7, difficulty=None, grid_h=14, grid_w=15, n_h=5, n_v=5)
    assert (len(grid), len(grid[0])) == (14, 15)
    cr, cc, row_counts, col_counts = _axes(grid)
    assert row_counts[cr] == 5
    assert col_counts[cc] == 5
    assert gen.self_check(grid) == []


def test_generation_is_deterministic_for_identical_arguments():
    gen = _load("generator_882_determinism", HOME / "generator.py")
    kwargs = dict(difficulty="medium", grid_h=15, grid_w=16, n_h=4, n_v=3,
                  palette_kind="primary", anchor_corner=True)
    assert gen.generate(1234, 2, **kwargs) == gen.generate(1234, 2, **kwargs)

REPO = HOME.parents[1]
PARAMETRIC = HOME / "workspace" / "parametric" / "prototype.py"


def _parametric():
    assert PARAMETRIC.is_file(), "parametric prototype has not been implemented"
    return _load("parametric_882", PARAMETRIC)


def _canonical_program():
    from arcpuzzles.catalog import Catalog
    catalog = Catalog(REPO)
    programs = {row["program_solution"] for row in catalog._variants()["882c01c42710"]}
    assert len(programs) == 1
    return next(iter(programs))


def test_parametric_default_program_is_exact_canonical_bytes():
    proto = _parametric()
    assert proto.program({"mode": "canonical"}) == _canonical_program()


def test_parametric_counts_settings_and_prefix_are_strict_and_stable():
    proto = _parametric()
    one = proto.generate(17, {"mode": "phase_locked"}, 3, 1)
    four = proto.generate(17, {"mode": "phase_locked"}, 3, 4)
    assert one["train"] == four["train"]
    assert one["test"] == four["test"][:1]
    visible_inputs = [pair["input"] for pair in four["train"] + four["test"]]
    assert len({repr(grid) for grid in visible_inputs}) == 7
    for bad in (1, 7, True):
        try:
            proto.generate(0, {"mode": "canonical"}, bad, 4)
        except (TypeError, ValueError):
            pass
        else:
            raise AssertionError(f"invalid demo count accepted: {bad!r}")
    try:
        proto.generate(0, {"mode": "unknown"}, 3, 4)
    except ValueError:
        pass
    else:
        raise AssertionError("unknown setting accepted")


def test_phase_locked_vertical_phase_consumes_horizontal_crossing_color():
    proto = _parametric()
    grid = [[0] * 9 for _ in range(9)]
    grid[4][1:5] = [1, 2, 3, 4]
    grid[0][5] = 3
    grid[1][5] = 4
    grid[2][5] = 1
    grid[3][5] = 2
    canonical = proto.python_oracle(grid, {"mode": "canonical"})
    phase_locked = proto.python_oracle(grid, {"mode": "phase_locked"})
    cr, cc = proto.seed_axes(grid)
    crossing = phase_locked[cr][cc]
    assert crossing == canonical[cr][cc]
    assert all(phase_locked[r][cc] in {1, 2, 3, 4} for r in range(9))
    assert phase_locked != canonical
    v_seq = [grid[r][cc] for r in range(9) if grid[r][cc] != 0]
    index = v_seq.index(crossing)
    assert phase_locked[cr - 1][cc] == v_seq[(index - 1) % len(v_seq)]
    assert phase_locked[cr + 1][cc] == v_seq[(index + 1) % len(v_seq)]


def test_generated_lessons_distinguish_settings_and_include_substantive_30x30_query():
    proto = _parametric()
    for mode in proto.MODES:
        episode = proto.generate(0, {"mode": mode}, 2, 4)
        other = next(candidate for candidate in proto.MODES if candidate != mode)
        assert any(pair["output"] != proto.python_oracle(pair["input"], {"mode": other})
                   for pair in episode["train"])
        last = episode["test"][-1]
        assert (len(last["input"]), len(last["input"][0])) == (30, 30)
        assert sum(cell != 0 for row in last["output"] for cell in row) >= 59
