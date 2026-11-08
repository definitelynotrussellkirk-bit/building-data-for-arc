from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve().parent
TASK_HOME = HERE.parent
PARAMETRIC = TASK_HOME / "workspace" / "parametric"
REPO = HERE.parents[2]
TASK_ID = "60baf0d49ed5"
for path in (REPO / "src", REPO / "shared" / "runtime"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


def load_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_native():
    return load_path("_test_native_60baf0d49ed5", PARAMETRIC / "native.py")


def load_generator():
    return load_path("_test_generator_60baf0d49ed5", TASK_HOME / "generator.py")


def catalog_program() -> str:
    from arcpuzzles import Catalog

    record = Catalog(REPO).get(TASK_ID)
    programs = {
        variant["program_solution"]
        for variant in record["variants"]
        if isinstance(variant.get("program_solution"), str)
    }
    assert len(programs) == 1
    return next(iter(programs))


def test_canonical_program_is_exact_selected_source() -> None:
    native = load_native()
    assert native.program({"application_mode": "direct"}) == catalog_program()


def test_base_controls_are_effective_and_transform_schedule_varies() -> None:
    generator = load_generator()
    one = generator.generate(
        7, 0, difficulty=None, n_distinct_colors=1, palette_kind="warm"
    )
    colors = {cell for row in one for cell in row if cell not in (0, 9)}
    assert len(colors) == 1
    assert colors <= set(generator.PALETTES["warm"])

    three = generator.generate(
        7, 0, difficulty=None, n_distinct_colors=3, texture="cool"
    )
    colors = {cell for row in three for cell in row if cell not in (0, 9)}
    assert len(colors) == 3
    assert colors <= set(generator.PALETTES["cool"])

    operations = [generator.infer_operation(generator.generate(61, i)) for i in range(3)]
    assert len(set(operations)) == 3


def test_direct_then_repeat_transform_uses_inferred_operation() -> None:
    native = load_native()
    grid, meta = native.sample_input(13, 0, native.DEMO_SPECS[0])
    op = native.infer_transform(grid)
    panels = native.split_panels(grid)
    direct = native.apply_transform(panels[2], op)
    repeated = native.apply_transform(direct, op)
    assert native.transform(grid, "direct") == direct
    assert native.transform(grid, "repeat_transform") == repeated
    assert direct != repeated
    assert meta["operation"] == op


def test_generated_inputs_are_matched_distinct_and_teaching_complete() -> None:
    native = load_native()
    direct = native.generate(17, {"application_mode": "direct"}, demos=3, queries=4)
    repeated = native.generate(
        17, {"application_mode": "repeat_transform"}, demos=3, queries=4
    )
    assert [pair["input"] for pair in direct["train"] + direct["test"]] == [
        pair["input"] for pair in repeated["train"] + repeated["test"]
    ]
    encoded = [
        json.dumps(pair["input"], separators=(",", ":"))
        for pair in repeated["train"] + repeated["test"]
    ]
    assert len(encoded) == len(set(encoded)) == 7
    assert repeated["certificate"]["surviving_settings"] == [
        {"application_mode": "repeat_transform"}
    ]
    assert repeated["certificate"]["ambiguous_rivals"] == []
    assert all(
        pair["output"] == native.transform(pair["input"], "repeat_transform")
        for pair in repeated["train"] + repeated["test"]
    )


def test_query_prefix_is_stable_and_maximum_scene_is_substantive() -> None:
    native = load_native()
    full = native.generate(23, {"application_mode": "repeat_transform"}, 6, 4)
    prefix = native.generate(23, {"application_mode": "repeat_transform"}, 6, 1)
    assert native.public_turn(full, 0) == native.public_turn(prefix, 0)
    stress = full["test"][-1]["input"]
    assert (len(stress), len(stress[0])) == (9, 29)
    nonzero = [(r, c) for r, row in enumerate(stress) for c, value in enumerate(row) if value]
    assert len(nonzero) >= 90
    assert min(r for r, _ in nonzero) == 0 and max(r for r, _ in nonzero) == 8
    assert min(c for _, c in nonzero) == 0 and max(c for _, c in nonzero) == 28


@pytest.mark.parametrize(
    "seed,demos,queries,settings,error",
    [
        (True, 3, 4, {"application_mode": "direct"}, TypeError),
        (0, 1, 4, {"application_mode": "direct"}, ValueError),
        (0, 3, 0, {"application_mode": "direct"}, ValueError),
        (0, 3, 4, {"application_mode": "unknown"}, ValueError),
        (0, 3, 4, {"application_mode": "direct", "extra": 1}, ValueError),
    ],
)
def test_invalid_requests_fail_closed(seed, demos, queries, settings, error) -> None:
    native = load_native()
    with pytest.raises(error):
        native.generate(seed, settings, demos, queries)


def test_counterfactual_skips_second_application() -> None:
    native = load_native()
    source = native.counterfactual_program()
    assert source == native.program({"application_mode": "direct"})
    assert source != native.program({"application_mode": "repeat_transform"})
