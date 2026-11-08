from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


generator = load_module("task_9aed_generator", HOME / "generator.py")


class _AlwaysInvalidShapeRng:
    """Grow a vertical line that always violates the requested max dimension."""

    def choice(self, values):
        values = list(values)
        if values and all(
            isinstance(v, tuple) and len(v) == 2 and v in {(1, 0), (-1, 0), (0, 1), (0, -1)}
            for v in values
        ):
            return (1, 0)
        return max(values)


def test_forced_shape_fallback_is_fully_asymmetric_and_band_safe():
    cells = generator._asym_no_blank_col(_AlwaysInvalidShapeRng(), size=4, maxd=2)

    assert len(generator._all8(cells)) == 8
    assert generator._no_blank_col(cells)
    assert all(
        generator._no_blank_col(generator._norm(generator._apply(cells, code)))
        for code in range(6)
    )


def test_generate_has_valid_deterministic_exhaustion_fallback(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(generator, "_no_blank_col", lambda _cells: False)

    grid = generator.generate(7, 0, difficulty=None)

    assert grid and all(len(row) == len(grid[0]) for row in grid)
    assert sum(cell != 0 for row in grid for cell in row) >= 9
    assert generator.self_check(grid, difficulty=None) == []

PARAMETRIC = HOME / "workspace" / "parametric"


@pytest.fixture
def prototype():
    path = PARAMETRIC / "prototype.py"
    assert path.is_file(), "parametric prototype is not implemented"
    return load_module("task_9aed_parametric_prototype", path)


def _canonical_program_from_catalog() -> str:
    from arcpuzzles import Catalog

    record = Catalog(Path.cwd()).get("9aed2df94248")
    programs = {
        variant["program_solution"]
        for variant in record["variants"]
        if isinstance(variant.get("program_solution"), str)
    }
    assert len(programs) == 1
    return programs.pop()


def test_forward_program_is_exact_canonical_and_reverse_is_guarded(prototype):
    canonical = _canonical_program_from_catalog()

    assert prototype.program_for("forward") == canonical
    reverse = prototype.program_for("reverse")
    assert reverse != canonical
    assert "rotate-cw (rotate-cw (rotate-cw c))" in reverse
    assert prototype.program_for("forward") == (PARAMETRIC / "canonical.rkt").read_text()


@pytest.mark.parametrize("demos", [2, 3, 6])
@pytest.mark.parametrize("direction", ["forward", "reverse"])
def test_episode_contract_is_deterministic_distinct_and_has_30x30_stress(
    prototype, demos: int, direction: str
):
    first = prototype.generate_claims(19, direction=direction, demos=demos, queries=4)
    second = prototype.generate_claims(19, direction=direction, demos=demos, queries=4)

    assert first == second
    assert first["program_solution"] == prototype.program_for(direction)
    assert len(first["train"]) == demos
    assert len(first["test"]) == 4
    pairs = first["train"] + first["test"]
    inputs = [pair["input"] for pair in pairs]
    assert len({prototype.grid_key(grid) for grid in inputs}) == len(inputs)
    assert [len(inputs[-1]), len(inputs[-1][0])] == [30, 30]
    assert sum(cell != 0 for row in inputs[-1] for cell in row) >= 120
    assert all(
        pair["output"] == prototype.solve_python(pair["input"], direction=direction)
        for pair in pairs
    )


def test_inputs_are_matched_across_settings_and_two_demos_teach_both_layers(prototype):
    forward = prototype.generate_claims(7, direction="forward", demos=2, queries=4)
    reverse = prototype.generate_claims(7, direction="reverse", demos=2, queries=4)

    assert [p["input"] for p in forward["train"] + forward["test"]] == [
        p["input"] for p in reverse["train"] + reverse["test"]
    ]
    assert any(
        left["output"] != right["output"]
        for left, right in zip(forward["train"], reverse["train"])
    )
    inferred = [prototype.infer_transform(pair["input"]) for pair in forward["train"]]
    assert inferred == [1, 4]

    # No fixed transform of C can explain the selected two-demo lesson.
    for code in range(8):
        candidate = [
            prototype.apply_transform(prototype.split_panels(pair["input"])[2], code)
            for pair in forward["train"]
        ]
        assert candidate != [pair["output"] for pair in forward["train"]]


def test_count_and_setting_validation(prototype):
    with pytest.raises(ValueError, match="direction"):
        prototype.generate_claims(0, direction="sideways", demos=3, queries=4)
    with pytest.raises(ValueError, match="demos"):
        prototype.generate_claims(0, direction="forward", demos=1, queries=4)
    with pytest.raises(ValueError, match="queries"):
        prototype.generate_claims(0, direction="forward", demos=3, queries=3)


def test_adapter_exports_native_contract(prototype):
    path = PARAMETRIC / "adapter.py"
    assert path.is_file(), "parametric adapter is not implemented"
    adapter = load_module("task_9aed_parametric_adapter", path)

    settings = {"analogy_direction": "reverse"}
    assert adapter.program(settings) == prototype.program_for("reverse")
    episode = adapter.generate(11, settings, 3, 4)
    assert episode == prototype.generate_claims(11, direction="reverse", demos=3, queries=4)
