from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def prototype():
    path = PARAMETRIC / "prototype.py"
    assert path.is_file(), "parametric prototype is not implemented"
    return load_module("task_e5ead55c33e7_parametric_prototype", path)


def _canonical_program_from_catalog() -> str:
    from arcpuzzles import Catalog

    record = Catalog(Path.cwd()).get("e5ead55c33e7")
    programs = {
        variant["program_solution"]
        for variant in record["variants"]
        if isinstance(variant.get("program_solution"), str)
    }
    assert len(programs) == 1
    return programs.pop()


def test_front_program_is_exact_canonical_and_rear_program_changes_only_order(prototype):
    canonical = _canonical_program_from_catalog()

    assert prototype.program_for("front_first") == canonical
    rear = prototype.program_for("rear_first")
    assert rear != canonical
    assert "(< (obj-c2 a) (obj-c2 b))" in rear
    assert prototype.program_for("front_first") == (PARAMETRIC / "canonical.rkt").read_text()


@pytest.mark.parametrize("demos", [2, 3, 6])
@pytest.mark.parametrize("packing_order", ["front_first", "rear_first"])
def test_episode_contract_is_deterministic_distinct_and_has_dense_30x30_stress(
    prototype, demos: int, packing_order: str
):
    first = prototype.generate_claims(23, packing_order=packing_order, demos=demos, queries=4)
    second = prototype.generate_claims(23, packing_order=packing_order, demos=demos, queries=4)

    assert first == second
    assert first["program_solution"] == prototype.program_for(packing_order)
    assert len(first["train"]) == demos
    assert len(first["test"]) == 4
    pairs = first["train"] + first["test"]
    inputs = [pair["input"] for pair in pairs]
    assert len({prototype.grid_key(grid) for grid in inputs}) == len(inputs)
    assert [len(inputs[-1]), len(inputs[-1][0])] == [30, 30]
    assert sum(cell != 0 for row in inputs[-1] for cell in row) >= 80
    assert all(
        pair["output"] == prototype.solve_python(pair["input"], packing_order=packing_order)
        for pair in pairs
    )


def test_inputs_are_matched_and_two_demos_identify_order_without_color_shortcut(prototype):
    front = prototype.generate_claims(5, packing_order="front_first", demos=2, queries=4)
    rear = prototype.generate_claims(5, packing_order="rear_first", demos=2, queries=4)

    assert [p["input"] for p in front["train"] + front["test"]] == [
        p["input"] for p in rear["train"] + rear["test"]
    ]
    assert all(
        left["output"] != right["output"]
        for left, right in zip(front["train"], rear["train"])
    )

    signatures = []
    for pair in front["train"]:
        objects = prototype.extract_objects(pair["input"])
        signatures.append(tuple(obj["color"] for obj in sorted(objects, key=lambda obj: obj["c2"])))
    assert signatures[0] != signatures[1]


def test_python_solver_reorders_interacting_chain_from_input_dependent_object_list(prototype):
    grid = prototype.build_input(0, role="train", index=0)
    objects = prototype.extract_objects(grid)

    assert len(objects) >= 3
    assert len({obj["c2"] for obj in objects}) == len(objects)
    assert prototype.solve_python(grid, packing_order="front_first") != prototype.solve_python(
        grid, packing_order="rear_first"
    )
    assert any(
        set(left["rows"]) & set(right["rows"])
        for i, left in enumerate(objects)
        for right in objects[i + 1 :]
    )


def test_count_and_setting_validation(prototype):
    with pytest.raises(ValueError, match="packing_order"):
        prototype.generate_claims(0, packing_order="simultaneous", demos=3, queries=4)
    with pytest.raises(ValueError, match="demos"):
        prototype.generate_claims(0, packing_order="front_first", demos=1, queries=4)
    with pytest.raises(ValueError, match="queries"):
        prototype.generate_claims(0, packing_order="front_first", demos=3, queries=3)


def test_adapter_exports_native_contract(prototype):
    path = PARAMETRIC / "adapter.py"
    assert path.is_file(), "parametric adapter is not implemented"
    adapter = load_module("task_e5ead55c33e7_parametric_adapter", path)

    settings = {"packing_order": "rear_first"}
    assert adapter.program(settings) == prototype.program_for("rear_first")
    episode = adapter.generate(13, settings, 3, 4)
    assert episode == prototype.generate_claims(13, packing_order="rear_first", demos=3, queries=4)


def test_seed_zero_first_query_budgets_gaps_before_the_wall(prototype):
    grid = prototype.build_input(0, role="test", index=0)
    wall = len(grid[0]) - 1

    assert max(obj["c2"] for obj in prototype.extract_objects(grid)) <= wall - 2


def test_seed_six_second_training_example_expands_for_mandatory_object_widths(prototype):
    grid = prototype.build_input(6, role="train", index=1)
    wall = len(grid[0]) - 1

    assert len(grid[0]) == 17
    assert max(obj["c2"] for obj in prototype.extract_objects(grid)) <= wall - 2
