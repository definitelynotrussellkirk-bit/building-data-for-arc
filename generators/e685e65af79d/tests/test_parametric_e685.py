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
TASK_ID = "e685e65af79d"
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
    return load_path("_test_native_e685e65af79d", PARAMETRIC / "native.py")


def load_generator():
    return load_path("_test_generator_e685e65af79d", TASK_HOME / "generator.py")


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
    assert native.program({"symmetry_closure": "rotational_4"}) == catalog_program()


def test_base_generation_refutes_half_turn_and_honors_shape_override() -> None:
    generator = load_generator()
    for sample_index in range(4):
        grid = generator.generate(59, sample_index, difficulty=None)
        assert generator.self_check(grid, difficulty=None) == []
        assert any(
            len(generator._rotation_closure(cells)) > len(generator._half_turn_closure(cells))
            for _color, cells, _bbox in generator._components(grid)
        )

    forced = generator.generate(11, 0, n_blobs=2, blob_shape_idx=3)
    expected = generator._norm(generator._SHAPE_BANK[3])
    assert all(generator._norm(cells) == expected for _color, cells, _bbox in generator._components(forced))


def test_largest_rotational_closure_selects_the_only_dihedral_object() -> None:
    native = load_native()
    grid, meta = native.sample_input(13, 0, native.DEMO_SPECS[0])
    rotational = native.transform(grid, "rotational_4")
    routed = native.transform(grid, "largest_closure_dihedral")
    analysis = native.analyze(grid)
    assert rotational != routed
    assert meta["chiral_object_count"] == meta["object_count"]
    assert meta["winner_object_index"] != 0
    assert analysis["rotational_closure_areas"].count(max(analysis["rotational_closure_areas"])) == 1
    assert analysis["selected_object_index"] == meta["winner_object_index"]
    assert native.analyze(routed)["component_count"] == meta["object_count"]


def test_dihedral_lessons_refute_fill_each_bbox_shortcut() -> None:
    native = load_native()
    episode = native.generate(29, {"symmetry_closure": "largest_closure_dihedral"}, 3, 4)

    def fill_bboxes(grid):
        output = [row[:] for row in grid]
        for obj in native._components(grid):
            r0, c0, r1, c1 = obj["bbox"]
            for r in range(r0, r1 + 1):
                for c in range(c0, c1 + 1):
                    output[r][c] = obj["color"]
        return output

    for rival in (
        "fill_each_bbox",
        "all_dihedral",
        "first_object_dihedral",
        "smallest_closure_dihedral",
        "largest_original_area_dihedral",
    ):
        assert rival in episode["certificate"]["tested_rivals"]
        assert rival not in episode["certificate"]["ambiguous_rivals"]
    assert any(
        pair["output"] != fill_bboxes(pair["input"])
        for pair in episode["train"]
    )


def test_generated_inputs_are_matched_distinct_and_teaching_complete() -> None:
    native = load_native()
    rotational = native.generate(17, {"symmetry_closure": "rotational_4"}, 3, 4)
    dihedral = native.generate(17, {"symmetry_closure": "largest_closure_dihedral"}, 3, 4)
    assert [pair["input"] for pair in rotational["train"] + rotational["test"]] == [
        pair["input"] for pair in dihedral["train"] + dihedral["test"]
    ]
    encoded = [
        json.dumps(pair["input"], separators=(",", ":"))
        for pair in dihedral["train"] + dihedral["test"]
    ]
    assert len(encoded) == len(set(encoded)) == 7
    assert dihedral["certificate"]["surviving_settings"] == [
        {"symmetry_closure": "largest_closure_dihedral"}
    ]
    assert dihedral["certificate"]["ambiguous_rivals"] == []
    assert all(
        pair["output"] == native.transform(pair["input"], "largest_closure_dihedral")
        for pair in dihedral["train"] + dihedral["test"]
    )


def test_query_prefix_is_stable_and_30_by_30_scene_is_substantive() -> None:
    native = load_native()
    full = native.generate(23, {"symmetry_closure": "largest_closure_dihedral"}, 6, 4)
    prefix = native.generate(23, {"symmetry_closure": "largest_closure_dihedral"}, 6, 1)
    assert native.public_turn(full, 0) == native.public_turn(prefix, 0)
    stress = full["test"][-1]["input"]
    assert (len(stress), len(stress[0])) == (30, 30)
    analysis = native.analyze(stress)
    assert analysis["component_count"] == 8
    assert analysis["nonzero_cells"] >= 56
    occupied = [(r, c) for r, row in enumerate(stress) for c, value in enumerate(row) if value]
    assert min(r for r, _ in occupied) == 0 and max(r for r, _ in occupied) == 29
    assert min(c for _, c in occupied) == 0 and max(c for _, c in occupied) == 29


@pytest.mark.parametrize(
    "seed,demos,queries,settings,error",
    [
        (True, 3, 4, {"symmetry_closure": "rotational_4"}, TypeError),
        (0, 1, 4, {"symmetry_closure": "rotational_4"}, ValueError),
        (0, 3, 0, {"symmetry_closure": "rotational_4"}, ValueError),
        (0, 3, 4, {"symmetry_closure": "unknown"}, ValueError),
        (0, 3, 4, {"symmetry_closure": "rotational_4", "extra": 1}, ValueError),
    ],
)
def test_invalid_requests_fail_closed(seed, demos, queries, settings, error) -> None:
    native = load_native()
    with pytest.raises(error):
        native.generate(seed, settings, demos, queries)


def test_counterfactual_uses_the_wrong_first_object_selector() -> None:
    native = load_native()
    source = native.counterfactual_program()
    assert source == (PARAMETRIC / "first_object_dihedral.rkt").read_text()
    assert source != native.program({"symmetry_closure": "rotational_4"})
    assert source != native.program({"symmetry_closure": "largest_closure_dihedral"})
